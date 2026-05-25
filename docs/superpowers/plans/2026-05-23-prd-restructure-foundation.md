# PRD Restructure — Foundation (Plan 1 of 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic foundation (project skill + 11 scripts + dim-section map) that the next plan will consume. Existing `/prd` and `/prd-review` remain unchanged when this plan ships.

**Architecture:** A repo-scoped project skill at `.claude/skills/script-llm-contract/` codifies the LLM↔script contract. 11 scripts live at `shield/scripts/prd/` — each is a `.sh` wrapper around a `.py` implementation (matching the existing `render-markdown.sh` + `render-markdown.py` pattern). Every script emits a JSON envelope on stdout and signals categories via exit code 0/1/2/3/4/5 per the contract. A `dim-section-map.yaml` at `shield/skills/general/prd/` is the single source of truth shared by `sparse-sections.sh` and `map-gaps-to-sections.sh`.

**Tech Stack:** Bash wrappers; Python 3.11+ via `uv run --quiet --with <deps>`; pytest for unit tests; PyYAML for config; standard library elsewhere.

**Spec source:** `docs/superpowers/specs/2026-05-23-prd-and-prd-review-restructure-design.md` (sections 11, 12 — Scripts and Script-LLM contract).

---

## File Structure

**Creates:**

```
.claude/skills/script-llm-contract/
├── SKILL.md                              ← contract description + walked example + checklist
└── evals/
    ├── script-exit-code-contract.eval.md
    ├── script-no-prompting.eval.md
    └── proactive-script-suggestion.eval.md

shield/skills/general/prd/
└── dim-section-map.yaml                  ← config consumed by sparse-sections.sh + map-gaps-to-sections.sh

shield/scripts/prd/
├── prd-ingest.sh                         ← shell wrapper
├── prd_ingest.py                         ← impl
├── detect-prd-type.sh
├── detect_prd_type.py
├── next-review-dir.sh
├── next_review_dir.py
├── extract-glossary-candidates.sh
├── extract_glossary_candidates.py
├── count-term-in-body.sh
├── count_term_in_body.py
├── sparse-sections.sh
├── sparse_sections.py
├── map-gaps-to-sections.sh
├── map_gaps_to_sections.py
├── aggregate-review.sh
├── aggregate_review.py
├── filter-low-confidence.sh
├── filter_low_confidence.py
├── update-manifest.sh
├── update_manifest.py
├── finalize-prd.sh
├── finalize_prd.py
├── _contract.py                          ← shared envelope helpers (exit codes + JSON shapes)
├── test_contract.py
├── test_prd_ingest.py
├── test_detect_prd_type.py
├── test_next_review_dir.py
├── test_extract_glossary_candidates.py
├── test_count_term_in_body.py
├── test_sparse_sections.py
├── test_map_gaps_to_sections.py
├── test_aggregate_review.py
├── test_filter_low_confidence.py
├── test_update_manifest.py
└── test_finalize_prd.py
```

**Modifies:** none in this plan (Plan 2 wires consumers).

**Convention reminders:**
- All scripts use `set -euo pipefail` and check for `uv` (exit 127 with installer hint per `render-markdown.sh`).
- All Python scripts begin with `from __future__ import annotations`.
- All scripts emit JSON to stdout; never to stderr. Errors are also JSON on stdout; exit code carries the category.
- Tests run via `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_<name>.py -v` (plus any extra deps the script declares).

---

## Task 1: Create `.claude/skills/script-llm-contract/SKILL.md`

**Files:**
- Create: `.claude/skills/script-llm-contract/SKILL.md`

- [ ] **Step 1: Write the skill file**

Write the following to `.claude/skills/script-llm-contract/SKILL.md`:

````markdown
---
name: script-llm-contract
description: Use when (a) editing a SKILL.md that calls Bash helper scripts, (b) designing a new plugin command or skill, or (c) proactively when writing or reviewing any new skill — scan the workflow for deterministic steps coded as LLM-only and suggest scripts. Codifies the exit-code-driven contract between LLM orchestrators and deterministic scripts used across tesseract plugins.
---

# Script-LLM Contract

## When to use

- **Auto-invoke** when editing a `SKILL.md` whose workflow includes Bash invocations of helper scripts — to ensure exit-code branches and JSON payload handling are wired correctly.
- **Auto-invoke** when designing a new plugin command or skill — to flag deterministic steps for scriptification.
- **Proactive:** when writing or reviewing any new skill — scan the workflow for deterministic steps coded as LLM-only and suggest scripts even if the contributor didn't ask.

## When NOT to use

- Editing a SKILL.md that is purely LLM-driven (no script invocations and no candidate deterministic steps).
- Editing a script that is not invoked by an LLM orchestrator (e.g., a CI-only script).

## The contract

1. **Scripts never prompt.** All inputs come from args or stdin. If a script needs a human decision (e.g., MCP not authenticated, ambiguous resolver match), it exits with code 4 (`needs-human`) and emits a JSON payload telling the LLM what to ask.
2. **Scripts emit JSON on stdout.** Success or failure, the payload is structured. Never write status text to stderr that the LLM must parse — stderr is for human-readable warnings only.
3. **Exit codes carry category.** The LLM branches on `$?`, not on stderr scraping.
4. **Scripts are idempotent and safe to retry** within an error category. A retried `prd-ingest.sh` produces the same output (or the same error) given the same inputs and external state.

## Exit code table

| Code | Category | LLM behavior |
|---|---|---|
| 0 | success | Use stdout payload, continue. |
| 1 | unexpected internal | Surface to user; do NOT retry. |
| 2 | invalid input | Caller bug. LLM re-examines inputs; never auto-retry the same call. |
| 3 | external resource unavailable | Transient. LLM may retry, prompt user, or fall back per `suggested_action`. |
| 4 | needs human input | LLM asks user the question in the payload, then re-invokes with chosen path. |
| 5 | partial success | LLM reviews `partial:` payload; decides re-dispatch / accept / escalate. |

## Output envelope

**Success:**

```json
{"ok": true, "data": {...}}
```

**Error (any non-zero exit):**

```json
{
  "ok": false,
  "code": 3,
  "category": "external_resource_unavailable",
  "resource": "notion_mcp",
  "reason": "401 unauthorized",
  "suggested_action": "ask_user_to_run_mcp_connect",
  "fallback": "webfetch_with_paste_prompt"
}
```

`suggested_action` and `fallback` are advisory. The LLM decides.

## Walked example

```
LLM: prd-ingest.sh "https://notion.so/page-abc"
  ↓
Script:
  - classify: notion URL
  - try notion MCP resolver
  - MCP returns 401 unauthorized
  - exit 3 with:
    {"ok":false,"code":3,"category":"external_resource_unavailable",
     "resource":"notion_mcp","reason":"401 unauthorized",
     "suggested_action":"ask_user_to_authenticate_notion_mcp",
     "fallback":"webfetch"}
  ↓
LLM reads code=3:
  a. Try fallback "webfetch" silently — invoke prd-ingest.sh --resolver webfetch <url>
     → success (exit 0) → continue with content.
     → failure (exit 3 again) → fall through to (b).
  b. Ask user per script's suggested_action:
     "Notion isn't connected. Want to (1) run /mcp connect notion,
      (2) paste the content, or (3) abort?"
     User picks → LLM re-invokes with the chosen resolver.
```

## Checklist for skill authors

For each LLM step in your SKILL.md workflow, ask:

- **Is this step deterministic given fixed inputs?** If yes → script.
- **Does this step parse structured data?** (JSON / YAML / counts / regex matches) If yes → script.
- **Does this step compute a path / counter / hash?** If yes → script.
- **Does this step interact with an external API where retries should be policy-driven, not LLM-improvised?** If yes → script.
- **Does this step need to be replayable / auditable?** If yes → script.

If you answer yes to any of these and the step is currently LLM-only, propose a script with the contract above.

## Common mistakes

| Mistake | Fix |
|---|---|
| Script prompts the user via `read` or `input()` | Replace with exit 4 + payload telling LLM what to ask. |
| Script catches errors and exits 0 with `"ok":true` | The LLM trusts exit code. Hidden failures break retries. Exit non-zero with the proper category. |
| Script retries internally with backoff and hides transients from the LLM | Move retry policy to the LLM. Script signals exit 3; LLM decides. |
| Script writes status to stderr that the LLM must parse | Move status to JSON stdout. Stderr is human warnings only. |
| Script depends on cwd or env vars not declared in args | All inputs explicit. Tests must pass without any environmental setup beyond the declared args. |
| Skill author scriptifies the synthesis step (e.g., the LLM rewrite itself) | Scripts handle deterministic glue. Don't replace LLM judgment calls with brittle string templates. |
````

- [ ] **Step 2: Verify the file renders as expected markdown**

Run: `head -5 .claude/skills/script-llm-contract/SKILL.md`
Expected: shows the YAML frontmatter starting with `---`, `name: script-llm-contract`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/script-llm-contract/SKILL.md
git commit -m "feat(skill): add script-llm-contract project skill

Codifies the exit-code-driven contract between LLM orchestrators and
deterministic scripts. Auto-invokes when editing SKILL.md files that
call scripts, when designing new plugin skills, and proactively when
reviewing skills with LLM-only deterministic steps."
```

---

## Task 2: Create `shield/skills/general/prd/dim-section-map.yaml`

This file is the SSoT used by `sparse-sections.sh` and `map-gaps-to-sections.sh`. It exists in the `prd/` directory (which will become the consolidated skill in Plan 2; creating only the YAML here keeps Plan 1 self-contained).

**Files:**
- Create: `shield/skills/general/prd/dim-section-map.yaml`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p shield/skills/general/prd
```

- [ ] **Step 2: Write the YAML**

Write the following to `shield/skills/general/prd/dim-section-map.yaml`:

```yaml
# shield/skills/general/prd/dim-section-map.yaml
#
# Maps reviewer dimensions (rubric.md) to the §s in the new 20-section
# PRD scaffold (templates.md). Scripts read this; LLM prompts reference
# it for context.
#
# Dim IDs match rubric.md. § numbers match templates.md.

dim_section_map:
  1:  [3]            # Problem clarity            → §3 Current context
  2:  [5, 19]        # Scope boundaries           → §5 Goals & non-goals, §19 Out of scope
  3:  [6]            # Measurable success         → §6 Success metrics
  4:  [7]            # Scenario coverage & AC     → §7 User stories
  5:  [9, 10, 11]    # NFR coverage (UX only)     → §9, §10 RBAC, §11 Deps
  6:  [14]           # Rollout & ops              → §14 Rollout plan
  7:  [1, 20]        # RACI & approvals           → §1 Header, §20 Sign-offs
  8:  [9, 12]        # Legal/privacy/compliance   → §9, §12 Risks
  9:  [16]           # GTM / customer-comms       → §16 GTM
  10: [17]           # Support / CX impact        → §17 Support
  11: [3]            # Why now & cost-of-inaction → §3 Current context
  12: [12, 13, 18]   # Risks & assumptions        → §12, §13, §18
  13: [15]           # Cost & resource impact     → §15 Cost estimate (lump only)
  # anti-patterns: cross-cutting, no specific §
```

- [ ] **Step 3: Validate YAML parses**

Run: `uv run --with pyyaml -- python -c "import yaml; print(list(yaml.safe_load(open('shield/skills/general/prd/dim-section-map.yaml'))['dim_section_map'].keys()))"`
Expected output: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]`

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/prd/dim-section-map.yaml
git commit -m "feat(shield): add dim-section-map.yaml SSoT for PRD scripts

Maps the 13 reviewer dimensions to §s in the new 20-section scaffold.
Consumed by sparse-sections.sh and map-gaps-to-sections.sh."
```

---

## Task 3: Build `_contract.py` shared helpers (DRY foundation for all scripts)

Every script emits the same envelope shape and exits with the same code categories. Centralize this once.

