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


def validate_text(text: str) -> list[tuple[int, str]]:
    """Return a sorted list of (line, message) findings for one document."""
    findings: list[tuple[int, str]] = []
    for start_line, body in _iter_mermaid_blocks(text):
        dtype = _block_diagram_type(body).lower()
        if dtype.startswith("sequencediagram"):
            findings.extend(_check_sequence_block(start_line, body))
        # Flowchart/other types: block-balance only (semicolons are legal in
        # flowcharts), kept conservative to avoid false positives.
    return sorted(findings)


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}:{line}: {msg}" for line, msg in validate_text(text)]


def main(argv: list[str]) -> int:
    failures: list[str] = []
    for arg in argv:
        p = Path(arg)
        if not p.is_file():
            continue
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
