# Shield SAST Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a SAST integration layer alongside the existing skill-driven backend review — two reference adapters (Semgrep, SonarQube Community) sharing a normalized finding schema, plugged into `backend-reviewer` via parallel dispatch with location-based dedup.

**Architecture:** Each adapter is a `adapter.md` (LLM-readable contract) + `adapter.py` (deterministic invocation/parsing) under `shield/adapters/sast/<tool>/`, mirroring the existing `shield/adapters/clickup/` pattern. Adapters opt-in via `.shield.json` `sast.adapters` list. Each adapter runs a layered fallback: consume existing output (if mtime-fresh) → invoke locally → best-effort skip with note. Adapters and skill agents run concurrently; aggregation dedups by file path + ±2 line range. SAST findings without a skill overlap surface in a dedicated "Repo-wide SAST findings" section.

**Tech Stack:** Python 3.11+ (matches existing `shield/adapters/clickup/server/`), pydantic for schema, stdlib json/subprocess/urllib for runtime. Markdown contracts. YAML for Semgrep rule packs. No new top-level dependencies — reuses what clickup adapter already pulls in.

---

## Spec reference

This plan implements `docs/superpowers/specs/2026-05-07-shield-sast-integration-design.md`. Read the spec first; this plan assumes its terminology and decisions.

## Scope of this plan (Plan 4)

**In scope:**
- Adapter framework foundation (directory layout, finding schema doc, severity mapping doc, README)
- Semgrep adapter (`adapter.md`, `adapter.py`, 4 custom rule pack YAMLs, mock-based parser tests)
- SonarQube adapter (`adapter.md`, `adapter.py`, sample `sonar-project.properties`, mock-based parser tests)
- `backend-reviewer.md` updates: `sast.adapters` configuration lookup, parallel dispatch, output format extensions
- Onboarding doc (`shield/adapters/sast/GETTING-STARTED.md`)
- End-to-end validation against the existing `spring-boot-api` fixture
- Bump shield to next minor version

**Out of scope (explicitly deferred):**
- `recommended-rules.md` mapping doc (rejected during design)
- `.shield.json` `sast.suppress` config (v1 uses tool-native suppression only)
- SonarQube branch analysis (paid feature)
- Spring Boot 2.x rule packs (Plan 5+ via `EXTENDING-VERSIONS.md` Pattern A)
- Additional adapters (SpotBugs, gitleaks, CodeQL — Plan 5+)
- CI workflow generation (users wire up their own)
- Auto-fix application for SAST findings
- Integration test suite invoking real tools (gated `pytest -m integration` infrastructure shipped, but actual integration runs deferred to release-time validation)

**Plan ordering caveat:** Plan 3 (SDLC integration into `/plan`, `/plan-review`, `/implement`) is in the design queue but not yet drafted. Plan 3 also modifies `shield/agents/backend-reviewer.md`. If Plan 3 and Plan 4 are executed on overlapping branches, expect a merge conflict in that file. Recommendation: execute on a fresh branch off main and rebase/resolve at PR time.

---

## File structure

**New files:**

```
shield/adapters/sast/
  ├── README.md                            (~80 lines)
  ├── finding-schema.md                    (~60 lines)
  ├── severity-mapping.md                  (~40 lines)
  ├── GETTING-STARTED.md                   (~120 lines, onboarding)
  ├── __init__.py                          (empty marker for Python imports)
  ├── common.py                            (~50 lines — Finding/AdapterResult dataclasses, shared types)
  ├── tests/
  │   ├── __init__.py
  │   └── test_common.py                   (~30 lines — schema validation)
  ├── semgrep/
  │   ├── __init__.py
  │   ├── adapter.md                       (~90 lines)
  │   ├── adapter.py                       (~150 lines)
  │   ├── rules/
  │   │   ├── spring-security.yml          (~40 lines)
  │   │   ├── spring-data.yml              (~30 lines)
  │   │   ├── spring-config.yml            (~30 lines)
  │   │   └── spring-web.yml               (~25 lines)
  │   └── tests/
  │       ├── __init__.py
  │       ├── conftest.py                  (~20 lines — fixture loader)
  │       ├── fixtures/
  │       │   ├── empty-output.json        (a valid Semgrep result with zero findings)
  │       │   ├── spring-boot-api-output.json   (real captured output, ~10 findings)
  │       │   └── invocation-error.json    (Semgrep error format sample)
  │       └── test_adapter.py              (~140 lines — parser + dispatch tests)
  └── sonarqube/
      ├── __init__.py
      ├── adapter.md                       (~110 lines)
      ├── adapter.py                       (~220 lines)
      ├── examples/
      │   └── sonar-project.properties     (~25 lines — recommended baseline)
      └── tests/
          ├── __init__.py
          ├── conftest.py                  (~20 lines)
          ├── fixtures/
          │   ├── empty-issues.json        (REST API empty response)
          │   ├── sample-issues.json       (REST API with ~5 issues)
          │   ├── sample-sarif.json        (SARIF export sample)
          │   └── stale-report-task.txt    (Maven report-task.txt sample)
          └── test_adapter.py              (~180 lines — parser + freshness + dispatch tests)
```

**Modified files:**

| File | Change |
|---|---|
| `shield/agents/backend-reviewer.md` | Add `## SAST Adapters` section after `## Skill Loading`. Add SAST output format extensions to `## Output Format` (header line, "Repo-wide SAST findings" section). Add SAST dispatch to `## Review Process`. |
| `.claude-plugin/marketplace.json` | Bump shield from `2.11.0` (after Plan 2) to `2.12.0` |

(Note: Plan 3 not yet executed; if Plan 3 lands first, the version bump in Plan 4 should be `next minor after Plan 3`.)

---

## Conventions used in this plan

- **TDD per Python module:** write a test using a fixture, run it (RED), implement, run again (GREEN), commit.
- **Test fixtures are real captured tool outputs.** Generate once by running the tool against the existing `spring-boot-api` fixture, then commit the JSON. Tests then run deterministically without tool installation.
- **All file paths are absolute** from the repo root: `/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/`.
- **Commits are per task** unless a step explicitly says otherwise. Conventional Commits (`feat(shield):`, `chore(shield):`).
- **Python is run via `uv run`** to match `shield/adapters/clickup/`. Test runner: `pytest`.
- **adapter.md content is hand-written markdown** — the LLM reads it; the engineer writes it.
- **adapter.py content is exact** — copy from this plan; don't paraphrase.

---

### Task 1: Adapter framework foundation

**Files:**
- Create: `shield/adapters/sast/__init__.py`
- Create: `shield/adapters/sast/common.py`
- Create: `shield/adapters/sast/README.md`
- Create: `shield/adapters/sast/finding-schema.md`
- Create: `shield/adapters/sast/severity-mapping.md`
- Create: `shield/adapters/sast/tests/__init__.py`
- Create: `shield/adapters/sast/tests/test_common.py`

- [ ] **Step 1: Create the directory marker**

```bash
mkdir -p shield/adapters/sast/tests
touch shield/adapters/sast/__init__.py shield/adapters/sast/tests/__init__.py
```

- [ ] **Step 2: Write the shared dataclasses module**

Write `shield/adapters/sast/common.py`:

```python
"""Shared types for shield SAST adapters.

Each adapter normalizes its tool's output to the dataclasses defined here.
The normalized findings flow into backend-reviewer's aggregation step,
which dedups by file + overlapping line range.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Severity = Literal["high", "medium", "low"]
Category = Literal["security", "code-quality", "performance", "reliability", "style"]


@dataclass
class Finding:
    """A single normalized SAST finding."""
    source: str          # adapter name, e.g., "semgrep"
    rule_id: str         # tool-native rule ID
    file: str            # path relative to repo root
    lines: str           # "27" or "27-29"
    severity: Severity
    category: Category
    message: str
    fix_hint: str | None = None


@dataclass
class AdapterResult:
    """Result of a single adapter run."""
    source: str
    mode: Literal["consumed", "invoked", "unavailable"]
    runtime_seconds: float
    findings: list[Finding] = field(default_factory=list)
    note: str | None = None  # for "best-effort" messages or invocation errors
```

- [ ] **Step 3: Write the schema test**

Write `shield/adapters/sast/tests/test_common.py`:

```python
"""Tests for the shared Finding/AdapterResult dataclasses."""

from shield.adapters.sast.common import Finding, AdapterResult


def test_finding_construction():
    f = Finding(
        source="semgrep",
        rule_id="java.spring.security.noop-encoder",
        file="src/main/java/Foo.java",
        lines="17",
        severity="high",
        category="security",
        message="NoOpPasswordEncoder stores plaintext",
    )
    assert f.source == "semgrep"
    assert f.fix_hint is None


def test_finding_with_fix_hint():
    f = Finding(
        source="semgrep",
        rule_id="x",
        file="x.java",
        lines="1",
        severity="medium",
        category="code-quality",
        message="x",
        fix_hint="Use BCrypt instead",
    )
    assert f.fix_hint == "Use BCrypt instead"


def test_adapter_result_default_findings():
    r = AdapterResult(
        source="semgrep",
        mode="invoked",
        runtime_seconds=1.5,
    )
    assert r.findings == []
    assert r.note is None


def test_adapter_result_unavailable():
    r = AdapterResult(
        source="sonarqube",
        mode="unavailable",
        runtime_seconds=0.0,
        note="sonarqube adapter — credentials missing",
    )
    assert r.mode == "unavailable"
    assert r.findings == []
```