**Files:**
- Create: `shield/scripts/prd/_contract.py`
- Create: `shield/scripts/prd/test_contract.py`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p shield/scripts/prd
```

- [ ] **Step 2: Write the failing test for envelope helpers**

Write to `shield/scripts/prd/test_contract.py`:

```python
"""Tests for _contract.py — shared envelope + exit-code helpers.

Runnable: `cd shield/scripts/prd && uv run --with pytest pytest test_contract.py -v`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import (  # type: ignore[import-not-found]
    EXIT_SUCCESS,
    EXIT_INTERNAL,
    EXIT_INVALID_INPUT,
    EXIT_EXTERNAL_UNAVAILABLE,
    EXIT_NEEDS_HUMAN,
    EXIT_PARTIAL,
    emit_success,
    emit_error,
)


def test_exit_codes_are_distinct() -> None:
    codes = {
        EXIT_SUCCESS,
        EXIT_INTERNAL,
        EXIT_INVALID_INPUT,
        EXIT_EXTERNAL_UNAVAILABLE,
        EXIT_NEEDS_HUMAN,
        EXIT_PARTIAL,
    }
    assert len(codes) == 6
    assert EXIT_SUCCESS == 0


def test_emit_success_payload(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        emit_success({"foo": "bar", "count": 3})
    assert exc.value.code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {"ok": True, "data": {"foo": "bar", "count": 3}}


def test_emit_error_with_code_and_category(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        emit_error(
            code=EXIT_EXTERNAL_UNAVAILABLE,
            category="external_resource_unavailable",
            resource="notion_mcp",
            reason="401 unauthorized",
            suggested_action="ask_user_to_run_mcp_connect",
            fallback="webfetch",
        )
    assert exc.value.code == 3
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert payload["code"] == 3
    assert payload["category"] == "external_resource_unavailable"
    assert payload["resource"] == "notion_mcp"
    assert payload["reason"] == "401 unauthorized"
    assert payload["suggested_action"] == "ask_user_to_run_mcp_connect"
    assert payload["fallback"] == "webfetch"


def test_emit_error_minimal_fields(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        emit_error(
            code=EXIT_INVALID_INPUT,
            category="invalid_input",
            reason="missing required arg --source",
        )
    assert exc.value.code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "ok": False,
        "code": 2,
        "category": "invalid_input",
        "reason": "missing required arg --source",
    }
    # Optional fields absent when not supplied.
    assert "resource" not in payload
    assert "suggested_action" not in payload
    assert "fallback" not in payload
```

- [ ] **Step 3: Run the test, verify it fails**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_contract.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named '_contract'`

- [ ] **Step 4: Write the implementation**

Write to `shield/scripts/prd/_contract.py`:

```python
"""Shared envelope + exit-code helpers for all shield/scripts/prd/ scripts.

Implements the contract documented at
`.claude/skills/script-llm-contract/SKILL.md`.

Scripts call `emit_success(data)` or `emit_error(code=…, category=…, …)`
and the helper writes JSON to stdout and calls `sys.exit()` with the
correct code. Callers never construct exit codes or JSON envelopes
themselves — keeps the contract surface small.
"""
from __future__ import annotations

import json
import sys
from typing import Any

EXIT_SUCCESS = 0
EXIT_INTERNAL = 1
EXIT_INVALID_INPUT = 2
EXIT_EXTERNAL_UNAVAILABLE = 3
EXIT_NEEDS_HUMAN = 4
EXIT_PARTIAL = 5


def emit_success(data: Any) -> None:
    """Write success envelope to stdout and exit 0."""
    sys.stdout.write(json.dumps({"ok": True, "data": data}))
    sys.stdout.write("\n")
    sys.exit(EXIT_SUCCESS)


def emit_error(
    *,
    code: int,
    category: str,
    reason: str | None = None,
    resource: str | None = None,
    suggested_action: str | None = None,
    fallback: str | None = None,
    partial: Any = None,
) -> None:
    """Write error envelope to stdout and exit with the given code."""
    payload: dict[str, Any] = {"ok": False, "code": code, "category": category}
    if reason is not None:
        payload["reason"] = reason
    if resource is not None:
        payload["resource"] = resource
    if suggested_action is not None:
        payload["suggested_action"] = suggested_action
    if fallback is not None:
        payload["fallback"] = fallback
    if partial is not None:
        payload["partial"] = partial
    sys.stdout.write(json.dumps(payload))
    sys.stdout.write("\n")
    sys.exit(code)
```

- [ ] **Step 5: Run the test, verify it passes**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_contract.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add shield/scripts/prd/_contract.py shield/scripts/prd/test_contract.py
git commit -m "feat(scripts/prd): add _contract.py envelope + exit-code helpers

DRY foundation for all shield/scripts/prd/ scripts. Implements the
contract documented at .claude/skills/script-llm-contract/SKILL.md."
```

---

<!-- PLAN-CHUNK-1-END -->

## Task 4: Build `prd-ingest.sh` + `prd_ingest.py`

`prd-ingest.sh` classifies the source (local path / URL / stdin paste) and returns normalized markdown. **Scope for Plan 1:** local paths and stdin paste are fully handled. URLs (notion.so, atlassian.net, generic HTTP) exit 4 with a payload telling the LLM which MCP tool or WebFetch path to use, then re-invoke with `--paste-from-stdin`. This keeps the script free of subprocess-MCP coupling while preserving the contract pattern.

**Files:**
- Create: `shield/scripts/prd/prd-ingest.sh`
- Create: `shield/scripts/prd/prd_ingest.py`
- Create: `shield/scripts/prd/test_prd_ingest.py`

- [ ] **Step 1: Write failing test for local-path ingest**

Write to `shield/scripts/prd/test_prd_ingest.py`:

```python
"""Tests for prd_ingest.py.

Runnable: `cd shield/scripts/prd && uv run --with pytest pytest test_prd_ingest.py -v`
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import prd_ingest  # type: ignore[import-not-found]


def _run_main(argv: list[str], stdin: str | None = None) -> tuple[int, dict]:
    """Run prd_ingest.main with argv; capture exit code + parsed stdout JSON."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "prd_ingest.py"), *argv],
        input=stdin,
        capture_output=True,
        text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_local_markdown_file(tmp_path: Path) -> None:
    src = tmp_path / "sample.md"
    src.write_text("# Hello\n\nbody text\n")
    code, payload = _run_main(["--source", str(src)])
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["source_type"] == "local"
    assert payload["data"]["format"] == "markdown"
    assert "# Hello" in payload["data"]["content"]


def test_local_file_missing(tmp_path: Path) -> None:
    code, payload = _run_main(["--source", str(tmp_path / "nope.md")])
    assert code == 2
    assert payload["category"] == "invalid_input"
    assert "not found" in payload["reason"].lower()


def test_notion_url_routes_to_mcp(tmp_path: Path) -> None:
    code, payload = _run_main(["--source", "https://notion.so/page-abc"])
    assert code == 4
    assert payload["category"] == "needs_human"
    assert payload["resource"] == "notion_mcp"
    assert payload["suggested_action"]


def test_atlassian_url_routes_to_mcp(tmp_path: Path) -> None:
    code, payload = _run_main(["--source", "https://acme.atlassian.net/wiki/x"])
    assert code == 4
    assert payload["resource"] == "atlassian_mcp"


def test_generic_url_routes_to_webfetch(tmp_path: Path) -> None:
    code, payload = _run_main(["--source", "https://example.com/page"])
    assert code == 4
    assert payload["resource"] == "webfetch"


def test_paste_from_stdin() -> None:
    code, payload = _run_main(["--paste-from-stdin"], stdin="# Pasted\nbody\n")
    assert code == 0
    assert payload["data"]["source_type"] == "paste"
    assert payload["data"]["content"].startswith("# Pasted")


def test_missing_required_args() -> None:
    code, payload = _run_main([])
    assert code == 2
    assert payload["category"] == "invalid_input"
```

- [ ] **Step 2: Run the test, verify it fails**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_prd_ingest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prd_ingest'`

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/prd_ingest.py`:

```python
"""prd-ingest: classify a PRD source and emit normalized markdown.

Sources:
  --source <local-path>   read + return file content (markdown / text)
  --source <url>          exit 4 with a payload telling the LLM which
                          MCP tool (notion / atlassian) or WebFetch to
                          use, then re-invoke with --paste-from-stdin
  --paste-from-stdin      read stdin, wrap as paste-sourced content
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import (
    EXIT_INVALID_INPUT,
    EXIT_NEEDS_HUMAN,
    emit_error,
    emit_success,
)


MCP_HOSTS = {
    "notion.so": "notion_mcp",
    "www.notion.so": "notion_mcp",
}


def _is_atlassian(host: str) -> bool:
    return host.endswith(".atlassian.net") or host == "atlassian.net"


def _classify_url(url: str) -> tuple[str, str]:
    """Return (resource, suggested_action) for the LLM."""
    host = (urlparse(url).hostname or "").lower()
    if host in MCP_HOSTS:
        return MCP_HOSTS[host], "use_notion_mcp_fetch_then_reinvoke_with_paste"
    if _is_atlassian(host):
        return "atlassian_mcp", "use_atlassian_mcp_fetch_then_reinvoke_with_paste"
    return "webfetch", "use_webfetch_then_reinvoke_with_paste"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--source", help="local path OR url")
    parser.add_argument("--paste-from-stdin", action="store_true")
    args = parser.parse_args(argv)

    if args.paste_from_stdin:
        content = sys.stdin.read()
        emit_success({
            "source_type": "paste",
            "format": "markdown",
            "content": content,
        })
        return

    if not args.source:
        emit_error(
            code=EXIT_INVALID_INPUT,
            category="invalid_input",
            reason="must pass either --source <path|url> or --paste-from-stdin",
        )
        return

    # URL?
    parsed = urlparse(args.source)
    if parsed.scheme in ("http", "https"):
        resource, action = _classify_url(args.source)
        emit_error(
            code=EXIT_NEEDS_HUMAN,
            category="needs_human",
            resource=resource,
            reason=f"URL detected ({args.source}); resolver chain requires LLM-mediated fetch",
            suggested_action=action,
            fallback="paste",
        )
        return

    # Local path
    src = Path(args.source)
    if not src.exists():
        emit_error(
            code=EXIT_INVALID_INPUT,
            category="invalid_input",
            reason=f"local file not found: {args.source}",
        )
        return
    if src.is_dir():
        emit_error(
            code=EXIT_INVALID_INPUT,
            category="invalid_input",
            reason=f"source is a directory, not a file: {args.source}",
        )
        return

    content = src.read_text(encoding="utf-8")
    emit_success({
        "source_type": "local",
        "format": "markdown",
        "content": content,
        "source_path": str(src.resolve()),
    })


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_prd_ingest.py -v`
Expected: 7 passed.

- [ ] **Step 5: Write the shell wrapper**

Write to `shield/scripts/prd/prd-ingest.sh`:

```bash
#!/usr/bin/env bash
# prd-ingest: classify a PRD source and emit normalized markdown.
#
# See _contract.py for envelope shape and exit codes. See
# .claude/skills/script-llm-contract/SKILL.md for the LLM-side
# behavior on each exit code.

set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  cat >&2 <<'MSG'
prd-ingest: uv is required but not installed.

To install uv (one-time, ~/.local/bin):
  curl -LsSf https://astral.sh/uv/install.sh | sh
MSG
  exit 127
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet -- python "$SCRIPT_DIR/prd_ingest.py" "$@"
```

- [ ] **Step 6: Make the wrapper executable + smoke test**

```bash
chmod +x shield/scripts/prd/prd-ingest.sh

# Smoke: local file
echo "# smoke" > /tmp/prd-smoke.md
shield/scripts/prd/prd-ingest.sh --source /tmp/prd-smoke.md

# Smoke: URL routing
shield/scripts/prd/prd-ingest.sh --source https://notion.so/abc; echo "exit=$?"

# Smoke: paste
echo "# pasted" | shield/scripts/prd/prd-ingest.sh --paste-from-stdin
```

Expected: first call exits 0 with success envelope; URL call exits 4 with `notion_mcp`; paste exits 0.

- [ ] **Step 7: Commit**

```bash
git add shield/scripts/prd/prd-ingest.sh shield/scripts/prd/prd_ingest.py shield/scripts/prd/test_prd_ingest.py
git commit -m "feat(scripts/prd): add prd-ingest.sh + impl + tests

