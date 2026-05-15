#!/usr/bin/env python3
"""Parse an eval markdown file into discrete artifacts for run-eval.sh."""
from __future__ import annotations

import re
import sys
from pathlib import Path

def split_sections(text):
    """Split markdown by ## headings, returning {heading-slug: body}.

    Tracks fenced code blocks so that ## headings inside a fence are NOT
    treated as section boundaries (needed for eval files whose Setup blocks
    contain heredocs with sub-headings like '## Glossary').
    """
    sections = {}
    current_key = None
    current_lines = []
    in_fence = False
    for line in text.splitlines():
        # Toggle fence state when we see a line starting with ```
        if re.match(r"^```", line):
            in_fence = not in_fence
        if not in_fence:
            m = re.match(r"^## +(.+)$", line)
            if m:
                if current_key is not None:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = m.group(1).strip().lower()
                current_lines = []
                continue
        current_lines.append(line)
    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()
    return sections


def extract_code_block(body, fence_lang=""):
    """Extract first fenced code block of given lang (or any if blank)."""
    pattern = rf"```{fence_lang}\n(.*?)```" if fence_lang else r"```[a-z]*\n(.*?)```"
    m = re.search(pattern, body, re.DOTALL)
    return m.group(1) if m else ""


def main():
    eval_file = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    text = eval_file.read_text()
    sections = split_sections(text)

    # setup -> setup.sh
    setup_body = sections.get("setup", "")
    setup_sh = extract_code_block(setup_body, "bash") or setup_body
    (out_dir / "setup.sh").write_text(setup_sh)

    # prompt -> prompt.txt (strip leading "> " markers if blockquote)
    prompt_body = sections.get("prompt", "")
    prompt = "\n".join(l.lstrip("> ").rstrip() for l in prompt_body.splitlines() if l.strip())
    (out_dir / "prompt.txt").write_text(prompt)

    # success criteria -> structural.txt and qualitative.txt
    crit_body = sections.get("success criteria", "")
    structural = []
    qualitative = []
    current_bucket = None
    for line in crit_body.splitlines():
        if re.match(r"^### +Structural", line, re.I):
            current_bucket = structural
            continue
        if re.match(r"^### +Qualitative", line, re.I):
            current_bucket = qualitative
            continue
        m = re.match(r"^- +(.+)$", line)
        if m and current_bucket is not None:
            current_bucket.append(m.group(1).strip())
    (out_dir / "structural.txt").write_text("\n".join(structural) + "\n")
    (out_dir / "qualitative.txt").write_text("\n".join(qualitative) + "\n")

    # pass threshold
    threshold = sections.get("pass threshold", "all").strip()
    (out_dir / "threshold.txt").write_text(threshold)


if __name__ == "__main__":
    main()
