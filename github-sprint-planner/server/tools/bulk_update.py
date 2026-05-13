"""MCP tool: sprint_bulk_update — batch issue updates."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.github_client import GitHubClient, GitHubAPIError


def register(mcp: FastMCP, client: GitHubClient, action_log: ActionLog):
    @mcp.tool()
    async def sprint_bulk_update(
        updates: list[dict],
    ) -> dict:
        """Batch update assignees, labels, or state across multiple GitHub issues.

        Each update dict should have:
          - issue_number (required): The issue to update
          - assignees: List of GitHub logins to assign
          - labels: List of label names to set
          - state: "open" or "closed"
          - title: New issue title
          - body: New issue body (markdown)

        Args:
            updates: Array of update objects with issue_number and fields to change.
        """
        updated = []
        failed = []

        for update in updates:
            issue_number = update.get("issue_number")
            if not issue_number:
                failed.append({"error": "Missing issue_number", "update": update})
                continue

            payload: dict = {}
            changes = []

            if "assignees" in update:
                payload["assignees"] = update["assignees"]
                changes.append("assignees")
            if "labels" in update:
                payload["labels"] = update["labels"]
                changes.append("labels")
            if "state" in update:
                payload["state"] = update["state"]
                changes.append("state")
            if "title" in update:
                payload["title"] = update["title"]
                changes.append("title")
            if "body" in update:
                payload["body"] = update["body"]
                changes.append("body")

            if not payload:
                failed.append({"issue_number": issue_number, "error": "No fields to update"})
                continue

            try:
                await client.update_issue(issue_number, payload)
                updated.append({
                    "issue_number": issue_number,
                    "status": "success",
                    "changes": changes,
                })
            except GitHubAPIError as e:
                failed.append({
                    "issue_number": issue_number,
                    "status": "failed",
                    "error": str(e),
                })

        log_warning = None
        try:
            action_log.log_action(
                action="bulk_update",
                status="success" if not failed else "partial",
                summary=f"Updated {len(updated)}/{len(updates)} issues",
                results=updated + failed,
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        result = {"updated": updated, "failed": failed}
        if log_warning:
            result["log_warning"] = log_warning
        return result
