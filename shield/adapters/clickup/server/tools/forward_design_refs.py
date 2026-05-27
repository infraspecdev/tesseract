"""ClickUp `forward_design_refs` — writes plan.json design_refs[] as URL
custom-field values on the synced ClickUp task with idempotent dedup.

ClickUp has no native upsert-by-key, so the adapter:

1. GETs the task's custom fields.
2. Looks up the `Shield Design Links` URL-list custom field (created at
   workspace init time; see `bulk_create.py`).
3. Compares each ref's idempotency_key against the field's `Shield Design Link Keys`
   companion (a text custom field holding comma-separated keys).
4. POSTs an updated URL list only for refs whose key isn't already present.

Re-running with the same refs produces zero duplicates because the second
call sees every key in the companion text field.
"""

from __future__ import annotations

import logging
from typing import Iterable

import httpx

from shield_adapters_common import DesignRef, ForwardError, ForwardResult


logger = logging.getLogger(__name__)

URL_FIELD_NAME = "Shield Design Links"
KEY_FIELD_NAME = "Shield Design Link Keys"


def _fetch_task(client: httpx.Client, base_url: str, task_id: str) -> dict | None:
    try:
        resp = client.get(f"{base_url}/api/v2/task/{task_id}", timeout=15)
    except httpx.RequestError:
        return None
    if resp.status_code != 200:
        return None
    return resp.json()


def _key_field_value(task: dict | None) -> tuple[str | None, list[str]]:
    """Return (field_id, existing_keys) for the keys companion field."""
    if not task:
        return None, []
    for field in task.get("custom_fields") or []:
        if field.get("name") == KEY_FIELD_NAME:
            raw = (field.get("value") or "") if isinstance(field.get("value"), str) else ""
            keys = [k.strip() for k in raw.split(",") if k.strip()]
            return field.get("id"), keys
    return None, []


def _url_field_id(task: dict | None) -> str | None:
    if not task:
        return None
    for field in task.get("custom_fields") or []:
        if field.get("name") == URL_FIELD_NAME:
            return field.get("id")
    return None


def _set_custom_field(
    client: httpx.Client,
    base_url: str,
    task_id: str,
    field_id: str,
    value: str,
) -> tuple[bool, ForwardError | None]:
    try:
        resp = client.post(
            f"{base_url}/api/v2/task/{task_id}/field/{field_id}",
            json={"value": value},
            timeout=15,
        )
    except httpx.RequestError as exc:
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


def forward_design_refs(
    task_id: str,
    refs: Iterable[DesignRef],
    *,
    client: httpx.Client | None = None,
    base_url: str = "https://api.clickup.com",
) -> ForwardResult:
    """Forward design_refs[] to a ClickUp task's URL custom field.

    Idempotency model: ref.idempotency_key is appended to the
    `Shield Design Link Keys` companion text field. Subsequent calls scan
    that field; refs whose key is already present are skipped without an
    HTTP write.
    """
    cli = client or httpx.Client()
    result = ForwardResult()

    task = _fetch_task(cli, base_url, task_id)
    url_field_id = _url_field_id(task)
    key_field_id, existing_keys = _key_field_value(task)

    if url_field_id is None or key_field_id is None:
        # No custom fields wired — log a no-op and return; this is a workspace
        # configuration concern handled by `/pm-sync` setup, not a hard error.
        for ref in refs:
            result.skipped += 1
            logger.info(
                "forward_design_ref",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "clickup",
                    "anchor_url": ref.anchor_url,
                    "outcome": "skipped_no_custom_field",
                    "idempotency_key": ref.idempotency_key,
                },
            )
        return result

    for ref in refs:
        if not ref.anchor_url:
            result.skipped += 1
            logger.info(
                "forward_design_ref",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "clickup",
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
                    "adapter": "clickup",
                    "anchor_url": ref.anchor_url,
                    "outcome": "idempotent_skip",
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue

        # Write the URL field, then update the keys companion.
        ok_url, err_url = _set_custom_field(cli, base_url, task_id, url_field_id, ref.anchor_url)
        if not ok_url:
            err = ForwardError(
                ref=ref,
                error_class=err_url.error_class if err_url else "HTTPError",
                message=err_url.message if err_url else "unknown",
                http_status=err_url.http_status if err_url else None,
            )
            result.errors.append(err)
            logger.warning(
                "forward_design_ref_failed",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "clickup",
                    "error_class": err.error_class,
                    "http_status": err.http_status,
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue

        existing_keys.append(ref.idempotency_key)
        joined = ",".join(existing_keys)
        ok_key, err_key = _set_custom_field(cli, base_url, task_id, key_field_id, joined)
        if not ok_key:
            # URL write succeeded but key companion failed — this is the only
            # window where a duplicate could leak on re-run. Treat as error.
            err = ForwardError(
                ref=ref,
                error_class=err_key.error_class if err_key else "HTTPError",
                message=(err_key.message if err_key else "key_field_write_failed"),
                http_status=err_key.http_status if err_key else None,
            )
            result.errors.append(err)
            logger.warning(
                "forward_design_ref_failed",
                extra={
                    "story_id": ref.story_id,
                    "adapter": "clickup",
                    "error_class": err.error_class,
                    "http_status": err.http_status,
                    "idempotency_key": ref.idempotency_key,
                },
            )
            continue
        result.created += 1
        logger.info(
            "forward_design_ref",
            extra={
                "story_id": ref.story_id,
                "adapter": "clickup",
                "anchor_url": ref.anchor_url,
                "outcome": "created",
                "idempotency_key": ref.idempotency_key,
            },
        )
    return result
