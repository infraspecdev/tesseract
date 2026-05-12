"""MCP tool: sprint_status — sprint/epic overview via GitHub sub-issues."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.config import SprintPlannerConfig
from server.github_client import GitHubClient, GitHubAPIError
from server.tools._helpers import normalize_status


def _extract_labels(issue: dict) -> list[str]:
    return [lbl.get("name", "") for lbl in issue.get("labels", [])]


def _story_row(issue: dict, team_by_login: dict) -> dict:
    assignees = issue.get("assignees", [])
    assignee_login = assignees[0].get("login") if assignees else None
    assignee_name = team_by_login.get(assignee_login, assignee_login) if assignee_login else None
    labels = _extract_labels(issue)
    return {
        "issue_number": issue["number"],
        "name": issue.get("title", ""),
        "status": normalize_status(issue.get("state", "open"), labels),
        "assignee": assignee_name,
        "url": issue.get("html_url", f"https://github.com/issues/{issue['number']}"),
    }


def _compute_stats(stories: list[dict]) -> dict:
    stats = {"total": len(stories), "done": 0, "in_progress": 0, "ready": 0, "blocked": 0}
    for s in stories:
        cat = s.get("status", "ready")
        if cat in stats:
            stats[cat] += 1
    return stats


def register(mcp: FastMCP, client: GitHubClient, config: SprintPlannerConfig):
    @mcp.tool()
    async def sprint_status(
        epic: str | None = None,
        group_by: str = "epic",
    ) -> dict:
        """Get sprint/epic overview with story states from GitHub Issues.

        Fetches sub-issues of each epic issue and aggregates stats.

        Args:
            epic: Epic ID to filter (e.g. "P1a"). Omit for all epics.
            group_by: Grouping: "epic" (default), "status", or "assignee".
        """
        epics_to_check = config.plan_docs.epics
        if epic:
            epics_to_check = [e for e in epics_to_check if e.id == epic]
            if not epics_to_check:
                available = [e.id for e in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        team_by_login = {m.github_login: m.name for m in config.team}

        if group_by == "epic":
            result_epics = []
            for epic_cfg in epics_to_check:
                try:
                    issues = await client.get_sub_issues(epic_cfg.epic_issue_number)
                except GitHubAPIError as e:
                    result_epics.append({
                        "id": epic_cfg.id,
                        "name": epic_cfg.name,
                        "error": str(e),
                    })
                    continue
                stories = [_story_row(i, team_by_login) for i in issues]
                result_epics.append({
                    "id": epic_cfg.id,
                    "name": epic_cfg.name,
                    "epic_issue_number": epic_cfg.epic_issue_number,
                    "stats": _compute_stats(stories),
                    "stories": stories,
                })
            return {"epics": result_epics}

        all_stories: list[dict] = []
        for epic_cfg in epics_to_check:
            try:
                issues = await client.get_sub_issues(epic_cfg.epic_issue_number)
                all_stories.extend(_story_row(i, team_by_login) for i in issues)
            except GitHubAPIError:
                continue

        if group_by == "status":
            groups: dict[str, list] = {"done": [], "in_progress": [], "ready": [], "blocked": []}
            for s in all_stories:
                cat = s.get("status", "ready")
                groups.setdefault(cat, []).append(s)
            return {"groups": {k: {"count": len(v), "stories": v} for k, v in groups.items()}}

        if group_by == "assignee":
            groups = {}
            for s in all_stories:
                key = s.get("assignee") or "Unassigned"
                groups.setdefault(key, []).append(s)
            return {
                "groups": {
                    k: {"count": len(v), "stats": _compute_stats(v), "stories": v}
                    for k, v in groups.items()
                }
            }

        return {"error": f"Invalid group_by: {group_by!r}. Use 'epic', 'status', or 'assignee'."}
