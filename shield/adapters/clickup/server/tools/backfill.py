"""MCP tool: pm_backfill_ids — write ClickUp task ids/urls back into plan.json."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from shield_parsers.sidecar import CURRENT_SCHEMA_VERSION, load_plan, save_plan


def pm_backfill_ids_impl(
    plan_json_path: str,
    epics: list[dict] | None = None,
    stories: list[dict] | None = None,
) -> dict[str, Any]:
    """Write ClickUp task ids/urls back into a plan.json sidecar.

    Pure filesystem write — no ClickUp client. Takes an EXPLICIT mapping of
    plan epic/story ids to their newly-created ClickUp pm_id/pm_url (built by
    the caller from pm_bulk_create `created[]` results); it does NOT re-correlate
    by name. Mutates matching epics/stories in place and saves atomically,
    stamping the current schema version so the next sync sees the tasks as `match`.

    Args:
        plan_json_path: Path to the plan.json sidecar to write into.
        epics: List of {id, pm_id, pm_url} mappings for plan epics.
        stories: List of {id, pm_id, pm_url} mappings for plan stories.

    Returns:
        {"updated_epics": [...], "updated_stories": [...],
         "not_found": [{"id": ..., "type": "epic"|"story"}, ...],
         "version": CURRENT_SCHEMA_VERSION}
    """
    plan = load_plan(plan_json_path)

    epic_map = {e["id"]: e for e in (epics or [])}
    story_map = {s["id"]: s for s in (stories or [])}

    updated_epics: list[str] = []
    updated_stories: list[str] = []
    consumed_epics: set[str] = set()
    consumed_stories: set[str] = set()

    for epic in plan.epics:
        if epic.id in epic_map:
            entry = epic_map[epic.id]
            epic.pm_id = entry.get("pm_id")
            epic.pm_url = entry.get("pm_url")
            updated_epics.append(epic.id)
            consumed_epics.add(epic.id)
        for story in epic.stories:
            if story.id in story_map:
                entry = story_map[story.id]
                story.pm_id = entry.get("pm_id")
                story.pm_url = entry.get("pm_url")
                updated_stories.append(story.id)
                consumed_stories.add(story.id)

    not_found: list[dict[str, str]] = []
    for eid in epic_map:
        if eid not in consumed_epics:
            not_found.append({"id": eid, "type": "epic"})
    for sid in story_map:
        if sid not in consumed_stories:
            not_found.append({"id": sid, "type": "story"})

    save_plan(plan_json_path, plan)

    return {
        "updated_epics": updated_epics,
        "updated_stories": updated_stories,
        "not_found": not_found,
        "version": CURRENT_SCHEMA_VERSION,
    }


def register(mcp: FastMCP):
    @mcp.tool()
    async def pm_backfill_ids(
        plan_json_path: str,
        epics: list[dict] | None = None,
        stories: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Write created ClickUp task ids/urls back into plan.json.

        Call this AFTER pm_bulk_create. Pass each plan epic/story id paired with
        the ClickUp task_id (as pm_id) and task_url (as pm_url) obtained from the
        bulk_create `created[]` results. It writes them into plan.json — atomic,
        stamping the current schema version — so the next pm_sync_sidecar sees those
        epics/stories as `match` and the sync becomes idempotent.

        This is a pure write: it does NOT re-correlate by name. Ids in the input
        that match no plan epic/story are surfaced in `not_found` rather than
        silently dropped.

        Args:
            plan_json_path: Path to the plan.json sidecar to write into.
            epics: List of {id, pm_id, pm_url} mappings for plan epics.
            stories: List of {id, pm_id, pm_url} mappings for plan stories.
        """
        return pm_backfill_ids_impl(
            plan_json_path=plan_json_path,
            epics=epics,
            stories=stories,
        )
