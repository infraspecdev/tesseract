#!/usr/bin/env python3
"""Lint ```mermaid fenced blocks in Markdown for the syntax errors that
silently ship today.

Shield embeds Mermaid diagrams in generated docs (LLDs, TRDs, PRDs) and the
renderer emits them verbatim as `<pre class="mermaid">` for client-side
mermaid.js — so an invalid diagram fails *only* in the browser at view time.
Nothing in the author → write → eval → render path ever parses the diagram.
This check closes that gap offline and without Node.

Scope — this is a targeted linter, not a full Mermaid grammar. It catches the
high-frequency failure modes that LLM-authored diagrams hit (and that a real
mermaid-cli run flagged in the component LLDs):

  1. Semicolons inside a sequenceDiagram. Mermaid treats ';' as a statement
     separator, so any text after it on a message/condition line is re-parsed
     as a new (bogus) statement — even inside quotes or parentheses.
  2. An actor/participant identifier that collides with a reserved Mermaid
     keyword (e.g. a participant literally named `Create`, which clashes with
     the create/destroy actor-lifecycle keywords).
  3. Unbalanced block keywords (alt/loop/opt/par/critical/rect/break/box vs
     end) in a sequenceDiagram.

For full grammar coverage, run mermaid-cli (`mmdc`) in CI; this linter is the
fast, dependency-free first line of defence.

Usage:
    python3 validate_mermaid.py FILE.md [FILE.md ...]

Exit status is non-zero if any block fails a check; each failure is printed as
`path:line: message`.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

# Mermaid keywords that cannot be used as an actor/participant identifier in a
# sequenceDiagram — using one as a name makes the lexer take the keyword path.
RESERVED_ACTOR_WORDS = frozenset(
    {
        "participant", "actor", "create", "destroy", "box", "end", "alt",
        "else", "opt", "loop", "par", "and", "critical", "option", "rect",
        "break", "note", "activate", "deactivate", "autonumber", "link",
        "links", "title",
    }
)

# Block-opening keywords that must be matched by a closing `end`.
BLOCK_OPENERS = frozenset(
    {"alt", "opt", "loop", "par", "critical", "rect", "break", "box"}
)

# A sequence message line: `A->>B: text`, `A-->>-B: text`, etc. We only need
# the two actor tokens, so capture the identifiers either side of the arrow.
_ARROW = r"(?:-{1,2}>>?|--?>|-[)x]|<<-->>|x--|--x)"
_MSG_RE = re.compile(
    rf"^\s*(?P<left>[^\s:>-]+)\s*{_ARROW}\s*[+-]?(?P<right>[^\s:>-]+)\s*:"
)
_PARTICIPANT_RE = re.compile(
    r"^\s*(?:participant|actor)\s+(?P<id>[^\s]+)(?:\s+as\s+.*)?$"
)
# Splits a `participant <id> as <alias>` line into the id side and the
# free-form alias so --fix can rename the id without touching the alias.
_ALIAS_SPLIT_RE = re.compile(
    r"^(?P<head>\s*(?:participant|actor)\s+\S+)(?P<sep>\s+as\s+)(?P<alias>.*)$"
)


_NODE_LINE_RE = re.compile(r"line\s+(\d+)", re.IGNORECASE)


def _parse_node_error(stderr: str) -> tuple[int, str]:
    """Map a mermaid.parse() error to a 1-based block line and a one-line message."""
    text = stderr.strip()
    m = _NODE_LINE_RE.search(text)
    block_line = int(m.group(1)) if m else 1
    first_line = text.splitlines()[0] if text else "mermaid parse error"
    return block_line, first_line


def _block_diagram_type(lines: list[str]) -> str:
    for ln in lines:
        s = ln.strip()
        if s:
            return s.split()[0] if s.split() else ""
    return ""


def _iter_mermaid_blocks(text: str):
    """Yield (start_line, list_of_body_lines) for each ```mermaid fence.

    start_line is the 1-based line number of the first body line (the line
    after the opening fence).
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().lower().startswith("```mermaid"):
            body_start = i + 1
            j = body_start
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            yield body_start + 1, lines[body_start:j]  # +1 → 1-based
            i = j + 1
        else:
            i += 1