- [ ] **Step 4: Run the tests**

```bash
cd shield/adapters/sast
uv run pytest tests/test_common.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Write the README**

Write `shield/adapters/sast/README.md`:

```markdown
# Shield SAST Adapters

This directory holds adapters that integrate Static Application Security Testing (SAST) tools into shield's `backend-reviewer` agent.

## Why SAST adapters

Shield's backend-domain skills (under `shield/skills/backend/`) are LLM-driven rubrics. They excel at architectural and judgment-based review (god class detection, YAGNI, deployment-safety reasoning) but duplicate work for pattern-detectable checks (annotations, imports, fixed call patterns) that SAST tools handle deterministically.

Plan 4 introduces a hybrid: SAST tools run alongside skills for the deterministic checks; skills focus on the judgment layer. Findings from both flow through the same aggregation pipeline.

See the design spec at `docs/superpowers/specs/2026-05-07-shield-sast-integration-design.md` for the full rationale.

## How adapters work

Each adapter lives in `<tool>/` (e.g., `semgrep/`, `sonarqube/`) and provides:

- `adapter.md` — LLM-readable contract: what the adapter does, how it's configured, what fallback modes it supports
- `adapter.py` — Python runtime: invokes the tool (or consumes its output), parses results, normalizes them to the schema in `common.py`
- `tests/fixtures/` — captured tool output samples for deterministic parser tests
- `tests/test_adapter.py` — pytest tests over the parser + dispatch logic

When `backend-reviewer` runs, it iterates the `sast.adapters` list from `.shield.json` and calls each adapter's `run()` function in parallel with the skill review.

## Layered fallback

Each adapter tries three modes in order:

1. **Consume existing output.** Look for SAST output at known paths. If the mtime is newer than the HEAD commit, parse and return.
2. **Invoke locally.** If no fresh output found, check the tool is installed and run it on the target path.
3. **Best-effort skip.** If the tool isn't available and can't be invoked, return zero findings with a `note` field. Don't fail the review.

Stale output (mtime older than HEAD commit) is treated as missing — fall through to invoke or skip.

## Adding a new adapter

1. Create `shield/adapters/sast/<tool>/` with `adapter.md`, `adapter.py`, `tests/`
2. Implement `run(target_path: str, config: dict, credentials: dict | None) -> AdapterResult`
3. Add fixture-based parser tests under `tests/`
4. Update `shield/agents/backend-reviewer.md` Skill Loading and Configuration sections to mention the new adapter
5. Document configuration knobs in `adapter.md`

## Adapters

- `semgrep/` — Lightweight CLI pattern matcher. Ships custom rule packs for Spring 3.x patterns. Default mode: invoke locally.
- `sonarqube/` — Self-hosted code-quality server. Reads existing reports via REST API or SARIF; falls back to local `sonar-scanner`. Default mode: consume.
```

- [ ] **Step 6: Write the finding schema doc**

Write `shield/adapters/sast/finding-schema.md`:

```markdown
# Normalized Finding Schema

Every SAST adapter normalizes its tool's output to this schema before returning it. Definitions live in `common.py` as Python dataclasses.

## Finding

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | yes | Adapter name, e.g. `"semgrep"`, `"sonarqube"` |
| `rule_id` | string | yes | Tool-native rule ID (e.g. `"java.spring.security.csrf-disabled"`, `"java:S5547"`) |
| `file` | string | yes | Path relative to repo root |
| `lines` | string | yes | Single line `"27"` or range `"27-29"` |
| `severity` | enum | yes | `"high"` \| `"medium"` \| `"low"` (see `severity-mapping.md`) |
| `category` | enum | yes | `"security"` \| `"code-quality"` \| `"performance"` \| `"reliability"` \| `"style"` |
| `message` | string | yes | One-line description from the tool |
| `fix_hint` | string | no | Recommended fix, when the tool provides one |

## AdapterResult

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | yes | Adapter name |
| `mode` | enum | yes | `"consumed"` \| `"invoked"` \| `"unavailable"` |
| `runtime_seconds` | float | yes | How long the adapter took |
| `findings` | list[Finding] | yes | May be empty |
| `note` | string | no | Used for best-effort skip messages, invocation errors |

## Dedup

Findings dedupe at aggregation by:

- `file` (exact match)
- `lines` (overlapping range within ±2)

Two findings on the same file/line area collapse to a single entry citing all `source` fields. No skill↔rule mapping is required — location overlap is sufficient.

SAST findings whose location does not overlap any skill finding surface in a dedicated "Repo-wide SAST findings" section in the report.
```

- [ ] **Step 7: Write the severity mapping doc**

Write `shield/adapters/sast/severity-mapping.md`:

```markdown
# Severity Mapping Reference

Each SAST tool has its own severity scale. Adapters map tool-native severities to shield's normalized `high` / `medium` / `low` when emitting findings.

## Semgrep

| Tool-native | Normalized |
|---|---|
| `ERROR` | high |
| `WARNING` | medium |
| `INFO` | low |

## SonarQube

| Tool-native | Normalized |
|---|---|
| `BLOCKER` | high |
| `CRITICAL` | high |
| `MAJOR` | medium |
| `MINOR` | low |
| `INFO` | low |

## Edge cases

- Tool-native severity not in the table → default to `medium`. The adapter logs a one-line warning to stderr so operators notice.
- Tool emits no severity at all → default to `medium`.
- New severity levels added by tool upstream → add a row here when adding the adapter version that uses them.

## Why this mapping

Shield's normalization is deliberately coarse (3 levels). Reasons:
- Cross-tool aggregation needs a common scale; finer granularity is tool-specific
- Reports are read by humans who scan for "is this a problem now?" — a binary-ish severity is more useful than a 5-point scale
- Severity calibration is the user's responsibility per their codebase; shield doesn't try to be authoritative
```

- [ ] **Step 8: Commit**

```bash
git add shield/adapters/sast/
git commit -m "feat(shield): scaffold SAST adapter framework — common types + framework docs"
```

---

### Task 2: Semgrep adapter — Python runtime

**Files:**
- Create: `shield/adapters/sast/semgrep/__init__.py`
- Create: `shield/adapters/sast/semgrep/adapter.py`
- Create: `shield/adapters/sast/semgrep/tests/__init__.py`
- Create: `shield/adapters/sast/semgrep/tests/conftest.py`
- Create: `shield/adapters/sast/semgrep/tests/fixtures/empty-output.json`
- Create: `shield/adapters/sast/semgrep/tests/fixtures/spring-boot-api-output.json`
- Create: `shield/adapters/sast/semgrep/tests/test_adapter.py`

- [ ] **Step 1: Create the directory + Python markers**

```bash
mkdir -p shield/adapters/sast/semgrep/tests/fixtures shield/adapters/sast/semgrep/rules
touch shield/adapters/sast/semgrep/__init__.py shield/adapters/sast/semgrep/tests/__init__.py
```

- [ ] **Step 2: Write the empty-output fixture**

Write `shield/adapters/sast/semgrep/tests/fixtures/empty-output.json`:

```json
{
  "version": "1.50.0",
  "results": [],
  "errors": [],
  "paths": {
    "scanned": ["src/main/java/com/example/api"],
    "skipped": []
  }
}
```

- [ ] **Step 3: Write the spring-boot-api sample fixture**

Write `shield/adapters/sast/semgrep/tests/fixtures/spring-boot-api-output.json`:

```json
{
  "version": "1.50.0",
  "results": [
    {
      "check_id": "java.spring.security.noop-encoder",
      "path": "shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java",
      "start": {"line": 17, "col": 9, "offset": 0},
      "end": {"line": 17, "col": 50, "offset": 41},
      "extra": {
        "severity": "ERROR",
        "message": "NoOpPasswordEncoder stores plaintext. Use BCrypt/Argon2/PBKDF2.",
        "metadata": {
          "category": "security",
          "shield-area": "spring-security"
        }
      }
    },
    {
      "check_id": "java.spring.security.csrf-disabled",
      "path": "shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java",
      "start": {"line": 27, "col": 13, "offset": 0},
      "end": {"line": 27, "col": 47, "offset": 34},
      "extra": {
        "severity": "ERROR",
        "message": "CSRF protection disabled without a stateless justification.",
        "metadata": {
          "category": "security",
          "shield-area": "spring-security"
        }
      }
    },
    {
      "check_id": "java.spring.config.value-for-typed-config",
      "path": "shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java",
      "start": {"line": 27, "col": 5, "offset": 0},
      "end": {"line": 28, "col": 30, "offset": 60},
      "extra": {
        "severity": "WARNING",
        "message": "Use @ConfigurationProperties for typed config values rather than @Value.",
        "metadata": {
          "category": "code-quality",
          "shield-area": "spring-config"
        }
      }
    }
  ],
  "errors": [],
  "paths": {
    "scanned": ["shield/examples/spring-boot-api"],
    "skipped": []
  }
}
```

- [ ] **Step 4: Write the conftest fixture loader**

Write `shield/adapters/sast/semgrep/tests/conftest.py`:

```python
"""Shared test fixtures for the Semgrep adapter."""

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def empty_output() -> dict:
    return json.loads((FIXTURES_DIR / "empty-output.json").read_text())


@pytest.fixture
def spring_boot_api_output() -> dict:
    return json.loads((FIXTURES_DIR / "spring-boot-api-output.json").read_text())
