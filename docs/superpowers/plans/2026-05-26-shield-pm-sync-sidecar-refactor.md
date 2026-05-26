# Shield `/pm-sync` Sidecar Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `/pm-sync`'s broken HTML/markdown parser path with a sidecar-driven flow that reads `plan.json` directly, extracted into a reusable `shield/parsers/` package. ClickUp adapter's existing 8 tests stay green throughout the refactor; the new behavior is covered by added tests at every phase.

**Architecture:** New top-level uv package `shield/parsers/` owning the canonical `plan.json` reader/writer with typed dataclasses (`Plan`, `Milestone`, `Epic`, `Story`, `DesignRef`). ClickUp adapter rewrites `sync.py` to consume it via a new MCP tool `pm_sync_sidecar`, deletes the old `server/parsers/` directory + `PlanDocsConfig.format`/`epics[]` config surface, and bumps `plan.json` schema 1.3 → 1.4 (adds `pm_id` + `pm_url` to Epic).

**Tech Stack:** Python 3.11+, uv (no system pip), pytest + pytest-cov, jsonschema (for Draft 2020-12 validation), respx (for HTTP mocking), httpx, mcp[cli], hatchling build backend.

**Spec:** [`docs/superpowers/specs/2026-05-26-shield-pm-sync-sidecar-refactor-design.md`](../specs/2026-05-26-shield-pm-sync-sidecar-refactor-design.md)

---

## Phase A — Build `shield/parsers/` in isolation

### Task 1: Scaffold the `shield/parsers/` package

**Files:**
- Create: `shield/parsers/pyproject.toml`
- Create: `shield/parsers/shield_parsers/__init__.py`
- Create: `shield/parsers/shield_parsers/sidecar.py`
- Create: `shield/parsers/tests/__init__.py`
- Create: `shield/parsers/tests/conftest.py`
- Create: `shield/parsers/tests/test_sidecar.py`

- [ ] **Step 1.1: Create the `pyproject.toml`**

```toml
[project]
name = "shield-parsers"
version = "0.1.0"
description = "Canonical typed reader/writer for Shield artifact files (plan.json sidecar, future TRD section parser, etc.)"
requires-python = ">=3.11"
dependencies = [
    "jsonschema>=4.0",
]

[project.optional-dependencies]
test = ["pytest>=9.0.3", "pytest-cov>=5"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["shield_parsers"]
```

- [ ] **Step 1.2: Create empty `shield_parsers/__init__.py`**

```python
"""Shield artifact parsers — typed reader/writer for plan.json and friends."""
```

- [ ] **Step 1.3: Create empty `shield_parsers/sidecar.py` placeholder**

```python
"""plan.json sidecar reader/writer."""
```

- [ ] **Step 1.4: Create `tests/__init__.py` (empty file)** and `tests/conftest.py`

`tests/__init__.py` — empty
`tests/conftest.py`:

```python
"""Pytest fixtures for shield_parsers tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def schema_path() -> Path:
    """Path to the canonical plan-sidecar JSON Schema in the repo."""
    # tests/ → parsers/ → shield/ → repo-root → shield/schema/plan-sidecar.schema.json
    return Path(__file__).resolve().parents[3] / "schema" / "plan-sidecar.schema.json"
```

- [ ] **Step 1.5: Verify the package installs**

Run: `uv sync --directory shield/parsers --extra test`
Expected: success, creates `shield/parsers/.venv/`.

- [ ] **Step 1.6: Commit**

```bash
git add shield/parsers/
git commit -m "feat(shield/parsers): scaffold shield-parsers uv package"
```

---

### Task 2: Add typed dataclasses for plan.json objects

**Files:**
- Modify: `shield/parsers/shield_parsers/sidecar.py`
- Modify: `shield/parsers/shield_parsers/__init__.py`
- Modify: `shield/parsers/tests/test_sidecar.py`

- [ ] **Step 2.1: Write failing test for dataclass instantiation**

In `tests/test_sidecar.py`:

```python
"""Tests for shield_parsers.sidecar."""

from __future__ import annotations

from shield_parsers.sidecar import (
    CURRENT_SCHEMA_VERSION,
    MIN_SUPPORTED_VERSION,
    DesignRef,
    Epic,
    Milestone,
    Plan,
    Story,
)


def test_constants_exposed() -> None:
    assert CURRENT_SCHEMA_VERSION == "1.4"
    assert MIN_SUPPORTED_VERSION == "1.0"


def test_dataclasses_instantiate_with_minimal_args() -> None:
    story = Story(
        id="EPIC-1-S1",
        name="Do the thing",
        status="ready",
        description="Does the thing.",
        tasks=["step 1"],
        acceptance_criteria=["it works"],
    )
    epic = Epic(id="EPIC-1", name="Epic name", stories=[story])
    milestone = Milestone(
        id="M1", name="MS one", outcome="ships X", exit_criteria=["X exists"]
    )
    plan = Plan(
        version="1.4",
        project="shield",
        name="some-feature",
        milestones=[milestone],
        epics=[epic],
    )

    assert plan.version == "1.4"
    assert plan.epics[0].stories[0].pm_id is None
    assert plan.epics[0].pm_id is None
```

