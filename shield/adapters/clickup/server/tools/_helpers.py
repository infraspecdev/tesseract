"""Shared helpers for sprint-planner MCP tools."""

from __future__ import annotations


def _get_linked_epic_ids(task: dict, relationship_field_id: str) -> set[str]:
    """Extract epic task IDs from a task's relationship custom field."""
    for cf in task.get("custom_fields", []):
        if cf.get("id") == relationship_field_id:
            value = cf.get("value") or []
            return {str(v.get("id", "")) for v in value if isinstance(v, dict)}
    return set()


MILESTONE_TAG_PREFIX = "shield:ms:"


def milestone_tag(milestone_id: str) -> str:
    """Canonical ClickUp tag for a milestone.

    Lowercased because ClickUp normalizes tag names to lowercase; keying on the
    stable milestone_id (e.g. "M1") rather than the mutable milestone name means
    a rename never orphans the tag.
    """
    return f"{MILESTONE_TAG_PREFIX}{milestone_id}".lower()
