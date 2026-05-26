"""Tests for the sidecar-driven pm_get_status MCP tool."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.clickup_client import ClickUpAPIError
from server.tools.status import pm_get_status_impl


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
    cfg.clickup.relationship_field.id = "REL-FIELD-UUID"
    # config.team is iterated as {m.id: m.name for m in config.team} — must be a real list.
    cfg.team = []
    return cfg


def _plan_with_pm_ids(tmp_path: Path, pm_ids: dict[int, str | None]) -> Path:
    """Load the fixture and set epics[i]["pm_id"] = value, write to tmp_path."""
    plan_data = json.loads(FIXTURE.read_text())
    for idx, value in pm_ids.items():
        plan_data["epics"][idx]["pm_id"] = value
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan_data))
    return p


def _linked_task(task_id: str, status: str, epic_pm_id: str) -> dict:
    return {
        "id": task_id,
        "name": f"Story {task_id}",
        "status": {"status": status},
        "assignees": [],
        "custom_fields": [
            {"id": "REL-FIELD-UUID", "value": [{"id": epic_pm_id}]}
        ],
    }


@pytest.mark.asyncio
async def test_status_group_by_epic_aggregates_linked_tasks(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """Epic group aggregates tasks linked via the relationship field."""
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})

    backlog_tasks = [
        _linked_task("T1", "done", "EPIC-PM-1"),
        _linked_task("T2", "ready", "EPIC-PM-1"),
    ]
    mock_client.get_tasks_by_list = AsyncMock(return_value=backlog_tasks)

    result = await pm_get_status_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        epic="EPIC-1",
        group_by="epic",
    )

    assert "error" not in result
    epic_group = next(e for e in result["epics"] if e["id"] == "EPIC-1")
    assert epic_group["epic_id"] == "EPIC-PM-1"
    assert epic_group["stats"]["total"] == 2
    assert epic_group["stats"]["done"] == 1
    assert epic_group["stats"]["ready"] == 1
    assert len(epic_group["stories"]) == 2
    # Only backlog list is fetched.
    mock_client.get_tasks_by_list.assert_awaited_once_with(
        "BACKLOG-LIST", include_closed=True
    )


@pytest.mark.asyncio
async def test_status_unsynced_epic_shows_zero_stories(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """A plan epic with pm_id=None stays in the output with zero stories."""
    p = _plan_with_pm_ids(tmp_path, {0: None, 1: None})

    # A backlog task exists but is linked to an epic no plan epic claims.
    mock_client.get_tasks_by_list = AsyncMock(
        return_value=[_linked_task("T1", "done", "EPIC-PM-XYZ")]
    )

    result = await pm_get_status_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        group_by="epic",
    )

    assert "error" not in result
    ids = [e["id"] for e in result["epics"]]
    assert "EPIC-1" in ids
    assert "EPIC-2" in ids
    for e in result["epics"]:
        assert e["epic_id"] is None
        assert e["stats"]["total"] == 0
        assert e["stories"] == []


@pytest.mark.asyncio
async def test_status_unknown_epic_returns_error(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """An epic id not in the plan returns an error listing available ids."""
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})

    result = await pm_get_status_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        epic="EPIC-99",
    )

    assert "error" in result
    assert "EPIC-99" in result["error"]
    assert "EPIC-1" in result["error"]
    assert "EPIC-2" in result["error"]


@pytest.mark.asyncio
async def test_status_group_by_status_ignores_epic_list(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """group_by='status' returns status groups regardless of the epic list."""
    p = _plan_with_pm_ids(tmp_path, {0: None, 1: None})

    mock_client.get_tasks_by_list = AsyncMock(
        return_value=[
            _linked_task("T1", "done", "EPIC-PM-1"),
            _linked_task("T2", "ready", "EPIC-PM-1"),
        ]
    )

    result = await pm_get_status_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        group_by="status",
    )

    assert "groups" in result
    assert result["groups"]["done"]["count"] == 1
    assert result["groups"]["ready"]["count"] == 1


@pytest.mark.asyncio
async def test_status_fetch_error_returns_error(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """A ClickUpAPIError fetching tasks surfaces as a result error."""
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})
    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=ClickUpAPIError(500, "INTERNAL", "status boom")
    )

    result = await pm_get_status_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
    )

    assert "error" in result
    assert result["error"].startswith("Failed to fetch tasks")


@pytest.mark.asyncio
async def test_status_invalid_group_by_returns_error(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """An unrecognized group_by value returns an error listing valid options."""
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})
    mock_client.get_tasks_by_list = AsyncMock(return_value=[])

    result = await pm_get_status_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        group_by="nonsense",
    )

    assert "error" in result
    assert "nonsense" in result["error"]
    assert "epic" in result["error"]
    assert "status" in result["error"]
    assert "assignee" in result["error"]


@pytest.mark.asyncio
async def test_status_group_by_assignee_resolves_team_names(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """group_by='assignee' groups tasks by assignee, resolving team-member ids
    to names and falling back to username for unknown ids."""
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})

    # config.team maps id "100" -> "Alice"; id "999" is not on the team.
    member = SimpleNamespace(id="100", name="Alice")
    mock_config.team = [member]

    tasks = [
        {
            "id": "T1",
            "name": "Story T1",
            "status": {"status": "done"},
            "assignees": [{"id": 100, "username": "alice_cu"}],
            "custom_fields": [],
        },
        {
            "id": "T2",
            "name": "Story T2",
            "status": {"status": "ready"},
            "assignees": [{"id": 999, "username": "bob_cu"}],
            "custom_fields": [],
        },
        {
            "id": "T3",
            "name": "Story T3",
            "status": {"status": "ready"},
            "assignees": [],
            "custom_fields": [],
        },
    ]
    mock_client.get_tasks_by_list = AsyncMock(return_value=tasks)

    result = await pm_get_status_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        group_by="assignee",
    )

    groups = result["groups"]
    # Known team id resolves to the configured name.
    assert "Alice" in groups
    assert groups["Alice"]["count"] == 1
    # Unknown id falls back to the ClickUp username.
    assert "bob_cu" in groups
    assert groups["bob_cu"]["count"] == 1
    # No assignees -> Unassigned bucket.
    assert "Unassigned" in groups
    assert groups["Unassigned"]["count"] == 1
    # _extract_stories resolved Alice's assignee name on the story summary.
    alice_story = groups["Alice"]["stories"][0]
    assert alice_story["assignee"] == "Alice"
