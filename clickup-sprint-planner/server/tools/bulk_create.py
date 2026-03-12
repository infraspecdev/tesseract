"""MCP tool: sprint_bulk_create — batch task creation with optional relationship linking."""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig

# Matches names already prefixed like "P3 - ", "P1a - ", "P2b - "
_EPIC_PREFIX_RE = re.compile(r"^[A-Z]\d+[a-z]?\s*-\s*")

# Required sections in card descriptions
_REQUIRED_SECTIONS = ["Summary", "Tasks", "Context", "Acceptance Criteria"]


def _auto_format_name(story: dict) -> str:
    """Auto-prefix task name with epic_id if not already prefixed."""
    name = story["name"]
    epic_id = story.get("epic_id")
    if epic_id and not _EPIC_PREFIX_RE.match(name):
        return f"{epic_id} - {name}"
    return name


def _check_description_sections(description: str | None) -> list[str]:
    """Check for required sections in a card description. Returns missing section names."""
    if not description:
        return list(_REQUIRED_SECTIONS)
    desc_lower = description.lower()
    return [s for s in _REQUIRED_SECTIONS if s.lower() not in desc_lower]


def register(mcp: FastMCP, client: ClickUpClient, action_log: ActionLog, config: SprintPlannerConfig):
    @mcp.tool()
    async def sprint_bulk_create(
        list_id: str,
        stories: list[dict],
        set_relationships: bool = False,
    ) -> dict:
        """Create multiple ClickUp tasks in one call with optional EPIC relationship linking.

        Each story dict should have:
          - name (required): Task name
          - description: Task description
          - assignee: User ID string
          - priority: "urgent", "high", "normal", or "low"
          - orderindex: Position in the list (string, e.g. "1000")
          - epic_id: EPIC task ID to link via relationship field (requires set_relationships=true)

        Args:
            list_id: The ClickUp list ID to create tasks in.
            stories: Array of story objects to create.
            set_relationships: If true, link each task to its epic_id via the relationship field.
        """
        priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}

        created = []
        failed = []
        relationships = []
        format_warnings = []

        for story in stories:
            # Auto-format name with epic prefix
            formatted_name = _auto_format_name(story)
            task_data: dict = {"name": formatted_name}

            # Validate description sections
            missing = _check_description_sections(story.get("description"))
            if missing:
                format_warnings.append({
                    "name": formatted_name,
                    "missing_sections": missing,
                })

            if story.get("description"):
                task_data["description"] = story["description"]
            if story.get("assignee"):
                task_data["assignees"] = [int(story["assignee"])]
            if story.get("priority") and story["priority"] in priority_map:
                task_data["priority"] = priority_map[story["priority"]]
            if story.get("orderindex") is not None:
                task_data["orderindex"] = str(story["orderindex"])

            try:
                result = await client.create_task(list_id, task_data)
                task_id = result["id"]
                task_url = result.get("url", f"https://app.clickup.com/t/{task_id}")
                created.append({
                    "task_id": task_id,
                    "task_url": task_url,
                    "name": formatted_name,
                    "status": "success",
                })

                # Set relationship if requested and epic_id provided
                if set_relationships and story.get("epic_id"):
                    field_id = config.clickup.relationship_field.id
                    try:
                        await client.set_relationship_field(
                            task_id, field_id, [story["epic_id"]]
                        )
                        relationships.append({
                            "task_id": task_id,
                            "epic_id": story["epic_id"],
                            "status": "success",
                        })
                    except ClickUpAPIError as e:
                        relationships.append({
                            "task_id": task_id,
                            "epic_id": story["epic_id"],
                            "status": "failed",
                            "error": str(e),
                        })

            except ClickUpAPIError as e:
                failed.append({
                    "name": formatted_name,
                    "status": "failed",
                    "error": str(e),
                })

        # Log grouped action
        log_warning = None
        try:
            action_log.log_action(
                action="bulk_create",
                status="success" if not failed else "partial",
                summary=f"Created {len(created)}/{len(stories)} tasks in list {list_id}",
                results=created + failed,
                relationships=relationships,
                undo={
                    "type": "bulk_delete",
                    "task_ids": [c["task_id"] for c in created],
                    "relationships_to_remove": [
                        {
                            "task_id": r["task_id"],
                            "epic_id": r["epic_id"],
                            "field_id": config.clickup.relationship_field.id,
                        }
                        for r in relationships
                        if r["status"] == "success"
                    ],
                },
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        result = {
            "created": created,
            "failed": failed,
            "relationships": relationships,
        }
        if format_warnings:
            result["format_warnings"] = format_warnings
        if log_warning:
            result["log_warning"] = log_warning
        return result
