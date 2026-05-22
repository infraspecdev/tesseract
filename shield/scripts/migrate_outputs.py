# shield/scripts/migrate_outputs.py
"""Migrate a Shield output tree from the legacy numbered-run layout to the
flat per-feature layout defined in
docs/superpowers/specs/2026-05-22-shield-output-structure-design.md.

Runnable: `uv run --with pyyaml shield/scripts/migrate_outputs.py [--root docs/shield] [--apply]`
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Patterns: (compiled regex on POSIX relpath, callable returning new relpath or None)
_RESEARCH_FINDINGS = re.compile(r"^research/\d+-[^/]+/findings\.md$")
_RESEARCH_TRANSCRIPT = re.compile(r"^research/\d+-[^/]+/transcript\.md$")
_PLAN_ARCH_HTML = re.compile(r"^plan/\d+-[^/]+/architecture\.html$")


def map_legacy_path(relpath: str) -> Optional[str]:
    """Map a path under {output_dir}/{feature}/ to its new location.

    Returns None if the path is already at its new location (no move needed) or
    is unrecognized (caller decides whether to warn).
    """
    if _RESEARCH_FINDINGS.match(relpath):
        return "research.md"
    if _RESEARCH_TRANSCRIPT.match(relpath):
        return ".session-transcript.md"
    if _PLAN_ARCH_HTML.match(relpath):
        return "outputs/plan-architecture.html"
    return None


# Files that are valid at the feature root in the new schema (no warning if seen here).
KNOWN_ROOT_FILES = {
    "README.md", "research.md", "prd.md", "plan.json", "plan.md",
    "plan-architecture.md", ".session-transcript.md",
}

# Subdirectories that are valid in the new schema (no warning if files are here).
KNOWN_SUBDIRS = {"outputs"}


def plan_moves(feature_dir: Path) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Walk a feature directory and return (moves, warnings).

    moves: list of (src, dst) absolute pairs to move.
    warnings: human-readable messages for files we don't recognize.
    """
    moves: list[tuple[Path, Path]] = []
    warnings: list[str] = []

    for path in sorted(feature_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(feature_dir).as_posix()
        target = map_legacy_path(rel)
        if target is not None:
            moves.append((path, feature_dir / target))
            continue
        # No mapping. Is it already-correct, or unrecognized?
        if "/" not in rel:
            if rel not in KNOWN_ROOT_FILES:
                warnings.append(f"{rel}: unrecognized file at feature root, left in place")
            # else: file is already at its correct location
        else:
            # Nested file. Check if it's in a known subdirectory (already migrated).
            top_dir = rel.split("/")[0]
            if top_dir not in KNOWN_SUBDIRS:
                # Not in a known subdir — warn.
                warnings.append(f"{rel}: unrecognized nested file, left in place")
            # else: file is already in a migrated location

    return moves, warnings


def apply_moves(moves: list[tuple[Path, Path]]) -> None:
    """Execute the moves and clean up empty parent directories."""
    parents_to_check: set[Path] = set()
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        parents_to_check.add(src.parent)

    # Sweep emptied numbered-run dirs and their parents (one level up).
    for p in sorted(parents_to_check, key=lambda x: len(x.as_posix()), reverse=True):
        if p.exists() and not any(p.iterdir()):
            p.rmdir()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()


# Artifact filenames the manifest tracks per feature (matches design §6.1).
TRACKED_ARTIFACTS = {
    "research":     "research.md",
    "prd":          "prd.md",
    "plan_json":    "plan.json",
    "plan_md":      "plan.md",
    "plan_arch_md": "plan-architecture.md",
    "readme":       "README.md",
}


def _summarize_reviews(feature_dir: Path, review_type: str) -> dict[str, str | int]:
    review_root = feature_dir / "reviews" / review_type
    if not review_root.exists():
        return {"count": 0}
    runs = sorted(d.name for d in review_root.iterdir() if d.is_dir())
    if not runs:
        return {"count": 0}
    return {"latest": runs[-1], "count": len(runs)}


def build_manifest(output_dir: Path) -> dict:
    """Walk {output_dir} and return a v2 manifest dict."""
    features: list[dict] = []
    for feature_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        if feature_dir.name == "outputs":
            continue  # global rendered output, not a feature
        artifacts = {
            key: (feature_dir / fname).exists()
            for key, fname in TRACKED_ARTIFACTS.items()
        }
        reviews = {
            rt: _summarize_reviews(feature_dir, rt)
            for rt in ("prd", "plan", "code")
        }
        features.append({
            "name": feature_dir.name,
            "artifacts": artifacts,
            "reviews": reviews,
            "updated": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        })
    return {"schema_version": 2, "features": features}
