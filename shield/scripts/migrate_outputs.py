# shield/scripts/migrate_outputs.py
"""Migrate a Shield output tree from the legacy numbered-run layout to the
flat per-feature layout defined in
docs/superpowers/specs/2026-05-22-shield-output-structure-design.md.

Runnable: `uv run --with pyyaml shield/scripts/migrate_outputs.py [--root docs/shield] [--apply]`
"""
from __future__ import annotations

import re
import sys
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
            # Nested file that's not a legacy pattern — warn.
            warnings.append(f"{rel}: unrecognized nested file, left in place")

    return moves, warnings
