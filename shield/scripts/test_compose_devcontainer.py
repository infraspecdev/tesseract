# shield/scripts/test_compose_devcontainer.py
"""Tests for compose_devcontainer.py.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_compose_devcontainer.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from compose_devcontainer import compose_devcontainer  # type: ignore[import-not-found]

FEATURE_MAP_PATH = SCRIPT_DIR.parent / "skills" / "devcontainer" / "feature-map.json"


def test_python_only_compose() -> None:
    cfg = compose_devcontainer(stacks=["python"], feature_map_path=FEATURE_MAP_PATH)
    assert cfg["remoteUser"] == "dev"
    assert "NET_ADMIN" in cfg["capAdd"]
    assert "NET_RAW" in cfg["capAdd"]
    # exactly one python feature, digest-pinned
    py_features = [k for k in cfg["features"] if "/python:" in k]
    assert len(py_features) == 1
    assert "@sha256:" in py_features[0]
    # EXTRA_HOSTS contains python's allowlist
    extra = cfg["containerEnv"]["EXTRA_HOSTS"].split()
    assert "pypi.org" in extra
    assert "files.pythonhosted.org" in extra


def test_polyglot_compose_python_node() -> None:
    cfg = compose_devcontainer(stacks=["python", "node"], feature_map_path=FEATURE_MAP_PATH)
    feature_keys = list(cfg["features"].keys())
    assert any("/python:" in k for k in feature_keys)
    assert any("/node:" in k for k in feature_keys)
    extra = cfg["containerEnv"]["EXTRA_HOSTS"].split()
    assert "pypi.org" in extra
    assert "registry.npmjs.org" in extra


def test_named_volume_mount_present() -> None:
    cfg = compose_devcontainer(stacks=["python"], feature_map_path=FEATURE_MAP_PATH)
    assert any("claude-config-" in m and "type=volume" in m for m in cfg["mounts"])


def test_shield_env_var_set() -> None:
    cfg = compose_devcontainer(stacks=["python"], feature_map_path=FEATURE_MAP_PATH)
    assert cfg["containerEnv"]["SHIELD_IN_DEVCONTAINER"] == "true"


def test_unknown_stack_silently_skipped_with_warning(capsys: pytest.CaptureFixture[str]) -> None:
    cfg = compose_devcontainer(stacks=["python", "lisp"], feature_map_path=FEATURE_MAP_PATH)
    # Lisp not in feature-map → no lisp Feature, no Crash, warning to stderr.
    assert all("/lisp" not in k for k in cfg["features"])
    captured = capsys.readouterr()
    assert "lisp" in captured.err.lower()


def test_extra_hosts_user_allowlist_appended() -> None:
    cfg = compose_devcontainer(
        stacks=["python"],
        feature_map_path=FEATURE_MAP_PATH,
        user_extra_allowlist=["internal.example.com", "mirror.corp.local"],
    )
    extra = cfg["containerEnv"]["EXTRA_HOSTS"].split()
    assert "internal.example.com" in extra
    assert "mirror.corp.local" in extra


def test_anthropic_claude_code_feature_always_present() -> None:
    """Claude Code is the constant layer — every devcontainer needs it,
    regardless of detected stacks. Without it the container has no agent."""
    for stacks in (["python"], ["node", "go"], []):
        cfg = compose_devcontainer(stacks=stacks, feature_map_path=FEATURE_MAP_PATH)
        assert any(
            "anthropics/devcontainer-features/claude-code" in k
            for k in cfg["features"]
        ), f"Anthropic claude-code Feature missing for stacks={stacks}"
