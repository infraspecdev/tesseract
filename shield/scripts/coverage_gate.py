#!/usr/bin/env -S uv run --with coverage --script
"""Patch-coverage gate for Shield Python packages.

Parses a coverage.xml file emitted by pytest --cov --cov-report=xml,
diffs against a base git ref to identify patch lines, then fails if the
fraction of patch lines covered is below the configured threshold.

Usage:
    uv run --with coverage shield/scripts/coverage_gate.py \\
        --xml shield/parsers/coverage.xml \\
        --threshold 95 \\
        --base-ref main
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _parse_covered_lines(xml_path: Path) -> dict[str, set[int]]:
    """Return {filename: {covered_line_numbers}} from coverage.xml."""
    tree = ET.parse(xml_path)
    out: dict[str, set[int]] = {}
    for cls in tree.iter("class"):
        filename = cls.get("filename")
        if filename is None:
            continue
        covered: set[int] = set()
        for line in cls.iter("line"):
            try:
                lineno = int(line.get("number", "0"))
                hits = int(line.get("hits", "0"))
            except ValueError:
                continue
            if hits > 0:
                covered.add(lineno)
        out.setdefault(filename, set()).update(covered)
    return out


def _patch_lines(base_ref: str) -> dict[str, set[int]]:
    """Return {filename: {added_or_modified_line_numbers}} relative to base_ref."""
    result = subprocess.run(
        ["git", "diff", "--unified=0", f"{base_ref}...HEAD"],
        capture_output=True, text=True, check=True,
    )
    out: dict[str, set[int]] = {}
    current_file: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            out.setdefault(current_file, set())
        elif line.startswith("@@") and current_file is not None:
            # @@ -X,Y +A,B @@   — pull A and B from the +A,B segment.
            after = line.split("+", 1)[1].split(" ", 1)[0]
            if "," in after:
                start_str, count_str = after.split(",")
                start, count = int(start_str), int(count_str)
            else:
                start, count = int(after), 1
            for ln in range(start, start + count):
                out[current_file].add(ln)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--xml", required=True, type=Path, help="coverage.xml path")
    p.add_argument("--threshold", required=True, type=float,
                   help="Minimum % of patch lines that must be covered")
    p.add_argument("--base-ref", default="main",
                   help="Git ref to diff against (default: main)")
    args = p.parse_args()

    covered = _parse_covered_lines(args.xml)
    patch = _patch_lines(args.base_ref)

    total_patch = 0
    total_covered = 0
    uncovered: list[tuple[str, int]] = []

    for filename, lines in patch.items():
        if not filename.endswith(".py"):
            continue
        # Match coverage paths (which are package-relative) against git paths
        # (which are repo-relative).
        cov_for_file = next(
            (cov for path, cov in covered.items() if filename.endswith(path)),
            set(),
        )
        for ln in lines:
            total_patch += 1
            if ln in cov_for_file:
                total_covered += 1
            else:
                uncovered.append((filename, ln))

    if total_patch == 0:
        print("No Python patch lines in scope — gate skipped.")
        return 0

    pct = 100.0 * total_covered / total_patch
    print(f"Patch coverage: {total_covered}/{total_patch} ({pct:.1f}%); "
          f"threshold {args.threshold:.1f}%")

    if pct < args.threshold:
        print(f"FAIL: patch coverage {pct:.1f}% < threshold {args.threshold:.1f}%")
        print("Uncovered patch lines:")
        for f, ln in sorted(uncovered):
            print(f"  {f}:{ln}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