def _check_sequence_block(start_line: int, body: list[str]) -> list[tuple[int, str]]:
    errors: list[tuple[int, str]] = []
    depth_openers = 0
    depth_ends = 0

    for offset, raw in enumerate(body):
        lineno = start_line + offset
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):  # blank / comment
            continue

        first = stripped.split()[0].lower()
        if first in BLOCK_OPENERS:
            depth_openers += 1
        elif first == "end":
            depth_ends += 1

        # 1. semicolons — illegal as message text in a sequenceDiagram.
        if ";" in line:
            errors.append(
                (
                    lineno,
                    "';' in sequenceDiagram is a statement separator — mermaid "
                    "re-parses everything after it as a new line; use '—' or ','",
                )
            )

        # 2. reserved-word actor identifiers.
        m = _PARTICIPANT_RE.match(line)
        if m and m.group("id").lower() in RESERVED_ACTOR_WORDS:
            errors.append(
                (
                    lineno,
                    f"participant id {m.group('id')!r} is a reserved mermaid "
                    "keyword — rename the actor",
                )
            )
        msg = _MSG_RE.match(line)
        if msg:
            for side in ("left", "right"):
                actor = msg.group(side)
                if actor.lower() in RESERVED_ACTOR_WORDS:
                    errors.append(
                        (
                            lineno,
                            f"actor {actor!r} is a reserved mermaid keyword — "
                            "rename the actor",
                        )
                    )

    # 3. block balance.
    if depth_openers != depth_ends:
        errors.append(
            (
                start_line,
                f"unbalanced blocks in sequenceDiagram: "
                f"{depth_openers} opener(s) (alt/loop/opt/…) vs {depth_ends} 'end'",
            )
        )
    return errors


_MJS_PATH = Path(__file__).with_name("validate_mermaid.mjs")
_NODE_MERMAID_PKG = "mermaid@10"  # must match shell.html CDN major


def _node_available() -> bool:
    return shutil.which("npx") is not None and shutil.which("node") is not None


def _run_node_backend(body: str) -> tuple[int, str]:
    """Run the .mjs backend on one diagram. Returns (exit_code, stderr)."""
    proc = subprocess.run(
        ["npx", "--yes", "--package", _NODE_MERMAID_PKG, "--package", "jsdom",
         "node", str(_MJS_PATH)],
        input=body, capture_output=True, text=True,
    )
    return proc.returncode, proc.stderr


def _validate_block_via_backend(start_line: int, body: list[str]):
    """Validate one block with the Node backend.

    Returns a list of (document_line, message) findings, or None if the backend
    is unavailable / failed to set up (caller falls back to the heuristic).
    """
    if not _node_available():
        return None
    code, stderr = _run_node_backend("\n".join(body) + "\n")
    if code == 0:
        return []
    if code == 1:
        block_line, msg = _parse_node_error(stderr)
        return [(start_line + block_line - 1, msg)]
    return None  # code 2 or anything unexpected → fall back


def _replace_semicolons(line: str) -> str:
    """`;` → `,` when inside () or "", else ` — `. Only after the message ':'.

    Inside parens/quotes the bare comma preserves any following space (so
    `f(x; y)` → `f(x, y)`); outside, the em-dash is space-padded and absorbs
    one adjacent space on each side so `a; b` → `a — b` (no doubled spaces).
    """
    out = []
    in_quote = False
    paren = 0
    for ch in line:
        if ch == '"':
            in_quote = not in_quote
            out.append(ch)
        elif ch == "(":
            paren += 1
            out.append(ch)
        elif ch == ")":
            paren = max(0, paren - 1)
            out.append(ch)
        elif ch == ";":
            if in_quote or paren > 0:
                out.append(",")
            else:
                # Drop a trailing space already emitted, re-pad uniformly.
                if out and out[-1] == " ":
                    out.pop()
                out.append(" — ")
        elif ch == " " and out and out[-1] == " — ":
            # Collapse the space that followed the original ';'.
            continue
        else:
            out.append(ch)
    return "".join(out)


