# shield/scripts/test_migrate_outputs.py
"""Tests for migrate_outputs.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from migrate_outputs import map_legacy_path  # type: ignore[import-not-found]


@pytest.mark.parametrize("old,new", [
    # research findings → research.md
    ("research/1-claude-isolation/findings.md", "research.md"),
    ("research/2-rerun/findings.md",            "research.md"),
    # session transcripts → hidden file
    ("research/1-claude-isolation/transcript.md", ".session-transcript.md"),
    # plan architecture HTML → outputs/
    ("plan/1-foo/architecture.html", "outputs/plan-architecture.html"),
    # files already at root → unchanged (None signals "no move needed")
    ("plan.json", None),
    ("handoff.md", None),
    ("README.md", None),
])
def test_map_legacy_path(old: str, new: str | None) -> None:
    assert map_legacy_path(old) == new
