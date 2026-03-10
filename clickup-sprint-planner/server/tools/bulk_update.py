"""MCP tool: sprint_bulk_update — batch task updates."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError


def register(mcp: FastMCP, client: ClickUpClient, action_log: ActionLog):
    @mcp.tool()
    async def sprint_bulk_update(
        updates: list[dict],
    ) -> dict:
        """Batch update status, assignee, or priority across multiple tasks.

        Each update dict should have:
          - task_id (required): The task to update
          - status: New status string
          - assignee: User ID to assign
          - priority: "urgent", "high", "normal", "low", or null to clear
          - description: New markdown description
          - orderindex: Position in the list (string, e.g. "1000")

        Args:
            updates: Array of update objects with task_id and fields to change.
        """
        priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}

        updated = []
        failed = []

        for update in updates:
            task_id = update.get("task_id")
            if not task_id:
                failed.append({"error": "Missing task_id", "update": update})
                continue

            task_data: dict = {}
            changes = []

            if "status" in update:
                task_data["status"] = update["status"]
                changes.append("status")
            if "assignee" in update:
                task_data["assignees"] = {"add": [int(update["assignee"])]}
                changes.append("assignee")
            if "priority" in update:
                p = update["priority"]
                task_data["priority"] = priority_map.get(p) if p else None
                changes.append("priority")
            if "description" in update:
                task_data["description"] = update["description"]
                changes.append("description")
            if "orderindex" in update:
                task_data["orderindex"] = str(update["orderindex"])
                changes.append("orderindex")

            if not task_data:
                failed.append({"task_id": task_id, "error": "No fields to update"})
                continue

            try:
                await client.update_task(task_id, task_data)
                updated.append({
                    "task_id": task_id,
                    "status": "success",
                    "changes": changes,
                })
            except ClickUpAPIError as e:
                failed.append({
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(e),
                })

        # Log grouped action
        log_warning = None
        try:
            action_log.log_action(
                action="bulk_update",
                status="success" if not failed else "partial",
                summary=f"Updated {len(updated)}/{len(updates)} tasks",
                results=updated + failed,
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        result = {"updated": updated, "failed": failed}
        if log_warning:
            result["log_warning"] = log_warning
        return result
