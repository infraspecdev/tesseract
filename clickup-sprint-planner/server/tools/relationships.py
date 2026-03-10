"""MCP tool: sprint_set_relationship — set list_relationship custom fields."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError


def register(mcp: FastMCP, client: ClickUpClient, action_log: ActionLog):
    @mcp.tool()
    async def sprint_set_relationship(
        task_id: str,
        field_id: str,
        linked_task_ids: list[str],
        action: str = "add",
    ) -> dict:
        """Set list_relationship custom fields using the direct REST API endpoint.

        This uses POST /task/{id}/field/{field_id} which actually works for
        relationship fields, unlike update_task which silently drops them.

        Args:
            task_id: The task to set the relationship on.
            field_id: The relationship field UUID.
            linked_task_ids: Task IDs to link/unlink.
            action: "add" to link, "remove" to unlink.
        """
        if action not in ("add", "remove"):
            return {"error": f"Invalid action: {action!r}. Use 'add' or 'remove'."}

        results = []
        for linked_id in linked_task_ids:
            try:
                await client.set_relationship_field(
                    task_id, field_id, [linked_id], action=action
                )
                results.append({
                    "task_id": task_id,
                    "linked_to": linked_id,
                    "action": action,
                    "status": "success",
                })
            except ClickUpAPIError as e:
                results.append({
                    "task_id": task_id,
                    "linked_to": linked_id,
                    "action": action,
                    "status": "failed",
                    "error": str(e),
                })

        # Log the action
        success_count = sum(1 for r in results if r["status"] == "success")
        log_warning = None
        try:
            action_log.log_action(
                action=f"set_relationship_{action}",
                status="success" if success_count == len(results) else "partial",
                summary=f"{'Linked' if action == 'add' else 'Unlinked'} {success_count}/{len(results)} tasks on {task_id}",
                results=results,
                undo={
                    "type": f"set_relationship_{'remove' if action == 'add' else 'add'}",
                    "task_id": task_id,
                    "field_id": field_id,
                    "linked_task_ids": [r["linked_to"] for r in results if r["status"] == "success"],
                },
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        response: dict = {"results": results}
        if log_warning:
            response["log_warning"] = log_warning
        return response
