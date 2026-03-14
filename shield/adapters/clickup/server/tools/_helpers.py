"""Shared helpers for sprint-planner MCP tools."""

from __future__ import annotations


def _get_linked_epic_ids(task: dict, relationship_field_id: str) -> set[str]:
    """Extract epic task IDs from a task's relationship custom field."""
    for cf in task.get("custom_fields", []):
        if cf.get("id") == relationship_field_id:
            value = cf.get("value") or []
            return {str(v.get("id", "")) for v in value if isinstance(v, dict)}
    return set()
