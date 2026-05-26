# shield/scripts/test_coverage_gate.py
"""Tests for coverage_gate.py.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_coverage_gate.py -v`
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from coverage_gate import _parse_covered_lines, _patch_lines  # type: ignore[import-not-found]


def test_parse_covered_lines_extracts_hit_lines(tmp_path: Path) -> None:
    xml = tmp_path / "coverage.xml"
    xml.write_text(
        """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="pkg/mod.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
            <line number="3" hits="5"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""
    )
    result = _parse_covered_lines(xml)
    assert result == {"pkg/mod.py": {1, 3}}


def test_patch_lines_parses_unified_diff_hunks(monkeypatch: pytest.MonkeyPatch) -> None:
    diff = (
        "diff --git a/some/file.py b/some/file.py\n"
        "--- a/some/file.py\n"
        "+++ b/some/file.py\n"
        "@@ -10,0 +11,3 @@\n"
        "+one\n"
        "+two\n"
        "+three\n"
    )

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=diff, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _patch_lines("main")
    assert result == {"some/file.py": {11, 12, 13}}


def test_patch_lines_single_line_hunk_form(monkeypatch: pytest.MonkeyPatch) -> None:
    diff = (
        "--- a/some/file.py\n"
        "+++ b/some/file.py\n"
        "@@ -5 +5 @@\n"
        "+changed\n"
    )

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=diff, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _patch_lines("main")
    assert result == {"some/file.py": {5}}


def test_patch_lines_handles_no_count_hunk(monkeypatch: pytest.MonkeyPatch) -> None:
    diff = (
        "--- a/some/file.py\n"
        "+++ b/some/file.py\n"
        "@@ -0,0 +7 @@\n"
        "+added\n"
    )

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=diff, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _patch_lines("main")
    assert result == {"some/file.py": {7}}
