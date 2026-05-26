# shield/scripts/test_devcontainer_gate.py
"""Tests for devcontainer_gate.py.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_devcontainer_gate.py -v`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from devcontainer_gate import Decision, decide  # type: ignore[import-not-found]


def _write_shield_json(repo: Path, required: str | None) -> None:
    payload: dict = {}
    if required is not None:
        payload["devcontainer"] = {"required": required}
    (repo / ".shield.json").write_text(json.dumps(payload))


def _mk_devcontainer(repo: Path) -> None:
    (repo / ".devcontainer").mkdir()
    (repo / ".devcontainer" / "devcontainer.json").write_text("{}")


def test_in_container_proceeds(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "ask")
    d = decide(repo=tmp_path, in_container=True, user_input=None)
    assert d == Decision.PROCEED


def test_no_devcontainer_dir_proceeds(tmp_path: Path) -> None:
    _write_shield_json(tmp_path, "ask")
    d = decide(repo=tmp_path, in_container=False, user_input=None)
    assert d == Decision.PROCEED


def test_required_false_proceeds(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "false")
    d = decide(repo=tmp_path, in_container=False, user_input=None)
    assert d == Decision.PROCEED


def test_required_true_refuses(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "true")
    d = decide(repo=tmp_path, in_container=False, user_input=None)
    assert d == Decision.REFUSE


@pytest.mark.parametrize("answer,expected_decision,expected_required_after", [
    ("y", Decision.REFUSE, "ask"),
    ("n", Decision.PROCEED, "ask"),
    ("always", Decision.REFUSE, "true"),
    ("never", Decision.PROCEED, "false"),
])
def test_ask_branch(tmp_path: Path, answer: str, expected_decision: Decision, expected_required_after: str) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "ask")
    d = decide(repo=tmp_path, in_container=False, user_input=answer)
    assert d == expected_decision
    after = json.loads((tmp_path / ".shield.json").read_text())
    assert after["devcontainer"]["required"] == expected_required_after


def test_missing_shield_json_treated_as_ask(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    # no .shield.json at all
    d = decide(repo=tmp_path, in_container=False, user_input="n")
    assert d == Decision.PROCEED
