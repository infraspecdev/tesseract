"""Shared test fixtures for the SonarQube adapter."""

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def empty_issues() -> dict:
    return json.loads((FIXTURES_DIR / "empty-issues.json").read_text())


@pytest.fixture
def sample_issues() -> dict:
    return json.loads((FIXTURES_DIR / "sample-issues.json").read_text())