```

- [ ] **Step 5: Write the failing parser tests**

Write `shield/adapters/sast/semgrep/tests/test_adapter.py`:

```python
"""Tests for the Semgrep adapter."""

from shield.adapters.sast.semgrep.adapter import (
    SEVERITY_MAP,
    _parse_semgrep_json,
)


def test_severity_mapping_complete():
    assert SEVERITY_MAP["ERROR"] == "high"
    assert SEVERITY_MAP["WARNING"] == "medium"
    assert SEVERITY_MAP["INFO"] == "low"


def test_parse_empty_output(empty_output):
    findings = _parse_semgrep_json(empty_output)
    assert findings == []


def test_parse_spring_boot_api_output(spring_boot_api_output):
    findings = _parse_semgrep_json(spring_boot_api_output)
    assert len(findings) == 3


def test_parse_finding_fields(spring_boot_api_output):
    findings = _parse_semgrep_json(spring_boot_api_output)
    f = findings[0]
    assert f.source == "semgrep"
    assert f.rule_id == "java.spring.security.noop-encoder"
    assert f.file == "shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java"
    assert f.lines == "17"
    assert f.severity == "high"
    assert f.category == "security"
    assert "NoOpPasswordEncoder" in f.message


def test_parse_multiline_range(spring_boot_api_output):
    """The third fixture finding spans lines 27-28."""
    findings = _parse_semgrep_json(spring_boot_api_output)
    multi = findings[2]
    assert multi.lines == "27-28"


def test_parse_severity_mapping(spring_boot_api_output):
    findings = _parse_semgrep_json(spring_boot_api_output)
    assert findings[0].severity == "high"  # ERROR
    assert findings[2].severity == "medium"  # WARNING


def test_parse_default_category_when_missing():
    payload = {
        "results": [
            {
                "check_id": "x",
                "path": "x.java",
                "start": {"line": 1},
                "end": {"line": 1},
                "extra": {"severity": "ERROR", "message": "x"}
            }
        ]
    }
    findings = _parse_semgrep_json(payload)
    assert findings[0].category == "code-quality"  # default


def test_parse_unknown_severity_defaults_medium():
    payload = {
        "results": [
            {
                "check_id": "x",
                "path": "x.java",
                "start": {"line": 1},
                "end": {"line": 1},
                "extra": {"severity": "FATAL_UNKNOWN", "message": "x"}
            }
        ]
    }
    findings = _parse_semgrep_json(payload)
    assert findings[0].severity == "medium"
```

- [ ] **Step 6: Run the failing tests**

```bash
cd shield/adapters/sast
uv run pytest semgrep/tests/test_adapter.py -v
```

Expected: ImportError (`adapter.py` doesn't exist yet) or NameError. This is the RED phase.

- [ ] **Step 7: Implement the parser**

Write `shield/adapters/sast/semgrep/adapter.py`:

```python
"""Semgrep SAST adapter for shield's backend-reviewer.

Default mode: invoke locally. Semgrep is fast (seconds for typical repos)
and parses to deterministic JSON. Custom shield rule packs ship under
`./rules/` and target Spring Boot 3.x patterns.

Layered fallback:
  1. Consume existing output (if --output path configured and mtime fresh)
  2. Invoke `semgrep --config <rules> --json <target_path>`
  3. Best-effort skip with note
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from shield.adapters.sast.common import (
    AdapterResult,
    Category,
    Finding,
    Severity,
)


SEVERITY_MAP: dict[str, Severity] = {
    "ERROR": "high",
    "WARNING": "medium",
    "INFO": "low",
}


VALID_CATEGORIES: set[Category] = {
    "security",
    "code-quality",
    "performance",
    "reliability",
    "style",
}


def _parse_semgrep_json(payload: dict[str, Any]) -> list[Finding]:
    """Convert Semgrep `--json` output to normalized findings.

    Semgrep result schema (relevant fields):
      results: [
        {
          check_id: str,
          path: str,
          start: { line: int, ... },
          end: { line: int, ... },
          extra: {
            severity: "ERROR" | "WARNING" | "INFO",
            message: str,
            metadata: { category: str, ... }
          }
        }
      ]
    """
    findings: list[Finding] = []
    for result in payload.get("results", []):
        check_id = result.get("check_id", "")
        path = result.get("path", "")
        start_line = result.get("start", {}).get("line", 0)
        end_line = result.get("end", {}).get("line", start_line)
        lines = f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}"

        extra = result.get("extra", {})
        severity_native = extra.get("severity", "INFO")
        severity: Severity = SEVERITY_MAP.get(severity_native, "medium")
        message = extra.get("message", "")

        category_raw = extra.get("metadata", {}).get("category", "code-quality")
        category: Category = (
            category_raw if category_raw in VALID_CATEGORIES else "code-quality"
        )

        findings.append(
            Finding(
                source="semgrep",
                rule_id=check_id,
                file=path,
                lines=lines,
                severity=severity,
                category=category,
                message=message,
            )
        )
    return findings


def _tool_available() -> bool:
    """Check `semgrep` is on PATH and runnable."""
    return shutil.which("semgrep") is not None


def _default_rules_path() -> str:
    """Path to shield's bundled rule packs."""
    return str(Path(__file__).parent / "rules")


