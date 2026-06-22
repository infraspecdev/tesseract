"""MCP tool: pm_bulk_rename — preview or apply epic prefix renames on issue titles."""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.config import SprintPlannerConfig
from server.github_client import GitHubClient, GitHubAPIError


def register(
    mcp: FastMCP,
    client: GitHubClient,
    action_log: ActionLog,
    config: SprintPlannerConfig,
):
    @mcp.tool()
    async def pm_bulk_rename(
        epic: str | None = None,
        apply: bool = False,
        strip_prefix: str | None = None,
        story_format: str | None = None,
    ) -> dict:
        """Preview or apply epic prefix renames on non-compliant issue titles.

        Args:
            epic: Epic ID to scope (e.g. "E26"). Omit for all epics.
            apply: If true, rename the issues. If false (default), preview only.
            strip_prefix: Regex to strip from existing titles before reformatting.
            story_format: Format string for titles. Placeholders: {epic_id}, {name}.
        """
        default_fmt = story_format or config.naming.story_format
        epics_to_check = config.plan_docs.epics
        if epic:
            epics_to_check = [e for e in epics_to_check if e.id == epic]
            if not epics_to_check:
                available = [e.id for e in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        strip_re = re.compile(strip_prefix) if strip_prefix else None
        renames = []

        for epic_cfg in epics_to_check:
            try:
                sub_issues = await client.get_sub_issues(epic_cfg.epic_issue_number)
            except GitHubAPIError as e:
                return {"error": f"Failed to fetch sub-issues for epic #{epic_cfg.epic_issue_number}: {e}"}

            for issue in sub_issues:
                current_title = issue.get("title", "")
                clean_title = strip_re.sub("", current_title).strip() if strip_re else current_title
                new_title = default_fmt.format(epic_id=epic_cfg.id, name=clean_title)
                if current_title != new_title:
                    renames.append({
                        "issue_number": issue["number"],
                        "epic": epic_cfg.id,
                        "current_title": current_title,
                        "new_title": new_title,
                        "url": issue.get("html_url", ""),
                    })

        if not renames:
            return {"message": "All issue titles are compliant.", "renames": []}

        if not apply:
            return {
                "message": f"Found {len(renames)} issues to rename. Set apply=True to execute.",
                "mode": "preview",
                "renames": renames,
            }

        renamed = []
        failed = []
        for r in renames:
            try:
                await client.update_issue(r["issue_number"], {"title": r["new_title"]})
                renamed.append({**r, "status": "success"})
            except GitHubAPIError as e:
                failed.append({**r, "status": "failed", "error": str(e)})

        log_warning = None
        try:
            action_log.log_action(
                action="bulk_rename",
                status="success" if not failed else "partial",
                summary=f"Renamed {len(renamed)}/{len(renames)} issue titles",
                results=renamed + failed,
                undo={
                    "type": "bulk_rename",
                    "rollback": [
                        {"issue_number": r["issue_number"], "title": r["current_title"]}
                        for r in renamed
                    ],
                },
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        result = {
            "message": f"Renamed {len(renamed)}/{len(renames)} issues.",
            "mode": "applied",
            "renamed": renamed,
            "failed": failed,
        }
        if log_warning:
            result["log_warning"] = log_warning
        return result
