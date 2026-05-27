"""Pytest fixtures for the Notion adapter."""

import pytest

from shield_adapters_common import DesignRef


@pytest.fixture
def sample_refs() -> list[DesignRef]:
    return [
        DesignRef(
            story_id="EPIC-1-S1",
            doc="trd",
            section_id="apis-involved",
            anchor_url="https://docs.example.com/trd.md#apis-involved",
            label="§11 APIs Involved",
        ),
    ]
