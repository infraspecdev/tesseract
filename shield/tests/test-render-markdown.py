#!/usr/bin/env python3
"""Regression test for shield/scripts/render-markdown.{sh,py}.

Three pathological markdown patterns that hand-rendered PRDs got wrong
and that python-markdown (3.x default extensions) also flattens. The
helper script must produce correct CommonMark output for all three.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

SHIELD_ROOT = Path(__file__).resolve().parent.parent
HELPER = SHIELD_ROOT / "scripts" / "render-markdown.sh"

FIXTURE_MD = """\
# Test fixture

## Case A: nested numbered list inside bullet

- **Happy path:**
  1. First step.
  2. Second step.
  3. Third step.
- **Other item.**

## Case B: list immediately after emphasised paragraph

Some intro paragraph here.

**Dashboard plan:**
- Item one.
- Item two.
- Item three.

## Case C: mixed loose/tight list spacing

- Tight item one.
- Tight item two.

  This item has a blank line above it, making the whole list loose.
- Tight-looking item three.
"""

SHELL_HTML = """\
<!doctype html>
<html><head><meta charset="utf-8"><title>t</title></head>
<body>{{BODY}}</body></html>
"""


def fail(msg: str, body: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    print("--- rendered body ---", file=sys.stderr)
    print(body, file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if not HELPER.is_file():
        print(f"FAIL: helper not found: {HELPER}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        md_path = tmp / "in.md"
        shell_path = tmp / "shell.html"
        out_path = tmp / "out.html"
        md_path.write_text(FIXTURE_MD)
        shell_path.write_text(SHELL_HTML)

        result = subprocess.run(
            [
                str(HELPER),
                "--md", str(md_path),
                "--shell", str(shell_path),
                "--out", str(out_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("FAIL: helper exited non-zero", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return 1
        if not out_path.is_file():
            print("FAIL: helper did not produce --out file", file=sys.stderr)
            return 1

        html = out_path.read_text()

        # Case A: must have <ol> nested inside an <li> of the parent <ul>.
        case_a = re.search(
            r"<li>(?:<p>)?\s*<strong>Happy path:</strong>.*?<ol>\s*<li>First step\.</li>",
            html,
            re.DOTALL,
        )
        if not case_a:
            fail("Case A — nested <ol> inside <li> not found", html)

        # Case B: list-after-paragraph must become its own <ul>, not
        # literal "- " text inside a <p>.
        if re.search(r"<p>[^<]*<strong>Dashboard plan:</strong>\s*\n?-\s+Item", html):
            fail("Case B — bullets leaked into <p> as literal text", html)
        case_b_ul = re.search(
            r"<p><strong>Dashboard plan:</strong></p>\s*<ul>\s*<li>Item one\.",
            html,
        )
        if not case_b_ul:
            fail("Case B — expected <p>...</p><ul><li>Item one... not found", html)

        # Case C: when any item is loose, every <li> in the list must be
        # wrapped in <p> (CommonMark loose-list rule). Find the Case-C
        # <ul> by anchoring on the unique first item.
        case_c_match = re.search(
            r"<ul>\s*<li>\s*(?:<p>)?Tight item one\.(?:</p>)?.*?</ul>",
            html,
            re.DOTALL,
        )
        if not case_c_match:
            fail("Case C — could not locate Case-C list in output", html)
        case_c_ul = case_c_match.group(0)
        items = re.findall(r"<li>(.*?)</li>", case_c_ul, re.DOTALL)
        if len(items) != 3:
            fail(f"Case C — expected 3 items, got {len(items)}: {items!r}", html)
        wrapped = [bool(re.match(r"\s*<p>", item)) for item in items]
        if not all(wrapped):
            fail(
                f"Case C — loose-list rule violated: <p>-wrapping is {wrapped}",
                html,
            )

        # Smoke: heading anchors are emitted.
        if not re.search(r'<h2 id="case-a[^"]*">Case A:', html):
            fail("heading anchors missing (anchors plugin not active?)", html)

    print("PASS: render-markdown handles all three CommonMark cases correctly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
