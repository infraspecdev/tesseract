# shield/scripts/test_path_resolver.py
"""Tests for path_resolver.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from path_resolver import resolve  # type: ignore[import-not-found]


def test_resolve_simple_template() -> None:
    result = resolve("feature_dir", output_dir="docs/shield", feature="vpc-20260522")
    assert result == "docs/shield/vpc-20260522"


def test_resolve_nested_template() -> None:
    # `research` template = "{feature_dir}/research.md", and `feature_dir` is itself a template
    result = resolve("research", output_dir="docs/shield", feature="vpc-20260522")
    assert result == "docs/shield/vpc-20260522/research.md"


def test_resolve_review_dir_first_run() -> None:
    result = resolve(
        "review_dir",
        output_dir="docs/shield",
        feature="vpc-20260522",
        review_type="plan",
        date="2026-05-21",
        _counter="",
    )
    assert result == "docs/shield/vpc-20260522/reviews/plan/2026-05-21"


def test_resolve_review_dir_same_day_rerun() -> None:
    result = resolve(
        "review_dir",
        output_dir="docs/shield",
        feature="vpc-20260522",
        review_type="plan",
        date="2026-05-21",
        _counter="_2",
    )
    assert result == "docs/shield/vpc-20260522/reviews/plan/2026-05-21_2"
