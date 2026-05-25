"""Shared types and protocols for Shield PM adapters.

Each adapter (Jira, Confluence, ClickUp, Notion) imports from this module so
all four expose the same `forward_design_refs(task_id, refs) -> ForwardResult`
signature with deterministic idempotency keys.
"""

from .design_refs import (
    DesignRef,
    ForwardError,
    ForwardResult,
    idempotency_key,
)

__all__ = [
    "DesignRef",
    "ForwardError",
    "ForwardResult",
    "idempotency_key",
]
