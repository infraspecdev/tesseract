#!/usr/bin/env python3
"""_build_negatives.py — derive the 16 negative TRD fixtures from positive-backend.

Run from the repo root after editing positive-backend or trd-sections.yaml:

    uv run --with pyyaml shield/evals/plan-trd/_build_negatives.py

Produces under shield/evals/plan-trd/fixtures/:
    missing-<slug>/trd.md   (14)
    extra-section/trd.md    (1)
    vague-tbd/trd.md        (1)

The script is idempotent and overwrites any prior fixture content.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "shield" / "evals" / "plan-trd" / "fixtures"
BASE = FIXTURES / "positive-backend" / "trd.md"
SECTIONS_YAML = REPO_ROOT / "shield" / "schema" / "trd-sections.yaml"

HEADER_RE = re.compile(r"^## §\d+ .+? \{#([a-z0-9-]+)\}\s*$", re.MULTILINE)


def _split_sections(text: str) -> list[tuple[str | None, int, int]]:
    """Return (slug, start, end) tuples covering the whole document.

    The first tuple has slug=None and covers the preamble before §1.
    """
    matches = list(HEADER_RE.finditer(text))
    if not matches:
        return [(None, 0, len(text))]
    spans: list[tuple[str | None, int, int]] = [(None, 0, matches[0].start())]
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        spans.append((m.group(1), m.start(), end))
    return spans


def _omit_section(text: str, slug: str) -> str:
    """Return text with the slug's section removed entirely."""
    spans = _split_sections(text)
    return "".join(text[s:e] for (sg, s, e) in spans if sg != slug)


def _append_extra_section(text: str) -> str:
    extra = (
        "\n## §15 Extra Drifted Section {#drift-section}\n\n"
        "This is an unprompted 15th section — drift-by-addition test.\n"
    )
    return text + extra


def _make_vague(text: str) -> str:
    """Replace §6 Non-Functional Requirements body with bare 'TBD'."""
    spans = _split_sections(text)
    chunks: list[str] = []
    for slug, start, end in spans:
        section = text[start:end]
        if slug == "non-functional-requirements":
            # Keep the header line, replace body with vague tokens.
            header, _body = section.split("\n", 1)
            section = header + "\n\nTBD\n"
        chunks.append(section)
    return "".join(chunks)


def main() -> None:
    base = BASE.read_text()
    sections = yaml.safe_load(SECTIONS_YAML.read_text())["sections"]

    for sec in sections:
        slug = sec["id"]
        target_dir = FIXTURES / f"missing-{slug}"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "trd.md").write_text(_omit_section(base, slug))
        print(f"wrote missing-{slug}/trd.md")

    (FIXTURES / "extra-section").mkdir(parents=True, exist_ok=True)
    (FIXTURES / "extra-section" / "trd.md").write_text(_append_extra_section(base))
    print("wrote extra-section/trd.md")

    (FIXTURES / "vague-tbd").mkdir(parents=True, exist_ok=True)
    (FIXTURES / "vague-tbd" / "trd.md").write_text(_make_vague(base))
    print("wrote vague-tbd/trd.md")


if __name__ == "__main__":
    main()
