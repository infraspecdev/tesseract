# shield/scripts/test_migrate_outputs.py
"""Tests for migrate_outputs.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from migrate_outputs import apply_moves, build_manifest, derive_review_date, git_dirty_paths, map_legacy_path, plan_moves  # type: ignore[import-not-found]


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


@pytest.mark.parametrize("old,new", [
    ("prd/1-foo/prd.md",          "prd.md"),
    ("prd/3-bar-baz-qux/prd.md",  "prd.md"),
])
def test_map_prd_md(old: str, new: str) -> None:
    assert map_legacy_path(old) == new


@pytest.mark.parametrize("old,new", [
    ("prd/1-foo/prd.html", "outputs/prd.html"),
])
def test_map_prd_html(old: str, new: str) -> None:
    assert map_legacy_path(old) == new


@pytest.mark.parametrize("old,new", [
    ("prd/1-foo/prd.meta.json", "prd.meta.json"),
])
def test_map_prd_meta_json(old: str, new: str) -> None:
    assert map_legacy_path(old) == new


@pytest.mark.parametrize("old,new", [
    ("plan/1-foo/plan.html", "outputs/plan.html"),
])
def test_map_plan_html(old: str, new: str) -> None:
    assert map_legacy_path(old) == new


def test_derive_review_date_from_dir_mtime(tmp_path: Path) -> None:
    d = tmp_path / "prd-review" / "1-foo"
    d.mkdir(parents=True)
    (d / "summary.md").write_text("x")
    ts = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    os.utime(d, (ts, ts))
    assert derive_review_date(d) == "2026-04-30"


def test_prd_review_folder_migrates_to_dated_dir(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    rev = feature / "prd-review" / "1-myslug"
    rev.mkdir(parents=True)
    (rev / "summary.md").write_text("s")
    (rev / "enhanced-prd.md").write_text("e")
    (rev / "source-prd.md").write_text("src")
    (rev / "review-comments.json").write_text("{}")
    detailed = rev / "detailed"
    detailed.mkdir()
    (detailed / "agile-coach.md").write_text("a")
    (detailed / "tech-lead-reviewer.md").write_text("t")

    ts = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    os.utime(rev, (ts, ts))

    moves, _warnings = plan_moves(feature)
    dst_paths = {dst.relative_to(feature).as_posix() for _src, dst in moves}

    expected = {
        "reviews/prd/2026-04-30/summary.md",
        "reviews/prd/2026-04-30/enhanced-prd.md",
        "reviews/prd/2026-04-30/source-prd.md",
        "reviews/prd/2026-04-30/review-comments.json",
        "reviews/prd/2026-04-30/detailed/agile-coach.md",
        "reviews/prd/2026-04-30/detailed/tech-lead-reviewer.md",
    }
    assert expected.issubset(dst_paths)


def test_plan_review_folder_migrates_to_dated_dir(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    rev = feature / "plan-review" / "1-foo"
    rev.mkdir(parents=True)
    (rev / "summary.md").write_text("s")
    (rev / "enhanced-plan.md").write_text("e")
    detailed = rev / "detailed"
    detailed.mkdir()
    (detailed / "backend-engineer.md").write_text("b")

    ts = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    os.utime(rev, (ts, ts))

    moves, _ = plan_moves(feature)
    dst_paths = {dst.relative_to(feature).as_posix() for _src, dst in moves}
    expected = {
        "reviews/plan/2026-05-21/summary.md",
        "reviews/plan/2026-05-21/enhanced-plan.md",
        "reviews/plan/2026-05-21/detailed/backend-engineer.md",
    }
    assert expected.issubset(dst_paths)


def test_same_day_review_folders_get_counter(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    for i, slug in enumerate(["1-first", "2-second"]):
        d = feature / "prd-review" / slug
        d.mkdir(parents=True)
        (d / "summary.md").write_text(f"r{i}")
        ts = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()
        os.utime(d, (ts, ts))

    moves, _ = plan_moves(feature)
    dst_dirs = {dst.parent.relative_to(feature).as_posix() for _, dst in moves}
    assert "reviews/prd/2026-04-30" in dst_dirs
    assert "reviews/prd/2026-04-30_2" in dst_dirs


def _make_realistic_tree(root: Path) -> Path:
    """Build a synthetic feature tree shaped like a real shield-managed project."""
    feature = root / "bill-payments-platform-20260430"
    files = {
        "plan.json": '{"epics": []}',
        "research/1-platform-foundations/findings.md": "platform foundations findings",
        "research/2-multi-geo-data-and-execution-residency/findings.md": "multi-geo findings",
        "prd/1-bill-payments-platform-v2/prd.md": "# PRD body",
        "prd/1-bill-payments-platform-v2/prd.html": "<html>PRD</html>",
        "prd/1-bill-payments-platform-v2/prd.meta.json": '{"version": 2}',
        "prd-review/1-bill-payments-platform-v2/summary.md": "# Summary",
        "prd-review/1-bill-payments-platform-v2/enhanced-prd.md": "# Enhanced PRD",
        "prd-review/1-bill-payments-platform-v2/source-prd.md": "# Source snapshot",
        "prd-review/1-bill-payments-platform-v2/review-comments.json": '{"comments": []}',
        "prd-review/1-bill-payments-platform-v2/detailed/agile-coach.md": "agile findings",
        "prd-review/1-bill-payments-platform-v2/detailed/tech-lead-reviewer.md": "tech findings",
        "plan/1-prd-v2-foundation/architecture.html": "<html>arch</html>",
        "plan/1-prd-v2-foundation/plan.html": "<html>plan</html>",
        "plan-review/1-bill-payments-platform/detailed/architecture-reviewer.md": "arch reviewer",
        "plans/product-note.md": "side note",
    }
    for relpath, content in files.items():
        p = feature / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return feature


def test_realistic_tree_full_migration(tmp_path: Path) -> None:
    feature = _make_realistic_tree(tmp_path)

    # Force the older research folder to be older than the newer one for collision resolution.
    older = feature / "research/1-platform-foundations/findings.md"
    newer = feature / "research/2-multi-geo-data-and-execution-residency/findings.md"
    os.utime(older, (1700000000, 1700000000))
    os.utime(newer, (1800000000, 1800000000))

    moves, warnings = plan_moves(feature)
    dst_paths = {dst.relative_to(feature).as_posix() for _, dst in moves}

    assert "prd.md" in dst_paths
    assert "outputs/prd.html" in dst_paths
    assert "prd.meta.json" in dst_paths
    assert "outputs/plan-architecture.html" in dst_paths
    assert "outputs/plan.html" in dst_paths

    review_dirs = {p for p in dst_paths if p.startswith("reviews/")}
    assert any("reviews/prd/" in p and "/summary.md" in p for p in review_dirs)
    assert any("reviews/plan/" in p and "/detailed/architecture-reviewer.md" in p for p in review_dirs)

    research_targets = [p for p in dst_paths if p == "research.md"]
    assert len(research_targets) == 1
    assert any("discarded on collision" in w for w in warnings)

    assert any("plans/product-note.md" in w for w in warnings)


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


def test_build_manifest_v2_structure(tmp_path: Path) -> None:
    output_dir = tmp_path / "docs" / "shield"
    feature = output_dir / "vpc-20260322"
    _make_tree(feature, [
        "research.md",
        "plan.json",
        "reviews/plan/2026-05-21/summary.md",
        "reviews/plan/2026-05-21_2/summary.md",
        "reviews/code/2026-05-22/summary.md",
    ])

    manifest = build_manifest(output_dir)

    assert manifest["schema_version"] == "2.1"
    assert len(manifest["features"]) == 1
    feat = manifest["features"][0]
    assert feat["name"] == "vpc-20260322"
    assert feat["artifacts"]["research"] is True
    assert feat["artifacts"]["plan_json"] is True
    assert feat["artifacts"]["prd"] is False
    assert feat["reviews"]["plan"] == {
        "latest": "2026-05-21_2",
        "count": 2,
        "entries": [
            {"date": "2026-05-21",
             "path": "vpc-20260322/outputs/reviews/plan/2026-05-21/summary.html"},
            {"date": "2026-05-21_2",
             "path": "vpc-20260322/outputs/reviews/plan/2026-05-21_2/summary.html"},
        ],
    }
    assert feat["reviews"]["code"] == {
        "latest": "2026-05-22",
        "count": 1,
        "entries": [
            {"date": "2026-05-22",
             "path": "vpc-20260322/outputs/reviews/code/2026-05-22/summary.html"},
        ],
    }
    assert "prd" not in feat["reviews"] or feat["reviews"]["prd"]["count"] == 0


def test_cli_dry_run_does_not_move(tmp_path: Path) -> None:
    output_dir = tmp_path / "docs" / "shield"
    feature = output_dir / "vpc-20260322"
    _make_tree(feature, ["research/1-claude-isolation/findings.md"])

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"), "--root", str(output_dir)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    # Dry-run: file should still be at old location
    assert (feature / "research" / "1-claude-isolation" / "findings.md").exists()
    assert not (feature / "research.md").exists()
    assert "dry-run" in result.stdout.lower() or "would move" in result.stdout.lower()


def test_plan_moves_reviews_subdir_no_warning(tmp_path: Path) -> None:
    """Files under reviews/ should not produce unrecognized-nested-file warnings."""
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, [
        "research.md",
        "plan.json",
        "reviews/plan/2026-05-21/summary.md",
    ])
    moves, warnings = plan_moves(feature)
    assert moves == []
    assert warnings == [], f"Expected no warnings but got: {warnings}"


def test_cli_apply_moves_and_writes_manifest(tmp_path: Path) -> None:
    output_dir = tmp_path / "docs" / "shield"
    feature = output_dir / "vpc-20260322"
    _make_tree(feature, ["research/1-claude-isolation/findings.md", "plan.json"])

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"),
         "--root", str(output_dir), "--apply"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (feature / "research.md").exists()
    assert (output_dir / "manifest.json").exists()
    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["schema_version"] == "2.1"


def test_plan_moves_returns_collision_resolutions(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    _make_tree(feature, [
        "research/1-old/findings.md",
        "research/2-new/findings.md",
    ])
    older = feature / "research/1-old/findings.md"
    newer = feature / "research/2-new/findings.md"
    os.utime(older, (1700000000, 1700000000))
    os.utime(newer, (1800000000, 1800000000))

    moves, warnings = plan_moves(feature)
    moves_to_research = [
        (src, dst) for src, dst in moves
        if dst.name == "research.md"
    ]
    assert len(moves_to_research) == 1
    chosen_src, _ = moves_to_research[0]
    assert chosen_src == newer, f"Expected newer file to win; got {chosen_src}"

    discard_warnings = [w for w in warnings if "discarded" in w.lower() and "1-old" in w]
    assert len(discard_warnings) == 1, f"Expected one discard warning; got {warnings!r}"


def test_cli_dry_run_logs_collision_discard(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    _make_tree(feature, [
        "research/1-old/findings.md",
        "research/2-new/findings.md",
    ])
    older = feature / "research/1-old/findings.md"
    newer = feature / "research/2-new/findings.md"
    os.utime(older, (1700000000, 1700000000))
    os.utime(newer, (1800000000, 1800000000))

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"), "--root", str(tmp_path)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    out = result.stdout + result.stderr
    assert "discarded on collision" in out
    assert "1-old" in out


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def test_git_dirty_paths_clean_repo(tmp_path: Path) -> None:
    _git_init(tmp_path)
    (tmp_path / "a.md").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    assert git_dirty_paths(tmp_path) == []


def test_git_dirty_paths_with_uncommitted(tmp_path: Path) -> None:
    _git_init(tmp_path)
    (tmp_path / "a.md").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "b.md").write_text("b")
    dirty = git_dirty_paths(tmp_path)
    assert dirty is not None
    assert any("b.md" in line for line in dirty)


def test_git_dirty_paths_non_git_returns_none(tmp_path: Path) -> None:
    assert git_dirty_paths(tmp_path) is None


def test_apply_with_dirty_tree_aborts_without_yes(tmp_path: Path) -> None:
    _git_init(tmp_path)
    feature = tmp_path / "f"
    _make_tree(feature, ["research/1-foo/findings.md"])
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "untracked.md").write_text("dirty")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"),
         "--root", str(tmp_path), "--apply"],
        capture_output=True, text=True, check=False,
        input="",
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "dirty" in combined or "uncommitted" in combined
    assert (feature / "research/1-foo/findings.md").exists()
    assert not (feature / "research.md").exists()


def test_apply_with_dirty_tree_proceeds_with_yes(tmp_path: Path) -> None:
    _git_init(tmp_path)
    feature = tmp_path / "f"
    _make_tree(feature, ["research/1-foo/findings.md"])
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "untracked.md").write_text("dirty")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"),
         "--root", str(tmp_path), "--apply", "--yes"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (feature / "research.md").exists()
