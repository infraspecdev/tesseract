"""Confluence `forward_design_refs` — turns plan.json design_refs[] into
remote_link entries on a Confluence page or task.

Confluence's `application/link` REST endpoint exposes a `name` field that
serves as our idempotency token (P0-3). Re-posting with the same `name`
returns the existing link rather than creating a duplicate.
"""

from __future__ import annotations

import logging
from typing import Iterable

import requests

from shield_adapters_common import DesignRef, ForwardError, ForwardResult


logger = logging.getLogger(__name__)


def _put_remote_link(
    session: requests.Session,
    base_url: str,
    page_id: str,
    ref: DesignRef,
) -> tuple[bool, ForwardError | None]:
    """PUT one remote link via `name`. Returns (created, error_or_none).

    Confluence treats PUT to /rest/api/content/{id}/relation/link/from with the
    same `name` as upsert-by-name. A 201 indicates a new link; 200 indicates
    idempotent replacement.
    """
    url = f"{base_url}/rest/api/content/{page_id}/relation/link/from"
    payload = {
        "name": ref.idempotency_key,
        "destination": {
            "url": ref.anchor_url or "about:blank",
            "title": ref.label,
        },
    }
    try:
        resp = session.put(url, json=payload, timeout=15)
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
        return False, None
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
    base_url: str = "https://example.atlassian.net/wiki",
) -> ForwardResult:
    """Forward design_refs[] to a Confluence page's remote links.

    `task_id` is the Confluence content ID (page or task) the link attaches to.
    """
    sess = session or requests.Session()
    result = ForwardResult()
    for ref in refs:
        if not ref.anchor_url:
            result.skipped += 1
            logger.info(
                "forward_design_ref",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "confluence",
                    "anchor_url": None,
                    "outcome": "skipped_no_anchor",
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue
        created, err = _put_remote_link(sess, base_url, task_id, ref)
        if err is not None:
            result.errors.append(err)
            logger.warning(
                "forward_design_ref_failed",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "confluence",
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
                "adapter": "confluence",
                "anchor_url": ref.anchor_url,
                "outcome": outcome,
                "idempotency_key": ref.idempotency_key,
            },
        )
    return result
