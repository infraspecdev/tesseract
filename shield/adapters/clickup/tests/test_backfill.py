"""Tests for the pm_backfill_ids write-back MCP tool."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from shield_parsers.sidecar import load_plan
from server.tools.backfill import pm_backfill_ids_impl


FIXTURE = Path(__file__).parent / "fixtures" / "plan-v14-2epics-3stories.json"


@pytest.fixture
def plan_path(tmp_path) -> Path:
    """Copy the shared fixture into tmp_path so we never mutate it."""
    dest = tmp_path / "plan.json"
    shutil.copy(FIXTURE, dest)
    return dest


def test_backfill_writes_epic_and_story_pm_ids(plan_path):
    result = pm_backfill_ids_impl(
        plan_json_path=str(plan_path),
        epics=[{"id": "EPIC-1", "pm_id": "86epic1", "pm_url": "https://app.clickup.com/t/86epic1"}],
        stories=[
            {"id": "EPIC-1-S1", "pm_id": "86s1", "pm_url": "https://app.clickup.com/t/86s1"},
            {"id": "EPIC-1-S2", "pm_id": "86s2", "pm_url": "https://app.clickup.com/t/86s2"},
        ],
    )

    plan = load_plan(plan_path)
    epics = {e.id: e for e in plan.epics}
    stories = {s.id: s for e in plan.epics for s in e.stories}

    assert epics["EPIC-1"].pm_id == "86epic1"
    assert epics["EPIC-1"].pm_url == "https://app.clickup.com/t/86epic1"
    assert stories["EPIC-1-S1"].pm_id == "86s1"
    assert stories["EPIC-1-S1"].pm_url == "https://app.clickup.com/t/86s1"
    assert stories["EPIC-1-S2"].pm_id == "86s2"

    # Untouched epic + story stay null.
    assert epics["EPIC-2"].pm_id is None
    assert stories["EPIC-2-S1"].pm_id is None

    # Result reports what it updated.
    assert "EPIC-1" in result["updated_epics"]
    assert set(result["updated_stories"]) == {"EPIC-1-S1", "EPIC-1-S2"}
    assert result["not_found"] == []

    # Written file is stamped schema 1.4.
    raw = json.loads(plan_path.read_text())
    assert raw["version"] == "1.4"
    assert result["version"] == "1.4"


def test_backfill_unknown_id_reported_not_silently_dropped(plan_path):
    result = pm_backfill_ids_impl(
        plan_json_path=str(plan_path),
        epics=[
            {"id": "EPIC-1", "pm_id": "86epic1", "pm_url": "u1"},
            {"id": "EPIC-99", "pm_id": "86bad", "pm_url": "bad"},
        ],
        stories=[
            {"id": "EPIC-1-S1", "pm_id": "86s1", "pm_url": "us1"},
            {"id": "EPIC-1-S9", "pm_id": "86sbad", "pm_url": "bads"},
        ],
    )

    # Valid ids still written.
    plan = load_plan(plan_path)
    epics = {e.id: e for e in plan.epics}
    stories = {s.id: s for e in plan.epics for s in e.stories}
    assert epics["EPIC-1"].pm_id == "86epic1"
    assert stories["EPIC-1-S1"].pm_id == "86s1"

    # Bad ids surfaced, not silently dropped.
    not_found = result["not_found"]
    assert {"id": "EPIC-99", "type": "epic"} in not_found
    assert {"id": "EPIC-1-S9", "type": "story"} in not_found
    assert "EPIC-99" not in result["updated_epics"]
    assert "EPIC-1-S9" not in result["updated_stories"]


def test_backfill_is_idempotent_and_preserves_other_fields(plan_path):
    before = load_plan(plan_path)
    s1_before = next(s for e in before.epics for s in e.stories if s.id == "EPIC-1-S1")
    name_before = s1_before.name
    desc_before = s1_before.description
    milestone_before = s1_before.milestone_id

    pm_backfill_ids_impl(
        plan_json_path=str(plan_path),
        epics=[{"id": "EPIC-1", "pm_id": "86epic1", "pm_url": "u1"}],
        stories=[{"id": "EPIC-1-S1", "pm_id": "86s1", "pm_url": "us1"}],
    )

    after = load_plan(plan_path)
    s1_after = next(s for e in after.epics for s in e.stories if s.id == "EPIC-1-S1")
    assert s1_after.name == name_before
    assert s1_after.description == desc_before
    assert s1_after.milestone_id == milestone_before
    assert s1_after.tasks == s1_before.tasks
    assert s1_after.acceptance_criteria == s1_before.acceptance_criteria
    # Only pm_id/pm_url changed.
    assert s1_after.pm_id == "86s1"

    # Running it again is a no-op on the data (idempotent).
    result2 = pm_backfill_ids_impl(
        plan_json_path=str(plan_path),
        epics=[{"id": "EPIC-1", "pm_id": "86epic1", "pm_url": "u1"}],
        stories=[{"id": "EPIC-1-S1", "pm_id": "86s1", "pm_url": "us1"}],
    )
    again = load_plan(plan_path)
    s1_again = next(s for e in again.epics for s in e.stories if s.id == "EPIC-1-S1")
    assert s1_again.pm_id == "86s1"
    assert s1_again.name == name_before
    assert result2["not_found"] == []


def test_backfill_partial_only_epics_or_only_stories(plan_path):
    # Only epics.
    result_e = pm_backfill_ids_impl(
        plan_json_path=str(plan_path),
        epics=[{"id": "EPIC-2", "pm_id": "86epic2", "pm_url": "u2"}],
    )
    assert result_e["updated_epics"] == ["EPIC-2"]
    assert result_e["updated_stories"] == []

    plan = load_plan(plan_path)
    epics = {e.id: e for e in plan.epics}
    assert epics["EPIC-2"].pm_id == "86epic2"

    # Only stories.
    result_s = pm_backfill_ids_impl(
        plan_json_path=str(plan_path),
        stories=[{"id": "EPIC-2-S1", "pm_id": "86s3", "pm_url": "u3"}],
    )
    assert result_s["updated_stories"] == ["EPIC-2-S1"]
    assert result_s["updated_epics"] == []

    plan2 = load_plan(plan_path)
    stories = {s.id: s for e in plan2.epics for s in e.stories}
    assert stories["EPIC-2-S1"].pm_id == "86s3"