def _consume_existing(output_path: Path, head_commit_time: float) -> list[Finding] | None:
    """Read pre-existing Semgrep output if fresh.

    Returns None if no output, output is stale, or output is unparseable.
    """
    if not output_path.exists():
        return None
    if output_path.stat().st_mtime < head_commit_time:
        return None
    try:
        payload = json.loads(output_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return _parse_semgrep_json(payload)


def _invoke_semgrep(target_path: str, rules_config: str) -> tuple[list[Finding], str | None]:
    """Run `semgrep` against `target_path` using `rules_config`.

    Returns (findings, error_note). `error_note` is None on success.
    """
    cmd = [
        "semgrep",
        "--config",
        rules_config,
        "--json",
        "--quiet",
        target_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return [], "semgrep adapter — invocation timed out after 120s"
    except OSError as e:
        return [], f"semgrep adapter — invocation error: {e}"

    # Semgrep returns 0 (clean) or 1 (findings present). Anything else is failure.
    if result.returncode not in (0, 1):
        return [], f"semgrep adapter — exit code {result.returncode}: {result.stderr[:200]}"

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return [], f"semgrep adapter — could not parse JSON output: {e}"

    return _parse_semgrep_json(payload), None


def run(
    target_path: str,
    config: dict[str, Any] | None = None,
    head_commit_time: float | None = None,
) -> AdapterResult:
    """Entry point for the Semgrep adapter.

    Layered fallback:
      1. If `config["output_path"]` is set, try to consume it (if mtime fresh).
      2. If semgrep is installed, invoke it locally.
      3. Otherwise, return AdapterResult with mode="unavailable".
    """
    config = config or {}
    start = time.time()

    # Mode 1: consume existing output
    output_path_str = config.get("output_path")
    if output_path_str and head_commit_time is not None:
        output_path = Path(output_path_str)
        consumed = _consume_existing(output_path, head_commit_time)
        if consumed is not None:
            return AdapterResult(
                source="semgrep",
                mode="consumed",
                runtime_seconds=time.time() - start,
                findings=consumed,
            )

    # Mode 2: invoke locally
    if _tool_available():
        rules = config.get("config") or _default_rules_path()
        findings, err = _invoke_semgrep(target_path, rules)
        return AdapterResult(
            source="semgrep",
            mode="invoked",
            runtime_seconds=time.time() - start,
            findings=findings,
            note=err,
        )

    # Mode 3: best-effort skip
    return AdapterResult(
        source="semgrep",
        mode="unavailable",
        runtime_seconds=time.time() - start,
        findings=[],
        note=(
            "semgrep adapter — tool not available; SAST coverage best-effort. "
            "Install with `pip install semgrep` to enable."
        ),
    )
```

- [ ] **Step 8: Run the tests — they should pass**

```bash
cd shield/adapters/sast
uv run pytest semgrep/tests/test_adapter.py -v
```

Expected: 8 passed.

- [ ] **Step 9: Commit**

```bash
git add shield/adapters/sast/semgrep/__init__.py \
        shield/adapters/sast/semgrep/adapter.py \
        shield/adapters/sast/semgrep/tests/
git commit -m "feat(shield): add Semgrep SAST adapter — parser, layered fallback, fixture tests"
```

---

### Task 3: Semgrep adapter — rule packs

**Files:**
- Create: `shield/adapters/sast/semgrep/rules/spring-security.yml`
- Create: `shield/adapters/sast/semgrep/rules/spring-data.yml`
- Create: `shield/adapters/sast/semgrep/rules/spring-config.yml`
- Create: `shield/adapters/sast/semgrep/rules/spring-web.yml`

- [ ] **Step 1: Write the spring-security rule pack**

Write `shield/adapters/sast/semgrep/rules/spring-security.yml`:

```yaml
rules:
  - id: java.spring.security.noop-encoder
    metadata:
      shield-area: spring-security
      shield-severity: high
    message: NoOpPasswordEncoder stores plaintext. Use BCrypt/Argon2/PBKDF2.
    languages: [java]
    severity: ERROR
    pattern: NoOpPasswordEncoder.getInstance()

  - id: java.spring.security.csrf-disabled
    metadata:
      shield-area: spring-security
      shield-severity: high
    message: CSRF disabled without a stateless justification. For browser flows with cookies, CSRF must be enabled.
    languages: [java]
    severity: ERROR
    pattern-either:
      - pattern: $H.csrf().disable()
      - pattern: $H.csrf(csrf -> csrf.disable())
      - pattern: $H.csrf((csrf) -> csrf.disable())

  - id: java.spring.security.permit-all-any-request
    metadata:
      shield-area: spring-security
      shield-severity: high
    message: anyRequest().permitAll() — authentication effectively disabled. Enumerate which endpoints are public.
    languages: [java]
    severity: ERROR
    pattern-either:
      - pattern: $A.anyRequest().permitAll()
      - pattern: |
          $H.authorizeHttpRequests($A -> $A.anyRequest().permitAll())
```

- [ ] **Step 2: Write the spring-data rule pack**

Write `shield/adapters/sast/semgrep/rules/spring-data.yml`:

```yaml
rules:
  - id: java.spring.data.transactional-on-private
    metadata:
      shield-area: spring-data
      shield-severity: high
    message: '@Transactional on a private method is a no-op. Spring AOP proxies do not intercept private methods.'
    languages: [java]
    severity: ERROR
    pattern: |
      @Transactional
      private $RET $METHOD(...) { ... }

  - id: java.spring.data.modifying-required
    metadata:
      shield-area: spring-data
      shield-severity: high
    message: 'Mutating @Query (UPDATE/DELETE) requires @Modifying. Without it, Spring treats it as SELECT and the change does not execute.'
    languages: [java]
    severity: ERROR
    pattern-either:
      - pattern: |
          @Query("UPDATE $...REST")
          $RET $METHOD(...);
      - pattern: |
          @Query("DELETE $...REST")
          $RET $METHOD(...);
    pattern-not-inside: |
      @Modifying
      ...
```

- [ ] **Step 3: Write the spring-config rule pack**

Write `shield/adapters/sast/semgrep/rules/spring-config.yml`:

```yaml
rules:
  - id: java.spring.config.properties-no-prefix
    metadata:
      shield-area: spring-config
      shield-severity: high
    message: '@ConfigurationProperties without prefix attribute — properties will not bind to nested keys correctly.'
    languages: [java]
    severity: ERROR
    pattern: |
      @ConfigurationProperties
      public class $C { ... }
    pattern-not: |
      @ConfigurationProperties(prefix=$P)
      public class $C { ... }

  - id: java.spring.config.value-for-typed-config
    metadata:
      shield-area: spring-config
      shield-severity: medium
    message: '@Value for typed config; prefer @ConfigurationProperties for type safety, defaults, and validation.'
    languages: [java]
    severity: WARNING
    pattern: |
      @Value("${$KEY:$DEFAULT}")
      private $TYPE $FIELD;
```

- [ ] **Step 4: Write the spring-web rule pack**

Write `shield/adapters/sast/semgrep/rules/spring-web.yml`:

```yaml
rules:
  - id: java.spring.web.field-injection
    metadata:
      shield-area: spring-web
      shield-severity: high
    message: 'Field injection via @Autowired. Prefer constructor injection with final fields.'
    languages: [java]
    severity: ERROR
    pattern: |
      @Autowired
      private $TYPE $FIELD;

  - id: java.spring.web.request-mapping-no-method
    metadata:
      shield-area: spring-web
      shield-severity: medium
    message: '@RequestMapping with no method attribute defaults to all methods. Use @PostMapping/@GetMapping/etc. or set method explicitly.'
    languages: [java]
    severity: WARNING
    pattern: |
      @RequestMapping($PATH)
      public $RET $METHOD(...) { ... }
    pattern-not: |
      @RequestMapping(value=$PATH, method=$M)
      public $RET $METHOD(...) { ... }
```

- [ ] **Step 5: Verify the rule pack files are well-formed YAML**

```bash
uv run python -c "
import yaml
from pathlib import Path
for path in Path('shield/adapters/sast/semgrep/rules').glob('*.yml'):
    data = yaml.safe_load(path.read_text())
    rules = data.get('rules', [])
    print(f'{path.name}: {len(rules)} rules')
    for r in rules:
        assert 'id' in r, f'rule missing id in {path}'
        assert 'metadata' in r, f'rule {r[\"id\"]} missing metadata'
        assert 'shield-area' in r['metadata'], f'rule {r[\"id\"]} missing shield-area'
        assert 'message' in r, f'rule {r[\"id\"]} missing message'
        assert 'severity' in r, f'rule {r[\"id\"]} missing severity'
"
```

Expected: each file prints "N rules" with no assertion errors.

- [ ] **Step 6: Commit**

```bash
git add shield/adapters/sast/semgrep/rules/
git commit -m "feat(shield): add Semgrep rule packs for Spring 3.x patterns"
```

---

### Task 4: Semgrep adapter — adapter.md contract

**Files:**
- Create: `shield/adapters/sast/semgrep/adapter.md`

- [ ] **Step 1: Write the adapter contract**

Write `shield/adapters/sast/semgrep/adapter.md`:

```markdown
# Semgrep SAST Adapter

LLM-readable contract for the Semgrep adapter. The Python runtime that executes this contract lives at `adapter.py`.

## What this adapter does

Runs Semgrep against the target codebase using shield's bundled Spring 3.x rule pack (or a user-overridden config), parses the `--json` output, and returns normalized findings to `backend-reviewer`.

## Configuration

In `.shield.json`:

```json
{
  "sast": {
    "adapters": ["semgrep"],
    "semgrep": {
      "config": "p/spring-boot-best-practices",
      "output_path": "target/semgrep-output.json"
    }
  }
}
```

| Key | Required | Default | Description |
|---|---|---|---|
| `config` | no | `shield/adapters/sast/semgrep/rules/` | Path or registry pack ID for Semgrep rules |
| `output_path` | no | (none) | Path to a pre-existing `semgrep --json` output file. Adapter will consume this if mtime is newer than HEAD commit. |

No credentials required. Optional `SEMGREP_APP_TOKEN` env var (for Semgrep Cloud) is honored by Semgrep itself; shield's adapter doesn't reference it.

## Layered fallback

1. **Consume existing output.** If `config.output_path` is set and the file's mtime is newer than HEAD commit time, parse it.
2. **Invoke locally.** If `semgrep` is on PATH, run `semgrep --config <rules> --json --quiet <target_path>` with a 120-second timeout.
3. **Best-effort skip.** If neither is possible, return zero findings with note: `"semgrep adapter — tool not available; SAST coverage best-effort. Install with `pip install semgrep` to enable."`

## Severity mapping

| Semgrep | shield |
|---|---|
| ERROR | high |
| WARNING | medium |
| INFO | low |

## v1 limitation: Spring Boot 3.x only

Bundled rules at `rules/spring-*.yml` target Spring Boot 3.x patterns:
- `csrf(csrf -> csrf.disable())` lambda DSL (SS6); will not match SB2's `csrf().disable()` chained DSL
- `@RequestMapping` with `jakarta.*` imports

Spring Boot 2.x patterns will not be flagged by these rules. To add SB2 coverage, follow Pattern A (broaden) per `EXTENDING-VERSIONS.md` — add a parallel set of patterns to each rule's `pattern-either` block, OR ship a sibling `spring-*-sb2.yml` rule pack.

## Behavior on unparseable output

If `semgrep --json` returns malformed JSON (rare but possible during interrupted runs), the adapter logs the error to its `note` field and returns zero findings. Don't fail the review.

## Testing

Parser tests at `tests/test_adapter.py` use captured fixtures (`tests/fixtures/*.json`). To regenerate fixtures, run Semgrep against the spring-boot-api fixture:

```bash
semgrep --config shield/adapters/sast/semgrep/rules \
        --json --quiet \
        shield/examples/spring-boot-api > \
        shield/adapters/sast/semgrep/tests/fixtures/spring-boot-api-output.json
```

The bundled rule packs themselves can be self-tested via `semgrep --test rules/`. Each rule pack ships with a `<name>.test.java` example that triggers the rule (and a `<name>.test.java` no-trigger negative case if needed).

## Related

- See `../README.md` for the framework overview
- See `../finding-schema.md` for the normalized finding shape
- See `../severity-mapping.md` for the full severity table
```

- [ ] **Step 2: Commit**

```bash
git add shield/adapters/sast/semgrep/adapter.md
git commit -m "docs(shield): add Semgrep adapter contract (adapter.md)"
```

---

### Task 5: SonarQube adapter — Python runtime

**Files:**
- Create: `shield/adapters/sast/sonarqube/__init__.py`
- Create: `shield/adapters/sast/sonarqube/adapter.py`
- Create: `shield/adapters/sast/sonarqube/tests/__init__.py`
- Create: `shield/adapters/sast/sonarqube/tests/conftest.py`
- Create: `shield/adapters/sast/sonarqube/tests/fixtures/empty-issues.json`
- Create: `shield/adapters/sast/sonarqube/tests/fixtures/sample-issues.json`
- Create: `shield/adapters/sast/sonarqube/tests/test_adapter.py`

- [ ] **Step 1: Create the directory + Python markers**

```bash
mkdir -p shield/adapters/sast/sonarqube/tests/fixtures shield/adapters/sast/sonarqube/examples
touch shield/adapters/sast/sonarqube/__init__.py shield/adapters/sast/sonarqube/tests/__init__.py
```

- [ ] **Step 2: Write the empty-issues fixture**

Write `shield/adapters/sast/sonarqube/tests/fixtures/empty-issues.json`:

```json
{
  "total": 0,
  "p": 1,
  "ps": 100,
  "paging": {"pageIndex": 1, "pageSize": 100, "total": 0},
  "issues": [],
  "components": []
}
```

- [ ] **Step 3: Write the sample-issues fixture**

Write `shield/adapters/sast/sonarqube/tests/fixtures/sample-issues.json`:

```json
{
  "total": 4,
  "p": 1,
  "ps": 100,
  "paging": {"pageIndex": 1, "pageSize": 100, "total": 4},
  "issues": [
    {
      "key": "AYbX1...",
      "rule": "java:S5547",
      "severity": "BLOCKER",
      "component": "tesseract:shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java",
      "project": "tesseract",
      "line": 17,
      "textRange": {"startLine": 17, "endLine": 21},
      "message": "Use a more secure password encoder than NoOpPasswordEncoder.",
      "type": "VULNERABILITY",
      "status": "OPEN"
    },
    {
      "key": "AYbX2...",
      "rule": "java:S4502",
      "severity": "CRITICAL",
      "component": "tesseract:shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java",
      "project": "tesseract",
      "line": 27,
      "textRange": {"startLine": 27, "endLine": 27},
      "message": "Make sure disabling CSRF protection is safe here.",
      "type": "VULNERABILITY",
      "status": "OPEN"
    },
    {
      "key": "AYbX3...",
      "rule": "java:S1144",
      "severity": "MAJOR",
      "component": "tesseract:shield/examples/spring-boot-api/src/main/java/com/example/api/service/UserService.java",
      "project": "tesseract",
      "line": 56,
      "textRange": {"startLine": 56, "endLine": 56},
      "message": "Remove this unused private field.",
      "type": "CODE_SMELL",
      "status": "OPEN"
    },
    {
      "key": "AYbX4...",
      "rule": "java:S100",
      "severity": "MINOR",
      "component": "tesseract:shield/examples/spring-boot-api/src/main/java/com/example/api/service/UserService.java",
      "project": "tesseract",
      "line": 61,
      "textRange": {"startLine": 61, "endLine": 76},
      "message": "Rename this method name to match the regular expression '^[a-z][a-zA-Z0-9]*$'.",
      "type": "CODE_SMELL",
      "status": "OPEN"
    }
  ],
  "components": []
}
```

- [ ] **Step 4: Write the conftest fixture loader**

Write `shield/adapters/sast/sonarqube/tests/conftest.py`:

```python
"""Shared test fixtures for the SonarQube adapter."""

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def empty_issues() -> dict:
    return json.loads((FIXTURES_DIR / "empty-issues.json").read_text())


@pytest.fixture
def sample_issues() -> dict:
    return json.loads((FIXTURES_DIR / "sample-issues.json").read_text())
```

- [ ] **Step 5: Write the failing tests**

Write `shield/adapters/sast/sonarqube/tests/test_adapter.py`:

```python
"""Tests for the SonarQube adapter."""

import os

from shield.adapters.sast.sonarqube.adapter import (
    SEVERITY_MAP,
    _load_credentials,
    _parse_sonar_issues,
    _strip_project_prefix,
)


def test_severity_mapping_complete():
    assert SEVERITY_MAP["BLOCKER"] == "high"
    assert SEVERITY_MAP["CRITICAL"] == "high"
    assert SEVERITY_MAP["MAJOR"] == "medium"
    assert SEVERITY_MAP["MINOR"] == "low"
    assert SEVERITY_MAP["INFO"] == "low"


def test_strip_project_prefix():
    assert _strip_project_prefix("my-project:src/Foo.java") == "src/Foo.java"
    # no prefix → return as-is
    assert _strip_project_prefix("src/Foo.java") == "src/Foo.java"


def test_parse_empty_issues(empty_issues):
    findings = _parse_sonar_issues(empty_issues)
    assert findings == []


def test_parse_sample_issues_count(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    assert len(findings) == 4


def test_parse_first_finding(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    f = findings[0]
    assert f.source == "sonarqube"
    assert f.rule_id == "java:S5547"
    assert f.file == "shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java"
    assert f.lines == "17-21"
    assert f.severity == "high"
    assert f.category == "security"


def test_parse_severity_mapping(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    severities = [f.severity for f in findings]
    assert severities == ["high", "high", "medium", "low"]  # BLOCKER, CRITICAL, MAJOR, MINOR


def test_parse_category_from_type(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    categories = [f.category for f in findings]
    # VULNERABILITY/VULNERABILITY/CODE_SMELL/CODE_SMELL
    assert categories == ["security", "security", "code-quality", "code-quality"]


def test_load_credentials_from_env(monkeypatch, tmp_path):
    # Ensure no credentials.json in HOME
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHIELD_SONAR_URL", "https://sonar.test")
    monkeypatch.setenv("SHIELD_SONAR_TOKEN", "tok123")
    monkeypatch.setenv("SHIELD_SONAR_PROJECT_KEY", "myproj")

    creds = _load_credentials()
    assert creds["url"] == "https://sonar.test"
    assert creds["token"] == "tok123"
    assert creds["project_key"] == "myproj"


def test_load_credentials_from_file(monkeypatch, tmp_path):
    """Credentials file takes precedence over env vars."""
    home = tmp_path
    monkeypatch.setenv("HOME", str(home))
    shield_dir = home / ".shield"
    shield_dir.mkdir()
    (shield_dir / "credentials.json").write_text(
        '{"sonarqube": {"url": "https://from-file", "token": "filetok", "project_key": "filekey"}}'
    )
    # env vars present too — file should win
    monkeypatch.setenv("SHIELD_SONAR_URL", "https://from-env")

    creds = _load_credentials()
    assert creds["url"] == "https://from-file"
    assert creds["token"] == "filetok"
    assert creds["project_key"] == "filekey"


def test_load_credentials_missing(monkeypatch, tmp_path):
    """No file, no env vars → all None."""
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in ("SHIELD_SONAR_URL", "SHIELD_SONAR_TOKEN", "SHIELD_SONAR_PROJECT_KEY"):
        monkeypatch.delenv(var, raising=False)

    creds = _load_credentials()
    assert creds["url"] is None
    assert creds["token"] is None
    assert creds["project_key"] is None
```

- [ ] **Step 6: Run the failing tests**

```bash
cd shield/adapters/sast
uv run pytest sonarqube/tests/test_adapter.py -v
```

Expected: ImportError. RED phase.

- [ ] **Step 7: Implement the adapter**

Write `shield/adapters/sast/sonarqube/adapter.py`:

```python
"""SonarQube Community SAST adapter for shield's backend-reviewer.

Default mode: consume existing output. SonarQube full scans take minutes,
so the adapter prefers reading pre-existing reports over invoking locally.

Layered fallback:
  1. Read SARIF / REST output at known/configured paths
  2. Fetch issues via REST API using credentials
  3. (Last resort) Invoke `sonar-scanner` locally
  4. Best-effort skip
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from shield.adapters.sast.common import (
    AdapterResult,
    Category,
    Finding,
    Severity,
)


SEVERITY_MAP: dict[str, Severity] = {
    "BLOCKER": "high",
    "CRITICAL": "high",
    "MAJOR": "medium",
    "MINOR": "low",
    "INFO": "low",
}


TYPE_TO_CATEGORY: dict[str, Category] = {
    "VULNERABILITY": "security",
    "SECURITY_HOTSPOT": "security",
    "BUG": "reliability",
    "CODE_SMELL": "code-quality",
}


def _load_credentials() -> dict[str, str | None]:
    """Resolve SonarQube credentials.

    Order:
      1. ~/.shield/credentials.json → "sonarqube" block
      2. Env vars: SHIELD_SONAR_URL, SHIELD_SONAR_TOKEN, SHIELD_SONAR_PROJECT_KEY
    """
    home = Path(os.environ.get("HOME", str(Path.home())))
    creds_path = home / ".shield" / "credentials.json"

    file_creds: dict[str, Any] = {}
    if creds_path.exists():
        try:
            data = json.loads(creds_path.read_text())
            file_creds = data.get("sonarqube", {}) or {}
        except (json.JSONDecodeError, OSError):
            file_creds = {}

    return {
        "url": file_creds.get("url") or os.environ.get("SHIELD_SONAR_URL"),
        "token": file_creds.get("token") or os.environ.get("SHIELD_SONAR_TOKEN"),
        "project_key": file_creds.get("project_key") or os.environ.get("SHIELD_SONAR_PROJECT_KEY"),
    }


def _strip_project_prefix(component: str) -> str:
    """SonarQube prefixes file paths with `project_key:` — strip it."""
    if ":" in component:
        return component.split(":", 1)[1]
    return component


def _parse_sonar_issues(payload: dict[str, Any]) -> list[Finding]:
    """Convert SonarQube /api/issues/search response to normalized findings."""
    findings: list[Finding] = []
    for issue in payload.get("issues", []):
        rule = issue.get("rule", "")
        component = issue.get("component", "")
        path = _strip_project_prefix(component)

        text_range = issue.get("textRange") or {}
        line = issue.get("line", 0)
        start_line = text_range.get("startLine", line)
        end_line = text_range.get("endLine", start_line)
        lines = f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}"

        severity_native = issue.get("severity", "MAJOR")
        severity: Severity = SEVERITY_MAP.get(severity_native, "medium")

        finding_type = issue.get("type", "CODE_SMELL")
        category: Category = TYPE_TO_CATEGORY.get(finding_type, "code-quality")

        findings.append(
            Finding(
                source="sonarqube",
                rule_id=rule,
                file=path,
                lines=lines,
                severity=severity,
                category=category,
                message=issue.get("message", ""),
            )
        )
    return findings


def _consume_existing(output_path: Path, head_commit_time: float) -> list[Finding] | None:
    """Read pre-existing SonarQube output if fresh."""
    if not output_path.exists():
        return None
    if output_path.stat().st_mtime < head_commit_time:
        return None
    try:
        payload = json.loads(output_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return _parse_sonar_issues(payload)


def _fetch_via_api(url: str, token: str, project_key: str) -> tuple[list[Finding], str | None]:
    """Fetch issues via SonarQube REST API."""
    api_url = url.rstrip("/") + "/api/issues/search"
    params = urllib.parse.urlencode({
        "componentKeys": project_key,
        "ps": 500,
        "statuses": "OPEN,REOPENED,CONFIRMED",
    })
    full_url = f"{api_url}?{params}"

    req = urllib.request.Request(full_url)
    encoded = base64.b64encode((token + ":").encode()).decode()
    req.add_header("Authorization", f"Basic {encoded}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        return [], f"sonarqube adapter — API fetch failed: {e}"

    return _parse_sonar_issues(payload), None


def _invoke_scanner(target_path: str, creds: dict[str, str | None]) -> tuple[list[Finding], str | None]:
    """Run `sonar-scanner` locally as last resort. Slow."""
    if shutil.which("sonar-scanner") is None:
        return [], "sonarqube adapter — sonar-scanner not on PATH"
    if not (creds["url"] and creds["token"] and creds["project_key"]):
        return [], "sonarqube adapter — credentials missing for local invocation"

    cmd = [
        "sonar-scanner",
        f"-Dsonar.host.url={creds['url']}",
        f"-Dsonar.login={creds['token']}",
        f"-Dsonar.projectKey={creds['project_key']}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=target_path)
    except subprocess.TimeoutExpired:
        return [], "sonarqube adapter — sonar-scanner timed out after 600s"
    except OSError as e:
        return [], f"sonarqube adapter — sonar-scanner error: {e}"

    if result.returncode != 0:
        return [], f"sonarqube adapter — sonar-scanner exit {result.returncode}: {result.stderr[:200]}"

    # After scan, fetch via API
    return _fetch_via_api(creds["url"], creds["token"], creds["project_key"])


def run(
    target_path: str,
    config: dict[str, Any] | None = None,
    head_commit_time: float | None = None,
) -> AdapterResult:
    """Entry point for the SonarQube adapter."""
    config = config or {}
    start = time.time()

    # Mode 1: consume existing output file
    output_path_str = config.get("consume_path")
    if output_path_str and head_commit_time is not None:
        output_path = Path(output_path_str)
        consumed = _consume_existing(output_path, head_commit_time)
        if consumed is not None:
            return AdapterResult(
                source="sonarqube",
                mode="consumed",
                runtime_seconds=time.time() - start,
                findings=consumed,
            )

    # Mode 2: fetch via REST API
    creds = _load_credentials()
    if creds["url"] and creds["token"] and creds["project_key"]:
        findings, err = _fetch_via_api(creds["url"], creds["token"], creds["project_key"])
        if err is None:
            return AdapterResult(
                source="sonarqube",
                mode="consumed",
                runtime_seconds=time.time() - start,
                findings=findings,
            )
        # API failed — try local scan as last resort
        findings, scan_err = _invoke_scanner(target_path, creds)
        if scan_err is None:
            return AdapterResult(
                source="sonarqube",
                mode="invoked",
                runtime_seconds=time.time() - start,
                findings=findings,
            )
        # Both failed
        return AdapterResult(
            source="sonarqube",
            mode="unavailable",
            runtime_seconds=time.time() - start,
            findings=[],
            note=f"{err}; {scan_err}",
        )

    # Mode 3: best-effort skip — credentials missing
    return AdapterResult(
        source="sonarqube",
        mode="unavailable",
        runtime_seconds=time.time() - start,
        findings=[],
        note=(
            "sonarqube adapter — credentials missing; SAST coverage best-effort. "
            "Configure ~/.shield/credentials.json (sonarqube block) or "
            "SHIELD_SONAR_{URL,TOKEN,PROJECT_KEY} env vars to enable."
        ),
    )
```

- [ ] **Step 8: Run the tests — they should pass**

```bash
cd shield/adapters/sast
uv run pytest sonarqube/tests/test_adapter.py -v
```

Expected: 10 passed.

- [ ] **Step 9: Commit**

```bash
git add shield/adapters/sast/sonarqube/__init__.py \
        shield/adapters/sast/sonarqube/adapter.py \
        shield/adapters/sast/sonarqube/tests/
git commit -m "feat(shield): add SonarQube SAST adapter — REST API consume + local scanner fallback"
```

---

### Task 6: SonarQube adapter — adapter.md + sample config

**Files:**
- Create: `shield/adapters/sast/sonarqube/adapter.md`
- Create: `shield/adapters/sast/sonarqube/examples/sonar-project.properties`

- [ ] **Step 1: Write the sample sonar-project.properties**

Write `shield/adapters/sast/sonarqube/examples/sonar-project.properties`:

```properties
# Recommended baseline for shield's SonarQube adapter.
# Place this at the root of your Spring Boot project alongside pom.xml/build.gradle.

sonar.projectKey=YOUR_PROJECT_KEY
sonar.projectName=YOUR_PROJECT_NAME
sonar.projectVersion=1.0

# Sources and tests
sonar.sources=src/main/java
sonar.tests=src/test/java
sonar.java.binaries=target/classes
sonar.java.test.binaries=target/test-classes

# Encoding
sonar.sourceEncoding=UTF-8

# Java version (matches Spring Boot 3 baseline)
sonar.java.source=17
sonar.java.target=17

# Coverage — adjust to your tooling
# sonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml

# Exclusions (typical defaults — adjust for your project)
sonar.exclusions=**/generated/**,**/build/**,**/target/**

# Recommended quality gate: "Sonar way" (default) augmented with "Spring" rules.
# Enable Spring rules in your SonarQube admin → Quality Profiles → Java.
```

- [ ] **Step 2: Write the adapter contract**

Write `shield/adapters/sast/sonarqube/adapter.md`:

```markdown
# SonarQube Community SAST Adapter

LLM-readable contract for the SonarQube adapter. The Python runtime that executes this contract lives at `adapter.py`.

## What this adapter does

Consumes findings from a SonarQube Community Edition server. By default the adapter does NOT invoke `sonar-scanner` locally (full scans take minutes); it expects the user to run scans in CI and reads the results via REST API.

## Configuration

In `.shield.json`:

```json
{
  "sast": {
    "adapters": ["sonarqube"],
    "sonarqube": {
      "consume_path": "target/sonarqube-issues.json"
    }
  }
}
```

| Key | Required | Default | Description |
|---|---|---|---|
| `consume_path` | no | (none) | Path to a pre-fetched SonarQube REST API response. Mtime-checked against HEAD commit. |

In `~/.shield/credentials.json`:

```json
{
  "sonarqube": {
    "url": "https://sonar.example.com",
    "token": "...",
    "project_key": "my-project"
  }
}
```

Env var fallback (used if any credential is missing in the file): `SHIELD_SONAR_URL`, `SHIELD_SONAR_TOKEN`, `SHIELD_SONAR_PROJECT_KEY`.

## Layered fallback

1. **Consume `consume_path` file** if its mtime is newer than HEAD commit time.
2. **Fetch via REST API** at `{url}/api/issues/search?componentKeys={project_key}&statuses=OPEN,REOPENED,CONFIRMED` using credentials.
3. **Invoke `sonar-scanner`** locally if credentials are configured AND `sonar-scanner` is on PATH (slow, last resort). After scan, fetch via API.
4. **Best-effort skip** if no path forward (no consumable file, no working API, no scanner).

## Severity mapping

| SonarQube | shield |
|---|---|
| BLOCKER | high |
| CRITICAL | high |
| MAJOR | medium |
| MINOR | low |
| INFO | low |

## Category derivation

SonarQube issue `type` field:
- `VULNERABILITY`, `SECURITY_HOTSPOT` → `security`
- `BUG` → `reliability`
- `CODE_SMELL` → `code-quality`
- Any other → `code-quality` (default)

## Stale output handling

`consume_path` mtime older than HEAD commit time → treat as missing, fall through to API fetch. The user's CI scan was older than their latest commit; trust live API over stale report.

## Branch analysis

SonarQube Community Edition does NOT support branch analysis (Developer Edition feature). All findings cover the whole project regardless of which branch the user is reviewing. The aggregator surfaces SAST findings in a "Repo-wide SAST findings" section to make this clear.

## Authentication notes

SonarQube uses HTTP Basic auth with the token as the username (and an empty password): `Authorization: Basic base64(token + ":")`. The adapter handles this; users only provide the raw token.

## Behavior on unreachable server

If the API is unreachable (network error, server down, 401), the adapter logs the error in its `note` field and returns zero findings. Doesn't fail the review.

## Sample sonar-project.properties

`examples/sonar-project.properties` is a reasonable baseline for a Spring Boot 3 project. Copy to your project root and adjust the `sonar.projectKey` etc.

## Testing

Parser tests at `tests/test_adapter.py` use captured fixtures (`tests/fixtures/*.json`). To regenerate fixtures, hit the API with curl:

```bash
curl -u "$SHIELD_SONAR_TOKEN:" \
  "$SHIELD_SONAR_URL/api/issues/search?componentKeys=$SHIELD_SONAR_PROJECT_KEY&ps=10" > \
  shield/adapters/sast/sonarqube/tests/fixtures/sample-issues.json
```

## Related

- See `../README.md` for the framework overview
- See `../finding-schema.md` for the normalized finding shape
- See `examples/sonar-project.properties` for a recommended scanner config
```

- [ ] **Step 3: Commit**

```bash
git add shield/adapters/sast/sonarqube/adapter.md \
        shield/adapters/sast/sonarqube/examples/
git commit -m "docs(shield): add SonarQube adapter contract + sample sonar-project.properties"
```

---

### Task 7: backend-reviewer integration

**Files:**
- Modify: `shield/agents/backend-reviewer.md`

- [ ] **Step 1: Read the current agent file**

Read `shield/agents/backend-reviewer.md`. Note the existing structure: Persona, Trigger Keywords, Weight, Modes, Stack Detection, Skill Loading, Specialist Dispatch, Review Process, Output Format, Edge Cases, Common Mistakes.

- [ ] **Step 2: Add a new "## SAST Adapters" section after "## Skill Loading"**

Find the section that ends with `**Other stacks (Python, Node/TS, Go):** No framework skills in v1 — Plan 2 covers Java/Kotlin only. Python ships in v2, Node/TS in v3, Go in v4.`

After it (and before the next `---` separator), INSERT this:

```markdown

---

## SAST Adapters

If `.shield.json` includes a `sast.adapters` list, run those adapters in parallel with the skill review. The adapters live under `shield/adapters/sast/<name>/` and produce normalized findings.

### Configuration lookup

```json
// .shield.json (committed)
{
  "project": "...",
  "sast": {
    "adapters": ["semgrep", "sonarqube"],
    "semgrep": { ... per-adapter config ... },
    "sonarqube": { ... per-adapter config ... }
  }
}
```

Empty list or missing `sast` key → SAST inactive. Skip the dispatch entirely.

Credentials for adapters that need them live in `~/.shield/credentials.json` under each adapter's name (e.g., `"sonarqube": { "url": "...", "token": "...", "project_key": "..." }`). The adapters resolve credentials themselves; the agent only passes per-project config.

### Dispatch

For each adapter listed:

1. Import its `adapter.run(target_path, config, head_commit_time)` function from `shield.adapters.sast.<name>.adapter`
2. Pass the target_path being reviewed, the adapter's config block from `.shield.json`, and the HEAD commit's timestamp (used for stale-output detection)
3. Each adapter returns an `AdapterResult` with `mode` (consumed/invoked/unavailable), `findings`, and an optional `note`

Run adapters concurrently with the skill review (Python `concurrent.futures.ThreadPoolExecutor` or equivalent). They are independent — no shared state.

### Aggregation

After all sources (skills, SAST adapters, specialists) return, aggregate findings:

1. Group all findings by `(file, lines)` — two findings are duplicates if their files match exactly AND their line ranges overlap within ±2 lines
2. For each duplicate group, collapse to a single entry citing all `source` values (e.g., `source: "skill+semgrep"`)
3. Findings whose location does not overlap any skill finding go into a separate "Repo-wide SAST findings" section
4. SAST findings whose location DOES overlap a skill finding merge into the module section where that skill finding lives

---
```

- [ ] **Step 3: Update the "## Output Format" section**

Find the existing Output Format section. Locate the line that says:

```
**Skills applied:** {agnostic: 7; framework: 0 (Plan 2 ships Java)}
```

REPLACE it with:

```
**Skills applied:** 13 (7 agnostic + 6 framework)
**SAST adapters:** {summary line — see below}
```

Then find the line near the bottom of the Output Format example that shows the Module section ending, and BEFORE the `### Specialist Findings` section, INSERT:

```markdown

### Repo-wide SAST findings (no skill mapping)

| Severity | Source | Rule | File | Lines | Finding |
|---|---|---|---|---|---|
| Medium | sonarqube | java:S1144 | service/LegacyUtil.java | 42 | Unused private method |
...

```

The full Output Format section (after both edits) should now look like:

```
## Output Format

```
## Backend Review

**Scope:** {N files in M modules}
**Stacks detected:** Java/Kotlin · Spring Boot 3.2.0 · Java 17
**Skills applied:** 13 (7 agnostic + 6 framework)
**SAST adapters:** semgrep (invoked, 12 findings) · sonarqube (consumed, mtime stale → re-fetched, 47 findings)
**Specialists consulted:** {security, architecture, agile-coach, operations, dx-engineer, product-manager}

### Module: services/api/ (Java/Kotlin)

| Severity | Source | Skill / Rule | File | Lines | Finding |
|---|---|---|---|---|---|
| High | skill+semgrep | spring-security:SS1 + java.spring.security.noop-encoder | config/SecurityConfig.java | 17-20 | NoOpPasswordEncoder stores plaintext |
| High | skill | code-quality-review:Q1 | service/UserService.java | 9-13 | God class — handles unrelated domains |
...

### Module: services/worker/ (Java/Kotlin)
...

### Repo-wide SAST findings (no skill mapping)

| Severity | Source | Rule | File | Lines | Finding |
|---|---|---|---|---|---|
| Medium | sonarqube | java:S1144 | service/LegacyUtil.java | 42 | Unused private method |
...

### Specialist Findings

#### security-reviewer
...

### Summary

- Total findings: {N} (skill: {n}, SAST-skill-overlap: {n}, SAST-only: {n})
- High: {n}; Medium: {n}; Low: {n}
- Modules with no findings: {list}
```

```

- [ ] **Step 4: Update the "## Edge Cases" table**

Find the Edge Cases table. ADD these rows at the bottom:

```markdown
| `sast.adapters` references unknown adapter name | Skip with warning; continue with known adapters |
| All SAST adapters return mode=unavailable | Review proceeds skill-only; report header lists which adapters were unavailable and why |
| SAST finding location matches a skill finding | Collapse to one entry; cite all sources in the `source` column |
| SAST finding location does not match any skill finding | Place in "Repo-wide SAST findings" section |
```

- [ ] **Step 5: Update the "## Common Mistakes" table**

Find the Common Mistakes table. ADD these rows at the bottom:

```markdown
| Loading SAST adapters when none configured | If `sast.adapters` list is empty/missing, do NOT invoke any adapter. SAST is opt-in |
| Treating SAST findings as authoritative over skills | They're complementary. Dedup by location is fine, but don't suppress a skill finding because SAST didn't catch it (skills check things SAST can't) |
| Running SonarQube full scan on every review | SonarQube's default mode is consume. Don't invoke `sonar-scanner` unless explicitly fallback path |
```

- [ ] **Step 6: Verify with git diff**

```bash
git diff shield/agents/backend-reviewer.md
```

Expected: a new "## SAST Adapters" section, an extended Output Format, and 4+3 new rows across Edge Cases and Common Mistakes.

- [ ] **Step 7: Commit**

```bash
git add shield/agents/backend-reviewer.md
git commit -m "feat(shield): integrate SAST adapters into backend-reviewer (parallel dispatch + output format)"
```

---

### Task 8: Onboarding doc

**Files:**
- Create: `shield/adapters/sast/GETTING-STARTED.md`

- [ ] **Step 1: Write the onboarding doc**

Write `shield/adapters/sast/GETTING-STARTED.md`:

```markdown
# Getting Started with Shield SAST Adapters

This guide walks you from "shield works skill-only" to "shield runs SAST tools alongside skills."

## TL;DR

```bash
# 1. Install Semgrep (lightest tool to start)
pip install semgrep

# 2. Edit your repo's .shield.json to opt in
echo '{
  "project": "my-project",
  "sast": { "adapters": ["semgrep"] }
}' > .shield.json

# 3. Run shield review
/review-backend
```

That's it. SAST runs automatically on the next `/review-backend` invocation.

## Adding SonarQube

SonarQube Community is heavier — it requires a self-hosted server. If your team already runs SonarQube in CI, configure shield to consume the existing scans:

### One-time setup

1. Get a token: in SonarQube, Account → Security → Generate Token
2. Configure credentials at `~/.shield/credentials.json`:
   ```json
   {
     "clickup":   { "api_token": "..." },
     "sonarqube": {
       "url": "https://sonar.your-company.com",
       "token": "<token from step 1>",
       "project_key": "<your project's sonar key>"
     }
   }
   ```
   (Permissions: `chmod 600 ~/.shield/credentials.json`)

3. Add `sonarqube` to your repo's `.shield.json`:
   ```json
   {
     "project": "my-project",
     "sast": {
       "adapters": ["semgrep", "sonarqube"]
     }
   }
   ```

### Verifying

```bash
# Quick sanity check the credentials work
curl -u "$SHIELD_SONAR_TOKEN:" \
     "$SHIELD_SONAR_URL/api/projects/search?projects=$SHIELD_SONAR_PROJECT_KEY"
```

Should return a JSON object with your project metadata. If 401, the token is wrong; if 404, the project_key is wrong; if connection refused, the URL is wrong.

## Configuration reference

`.shield.json` `sast` block:

```json
{
  "sast": {
    "adapters": ["semgrep", "sonarqube"],
    "semgrep": {
      "config": "p/spring-boot-best-practices",
      "output_path": "target/semgrep-output.json"
    },
    "sonarqube": {
      "consume_path": "target/sonarqube-issues.json"
    }
  }
}
```

All keys under each adapter are optional. Defaults:
- Semgrep `config`: shield's bundled rule pack at `shield/adapters/sast/semgrep/rules/`
- Semgrep `output_path`: none (always invoke locally)
- SonarQube `consume_path`: none (fetch via API)

## Suppression

Use the tool's native suppression:

- **Semgrep:** `// nosemgrep: <rule_id>` on the offending line
- **SonarQube:** `@SuppressWarnings("java:S1234")` on the method/class, or mark the issue "Won't Fix" in the SonarQube UI

shield does not provide its own suppression mechanism in v1. If SAST output becomes too noisy, consider:
1. Disabling specific rules at the tool level (Semgrep: edit your rule pack; SonarQube: adjust your Quality Profile)
2. Removing the adapter from `sast.adapters` if the noise outweighs the value

## What if a tool isn't installed?

The adapter emits a one-line "best-effort" note in the report header and continues. The review still completes; you just don't get that adapter's findings.

Example output header when only Semgrep is installed:

```
**SAST adapters:** semgrep (invoked, 8 findings) · sonarqube (unavailable: credentials missing)
```

## Reading the output

Findings appear in two places:

1. **Inside module sections** — when SAST and skills both flag the same file:line area, the entry shows `source: "skill+semgrep"` (or whichever combination). Both sources caught it; treat as a confirmed issue.
2. **"Repo-wide SAST findings" section** — SAST-only findings (no skill overlap). These cover the whole repo, not just changed files, since SonarQube Community doesn't do branch analysis.

The summary at the bottom shows a breakdown:
```
- Total findings: 73 (skill: 38, SAST-skill-overlap: 8, SAST-only: 27)
```
"SAST-only" tells you how much value SAST added beyond what skills caught.

## Adding a new adapter

See `shield/adapters/sast/README.md`. Implement the `adapter.run(target_path, config, head_commit_time)` contract defined in `finding-schema.md`, write parser tests against captured fixtures, and add the adapter name to your `.shield.json`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `semgrep adapter — tool not available` | Semgrep not in PATH | `pip install semgrep` |
| `sonarqube adapter — credentials missing` | No `~/.shield/credentials.json` and no env vars | Set up credentials per "One-time setup" above |
| `sonarqube adapter — API fetch failed: 401` | Wrong token | Regenerate the token in SonarQube and update credentials.json |
| `sonarqube adapter — API fetch failed: 404` | Wrong project_key | Find the project's actual key in the SonarQube UI under Project Settings |
| `mtime stale → re-fetched` in header | Existing output is older than HEAD commit | This is expected behavior; adapter automatically refetched |
| SAST finds 200+ noisy CODE_SMELL findings | Quality profile too broad | Tune your SonarQube Quality Profile to focus on Bugs + Vulnerabilities |
| Same finding appears twice in report | Dedup edge case | Check that the file paths match exactly; SonarQube prefixes paths with `project_key:` and our adapter strips this — file a bug if dedup misses |
```

- [ ] **Step 2: Commit**

```bash
git add shield/adapters/sast/GETTING-STARTED.md
git commit -m "docs(shield): add SAST adapter onboarding guide"
```

---

### Task 9: End-to-end validation

**Files:**
- (No file changes — validation step)

- [ ] **Step 1: Run all SAST adapter unit tests**

```bash
cd shield/adapters/sast
uv run pytest -v
```

Expected: all parser/dispatch tests pass for both adapters (Semgrep ~8 tests, SonarQube ~10 tests, common ~4 tests).

- [ ] **Step 2: Validate the rule packs**

```bash
uv run python -c "
import yaml
from pathlib import Path

rules_dir = Path('shield/adapters/sast/semgrep/rules')
total = 0
for path in sorted(rules_dir.glob('*.yml')):
    data = yaml.safe_load(path.read_text())
    rules = data.get('rules', [])
    print(f'{path.name}: {len(rules)} rules')
    total += len(rules)
    for r in rules:
        assert 'id' in r
        assert 'metadata' in r
        assert 'shield-area' in r['metadata']
        assert 'message' in r
        assert 'severity' in r
        assert 'languages' in r
        # Must have at least one of: pattern, pattern-either, pattern-regex
        assert any(k.startswith('pattern') for k in r.keys()), f'rule {r[\"id\"]} has no pattern'
print(f'Total: {total} rules')
"
```

Expected: each file lists its rule count. Total should be 9 rules (3 + 2 + 2 + 2 across the four files). No assertions fail.

- [ ] **Step 3: Dispatch a subagent to validate the agent contract**

Use the `Agent` tool with `subagent_type: general-purpose` and `model: opus`:

```
You are validating shield's SAST adapter integration end-to-end.

Working directory: /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/

Read the following files in full:

1. shield/agents/backend-reviewer.md (focus on the new "## SAST Adapters" section, updated Output Format, and edge cases)
2. shield/adapters/sast/README.md
3. shield/adapters/sast/finding-schema.md
4. shield/adapters/sast/severity-mapping.md
5. shield/adapters/sast/semgrep/adapter.md
6. shield/adapters/sast/sonarqube/adapter.md
7. shield/adapters/sast/GETTING-STARTED.md

Then verify the following claims by reading the corresponding code:

A. The Semgrep adapter (`shield/adapters/sast/semgrep/adapter.py`) implements the layered fallback as documented:
   1. Mode 1 (consume): reads output_path if mtime > head_commit_time
   2. Mode 2 (invoke): runs `semgrep --config <rules> --json --quiet <target>` if semgrep is on PATH
   3. Mode 3 (unavailable): returns AdapterResult with mode="unavailable" and a clear note

B. The SonarQube adapter (`shield/adapters/sast/sonarqube/adapter.py`) implements:
   1. Credential resolution from ~/.shield/credentials.json then env vars (file wins)
   2. Component prefix stripping (project_key:src/Foo.java → src/Foo.java)
   3. Severity mapping (BLOCKER/CRITICAL → high, MAJOR → medium, MINOR/INFO → low)
   4. Type-to-category mapping (VULNERABILITY → security, CODE_SMELL → code-quality, etc.)

C. The Finding/AdapterResult dataclasses in shield/adapters/sast/common.py match the schema in finding-schema.md.

D. The agent doc is consistent — the dispatch logic in "## SAST Adapters" matches the output format example.

Report:
- Section-by-section: PASS or list specific contradictions/gaps
- Any issues that would cause the integration to misbehave at runtime
- Verdict: PASS / PARTIAL / FAIL

Do NOT actually run the adapters or skills — this is a static contract validation.
```

- [ ] **Step 4: Address any issues from Step 3**

If the validation reports gaps:
- Code/contract mismatch → fix the code (since the contract is the spec)
- Documentation missing detail → update the relevant `.md`
- Re-run Step 3 until verdict is PASS

If verdict is PASS, no commit needed. Skip to Task 10.

If commits are needed:

```bash
git add <changed files>
git commit -m "fix(shield): refine SAST adapter integration based on contract validation"
```

---

### Task 10: Bump shield version

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current shield version**

Read `.claude-plugin/marketplace.json`. Confirm shield's `version` is at the expected baseline (likely `2.11.0` after Plan 2; if Plan 3 has merged first, it may be higher).

- [ ] **Step 2: Bump to next minor**

If current is `2.11.0` → change to `2.12.0`. If higher (Plan 3 already merged), change to `<current_minor + 1>.0`.

- [ ] **Step 3: Verify**

```bash
git diff .claude-plugin/marketplace.json
```

Expected: single-line change in shield's version.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to <new-version> — SAST adapter integration (Plan 4)"
```

---

## Self-review checklist (run at end of plan execution)

- [ ] All 10 tasks committed
- [ ] `shield/adapters/sast/` exists with `common.py`, `README.md`, `finding-schema.md`, `severity-mapping.md`, `GETTING-STARTED.md`
- [ ] Both adapters (`semgrep/`, `sonarqube/`) have `adapter.md`, `adapter.py`, `tests/test_adapter.py`, `tests/fixtures/`
- [ ] Semgrep adapter has 4 rule pack YAML files at `semgrep/rules/`
- [ ] SonarQube adapter has `examples/sonar-project.properties`
- [ ] `shield/agents/backend-reviewer.md` includes the new "## SAST Adapters" section
- [ ] All Python tests pass (`uv run pytest shield/adapters/sast/ -v`)
- [ ] Rule pack YAMLs are valid and have required metadata
- [ ] End-to-end agent contract validation (Task 9 Step 3) reports PASS
- [ ] `.claude-plugin/marketplace.json` shows the bumped shield version
- [ ] No SKILL.md or adapter.md contains a TBD/TODO

## After Plan 4 ships

Plan 5+ candidates:
- SpotBugs + FindSecBugs + spotbugs-spring adapter (bytecode-level depth; transactional self-invocation)
- gitleaks adapter (secrets scanning, narrow/high-ROI)
- CodeQL adapter (semantic queries; heavier setup)
- `.shield.json` `sast.suppress` config (if user feedback shows tool-native suppression is insufficient)
- SB2 rule packs (`spring-*-sb2.yml`) following Pattern A from `EXTENDING-VERSIONS.md`
- Kotlin-specific Semgrep rules (paired with Plan 2's deferred Kotlin fixture)
- Integration test infrastructure: install Semgrep + run SonarQube in Docker, gated `pytest -m integration`