Classifies a PRD source (local path / URL / paste) and emits normalized
markdown per the script-LLM contract. URLs exit 4 with payload telling
the LLM which MCP tool or WebFetch to use, then re-invoke with paste."
```

---


## Task 5: Build `detect-prd-type.sh` + `detect_prd_type.py`

Lean vs standard PRD classifier. Counts top-level `##` headings and looks for telltale section names. LLM still confirms with the user; this script just gives the best guess deterministically.

**Files:**
- Create: `shield/scripts/prd/detect-prd-type.sh`
- Create: `shield/scripts/prd/detect_prd_type.py`
- Create: `shield/scripts/prd/test_detect_prd_type.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_detect_prd_type.py`:

```python
"""Tests for detect_prd_type.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

LEAN_FIXTURE = """\
# Feature X

## 1. Header
owner: alice

## 2. Terminologies

## 3. Current context
problem here

## 4. Personas

## 5. Goals & non-goals

## 6. Success metrics

## 7. User stories

## 8. Milestones

## 9. Open questions

## 10. Out of scope
"""

STANDARD_FIXTURE = """\
# Feature Y

""" + "\n".join(f"## {i}. Section {i}" for i in range(1, 21)) + "\n"


def _run(prd_path: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "detect_prd_type.py"), prd_path],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_lean_prd(tmp_path: Path) -> None:
    prd = tmp_path / "lean.md"
    prd.write_text(LEAN_FIXTURE)
    code, payload = _run(str(prd))
    assert code == 0
    assert payload["data"]["type"] == "lean"
    assert payload["data"]["section_count"] == 10


def test_standard_prd(tmp_path: Path) -> None:
    prd = tmp_path / "standard.md"
    prd.write_text(STANDARD_FIXTURE)
    code, payload = _run(str(prd))
    assert code == 0
    assert payload["data"]["type"] == "standard"
    assert payload["data"]["section_count"] == 20


def test_ambiguous_count(tmp_path: Path) -> None:
    # 14 sections — neither lean (~8-10) nor standard (~19-20).
    prd = tmp_path / "ambig.md"
    prd.write_text("# X\n\n" + "\n".join(f"## {i}. S" for i in range(1, 15)) + "\n")
    code, payload = _run(str(prd))
    assert code == 0
    assert payload["data"]["type"] == "ambiguous"


def test_missing_file(tmp_path: Path) -> None:
    code, payload = _run(str(tmp_path / "nope.md"))
    assert code == 2
    assert payload["category"] == "invalid_input"
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_detect_prd_type.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/detect_prd_type.py`:

```python
"""detect-prd-type: classify a PRD as lean / standard / ambiguous by §-count."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, emit_error, emit_success

H2_RE = re.compile(r"^##\s+\d+\.\s", re.MULTILINE)


def classify(section_count: int) -> str:
    if 7 <= section_count <= 11:
        return "lean"
    if 18 <= section_count <= 21:
        return "standard"
    return "ambiguous"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prd_path")
    args = parser.parse_args(argv)
    src = Path(args.prd_path)
    if not src.exists() or src.is_dir():
        emit_error(
            code=EXIT_INVALID_INPUT,
            category="invalid_input",
            reason=f"prd path not a file: {args.prd_path}",
        )
        return
    text = src.read_text(encoding="utf-8")
    count = len(H2_RE.findall(text))
    emit_success({"type": classify(count), "section_count": count, "prd_path": str(src.resolve())})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_detect_prd_type.py -v`
Expected: 4 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/detect-prd-type.sh`:

```bash
#!/usr/bin/env bash
# detect-prd-type: classify a PRD as lean / standard / ambiguous.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "detect-prd-type: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet -- python "$SCRIPT_DIR/detect_prd_type.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/detect-prd-type.sh
git add shield/scripts/prd/detect-prd-type.sh shield/scripts/prd/detect_prd_type.py shield/scripts/prd/test_detect_prd_type.py
git commit -m "feat(scripts/prd): add detect-prd-type.sh + impl + tests

Counts top-level \"## N.\" headings and classifies as lean (7-11),
standard (18-21), or ambiguous. LLM confirms with user."
```

---

## Task 6: Build `next-review-dir.sh` + `next_review_dir.py`

Resolves `{date}{_counter}` for `{output_dir}/{feature}/reviews/prd/`. Today's ISO date for first run; `_2`, `_3`, … on same-day collisions. Pure filesystem inspection + numeric sort — no LLM involvement.

**Files:**
- Create: `shield/scripts/prd/next-review-dir.sh`
- Create: `shield/scripts/prd/next_review_dir.py`
- Create: `shield/scripts/prd/test_next_review_dir.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_next_review_dir.py`:

```python
"""Tests for next_review_dir.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "next_review_dir.py"), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_first_run_today(tmp_path: Path) -> None:
    reviews_root = tmp_path / "docs/shield/feat-x/reviews/prd"
    reviews_root.mkdir(parents=True)
    code, payload = _run("--reviews-root", str(reviews_root), "--date", "2026-05-23")
    assert code == 0
    assert payload["data"]["dir_name"] == "2026-05-23"
    assert payload["data"]["counter"] == ""


def test_same_day_rerun(tmp_path: Path) -> None:
    reviews_root = tmp_path / "rev"
    (reviews_root / "2026-05-23").mkdir(parents=True)
    code, payload = _run("--reviews-root", str(reviews_root), "--date", "2026-05-23")
    assert code == 0
    assert payload["data"]["dir_name"] == "2026-05-23_2"
    assert payload["data"]["counter"] == "_2"


def test_third_same_day_run(tmp_path: Path) -> None:
    reviews_root = tmp_path / "rev"
    (reviews_root / "2026-05-23").mkdir(parents=True)
    (reviews_root / "2026-05-23_2").mkdir()
    code, payload = _run("--reviews-root", str(reviews_root), "--date", "2026-05-23")
    assert code == 0
    assert payload["data"]["dir_name"] == "2026-05-23_3"


def test_unrelated_dirs_ignored(tmp_path: Path) -> None:
    reviews_root = tmp_path / "rev"
    (reviews_root / "2026-05-21").mkdir(parents=True)
    (reviews_root / "2026-05-22_2").mkdir()
    code, payload = _run("--reviews-root", str(reviews_root), "--date", "2026-05-23")
    assert code == 0
    assert payload["data"]["dir_name"] == "2026-05-23"  # no prior 23rd entries
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_next_review_dir.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/next_review_dir.py`:

```python
"""next-review-dir: resolve {date}{_counter} for reviews/prd/ same-day collisions."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, emit_error, emit_success

COUNTER_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:_(\d+))?$")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews-root", required=True, help="path to {feature}/reviews/prd/")
    parser.add_argument("--date", default=None, help="ISO date YYYY-MM-DD (default: today)")
    args = parser.parse_args(argv)

    today = args.date or date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", today):
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"--date must be YYYY-MM-DD: {today}")
        return

    root = Path(args.reviews_root)
    if not root.exists():
        # First run for this feature — no reviews dir yet.
        emit_success({"dir_name": today, "counter": "", "absolute_path": str(root / today)})
        return

    # Inspect siblings.
    highest = 1  # 1 means "no counter" / first run; 2 means "_2"; etc.
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        m = COUNTER_RE.match(entry.name)
        if not m:
            continue
        if not entry.name.startswith(today):
            continue
        ctr = int(m.group(1)) if m.group(1) else 1
        if ctr >= highest:
            highest = ctr + 1

    if highest == 1:
        dir_name = today
        counter = ""
    else:
        dir_name = f"{today}_{highest}"
        counter = f"_{highest}"

    emit_success({"dir_name": dir_name, "counter": counter, "absolute_path": str(root / dir_name)})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_next_review_dir.py -v`
Expected: 4 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/next-review-dir.sh`:

```bash
#!/usr/bin/env bash
# next-review-dir: resolve {date}{_counter} for reviews/prd/.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "next-review-dir: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet -- python "$SCRIPT_DIR/next_review_dir.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/next-review-dir.sh
git add shield/scripts/prd/next-review-dir.sh shield/scripts/prd/next_review_dir.py shield/scripts/prd/test_next_review_dir.py
git commit -m "feat(scripts/prd): add next-review-dir.sh + impl + tests

Resolves {date}{_counter} for reviews/prd/ — first run uses today's
ISO date; same-day collisions use _2, _3, ..."
```

---


## Task 7: Build `extract-glossary-candidates.sh` + `extract_glossary_candidates.py`

Parses a research transcript's `## Glossary` / `## Terminology` / `## Terms` section into candidate rows. **Does NOT copy into the PRD** — that's the orchestrator's job once the body-grounding filter runs.

**Files:**
- Create: `shield/scripts/prd/extract-glossary-candidates.sh`
- Create: `shield/scripts/prd/extract_glossary_candidates.py`
- Create: `shield/scripts/prd/test_extract_glossary_candidates.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_extract_glossary_candidates.py`:

```python
"""Tests for extract_glossary_candidates.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

TRANSCRIPT_TABLE = """\
# Research transcript

## Glossary

| Term | Definition |
|---|---|
| ICP | Ideal customer profile |
| PLG | Product-led growth |

## Other section

Body content.
"""

TRANSCRIPT_BULLETS = """\
# Research transcript

## Terms

- **MAU** — Monthly active users
- **DAU** — Daily active users; subset of MAU
- **NPS** — Net promoter score

## Notes
unrelated bullet.
"""

TRANSCRIPT_NO_GLOSSARY = """\
# Research transcript

Just body.
"""


def _run(path: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "extract_glossary_candidates.py"), path],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_table_glossary(tmp_path: Path) -> None:
    src = tmp_path / "t.md"
    src.write_text(TRANSCRIPT_TABLE)
    code, payload = _run(str(src))
    assert code == 0
    terms = {c["term"]: c["definition"] for c in payload["data"]["candidates"]}
    assert terms == {"ICP": "Ideal customer profile", "PLG": "Product-led growth"}
    assert all(c["source"] == "research" for c in payload["data"]["candidates"])


def test_bullet_glossary(tmp_path: Path) -> None:
    src = tmp_path / "t.md"
    src.write_text(TRANSCRIPT_BULLETS)
    code, payload = _run(str(src))
    assert code == 0
    terms = {c["term"]: c["definition"] for c in payload["data"]["candidates"]}
    assert terms["MAU"] == "Monthly active users"
    assert terms["DAU"] == "Daily active users; subset of MAU"
    assert terms["NPS"] == "Net promoter score"


def test_no_glossary_section(tmp_path: Path) -> None:
    src = tmp_path / "t.md"
    src.write_text(TRANSCRIPT_NO_GLOSSARY)
    code, payload = _run(str(src))
    assert code == 0
    assert payload["data"]["candidates"] == []


def test_missing_file(tmp_path: Path) -> None:
    code, payload = _run(str(tmp_path / "nope.md"))
    assert code == 2
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_extract_glossary_candidates.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/extract_glossary_candidates.py`:

