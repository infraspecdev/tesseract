"""Tests for pm_bulk_create milestone tagging + the milestone_tag helper."""

from __future__ import annotations

from server.tools._helpers import MILESTONE_TAG_PREFIX, milestone_tag


def test_milestone_tag_lowercases() -> None:
    assert milestone_tag("M2") == "shield:ms:m2"


def test_milestone_tag_uses_prefix() -> None:
    assert milestone_tag("M1").startswith(MILESTONE_TAG_PREFIX)
    assert milestone_tag("M1") == "shield:ms:m1"
