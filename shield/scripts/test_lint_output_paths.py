# shield/scripts/test_lint_output_paths.py
"""Tests for lint_output_paths.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lint_output_paths import discover_assets, parse_outputs_block  # type: ignore[import-not-found]


def _write_asset(path: Path, frontmatter: str, body: str = "Body.\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}")


def test_discover_finds_md_files(tmp_path: Path) -> None:
    _write_asset(tmp_path / "commands" / "plan.md", "name: plan\n")
    _write_asset(tmp_path / "skills" / "x" / "SKILL.md", "name: x\n")
    (tmp_path / "README.md").write_text("not an asset\n")
    found = discover_assets(tmp_path)
    rels = sorted(p.relative_to(tmp_path).as_posix() for p in found)
    assert rels == ["commands/plan.md", "skills/x/SKILL.md"]


def test_parse_outputs_block_present(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n  - plan_json\n")
    assert parse_outputs_block(asset) == ["plan_md", "plan_json"]


def test_parse_outputs_block_absent(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\n")
    assert parse_outputs_block(asset) == []