```python
"""extract-glossary-candidates: parse research transcript glossary into candidates.

Recognized section headings (case-insensitive): "Glossary", "Terminology", "Terms".
Accepts either a table (| Term | Definition |) or bullets ("- **Term** — def").
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, emit_error, emit_success

SECTION_RE = re.compile(r"^##\s+(?:\d+\.\s+)?(Glossary|Terminology|Terms)\s*$", re.IGNORECASE | re.MULTILINE)
NEXT_H2_RE = re.compile(r"^##\s", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")
BULLET_RE = re.compile(r"^\s*-\s*\*\*\s*([^*]+?)\s*\*\*\s*[—\-:]\s*(.+?)\s*$")


def _extract_section(text: str) -> str:
    m = SECTION_RE.search(text)
    if not m:
        return ""
    start = m.end()
    nxt = NEXT_H2_RE.search(text, start)
    end = nxt.start() if nxt else len(text)
    return text[start:end]


def _parse_rows(section_text: str) -> list[dict]:
    candidates: list[dict] = []
    for line in section_text.splitlines():
        # Skip empty lines, separator rows (|---|---|), and header rows (| Term | Definition |).
        if not line.strip():
            continue
        if re.match(r"^\|\s*-+\s*\|", line):
            continue
        m = TABLE_ROW_RE.match(line)
        if m:
            term, definition = m.group(1).strip(), m.group(2).strip()
            if term.lower() in ("term", "name") and definition.lower() in ("definition", "meaning"):
                continue  # header row
            candidates.append({"term": term, "definition": definition, "source": "research"})
            continue
        m = BULLET_RE.match(line)
        if m:
            candidates.append({"term": m.group(1).strip(), "definition": m.group(2).strip(), "source": "research"})
            continue
    return candidates


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript_path")
    args = parser.parse_args(argv)
    src = Path(args.transcript_path)
    if not src.exists() or src.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"transcript path not a file: {args.transcript_path}")
        return
    text = src.read_text(encoding="utf-8")
    section = _extract_section(text)
    candidates = _parse_rows(section) if section else []
    emit_success({"candidates": candidates, "source_path": str(src.resolve())})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_extract_glossary_candidates.py -v`
Expected: 4 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/extract-glossary-candidates.sh`:

```bash
#!/usr/bin/env bash
# extract-glossary-candidates: parse research transcript glossary into candidates.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "extract-glossary-candidates: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet -- python "$SCRIPT_DIR/extract_glossary_candidates.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/extract-glossary-candidates.sh
git add shield/scripts/prd/extract-glossary-candidates.sh shield/scripts/prd/extract_glossary_candidates.py shield/scripts/prd/test_extract_glossary_candidates.py
git commit -m "feat(scripts/prd): add extract-glossary-candidates.sh + impl + tests

Parses a research transcript's Glossary/Terminology/Terms section into
candidate rows. Candidates are filtered downstream by body-occurrence."
```

---

## Task 8: Build `count-term-in-body.sh` + `count_term_in_body.py`

Counts occurrences of a term in the PRD body, **excluding** §2 Terminologies (to avoid the row counting itself). Used by the body-grounding filter for §2.

**Files:**
- Create: `shield/scripts/prd/count-term-in-body.sh`
- Create: `shield/scripts/prd/count_term_in_body.py`
- Create: `shield/scripts/prd/test_count_term_in_body.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_count_term_in_body.py`:

```python
"""Tests for count_term_in_body.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

PRD_FIXTURE = """\
# Feature

## 1. Header
owner: x

## 2. Terminologies

| Term | Definition |
|---|---|
| ICP | Ideal customer profile |
| RBAC | Role-based access |

## 3. Current context
Our ICP includes Series B SaaS. ICP teams want RBAC.

## 4. Personas
The ICP persona...

## 5. Goals
RBAC is not a goal.
"""


def _run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "count_term_in_body.py"), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_count_excludes_section_2(tmp_path: Path) -> None:
    prd = tmp_path / "p.md"
    prd.write_text(PRD_FIXTURE)
    # ICP appears 3 times in §3 + §4 body, plus once in §2 → script returns 3.
    code, payload = _run("--term", "ICP", "--prd", str(prd))
    assert code == 0
    assert payload["data"]["term"] == "ICP"
    assert payload["data"]["count"] == 3


def test_count_case_insensitive(tmp_path: Path) -> None:
    prd = tmp_path / "p.md"
    prd.write_text(PRD_FIXTURE)
    code, payload = _run("--term", "rbac", "--prd", str(prd))
    assert code == 0
    # "RBAC" appears in §3 body + §5 body → 2.
    assert payload["data"]["count"] == 2


def test_count_zero(tmp_path: Path) -> None:
    prd = tmp_path / "p.md"
    prd.write_text(PRD_FIXTURE)
    code, payload = _run("--term", "PLG", "--prd", str(prd))
    assert code == 0
    assert payload["data"]["count"] == 0


def test_missing_prd(tmp_path: Path) -> None:
    code, payload = _run("--term", "X", "--prd", str(tmp_path / "nope.md"))
    assert code == 2
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_count_term_in_body.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/count_term_in_body.py`:

```python
"""count-term-in-body: count occurrences of a term in PRD body, excluding §2."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, emit_error, emit_success

SECTION_2_RE = re.compile(r"^##\s+2\.\s+Terminologies.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL | re.IGNORECASE)


def _strip_section_2(text: str) -> str:
    return SECTION_2_RE.sub("", text)


def _count(term: str, body: str) -> int:
    pattern = r"\b" + re.escape(term) + r"\b"
    return len(re.findall(pattern, body, flags=re.IGNORECASE))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--term", required=True)
    parser.add_argument("--prd", required=True)
    args = parser.parse_args(argv)
    src = Path(args.prd)
    if not src.exists() or src.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"prd path not a file: {args.prd}")
        return
    text = src.read_text(encoding="utf-8")
    body = _strip_section_2(text)
    count = _count(args.term, body)
    emit_success({"term": args.term, "count": count})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_count_term_in_body.py -v`
Expected: 4 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/count-term-in-body.sh`:

```bash
#!/usr/bin/env bash
# count-term-in-body: count term occurrences in PRD body, excluding §2.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "count-term-in-body: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet -- python "$SCRIPT_DIR/count_term_in_body.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/count-term-in-body.sh
git add shield/scripts/prd/count-term-in-body.sh shield/scripts/prd/count_term_in_body.py shield/scripts/prd/test_count_term_in_body.py
git commit -m "feat(scripts/prd): add count-term-in-body.sh + impl + tests

Word-boundary, case-insensitive count of a term in the PRD body,
excluding §2 Terminologies. Used by the §2 body-grounding filter."
```

---


## Task 9: Build `sparse-sections.sh` + `sparse_sections.py`

Parses `review-comments.json` for evaluation points graded D or F at `severity=Critical`, joins with `dim-section-map.yaml`, and returns the deduped, sorted list of section IDs that look sparse.

**Files:**
- Create: `shield/scripts/prd/sparse-sections.sh`
- Create: `shield/scripts/prd/sparse_sections.py`
- Create: `shield/scripts/prd/test_sparse_sections.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_sparse_sections.py`:

```python
"""Tests for sparse_sections.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

DIM_MAP_YAML = """\
dim_section_map:
  1:  [3]
  3:  [6]
  5:  [9, 10, 11]
  13: [15]
"""

REVIEW_BOTH_CRITICAL_DF = {
    "dimensions": [
        {"id": 1, "name": "Problem clarity", "grade": "D",
         "evaluation_points": [
             {"id": "1a", "grade": "F", "severity": "Critical", "gap": "g", "suggestion": "s"},
             {"id": "1b", "grade": "C", "severity": "Important", "gap": "g", "suggestion": "s"},
         ]},
        {"id": 3, "name": "Measurable success", "grade": "B",
         "evaluation_points": [
             {"id": "3a", "grade": "B", "severity": "Critical", "gap": None, "suggestion": None},
         ]},
        {"id": 5, "name": "NFR coverage", "grade": "D",
         "evaluation_points": [
             {"id": "5a", "grade": "D", "severity": "Critical", "gap": "g", "suggestion": "s"},
         ]},
        {"id": 13, "name": "Cost", "grade": "B",
         "evaluation_points": [
             {"id": "13a", "grade": "C", "severity": "Important", "gap": "g", "suggestion": "s"},
         ]},
    ],
}


def _run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "sparse_sections.py"), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_critical_df_sections(tmp_path: Path) -> None:
    review = tmp_path / "review-comments.json"
    review.write_text(json.dumps(REVIEW_BOTH_CRITICAL_DF))
    dim_map = tmp_path / "dim-section-map.yaml"
    dim_map.write_text(DIM_MAP_YAML)
    code, payload = _run("--review", str(review), "--dim-map", str(dim_map))
    assert code == 0
    # Dim 1 (1a=F Critical) → §3; Dim 5 (5a=D Critical) → §9, §10, §11.
    # Dim 3 (3a=B Critical) and Dim 13 (13a=C Important) excluded.
    assert payload["data"]["section_ids"] == [3, 9, 10, 11]


def test_no_sparse(tmp_path: Path) -> None:
    review = tmp_path / "r.json"
    review.write_text(json.dumps({"dimensions": [
        {"id": 1, "name": "x", "grade": "A",
         "evaluation_points": [
             {"id": "1a", "grade": "A", "severity": "Critical", "gap": None, "suggestion": None},
         ]}
    ]}))
    dim_map = tmp_path / "d.yaml"
    dim_map.write_text(DIM_MAP_YAML)
    code, payload = _run("--review", str(review), "--dim-map", str(dim_map))
    assert code == 0
    assert payload["data"]["section_ids"] == []


def test_missing_review(tmp_path: Path) -> None:
    dim_map = tmp_path / "d.yaml"
    dim_map.write_text(DIM_MAP_YAML)
    code, payload = _run("--review", str(tmp_path / "nope.json"), "--dim-map", str(dim_map))
    assert code == 2


def test_unmapped_dim_skipped(tmp_path: Path) -> None:
    review = tmp_path / "r.json"
    review.write_text(json.dumps({"dimensions": [
        {"id": 99, "name": "unknown", "grade": "F",
         "evaluation_points": [
             {"id": "99a", "grade": "F", "severity": "Critical", "gap": "g", "suggestion": "s"},
         ]}
    ]}))
    dim_map = tmp_path / "d.yaml"
    dim_map.write_text(DIM_MAP_YAML)
    code, payload = _run("--review", str(review), "--dim-map", str(dim_map))
    # Partial: known dims OK, unmapped dim reported in partial.
    assert code == 5
    assert payload["category"] == "partial"
    assert 99 in payload["partial"]["unmapped_dims"]
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_sparse_sections.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/sparse_sections.py`:

```python
"""sparse-sections: find §s with Critical D/F findings.

Reads review-comments.json + dim-section-map.yaml. For each dim, looks
at evaluation_points with severity=Critical and grade in {D, F}. Joins
to section IDs via the map. Emits sorted deduped section_ids.

If a dim is present in the review but missing from the map, emits exit
5 (partial) with unmapped_dims in the partial payload so the LLM can
decide whether to update the map.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, EXIT_PARTIAL, emit_error, emit_success

SPARSE_GRADES = {"D", "F"}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True)
    parser.add_argument("--dim-map", required=True)
    args = parser.parse_args(argv)

    review_path = Path(args.review)
    dim_map_path = Path(args.dim_map)
    if not review_path.exists() or not dim_map_path.exists():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"review or dim-map not found: review={args.review} dim_map={args.dim_map}")
        return

    review = json.loads(review_path.read_text(encoding="utf-8"))
    dim_map = yaml.safe_load(dim_map_path.read_text(encoding="utf-8"))["dim_section_map"]

    sections: set[int] = set()
    unmapped: list[int] = []
    for dim in review.get("dimensions", []):
        critical_df = any(
            ep.get("severity") == "Critical" and ep.get("grade") in SPARSE_GRADES
            for ep in dim.get("evaluation_points", [])
        )
        if not critical_df:
            continue
        secs = dim_map.get(dim["id"])
        if secs is None:
            unmapped.append(dim["id"])
            continue
        sections.update(secs)

    result = {"section_ids": sorted(sections)}

    if unmapped:
        emit_error(code=EXIT_PARTIAL, category="partial",
                   reason=f"{len(unmapped)} dim(s) absent from dim-section-map.yaml",
                   partial={"section_ids": sorted(sections), "unmapped_dims": sorted(unmapped)})
        return

    emit_success(result)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_sparse_sections.py -v`
Expected: 4 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/sparse-sections.sh`:

```bash
#!/usr/bin/env bash
# sparse-sections: §-IDs where reviewers flagged Critical D/F.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "sparse-sections: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet --with pyyaml -- python "$SCRIPT_DIR/sparse_sections.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/sparse-sections.sh
git add shield/scripts/prd/sparse-sections.sh shield/scripts/prd/sparse_sections.py shield/scripts/prd/test_sparse_sections.py
git commit -m "feat(scripts/prd): add sparse-sections.sh + impl + tests

