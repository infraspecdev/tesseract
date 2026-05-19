"""MCP tool: pm_link_story_to_epic — link issues as sub-issues of an epic."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.github_client import GitHubClient, GitHubAPIError


def register(mcp: FastMCP, client: GitHubClient, action_log: ActionLog):
    @mcp.tool()
    async def pm_link_story_to_epic(
        epic_issue_number: int,
        issue_numbers: list[int],
    ) -> dict:
        """Link GitHub issues as sub-issues of an epic.

        Args:
            epic_issue_number: The parent epic issue number.
            issue_numbers: Issue numbers to link as sub-issues.
        """
        results = []
        for issue_number in issue_numbers:
            try:
                await client.add_sub_issue(epic_issue_number, issue_number)
                results.append({
                    "issue_number": issue_number,
                    "epic_issue_number": epic_issue_number,
                    "status": "success",
                })
            except GitHubAPIError as e:
                results.append({
                    "issue_number": issue_number,
                    "epic_issue_number": epic_issue_number,
                    "status": "failed",
                    "error": str(e),
                })

        success_count = sum(1 for r in results if r["status"] == "success")
        log_warning = None
        try:
            action_log.log_action(
                action="link_story_to_epic",
                status="success" if success_count == len(results) else "partial",
                summary=f"Linked {success_count}/{len(results)} issues to epic #{epic_issue_number}",
                results=results,
                undo={
                    "type": "unlink_sub_issues",
                    "epic_issue_number": epic_issue_number,
                    "issue_numbers": [r["issue_number"] for r in results if r["status"] == "success"],
                },
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        response: dict = {"results": results}
        if log_warning:
            response["log_warning"] = log_warning
        return response
