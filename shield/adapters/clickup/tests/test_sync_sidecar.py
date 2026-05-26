"""Tests for the sidecar-driven pm_sync_sidecar MCP tool."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.clickup_client import ClickUpAPIError
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


@pytest.mark.asyncio
async def test_sync_story_exact_id_match_with_drifted_name_is_to_update(
    mock_client: MagicMock, mock_config: MagicMock, tmp_path: Path
) -> None:
    """A story with pm_id matching a ClickUp task by exact id, but whose name
    has drifted well below FUZZY_MATCH_THRESHOLD, classifies as to_update."""
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
            # epics list — exact id match, name drifted -> epic to_update too
            [{"id": "EPIC-PM-1", "name": "Completely different epic title",
              "status": {"status": "open"}}],
            # backlog list — exact story id match, name drifted far from "Story one"
            [{"id": "STORY-PM-1",
              "name": "Totally unrelated wording here zzz",
              "status": {"status": "open"}, "custom_fields": []}],
        ]
    )

    result = await pm_sync_sidecar_impl(
        plan_json_path=p, client=mock_client, config=mock_config
    )

    story = next(s for s in result["stories"] if s["id"] == "EPIC-1-S1")
    assert story["diff"] == "to_update"
    assert story["pm_id"] == "STORY-PM-1"

    epic = next(e for e in result["epics"] if e["id"] == "EPIC-1")
    assert epic["diff"] == "to_update"
    assert epic["pm_id"] == "EPIC-PM-1"


@pytest.mark.asyncio
async def test_sync_epic_unknown_scope_returns_error(
    mock_client: MagicMock, mock_config: MagicMock
) -> None:
    """Scoping to an epic id not present in the plan returns an error listing
    the available epic ids (early return before any ClickUp fetch)."""
    result = await pm_sync_sidecar_impl(
        plan_json_path=FIXTURE,
        client=mock_client,
        config=mock_config,
        epic="EPIC-99",
    )

    assert "error" in result
    assert "EPIC-99" in result["error"]
    assert "EPIC-1" in result["error"]
    assert "EPIC-2" in result["error"]


@pytest.mark.asyncio
async def test_sync_clickup_fetch_error_returns_error(
    mock_client: MagicMock, mock_config: MagicMock
) -> None:
    """A ClickUpAPIError while fetching tasks surfaces as a result error."""
    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=ClickUpAPIError(500, "INTERNAL", "boom")
    )

    result = await pm_sync_sidecar_impl(
        plan_json_path=FIXTURE, client=mock_client, config=mock_config
    )

    assert "error" in result
    assert result["error"].startswith("Failed to fetch ClickUp tasks")


@pytest.mark.asyncio
async def test_sync_epic_to_link_for_fuzzy_match_on_epic_card(
    mock_client: MagicMock, mock_config: MagicMock
) -> None:
    """A plan epic (pm_id=None) whose name fuzzy-matches an existing ClickUp
    epic card between the link and match thresholds is flagged to_link."""
    mock_client.get_tasks_by_list = AsyncMock(
        side_effect=[
            # epics list — a card whose name is a near-but-not-exact match of
            # "First epic" (ratio between 0.6 and 0.8).
            [{"id": "EPIC-CARD-X", "name": "First epico draft",
              "status": {"status": "open"}}],
            # backlog list — empty
            [],
        ]
    )

    result = await pm_sync_sidecar_impl(
        plan_json_path=FIXTURE, client=mock_client, config=mock_config
    )

    to_link = [e for e in result["epics"] if e["diff"] == "to_link"]
    assert len(to_link) == 1
    assert to_link[0]["id"] == "EPIC-1"
    assert to_link[0]["candidate"]["clickup_id"] == "EPIC-CARD-X"