Joins review-comments.json with dim-section-map.yaml to identify §s
flagged by Critical D/F findings. Used by /prd-review to ask the user
whether to gather more context before generating the corrected PRD."
```

---

## Task 10: Build `map-gaps-to-sections.sh` + `map_gaps_to_sections.py`

Groups every non-A evaluation point (with a gap/suggestion) under its mapped section. Output is the structured input the corrected-PRD generation prompt consumes — one block of "here are the gaps for §N" per section.

**Files:**
- Create: `shield/scripts/prd/map-gaps-to-sections.sh`
- Create: `shield/scripts/prd/map_gaps_to_sections.py`
- Create: `shield/scripts/prd/test_map_gaps_to_sections.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_map_gaps_to_sections.py`:

```python
"""Tests for map_gaps_to_sections.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

DIM_MAP_YAML = """\
dim_section_map:
  1:  [3]
  5:  [9, 10, 11]
  12: [12, 13, 18]
"""

REVIEW = {
    "dimensions": [
        {"id": 1, "name": "Problem clarity", "grade": "C",
         "evaluation_points": [
             {"id": "1a", "grade": "F", "severity": "Critical", "gap": "no persona", "suggestion": "add Anya"},
             {"id": "1b", "grade": "A", "severity": "Important", "gap": None, "suggestion": None},
         ]},
        {"id": 5, "name": "NFR", "grade": "C",
         "evaluation_points": [
             {"id": "5a", "grade": "C", "severity": "Critical", "gap": "privacy unclear", "suggestion": "specify PII retention"},
         ]},
        {"id": 12, "name": "Risks", "grade": "B",
         "evaluation_points": [
             {"id": "12a", "grade": "B", "severity": "Warning", "gap": "minor gap", "suggestion": "tweak"},
         ]},
    ]
}


def _run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "map_gaps_to_sections.py"), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_groups_by_section(tmp_path: Path) -> None:
    review = tmp_path / "r.json"
    review.write_text(json.dumps(REVIEW))
    dim_map = tmp_path / "d.yaml"
    dim_map.write_text(DIM_MAP_YAML)
    code, payload = _run("--review", str(review), "--dim-map", str(dim_map))
    assert code == 0
    gaps = payload["data"]["gaps_by_section"]
    # Dim 1 → §3 (gap 1a present, 1b dropped because grade A)
    assert len(gaps["3"]) == 1
    assert gaps["3"][0]["dim_id"] == 1
    assert gaps["3"][0]["eval_point_id"] == "1a"
    # Dim 5 → §9, §10, §11 (5a appears in each)
    assert len(gaps["9"]) == 1
    assert len(gaps["10"]) == 1
    assert len(gaps["11"]) == 1
    # Dim 12 → §12, §13, §18 (12a appears in each)
    assert len(gaps["12"]) == 1
    assert len(gaps["18"]) == 1


def test_a_graded_excluded(tmp_path: Path) -> None:
    review = tmp_path / "r.json"
    review.write_text(json.dumps({"dimensions": [
        {"id": 1, "name": "x", "grade": "A",
         "evaluation_points": [
             {"id": "1a", "grade": "A", "severity": "Critical", "gap": None, "suggestion": None},
         ]}
    ]}))
    dim_map = tmp_path / "d.yaml"
    dim_map.write_text(DIM_MAP_YAML)
    code, payload = _run("--review", str(review), "--dim-map", str(dim_map))
    assert code == 0
    assert payload["data"]["gaps_by_section"] == {}


def test_unmapped_dim_partial(tmp_path: Path) -> None:
    review = tmp_path / "r.json"
    review.write_text(json.dumps({"dimensions": [
        {"id": 99, "name": "x", "grade": "F",
         "evaluation_points": [
             {"id": "99a", "grade": "F", "severity": "Critical", "gap": "g", "suggestion": "s"},
         ]}
    ]}))
    dim_map = tmp_path / "d.yaml"
    dim_map.write_text(DIM_MAP_YAML)
    code, payload = _run("--review", str(review), "--dim-map", str(dim_map))
    assert code == 5
    assert 99 in payload["partial"]["unmapped_dims"]
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_map_gaps_to_sections.py -v`
Expected: FAIL.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/map_gaps_to_sections.py`:

```python
"""map-gaps-to-sections: group review eval-point gaps by mapped section.

Skips evaluation points graded A (no gap to fix). For each remaining
point, fans out to all sections the dim maps to. Output's keys are
stringified section IDs so it serializes cleanly into JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, EXIT_PARTIAL, emit_error, emit_success


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True)
    parser.add_argument("--dim-map", required=True)
    args = parser.parse_args(argv)

    rp, dp = Path(args.review), Path(args.dim_map)
    if not rp.exists() or not dp.exists():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"review or dim-map not found: review={args.review} dim_map={args.dim_map}")
        return

    review = json.loads(rp.read_text(encoding="utf-8"))
    dim_map = yaml.safe_load(dp.read_text(encoding="utf-8"))["dim_section_map"]

    gaps_by_section: dict[str, list[dict]] = {}
    unmapped: list[int] = []
    for dim in review.get("dimensions", []):
        secs = dim_map.get(dim["id"])
        if secs is None:
            unmapped.append(dim["id"])
            continue
        for ep in dim.get("evaluation_points", []):
            if ep.get("grade") == "A":
                continue
            if not ep.get("gap") and not ep.get("suggestion"):
                continue
            entry = {
                "dim_id": dim["id"],
                "dim_name": dim.get("name"),
                "eval_point_id": ep.get("id"),
                "grade": ep.get("grade"),
                "severity": ep.get("severity"),
                "gap": ep.get("gap"),
                "suggestion": ep.get("suggestion"),
            }
            for sec in secs:
                gaps_by_section.setdefault(str(sec), []).append(entry)

    if unmapped:
        emit_error(code=EXIT_PARTIAL, category="partial",
                   reason=f"{len(unmapped)} dim(s) absent from dim-section-map.yaml",
                   partial={"gaps_by_section": gaps_by_section, "unmapped_dims": sorted(unmapped)})
        return

    emit_success({"gaps_by_section": gaps_by_section})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_map_gaps_to_sections.py -v`
Expected: 3 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/map-gaps-to-sections.sh`:

```bash
#!/usr/bin/env bash
# map-gaps-to-sections: group review gaps by mapped section.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "map-gaps-to-sections: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet --with pyyaml -- python "$SCRIPT_DIR/map_gaps_to_sections.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/map-gaps-to-sections.sh
git add shield/scripts/prd/map-gaps-to-sections.sh shield/scripts/prd/map_gaps_to_sections.py shield/scripts/prd/test_map_gaps_to_sections.py
git commit -m "feat(scripts/prd): add map-gaps-to-sections.sh + impl + tests

Groups review-comments.json gaps by mapped section ID, fanning each
gap out to every § the dim maps to. Consumed by the corrected-PRD
generation prompt as structured per-section guidance."
```

---


## Task 11: Build `aggregate-review.sh` + `aggregate_review.py`

Reads a directory of dim-block JSON files emitted by the 13 reviewer dispatches, combines them, computes per-persona + composite grades, applies the P0-gate, and writes `review-comments.json` (structured) + `summary.md` (human-readable scorecard).

**Two envelope shapes coexist** (per spec §4 of prd-review SKILL.md / dimensions.md):
- **Per-dim envelope** (skill-internal prompts, dims 1, 2, 3, 7, 8, 9, 10, 11, 12): the file IS one dim-block.
- **Per-persona envelope** (legacy personas: agile-coach, architect for dims 5+6, dx-engineer, finops-analyst): one file wraps `dimensions: [...]` and optionally `anti_patterns: [...]`.

**Persona weights** (from dimensions.md):

| Persona | Weight | Dims |
|---|---|---|
| product-manager | 1.0 | 1, 2, 3, 7, 8, 9, 10, 11, 12 |
| agile-coach | 1.0 | 4 |
| tech-lead | 1.0 | 5, 6 |
| dx-engineer | 0.7 | (anti-patterns only) |
| finops-analyst | 0.7 | 13 |

**Grade ↔ numeric:** A=4, B=3, C=2, D=1, F=0.

**Verdict:**
- composite ≥ 3.5 → `Ready`
- composite ≥ 2.5 → `Needs Work`
- composite < 2.5 → `Not Ready`
- **P0-gate:** if ANY Critical evaluation point graded D or F exists, verdict is forced to `Needs Work` regardless of composite.

**Files:**
- Create: `shield/scripts/prd/aggregate-review.sh`
- Create: `shield/scripts/prd/aggregate_review.py`
- Create: `shield/scripts/prd/test_aggregate_review.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_aggregate_review.py`:

