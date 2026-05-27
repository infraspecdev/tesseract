"""Idempotency test (P0-4) for the Confluence adapter."""

from __future__ import annotations

import responses
from shield_adapters_common import DesignRef

from server.tools.sync import forward_design_refs


CONF = "https://example.atlassian.net/wiki"


def _ref() -> DesignRef:
    return DesignRef(
        story_id="EPIC-1-S1",
        doc="trd",
        section_id="apis-involved",
        anchor_url="https://docs.example.com/trd.md#apis-involved",
        label="§11 APIs Involved",
    )


@responses.activate
def test_double_run_yields_zero_duplicates() -> None:
    ref = _ref()
    responses.add(
        responses.PUT,
        f"{CONF}/rest/api/content/page-1/relation/link/from",
        json={"name": ref.idempotency_key},
        status=201,
    )
    first = forward_design_refs("page-1", [ref], base_url=CONF)
    assert first.created == 1
    assert first.skipped == 0

    responses.replace(
        responses.PUT,
        f"{CONF}/rest/api/content/page-1/relation/link/from",
        json={"name": ref.idempotency_key},
        status=200,
    )
    second = forward_design_refs("page-1", [ref], base_url=CONF)
    assert second.created == 0
    assert second.skipped == 1
