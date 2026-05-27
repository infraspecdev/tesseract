"""Per-adapter idempotency test (P0-4) for the ClickUp adapter."""

from __future__ import annotations

import httpx
import respx
from shield_adapters_common import DesignRef

from server.tools.forward_design_refs import (
    KEY_FIELD_NAME,
    URL_FIELD_NAME,
    forward_design_refs,
)


CLICKUP = "https://api.clickup.com"


def _ref() -> DesignRef:
    return DesignRef(
        story_id="EPIC-1-S1",
        doc="trd",
        section_id="apis-involved",
        anchor_url="https://docs.example.com/trd.md#apis-involved",
        label="§11 APIs Involved",
    )


def _task_payload(keys: str = "") -> dict:
    return {
        "id": "t1",
        "custom_fields": [
            {"id": "url-field-id", "name": URL_FIELD_NAME, "value": None},
            {"id": "key-field-id", "name": KEY_FIELD_NAME, "value": keys},
        ],
    }


@respx.mock
def test_double_run_yields_zero_duplicates() -> None:
    ref = _ref()

    # First run: task has empty key field. URL + key field writes both succeed.
    respx.get(f"{CLICKUP}/api/v2/task/t1").mock(return_value=httpx.Response(200, json=_task_payload("")))
    respx.post(f"{CLICKUP}/api/v2/task/t1/field/url-field-id").mock(return_value=httpx.Response(200))
    respx.post(f"{CLICKUP}/api/v2/task/t1/field/key-field-id").mock(return_value=httpx.Response(200))

    with httpx.Client() as client:
        first = forward_design_refs("t1", [ref], client=client, base_url=CLICKUP)

    assert first.created == 1
    assert first.skipped == 0
    assert first.errors == []

    # Second run: task now reports the key in its key field → skip without write.
    respx.reset()
    respx.get(f"{CLICKUP}/api/v2/task/t1").mock(
        return_value=httpx.Response(200, json=_task_payload(ref.idempotency_key))
    )

    with httpx.Client() as client:
        second = forward_design_refs("t1", [ref], client=client, base_url=CLICKUP)

    assert second.created == 0
    assert second.skipped == 1
    assert second.errors == []


@respx.mock
def test_anchorless_placeholder_skips() -> None:
    placeholder = DesignRef(
        story_id="EPIC-1-S1",
        doc="lld",
        section_id=None,
        anchor_url=None,
        label="TODO: link when /lld lands",
    )
    respx.get(f"{CLICKUP}/api/v2/task/t1").mock(return_value=httpx.Response(200, json=_task_payload("")))

    with httpx.Client() as client:
        result = forward_design_refs("t1", [placeholder], client=client, base_url=CLICKUP)

    assert result.created == 0
    assert result.skipped == 1
    assert result.errors == []


@respx.mock
def test_no_custom_field_logs_noop_without_error() -> None:
    """If the ClickUp workspace doesn't have the Shield custom fields wired,
    the adapter logs and skips rather than failing — workspace configuration
    is handled by /pm-sync setup, not by the forwarding code."""
    respx.get(f"{CLICKUP}/api/v2/task/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "custom_fields": []})
    )

    with httpx.Client() as client:
        result = forward_design_refs("t1", [_ref()], client=client, base_url=CLICKUP)

    assert result.created == 0
    assert result.skipped == 1
    assert result.errors == []
