"""Tests for the version-gated milestone-diagram gate in validate_plan.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "shield" / "scripts" / "validate_plan.py"
NEW_VERSION = "1.6"   # MUST equal the value chosen in Task 2 Step 2
OLD_VERSION = "1.5"


def _plan(version: str, milestone_extra: dict) -> dict:
    ms = {"id": "M1", "name": "Core", "outcome": "x", "exit_criteria": ["e"]}
    ms.update(milestone_extra)
    return {
        "version": version,
        "project": "demo",
        "name": "demo-plan",
        "milestones": [ms],
        "epics": [{"id": "EPIC-1", "name": "E", "stories": [{
            "id": "EPIC-1-S1",
            "name": "s",
            "status": "ready",
            "description": "x",
            "tasks": ["t"],
            "acceptance_criteria": ["a"],
            "milestone_id": "M1",
            "design_refs": [],
        }]}],
    }


def _run(plan: dict) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "plan.json"
        p.write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(SCRIPT), str(p)],
                              capture_output=True, text=True)


def test_new_version_missing_diagram_fails():
    r = _run(_plan(NEW_VERSION, {}))
    assert r.returncode == 1
    assert "milestone_no_diagram:M1" in r.stderr


def test_new_version_ascii_diagram_fails():
    r = _run(_plan(NEW_VERSION, {"diagram": "┌──┐\n│hi│\n└──┘"}))
    assert r.returncode == 1
    assert "milestone_ascii_diagram:M1" in r.stderr


def test_new_version_with_mermaid_diagram_passes():
    r = _run(_plan(NEW_VERSION, {"diagram": "flowchart LR\n A-->B"}))
    assert "milestone_no_diagram" not in r.stderr
    assert "milestone_ascii_diagram" not in r.stderr


def test_old_version_missing_diagram_grandfathered():
    r = _run(_plan(OLD_VERSION, {}))
    assert "milestone_no_diagram" not in r.stderr
