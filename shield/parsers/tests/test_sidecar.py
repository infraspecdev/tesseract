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
