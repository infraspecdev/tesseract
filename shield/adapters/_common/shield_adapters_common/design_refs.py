"""design_refs.py — shared types and protocol for forwarding design_refs[] from
plan.json sidecars to PM-tool web links.

All four adapters (Jira, Confluence, ClickUp, Notion) implement the same
`forward_design_refs(task_id, refs) -> ForwardResult` signature, using
deterministic idempotency keys to guarantee that re-running `/pm-sync` produces
no duplicate remote-links.

Key shape (per P0-3 in the plan review):

    idempotency_key = sha256(story_id + anchor_url)[:32]

Adapter wiring (per P0-3):

- Jira:       `globalId` on `remote_issue_link`
- Confluence: `name` on `remote_link`
- ClickUp:    comparison key for URL custom-field dedup before write
- Notion:     comparison key for URL property dedup before write
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class DesignRef:
    """One design_refs[] entry as projected for forwarding.

    `story_id` is the owning plan.json story id; it is not stored on the ref
    in plan.json itself but is needed to compute the idempotency key.
    """

    story_id: str
    doc: str  # "trd" | "lld" | "prd"
    section_id: str | None
    anchor_url: str | None
    label: str
    component: str | None = None

    @property
    def idempotency_key(self) -> str:
        return idempotency_key(self.story_id, self.anchor_url, self.doc, self.component)


@dataclass
class ForwardError:
    """One failed forward call. `idempotency_key` lets callers correlate the
    failure with the originating ref."""

    ref: DesignRef
    error_class: str
    message: str
    http_status: int | None = None

    @property
    def idempotency_key(self) -> str:
        return self.ref.idempotency_key


@dataclass
class ForwardResult:
    """Aggregate outcome of forwarding a batch of refs for one task."""

    created: int = 0
    skipped: int = 0
    errors: list[ForwardError] = field(default_factory=list)


def idempotency_key(
    story_id: str,
    anchor_url: str | None,
    doc: str = "trd",
    component: str | None = None,
) -> str:
    """Compute the deterministic 32-char idempotency key.

    `sha256(story_id + anchor_url)[:32]` for refs with a concrete anchor.
    For anchorless placeholders (e.g., LLD `TODO`), hash a synthetic key so
    re-runs remain stable across regenerations.
    """
    if anchor_url:
        payload = f"{story_id}::{anchor_url}"
    else:
        payload = f"{story_id}::{doc}::{component or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class ForwardDesignRefsProtocol(Protocol):
    """The adapter-side function signature each PM tool implements."""

    def __call__(self, task_id: str, refs: list[DesignRef]) -> ForwardResult: ...
