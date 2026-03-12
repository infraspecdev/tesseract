"""MCP tool: sprint_status — sprint/epic overview with story states."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig
from server.tools._helpers import _get_linked_epic_ids


def _normalize_status(status_str: str) -> str:
    """Normalize ClickUp status strings to summary categories."""
    s = status_str.lower().strip()
    if s in ("done", "complete", "closed"):
        return "done"
    if s in ("in progress", "in review", "in dev"):
        return "in_progress"
    if s in ("blocked",):
        return "blocked"
    return "ready"


def register(mcp: FastMCP, client: ClickUpClient, config: SprintPlannerConfig):
    @mcp.tool()
    async def sprint_status(
        epic: str | None = None,
        group_by: str = "epic",
    ) -> dict:
        """Get sprint/epic overview with story states from ClickUp.

        Fetches tasks from the backlog list and aggregates stats per epic.

        Args:
            epic: Epic ID to filter (e.g. "P1a"). Omit for all epics.
            group_by: Grouping: "epic" (default), "status", or "assignee".
        """
        epics_to_check = config.plan_docs.epics
        if epic:
            epics_to_check = [p for p in epics_to_check if p.id == epic]
            if not epics_to_check:
                available = [p.id for p in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        # Fetch all backlog tasks
        try:
            all_tasks = await client.get_tasks_by_list(
                config.clickup.lists.backlog.id, include_closed=True
            )
        except ClickUpAPIError as e:
            return {"error": f"Failed to fetch tasks: {e}"}

        # Build team lookup
        team_by_id = {m.id: m.name for m in config.team}

        relationship_field_id = config.clickup.relationship_field.id

        if group_by == "epic":
            return _group_by_epic(epics_to_check, all_tasks, team_by_id, relationship_field_id)
        elif group_by == "status":
            return _group_by_status(all_tasks, team_by_id)
        elif group_by == "assignee":
            return _group_by_assignee(all_tasks, team_by_id)
        else:
            return {"error": f"Invalid group_by: {group_by!r}. Use 'epic', 'status', or 'assignee'."}


def _extract_stories(tasks: list[dict], team_by_id: dict) -> list[dict]:
    """Convert ClickUp tasks to story summary dicts."""
    stories = []
    for task in tasks:
        assignees = task.get("assignees", [])
        assignee_name = None
        if assignees:
            assignee_id = str(assignees[0].get("id", ""))
            assignee_name = team_by_id.get(assignee_id, assignees[0].get("username", assignee_id))
        stories.append({
            "task_id": task["id"],
            "name": task.get("name", ""),
            "status": task.get("status", {}).get("status", "unknown"),
            "assignee": assignee_name,
            "url": task.get("url", f"https://app.clickup.com/t/{task['id']}"),
        })
    return stories


def _compute_stats(tasks: list[dict]) -> dict:
    """Compute status statistics for a list of tasks."""
    stats = {"total": len(tasks), "done": 0, "in_progress": 0, "ready": 0, "blocked": 0}
    for task in tasks:
        status = task.get("status", {}).get("status", "")
        category = _normalize_status(status)
        if category in stats:
            stats[category] += 1
    return stats


def _group_by_epic(epics: list, all_tasks: list[dict], team_by_id: dict, relationship_field_id: str) -> dict:
    """Group tasks by epic — uses relationship custom field to match tasks to epics."""
    result_epics = []
    for epic_cfg in epics:
        epic_tasks = [
            t for t in all_tasks
            if epic_cfg.epic_id in _get_linked_epic_ids(t, relationship_field_id)
        ]
        result_epics.append({
            "id": epic_cfg.id,
            "name": epic_cfg.name,
            "epic_id": epic_cfg.epic_id,
            "stats": _compute_stats(epic_tasks),
            "stories": _extract_stories(epic_tasks, team_by_id),
        })
    return {"epics": result_epics}


def _group_by_status(all_tasks: list[dict], team_by_id: dict) -> dict:
    """Group all tasks by status category."""
    groups: dict[str, list[dict]] = {"done": [], "in_progress": [], "ready": [], "blocked": []}
    for task in all_tasks:
        status = task.get("status", {}).get("status", "")
        category = _normalize_status(status)
        if category in groups:
            groups[category].append(task)
    return {
        "groups": {
            k: {"count": len(v), "stories": _extract_stories(v, team_by_id)}
            for k, v in groups.items()
        }
    }


def _group_by_assignee(all_tasks: list[dict], team_by_id: dict) -> dict:
    """Group all tasks by assignee."""
    groups: dict[str, list[dict]] = {}
    for task in all_tasks:
        assignees = task.get("assignees", [])
        if assignees:
            for assignee in assignees:
                name = team_by_id.get(str(assignee.get("id", "")), assignee.get("username", "Unknown"))
                groups.setdefault(name, []).append(task)
        else:
            groups.setdefault("Unassigned", []).append(task)
    return {
        "groups": {
            k: {"count": len(v), "stats": _compute_stats(v), "stories": _extract_stories(v, team_by_id)}
            for k, v in groups.items()
        }
    }
