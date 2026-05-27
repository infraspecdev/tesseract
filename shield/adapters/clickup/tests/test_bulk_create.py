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

from server.tools.bulk_create import pm_bulk_create_impl


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
