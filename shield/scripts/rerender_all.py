#!/usr/bin/env python3
"""Re-render every Shield source markdown into the shared shell.

Walks {output_dir} for known source docs (and review summaries) and renders
each to its outputs/ HTML via render-markdown.sh + templates/shell.html, then
writes the shared assets. Idempotent — safe to re-run.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SHELL = SCRIPT_DIR.parent / "templates" / "shell.html"
RENDER_SH = SCRIPT_DIR / "render-markdown.sh"

# (source-md-relative-to-feature, output-html-relative-to-feature, title-prefix)
DOC_MAP = [
    ("research.md", "outputs/research.html", "Research"),
    ("prd.md", "outputs/prd.html", "PRD"),
    ("trd.md", "outputs/trd.html", "TRD"),
    ("plan.md", "outputs/plan.html", "Plan"),
    ("plan-architecture.md", "outputs/plan-architecture.html", "Architecture"),
]


def _render(md: Path, out: Path, title: str, output_dir: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(RENDER_SH), "--md", str(md), "--shell", str(SHELL),
         "--out", str(out), "--assets-root", str(output_dir), "--title", title],
        check=True,
    )


def rerender_all(output_dir: Path) -> int:
    count = 0
    for feature in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        if feature.name == "outputs":
            continue
        for src_name, out_rel, prefix in DOC_MAP:
            md = feature / src_name
            if md.is_file():
                _render(md, feature / out_rel, f"{prefix} — {feature.name}", output_dir)
                count += 1
        for summary in feature.glob("reviews/*/*/summary.md"):
            rel = summary.relative_to(feature).with_suffix(".html")
            _render(summary, feature / "outputs" / rel,
                    f"Review — {feature.name}", output_dir)
            count += 1
    print(f"rerender_all: rendered {count} page(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args()
    if not args.output_dir.is_dir():
        print(f"rerender_all: not a dir: {args.output_dir}", file=sys.stderr)
        return 2
    return rerender_all(args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
