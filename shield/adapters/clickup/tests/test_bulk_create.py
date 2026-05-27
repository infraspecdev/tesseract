"""Tests for pm_bulk_create milestone tagging + the milestone_tag helper."""

from __future__ import annotations

from server.tools._helpers import MILESTONE_TAG_PREFIX, milestone_tag


def test_milestone_tag_lowercases() -> None:
    assert milestone_tag("M2") == "shield:ms:m2"


def test_milestone_tag_uses_prefix() -> None:
    assert milestone_tag("M1").startswith(MILESTONE_TAG_PREFIX)
    assert milestone_tag("M1") == "shield:ms:m1"


from unittest.mock import AsyncMock, MagicMock

import pytest

from server.clickup_client import ClickUpAPIError
from server.tools.bulk_create import pm_bulk_create_impl

_FULL_DESC = "Summary\nTasks\nContext\nAcceptance Criteria"


def _mocks() -> tuple[MagicMock, MagicMock, MagicMock]:
    client = MagicMock()
    client.create_task = AsyncMock(
        return_value={"id": "T1", "url": "https://app.clickup.com/t/T1"}
    )
    client.set_relationship_field = AsyncMock(return_value={})
    action_log = MagicMock()
    action_log.log_action = MagicMock(return_value=None)
    config = MagicMock()
    config.clickup.relationship_field.id = "REL-FIELD"
    return client, action_log, config


@pytest.mark.asyncio
async def test_bulk_create_sets_milestone_tag() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "Story one",
        "description": "Summary\nTasks\nContext\nAcceptance Criteria",
        "milestone_id": "M1",
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    assert client.create_task.await_count == 1
    _list_id, task_data = client.create_task.await_args.args
    assert task_data["tags"] == ["shield:ms:m1"]


@pytest.mark.asyncio
async def test_bulk_create_no_milestone_no_tag() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "Story without milestone",
        "description": "Summary\nTasks\nContext\nAcceptance Criteria",
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert "tags" not in task_data


@pytest.mark.asyncio
async def test_bulk_create_null_milestone_no_tag() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "Story with null milestone",
        "description": "Summary\nTasks\nContext\nAcceptance Criteria",
        "milestone_id": None,
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert "tags" not in task_data


@pytest.mark.asyncio
async def test_bulk_create_sets_relationship_when_requested() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "P1 - Story one",
        "description": _FULL_DESC,
        "epic_id": "EPIC-PM-1",
    }]

    result = await pm_bulk_create_impl(
        "BACKLOG", stories, True,
        client=client, action_log=action_log, config=config,
    )

    client.set_relationship_field.assert_awaited_once_with(
        "T1", "REL-FIELD", ["EPIC-PM-1"]
    )
    assert len(result["relationships"]) == 1
    assert result["relationships"][0]["status"] == "success"
    assert result["relationships"][0]["epic_id"] == "EPIC-PM-1"


@pytest.mark.asyncio
async def test_bulk_create_relationship_failure_recorded() -> None:
    client, action_log, config = _mocks()
    client.set_relationship_field = AsyncMock(
        side_effect=ClickUpAPIError(500, "ERR", "rel boom")
    )
    stories = [{
        "name": "P1 - Story one",
        "description": _FULL_DESC,
        "epic_id": "EPIC-PM-1",
    }]

    result = await pm_bulk_create_impl(
        "BACKLOG", stories, True,
        client=client, action_log=action_log, config=config,
    )

    # Task creation succeeded
    assert len(result["created"]) == 1
    assert result["created"][0]["task_id"] == "T1"
    # Relationship recorded as failed with error string
    assert len(result["relationships"]) == 1
    assert result["relationships"][0]["status"] == "failed"
    assert "rel boom" in result["relationships"][0]["error"]


@pytest.mark.asyncio
async def test_bulk_create_create_failure_goes_to_failed() -> None:
    client, action_log, config = _mocks()
    client.create_task = AsyncMock(
        side_effect=ClickUpAPIError(400, "BAD", "create boom")
    )
    stories = [{
        "name": "P1 - Story one",
        "description": _FULL_DESC,
        "epic_id": "EPIC-PM-1",
    }]

    result = await pm_bulk_create_impl(
        "BACKLOG", stories, True,
        client=client, action_log=action_log, config=config,
    )

    assert result["created"] == []
    assert len(result["failed"]) == 1
    assert result["failed"][0]["status"] == "failed"
    assert "create boom" in result["failed"][0]["error"]
    client.set_relationship_field.assert_not_awaited()


@pytest.mark.asyncio
async def test_bulk_create_format_warnings_for_missing_sections() -> None:
    client, action_log, config = _mocks()
    stories = [
        {"name": "P1 - Incomplete story", "description": "hi"},
        {"name": "P2 - No description"},  # missing description key -> all sections missing
    ]

    result = await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    assert "format_warnings" in result
    assert len(result["format_warnings"]) == 2
    for warning in result["format_warnings"]:
        assert set(warning["missing_sections"]) == {
            "Summary", "Tasks", "Context", "Acceptance Criteria"
        }


@pytest.mark.asyncio
async def test_bulk_create_passes_assignee_priority_orderindex() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "P1 - Story one",
        "description": _FULL_DESC,
        "assignee": "123",
        "priority": "high",
        "orderindex": "2000",
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert task_data["assignees"] == [123]
    assert task_data["priority"] == 2
    assert task_data["orderindex"] == "2000"


@pytest.mark.asyncio
async def test_bulk_create_auto_prefixes_name_with_epic_id() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "Install Istio",
        "epic_id": "P3",
        "description": _FULL_DESC,
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert task_data["name"] == "P3 - Install Istio"


@pytest.mark.asyncio
async def test_bulk_create_log_warning_when_action_log_raises() -> None:
    client, action_log, config = _mocks()
    action_log.log_action = MagicMock(side_effect=Exception("log down"))
    stories = [{
        "name": "P1 - Story one",
        "description": _FULL_DESC,
    }]

    result = await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    assert len(result["created"]) == 1
    assert "log_warning" in result
    assert "log down" in result["log_warning"]
