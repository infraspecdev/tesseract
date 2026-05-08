"""Shared test fixtures for the Semgrep adapter."""

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def empty_output() -> dict:
    return json.loads((FIXTURES_DIR / "empty-output.json").read_text())


@pytest.fixture
def spring_boot_api_output() -> dict:
    return json.loads((FIXTURES_DIR / "spring-boot-api-output.json").read_text())
