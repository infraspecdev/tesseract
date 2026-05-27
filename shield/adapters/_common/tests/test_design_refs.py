"""Contract tests for shield_adapters_common.design_refs."""

from __future__ import annotations

from shield_adapters_common import DesignRef, ForwardError, ForwardResult, idempotency_key


def test_idempotency_key_is_deterministic() -> None:
    k1 = idempotency_key("EPIC-1-S1", "trd.md#high-level-design")
    k2 = idempotency_key("EPIC-1-S1", "trd.md#high-level-design")
    assert k1 == k2
    assert len(k1) == 32
    assert all(c in "0123456789abcdef" for c in k1)


def test_idempotency_key_differs_per_story() -> None:
    k1 = idempotency_key("EPIC-1-S1", "trd.md#x")
    k2 = idempotency_key("EPIC-1-S2", "trd.md#x")
    assert k1 != k2


def test_idempotency_key_differs_per_anchor() -> None:
    k1 = idempotency_key("S1", "trd.md#a")
    k2 = idempotency_key("S1", "trd.md#b")
    assert k1 != k2


def test_idempotency_key_anchorless_placeholder() -> None:
    """LLD placeholders without anchor_url still produce stable keys
    distinguished by (story_id, doc, component)."""
    k1 = idempotency_key("S1", None, doc="lld", component="orders-refund")
    k2 = idempotency_key("S1", None, doc="lld", component="payments")
    assert k1 != k2
    assert len(k1) == 32
    # Same triple → same key.
    assert k1 == idempotency_key("S1", None, doc="lld", component="orders-refund")


def test_design_ref_idempotency_key_matches_helper() -> None:
    ref = DesignRef(
        story_id="EPIC-1-S1",
        doc="trd",
        section_id="apis-involved",
        anchor_url="trd.md#apis-involved",
        label="§11 APIs Involved",
    )
    assert ref.idempotency_key == idempotency_key("EPIC-1-S1", "trd.md#apis-involved")


def test_forward_result_aggregates() -> None:
    ref = DesignRef("S1", "trd", "x", "trd.md#x", "x")
    result = ForwardResult(
        created=2,
        skipped=1,
        errors=[ForwardError(ref=ref, error_class="HTTPError", message="500", http_status=500)],
    )
    assert result.created == 2
    assert result.skipped == 1
    assert len(result.errors) == 1
    assert result.errors[0].idempotency_key == ref.idempotency_key
