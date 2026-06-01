#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""check_plan_review_trd.py — deterministic gates 0a–0e from /plan-review.

This script runs the gates that are too dynamic for `validate_trd.py` alone
(stale-anchor lookup, PRD↔TRD duplication, implementation-manual rule). It
emits the same named error codes documented in
`shield/skills/general/plan-review/SKILL.md` so eval fixtures can assert
against them.

Exit codes:
  0  — all gates passed.
  1  — at least one gate produced a Critical finding.
  2  — usage error.

Named findings (stderr prefix on FAIL):
  stale_anchor:<story_id>:<slug>     — design_refs[] points at an anchor missing from trd.md
  prd_trd_duplication:<section>:<n>  — TRD section restates PRD verbatim (n chars overlap)
  implementation_manual:<lines>      — TRD §7 code block N lines without §8 rationale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SECTIONS_YAML = REPO_ROOT / "shield" / "schema" / "trd-sections.yaml"

DUPLICATION_THRESHOLD = 80
CODE_BLOCK_THRESHOLD = 20

ANCHOR_RE = re.compile(r"\{#([a-z0-9-]+)\}")
SECTION_HEADER_RE = re.compile(r"^##\s+(?:§\s*\d+\s+)?(.+?)\s*\{#([a-z0-9-]+)\}\s*$", re.MULTILINE)


def _emit(severity: str, code: str) -> None:
    print(f"{severity}: {code}", file=sys.stderr)


def _slugs_in_trd(text: str) -> set[str]:
    return set(ANCHOR_RE.findall(text))


def _section_body(text: str, slug: str) -> str:
    """Return the body of the section with the given slug, or empty string."""
    matches = list(SECTION_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        if m.group(2) == slug:
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[start:end]
    return ""


def _longest_common_substring(a: str, b: str) -> int:
    """Return length of longest common substring (case-insensitive,
    whitespace-collapsed). Naive O(n*m) — fine for the 14-section TRD sizes."""
    a = re.sub(r"\s+", " ", a.lower()).strip()
    b = re.sub(r"\s+", " ", b.lower()).strip()
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 0
    # Use space-efficient rolling table.
    best = 0
    prev = [0] * (m + 1)
    for i in range(1, n + 1):
        curr = [0] * (m + 1)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
                if curr[j] > best:
                    best = curr[j]
        prev = curr
    return best


def _check_stale_anchors(plan: dict[str, Any], trd_slugs: set[str]) -> list[str]:
    findings: list[str] = []
    for epic in plan.get("epics") or []:
        for story in epic.get("stories") or []:
            for ref in story.get("design_refs") or []:
                if ref.get("stale"):
                    findings.append(f"stale_anchor:{story.get('id')}:{ref.get('section_id') or 'unknown'}")
                    continue
                if ref.get("doc") != "trd":
                    continue
                anchor = ref.get("anchor_url") or ""
                if "#" not in anchor:
                    continue
                slug = anchor.split("#", 1)[1]
                if slug not in trd_slugs:
                    findings.append(f"stale_anchor:{story.get('id')}:{slug}")
    return findings


def _check_duplication(trd_text: str, prd_text: str) -> list[str]:
    findings: list[str] = []
    for slug, prd_section_key in [
        ("problem-statement", "problem"),
        ("functional-requirements", "functional"),
    ]:
        trd_body = _section_body(trd_text, slug)
        if not trd_body:
            continue
        # Crudely grab the matching PRD section: scan for a header containing the
        # keyword. The exact PRD header shape varies; we use the keyword as a
        # tolerant proxy.
        prd_body = _extract_prd_section(prd_text, prd_section_key)
        if not prd_body:
            continue
        overlap = _longest_common_substring(trd_body, prd_body)
        if overlap > DUPLICATION_THRESHOLD:
            findings.append(f"prd_trd_duplication:{slug}:{overlap}")
    return findings


def _extract_prd_section(prd_text: str, keyword: str) -> str:
    """Pull the body of the first PRD heading whose title contains `keyword`."""
    pattern = re.compile(r"^#{1,3}\s+.*?" + re.escape(keyword) + r".*$", re.IGNORECASE | re.MULTILINE)
    m = pattern.search(prd_text)
    if not m:
        return ""
    start = m.end()
    next_header = re.search(r"^#{1,3}\s+", prd_text[start:], re.MULTILINE)
    end = start + next_header.start() if next_header else len(prd_text)
    return prd_text[start:end]


def _check_implementation_manual(trd_text: str) -> list[str]:
    findings: list[str] = []
    hld_body = _section_body(trd_text, "high-level-design")
    alt_body = _section_body(trd_text, "alternatives-considered")
    # Skip alternatives body that is only `n/a — reason`.
    alt_meaningful = bool(alt_body.strip()) and not re.match(r"^\s*n/a\b", alt_body.strip(), re.IGNORECASE)
    for match in re.finditer(r"```[^\n]*\n(.*?)```", hld_body, re.DOTALL):
        code = match.group(1)
        line_count = code.count("\n")
        if line_count > CODE_BLOCK_THRESHOLD and not alt_meaningful:
            findings.append(f"implementation_manual:{line_count}")
    return findings


def check(plan_path: Path, trd_path: Path, prd_path: Path | None) -> int:
    if not plan_path.is_file():
        _emit("FAIL", "file_not_found:plan_json")
        return 2
    if not trd_path.is_file():
        _emit("FAIL", "file_not_found:trd_md")
        return 2
    plan = json.loads(plan_path.read_text())
    trd_text = trd_path.read_text()
    trd_slugs = _slugs_in_trd(trd_text)

    findings: list[str] = []
    findings.extend(_check_stale_anchors(plan, trd_slugs))
    if prd_path is not None and prd_path.is_file():
        prd_text = prd_path.read_text()
        findings.extend(_check_duplication(trd_text, prd_text))
    findings.extend(_check_implementation_manual(trd_text))

    for f in findings:
        _emit("FAIL", f)
    return 1 if findings else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("plan_json", help="Path to plan.json sidecar.")
    parser.add_argument("trd_md", help="Path to trd.md.")
    parser.add_argument("--prd", default=None, help="Optional path to prd.md.")
    args = parser.parse_args(argv)
    prd = Path(args.prd) if args.prd else None
    return check(Path(args.plan_json), Path(args.trd_md), prd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
