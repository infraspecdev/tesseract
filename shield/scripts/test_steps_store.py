# shield/scripts/test_steps_store.py
"""Tests for steps_store.py — the producer of ~/.shield/projects/<project>/steps.json.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_steps_store.py -v`

The path assertions here are the regression gate for the bug this script fixes:
the steps.json path MUST match what the session-start hook reads
(`${SHIELD_HOME:-~/.shield}/projects/<project>/steps.json`).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import steps_store  # type: ignore[import-not-found]


SCRIPT = SCRIPT_DIR / "steps_store.py"


# ---------- path resolution (matches the hook) -----------------------------

def test_resolve_path_matches_hook_formula(tmp_path: Path) -> None:
    # The hook reads ${SHIELD_HOME}/projects/${PROJECT_NAME}/steps.json
    result = steps_store.resolve_steps_path(project="Shield", shield_home=tmp_path)
    assert result == tmp_path / "projects" / "Shield" / "steps.json"


def test_resolve_path_reads_project_from_marker(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    (repo / ".shield.json").write_text(json.dumps({"project": "Foo"}))
    home = tmp_path / "home"
    result = steps_store.resolve_steps_path(shield_home=home, start_dir=nested)
    assert result == home / "projects" / "Foo" / "steps.json"


def test_resolve_path_override_wins(tmp_path: Path) -> None:
    override = tmp_path / "custom" / "steps.json"
    result = steps_store.resolve_steps_path(override=override, project="Ignored", shield_home=tmp_path)
    assert result == override


# ---------- init / read ----------------------------------------------------

def test_init_writes_skeleton(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    steps_store.init_steps(
        "research",
        "vpc-20260622",
        [{"id": 1, "action": "Repo scan"}, {"id": 2, "action": "Q&A walk"}],
        path=path,
    )
    doc = json.loads(path.read_text())
    assert doc["skill"] == "research"
    assert doc["feature"] == "vpc-20260622"
    assert doc["started_at"]  # stamped, non-empty
    assert [s["id"] for s in doc["steps"]] == [1, 2]


def test_init_normalizes_step_defaults(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    steps_store.init_steps("review", "f", [{"id": 1, "action": "scan"}], path=path)
    step = json.loads(path.read_text())["steps"][0]
    assert step["status"] == "pending"
    assert step["mandatory"] is True
    assert step["output"] is None


def test_init_creates_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "projects" / "Shield" / "steps.json"
    steps_store.init_steps("plan", "f", [{"id": 1, "action": "x"}], path=path)
    assert path.exists()


def test_read_missing_returns_none(tmp_path: Path) -> None:
    assert steps_store.read_steps(tmp_path / "nope.json") is None


# ---------- status transitions ---------------------------------------------

def test_start_then_complete_with_output(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    steps_store.init_steps("research", "f", [{"id": 1, "action": "x"}], path=path)
    steps_store.set_status(1, "in_progress", path=path)
    assert steps_store.read_steps(path)["steps"][0]["status"] == "in_progress"
    steps_store.set_status(1, "complete", path=path, output="docs/shield/f/research.md")
    step = steps_store.read_steps(path)["steps"][0]
    assert step["status"] == "complete"
    assert step["output"] == "docs/shield/f/research.md"


def test_set_status_unknown_id_raises(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    steps_store.init_steps("research", "f", [{"id": 1, "action": "x"}], path=path)
    with pytest.raises(steps_store.StepsError):
        steps_store.set_status(99, "complete", path=path)


# ---------- clear ----------------------------------------------------------

def test_clear_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    steps_store.init_steps("research", "f", [{"id": 1, "action": "x"}], path=path)
    assert steps_store.clear_steps(path) is True
    assert not path.exists()
    assert steps_store.clear_steps(path) is False  # already gone, no error


# ---------- CLI ------------------------------------------------------------

def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_cli_init_read_clear_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    steps = json.dumps([{"id": 1, "action": "scan"}, {"id": 2, "action": "synthesize"}])
    init = _run("init", "--skill", "research", "--feature", "f",
                "--steps-json", steps, "--steps-file", str(path))
    assert init.returncode == 0, init.stderr
    assert path.exists()

    read = _run("read", "--steps-file", str(path))
    assert read.returncode == 0
    assert json.loads(read.stdout)["skill"] == "research"

    clear = _run("clear", "--steps-file", str(path))
    assert clear.returncode == 0
    assert not path.exists()


def test_cli_set_status_unknown_id_exit_1(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    steps_store.init_steps("research", "f", [{"id": 1, "action": "x"}], path=path)
    res = _run("complete", "42", "--steps-file", str(path))
    assert res.returncode == 1
    assert "42" in res.stderr


def test_cli_read_missing_prints_none_exit_0(tmp_path: Path) -> None:
    res = _run("read", "--steps-file", str(tmp_path / "nope.json"))
    assert res.returncode == 0
    assert res.stdout.strip() == "none"
