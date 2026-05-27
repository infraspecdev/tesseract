"""Pytest fixtures for shield_parsers tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def schema_path() -> Path:
    """Path to the canonical plan-sidecar JSON Schema in the repo."""
    # tests/ → parsers/ → shield/ → shield/schema/plan-sidecar.schema.json
    return Path(__file__).resolve().parents[2] / "schema" / "plan-sidecar.schema.json"