```python
"""Tests for aggregate_review.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _per_dim(id_: int, name: str, grade: str, ep_grade: str = "A", severity: str = "Critical") -> dict:
    return {
        "id": id_, "name": name, "grade": grade,
        "evaluation_points": [
            {"id": f"{id_}a", "grade": ep_grade, "severity": severity,
             "gap": None if ep_grade == "A" else "g", "suggestion": None if ep_grade == "A" else "s"},
        ],
    }


def _per_persona(persona: str, persona_grade: str, dims: list[dict], anti_patterns: list[dict] | None = None) -> dict:
    payload = {"persona": persona, "persona_grade": persona_grade, "dimensions": dims}
    if anti_patterns is not None:
        payload["anti_patterns"] = anti_patterns
    return payload


def _run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "aggregate_review.py"), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def _write_dispatch_dir(tmp_path: Path, files: dict[str, dict]) -> Path:
    d = tmp_path / "dispatch"
    d.mkdir()
    for name, payload in files.items():
        (d / name).write_text(json.dumps(payload))
    return d


def test_all_a_grades_ready(tmp_path: Path) -> None:
    d = _write_dispatch_dir(tmp_path, {
        "dim-1.json": _per_dim(1, "Problem clarity", "A"),
        "dim-2.json": _per_dim(2, "Scope", "A"),
        "dim-3.json": _per_dim(3, "Measurable success", "A"),
        "dim-7.json": _per_dim(7, "RACI", "A"),
        "dim-8.json": _per_dim(8, "Legal", "A"),
        "dim-9.json": _per_dim(9, "GTM", "A"),
        "dim-10.json": _per_dim(10, "Support", "A"),
        "dim-11.json": _per_dim(11, "Why now", "A"),
        "dim-12.json": _per_dim(12, "Risks", "A"),
        "agile-coach.json": _per_persona("agile-coach", "A", [_per_dim(4, "AC", "A")]),
        "architect.json": _per_persona("tech-lead", "A", [_per_dim(5, "NFR", "A"), _per_dim(6, "Rollout", "A")]),
        "dx-engineer.json": _per_persona("dx-engineer", "A", [], anti_patterns=[]),
        "finops-analyst.json": _per_persona("finops-analyst", "A", [_per_dim(13, "Cost", "A")]),
    })
    out_dir = tmp_path / "out"; out_dir.mkdir()
    code, payload = _run("--dispatch-dir", str(d), "--out-dir", str(out_dir))
    assert code == 0
    assert payload["data"]["verdict"] == "Ready"
    assert payload["data"]["composite"] >= 3.5
    assert payload["data"]["p0_count"] == 0
    # Outputs written.
    assert (out_dir / "review-comments.json").exists()
    assert (out_dir / "summary.md").exists()


def test_critical_d_forces_needs_work(tmp_path: Path) -> None:
    # All dims A except dim 1 which has ONE Critical-D eval point.
    d = _write_dispatch_dir(tmp_path, {
        "dim-1.json": _per_dim(1, "Problem clarity", "A", ep_grade="D", severity="Critical"),
        "dim-2.json": _per_dim(2, "Scope", "A"),
        "dim-3.json": _per_dim(3, "Measurable success", "A"),
        "dim-7.json": _per_dim(7, "RACI", "A"),
        "dim-8.json": _per_dim(8, "Legal", "A"),
        "dim-9.json": _per_dim(9, "GTM", "A"),
        "dim-10.json": _per_dim(10, "Support", "A"),
        "dim-11.json": _per_dim(11, "Why now", "A"),
        "dim-12.json": _per_dim(12, "Risks", "A"),
        "agile-coach.json": _per_persona("agile-coach", "A", [_per_dim(4, "AC", "A")]),
        "architect.json": _per_persona("tech-lead", "A", [_per_dim(5, "NFR", "A"), _per_dim(6, "Rollout", "A")]),
        "dx-engineer.json": _per_persona("dx-engineer", "A", [], anti_patterns=[]),
        "finops-analyst.json": _per_persona("finops-analyst", "A", [_per_dim(13, "Cost", "A")]),
    })
    out_dir = tmp_path / "out"; out_dir.mkdir()
    code, payload = _run("--dispatch-dir", str(d), "--out-dir", str(out_dir))
    assert code == 0
    assert payload["data"]["p0_count"] == 1
    # P0-gate forces Needs Work even though dim grades are all A.
    assert payload["data"]["verdict"] == "Needs Work"


def test_missing_dispatch_dir(tmp_path: Path) -> None:
    code, payload = _run("--dispatch-dir", str(tmp_path / "nope"), "--out-dir", str(tmp_path / "out"))
    assert code == 2


def test_partial_when_dim_missing(tmp_path: Path) -> None:
    # Only dim 1 supplied. Aggregator returns exit 5.
    d = _write_dispatch_dir(tmp_path, {
        "dim-1.json": _per_dim(1, "Problem clarity", "A"),
    })
    out_dir = tmp_path / "out"; out_dir.mkdir()
    code, payload = _run("--dispatch-dir", str(d), "--out-dir", str(out_dir))
    assert code == 5
    assert payload["category"] == "partial"
    assert set(payload["partial"]["missing_dims"]) == {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}


def test_review_comments_json_shape(tmp_path: Path) -> None:
    d = _write_dispatch_dir(tmp_path, {
        "dim-1.json": _per_dim(1, "Problem clarity", "B", ep_grade="B"),
        "dim-2.json": _per_dim(2, "Scope", "A"),
        "dim-3.json": _per_dim(3, "Measurable success", "A"),
        "dim-7.json": _per_dim(7, "RACI", "A"),
        "dim-8.json": _per_dim(8, "Legal", "A"),
        "dim-9.json": _per_dim(9, "GTM", "A"),
        "dim-10.json": _per_dim(10, "Support", "A"),
        "dim-11.json": _per_dim(11, "Why now", "A"),
        "dim-12.json": _per_dim(12, "Risks", "A"),
        "agile-coach.json": _per_persona("agile-coach", "A", [_per_dim(4, "AC", "A")]),
        "architect.json": _per_persona("tech-lead", "A", [_per_dim(5, "NFR", "A"), _per_dim(6, "Rollout", "A")]),
        "dx-engineer.json": _per_persona("dx-engineer", "A", [], anti_patterns=[
            {"name": "implementation-detail-bleed", "evidence_line": 42, "evidence_quote": "use Redis"},
        ]),
        "finops-analyst.json": _per_persona("finops-analyst", "A", [_per_dim(13, "Cost", "A")]),
    })
    out_dir = tmp_path / "out"; out_dir.mkdir()
    code, _ = _run("--dispatch-dir", str(d), "--out-dir", str(out_dir))
    assert code == 0
    rc = json.loads((out_dir / "review-comments.json").read_text())
    # All 13 dims present.
    assert {d["id"] for d in rc["dimensions"]} == set(range(1, 14))
    # Anti-patterns flowed through.
    assert any(ap["name"] == "implementation-detail-bleed" for ap in rc["anti_patterns"])
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_aggregate_review.py -v`
Expected: FAIL.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/aggregate_review.py`:

```python
"""aggregate-review: composite + P0-gate from a directory of dim-block files.

Reads every *.json in --dispatch-dir, unwraps per-persona envelopes,
combines into one canonical review-comments.json + writes summary.md.

See dimensions.md for the dim → persona table; persona weights are
hardcoded below to match.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, EXIT_PARTIAL, emit_error, emit_success

GRADE_VALUES = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
NUMERIC_TO_GRADE = [(3.5, "A"), (2.5, "B"), (1.5, "C"), (0.5, "D"), (0.0, "F")]

DIM_PERSONA = {
    1: "product-manager", 2: "product-manager", 3: "product-manager",
    4: "agile-coach",
    5: "tech-lead", 6: "tech-lead",
    7: "product-manager", 8: "product-manager", 9: "product-manager",
    10: "product-manager", 11: "product-manager", 12: "product-manager",
    13: "finops-analyst",
}
PERSONA_WEIGHTS = {
    "product-manager": 1.0,
    "agile-coach": 1.0,
    "tech-lead": 1.0,
    "dx-engineer": 0.7,
    "finops-analyst": 0.7,
}
ALL_DIMS = set(range(1, 14))


def _numeric_to_letter(v: float) -> str:
    for threshold, letter in NUMERIC_TO_GRADE:
        if v >= threshold:
            return letter
    return "F"


def _collect_dim_blocks(dispatch_dir: Path) -> tuple[list[dict], list[dict]]:
    """Return (dim_blocks, anti_patterns) — accepts both envelope shapes."""
    dim_blocks: list[dict] = []
    anti_patterns: list[dict] = []
    for path in sorted(dispatch_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "dimensions" in payload:
            # per-persona envelope
            dim_blocks.extend(payload["dimensions"])
            anti_patterns.extend(payload.get("anti_patterns", []))
        elif "id" in payload and "evaluation_points" in payload:
            # per-dim envelope
            dim_blocks.append(payload)
    return dim_blocks, anti_patterns


def _count_p0s(dim_blocks: list[dict]) -> int:
    n = 0
    for d in dim_blocks:
        for ep in d.get("evaluation_points", []):
            if ep.get("severity") == "Critical" and ep.get("grade") in ("D", "F"):
                n += 1
    return n


def _persona_grades(dim_blocks: list[dict]) -> dict[str, float]:
    """Average dim grades per persona."""
    buckets: dict[str, list[float]] = {}
    for d in dim_blocks:
        persona = DIM_PERSONA.get(d["id"])
        if persona is None:
            continue
        buckets.setdefault(persona, []).append(GRADE_VALUES.get(d.get("grade", "F"), 0.0))
    return {p: sum(vs) / len(vs) for p, vs in buckets.items() if vs}


def _composite(persona_grades: dict[str, float]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for persona, grade in persona_grades.items():
        w = PERSONA_WEIGHTS.get(persona, 1.0)
        weighted_sum += grade * w
        total_weight += w
    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight


def _verdict(composite: float, p0_count: int) -> str:
    if p0_count > 0:
        return "Needs Work"
    if composite >= 3.5:
        return "Ready"
    if composite >= 2.5:
        return "Needs Work"
    return "Not Ready"


def _write_summary(out_dir: Path, *, dim_blocks: list[dict], persona_grades: dict[str, float],
                   composite: float, verdict: str, p0_count: int,
                   anti_patterns: list[dict]) -> None:
    lines: list[str] = [
        "# PRD Review Summary",
        "",
        f"**Verdict:** {verdict}",
        f"**Composite:** {composite:.2f} ({_numeric_to_letter(composite)})",
        f"**P0 findings:** {p0_count}",
        "",
        "## Persona grades",
        "",
        "| Persona | Grade | Weight |",
        "|---|---|---|",
    ]
    for persona in sorted(persona_grades):
        letter = _numeric_to_letter(persona_grades[persona])
        weight = PERSONA_WEIGHTS.get(persona, 1.0)
        lines.append(f"| {persona} | {letter} ({persona_grades[persona]:.2f}) | {weight} |")
    lines += ["", "## Dimension grades", "", "| Dim | Name | Grade |", "|---|---|---|"]
    for d in sorted(dim_blocks, key=lambda x: x["id"]):
        lines.append(f"| {d['id']} | {d.get('name','')} | {d.get('grade','')} |")
    if anti_patterns:
        lines += ["", "## Anti-patterns", ""]
        for ap in anti_patterns:
            ev = ap.get("evidence_quote", "")
            line_no = ap.get("evidence_line", "")
            lines.append(f"- **{ap['name']}** (line {line_no}): {ev}")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatch-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    dispatch_dir = Path(args.dispatch_dir)
    out_dir = Path(args.out_dir)
    if not dispatch_dir.exists() or not dispatch_dir.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"dispatch-dir not a directory: {args.dispatch_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    dim_blocks, anti_patterns = _collect_dim_blocks(dispatch_dir)

    found_dims = {d["id"] for d in dim_blocks}
    missing_dims = sorted(ALL_DIMS - found_dims)

    p0_count = _count_p0s(dim_blocks)
    persona_grades = _persona_grades(dim_blocks)
    composite = _composite(persona_grades)
    verdict = _verdict(composite, p0_count)

    review_comments = {
        "dimensions": sorted(dim_blocks, key=lambda d: d["id"]),
        "anti_patterns": anti_patterns,
        "composite": round(composite, 4),
        "verdict": verdict,
        "p0_count": p0_count,
        "persona_grades": {p: round(g, 4) for p, g in persona_grades.items()},
    }
    (out_dir / "review-comments.json").write_text(
        json.dumps(review_comments, indent=2), encoding="utf-8"
    )
    _write_summary(out_dir, dim_blocks=dim_blocks, persona_grades=persona_grades,
                   composite=composite, verdict=verdict, p0_count=p0_count,
                   anti_patterns=anti_patterns)

    data = {
        "composite": round(composite, 4),
        "verdict": verdict,
        "p0_count": p0_count,
        "review_comments_path": str((out_dir / "review-comments.json").resolve()),
        "summary_path": str((out_dir / "summary.md").resolve()),
    }

    if missing_dims:
        emit_error(code=EXIT_PARTIAL, category="partial",
                   reason=f"{len(missing_dims)} dim(s) missing from dispatch",
                   partial={**data, "missing_dims": missing_dims})
        return

    emit_success(data)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_aggregate_review.py -v`
Expected: 5 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/aggregate-review.sh`:

```bash
#!/usr/bin/env bash
# aggregate-review: composite + P0-gate from a directory of dim-block JSON files.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "aggregate-review: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet -- python "$SCRIPT_DIR/aggregate_review.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/aggregate-review.sh
git add shield/scripts/prd/aggregate-review.sh shield/scripts/prd/aggregate_review.py shield/scripts/prd/test_aggregate_review.py
git commit -m "feat(scripts/prd): add aggregate-review.sh + impl + tests

Combines dim-block JSON envelopes (both per-dim and per-persona shapes)
into review-comments.json + summary.md, computes weighted composite,
detects P0s (Critical D/F), applies P0-gate to verdict."
```

---

## Task 12: Build `filter-low-confidence.sh` + `filter_low_confidence.py`

Reads the `.prd-draft.confidence.json` sidecar that the LLM emits alongside the one-shot draft, returns the sorted list of section IDs marked `confidence: "low"`. These sections are walked interactively in `/prd`.

**Files:**
- Create: `shield/scripts/prd/filter-low-confidence.sh`
- Create: `shield/scripts/prd/filter_low_confidence.py`
- Create: `shield/scripts/prd/test_filter_low_confidence.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_filter_low_confidence.py`:

```python
"""Tests for filter_low_confidence.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


SIDECAR_MIX = {
    "sections": [
        {"id": 3, "confidence": "high"},
        {"id": 4, "confidence": "low"},
        {"id": 6, "confidence": "medium"},
        {"id": 9, "confidence": "low"},
        {"id": 15, "confidence": "low"},
    ]
}


def _run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "filter_low_confidence.py"), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_low_confidence_sections(tmp_path: Path) -> None:
    p = tmp_path / "conf.json"
    p.write_text(json.dumps(SIDECAR_MIX))
    code, payload = _run("--sidecar", str(p))
    assert code == 0
    assert payload["data"]["section_ids"] == [4, 9, 15]


