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


def test_resolve_unknown_name_raises() -> None:
    with pytest.raises(KeyError) as excinfo:
        resolve("not_a_registered_name", output_dir="docs/shield", feature="x")
    assert "not_a_registered_name" in str(excinfo.value)


def test_resolve_missing_variable_raises() -> None:
    # `research` needs `output_dir` and `feature`; omit `feature`.
    with pytest.raises(KeyError) as excinfo:
        resolve("research", output_dir="docs/shield")
    assert "feature" in str(excinfo.value)


def test_all_spec_paths_resolve() -> None:
    """Smoke test: every path in the spec §5.1 resolves with sample bindings."""
    new_paths = [
        ("manifest",              dict(output_dir="docs/shield")),
        ("global_outputs_dir",    dict(output_dir="docs/shield")),
        ("global_index_html",     dict(output_dir="docs/shield")),
        ("feature_dir",           dict(output_dir="docs/shield", feature="f")),
        ("readme",                dict(output_dir="docs/shield", feature="f")),
        ("research",              dict(output_dir="docs/shield", feature="f")),
        ("prd",                   dict(output_dir="docs/shield", feature="f")),
        ("plan_json",             dict(output_dir="docs/shield", feature="f")),
        ("plan_md",               dict(output_dir="docs/shield", feature="f")),
        ("plan_arch_md",          dict(output_dir="docs/shield", feature="f")),
        ("feature_outputs",       dict(output_dir="docs/shield", feature="f")),
        ("readme_html",           dict(output_dir="docs/shield", feature="f")),
        ("prd_html",              dict(output_dir="docs/shield", feature="f")),
        ("plan_html",             dict(output_dir="docs/shield", feature="f")),
        ("plan_arch_html",        dict(output_dir="docs/shield", feature="f")),
        ("review_dir",            dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_summary",        dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_enhanced",       dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_detailed",       dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="",
                                       agent="backend-engineer")),
        ("review_outputs_dir",    dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_summary_html",   dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_enhanced_html",  dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_detailed_html",  dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="",
                                       agent="backend-engineer")),
    ]
    for name, bindings in new_paths:
        result = resolve(name, **bindings)
        assert result.startswith("docs/shield"), f"{name} did not resolve cleanly: {result!r}"


def test_legacy_paths_resolve() -> None:
    """Legacy entries (pre-redesign) must resolve so lint can pass during Phase 3 cutover."""
    legacy_paths = [
        ("legacy_research_dir", dict(output_dir="docs/shield", feature="f",
                                     n="1", slug="my-topic")),
        ("legacy_plan_dir",     dict(output_dir="docs/shield", feature="f",
                                     n="1", slug="my-plan")),
    ]
    for name, bindings in legacy_paths:
        result = resolve(name, **bindings)
        assert result.startswith("docs/shield"), f"{name} did not resolve: {result!r}"
