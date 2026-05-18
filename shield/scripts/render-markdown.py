#!/usr/bin/env python3
"""Render a markdown file into an HTML shell.

The shell is an HTML file containing a literal `{{BODY}}` placeholder
(mandatory) and an optional literal `{{TOC}}` placeholder. This script
reads the markdown, renders it with a CommonMark-strict parser
(markdown-it-py) plus the `tables`, `strikethrough`, and `anchors`
extensions, builds a Table of Contents from h2/h3 headings, and writes
the shell with placeholders substituted. Mermaid fences (info string
`mermaid`) are emitted as `<pre class="mermaid">...</pre>` so mermaid.js
can render them client-side.

Invocation contract is owned by render-markdown.sh — see that file.
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin


BODY_PLACEHOLDER = "{{BODY}}"
TOC_PLACEHOLDER = "{{TOC}}"


def _make_parser() -> MarkdownIt:
    md = (
        MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": False})
        .enable("table")
        .enable("strikethrough")
        .use(anchors_plugin, min_level=1, max_level=4, permalink=False)
    )
    _override_mermaid_fence(md)
    return md


def _override_mermaid_fence(md: MarkdownIt) -> None:
    """Render ```mermaid fences as <pre class="mermaid">…</pre> (no <code>)."""
    default_fence = md.renderer.rules.get("fence")

    def fence(tokens, idx, options, env):
        token = tokens[idx]
        if token.info.strip().lower() == "mermaid":
            return f'<pre class="mermaid">{html.escape(token.content)}</pre>\n'
        if default_fence is not None:
            return default_fence(tokens, idx, options, env)
        return f'<pre><code>{html.escape(token.content)}</code></pre>\n'

    md.renderer.rules["fence"] = fence


def _collect_toc_entries(tokens: list) -> list[tuple[int, str, str]]:
    """Return list of (level, text, anchor_id) for h2/h3 in document order."""
    entries = []
    for i, tok in enumerate(tokens):
        if tok.type != "heading_open":
            continue
        level = int(tok.tag[1:])
        if level not in (2, 3):
            continue
        anchor_id = tok.attrGet("id") or ""
        text = ""
        if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
            inline_tok = tokens[i + 1]
            text = "".join(
                c.content
                for c in (inline_tok.children or [])
                if c.type in ("text", "code_inline", "softbreak")
            ).replace("\n", " ")
        entries.append((level, text, anchor_id))
    return entries


def _build_toc_html(entries: list[tuple[int, str, str]]) -> str:
    """Build a <nav class='toc'> tree. Empty input → ''."""
    if not entries:
        return ""
    parts = ['<nav class="toc">', '<div class="toc-title">Contents</div>', '<ul>']
    in_h2_li = False
    in_h3_ul = False
    for level, text, anchor in entries:
        safe_text = html.escape(text)
        href = f"#{anchor}" if anchor else "#"
        if level == 2:
            if in_h3_ul:
                parts.append("</ul>")
                in_h3_ul = False
            if in_h2_li:
                parts.append("</li>")
            parts.append(f'<li><a href="{href}">{safe_text}</a>')
            in_h2_li = True
        else:  # level == 3
            if not in_h2_li:
                # orphan: self-contained <li>, no open state to track
                parts.append(f'<li><a href="{href}">{safe_text}</a></li>')
                continue
            if not in_h3_ul:
                parts.append("<ul>")
                in_h3_ul = True
            parts.append(f'<li><a href="{href}">{safe_text}</a></li>')
    if in_h3_ul:
        parts.append("</ul>")
    if in_h2_li:
        parts.append("</li>")
    parts.append("</ul>")
    parts.append("</nav>")
    return "\n".join(parts)


def render(md_text: str) -> tuple[str, str]:
    """Return (toc_html, body_html). toc_html is '' when no h2/h3 found."""
    md = _make_parser()
    env: dict = {}
    tokens = md.parse(md_text, env)
    body = md.renderer.render(tokens, md.options, env)
    toc = _build_toc_html(_collect_toc_entries(tokens))
    return toc, body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--md", required=True, type=Path, help="Input Markdown file")
    parser.add_argument("--shell", required=True, type=Path,
        help="HTML shell containing {{BODY}} (mandatory) and optional {{TOC}} placeholder")
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

    toc, body = render(args.md.read_text())
    out = shell
    if TOC_PLACEHOLDER in out:
        out = out.replace(TOC_PLACEHOLDER, toc)
    out = out.replace(BODY_PLACEHOLDER, body)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
