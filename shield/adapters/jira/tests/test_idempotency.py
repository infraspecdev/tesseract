"""Per-adapter idempotency test (P0-4): running forward_design_refs twice
with the same refs against a mocked Jira remote produces zero duplicates.
"""

from __future__ import annotations

import responses
from shield_adapters_common import DesignRef

from server.tools.sync import forward_design_refs


JIRA = "https://example.atlassian.net"


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
    # Jira semantics: first POST with a new globalId → 201; second POST with
    # the same globalId → 200 (idempotent).
    responses.add(
        responses.POST,
        f"{JIRA}/rest/api/3/issue/ENG-1/remotelink",
        json={"id": 100, "globalId": ref.idempotency_key},
        status=201,
    )
    first = forward_design_refs("ENG-1", [ref], base_url=JIRA)
    assert first.created == 1
    assert first.skipped == 0
    assert first.errors == []

    responses.replace(
        responses.POST,
        f"{JIRA}/rest/api/3/issue/ENG-1/remotelink",
        json={"id": 100, "globalId": ref.idempotency_key},
        status=200,
    )
    second = forward_design_refs("ENG-1", [ref], base_url=JIRA)
    assert second.created == 0
    assert second.skipped == 1
    assert second.errors == []