- [ ] **Step 2.2: Run the test — expect failure**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py -v`
Expected: FAIL with `ImportError` — dataclasses not defined yet.

- [ ] **Step 2.3: Implement the dataclasses in `sidecar.py`**

```python
"""plan.json sidecar reader/writer with typed dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CURRENT_SCHEMA_VERSION = "1.4"
MIN_SUPPORTED_VERSION = "1.0"


@dataclass
class DesignRef:
    doc: str  # "trd" | "lld" | "prd"
    label: str
    component: str | None = None
    section_id: str | None = None
    anchor_url: str | None = None
    stale: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Story:
    id: str
    name: str
    status: str
    description: str
    tasks: list[str]
    acceptance_criteria: list[str]
    assignee: str | None = None
    priority: str | None = None
    week: str | int | None = None
    milestone_id: str | None = None
    design_refs: list[DesignRef] = field(default_factory=list)
    pm_id: str | None = None
    pm_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Epic:
    id: str
    name: str
    stories: list[Story]
    pm_id: str | None = None
    pm_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Milestone:
    id: str
    name: str
    outcome: str
    exit_criteria: list[str]
    depends_on: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    version: str
    project: str
    name: str
    epics: list[Epic]
    milestones: list[Milestone] = field(default_factory=list)
    phase: str | None = None
    source_research: str | None = None
    source_prd: str | None = None
    prd_rubric_version_at_planning: str | None = None
    last_aligned_with: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 2.4: Re-export from `__init__.py`**

```python
"""Shield artifact parsers — typed reader/writer for plan.json and friends."""

from shield_parsers.sidecar import (
    CURRENT_SCHEMA_VERSION,
    MIN_SUPPORTED_VERSION,
    DesignRef,
    Epic,
    Milestone,
    Plan,
    Story,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "MIN_SUPPORTED_VERSION",
    "DesignRef",
    "Epic",
    "Milestone",
    "Plan",
    "Story",
]
```

- [ ] **Step 2.5: Re-run the test — expect pass**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py -v`
Expected: PASS (2 tests).

- [ ] **Step 2.6: Commit**

```bash
git add shield/parsers/shield_parsers/sidecar.py shield/parsers/shield_parsers/__init__.py shield/parsers/tests/test_sidecar.py
git commit -m "feat(shield/parsers): add Plan/Epic/Story/Milestone/DesignRef dataclasses"
```

---

### Task 3: Implement `load_plan()` — minimum valid v1.4

**Files:**
- Modify: `shield/parsers/shield_parsers/sidecar.py`
- Modify: `shield/parsers/tests/test_sidecar.py`
- Create: `shield/parsers/tests/fixtures/plan-v14-minimal.json`

- [ ] **Step 3.1: Create the v1.4 minimal fixture**

In `shield/parsers/tests/fixtures/plan-v14-minimal.json`:

```json
{
  "version": "1.4",
  "project": "shield",
  "name": "some-feature",
  "milestones": [
    {
      "id": "M1",
      "name": "MS one",
      "outcome": "ships X",
      "exit_criteria": ["X exists"]
    }
  ],
  "epics": [
    {
      "id": "EPIC-1",
      "name": "Epic name",
      "pm_id": null,
      "pm_url": null,
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "Do the thing",
          "status": "ready",
          "description": "Does the thing.",
          "tasks": ["step 1"],
          "acceptance_criteria": ["it works"],
          "milestone_id": "M1",
          "pm_id": null,
          "pm_url": null
        }
      ]
    }
  ]
}
```

- [ ] **Step 3.2: Write failing test for `load_plan`**

Append to `tests/test_sidecar.py`:

```python
from pathlib import Path

from shield_parsers.sidecar import load_plan


def test_load_plan_v14_minimal(tmp_path: Path) -> None:
    src = Path(__file__).parent / "fixtures" / "plan-v14-minimal.json"
    plan = load_plan(src)

    assert plan.version == "1.4"
    assert plan.project == "shield"
    assert plan.name == "some-feature"
    assert len(plan.milestones) == 1
    assert plan.milestones[0].id == "M1"
    assert len(plan.epics) == 1
    assert plan.epics[0].id == "EPIC-1"
    assert plan.epics[0].pm_id is None
    assert len(plan.epics[0].stories) == 1
    assert plan.epics[0].stories[0].id == "EPIC-1-S1"
    assert plan.epics[0].stories[0].milestone_id == "M1"
```

- [ ] **Step 3.3: Run the test — expect failure**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py::test_load_plan_v14_minimal -v`
Expected: FAIL with `ImportError: cannot import name 'load_plan'`.

- [ ] **Step 3.4: Implement `load_plan()`**

Append to `sidecar.py`:

```python
import json
from pathlib import Path


def _story_from_dict(d: dict[str, Any]) -> Story:
    known = {
        "id", "name", "status", "description", "tasks", "acceptance_criteria",
        "assignee", "priority", "week", "milestone_id", "design_refs",
        "pm_id", "pm_url",
    }
    refs = [_design_ref_from_dict(r) for r in d.get("design_refs", []) or []]
    extra = {k: v for k, v in d.items() if k not in known}
    return Story(
        id=d["id"],
        name=d["name"],
        status=d["status"],
        description=d["description"],
        tasks=list(d.get("tasks", [])),
        acceptance_criteria=list(d.get("acceptance_criteria", [])),
        assignee=d.get("assignee"),
        priority=d.get("priority"),
        week=d.get("week"),
        milestone_id=d.get("milestone_id"),
        design_refs=refs,
        pm_id=d.get("pm_id"),
        pm_url=d.get("pm_url"),
        extra=extra,
    )


def _design_ref_from_dict(d: dict[str, Any]) -> DesignRef:
    known = {"doc", "label", "component", "section_id", "anchor_url", "stale"}
    extra = {k: v for k, v in d.items() if k not in known}
    return DesignRef(
        doc=d["doc"],
        label=d["label"],
        component=d.get("component"),
        section_id=d.get("section_id"),
        anchor_url=d.get("anchor_url"),
        stale=d.get("stale", False),
        extra=extra,
    )


def _epic_from_dict(d: dict[str, Any]) -> Epic:
    known = {"id", "name", "stories", "pm_id", "pm_url"}
    extra = {k: v for k, v in d.items() if k not in known}
    return Epic(
        id=d["id"],
        name=d["name"],
        stories=[_story_from_dict(s) for s in d.get("stories", [])],
        pm_id=d.get("pm_id"),
        pm_url=d.get("pm_url"),
        extra=extra,
    )


def _milestone_from_dict(d: dict[str, Any]) -> Milestone:
    known = {"id", "name", "outcome", "exit_criteria", "depends_on"}
    extra = {k: v for k, v in d.items() if k not in known}
    return Milestone(
        id=d["id"],
        name=d["name"],
        outcome=d["outcome"],
        exit_criteria=list(d["exit_criteria"]),
        depends_on=list(d.get("depends_on", [])),
        extra=extra,
    )


def load_plan(path: Path | str) -> Plan:
    """Load a plan.json sidecar from disk into a typed `Plan` object."""
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    known_top = {
        "version", "project", "name", "phase", "source_research", "source_prd",
        "prd_rubric_version_at_planning", "last_aligned_with", "milestones",
        "epics", "metadata",
    }
    extra = {k: v for k, v in raw.items() if k not in known_top}
    return Plan(
        version=raw["version"],
        project=raw["project"],
        name=raw["name"],
        milestones=[_milestone_from_dict(m) for m in raw.get("milestones", [])],
        epics=[_epic_from_dict(e) for e in raw.get("epics", [])],
        phase=raw.get("phase"),
        source_research=raw.get("source_research"),
        source_prd=raw.get("source_prd"),
        prd_rubric_version_at_planning=raw.get("prd_rubric_version_at_planning"),
        last_aligned_with=raw.get("last_aligned_with"),
        metadata=dict(raw.get("metadata", {})),
        extra=extra,
    )
```

Update `__init__.py` re-exports to add `load_plan`.

- [ ] **Step 3.5: Re-run the test — expect pass**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py::test_load_plan_v14_minimal -v`
Expected: PASS.

- [ ] **Step 3.6: Commit**

```bash
git add shield/parsers/shield_parsers/sidecar.py shield/parsers/shield_parsers/__init__.py shield/parsers/tests/test_sidecar.py shield/parsers/tests/fixtures/
git commit -m "feat(shield/parsers): implement load_plan() for v1.4 sidecars"
```

---

### Task 4: JSON Schema validation in `load_plan()`

**Files:**
- Modify: `shield/parsers/shield_parsers/sidecar.py`
- Modify: `shield/parsers/tests/test_sidecar.py`
- Create: `shield/parsers/tests/fixtures/plan-invalid-missing-stories.json`

- [ ] **Step 4.1: Create an invalid fixture**

`shield/parsers/tests/fixtures/plan-invalid-missing-stories.json`:

```json
{
  "version": "1.4",
  "project": "shield",
  "name": "broken",
  "epics": [
    { "id": "EPIC-1", "name": "Missing stories" }
  ]
}
```

- [ ] **Step 4.2: Write failing test**

Append to `tests/test_sidecar.py`:

```python
import pytest

from shield_parsers.sidecar import PlanSchemaError


def test_load_plan_rejects_invalid_schema(schema_path: Path) -> None:
    src = Path(__file__).parent / "fixtures" / "plan-invalid-missing-stories.json"
    with pytest.raises(PlanSchemaError) as exc_info:
        load_plan(src)
    msg = str(exc_info.value)
    # The error must name the failing field so callers can act on it.
    assert "stories" in msg
```

- [ ] **Step 4.3: Run test — expect failure**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py::test_load_plan_rejects_invalid_schema -v`
Expected: FAIL with `ImportError: cannot import name 'PlanSchemaError'`.

- [ ] **Step 4.4: Implement schema validation**

In `sidecar.py`, add at the top after imports:

```python
import jsonschema


class PlanSchemaError(ValueError):
    """Raised when a plan.json file fails JSON Schema validation."""


def _schema_path() -> Path:
    # shield/parsers/shield_parsers/sidecar.py → ../../../schema/plan-sidecar.schema.json
    return Path(__file__).resolve().parents[2] / "schema" / "plan-sidecar.schema.json"


def _load_schema() -> dict[str, Any]:
    return json.loads(_schema_path().read_text(encoding="utf-8"))
```

Modify `load_plan()` — insert schema validation immediately after `raw = json.loads(...)`:

```python
def load_plan(path: Path | str) -> Plan:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))

    schema = _load_schema()
    try:
        jsonschema.validate(raw, schema)
    except jsonschema.ValidationError as e:
        # Path is a deque of keys; render it for the error message.
        loc = "/".join(str(seg) for seg in e.absolute_path) or "<root>"
        raise PlanSchemaError(
            f"plan.json at {p} failed schema validation at {loc}: {e.message}"
        ) from e

    # ... rest unchanged ...
```

Re-export `PlanSchemaError` from `__init__.py`.

- [ ] **Step 4.5: Re-run — expect pass; also re-run all tests to confirm no regression**

Run: `uv run --directory shield/parsers --extra test pytest tests/ -v`
Expected: all PASS (4 tests now).

- [ ] **Step 4.6: Commit**

```bash
git add shield/parsers/
git commit -m "feat(shield/parsers): JSON Schema validation in load_plan() with named errors"
```

---

### Task 5: Schema-version handling (`SchemaVersionTooNew`, back-compat reads)

**Files:**
- Modify: `shield/parsers/shield_parsers/sidecar.py`
- Modify: `shield/parsers/tests/test_sidecar.py`
- Create: `shield/parsers/tests/fixtures/plan-v11-no-pm-ids.json`
- Create: `shield/parsers/tests/fixtures/plan-v20-too-new.json`

- [ ] **Step 5.1: Create v1.1 fixture (no pm_id anywhere)**

`shield/parsers/tests/fixtures/plan-v11-no-pm-ids.json`:

```json
{
  "version": "1.1",
  "project": "shield",
  "name": "legacy",
  "epics": [
    {
      "id": "EPIC-1",
      "name": "Legacy epic",
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "Legacy story",
          "status": "ready",
          "description": "Pre-1.4 story.",
          "tasks": ["t"],
          "acceptance_criteria": ["a"]
        }
      ]
    }
  ]
}
```

- [ ] **Step 5.2: Create v2.0 too-new fixture**

`shield/parsers/tests/fixtures/plan-v20-too-new.json`:

```json
{
  "version": "2.0",
  "project": "shield",
  "name": "future",
  "epics": [
    {
      "id": "EPIC-1",
      "name": "Future epic",
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "Future story",
          "status": "ready",
          "description": "From the future.",
          "tasks": ["t"],
          "acceptance_criteria": ["a"]
        }
      ]
    }
  ]
}
```

- [ ] **Step 5.3: Write failing tests**

Append to `tests/test_sidecar.py`:

```python
from shield_parsers.sidecar import SchemaVersionTooNew


def test_load_plan_v11_reads_with_defaults_for_pm_fields() -> None:
    src = Path(__file__).parent / "fixtures" / "plan-v11-no-pm-ids.json"
    plan = load_plan(src)
    assert plan.version == "1.1"
    assert plan.epics[0].pm_id is None
    assert plan.epics[0].stories[0].pm_id is None


def test_load_plan_rejects_too_new_version() -> None:
    src = Path(__file__).parent / "fixtures" / "plan-v20-too-new.json"
    with pytest.raises(SchemaVersionTooNew) as exc_info:
        load_plan(src)
    assert "2.0" in str(exc_info.value)
```

- [ ] **Step 5.4: Run tests — expect failures**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py -v`
Expected: 2 new tests FAIL (`SchemaVersionTooNew` not defined; v2.0 plan currently passes through schema-validation only since `additionalProperties: true`).

- [ ] **Step 5.5: Implement version handling**

In `sidecar.py`, add after `PlanSchemaError`:

```python
class SchemaVersionTooNew(ValueError):
    """Raised when a plan.json declares a major version we don't support."""


