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
