# Mermaid Diagram Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate Mermaid diagrams with the real parser, auto-repair the common breakages, and catch them at authoring time so invalid diagrams never ship.

**Architecture:** A Python orchestrator (`validate_mermaid.py`, already present from PR #69) extracts ```mermaid blocks and validates each one. When Node is available it shells out to `validate_mermaid.mjs`, which runs the authoritative `mermaid.parse()` (syntax-only, no Chromium); otherwise it falls back to the existing pure-Python heuristic. A deterministic `--fix` repairs known classes. The doc-authoring skills validate before writing and a style guide prevents bad generation up front.

**Tech Stack:** Python 3.11+ (stdlib only, run via `uv`), Node 25 + `mermaid@10` + `jsdom` (run via `npx --yes --package`), pre-commit, pytest.

---

## Context the engineer needs

- **Branch:** all work lands on `feat/shield-mermaid-validation` (PR #69). Do NOT branch off `main`.
- **Match the renderer:** `shield/templates/shell.html:11` loads `mermaid@10` from jsdelivr. The Node parser MUST pin the same major (`mermaid@10`) so we validate against what users render. If `shell.html` ever bumps to `@11`, the pin moves with it (Task 11 adds a test guarding this).
- **Existing script (PR #69):** `shield/scripts/validate_mermaid.py` exposes `validate_text(text) -> list[(line, msg)]`, `validate_file(path) -> list[str]`, `_iter_mermaid_blocks(text)` (yields `(start_line_1based, body_lines)`), `_check_sequence_block(...)`, `RESERVED_ACTOR_WORDS`, `BLOCK_OPENERS`, and `main(argv)`. Its pytest is `shield/scripts/test_validate_mermaid.py`.
- **Test corpus:** the real LLDs. RED = the pre-fix diagrams (`git show docs/lld-component-backfill~1:docs/lld/<c>.md`); GREEN = the post-fix diagrams (`git show docs/lld-component-backfill:docs/lld/<c>.md`). Phase 1/2 tests embed small inline fixtures rather than depending on those paths, but you can sanity-check against them.
- **Run tests:** `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py`.
- **Determinism:** the Node backend needs `npx` to resolve `mermaid` (may hit the network on first run). All pure-Python logic (extraction, line-mapping, `--fix`, error parsing, fallback) is tested without Node. The one live-Node integration test is guarded with `skipif` so CI without network/mermaid still passes.

---

## File Structure

- Create: `shield/scripts/validate_mermaid.mjs` — Node parse backend (stdin → exit 0/1/2).
- Modify: `shield/scripts/validate_mermaid.py` — add Node backend integration, line-mapping, `--fix`.
- Modify: `shield/scripts/test_validate_mermaid.py` — tests for backend integration, line-mapping, `--fix`, fallback.
- Modify: `.pre-commit-config.yaml` — backend already covered by existing hook; add `--fix` hook (Phase 2).
- Create: `shield/skills/general/mermaid-authoring.md` — prevention style guide (Phase 3).
- Modify: `shield/skills/general/lld-docs/SKILL.md` — validate-before-write contract (Phase 3).
- Modify: `shield/skills/general/prd-docs/SKILL.md`, `shield/skills/general/plan-docs/SKILL.md`, `shield/agents/architect.md` — reference the style guide (Phase 3).
- Create: `shield/scripts/test_mermaid_authoring_wiring.py` — eval that the guide exists and is referenced (Phase 3).

---

# Phase 1 — Real parser backend + fallback

## Task 1: Spike — prove `mermaid.parse()` runs headless

**Files:**
- Create (temporary, not committed): `/tmp/spike.mjs`

- [ ] **Step 1: Write the spike script**

```javascript
// /tmp/spike.mjs
import { JSDOM } from "jsdom";
const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.navigator = dom.window.navigator;
const { default: mermaid } = await import("mermaid");
mermaid.initialize({ startOnLoad: false });
const ok = "sequenceDiagram\n  A->>B: hi\n";
const bad = "sequenceDiagram\n  A->>B: a; b\n";
try { await mermaid.parse(ok); console.log("OK parsed clean"); } catch (e) { console.log("OK FAILED:", e.message); }
try { await mermaid.parse(bad); console.log("BAD parsed clean (unexpected)"); } catch (e) { console.log("BAD rejected:", e.message.split("\n")[0]); }
```

- [ ] **Step 2: Run it**

Run: `npx --yes --package mermaid@10 --package jsdom node /tmp/spike.mjs`
Expected: `OK parsed clean` and `BAD rejected: ...`. This confirms jsdom is sufficient and no Chromium is needed.

- [ ] **Step 3: Record the outcome**

If both lines print as expected, proceed to Task 2 using this exact setup. If `mermaid.parse` throws on the *valid* diagram (setup/DOM problem), note the error; the backend (Task 2) wraps setup failures as exit code 2 so the orchestrator falls back to the heuristic — the plan still holds, but flag it for review before relying on the Node path. No commit.

## Task 2: Node backend script

**Files:**
- Create: `shield/scripts/validate_mermaid.mjs`

- [ ] **Step 1: Write the backend**

```javascript
#!/usr/bin/env node
// Validate ONE mermaid diagram read from stdin with the real parser.
// Exit codes: 0 = valid, 1 = syntax error (message on stderr),
//             2 = backend/setup failure (caller should fall back).
// Syntax-only: mermaid.parse() needs a DOM (jsdom) but NOT headless Chromium.
let mermaid;
try {
  const { JSDOM } = await import("jsdom");
  const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  globalThis.navigator = dom.window.navigator;
  mermaid = (await import("mermaid")).default;
  mermaid.initialize({ startOnLoad: false });
} catch (e) {
  process.stderr.write("backend-setup-failure: " + (e?.message ?? e));
  process.exit(2);
}

let input = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) input += chunk;

try {
  await mermaid.parse(input);
  process.exit(0);
} catch (err) {
  process.stderr.write(String(err?.message ?? err));
  process.exit(1);
}
```

- [ ] **Step 2: Smoke-test it manually**

Run: `printf 'sequenceDiagram\n  A->>B: a; b\n' | npx --yes --package mermaid@10 --package jsdom node shield/scripts/validate_mermaid.mjs; echo "exit=$?"`
Expected: a parse-error message on stderr and `exit=1`.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/validate_mermaid.mjs
git commit -m "feat(shield): mermaid.parse() Node backend for validate_mermaid"
```

## Task 3: Parse mermaid's error message into (line, text)

**Files:**
- Modify: `shield/scripts/validate_mermaid.py`
- Test: `shield/scripts/test_validate_mermaid.py`

- [ ] **Step 1: Write the failing test**

```python
from validate_mermaid import _parse_node_error

def test_parse_node_error_extracts_block_line():
    stderr = "Parse error on line 3:\n... -->> ...\nExpecting 'X', got ';'"
    line, msg = _parse_node_error(stderr)
    assert line == 3
    assert "Parse error" in msg

def test_parse_node_error_defaults_line_to_one():
    line, msg = _parse_node_error("Lexical error: something")
    assert line == 1
    assert "Lexical error" in msg
```

- [ ] **Step 2: Run it, verify it fails**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py::test_parse_node_error_extracts_block_line -v`
Expected: FAIL with `ImportError: cannot import name '_parse_node_error'`.

- [ ] **Step 3: Implement `_parse_node_error`**

Add to `validate_mermaid.py`:

```python
import re as _re

_NODE_LINE_RE = _re.compile(r"line\s+(\d+)", _re.IGNORECASE)


def _parse_node_error(stderr: str) -> tuple[int, str]:
    """Map a mermaid.parse() error to a 1-based block line and a one-line message."""
    text = stderr.strip()
    m = _NODE_LINE_RE.search(text)
    block_line = int(m.group(1)) if m else 1
    first_line = text.splitlines()[0] if text else "mermaid parse error"
    return block_line, first_line
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k parse_node_error -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/validate_mermaid.py shield/scripts/test_validate_mermaid.py
git commit -m "feat(shield): parse mermaid backend errors into (line, message)"
```

## Task 4: Node availability + per-block backend call

**Files:**
- Modify: `shield/scripts/validate_mermaid.py`
- Test: `shield/scripts/test_validate_mermaid.py`

- [ ] **Step 1: Write the failing test (pure, no Node needed)**

```python
import validate_mermaid as vm

def test_validate_block_uses_backend_when_available(monkeypatch):
    # Backend reports a syntax error on block-line 2.
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_run_node_backend", lambda body: (1, "Parse error on line 2:\n..."))
    findings = vm._validate_block_via_backend(start_line=10, body=["sequenceDiagram", "A->>B: a; b"])
    assert findings == [(11, "Parse error on line 2:")]

def test_validate_block_backend_ok_returns_no_findings(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_run_node_backend", lambda body: (0, ""))
    assert vm._validate_block_via_backend(10, ["sequenceDiagram", "A->>B: ok"]) == []

def test_validate_block_backend_setup_failure_returns_none(monkeypatch):
    # Exit 2 => caller must fall back; signalled by returning None.
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_run_node_backend", lambda body: (2, "backend-setup-failure: x"))
    assert vm._validate_block_via_backend(10, ["sequenceDiagram"]) is None
```

- [ ] **Step 2: Run it, verify it fails**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k validate_block -v`
Expected: FAIL with `AttributeError`/`ImportError` on the new names.

- [ ] **Step 3: Implement the backend caller**

Add to `validate_mermaid.py`:

```python
import shutil
import subprocess

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
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k validate_block -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/validate_mermaid.py shield/scripts/test_validate_mermaid.py
git commit -m "feat(shield): per-block mermaid backend call with fallback signal"
```

## Task 5: Wire backend into `validate_text` with heuristic fallback

**Files:**
- Modify: `shield/scripts/validate_mermaid.py`
- Test: `shield/scripts/test_validate_mermaid.py`

- [ ] **Step 1: Write the failing test**

```python
import validate_mermaid as vm

def _doc(body):
    return "# d\n\n```mermaid\n" + body + "\n```\n"

def test_validate_text_falls_back_to_heuristic_without_node(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)
    findings = vm.validate_text(_doc("sequenceDiagram\n    A->>B: a; b"))
    assert len(findings) == 1
    assert "statement separator" in findings[0][1]

def test_validate_text_prefers_backend_when_available(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_validate_block_via_backend",
                        lambda start, body: [(start + 1, "Parse error on line 2:")])
    findings = vm.validate_text(_doc("sequenceDiagram\n    A->>B: whatever"))
    assert findings and "Parse error" in findings[0][1]

def test_validate_text_backend_none_falls_back(monkeypatch):
    # Backend present but setup-failed (returns None) → heuristic runs.
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_validate_block_via_backend", lambda start, body: None)
    findings = vm.validate_text(_doc("sequenceDiagram\n    A->>B: a; b"))
    assert any("statement separator" in m for _, m in findings)
```

- [ ] **Step 2: Run it, verify it fails**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k validate_text -v`
Expected: FAIL — current `validate_text` ignores the backend.

- [ ] **Step 3: Rewrite `validate_text` to prefer the backend**

Replace the existing `validate_text` body with:

```python
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
```

- [ ] **Step 4: Run the whole suite, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py`
Expected: all pass (existing heuristic tests still pass because they don't set `_node_available` → it returns False in a no-Node test env; if the env HAS node, see Task 6 which makes the heuristic tests robust).

- [ ] **Step 5: Make existing heuristic tests deterministic**

The PR #69 tests assert exact heuristic messages. With a real Node env they would now hit the backend. Add an autouse fixture at the TOP of `test_validate_mermaid.py` so heuristic-specific tests force the fallback:

```python
import pytest
import validate_mermaid as vm

@pytest.fixture(autouse=True)
def _force_heuristic(monkeypatch, request):
    # Tests tagged @pytest.mark.backend opt back into the real backend.
    if "backend" not in request.keywords:
        monkeypatch.setattr(vm, "_node_available", lambda: False)
```

(Remove any now-redundant `monkeypatch.setattr(vm, "_node_available", ...)` calls in the fallback tests — the fixture handles it. Keep the explicit `lambda: True` in backend-preference tests and mark them `@pytest.mark.backend`.)

- [ ] **Step 6: Run suite again, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add shield/scripts/validate_mermaid.py shield/scripts/test_validate_mermaid.py
git commit -m "feat(shield): validate mermaid via real parser, heuristic fallback"
```

## Task 6: Live backend integration test (guarded)

**Files:**
- Test: `shield/scripts/test_validate_mermaid.py`

- [ ] **Step 1: Add a skip-guarded live test**

```python
import validate_mermaid as vm

def _backend_smoke_ok() -> bool:
    if not vm._node_available():
        return False
    code, _ = vm._run_node_backend("sequenceDiagram\n  A->>B: ok\n")
    return code == 0

@pytest.mark.backend
@pytest.mark.skipif(not _backend_smoke_ok(), reason="node/mermaid backend unavailable")
def test_real_backend_catches_semicolon():
    findings = vm.validate_text("```mermaid\nsequenceDiagram\n  A->>B: a; b\n```\n")
    assert findings, "real parser should reject ';' in a sequence message"

@pytest.mark.backend
@pytest.mark.skipif(not _backend_smoke_ok(), reason="node/mermaid backend unavailable")
def test_real_backend_accepts_valid():
    assert vm.validate_text("```mermaid\nsequenceDiagram\n  A->>B: ok\n```\n") == []
```

- [ ] **Step 2: Register the marker**

Create `shield/scripts/pytest.ini` if absent (else append under `[pytest]`):

```ini
[pytest]
markers =
    backend: tests that require the live Node mermaid backend
```

- [ ] **Step 3: Run it**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k real_backend -v`
Expected: 2 passed (if Node+mermaid resolve) or 2 skipped (if not). Either is green.

- [ ] **Step 4: Commit**

```bash
git add shield/scripts/test_validate_mermaid.py shield/scripts/pytest.ini
git commit -m "test(shield): guarded live mermaid backend integration tests"
```

## Task 7: Confirm pre-commit hook uses the upgraded validator

**Files:**
- Modify: `.pre-commit-config.yaml` (only if the entry needs changing)

- [ ] **Step 1: Verify the existing hook still works end-to-end**

The PR #69 hook `shield-mermaid-validate` runs `python3 shield/scripts/validate_mermaid.py` on changed markdown. No entry change is needed — the script now auto-detects Node. Confirm:

Run: `printf '# x\n\n```mermaid\nsequenceDiagram\n  A->>B: a; b\n```\n' > /tmp/bad.md && python3 shield/scripts/validate_mermaid.py /tmp/bad.md; echo "exit=$?"`
Expected: a finding printed and `exit=1` (via backend if Node present, else heuristic).

- [ ] **Step 2: Run the hook directly**

Run: `pre-commit run shield-mermaid-validate --files /tmp/bad.md`
Expected: the hook FAILS (reports the finding).

- [ ] **Step 3: No commit needed** unless the entry changed. If you adjusted `.pre-commit-config.yaml`, commit it:

```bash
git add .pre-commit-config.yaml
git commit -m "chore(shield): confirm mermaid hook uses real-parser validator"
```

---

# Phase 2 — Deterministic `--fix`

## Task 8: `--fix` transforms for known classes

**Files:**
- Modify: `shield/scripts/validate_mermaid.py`
- Test: `shield/scripts/test_validate_mermaid.py`

- [ ] **Step 1: Write the failing tests**

```python
import validate_mermaid as vm

def test_fix_replaces_semicolon_with_dash():
    block = "sequenceDiagram\n    A->>B: a; b"
    fixed = vm._fix_block(block)
    assert ";" not in fixed
    assert "a — b" in fixed

def test_fix_semicolon_inside_parens_uses_comma():
    block = 'sequenceDiagram\n    A->>B: f(x; y)'
    fixed = vm._fix_block(block)
    assert "f(x, y)" in fixed

def test_fix_semicolon_inside_quotes_uses_comma():
    block = 'sequenceDiagram\n    A-->>B: note="a; b"'
    fixed = vm._fix_block(block)
    assert 'note="a, b"' in fixed

def test_fix_renames_reserved_actor_consistently():
    block = ("sequenceDiagram\n"
             "    participant Create as pm_bulk_create\n"
             "    Skill->>Create: stories\n"
             "    Create-->>Skill: done")
    fixed = vm._fix_block(block)
    assert "participant CreateActor as pm_bulk_create" in fixed
    assert "Skill->>CreateActor:" in fixed
    assert "CreateActor-->>Skill:" in fixed
    # the prose alias after `as` is untouched; only the identifier changed
    assert "pm_bulk_create" in fixed
```

- [ ] **Step 2: Run, verify fail**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k fix -v`
Expected: FAIL with `AttributeError: _fix_block`.

- [ ] **Step 3: Implement `_fix_block`**

```python
def _replace_semicolons(line: str) -> str:
    """`;` → `,` when inside () or "", else `—`. Only after the message ':'."""
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
            out.append("," if (in_quote or paren > 0) else "—")
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
    """Apply deterministic repairs to one diagram body (no fence)."""
    # 1. semicolons, line by line.
    lines = [_replace_semicolons(ln) for ln in body.splitlines()]
    fixed = "\n".join(lines)
    # 2. reserved-word actor ids → <Id>Actor, whole-word, across the block.
    for ident in sorted(_reserved_actor_ids(fixed), key=len, reverse=True):
        fixed = _re.sub(rf"(?<![\w]){_re.escape(ident)}(?![\w])", ident + "Actor", fixed)
    return fixed
```

Note: the `as <alias>` text uses different words (e.g. `pm_bulk_create`), so the
whole-word rename of the identifier `Create` does not touch `pm_bulk_create`.

- [ ] **Step 4: Run, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k fix -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/validate_mermaid.py shield/scripts/test_validate_mermaid.py
git commit -m "feat(shield): deterministic --fix transforms for mermaid traps"
```

## Task 9: `--fix` file rewrite + re-validate + CLI flag

**Files:**
- Modify: `shield/scripts/validate_mermaid.py`
- Test: `shield/scripts/test_validate_mermaid.py`

- [ ] **Step 1: Write the failing tests**

```python
import validate_mermaid as vm

def test_fix_text_repairs_and_clears_findings(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)  # heuristic check
    src = "# d\n\n```mermaid\nsequenceDiagram\n    A->>B: a; b\n```\n"
    new_text, remaining = vm.fix_text(src)
    assert ";" not in new_text
    assert remaining == []

def test_fix_text_leaves_unfixable_and_reports(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)
    # unbalanced alt is not a deterministic-fix class
    src = "# d\n\n```mermaid\nsequenceDiagram\n    alt x\n    A->>B: ok\n```\n"
    new_text, remaining = vm.fix_text(src)
    assert any("unbalanced" in m for _, m in remaining)

def test_main_fix_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)
    p = tmp_path / "d.md"
    p.write_text("# d\n\n```mermaid\nsequenceDiagram\n    A->>B: a; b\n```\n")
    rc = vm.main(["--fix", str(p)])
    assert ";" not in p.read_text()
    assert rc == 0  # all clean after fix
```

- [ ] **Step 2: Run, verify fail**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py -k fix_text -v`
Expected: FAIL with `AttributeError: fix_text`.

- [ ] **Step 3: Implement `fix_text` and extend `main`**

Add `fix_text`:

```python
def fix_text(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Apply deterministic repairs to every mermaid block; return (new_text,
    remaining findings after the repair)."""
    lines = text.splitlines(keepends=True)
    # Rebuild the document, swapping each block body for its fixed version.
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
```

Modify `main` to accept `--fix`:

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/validate_mermaid.py shield/scripts/test_validate_mermaid.py
git commit -m "feat(shield): --fix mode rewrites files and re-validates"
```

## Task 10: pre-commit autofix hook

**Files:**
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: Add the autofix hook after `shield-mermaid-validate`**

```yaml
      # ── 9b. mermaid autofix ──────────────────────────────────────────────
      # Repairs the deterministic trap classes (semicolons, reserved-word
      # actors) and fails if it changed anything, so the dev re-stages — the
      # standard pre-commit fixer pattern.
      - id: shield-mermaid-fix
        name: shield mermaid autofix
        entry: python3 shield/scripts/validate_mermaid.py --fix
        language: system
        files: '^(docs/.*|shield/(skills|templates|agents)/.*)\.md$'
```

- [ ] **Step 2: Test it rewrites + fails on a bad file**

```bash
printf '# x\n\n```mermaid\nsequenceDiagram\n  A->>B: a; b\n```\n' > /tmp/fixme.md
pre-commit run shield-mermaid-fix --files /tmp/fixme.md; echo "exit=$?"
grep -q ';' /tmp/fixme.md && echo "STILL BAD" || echo "REPAIRED"
```

Expected: hook reports a change/fails on first run; `REPAIRED` printed (the `;` is gone).

- [ ] **Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "feat(shield): pre-commit mermaid autofix hook"
```

---

# Phase 3 — Author-time validation + prevention

## Task 11: `mermaid-authoring.md` style guide + renderer-pin guard

**Files:**
- Create: `shield/skills/general/mermaid-authoring.md`
- Test: `shield/scripts/test_mermaid_authoring_wiring.py`

- [ ] **Step 1: Write the style guide**

```markdown
# Mermaid authoring

Shared rules for any Shield skill that emits a Mermaid diagram (LLDs, TRDs,
PRDs, architecture diagrams). Diagrams are validated by
`shield/scripts/validate_mermaid.py` against `mermaid@10` (the version
`shield/templates/shell.html` renders with). Following these rules avoids the
failures that validator catches.

## Hard rules (these break parsing)

- **No semicolons inside a `sequenceDiagram`.** Mermaid treats `;` as a
  statement separator, so text after it is re-parsed as a new line — even
  inside quotes or parentheses. Use `—`, or `,` inside `()`/`""`.
- **Never name an actor/participant a reserved word.** Reserved:
  `create`, `destroy`, `box`, `end`, `alt`, `else`, `opt`, `loop`, `par`,
  `and`, `critical`, `rect`, `break`, `note`, `activate`, `deactivate`,
  `participant`, `actor`, `autonumber`, `link`, `links`, `title`. Rename the
  identifier (the `as <alias>` text is free-form and may keep the real name).
- **Balance every block.** Each `alt`/`loop`/`opt`/`par`/`critical`/`rect`/
  `break`/`box` needs a matching `end`.

## Style (keeps diagrams parseable and readable)

- Keep message labels short; put detail in the prose around the diagram.
- Prefer simple identifiers (`A`, `Svc`, `DB`) with `as` aliases for display.
- One journey per diagram; split large flows.
```

- [ ] **Step 2: Write the wiring test (failing)**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root from shield/scripts/

def test_style_guide_exists():
    assert (ROOT / "shield/skills/general/mermaid-authoring.md").is_file()

def test_renderer_and_validator_pin_same_major():
    shell = (ROOT / "shield/templates/shell.html").read_text()
    validator = (ROOT / "shield/scripts/validate_mermaid.py").read_text()
    assert "mermaid@10" in shell        # renderer CDN pin
    assert 'mermaid@10' in validator    # _NODE_MERMAID_PKG pin

def test_emitting_skills_reference_style_guide():
    for rel in [
        "shield/skills/general/lld-docs/SKILL.md",
        "shield/skills/general/prd-docs/SKILL.md",
        "shield/skills/general/plan-docs/SKILL.md",
        "shield/agents/architect.md",
    ]:
        assert "mermaid-authoring" in (ROOT / rel).read_text(), rel
```

- [ ] **Step 3: Run, verify fail**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_mermaid_authoring_wiring.py -v`
Expected: `test_style_guide_exists` passes; the reference test FAILS (skills not yet wired).

- [ ] **Step 4: Commit the guide + test**

```bash
git add shield/skills/general/mermaid-authoring.md shield/scripts/test_mermaid_authoring_wiring.py
git commit -m "feat(shield): mermaid-authoring style guide + wiring test"
```

## Task 12: Reference the style guide from emitting skills

**Files:**
- Modify: `shield/skills/general/lld-docs/SKILL.md`
- Modify: `shield/skills/general/prd-docs/SKILL.md`
- Modify: `shield/skills/general/plan-docs/SKILL.md`
- Modify: `shield/agents/architect.md`

- [ ] **Step 1: Add a reference line to each**

In each file, under the section that discusses diagrams/architecture (search for an existing `architecture-authoring` reference and add alongside it), add:

```markdown
When emitting Mermaid diagrams, follow `shield/skills/general/mermaid-authoring.md`
(hard syntax rules — no semicolons, no reserved-word actors, balanced blocks).
```

- [ ] **Step 2: Run the wiring test, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_mermaid_authoring_wiring.py -v`
Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/lld-docs/SKILL.md shield/skills/general/prd-docs/SKILL.md shield/skills/general/plan-docs/SKILL.md shield/agents/architect.md
git commit -m "feat(shield): reference mermaid-authoring guide from emitting skills"
```

## Task 13: lld-docs validate-before-write contract

**Files:**
- Modify: `shield/skills/general/lld-docs/SKILL.md`
- Test: `shield/scripts/test_mermaid_authoring_wiring.py`

- [ ] **Step 1: Write the failing contract test**

```python
def test_lld_docs_has_validate_before_write_contract():
    text = (ROOT / "shield/skills/general/lld-docs/SKILL.md").read_text()
    assert "validate_mermaid.py" in text
    # The contract must require validate → fix → agent-repair before the write.
    assert "before" in text.lower() and "write" in text.lower()
    assert "--fix" in text
```

- [ ] **Step 2: Run, verify fail**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_mermaid_authoring_wiring.py -k validate_before_write -v`
Expected: FAIL.

- [ ] **Step 3: Add the contract to lld-docs SKILL.md**

In the "Atomic write contract" section, add a new numbered step before the write:

```markdown
## Mermaid validation (before write)

Before the atomic write, validate every ```mermaid block:

1. Run `python3 shield/scripts/validate_mermaid.py <target>.tmp` (or validate
   the composed content). If it passes, proceed to the write.
2. If it fails, run `python3 shield/scripts/validate_mermaid.py --fix <target>.tmp`
   to repair the deterministic classes, then re-validate.
3. If findings remain, rewrite the offending diagram from the parse error,
   re-validate, and retry (bounded — 3 attempts). Never write a file whose
   diagrams do not validate.

Diagram syntax rules: `shield/skills/general/mermaid-authoring.md`.
```

- [ ] **Step 4: Run, verify pass**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_mermaid_authoring_wiring.py`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/lld-docs/SKILL.md shield/scripts/test_mermaid_authoring_wiring.py
git commit -m "feat(shield): lld-docs validates mermaid before write"
```

## Task 14: Wire the new pytest files into pre-commit

**Files:**
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: Extend the mermaid pytest hook to cover the wiring test**

Update the `shield-mermaid-tests` hook so it also runs the wiring test and triggers on the relevant assets:

```yaml
      - id: shield-mermaid-tests
        name: shield validate-mermaid pytest
        entry: bash -c 'cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py test_mermaid_authoring_wiring.py'
        language: system
        files: '^(shield/scripts/(validate_mermaid|test_validate_mermaid|test_mermaid_authoring_wiring)\.py|shield/skills/general/(mermaid-authoring\.md|lld-docs/SKILL\.md|prd-docs/SKILL\.md|plan-docs/SKILL\.md)|shield/agents/architect\.md|shield/templates/shell\.html)$'
        pass_filenames: false
```

- [ ] **Step 2: Run the hook**

Run: `pre-commit run shield-mermaid-tests --all-files`
Expected: Passed.

- [ ] **Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore(shield): run mermaid wiring tests in pre-commit"
```

## Task 15: Re-confirm version bump + full suite

**Files:**
- Verify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Confirm the shield version bump is present**

Run: `grep -A2 '"name": "shield"' .claude-plugin/marketplace.json | grep version`
Expected: `"version": "2.28.0"` (bumped on the branch in PR #69). If still `2.27.0`, bump it and commit.

- [ ] **Step 2: Run every mermaid test + the heuristic suite**

Run: `cd shield/scripts && uv run --quiet --with pytest pytest test_validate_mermaid.py test_mermaid_authoring_wiring.py -v`
Expected: all pass (live-backend tests pass or skip).

- [ ] **Step 3: Validate all real docs end-to-end**

Run: `python3 shield/scripts/validate_mermaid.py docs/lld/*.md`
Expected: exit 0 (the 17 fixed diagrams all pass under the real parser).

- [ ] **Step 4: Final commit if anything changed**

```bash
git add -A && git commit -m "chore(shield): confirm mermaid version bump and full-suite green" || echo "nothing to commit"
```

---

## Self-review notes (for the implementer)

- **Spec coverage:** Goal 1 (complete coverage) → Tasks 2–7; Goal 3 (auto-repair) → Tasks 8–10; Goal 2 + agent repair → Task 13; Goal 4 (prevent) → Tasks 11–12. Fallback (non-goal: no hard Node dep) → Tasks 4–6. Version/eval mandate → Tasks 11–15.
- **Type consistency:** function names used across tasks — `_parse_node_error`, `_node_available`, `_run_node_backend`, `_validate_block_via_backend`, `validate_text`, `_fix_block`, `_replace_semicolons`, `_reserved_actor_ids`, `fix_text`, `main` — are defined once and referenced consistently.
- **Pin coupling:** `mermaid@10` appears in both `shell.html` (renderer) and `_NODE_MERMAID_PKG` (validator); Task 11's `test_renderer_and_validator_pin_same_major` guards drift.
```
