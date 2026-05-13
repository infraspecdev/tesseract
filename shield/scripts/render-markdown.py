#!/usr/bin/env python3
"""Render a markdown file into an HTML shell.

The shell is an HTML file containing a literal `{{BODY}}` placeholder.
This script reads the markdown, renders it with a CommonMark-strict
parser (markdown-it-py) plus the `tables`, `strikethrough`, and
`anchors` extensions, and writes the shell with `{{BODY}}` replaced by
the rendered body HTML.

Why CommonMark-strict: python-markdown and ad-hoc hand-rendering have
historically mis-rendered three patterns common in Shield PRDs:
  1. Numbered sub-lists nested under bulleted parents (`- foo\\n  1. bar`)
     get flattened.
  2. Lists immediately following an emphasised paragraph (no blank
     line) get swallowed into the paragraph as literal text.
  3. Mixed loose/tight list spacing produces inconsistent <li><p>...
     wrapping within the same list.
markdown-it-py implements the CommonMark spec for these cases.

Invocation contract is owned by render-markdown.sh — see that file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin


BODY_PLACEHOLDER = "{{BODY}}"


def render_body(md_text: str) -> str:
    md = (
        MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": False})
        .enable("table")
        .enable("strikethrough")
        .use(anchors_plugin, min_level=1, max_level=4, permalink=False)
    )
    return md.render(md_text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--md", required=True, type=Path, help="Input markdown file")
    parser.add_argument(
        "--shell",
        required=True,
        type=Path,
        help="HTML shell file containing a literal {{BODY}} placeholder",
    )
    parser.add_argument("--out", required=True, type=Path, help="Output HTML file")
    args = parser.parse_args()

    if not args.md.is_file():
        print(f"render-markdown: --md not found: {args.md}", file=sys.stderr)
        return 2
    if not args.shell.is_file():
        print(f"render-markdown: --shell not found: {args.shell}", file=sys.stderr)
        return 2

    shell = args.shell.read_text()
    if BODY_PLACEHOLDER not in shell:
        print(
            f"render-markdown: shell file is missing {BODY_PLACEHOLDER!r}: {args.shell}",
            file=sys.stderr,
        )
        return 2

    body = render_body(args.md.read_text())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(shell.replace(BODY_PLACEHOLDER, body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
