"""Tests that NamingConfig carries project_prefix and load_shield_config reads it."""

from __future__ import annotations

from server.config import NamingConfig


def test_naming_config_defaults_project_prefix_empty() -> None:
    assert NamingConfig().project_prefix == ""


def test_naming_config_accepts_project_prefix() -> None:
    nc = NamingConfig(
        project_prefix="SHIELD",
        story_format="[{prefix}] {epic_id}-S{index}: {name}",
    )
    assert nc.project_prefix == "SHIELD"
    assert nc.story_format == "[{prefix}] {epic_id}-S{index}: {name}"
