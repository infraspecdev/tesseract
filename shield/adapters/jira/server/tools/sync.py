"""Jira `forward_design_refs` — turns plan.json design_refs[] into
remote_issue_link entries with idempotent globalId.

API contract (P0-3): same `forward_design_refs(task_id, refs) -> ForwardResult`
signature implemented by every Shield PM adapter. The Jira flavour uses
`globalId = <idempotency_key>` on the POST /rest/api/3/issue/{issueIdOrKey}/remotelink
endpoint, which Atlassian treats as an upsert key — repeating the call with the
same globalId returns the existing link rather than creating a duplicate.

This module is dispatched from `server/main.py` once the MCP tool is registered
(see EPIC-4-S3). The function below works as a plain callable so the
idempotency contract can be tested without spinning up the MCP server.
"""

from __future__ import annotations

import logging
from typing import Iterable

import requests

from shield_adapters_common import DesignRef, ForwardError, ForwardResult


logger = logging.getLogger(__name__)


def _post_remote_link(
    session: requests.Session,
    base_url: str,
    task_id: str,
    ref: DesignRef,
) -> tuple[bool, ForwardError | None]:
    """POST one remote link. Returns (created, error_or_none).

    Jira's remotelink endpoint is upsert-by-globalId — a repeat call with the
    same globalId returns 200 with the existing link. We classify any 2xx with
    `application/json` as `created` for the first ever insert; subsequent
    inserts come back as 200 too, so adapters typically GET-first to count
    `skipped` vs `created`. For the scaffold, we treat 201 as created, 200 as
    skipped (Atlassian's documented contract).
    """
    url = f"{base_url}/rest/api/3/issue/{task_id}/remotelink"
    payload = {
        "globalId": ref.idempotency_key,
        "object": {
            "url": ref.anchor_url or "about:blank",
            "title": ref.label,
        },
    }
    try:
        resp = session.post(url, json=payload, timeout=15)
    except requests.RequestException as exc:
        return False, ForwardError(
            ref=ref,
            error_class=type(exc).__name__,
            message=str(exc),
            http_status=None,
        )
    if resp.status_code == 201:
        return True, None
    if resp.status_code == 200:
        return False, None  # idempotent skip
    return False, ForwardError(
        ref=ref,
        error_class="HTTPError",
        message=resp.text[:200],
        http_status=resp.status_code,
    )


def forward_design_refs(
    task_id: str,
    refs: Iterable[DesignRef],
    *,
    session: requests.Session | None = None,
    base_url: str = "https://example.atlassian.net",
) -> ForwardResult:
    """Forward design_refs[] to a Jira issue's remote links.

    Args:
        task_id: Jira issue ID or key (e.g. "ENG-1234").
        refs:    The design refs to forward. Anchorless placeholders (LLD
                 `TODO`) are skipped silently.
        session: Optional requests.Session for credentials / connection reuse.
                 Defaults to a transient session.
        base_url: Jira cloud / DC base URL.

    Returns:
        A ForwardResult with created/skipped/errors aggregates.

    The function is observability-friendly: each ref dispatches one log line
    with `action='forward_design_ref'` and structured fields per the P1-8
    observability contract (story_id, adapter, anchor_url, outcome,
    idempotency_key). Failures emit `forward_design_ref_failed` with
    `{error_class, http_status, idempotency_key}`.
    """
    sess = session or requests.Session()
    result = ForwardResult()
    for ref in refs:
        if not ref.anchor_url:
            # Anchorless placeholders (e.g., LLD TODOs) do not forward.
            result.skipped += 1
            logger.info(
                "forward_design_ref",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "jira",
                    "anchor_url": None,
                    "outcome": "skipped_no_anchor",
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue
        created, err = _post_remote_link(sess, base_url, task_id, ref)
        if err is not None:
            result.errors.append(err)
            logger.warning(
                "forward_design_ref_failed",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "jira",
                    "error_class": err.error_class,
                    "http_status": err.http_status,
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue
        if created:
            result.created += 1
            outcome = "created"
        else:
            result.skipped += 1
            outcome = "idempotent_skip"
        logger.info(
            "forward_design_ref",
            extra={
                "story_id": ref.story_id,
                "adapter": "jira",
                "anchor_url": ref.anchor_url,
                "outcome": outcome,
                "idempotency_key": ref.idempotency_key,
            },
        )
    return result
