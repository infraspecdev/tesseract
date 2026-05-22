# shield/scripts/test_migrate_outputs.py
"""Tests for migrate_outputs.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from migrate_outputs import apply_moves, map_legacy_path, plan_moves  # type: ignore[import-not-found]


@pytest.mark.parametrize("old,new", [
    # research findings → research.md
    ("research/1-claude-isolation/findings.md", "research.md"),
    ("research/2-rerun/findings.md",            "research.md"),
    # session transcripts → hidden file
    ("research/1-claude-isolation/transcript.md", ".session-transcript.md"),
    # plan architecture HTML → outputs/
    ("plan/1-foo/architecture.html", "outputs/plan-architecture.html"),
    # files already at root → unchanged (None signals "no move needed")
    ("plan.json", None),
    ("handoff.md", None),
    ("README.md", None),
])
def test_map_legacy_path(old: str, new: str | None) -> None:
    assert map_legacy_path(old) == new


def _make_tree(root: Path, files: list[str]) -> None:
    for f in files:
        path = root / f
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content of " + f)


def test_plan_moves_typical_feature_tree(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, [
        "research/1-claude-isolation/findings.md",
        "research/1-claude-isolation/transcript.md",
        "plan.json",
        "plan/1-foo/architecture.html",
        "handoff.md",
    ])
    moves, warnings = plan_moves(feature)

    moves_set = {(src.relative_to(feature).as_posix(),
                  dst.relative_to(feature).as_posix())
                 for src, dst in moves}
    assert moves_set == {
        ("research/1-claude-isolation/findings.md",   "research.md"),
        ("research/1-claude-isolation/transcript.md", ".session-transcript.md"),
        ("plan/1-foo/architecture.html",              "outputs/plan-architecture.html"),
    }

    # handoff.md is unrecognized (under root, not in legacy patterns) → warning
    warning_paths = {w.split(":")[0] for w in warnings}
    assert "handoff.md" in warning_paths


def test_plan_moves_already_migrated_tree(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, ["research.md", "plan.json", "prd.md"])
    moves, warnings = plan_moves(feature)
    assert moves == []
    # Already-flat files at root that aren't in the new schema would warn, but research/prd/plan_json are.
    assert warnings == []


def test_apply_moves_executes(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, [
        "research/1-claude-isolation/findings.md",
        "research/1-claude-isolation/transcript.md",
        "plan/1-foo/architecture.html",
    ])
    moves, _ = plan_moves(feature)
    apply_moves(moves)

    assert (feature / "research.md").exists()
    assert (feature / ".session-transcript.md").exists()
    assert (feature / "outputs" / "plan-architecture.html").exists()
    # Sources should be gone
    assert not (feature / "research" / "1-claude-isolation" / "findings.md").exists()


def test_apply_moves_removes_empty_dirs(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, ["research/1-claude-isolation/findings.md"])
    moves, _ = plan_moves(feature)
    apply_moves(moves)

    # The numbered-run folder and its parent should be cleaned up if empty
    assert not (feature / "research").exists() or not any((feature / "research").iterdir())


def test_apply_then_plan_is_noop(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, [
        "research/1-claude-isolation/findings.md",
        "plan/1-foo/architecture.html",
    ])
    moves1, _ = plan_moves(feature)
    apply_moves(moves1)

    # Second pass: nothing to migrate
    moves2, warnings2 = plan_moves(feature)
    assert moves2 == []
    assert warnings2 == []
