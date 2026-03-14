"""MCP tool: sprint_action_log — query the action log."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog


def register(mcp: FastMCP, action_log: ActionLog):
    @mcp.tool()
    async def sprint_action_log(
        epic: str | None = None,
        action: str | None = None,
        since: str | None = None,
        last_n: int | None = None,
    ) -> dict:
        """Query the action log for past sprint planning operations.

        Filter by epic, action type, date, or get the last N entries.

        Args:
            epic: Filter by epic ID (e.g. "P1a").
            action: Filter by action type (e.g. "bulk_create", "set_relationship_add").
            since: ISO date string — only return entries after this timestamp.
            last_n: Return only the last N entries (after other filters).
        """
        actions = action_log.get_actions(
            epic=epic, action=action, since=since, last_n=last_n
        )
        return {"actions": actions, "total": len(actions)}
