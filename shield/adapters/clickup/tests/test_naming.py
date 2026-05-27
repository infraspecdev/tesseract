"""Tests for the canonical task-name formatter shared by create + rename."""

from __future__ import annotations

import pytest

from server.naming import format_epic_name, format_story_name, story_index


def test_story_simple_format() -> None:
    out = format_story_name(
        "[{epic_id}] {name}", prefix="", epic_id="EPIC-1", index="1", name="Do X"
    )
    assert out == "[EPIC-1] Do X"


def test_story_full_format_with_prefix_and_index() -> None:
    out = format_story_name(
        "[{prefix}] {epic_id}-S{index}: {name}",
        prefix="SHIELD", epic_id="EPIC-1", index="1", name="Do X",
    )
    assert out == "[SHIELD] EPIC-1-S1: Do X"


def test_story_unknown_placeholder_raises_named_error() -> None:
    with pytest.raises(ValueError) as exc:
        format_story_name(
            "{foo} {name}", prefix="", epic_id="E", index="1", name="n"
        )
    assert "story_format" in str(exc.value)
    assert "{foo}" in str(exc.value)


def test_epic_default_format_uses_name() -> None:
    out = format_epic_name(
        "[EPIC] {name} | [{epic_id}]",
        prefix="", epic_id="EPIC-1", name="First epic", epic_name="First epic",
    )
    assert out == "[EPIC] First epic | [EPIC-1]"


def test_epic_format_with_prefix_and_epic_name() -> None:
    out = format_epic_name(
        "[{prefix}] {epic_id}: {epic_name}",
        prefix="SHIELD", epic_id="EPIC-1", name="ignored", epic_name="First epic",
    )
    assert out == "[SHIELD] EPIC-1: First epic"


def test_epic_unknown_placeholder_raises_named_error() -> None:
    with pytest.raises(ValueError) as exc:
        format_epic_name(
            "{bar}", prefix="", epic_id="E", name="n", epic_name="n"
        )
    assert "epic_format" in str(exc.value)
    assert "{bar}" in str(exc.value)


def test_story_index_parses_trailing_s_number() -> None:
    assert story_index("EPIC-1-S1") == "1"
    assert story_index("EPIC-4-S0") == "0"
    assert story_index("EPIC-12-S37") == "37"


def test_story_index_returns_empty_when_absent() -> None:
    assert story_index("EPIC-1") == ""
    assert story_index("freeform-id") == ""
