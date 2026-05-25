"""Contract test for the Confluence adapter."""

from __future__ import annotations

import inspect

from shield_adapters_common import ForwardResult

from server.tools.sync import forward_design_refs


def test_signature_matches_common_protocol() -> None:
    sig = inspect.signature(forward_design_refs)
    params = list(sig.parameters.values())
    assert params[0].name == "task_id"
    assert params[1].name == "refs"


def test_empty_refs_returns_empty_result() -> None:
    result = forward_design_refs("page-1", [])
    assert isinstance(result, ForwardResult)
    assert result.created == 0
    assert result.skipped == 0
    assert result.errors == []
