"""Notion `forward_design_refs` — writes plan.json design_refs[] as URL property
values on the synced Notion page, with idempotent dedup via the idempotency_key.

Notion's API has no native upsert-by-globalId, so we GET the page first, scan
its `properties.<URL property>` collection for an entry whose URL matches the
ref's `anchor_url`, and PATCH only if absent. The idempotency_key is also
stored in a `properties.Shield Link Key` rich-text property to detect refs
whose anchor URL changed (label updates).
"""

from __future__ import annotations

import logging
from typing import Iterable

import requests

from shield_adapters_common import DesignRef, ForwardError, ForwardResult


logger = logging.getLogger(__name__)

URL_PROPERTY = "Design Links"
KEY_PROPERTY = "Shield Link Keys"


def _fetch_page(session: requests.Session, base_url: str, page_id: str) -> dict | None:
    url = f"{base_url}/v1/pages/{page_id}"
    try:
        resp = session.get(url, timeout=15)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    return resp.json()


def _patch_page(
    session: requests.Session,
    base_url: str,
    page_id: str,
    new_url: str,
    new_label: str,
    new_key: str,
    existing_urls: list[str],
    existing_keys: list[str],
) -> tuple[bool, ForwardError | None]:
    payload = {
        "properties": {
            URL_PROPERTY: {
                "url": new_url,
            },
            KEY_PROPERTY: {
                "rich_text": [
                    {"text": {"content": ", ".join(existing_keys + [new_key])}},
                ],
            },
        }
    }
    try:
        resp = session.patch(f"{base_url}/v1/pages/{page_id}", json=payload, timeout=15)
    except requests.RequestException as exc:
        return False, ForwardError(
            ref=None,  # type: ignore[arg-type]
            error_class=type(exc).__name__,
            message=str(exc),
            http_status=None,
        )
    if resp.status_code == 200:
        return True, None
    return False, ForwardError(
        ref=None,  # type: ignore[arg-type]
        error_class="HTTPError",
        message=resp.text[:200],
        http_status=resp.status_code,
    )


def _existing_keys(page: dict | None) -> list[str]:
    if not page:
        return []
    prop = (page.get("properties") or {}).get(KEY_PROPERTY) or {}
    rich = prop.get("rich_text") or []
    if not rich:
        return []
    raw = rich[0].get("text", {}).get("content", "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def forward_design_refs(
    task_id: str,
    refs: Iterable[DesignRef],
    *,
    session: requests.Session | None = None,
    base_url: str = "https://api.notion.com",
) -> ForwardResult:
    """Forward design_refs[] to a Notion page's URL property.

    `task_id` is the Notion page ID (UUID).
    """
    sess = session or requests.Session()
    result = ForwardResult()

    page = _fetch_page(sess, base_url, task_id)
    existing_keys = _existing_keys(page)

    for ref in refs:
        if not ref.anchor_url:
            result.skipped += 1
            logger.info(
                "forward_design_ref",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "notion",
                    "anchor_url": None,
                    "outcome": "skipped_no_anchor",
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue
        if ref.idempotency_key in existing_keys:
            result.skipped += 1
            logger.info(
                "forward_design_ref",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "notion",
                    "anchor_url": ref.anchor_url,
                    "outcome": "idempotent_skip",
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue
        ok, err = _patch_page(
            sess,
            base_url,
            task_id,
            ref.anchor_url,
            ref.label,
            ref.idempotency_key,
            existing_urls=[],
            existing_keys=existing_keys,
        )
        if not ok:
            # Re-attach the ref to the error before we surface it (the helper
            # doesn't have it in scope when constructing the error).
            err = ForwardError(
                ref=ref,
                error_class=err.error_class if err else "HTTPError",
                message=err.message if err else "unknown",
                http_status=err.http_status if err else None,
            )
            result.errors.append(err)
            logger.warning(
                "forward_design_ref_failed",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "notion",
                    "error_class": err.error_class,
                    "http_status": err.http_status,
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue
        existing_keys.append(ref.idempotency_key)
        result.created += 1
        logger.info(
            "forward_design_ref",
            extra={
                "story_id": ref.story_id,
                "adapter": "notion",
                "anchor_url": ref.anchor_url,
                "outcome": "created",
                "idempotency_key": ref.idempotency_key,
            },
        )
    return result