def _reserved_actor_ids(body: str) -> set[str]:
    ids = set()
    for line in body.splitlines():
        m = _PARTICIPANT_RE.match(line)
        if m and m.group("id").lower() in RESERVED_ACTOR_WORDS:
            ids.add(m.group("id"))
        msg = _MSG_RE.match(line)
        if msg:
            for side in ("left", "right"):
                if msg.group(side).lower() in RESERVED_ACTOR_WORDS:
                    ids.add(msg.group(side))
    return ids


def _fix_block(body: str) -> str:
    """Apply deterministic repairs to one diagram body (no fence).

    The trap classes we repair (`;` as a statement separator, reserved-word
    actor ids) are sequenceDiagram-specific — `;` is legal in a flowchart and
    the reserved words are sequence keywords — so we scope the fix the same way
    detection is scoped (see ``validate_text``). Non-sequence blocks are
    returned untouched to avoid corrupting valid diagrams.
    """
    lines = body.splitlines()
    if not _block_diagram_type(lines).lower().startswith("sequencediagram"):
        return body

    # 1. semicolons, line by line.
    lines = [_replace_semicolons(ln) for ln in lines]

    # 2. reserved-word actor ids → <Id>Actor. Whole-word, but only on the
    #    identifier — never the free-form `as <alias>` text on a participant
    #    line (the alias may legitimately reuse the reserved word).
    idents = sorted(_reserved_actor_ids("\n".join(lines)), key=len, reverse=True)

    def _rename(segment: str) -> str:
        for ident in idents:
            segment = re.sub(
                rf"(?<![\w]){re.escape(ident)}(?![\w])", ident + "Actor", segment
            )
        return segment

    out = []
    for line in lines:
        # Split a participant/actor declaration at ` as ` so only the id side is
        # renamed; everything else (messages, notes) is renamed whole.
        m = _ALIAS_SPLIT_RE.match(line)
        if m:
            out.append(_rename(m.group("head")) + m.group("sep") + m.group("alias"))
        else:
            out.append(_rename(line))
    return "\n".join(out)


def validate_text(text: str) -> list[tuple[int, str]]:
    """Return sorted (line, message) findings for one document.

    Uses the real mermaid parser (Node backend) per block when available and
    falls back to the pure-Python heuristic when the backend is absent or
    cannot set up.
    """
    findings: list[tuple[int, str]] = []
    for start_line, body in _iter_mermaid_blocks(text):
        via_backend = _validate_block_via_backend(start_line, body)
        if via_backend is not None:
            findings.extend(via_backend)
            continue
        dtype = _block_diagram_type(body).lower()
        if dtype.startswith("sequencediagram"):
            findings.extend(_check_sequence_block(start_line, body))
    return sorted(findings)


def fix_text(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Apply deterministic repairs to every mermaid block; return (new_text,
    remaining findings after the repair)."""
    out = []
    i = 0
    raw = text.splitlines()
    while i < len(raw):
        if raw[i].strip().lower().startswith("```mermaid"):
            out.append(raw[i])
            j = i + 1
            body = []
            while j < len(raw) and not raw[j].strip().startswith("```"):
                body.append(raw[j])
                j += 1
            fixed_body = _fix_block("\n".join(body))
            out.extend(fixed_body.splitlines())
            if j < len(raw):
                out.append(raw[j])  # closing fence
            i = j + 1
        else:
            out.append(raw[i])
            i += 1
    new_text = "\n".join(out)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, validate_text(new_text)


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}:{line}: {msg}" for line, msg in validate_text(text)]


def main(argv: list[str]) -> int:
    fix = "--fix" in argv
    paths = [a for a in argv if a != "--fix"]
    failures: list[str] = []
    for arg in paths:
        p = Path(arg)
        if not p.is_file():
            continue
        if fix:
            new_text, remaining = fix_text(p.read_text(encoding="utf-8"))
            p.write_text(new_text, encoding="utf-8")
            failures.extend(f"{p}:{line}: {msg}" for line, msg in remaining)
        else:
            failures.extend(validate_file(p))

    if failures:
        print("Invalid mermaid diagram(s) found:\n", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(
            f"\n{len(failures)} finding(s). Fix the diagram(s) above; for full "
            "grammar coverage run mermaid-cli (mmdc).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
