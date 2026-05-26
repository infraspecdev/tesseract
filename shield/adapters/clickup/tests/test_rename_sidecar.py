"""Tests for the sidecar-driven pm_bulk_rename MCP tool."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.tools.rename import pm_bulk_rename_impl


FIXTURE = Path(__file__).parent / "fixtures" / "plan-v14-2epics-3stories.json"


@pytest.fixture
def mock_client() -> MagicMock:
    """Mock ClickUpClient — returns empty lists by default."""
    client = MagicMock()
    client.get_tasks_by_list = AsyncMock(return_value=[])
    client.update_task = AsyncMock(return_value={})
    return client


@pytest.fixture
def mock_action_log() -> MagicMock:
    log = MagicMock()
    log.log_action = MagicMock(return_value=None)
    return log


@pytest.fixture
def mock_config() -> MagicMock:
    cfg = MagicMock()
    cfg.clickup.lists.backlog.id = "BACKLOG-LIST"
    cfg.clickup.lists.epics.id = "EPICS-LIST"
    cfg.clickup.relationship_field.id = "REL-FIELD-UUID"
    cfg.naming.story_format = "{epic_id}: {name}"
    cfg.naming.epic_format = "{epic_id}: {epic_name}"
    return cfg


def _plan_with_pm_ids(tmp_path: Path, pm_ids: dict[int, str | None]) -> Path:
    """Load the fixture and set epics[i]["pm_id"] = value, write to tmp_path."""
    plan_data = json.loads(FIXTURE.read_text())
    for idx, value in pm_ids.items():
        plan_data["epics"][idx]["pm_id"] = value
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan_data))
    return p


@pytest.mark.asyncio
async def test_rename_previews_noncompliant_story_names(
    mock_client: MagicMock,
    mock_config: MagicMock,
    mock_action_log: MagicMock,
    tmp_path: Path,
) -> None:
    """A backlog task linked to a synced epic with a non-compliant name yields
    a rename proposal in preview mode."""
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})

    backlog_tasks = [
        {
            "id": "STORY-PM-1",
            "name": "Story one",
            "custom_fields": [
                {"id": "REL-FIELD-UUID", "value": [{"id": "EPIC-PM-1"}]}
            ],
        }
    ]
    epic_tasks = []  # no epic card present
    # rename.py fetches backlog first, then epics.
    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=[backlog_tasks, epic_tasks]
    )

    result = await pm_bulk_rename_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        action_log=mock_action_log,
        apply=False,
    )

    assert result["mode"] == "preview"
    story_renames = [r for r in result["renames"] if r["type"] == "story"]
    assert len(story_renames) == 1
    assert story_renames[0]["task_id"] == "STORY-PM-1"
    assert story_renames[0]["current_name"] == "Story one"
    assert story_renames[0]["new_name"] == "EPIC-1: Story one"


@pytest.mark.asyncio
async def test_rename_skips_unsynced_epic_with_null_pm_id(
    mock_client: MagicMock,
    mock_config: MagicMock,
    mock_action_log: MagicMock,
    tmp_path: Path,
) -> None:
    """A plan epic with pm_id=None is skipped — no error, no renames."""
    # Epic 0 has pm_id=None (fixture default), epic 1 too.
    p = _plan_with_pm_ids(tmp_path, {0: None, 1: None})

    # A backlog task linked to "EPIC-PM-1" exists, but no plan epic has that pm_id.
    backlog_tasks = [
        {
            "id": "STORY-PM-1",
            "name": "Story one",
            "custom_fields": [
                {"id": "REL-FIELD-UUID", "value": [{"id": "EPIC-PM-1"}]}
            ],
        }
    ]
    mock_client.get_tasks_by_list = AsyncMock(side_effect=[backlog_tasks, []])

    result = await pm_bulk_rename_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        action_log=mock_action_log,
        apply=False,
    )

    assert "error" not in result
    assert result["renames"] == []
    assert result["message"] == "All task names are compliant."


@pytest.mark.asyncio
async def test_rename_unknown_epic_returns_error(
    mock_client: MagicMock,
    mock_config: MagicMock,
    mock_action_log: MagicMock,
    tmp_path: Path,
) -> None:
    """Passing an epic id not in the plan returns an error listing available ids."""
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})

    result = await pm_bulk_rename_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        action_log=mock_action_log,
        epic="EPIC-99",
    )

    assert "error" in result
    assert "EPIC-99" in result["error"]
    assert "EPIC-1" in result["error"]
    assert "EPIC-2" in result["error"]