def test_all_high_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / "conf.json"
    p.write_text(json.dumps({"sections": [{"id": 3, "confidence": "high"}]}))
    code, payload = _run("--sidecar", str(p))
    assert code == 0
    assert payload["data"]["section_ids"] == []


def test_missing_sidecar(tmp_path: Path) -> None:
    code, payload = _run("--sidecar", str(tmp_path / "nope.json"))
    assert code == 2


def test_malformed_sidecar(tmp_path: Path) -> None:
    p = tmp_path / "conf.json"
    p.write_text("not json")
    code, payload = _run("--sidecar", str(p))
    assert code == 2
    assert "json" in payload["reason"].lower()


def test_unknown_confidence_value_skipped(tmp_path: Path) -> None:
    p = tmp_path / "conf.json"
    p.write_text(json.dumps({"sections": [
        {"id": 3, "confidence": "high"},
        {"id": 4, "confidence": "low"},
        {"id": 9, "confidence": "??"},
    ]}))
    code, payload = _run("--sidecar", str(p))
    assert code == 0
    assert payload["data"]["section_ids"] == [4]
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_filter_low_confidence.py -v`
Expected: FAIL.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/filter_low_confidence.py`:

```python
"""filter-low-confidence: list §-IDs tagged 'low' confidence in draft sidecar."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _contract import EXIT_INVALID_INPUT, emit_error, emit_success

VALID = {"high", "medium", "low"}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sidecar", required=True)
    args = parser.parse_args(argv)

    p = Path(args.sidecar)
    if not p.exists() or p.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"sidecar path not a file: {args.sidecar}")
        return
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"sidecar is not valid json: {e}")
        return

    sections = payload.get("sections", [])
    low = sorted({s["id"] for s in sections if s.get("confidence") in VALID and s.get("confidence") == "low"})
    emit_success({"section_ids": low})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pytest pytest test_filter_low_confidence.py -v`
Expected: 5 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/filter-low-confidence.sh`:

```bash
#!/usr/bin/env bash
# filter-low-confidence: list §-IDs the one-shot draft marked low confidence.
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "filter-low-confidence: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet -- python "$SCRIPT_DIR/filter_low_confidence.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/filter-low-confidence.sh
git add shield/scripts/prd/filter-low-confidence.sh shield/scripts/prd/filter_low_confidence.py shield/scripts/prd/test_filter_low_confidence.py
git commit -m "feat(scripts/prd): add filter-low-confidence.sh + impl + tests

Parses the .prd-draft.confidence.json sidecar and returns §-IDs tagged
'low'. Used by /prd to determine which sections need an interactive
walk after one-shot generation."
```

---


## Task 13: Build `update-manifest.sh` + `update_manifest.py`

Rebuilds `{output_dir}/manifest.json` from filesystem state by reusing the existing `build_manifest()` function in `shield/scripts/migrate_outputs.py`. This is idempotent — running it twice produces the same output. **Index.html regeneration is intentionally out of scope for Plan 1**; the spec's §8 step (f) calls for it, and Plan 2 will extend this script (or add a sibling) to handle that.

**Files:**
- Create: `shield/scripts/prd/update-manifest.sh`
- Create: `shield/scripts/prd/update_manifest.py`
- Create: `shield/scripts/prd/test_update_manifest.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_update_manifest.py`:

```python
"""Tests for update_manifest.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "update_manifest.py"), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def _make_feature(root: Path, name: str, *, with_prd: bool = False, with_research: bool = False) -> None:
    feat = root / name
    feat.mkdir(parents=True, exist_ok=True)
    if with_prd:
        (feat / "prd.md").write_text("# x\n")
    if with_research:
        (feat / "research.md").write_text("# y\n")


def test_rebuild_writes_manifest(tmp_path: Path) -> None:
    root = tmp_path / "docs" / "shield"
    _make_feature(root, "alpha-20260520", with_prd=True, with_research=True)
    _make_feature(root, "beta-20260521", with_prd=True)
    code, payload = _run("--output-dir", str(root))
    assert code == 0
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["schema_version"] == 2
    names = {f["name"] for f in manifest["features"]}
    assert names == {"alpha-20260520", "beta-20260521"}
    alpha = next(f for f in manifest["features"] if f["name"] == "alpha-20260520")
    assert alpha["artifacts"]["prd"] is True
    assert alpha["artifacts"]["research"] is True


def test_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "docs" / "shield"
    _make_feature(root, "alpha-20260520", with_prd=True)
    _run("--output-dir", str(root))
    first = (root / "manifest.json").read_text()
    _run("--output-dir", str(root))
    second = (root / "manifest.json").read_text()
    # Idempotent ignoring the `updated` timestamp.
    f1 = json.loads(first); f2 = json.loads(second)
    for f in f1["features"] + f2["features"]:
        f.pop("updated", None)
    assert f1 == f2


def test_missing_output_dir(tmp_path: Path) -> None:
    code, payload = _run("--output-dir", str(tmp_path / "nope"))
    assert code == 2
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_update_manifest.py -v`
Expected: FAIL.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/update_manifest.py`:

```python
"""update-manifest: rebuild {output_dir}/manifest.json from filesystem state.

Delegates to shield/scripts/migrate_outputs.py:build_manifest — the
documented source of truth per shield/skills/general/manifest-schema.md.

Index.html regeneration is intentionally NOT done by this script in
Plan 1. Plan 2 will extend it (or add a sibling render-index script).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
# Add sibling scripts/ dir for build_manifest import.
sys.path.insert(0, str(SCRIPT_DIR.parent))

from _contract import EXIT_INVALID_INPUT, emit_error, emit_success
from migrate_outputs import build_manifest  # type: ignore[import-not-found]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"output-dir not a directory: {args.output_dir}")
        return

    manifest = build_manifest(output_dir)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    emit_success({
        "manifest_path": str(manifest_path.resolve()),
        "feature_count": len(manifest["features"]),
        "index_html_regenerated": False,  # deferred to Plan 2 per spec §8(f)
    })


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_update_manifest.py -v`
Expected: 3 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/update-manifest.sh`:

```bash
#!/usr/bin/env bash
# update-manifest: rebuild {output_dir}/manifest.json from filesystem state.
#
# NOTE: Plan 1 only rebuilds manifest.json. index.html regeneration is
# Plan 2 scope — see docs/superpowers/specs/2026-05-23-prd-and-prd-review-restructure-design.md §8(f).
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "update-manifest: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet --with pyyaml -- python "$SCRIPT_DIR/update_manifest.py" "$@"
```

- [ ] **Step 6: chmod + commit**

```bash
chmod +x shield/scripts/prd/update-manifest.sh
git add shield/scripts/prd/update-manifest.sh shield/scripts/prd/update_manifest.py shield/scripts/prd/test_update_manifest.py
git commit -m "feat(scripts/prd): add update-manifest.sh + impl + tests

Rebuilds {output_dir}/manifest.json by delegating to the existing
build_manifest() in shield/scripts/migrate_outputs.py. Idempotent.
Index.html regeneration is Plan 2 scope."
```

---

## Task 14: Build `finalize-prd.sh` + `finalize_prd.py`

The capstone script. Atomic copy + render + cleanup + meta update + manifest rebuild. If any step fails, exits non-zero and leaves the temp draft in place (so the user can resume).

**Contract:** `finalize-prd.sh --entry prd|prd-review --feature X --draft <path> [--review-dir <path>]`

**Steps inside the script (all-or-nothing):**

1. Pre-flight: `uv` installed? Draft file exists? Feature dir exists/writable? Each failure → distinct exit code with payload.
2. `cp <draft> {feature_dir}/prd.md`.
3. Render `{feature_dir}/outputs/prd.html` via the existing `shield/scripts/render-markdown.sh` (with the shell-HTML scaffold pattern from prd-docs/SKILL.md step 15).
4. Update `{feature_dir}/prd.meta.json` (`last_updated`, `source_command`, `review_link`).
5. Delete the temp:
   - `--entry prd`: rm `{feature_dir}/.prd-draft.md` and `{feature_dir}/.prd-draft.confidence.json`
   - `--entry prd-review`: rm `<review_dir>/corrected-prd.md`
6. Call `update-manifest.sh --output-dir <parent-of-feature-dir>`.

For Plan 1, **steps 3 (HTML render) and 4 (prd.meta.json update with a richly-templated shell) are simplified**: HTML rendering uses a minimal shell template (placeholder `{{BODY}}` only — no nav/TOC/sidecar-meta; those are Plan 2 scope). Plan 2 wires the full HTML shell once `prd/SKILL.md` and `templates.md` exist.

**Files:**
- Create: `shield/scripts/prd/finalize-prd.sh`
- Create: `shield/scripts/prd/finalize_prd.py`
- Create: `shield/scripts/prd/test_finalize_prd.py`

- [ ] **Step 1: Write the failing test**

Write to `shield/scripts/prd/test_finalize_prd.py`:

```python
"""Tests for finalize_prd.py."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # shield/scripts/prd → repo root


def _run(*args: str, env_override: dict | None = None) -> tuple[int, dict]:
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "finalize_prd.py"), *args],
        capture_output=True, text=True, env=env,
    )
    return proc.returncode, json.loads(proc.stdout)


def _setup_output_tree(tmp_path: Path, feature: str = "alpha-20260523") -> Path:
    """Create {tmp_path}/docs/shield/{feature}/ structure; return output_dir path."""
    output_dir = tmp_path / "docs" / "shield"
    feat_dir = output_dir / feature
    feat_dir.mkdir(parents=True)
    return output_dir


def test_finalize_prd_entry(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    draft = feat_dir / ".prd-draft.md"
    draft.write_text("# Alpha PRD\n\nbody.\n")
    confidence = feat_dir / ".prd-draft.confidence.json"
    confidence.write_text('{"sections":[]}')
    code, payload = _run(
        "--entry", "prd",
        "--feature-dir", str(feat_dir),
        "--draft", str(draft),
        "--output-dir", str(output_dir),
    )
    assert code == 0, payload
    # Canonical written.
    assert (feat_dir / "prd.md").read_text() == "# Alpha PRD\n\nbody.\n"
    # HTML rendered.
    assert (feat_dir / "outputs" / "prd.html").exists()
    # Meta written.
    meta = json.loads((feat_dir / "prd.meta.json").read_text())
    assert meta["source_command"] == "prd"
    assert meta["last_updated"]
    assert meta.get("review_link") is None
    # Temp draft cleaned up.
    assert not draft.exists()
    assert not confidence.exists()
    # Manifest written.
    assert (output_dir / "manifest.json").exists()


def test_finalize_prd_review_entry(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    review_dir = feat_dir / "reviews" / "prd" / "2026-05-23"
    review_dir.mkdir(parents=True)
    corrected = review_dir / "corrected-prd.md"
    corrected.write_text("# Corrected\n\nbody2.\n")
    # Side-artifacts that MUST survive cleanup.
    (review_dir / "summary.md").write_text("scorecard")
    (review_dir / "source-prd.md").write_text("orig")
    code, payload = _run(
        "--entry", "prd-review",
        "--feature-dir", str(feat_dir),
        "--draft", str(corrected),
        "--review-dir", str(review_dir),
        "--output-dir", str(output_dir),
    )
    assert code == 0, payload
    assert (feat_dir / "prd.md").read_text() == "# Corrected\n\nbody2.\n"
    # Temp corrected deleted.
    assert not corrected.exists()
    # Side-artifacts preserved.
    assert (review_dir / "summary.md").exists()
    assert (review_dir / "source-prd.md").exists()
    # Meta records review_link.
    meta = json.loads((feat_dir / "prd.meta.json").read_text())
    assert meta["source_command"] == "prd-review"
    assert meta["review_link"] == str(review_dir.resolve())


def test_missing_draft_exits_2(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    code, payload = _run(
        "--entry", "prd",
        "--feature-dir", str(feat_dir),
        "--draft", str(feat_dir / ".prd-draft.md"),  # does not exist
        "--output-dir", str(output_dir),
    )
    assert code == 2
    assert payload["category"] == "invalid_input"


def test_missing_review_dir_exits_2_for_prd_review(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    draft = feat_dir / "x.md"
    draft.write_text("# x\n")
    code, payload = _run(
        "--entry", "prd-review",
        "--feature-dir", str(feat_dir),
        "--draft", str(draft),
        "--output-dir", str(output_dir),
        # --review-dir omitted
    )
    assert code == 2


def test_html_rendered_when_md_changes(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    draft = feat_dir / ".prd-draft.md"
    draft.write_text("# version1\n")
    _run("--entry", "prd", "--feature-dir", str(feat_dir),
         "--draft", str(draft), "--output-dir", str(output_dir))
    html_v1 = (feat_dir / "outputs" / "prd.html").read_text()
    assert "version1" in html_v1

    # Second run with different content — html MUST be regenerated.
    draft2 = feat_dir / ".prd-draft.md"
    draft2.write_text("# version2\n")
    _run("--entry", "prd", "--feature-dir", str(feat_dir),
         "--draft", str(draft2), "--output-dir", str(output_dir))
    html_v2 = (feat_dir / "outputs" / "prd.html").read_text()
    assert "version2" in html_v2
    assert html_v1 != html_v2
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_finalize_prd.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the Python implementation**

Write to `shield/scripts/prd/finalize_prd.py`:

```python
"""finalize-prd: atomic copy + render + cleanup + meta update + manifest rebuild.

Called by both /prd and /prd-review at the end of their flows. If any
step fails, exits non-zero and leaves the temp draft in place so the
user can resume.

Plan 1 scope: minimal HTML shell ({{BODY}} placeholder only). Plan 2
extends with TOC, nav header, sidecar references.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parent))  # for migrate_outputs

from _contract import (
    EXIT_INTERNAL,
    EXIT_INVALID_INPUT,
    emit_error,
    emit_success,
)


MIN_SHELL_HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>PRD</title>
<style>body{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;line-height:1.5}
code{background:#f4f4f4;padding:.1rem .3rem;border-radius:3px}
pre{background:#f4f4f4;padding:.7rem;border-radius:6px;overflow-x:auto}
table{border-collapse:collapse}th,td{border:1px solid #ddd;padding:.4rem .6rem}</style>
</head><body>
{{BODY}}
</body></html>
"""