def _parse_version(v: str) -> tuple[int, int]:
    parts = v.split(".")
    return int(parts[0]), int(parts[1])
```

In `load_plan()`, after schema validation succeeds, add:

```python
    declared_major, _ = _parse_version(raw["version"])
    current_major, _ = _parse_version(CURRENT_SCHEMA_VERSION)
    if declared_major > current_major:
        raise SchemaVersionTooNew(
            f"plan.json at {p} declares version {raw['version']!r}, "
            f"newer than supported (max {CURRENT_SCHEMA_VERSION!r})"
        )
```

Re-export `SchemaVersionTooNew` from `__init__.py`.

- [ ] **Step 5.6: Re-run tests**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py -v`
Expected: all PASS (6 tests).

- [ ] **Step 5.7: Commit**

```bash
git add shield/parsers/
git commit -m "feat(shield/parsers): SchemaVersionTooNew + back-compat reads of v1.0+"
```

---

### Task 6: Implement `save_plan()` with atomic write + version stamp

**Files:**
- Modify: `shield/parsers/shield_parsers/sidecar.py`
- Modify: `shield/parsers/shield_parsers/__init__.py`
- Modify: `shield/parsers/tests/test_sidecar.py`

- [ ] **Step 6.1: Write failing tests**

Append to `tests/test_sidecar.py`:

```python
import os

from shield_parsers.sidecar import save_plan


def test_save_plan_stamps_current_version_on_v11_input(tmp_path: Path) -> None:
    src = Path(__file__).parent / "fixtures" / "plan-v11-no-pm-ids.json"
    plan = load_plan(src)
    assert plan.version == "1.1"

    out = tmp_path / "out.json"
    save_plan(out, plan)

    written = json.loads(out.read_text())
    assert written["version"] == "1.4"
    # pm_id keys present on Epic + Story (nullable) after save.
    assert written["epics"][0]["pm_id"] is None
    assert written["epics"][0]["stories"][0]["pm_id"] is None


def test_save_plan_round_trip_preserves_unknown_keys(tmp_path: Path) -> None:
    src = tmp_path / "in.json"
    src.write_text(
        json.dumps(
            {
                "version": "1.4",
                "project": "shield",
                "name": "rt",
                "futuristic_field": "preserved",
                "epics": [
                    {
                        "id": "EPIC-1",
                        "name": "E",
                        "unknown_epic_key": 42,
                        "stories": [
                            {
                                "id": "EPIC-1-S1",
                                "name": "S",
                                "status": "ready",
                                "description": "d",
                                "tasks": ["t"],
                                "acceptance_criteria": ["a"],
                                "unknown_story_key": [1, 2, 3],
                            }
                        ],
                    }
                ],
            }
        )
    )
    plan = load_plan(src)
    out = tmp_path / "out.json"
    save_plan(out, plan)

    written = json.loads(out.read_text())
    assert written["futuristic_field"] == "preserved"
    assert written["epics"][0]["unknown_epic_key"] == 42
    assert written["epics"][0]["stories"][0]["unknown_story_key"] == [1, 2, 3]


def test_save_plan_is_atomic_no_partial_file(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "out.json"
    out.write_text('{"old": "content"}')

    minimal = load_plan(Path(__file__).parent / "fixtures" / "plan-v14-minimal.json")

    # Force os.replace to raise after the temp file is fully written.
    real_replace = os.replace

    def boom(*args, **kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        save_plan(out, minimal)
    monkeypatch.setattr(os, "replace", real_replace)

    # Original file untouched, no orphan .tmp file in the directory.
    assert out.read_text() == '{"old": "content"}'
    leftovers = [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    assert leftovers == [], f"orphan tmp files: {leftovers}"
```

- [ ] **Step 6.2: Run tests — expect failures**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py -v`
Expected: 3 new tests FAIL with `ImportError: cannot import name 'save_plan'`.

- [ ] **Step 6.3: Implement `save_plan()`**

Append to `sidecar.py`:

```python
import tempfile


def _design_ref_to_dict(r: DesignRef) -> dict[str, Any]:
    out = {
        "doc": r.doc,
        "label": r.label,
        "component": r.component,
        "section_id": r.section_id,
        "anchor_url": r.anchor_url,
    }
    if r.stale:
        out["stale"] = True
    out.update(r.extra)
    return out


def _story_to_dict(s: Story) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": s.id,
        "name": s.name,
        "status": s.status,
        "assignee": s.assignee,
        "priority": s.priority,
        "week": s.week,
        "milestone_id": s.milestone_id,
        "description": s.description,
        "tasks": list(s.tasks),
        "acceptance_criteria": list(s.acceptance_criteria),
        "pm_id": s.pm_id,
        "pm_url": s.pm_url,
    }
    if s.design_refs:
        out["design_refs"] = [_design_ref_to_dict(r) for r in s.design_refs]
    out.update(s.extra)
    return out


def _epic_to_dict(e: Epic) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": e.id,
        "name": e.name,
        "pm_id": e.pm_id,
        "pm_url": e.pm_url,
        "stories": [_story_to_dict(s) for s in e.stories],
    }
    out.update(e.extra)
    return out


def _milestone_to_dict(m: Milestone) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": m.id,
        "name": m.name,
        "outcome": m.outcome,
        "exit_criteria": list(m.exit_criteria),
    }
    if m.depends_on:
        out["depends_on"] = list(m.depends_on)
    out.update(m.extra)
    return out


def _plan_to_dict(plan: Plan) -> dict[str, Any]:
    out: dict[str, Any] = {
        "version": CURRENT_SCHEMA_VERSION,    # always stamp current on save
        "project": plan.project,
        "name": plan.name,
        "phase": plan.phase,
        "source_research": plan.source_research,
        "source_prd": plan.source_prd,
        "prd_rubric_version_at_planning": plan.prd_rubric_version_at_planning,
        "last_aligned_with": plan.last_aligned_with,
        "milestones": [_milestone_to_dict(m) for m in plan.milestones],
        "epics": [_epic_to_dict(e) for e in plan.epics],
    }
    if plan.metadata:
        out["metadata"] = dict(plan.metadata)
    out.update(plan.extra)
    return out


def save_plan(path: Path | str, plan: Plan) -> None:
    """Atomically write a Plan to disk as plan.json, stamping CURRENT_SCHEMA_VERSION."""
    p = Path(path)
    data = _plan_to_dict(plan)
    parent = p.parent
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=p.name + ".", suffix=".tmp", dir=parent
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, p)
    except Exception:
        # Clean up the temp file on any failure so we don't leave .tmp orphans.
        if tmp_path.exists():
            tmp_path.unlink()
        raise
```

Add `import os` near the top of `sidecar.py` if not already present. Re-export `save_plan` from `__init__.py`.

- [ ] **Step 6.4: Re-run tests**

Run: `uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py -v`
Expected: all PASS (9 tests).

- [ ] **Step 6.5: Commit**

```bash
git add shield/parsers/
git commit -m "feat(shield/parsers): save_plan() with atomic write + v1.4 stamp + round-trip"
```

---

### Task 7: Phase A checkpoint — coverage + ClickUp adapter still green

- [ ] **Step 7.1: Measure shield/parsers coverage**

Run:
```bash
uv run --directory shield/parsers --extra test pytest \
  --cov=shield_parsers --cov-report=term-missing tests/
