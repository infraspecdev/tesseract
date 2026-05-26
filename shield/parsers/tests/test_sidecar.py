"""Tests for shield_parsers.sidecar."""

from __future__ import annotations

import json

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


from pathlib import Path

import pytest

from shield_parsers.sidecar import PlanSchemaError, load_plan


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


def test_load_plan_rejects_invalid_schema() -> None:
    src = Path(__file__).parent / "fixtures" / "plan-invalid-missing-stories.json"
    with pytest.raises(PlanSchemaError) as exc_info:
        load_plan(src)
    msg = str(exc_info.value)
    # The error must name the failing field so callers can act on it.
    assert "stories" in msg


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
