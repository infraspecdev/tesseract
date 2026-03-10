"""MCP tool: sprint_sync — diff plan documents against ClickUp state."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig
from server.parsers.base import Story, get_parser


FUZZY_THRESHOLD = 0.6


def _fuzzy_match(name: str, candidates: list[dict]) -> dict | None:
    """Find the best fuzzy match for a story name among ClickUp tasks."""
    best_match = None
    best_ratio = 0.0
    name_lower = name.lower().strip()
    for task in candidates:
        task_name = task.get("name", "")
        # Strip common prefixes like "[Project] P1a-S1: "
        clean_name = task_name
        if ": " in clean_name:
            clean_name = clean_name.split(": ", 1)[-1]
        ratio = SequenceMatcher(None, name_lower, clean_name.lower().strip()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = task
    return best_match if best_ratio >= FUZZY_THRESHOLD else None


def _determine_diff(story: Story, clickup_task: dict | None) -> str:
    """Determine the diff status between a plan story and its ClickUp match."""
    if clickup_task is None:
        return "to_create"
    task_name = clickup_task.get("name", "")
    clean_name = task_name
    if ": " in clean_name:
        clean_name = clean_name.split(": ", 1)[-1]
    ratio = SequenceMatcher(None, story.name.lower(), clean_name.lower()).ratio()
    if ratio >= 0.8:
        return "match"
    return "to_update"


def _filter_tasks_by_epic(tasks: list[dict], epic_id: str) -> list[dict]:
    """Filter tasks that belong to a specific epic by name prefix convention.

    Tasks follow the pattern: [Project] P1a-S1: ...
    We match on "{epic_id}-" to avoid P1 matching P1a tasks.
    """
    prefix = f"{epic_id}-"
    return [t for t in tasks if prefix in t.get("name", "")]


def register(mcp: FastMCP, client: ClickUpClient, config: SprintPlannerConfig, base_path: Path):
    @mcp.tool()
    async def sprint_sync(
        epic: str | None = None,
    ) -> dict:
        """Diff plan documents against ClickUp state. Read-only — makes no changes.

        Parses stories from plan docs and compares against tasks linked to each
        epic's EPIC in ClickUp. Reports which stories match, need creation,
        need updates, or are orphaned.

        Args:
            epic: Epic ID to sync (e.g. "P1a"). If omitted, syncs all epics.
        """
        epics_to_sync = config.plan_docs.epics
        if epic:
            epics_to_sync = [p for p in epics_to_sync if p.id == epic]
            if not epics_to_sync:
                available = [p.id for p in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        parser = get_parser(config.plan_docs.format)
        extraction_config = config.story_extraction.html.model_dump()

        # Fetch all backlog tasks including closed (needed to match done stories)
        try:
            all_clickup_tasks = await client.get_tasks_by_list(
                config.clickup.lists.backlog.id, include_closed=True
            )
        except ClickUpAPIError as e:
            return {"error": f"Failed to fetch ClickUp tasks: {e}"}

        results = []
        for epic_cfg in epics_to_sync:
            plan_doc_path = base_path / epic_cfg.plan_doc
            if not plan_doc_path.exists():
                results.append({
                    "epic": epic_cfg.id,
                    "name": epic_cfg.name,
                    "error": f"Plan doc not found: {plan_doc_path}",
                })
                continue

            # Parse stories from plan doc
            try:
                stories = parser.extract_stories(plan_doc_path, extraction_config)
            except Exception as e:
                results.append({
                    "epic": epic_cfg.id,
                    "name": epic_cfg.name,
                    "error": f"Failed to parse plan doc: {e}",
                })
                continue

            # Filter ClickUp tasks to this epic only
            clickup_tasks = _filter_tasks_by_epic(all_clickup_tasks, epic_cfg.id)

            # Match stories to ClickUp tasks
            matched_task_ids = set()
            story_results = []

            for story in stories:
                # 1. Try exact match by clickup_id
                if story.clickup_id:
                    task = next(
                        (t for t in all_clickup_tasks if t["id"] == story.clickup_id), None
                    )
                    if task:
                        matched_task_ids.add(task["id"])
                        diff = _determine_diff(story, task)
                        story_results.append({
                            "index": story.index,
                            "name": story.name,
                            "plan_status": story.status,
                            "clickup_id": story.clickup_id,
                            "clickup_status": task.get("status", {}).get("status"),
                            "diff": diff,
                        })
                        continue

                # 2. Try fuzzy name match against epic-scoped tasks
                unmatched = [t for t in clickup_tasks if t["id"] not in matched_task_ids]
                match = _fuzzy_match(story.name, unmatched)
                if match:
                    matched_task_ids.add(match["id"])
                    diff = _determine_diff(story, match)
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "clickup_id": match["id"],
                        "clickup_status": match.get("status", {}).get("status"),
                        "diff": diff,
                    })
                else:
                    # 3. No match — to_create
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "clickup_id": None,
                        "diff": "to_create",
                    })

            # Orphaned: ClickUp tasks for this epic with no matching plan story
            orphaned_count = sum(
                1 for t in clickup_tasks if t["id"] not in matched_task_ids
            )

            summary = {
                "match": sum(1 for s in story_results if s["diff"] == "match"),
                "to_create": sum(1 for s in story_results if s["diff"] == "to_create"),
                "to_update": sum(1 for s in story_results if s["diff"] == "to_update"),
                "to_link": 0,
                "orphaned": orphaned_count,
            }

            results.append({
                "epic": epic_cfg.id,
                "name": epic_cfg.name,
                "summary": summary,
                "stories": story_results,
            })

        if len(results) == 1:
            return results[0]
        return {"epics": results}
