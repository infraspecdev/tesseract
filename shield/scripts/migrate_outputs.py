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
KNOWN_SUBDIRS = {"outputs", "reviews"}


def plan_moves(feature_dir: Path) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Walk a feature directory and return (moves, warnings).

    On destination collisions, the latest-mtime source wins; older sources are
    discarded with a warning (their content remains recoverable via git history
    of the source path, provided the source tree was committed before migration).
    """
    raw_moves: list[tuple[Path, Path]] = []
    warnings: list[str] = []

    for path in sorted(feature_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(feature_dir).as_posix()
        target = map_legacy_path(rel)
        if target is not None:
            raw_moves.append((path, feature_dir / target))
            continue
        if "/" not in rel:
            if rel not in KNOWN_ROOT_FILES:
                warnings.append(f"{rel}: unrecognized file at feature root, left in place")
        else:
            top_dir = rel.split("/")[0]
            if top_dir not in KNOWN_SUBDIRS:
                warnings.append(f"{rel}: unrecognized nested file, left in place")

    by_dst: dict[Path, list[Path]] = {}
    for src, dst in raw_moves:
        by_dst.setdefault(dst, []).append(src)

    resolved: list[tuple[Path, Path]] = []
    for dst, srcs in by_dst.items():
        if len(srcs) == 1:
            resolved.append((srcs[0], dst))
            continue
        srcs_sorted = sorted(srcs, key=lambda p: p.stat().st_mtime, reverse=True)
        winner = srcs_sorted[0]
        resolved.append((winner, dst))
        for loser in srcs_sorted[1:]:
            rel_loser = loser.relative_to(feature_dir).as_posix()
            rel_winner = winner.relative_to(feature_dir).as_posix()
            rel_dst = dst.relative_to(feature_dir).as_posix()
            warnings.append(
                f"{rel_loser}: discarded on collision (newer {rel_winner} wins for {rel_dst})"
            )

    return resolved, warnings


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


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Migrate Shield output tree to new flat layout."
    )
    parser.add_argument("--root", default="docs/shield",
                        help="Output directory to migrate (default: docs/shield)")
    parser.add_argument("--apply", action="store_true",
                        help="Actually move files (default: dry-run)")
    args = parser.parse_args(argv)

    output_dir = Path(args.root).resolve()
    if not output_dir.exists():
        print(f"error: --root {output_dir} does not exist", file=sys.stderr)
        return 2

    total_moves = 0
    total_warnings = 0

    for feature_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        if feature_dir.name == "outputs":
            continue
        moves, warnings = plan_moves(feature_dir)
        for src, dst in moves:
            rel_src = src.relative_to(output_dir).as_posix()
            rel_dst = dst.relative_to(output_dir).as_posix()
            verb = "moving" if args.apply else "would move"
            print(f"{verb}: {rel_src} -> {rel_dst}")
        for w in warnings:
            print(f"warning: {feature_dir.name}/{w}")
        if args.apply:
            apply_moves(moves)
        total_moves += len(moves)
        total_warnings += len(warnings)

    if args.apply:
        manifest = build_manifest(output_dir)
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"wrote manifest: {output_dir / 'manifest.json'}")

    mode = "applied" if args.apply else "dry-run"
    print(f"{mode}: {total_moves} moves, {total_warnings} warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