def _render_html(feature_dir: Path) -> Path:
    """Render prd.md → outputs/prd.html via shield/scripts/render-markdown.sh."""
    outputs = feature_dir / "outputs"
    outputs.mkdir(exist_ok=True)
    shell = feature_dir / ".prd.shell.html"
    shell.write_text(MIN_SHELL_HTML, encoding="utf-8")
    renderer = SCRIPT_DIR.parent / "render-markdown.sh"
    try:
        subprocess.run(
            [str(renderer),
             "--md", "prd.md",
             "--shell", ".prd.shell.html",
             "--out", "outputs/prd.html"],
            cwd=str(feature_dir),
            check=True,
            capture_output=True,
        )
    finally:
        if shell.exists():
            shell.unlink()
    return outputs / "prd.html"


def _write_meta(feature_dir: Path, *, source_command: str, review_link: Path | None) -> Path:
    meta_path = feature_dir / "prd.meta.json"
    existing: dict = {}
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing["last_updated"] = datetime.now(timezone.utc).isoformat()
    existing["source_command"] = source_command
    existing["review_link"] = str(review_link.resolve()) if review_link else None
    meta_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return meta_path


def _rebuild_manifest(output_dir: Path) -> Path:
    from migrate_outputs import build_manifest  # type: ignore[import-not-found]
    manifest = build_manifest(output_dir)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry", choices=["prd", "prd-review"], required=True)
    parser.add_argument("--feature-dir", required=True)
    parser.add_argument("--draft", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--review-dir", default=None)
    args = parser.parse_args(argv)

    # Pre-flight.
    if shutil.which("uv") is None:
        emit_error(code=EXIT_INTERNAL, category="environment",
                   reason="uv not installed",
                   suggested_action="install uv via curl -LsSf https://astral.sh/uv/install.sh | sh")
        return

    feature_dir = Path(args.feature_dir)
    draft = Path(args.draft)
    output_dir = Path(args.output_dir)
    review_dir = Path(args.review_dir) if args.review_dir else None

    if not feature_dir.exists() or not feature_dir.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"feature-dir not a directory: {args.feature_dir}")
        return
    if not draft.exists() or draft.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"draft path not a file: {args.draft}")
        return
    if not output_dir.exists() or not output_dir.is_dir():
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                   reason=f"output-dir not a directory: {args.output_dir}")
        return
    if args.entry == "prd-review":
        if review_dir is None:
            emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                       reason="--review-dir is required when --entry=prd-review")
            return
        if not review_dir.exists() or not review_dir.is_dir():
            emit_error(code=EXIT_INVALID_INPUT, category="invalid_input",
                       reason=f"review-dir not a directory: {args.review_dir}")
            return

    # Step 2: copy draft → prd.md
    canonical = feature_dir / "prd.md"
    canonical.write_text(draft.read_text(encoding="utf-8"), encoding="utf-8")

    # Step 3: render HTML.
    html_path = _render_html(feature_dir)

    # Step 4: meta.
    meta_path = _write_meta(
        feature_dir,
        source_command=args.entry,
        review_link=review_dir if args.entry == "prd-review" else None,
    )

    # Step 5: delete temp draft + sidecars.
    if args.entry == "prd":
        for f in (feature_dir / ".prd-draft.md",
                  feature_dir / ".prd-draft.confidence.json"):
            if f.exists():
                f.unlink()
    else:
        if draft.exists():
            draft.unlink()
        # Side-artifacts (summary.md, source-prd.md, detailed/, review-comments.json) are NOT removed.

    # Step 6: rebuild manifest.
    manifest_path = _rebuild_manifest(output_dir)

    emit_success({
        "prd_md": str(canonical.resolve()),
        "prd_html": str(html_path.resolve()),
        "prd_meta": str(meta_path.resolve()),
        "manifest": str(manifest_path.resolve()),
    })


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_finalize_prd.py -v`
Expected: 5 passed.

- [ ] **Step 5: Write shell wrapper**

Write to `shield/scripts/prd/finalize-prd.sh`:

```bash
#!/usr/bin/env bash
# finalize-prd: atomic copy + render + cleanup + meta update + manifest rebuild.
#
# See script-LLM contract for exit codes:
# .claude/skills/script-llm-contract/SKILL.md
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  echo "finalize-prd: uv is required; install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 127
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --quiet --with pyyaml --with markdown-it-py --with mdit-py-plugins -- python "$SCRIPT_DIR/finalize_prd.py" "$@"
```

- [ ] **Step 6: chmod + smoke test + commit**

```bash
chmod +x shield/scripts/prd/finalize-prd.sh

# Smoke test: full /prd path.
mkdir -p /tmp/smoke/docs/shield/test-20260523
echo "# smoke prd" > /tmp/smoke/docs/shield/test-20260523/.prd-draft.md
echo '{"sections":[]}' > /tmp/smoke/docs/shield/test-20260523/.prd-draft.confidence.json
shield/scripts/prd/finalize-prd.sh \
  --entry prd \
  --feature-dir /tmp/smoke/docs/shield/test-20260523 \
  --draft /tmp/smoke/docs/shield/test-20260523/.prd-draft.md \
  --output-dir /tmp/smoke/docs/shield
ls /tmp/smoke/docs/shield/test-20260523/
# Expected: prd.md, prd.meta.json, outputs/ (containing prd.html). No .prd-draft.md.

git add shield/scripts/prd/finalize-prd.sh shield/scripts/prd/finalize_prd.py shield/scripts/prd/test_finalize_prd.py
git commit -m "feat(scripts/prd): add finalize-prd.sh + impl + tests

Capstone script: atomic copy + render + cleanup + meta update + manifest
rebuild. Called by both /prd and /prd-review. Plan 1 uses a minimal HTML
shell ({{BODY}} placeholder only); Plan 2 wires the full nav/TOC/sidecar
shell once prd/SKILL.md and templates.md exist."
```

---

## Self-Review

**Spec coverage:** Walked every script + skill mentioned in spec §11, §12.

| Spec entry | Plan task |
|---|---|
| script-llm-contract skill (spec §12) | Task 1 |
| dim-section-map.yaml (spec §10) | Task 2 |
| prd-ingest.sh (spec §11) | Task 4 |
| detect-prd-type.sh (spec §11) | Task 5 |
| next-review-dir.sh (spec §11) | Task 6 |
| extract-glossary-candidates.sh (spec §11, §5.1) | Task 7 |
| count-term-in-body.sh (spec §11, §5.1) | Task 8 |
| sparse-sections.sh (spec §11) | Task 9 |
| map-gaps-to-sections.sh (spec §11) | Task 10 |
| aggregate-review.sh (spec §11) | Task 11 |
| filter-low-confidence.sh (spec §11) | Task 12 |
| update-manifest.sh (spec §8, §11) | Task 13 (manifest only — index.html deferred to Plan 2) |
| finalize-prd.sh (spec §8, §11) | Task 14 (minimal HTML shell — Plan 2 swaps in full shell with TOC + nav) |

**Spec coverage deferred to Plan 2 (intentional):**

- Consolidated `shield/skills/general/prd/SKILL.md` orchestrator (spec §4, §6, §7).
- `templates.md`, `rubric.md`, `dimensions.md`, `prompts/`, `scoring.md`, `ingest.md`, `meta-schema.md`, `type-detection.md` content (spec §5, §9, §10).
- DX engineer agent's `implementation-detail-bleed` anti-pattern (spec §9.3).
- Commands `prd.md`, `prd-review.md` rewrites (spec §6, §7).
- Evals listed in spec §13 — covered as user-flow evals in Plan 2 (Plan 1 ships only the script unit tests, which is necessary but not sufficient).
- Delete legacy directories `prd-docs/`, `prd-review/` (spec §15).
- Marketplace version bump (spec §17).
- Index.html regeneration in `update-manifest.sh` / `finalize-prd.sh` (spec §8 step f).
- Full HTML shell with TOC + nav + sidecar-meta in `finalize-prd.sh` (spec §8 step c).

**Placeholder scan:** None — every step has the full code or full command needed.

**Type consistency:** Cross-checked envelope shape — every script returns `{"ok": true, "data": ...}` on success and the error envelope shape on non-zero exit. `data` keys are consistent: scripts that produce paths return them as absolute via `str(p.resolve())`. The dim-block / per-persona JSON shape used in `aggregate_review.py` matches the shape returned by today's reviewer prompts (per `prompts/problem-clarity.md` and the legacy persona skeleton in `prd-review/SKILL.md` §4).

**Risks called out:**

- `_contract.py` is imported by every Python script via a `sys.path.insert`. If someone moves the scripts or installs them as a package, this breaks. Mitigation: keep all scripts colocated in `shield/scripts/prd/`. (Same pattern as existing `path_resolver.py` consumers in `shield/scripts/`.)
- `update_manifest.py` imports `build_manifest` from `shield/scripts/migrate_outputs.py` via `sys.path.insert(scripts_parent)`. If that function is renamed or moved, this breaks — add a comment on `build_manifest()` upstream. Defensive note added in the script's docstring.
- `aggregate_review.py` hardcodes `DIM_PERSONA` + `PERSONA_WEIGHTS`. These also live in `dimensions.md`. **Single source of truth violation** — if dimensions.md changes (e.g., dim 13 weight) and the script isn't updated, results drift. Plan 2 should resolve this by moving the table into a YAML config alongside `dim-section-map.yaml`.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-23-prd-restructure-foundation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Best fit for this plan: 14 tasks × ~6 steps each is ideal subagent shape (each subagent owns one script end-to-end).

**2. Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints.

Which approach? (After Plan 1 ships, ask me to write Plan 2 — the consolidated `prd/` skill + scaffold + commands + cutover.)
