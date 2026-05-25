"""Contract test — placeholder per EPIC-4-S0 AC.

Confirms the adapter exposes the canonical `forward_design_refs` signature
imported from shield_adapters_common.
"""

from __future__ import annotations

import inspect

from shield_adapters_common import DesignRef, ForwardResult

from server.tools.sync import forward_design_refs


def test_signature_matches_common_protocol() -> None:
    sig = inspect.signature(forward_design_refs)
    params = list(sig.parameters.values())
    # First positional: task_id (str). Second: refs (iterable of DesignRef).
    assert params[0].name == "task_id"
    assert params[1].name == "refs"


def test_empty_refs_returns_empty_result() -> None:
    result = forward_design_refs("ENG-1", [])
    assert isinstance(result, ForwardResult)
    assert result.created == 0
    assert result.skipped == 0
    assert result.errors == []


def test_anchorless_placeholder_skips_without_http(sample_refs: list[DesignRef]) -> None:
    """LLD TODO placeholders (anchor_url=None) MUST be skipped before any HTTP
    call — they don't have a target URL to post."""
    placeholder = [r for r in sample_refs if r.anchor_url is None]
    result = forward_design_refs("ENG-1", placeholder)
    assert result.skipped == len(placeholder)
    assert result.created == 0
    assert result.errors == []
