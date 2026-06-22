"""Shared helpers for github-sprint-planner MCP tools."""

from __future__ import annotations


def normalize_status(state: str, labels: list[str]) -> str:
    """Map GitHub issue state + labels to a sprint status category."""
    if state == "closed":
        return "done"
    label_lower = [l.lower() for l in labels]
    if any(l in label_lower for l in ("in progress", "in-progress", "in dev", "in-dev")):
        return "in_progress"
    if any(l in label_lower for l in ("blocked",)):
        return "blocked"
    return "ready"
