"""Idempotency test (P0-4) for the Notion adapter.

Notion has no native upsert-by-key, so the adapter scans the page's
`Shield Link Keys` rich-text property for the ref's idempotency_key. First
call writes; second call sees the key in the property and skips.
"""

from __future__ import annotations

import responses
from shield_adapters_common import DesignRef

from server.tools.sync import forward_design_refs


NOTION = "https://api.notion.com"


def _ref() -> DesignRef:
    return DesignRef(
        story_id="EPIC-1-S1",
        doc="trd",
        section_id="apis-involved",
        anchor_url="https://docs.example.com/trd.md#apis-involved",
        label="§11 APIs Involved",
    )


def _empty_page() -> dict:
    return {
        "id": "page-uuid",
        "properties": {
            "Shield Link Keys": {"rich_text": []},
            "Design Links": {"url": None},
        },
    }


def _page_with_key(key: str) -> dict:
    return {
        "id": "page-uuid",
        "properties": {
            "Shield Link Keys": {
                "rich_text": [{"text": {"content": key}}],
            },
            "Design Links": {"url": "https://prev"},
        },
    }


@responses.activate
def test_double_run_yields_zero_duplicates() -> None:
    ref = _ref()

    # First run: page has no keys → PATCH succeeds.
    responses.get(f"{NOTION}/v1/pages/page-uuid", json=_empty_page(), status=200)
    responses.patch(f"{NOTION}/v1/pages/page-uuid", json={"id": "page-uuid"}, status=200)

    first = forward_design_refs("page-uuid", [ref], base_url=NOTION)
    assert first.created == 1
    assert first.skipped == 0
    assert first.errors == []

    # Reset mocks for second run: page now reports the key.
    responses.reset()
    responses.get(f"{NOTION}/v1/pages/page-uuid", json=_page_with_key(ref.idempotency_key), status=200)

    second = forward_design_refs("page-uuid", [ref], base_url=NOTION)
    assert second.created == 0
    assert second.skipped == 1
    assert second.errors == []