```
Expected: coverage ≥ 95% line + branch. If lower, write tests for uncovered branches before proceeding.

- [ ] **Step 7.2: Verify ClickUp adapter tests still green (no-regression check)**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest -v
```
Expected: all 8 existing tests PASS. (We haven't touched the adapter yet; this is a baseline confirmation.)

- [ ] **Step 7.3: Tag the Phase A green checkpoint in commits**

```bash
git commit --allow-empty -m "chore(shield/parsers): Phase A green checkpoint — parsers package complete, clickup adapter untouched"
```

---

## Phase B — Migrate ClickUp `sync.py` to consume `shield_parsers`

### Task 8: Bump `plan-sidecar.schema.json` to v1.4

**Files:**
- Modify: `shield/schema/plan-sidecar.schema.json`
- Modify: `shield/skills/general/plan-docs/sidecar-schema.md`

- [ ] **Step 8.1: Update the JSON Schema — add pm_id/pm_url to Epic, bump $id + title**

In `shield/schema/plan-sidecar.schema.json`, change:

```jsonc
// Line 3
"$id": "https://shield.tesseract/schema/plan-sidecar/1.4",
// Line 4
"title": "Shield plan.json sidecar — schema 1.4",
```

And inside `$defs.epic.properties`, add (just before the closing `}` of the `properties` block, after `stories`):

```jsonc
"pm_id":  { "type": ["string", "null"] },
"pm_url": { "type": ["string", "null"] }
```

- [ ] **Step 8.2: Update the markdown schema doc**

In `shield/skills/general/plan-docs/sidecar-schema.md`, change `Current version: **1.3**.` to `Current version: **1.4**.`

Find the Epic example block (sample JSON near the top). Add to the epic object:

```jsonc
"pm_id":   null,
"pm_url":  null,
```

In the per-field documentation section, add a paragraph next to the existing Story `pm_id` documentation:

```markdown
**`epics[].pm_id` / `pm_url` (1.4+)** — ClickUp/Jira/Notion task ID + URL for the epic itself. `null` until first `/pm-sync`. Symmetric with `stories[].pm_id` / `pm_url`. First sync creates the epic task; subsequent syncs read this field to skip already-synced epics.
```

- [ ] **Step 8.3: Sanity-check the schema parses + minimal v1.4 fixture still validates**

Run:
```bash
uv run --directory shield/parsers --extra test pytest tests/test_sidecar.py -v
```
Expected: all PASS — the v1.4 fixture (Task 3) already includes `pm_id: null` on epics so this should be transparent.

- [ ] **Step 8.4: Commit**

```bash
git add shield/schema/plan-sidecar.schema.json shield/skills/general/plan-docs/sidecar-schema.md
git commit -m "feat(shield/schema): plan.json schema 1.3 → 1.4 (pm_id/pm_url on Epic)"
```

---

### Task 9: Add `shield-parsers` dep to ClickUp adapter pyproject

**Files:**
- Modify: `shield/adapters/clickup/pyproject.toml`

- [ ] **Step 9.1: Add the dep**

In `shield/adapters/clickup/pyproject.toml`, modify the `dependencies` array:

```toml
dependencies = [
    "mcp[cli]>=1.12",
    "httpx>=0.27",
    "beautifulsoup4>=4.12",
    "pydantic>=2.0",
    "shield-adapters-common",
    "shield-parsers",
]
```

And add a sources entry at the same indentation as the existing `shield-adapters-common` entry:

```toml
[tool.uv.sources]
shield-adapters-common = { path = "../_common", editable = true }
shield-parsers = { path = "../../parsers", editable = true }
```

Also add `pytest-cov` to the test extras:

```toml
[project.optional-dependencies]
test = ["pytest>=9.0.3", "jsonschema>=4.0", "respx>=0.21", "pytest-cov>=5"]
```

- [ ] **Step 9.2: Verify install resolves**

Run:
```bash
uv sync --directory shield/adapters/clickup --extra test
uv run --directory shield/adapters/clickup --extra test python -c "import shield_parsers; print(shield_parsers.CURRENT_SCHEMA_VERSION)"
```
Expected: prints `1.4`.

- [ ] **Step 9.3: Verify baseline tests still pass**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest -v
```
Expected: all 8 baseline tests PASS.

- [ ] **Step 9.4: Commit**

```bash
git add shield/adapters/clickup/pyproject.toml shield/adapters/clickup/uv.lock
git commit -m "chore(shield/clickup): add shield-parsers + pytest-cov deps"
```

---

### Task 10: Write failing tests for sidecar sync orchestration

**Files:**
- Create: `shield/adapters/clickup/tests/test_sync_sidecar.py`
- Create: `shield/adapters/clickup/tests/fixtures/plan-v14-2epics-3stories.json`

- [ ] **Step 10.1: Create test fixture**

`shield/adapters/clickup/tests/fixtures/plan-v14-2epics-3stories.json`:

```json
{
  "version": "1.4",
  "project": "shield",
  "name": "sync-fixture",
  "milestones": [
    {"id": "M1", "name": "MS1", "outcome": "X", "exit_criteria": ["X done"]}
  ],
  "epics": [
    {
      "id": "EPIC-1",
      "name": "First epic",
      "pm_id": null,
      "pm_url": null,
      "stories": [
        {
          "id": "EPIC-1-S1", "name": "Story one",
          "status": "ready", "description": "First story.",
          "tasks": ["t1"], "acceptance_criteria": ["a1"],
          "milestone_id": "M1", "pm_id": null, "pm_url": null
        },
        {
          "id": "EPIC-1-S2", "name": "Story two",
          "status": "ready", "description": "Second story.",
          "tasks": ["t2"], "acceptance_criteria": ["a2"],
          "milestone_id": "M1", "pm_id": null, "pm_url": null
        }
      ]
    },
    {
      "id": "EPIC-2",
      "name": "Second epic",
      "pm_id": null,
      "pm_url": null,
      "stories": [
        {
          "id": "EPIC-2-S1", "name": "Story three",
          "status": "ready", "description": "Third story.",
          "tasks": ["t3"], "acceptance_criteria": ["a3"],
          "milestone_id": "M1", "pm_id": null, "pm_url": null
        }
      ]
    }
  ]
}
```

- [ ] **Step 10.2: Write the five failing tests**

`shield/adapters/clickup/tests/test_sync_sidecar.py`:

```python
"""Tests for the sidecar-driven pm_sync_sidecar MCP tool."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.tools.sync import pm_sync_sidecar_impl


FIXTURE = Path(__file__).parent / "fixtures" / "plan-v14-2epics-3stories.json"


@pytest.fixture
def mock_client() -> MagicMock:
    """Mock ClickUpClient — returns empty backlog by default."""
    client = MagicMock()
    client.get_tasks_by_list = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_config() -> MagicMock:
    cfg = MagicMock()
    cfg.clickup.lists.backlog.id = "BACKLOG-LIST"
    cfg.clickup.lists.epics.id = "EPICS-LIST"
    cfg.clickup.relationship_field.id = "REL-FIELD-UUID"
    cfg.naming.story_format = "[{prefix}] {epic_id}-S{index}: {name}"
    return cfg


@pytest.mark.asyncio
async def test_sync_emits_epics_and_stories_from_plan_json(
    mock_client: MagicMock, mock_config: MagicMock
) -> None:
    """Given a plan.json with 2 epics + 3 stories and an empty ClickUp,
    the diff classifies every epic and story as to_create."""
    result = await pm_sync_sidecar_impl(
        plan_json_path=FIXTURE,
        client=mock_client,
        config=mock_config,
    )

    assert result["summary"]["epics"]["to_create"] == 2
    assert result["summary"]["stories"]["to_create"] == 3
    assert all(e["diff"] == "to_create" for e in result["epics"])
    assert all(s["diff"] == "to_create" for s in result["stories"])


@pytest.mark.asyncio
async def test_sync_skips_already_synced_stories(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """Stories with non-null pm_id whose task exists in ClickUp report match."""
    import json
    plan_data = json.loads(FIXTURE.read_text())
    plan_data["epics"][0]["pm_id"] = "EPIC-PM-1"
    plan_data["epics"][0]["pm_url"] = "https://clickup/EPIC-PM-1"
    plan_data["epics"][0]["stories"][0]["pm_id"] = "STORY-PM-1"
    plan_data["epics"][0]["stories"][0]["pm_url"] = "https://clickup/STORY-PM-1"
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan_data))

    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=[
            # epics list
            [{"id": "EPIC-PM-1", "name": "EPIC-1: First epic", "status": {"status": "open"}}],
            # backlog list
            [{"id": "STORY-PM-1", "name": "[SHIELD] EPIC-1-S1: Story one",
              "status": {"status": "open"}, "custom_fields": []}],
        ]
    )

    result = await pm_sync_sidecar_impl(
        plan_json_path=p, client=mock_client, config=mock_config
    )

    matched_epic_ids = [e["id"] for e in result["epics"] if e["diff"] == "match"]
    matched_story_ids = [s["id"] for s in result["stories"] if s["diff"] == "match"]
    assert "EPIC-1" in matched_epic_ids
    assert "EPIC-1-S1" in matched_story_ids


@pytest.mark.asyncio
async def test_sync_idempotent_second_run(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """After a sync that backfilled pm_id everywhere, a second sync against
    the same file produces 0 creates."""
    import json
    plan_data = json.loads(FIXTURE.read_text())
    # Simulate a completed first sync — every epic + story has pm_id.
    for i, e in enumerate(plan_data["epics"], 1):
        e["pm_id"] = f"EPIC-PM-{i}"
        e["pm_url"] = f"https://clickup/EPIC-PM-{i}"
        for j, s in enumerate(e["stories"], 1):
            s["pm_id"] = f"STORY-PM-{i}-{j}"
            s["pm_url"] = f"https://clickup/STORY-PM-{i}-{j}"
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan_data))

    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=[
            [
                {"id": "EPIC-PM-1", "name": "EPIC-1: First epic",
                 "status": {"status": "open"}},
                {"id": "EPIC-PM-2", "name": "EPIC-2: Second epic",
                 "status": {"status": "open"}},
            ],
            [
                {"id": "STORY-PM-1-1", "name": "[SHIELD] EPIC-1-S1: Story one",
                 "status": {"status": "open"}, "custom_fields": []},
                {"id": "STORY-PM-1-2", "name": "[SHIELD] EPIC-1-S2: Story two",
                 "status": {"status": "open"}, "custom_fields": []},
                {"id": "STORY-PM-2-1", "name": "[SHIELD] EPIC-2-S1: Story three",
                 "status": {"status": "open"}, "custom_fields": []},
            ],
        ]
    )

    result = await pm_sync_sidecar_impl(
        plan_json_path=p, client=mock_client, config=mock_config
    )

    assert result["summary"]["epics"]["to_create"] == 0
    assert result["summary"]["stories"]["to_create"] == 0


@pytest.mark.asyncio
async def test_sync_to_link_for_fuzzy_match_on_unlinked_task(
    mock_client: MagicMock, mock_config: MagicMock
) -> None:
    """An unlinked ClickUp task whose name fuzzy-matches a plan story is
    flagged to_link, not to_create."""
    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=[
            # epics list — empty (no epic created yet)
            [],
            # backlog list — has a task with a fuzzy-matching name
            [{
                "id": "STORY-PM-X",
                "name": "Story one - tweaked",
                "status": {"status": "open"},
                "custom_fields": [],
            }],
        ]
    )

    result = await pm_sync_sidecar_impl(
        plan_json_path=FIXTURE, client=mock_client, config=mock_config
    )

    to_link = [s for s in result["stories"] if s["diff"] == "to_link"]
    assert len(to_link) == 1
    assert to_link[0]["id"] == "EPIC-1-S1"
    assert to_link[0]["candidate"]["clickup_id"] == "STORY-PM-X"


@pytest.mark.asyncio
async def test_sync_orphans_in_clickup_surfaced(
    mock_client: MagicMock, mock_config: MagicMock
) -> None:
    """ClickUp tasks with no plan.json counterpart are reported as orphans."""
    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=[
            [],
            [{
                "id": "ORPHAN-1",
                "name": "Some random task created by someone else",
                "status": {"status": "open"},
                "custom_fields": [],
            }],
        ]
    )

    result = await pm_sync_sidecar_impl(
        plan_json_path=FIXTURE, client=mock_client, config=mock_config
    )

    orphans = result["orphans_in_clickup"]
    assert len(orphans) == 1
    assert orphans[0]["id"] == "ORPHAN-1"
```

Also add `pytest-asyncio` to test deps (next step's pyproject change).

- [ ] **Step 10.3: Add `pytest-asyncio` to test extras**

In `shield/adapters/clickup/pyproject.toml`:

```toml
[project.optional-dependencies]
test = ["pytest>=9.0.3", "pytest-asyncio>=0.23", "jsonschema>=4.0", "respx>=0.21", "pytest-cov>=5"]
```

Add asyncio mode config:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 10.4: Run tests — expect failures**

Run:
```bash
uv sync --directory shield/adapters/clickup --extra test
uv run --directory shield/adapters/clickup --extra test pytest tests/test_sync_sidecar.py -v
```
Expected: all 5 new tests FAIL with `ImportError: cannot import name 'pm_sync_sidecar_impl' from 'server.tools.sync'`.

- [ ] **Step 10.5: Commit (RED state)**

```bash
git add shield/adapters/clickup/tests/test_sync_sidecar.py shield/adapters/clickup/tests/fixtures/plan-v14-2epics-3stories.json shield/adapters/clickup/pyproject.toml shield/adapters/clickup/uv.lock
git commit -m "test(shield/clickup): failing tests for pm_sync_sidecar (Phase B RED)"
```

---

### Task 11: Rewrite `sync.py` — implement `pm_sync_sidecar_impl`

**Files:**
- Modify: `shield/adapters/clickup/server/tools/sync.py`

The full rewrite. Approach: extract the diff logic into a sync-able `pm_sync_sidecar_impl(plan_json_path, client, config)` function so tests can call it without the FastMCP plumbing, then have the `@mcp.tool()` wrapper call into it.

- [ ] **Step 11.1: Rewrite `sync.py` end-to-end**

Replace the entire file contents:

```python
"""MCP tool: pm_sync_sidecar — diff plan.json against ClickUp state."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from shield_parsers.sidecar import Plan, load_plan

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig
from server.tools._helpers import _get_linked_epic_ids


FUZZY_MATCH_THRESHOLD = 0.8
FUZZY_LINK_THRESHOLD = 0.6

# Strips epic prefixes from ClickUp task names so we compare just the story name
# portion. Matches "P3 - Install Istio" or "[Project] EPIC-1-S1: ..." prefixes.
_EPIC_PREFIX_RE = re.compile(r"^[A-Z]+\d+[a-z]?\s*-\s*")


def _strip_name_prefix(task_name: str) -> str:
    """Strip "[Project] EPIC-N-Sk: " or "Pn - " prefixes so the comparison
    runs against the bare story name."""
    if ": " in task_name:
        return task_name.split(": ", 1)[-1].strip()
    if _EPIC_PREFIX_RE.match(task_name):
        return _EPIC_PREFIX_RE.sub("", task_name).strip()
    return task_name.strip()


def _fuzzy_ratio(plan_name: str, task_name: str) -> float:
    return SequenceMatcher(
        None, plan_name.lower().strip(), _strip_name_prefix(task_name).lower()
    ).ratio()


def _best_fuzzy_match(
    plan_name: str, candidates: list[dict[str, Any]], used_ids: set[str]
) -> tuple[dict[str, Any] | None, float]:
    best: dict[str, Any] | None = None
    best_ratio = 0.0
    for task in candidates:
        if task["id"] in used_ids:
            continue
        ratio = _fuzzy_ratio(plan_name, task.get("name", ""))
        if ratio > best_ratio:
            best_ratio = ratio
            best = task
    return best, best_ratio


def _classify(plan_name: str, task: dict[str, Any] | None, ratio: float) -> str:
    if task is None:
        return "to_create"
    if ratio >= FUZZY_MATCH_THRESHOLD:
        return "match"
    return "to_update"


async def pm_sync_sidecar_impl(
    plan_json_path: Path | str,
    client: ClickUpClient,
    config: SprintPlannerConfig,
    epic: str | None = None,
) -> dict[str, Any]:
    """Diff a plan.json sidecar against ClickUp state. Pure read — no mutations.

    Returns a structured diff with classifications: match | to_update |
    to_create | to_link | orphan.
    """
    plan: Plan = load_plan(plan_json_path)

    epics_to_sync = plan.epics
    if epic is not None:
        epics_to_sync = [e for e in plan.epics if e.id == epic]
        if not epics_to_sync:
            return {
                "error": f"Epic {epic!r} not in plan.json. "
                f"Available: {[e.id for e in plan.epics]}"
            }

    rel_field_id = config.clickup.relationship_field.id

    # Fetch ClickUp state for epics + backlog lists.
    try:
        clickup_epic_tasks = await client.get_tasks_by_list(
            config.clickup.lists.epics.id, include_closed=True
        )
        clickup_backlog_tasks = await client.get_tasks_by_list(
            config.clickup.lists.backlog.id, include_closed=True
        )
    except ClickUpAPIError as e:
        return {"error": f"Failed to fetch ClickUp tasks: {e}"}

    used_epic_ids: set[str] = set()
    used_story_ids: set[str] = set()

    epic_results: list[dict[str, Any]] = []

    # ----- Epic diff -----
    for plan_epic in epics_to_sync:
        # 1. Exact ID match if plan_epic.pm_id is set.
        match_task = None
        ratio = 0.0
        if plan_epic.pm_id:
            match_task = next(
                (t for t in clickup_epic_tasks if t["id"] == plan_epic.pm_id), None
            )
            if match_task:
                ratio = _fuzzy_ratio(plan_epic.name, match_task.get("name", ""))

        # 2. Fuzzy match against the Flow Epics list.
        if match_task is None:
            candidate, candidate_ratio = _best_fuzzy_match(
                plan_epic.name, clickup_epic_tasks, used_epic_ids
            )
            if candidate and candidate_ratio >= FUZZY_MATCH_THRESHOLD:
                match_task = candidate
                ratio = candidate_ratio
            elif candidate and candidate_ratio >= FUZZY_LINK_THRESHOLD:
                # Ambiguous — flag to_link with the candidate
                used_epic_ids.add(candidate["id"])
                epic_results.append({
                    "id": plan_epic.id,
                    "name": plan_epic.name,
                    "pm_id": None,
                    "diff": "to_link",
                    "candidate": {
                        "clickup_id": candidate["id"],
                        "clickup_name": candidate.get("name"),
                        "fuzzy_ratio": round(candidate_ratio, 3),
                    },
                })
                continue

        if match_task:
            used_epic_ids.add(match_task["id"])
            epic_results.append({
                "id": plan_epic.id,
                "name": plan_epic.name,
                "pm_id": match_task["id"],
                "diff": _classify(plan_epic.name, match_task, ratio),
                "candidate": None,
            })
        else:
            epic_results.append({
                "id": plan_epic.id,
                "name": plan_epic.name,
                "pm_id": None,
                "diff": "to_create",
                "candidate": None,
            })

    # ----- Story diff -----
    story_results: list[dict[str, Any]] = []
    for plan_epic in epics_to_sync:
        # Find this epic's ClickUp ID (just-matched in epic_results or pre-existing).
        epic_pm_id = next(
            (r["pm_id"] for r in epic_results if r["id"] == plan_epic.id and r["pm_id"]),
            None,
        )

        # Linked backlog tasks (relationship field points to this epic).
        linked_backlog = (
            [t for t in clickup_backlog_tasks
             if epic_pm_id in _get_linked_epic_ids(t, rel_field_id)]
            if epic_pm_id else []
        )
        # Unlinked backlog tasks (no relationship field set) — possible to_link candidates.
        unlinked_backlog = [
            t for t in clickup_backlog_tasks
            if not _get_linked_epic_ids(t, rel_field_id)
        ]

        for plan_story in plan_epic.stories:
            match_task = None
            ratio = 0.0

            # 1. Exact ID match.
            if plan_story.pm_id:
                match_task = next(
                    (t for t in clickup_backlog_tasks if t["id"] == plan_story.pm_id),
                    None,
                )
                if match_task:
                    ratio = _fuzzy_ratio(plan_story.name, match_task.get("name", ""))

            # 2. Fuzzy match against linked tasks.
            if match_task is None:
                candidate, candidate_ratio = _best_fuzzy_match(
                    plan_story.name, linked_backlog, used_story_ids
                )
                if candidate and candidate_ratio >= FUZZY_MATCH_THRESHOLD:
                    match_task = candidate
                    ratio = candidate_ratio

            # 3. Fuzzy match against unlinked tasks for to_link candidates.
            if match_task is None:
                candidate, candidate_ratio = _best_fuzzy_match(
                    plan_story.name, unlinked_backlog, used_story_ids
                )
                if candidate and candidate_ratio >= FUZZY_LINK_THRESHOLD:
                    used_story_ids.add(candidate["id"])
                    story_results.append({
                        "id": plan_story.id,
                        "epic_id": plan_epic.id,
                        "name": plan_story.name,
                        "pm_id": None,
                        "diff": "to_link",
                        "candidate": {
                            "clickup_id": candidate["id"],
                            "clickup_name": candidate.get("name"),
                            "fuzzy_ratio": round(candidate_ratio, 3),
                        },
                    })
                    continue

            if match_task:
                used_story_ids.add(match_task["id"])
                story_results.append({
                    "id": plan_story.id,
                    "epic_id": plan_epic.id,
                    "name": plan_story.name,
                    "pm_id": match_task["id"],
                    "diff": _classify(plan_story.name, match_task, ratio),
                    "candidate": None,
                })
            else:
                story_results.append({
                    "id": plan_story.id,
                    "epic_id": plan_epic.id,
                    "name": plan_story.name,
                    "pm_id": None,
                    "diff": "to_create",
                    "candidate": None,
                })

    # ----- Orphans (ClickUp backlog tasks not matched to any plan story) -----
    matched_backlog_ids = used_story_ids
    orphans = [
        {"id": t["id"], "name": t.get("name", "")}
        for t in clickup_backlog_tasks
        if t["id"] not in matched_backlog_ids
    ]

    summary = {
        "epics": {
            "match":     sum(1 for r in epic_results if r["diff"] == "match"),
            "to_create": sum(1 for r in epic_results if r["diff"] == "to_create"),
            "to_update": sum(1 for r in epic_results if r["diff"] == "to_update"),
            "to_link":   sum(1 for r in epic_results if r["diff"] == "to_link"),
            "orphan":    0,
        },
        "stories": {
            "match":     sum(1 for r in story_results if r["diff"] == "match"),
            "to_create": sum(1 for r in story_results if r["diff"] == "to_create"),
            "to_update": sum(1 for r in story_results if r["diff"] == "to_update"),
            "to_link":   sum(1 for r in story_results if r["diff"] == "to_link"),
            "orphan":    len(orphans),
        },
    }

    return {
        "epics": epic_results,
        "stories": story_results,
        "summary": summary,
        "orphans_in_clickup": orphans,
    }


def register(
    mcp: FastMCP,
    client: ClickUpClient,
    config: SprintPlannerConfig,
    base_path: Path,
    action_log: ActionLog | None = None,
):
    @mcp.tool()
    async def pm_sync_sidecar(
        plan_json_path: str,
        epic: str | None = None,
    ) -> dict[str, Any]:
        """Diff a plan.json sidecar against ClickUp state. Pure read — no
        mutations. Returns match | to_update | to_create | to_link | orphan
        classifications for every epic + story.

        Args:
            plan_json_path: Path to the plan.json file to diff against ClickUp.
            epic: Optional plan-epic id (e.g. "EPIC-1") to scope the diff.
        """
        return await pm_sync_sidecar_impl(
            plan_json_path=plan_json_path,
            client=client,
            config=config,
            epic=epic,
        )
```

- [ ] **Step 11.2: Run the new tests — expect pass**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest tests/test_sync_sidecar.py -v
```
Expected: all 5 new tests PASS.

- [ ] **Step 11.3: Run the full test suite — confirm baseline still green**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest -v
```
Expected: all 8 baseline + 5 new = 13 tests PASS.

- [ ] **Step 11.4: Commit (GREEN state)**

```bash
git add shield/adapters/clickup/server/tools/sync.py
git commit -m "feat(shield/clickup): pm_sync_sidecar reads plan.json via shield_parsers (Phase B GREEN)"
```

---

### Task 12: Update `/pm-sync` skill SKILL.md to invoke `pm_sync_sidecar`

**Files:**
- Modify: `shield/skills/pm-sync/SKILL.md`

- [ ] **Step 12.1: Update the Available Tools table**

In `shield/skills/pm-sync/SKILL.md`, change the line:

```markdown
| `pm_sync` | Diff plan sidecar JSON against PM tool state (read-only) |
```

to:

```markdown
| `pm_sync_sidecar` | Diff plan.json sidecar against PM tool state (read-only) — requires plan_json_path arg |
```

- [ ] **Step 12.2: Update the "Creating Stories" workflow**

Find the `### Creating Stories` block and replace the `pm_sync(plan="<name>", epic="P1a")` line with:

```
2. pm_sync_sidecar(plan_json_path="{output_dir}/{feature}/plan.json", epic=None)
   → returns diff: match / to_create / to_update / to_link / orphan per epic + story
```

Update the "Updating Stories" workflow similarly:

```
1. pm_sync_sidecar(plan_json_path=..., epic="EPIC-1") → identify stale stories
```

- [ ] **Step 12.3: Update Rule 5 (locating plan sidecars)**

Find Rule 5 (`**Always locate and read plan sidecar JSONs first.**`) and append:

```
The MCP tool `pm_sync_sidecar` now takes the full plan_json_path as an explicit argument — the skill resolves the path and passes it in.
```

- [ ] **Step 12.4: Commit**

```bash
git add shield/skills/pm-sync/SKILL.md
git commit -m "docs(shield/pm-sync): SKILL.md routes to pm_sync_sidecar"
```

---

## Phase C — Delete the old parser path

### Task 13: Delete `shield/adapters/clickup/server/parsers/`

**Files:**
- Delete: `shield/adapters/clickup/server/parsers/` (whole directory)

- [ ] **Step 13.1: Confirm nothing in the codebase still imports the old parsers**

Run:
```bash
grep -rn "from server.parsers\|server\.parsers" shield/adapters/clickup/ \
  --include='*.py' | grep -v __pycache__
```
Expected: empty output. (Phase B's rewrite removed the only consumer.)

- [ ] **Step 13.2: Delete the directory**

Run:
```bash
rm -rf shield/adapters/clickup/server/parsers/
```

- [ ] **Step 13.3: Run tests — confirm still green**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest -v
```
Expected: all 13 tests PASS.

- [ ] **Step 13.4: Commit**

```bash
git add -u shield/adapters/clickup/server/parsers/
git commit -m "refactor(shield/clickup): delete server/parsers/ — replaced by shield_parsers"
```

---

### Task 14: Strip dead config fields from `config.py`

**Files:**
- Modify: `shield/adapters/clickup/server/config.py`

- [ ] **Step 14.1: Delete the dead Pydantic models**

In `shield/adapters/clickup/server/config.py`, remove these class definitions:

- `class HtmlExtractionConfig(BaseModel)` (lines ~61–66)
- `class StoryExtractionConfig(BaseModel)` (lines ~68–69)
- The `class EpicConfig(BaseModel)` (lines ~47–52)
- The `class PlanDocsConfig(BaseModel)` (lines ~55–58)

- [ ] **Step 14.2: Remove their use sites**

In `class SprintPlannerConfig(BaseModel)`, remove:

```python
plan_docs: PlanDocsConfig
story_extraction: StoryExtractionConfig = Field(default_factory=StoryExtractionConfig)
```

In `load_shield_config()`, remove the entire `# Build epic configs from pm.json` block (the `epic_entries`/`epics` list comprehension) and the `plan_docs=PlanDocsConfig(...)` constructor call in the return statement.

- [ ] **Step 14.3: Run tests — confirm still green**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest -v
```
Expected: all 13 tests PASS.

- [ ] **Step 14.4: Commit**

```bash
git add shield/adapters/clickup/server/config.py
git commit -m "refactor(shield/clickup): drop PlanDocsConfig + StoryExtractionConfig from config"
```

---

### Task 15: Update `pm.schema.json` to drop dead keys

**Files:**
- Modify: `shield/schemas/pm.schema.json`

- [ ] **Step 15.1: Inspect existing pm.schema.json**

Run:
```bash
cat shield/schemas/pm.schema.json
```

- [ ] **Step 15.2: Remove `epics`, `plan_docs`, and `story_extraction` keys from the schema**

Edit `shield/schemas/pm.schema.json`:
- Remove the `epics` property + its `$defs.epic` definition
- Remove the `plan_docs` property + its `$defs.plan_docs` definition (if present)
- Remove the `story_extraction` property (if present)
- Ensure `additionalProperties: true` stays so any leftover legacy keys load without failing

- [ ] **Step 15.3: Validate the user's existing pm.json still passes**

Run (uses the standalone validator):
```bash
uv run --with jsonschema python -c "
import json, jsonschema
schema = json.load(open('shield/schemas/pm.schema.json'))
pm = json.load(open('/Users/apple/.shield/projects/Shield/pm.json'))
jsonschema.validate(pm, schema)
print('valid')
"
```
Expected: `valid`.

- [ ] **Step 15.4: Commit**

```bash
git add shield/schemas/pm.schema.json
git commit -m "refactor(shield/schemas): pm.schema.json drops epics/plan_docs/story_extraction"
```

---

### Task 16: Update `/shield init` narrative

**Files:**
- Modify: `shield/commands/init.md`

- [ ] **Step 16.1: Remove old-shape references from step 7**

In `shield/commands/init.md`, in the step-7 PM tool section, remove any mention of `epics[]` or `plan_docs` blocks if present. The current init step-7 in this repo doesn't actually scaffold them, but check for any leftover narrative referencing those fields. The minimal pm.json shape to keep documented:

```json
{
  "adapter": "clickup",
  "adapter_mode": "hybrid",
  "workspace_id": "...",
  "space":  { "id": "...", "name": "..." },
  "folder": { "id": "...", "name": "..." },
  "lists":  {
    "epics":   { "id": "...", "name": "Flow Epics" },
    "backlog": { "id": "...", "name": "Flow Backlog" }
  },
  "relationship_field": { "id": "...", "type": "list_relationship" },
  "naming": { "project_prefix": "...", "story_format": "[{prefix}] {epic_id}-S{index}: {name}" }
}
```

- [ ] **Step 16.2: Commit**

```bash
git add shield/commands/init.md
git commit -m "docs(shield/init): pm.json shape no longer carries epics[]/plan_docs"
```

---

## Phase D — Coverage tooling + eval coverage

### Task 17: Add `shield/scripts/coverage_gate.py`

**Files:**
- Create: `shield/scripts/coverage_gate.py`

- [ ] **Step 17.1: Write the script**

`shield/scripts/coverage_gate.py`:

```python
#!/usr/bin/env -S uv run --with coverage --script
"""Patch-coverage gate for Shield Python packages.

Parses a coverage.xml file emitted by pytest --cov --cov-report=xml,
diffs against a base git ref to identify patch lines, then fails if the
fraction of patch lines covered is below the configured threshold.

Usage:
    uv run --with coverage shield/scripts/coverage_gate.py \\
        --xml shield/parsers/coverage.xml \\
        --threshold 95 \\
        --base-ref main
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _parse_covered_lines(xml_path: Path) -> dict[str, set[int]]:
    """Return {filename: {covered_line_numbers}} from coverage.xml."""
    tree = ET.parse(xml_path)
    out: dict[str, set[int]] = {}
    for cls in tree.iter("class"):
        filename = cls.get("filename")
        if filename is None:
            continue
        covered: set[int] = set()
        for line in cls.iter("line"):
            try:
                lineno = int(line.get("number", "0"))
                hits = int(line.get("hits", "0"))
            except ValueError:
                continue
            if hits > 0:
                covered.add(lineno)
        out.setdefault(filename, set()).update(covered)
    return out


def _patch_lines(base_ref: str) -> dict[str, set[int]]:
    """Return {filename: {added_or_modified_line_numbers}} relative to base_ref."""
    result = subprocess.run(
        ["git", "diff", "--unified=0", f"{base_ref}...HEAD"],
        capture_output=True, text=True, check=True,
    )
    out: dict[str, set[int]] = {}
    current_file: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            out.setdefault(current_file, set())
        elif line.startswith("@@") and current_file is not None:
            # @@ -X,Y +A,B @@   — pull A and B from the +A,B segment.
            after = line.split("+", 1)[1].split(" ", 1)[0]
            if "," in after:
                start_str, count_str = after.split(",")
                start, count = int(start_str), int(count_str)
            else:
                start, count = int(after), 1
            for ln in range(start, start + count):
                out[current_file].add(ln)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--xml", required=True, type=Path, help="coverage.xml path")
    p.add_argument("--threshold", required=True, type=float,
                   help="Minimum % of patch lines that must be covered")
    p.add_argument("--base-ref", default="main",
                   help="Git ref to diff against (default: main)")
    args = p.parse_args()

    covered = _parse_covered_lines(args.xml)
    patch = _patch_lines(args.base_ref)

    total_patch = 0
    total_covered = 0
    uncovered: list[tuple[str, int]] = []

    for filename, lines in patch.items():
        if not filename.endswith(".py"):
            continue
        # Match coverage paths (which are package-relative) against git paths
        # (which are repo-relative).
        cov_for_file = next(
            (cov for path, cov in covered.items() if filename.endswith(path)),
            set(),
        )
        for ln in lines:
            total_patch += 1
            if ln in cov_for_file:
                total_covered += 1
            else:
                uncovered.append((filename, ln))

    if total_patch == 0:
        print("No Python patch lines in scope — gate skipped.")
        return 0

    pct = 100.0 * total_covered / total_patch
    print(f"Patch coverage: {total_covered}/{total_patch} ({pct:.1f}%); "
          f"threshold {args.threshold:.1f}%")

    if pct < args.threshold:
        print(f"FAIL: patch coverage {pct:.1f}% < threshold {args.threshold:.1f}%")
        print("Uncovered patch lines:")
        for f, ln in sorted(uncovered):
            print(f"  {f}:{ln}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 17.2: Make it executable**

Run:
```bash
chmod +x shield/scripts/coverage_gate.py
```

- [ ] **Step 17.3: Smoke-test against the parsers coverage**

Run:
```bash
uv run --directory shield/parsers --extra test pytest --cov=shield_parsers --cov-report=xml
uv run --with coverage shield/scripts/coverage_gate.py \
  --xml shield/parsers/coverage.xml \
  --threshold 90 \
  --base-ref HEAD~10
```
Expected: prints patch coverage summary; exits 0 (since the parsers were added in this branch with comprehensive tests).

- [ ] **Step 17.4: Commit**

```bash
git add shield/scripts/coverage_gate.py
git commit -m "tooling(shield): patch-coverage gate script (uv-run, no install)"
```

---

### Task 18: Add eval `shield/evals/pm-sync-sidecar/`

**Files:**
- Create: `shield/evals/pm-sync-sidecar/eval.yaml`
- Create: `shield/evals/pm-sync-sidecar/fixtures/plan-v14-minimal.json`
- Create: `shield/evals/pm-sync-sidecar/README.md`

- [ ] **Step 18.1: Inspect existing eval structure to match conventions**

Run:
```bash
ls shield/evals/plan-trd/ 2>/dev/null || ls shield/evals/prd-docs/ 2>/dev/null
cat shield/evals/plan-trd.yaml 2>/dev/null | head -40
```

- [ ] **Step 18.2: Create the minimal v1.4 fixture (same shape as the parsers test fixture)**

`shield/evals/pm-sync-sidecar/fixtures/plan-v14-minimal.json` — copy the contents from `shield/parsers/tests/fixtures/plan-v14-minimal.json`.

- [ ] **Step 18.3: Create `eval.yaml`**

`shield/evals/pm-sync-sidecar/eval.yaml`:

```yaml
name: pm-sync-sidecar
description: |
  Verifies the /pm-sync skill orchestrates sidecar-driven sync correctly:
  reads plan.json, calls pm_sync_sidecar, presents the diff, confirms with user,
  calls pm_bulk_create epic-first then story-first, backfills pm_id back into
  plan.json, re-renders plan.md.

prompt: |
  Run /pm-sync against {fixture}. There is exactly one epic with two stories
  in the plan.json. ClickUp is empty (mocked). Confirm "apply all" when asked.
  After the sync, report the final pm_id values written back to plan.json.

fixtures:
  - path: fixtures/plan-v14-minimal.json
    role: plan_json

expectations:
  positive:
    - "pm_sync_sidecar is invoked exactly once with the fixture's path"
    - "pm_bulk_create is invoked at least twice: once with list_id matching the epics list, once with list_id matching the backlog list"
    - "The first pm_bulk_create call (epics) happens before the second (stories) — epic-first ordering"
    - "Stories in the second pm_bulk_create call carry epic_id values returned from the first call (links to just-created epic)"
    - "Final plan.json on disk has pm_id and pm_url populated on the epic and both stories"
    - "Final plan.json on disk has version: \"1.4\""
  negative:
    - "Stories are NOT created before epics"
    - "pm_id is NOT left null on successfully created stories"
    - "version is NOT downgraded below \"1.4\""

red_green_paper_trail:
  red: "Pre-change agent run (commit <BASE_REF>): documents the failure mode — pm_sync errors out with 'Unknown plan doc format' before producing any operations."
  green: "Post-change agent run (commit <THIS_PR>): documents the expected sequence — load plan.json, diff, confirm, epic-first bulk_create, story bulk_create with set_relationships=true, atomic save, plan.md rerender."
```

Replace `<BASE_REF>` and `<THIS_PR>` placeholders during PR-creation with the actual commit SHAs.

- [ ] **Step 18.4: Add a brief README**

`shield/evals/pm-sync-sidecar/README.md`:

```markdown
# pm-sync-sidecar eval

Skill-orchestration eval for the sidecar-driven `/pm-sync` flow.

See [`docs/superpowers/specs/2026-05-26-shield-pm-sync-sidecar-refactor-design.md`](../../../docs/superpowers/specs/2026-05-26-shield-pm-sync-sidecar-refactor-design.md) §9 for the eval contract.

## Run

```bash
uv run --with pyyaml shield/evals/run.py shield/evals/pm-sync-sidecar
```

## RED→GREEN paper trail

Recorded in the PR body for the sidecar refactor. The RED transcript shows
`/pm-sync` failing with `Unknown plan doc format: 'json'` against the
fixture; the GREEN transcript shows the full epic-first bulk_create + plan.json
backfill sequence.
```

- [ ] **Step 18.5: Commit**

```bash
git add shield/evals/pm-sync-sidecar/
git commit -m "eval(shield): pm-sync-sidecar eval + minimal v1.4 fixture (RED→GREEN)"
```

---

### Task 19: Plugin version bump per CLAUDE.md

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `shield/adapters/clickup/pyproject.toml`

- [ ] **Step 19.1: Inspect current versions**

Run:
```bash
grep -A1 '"name": "shield"' .claude-plugin/marketplace.json | head -5
grep '^version' shield/adapters/clickup/pyproject.toml
```

- [ ] **Step 19.2: Bump in `.claude-plugin/marketplace.json`**

Find the `shield` entry and bump its `version` field to the next minor (e.g., `2.20.0` → `2.21.0` — confirm against the actual current value first).

- [ ] **Step 19.3: Bump in clickup adapter `pyproject.toml`**

Change `version = "2.1.0"` to `version = "2.2.0"` (or the corresponding next minor of whatever is current).

- [ ] **Step 19.4: Commit**

```bash
git add .claude-plugin/marketplace.json shield/adapters/clickup/pyproject.toml
git commit -m "chore(shield): version bump for sidecar refactor"
```

---

### Task 20: Phase D checkpoint — full suite + DoD verification

- [ ] **Step 20.1: Run all Python tests + coverage**

Run:
```bash
uv run --directory shield/parsers --extra test pytest --cov=shield_parsers --cov-report=term-missing
uv run --directory shield/adapters/clickup --extra test pytest --cov=server --cov-report=term-missing
uv run --directory shield/adapters/_common --extra test pytest --cov=shield_adapters_common --cov-report=term-missing
```

Expected:
- shield/parsers: ≥ 95% coverage
- shield/adapters/clickup/server/tools: ≥ 85% on touched files (sync.py, bulk_create.py)
- shield/adapters/_common: ≥ 95% (already at this level)

- [ ] **Step 20.2: Confirm grep cleanliness**

Run:
```bash
grep -r "from server.parsers" shield/ --include='*.py' | grep -v __pycache__
grep -r "PlanDocsConfig\|HtmlExtractionConfig\|StoryExtractionConfig" shield/ --include='*.py' | grep -v __pycache__
```
Expected: empty output for both.

- [ ] **Step 20.3: End-to-end smoke test (live ClickUp run)**

This is a manual / interactive step. Run `/pm-sync` against `docs/shield/plan-trd-refactor-20260524/plan.json`. Confirm:
- Adapter advertises `pm_sync_sidecar` in `pm_get_capabilities`
- Diff shows 5 epics + 16 stories as `to_create`
- Approve "apply all"
- After: plan.json's epics and stories all have non-null `pm_id`/`pm_url`
- After: re-running `/pm-sync` against the same plan.json produces 0 creates / 0 updates

- [ ] **Step 20.4: Tag the GREEN checkpoint**

```bash
git commit --allow-empty -m "chore(shield): Phase D green — sidecar refactor complete, DoD met"
```

---

## Self-Review

Per the writing-plans skill, after all tasks are written:

1. **Spec coverage** — every spec section has at least one task:
   - Spec §4.1 (parsers package) → Tasks 1–7
   - Spec §4.2 (clickup adapter changes) → Tasks 9, 11, 13–14
   - Spec §4.3 (schema 1.3 → 1.4) → Task 8
   - Spec §5 (sync pipeline) → Task 11 (impl) + Task 12 (skill)
   - Spec §6 (test-first phasing) → Tasks 1–18 follow Phase A/B/C/D ordering
   - Spec §7 (coverage tooling) → Tasks 17, 20
   - Spec §8 (migration) → Tasks 15, 16
   - Spec §9 (evals) → Task 18
   - Spec §11 (DoD) → Task 20
2. **Placeholder scan** — `<BASE_REF>` and `<THIS_PR>` in Task 18 eval.yaml are intentional fill-at-PR-time placeholders; no other TBD/TODO.
3. **Type consistency** — `pm_sync_sidecar_impl` signature matches across Task 10 (tests), Task 11 (impl); dataclass field names consistent Task 2 → 3 → 6.

If anything's off, fix inline.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-26-shield-pm-sync-sidecar-refactor.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
