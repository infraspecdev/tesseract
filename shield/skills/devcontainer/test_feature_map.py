# shield/skills/devcontainer/test_feature_map.py
"""Validates feature-map.json against feature-map.schema.json.

Runnable: `cd shield/skills/devcontainer && uv run --with jsonschema --with pytest pytest -v`
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

DIR = Path(__file__).resolve().parent
MAP_PATH = DIR / "feature-map.json"
SCHEMA_PATH = DIR / "feature-map.schema.json"


def test_feature_map_validates() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    data = json.loads(MAP_PATH.read_text())
    jsonschema.validate(data, schema)


def test_feature_map_has_required_stacks() -> None:
    """Spec §Components.2 lists the stacks Shield supports out of the box."""
    data = json.loads(MAP_PATH.read_text())
    required = {"python", "node", "go", "java", "terraform"}
    missing = required - set(data.keys())
    assert not missing, f"feature-map missing entries: {missing}"


@pytest.mark.parametrize("stack,allowlist_must_include", [
    ("python", "pypi.org"),
    ("node", "registry.npmjs.org"),
    ("go", "proxy.golang.org"),
    ("terraform", "registry.terraform.io"),
])
def test_feature_map_firewall_allowlist_sane(stack: str, allowlist_must_include: str) -> None:
    data = json.loads(MAP_PATH.read_text())
    assert allowlist_must_include in data[stack]["firewall_allowlist"]
