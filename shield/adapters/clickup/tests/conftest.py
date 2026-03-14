"""Shared fixtures for ClickUp adapter tests."""
import pytest


@pytest.fixture
def mock_capabilities():
    """Expected capabilities response."""
    return {
        "adapter": "clickup",
        "adapter_mode": "hybrid",
        "capabilities": [
            "pm_sync",
            "pm_bulk_create",
            "pm_bulk_update",
            "pm_get_status",
            "pm_link_story_to_epic",
            "pm_bulk_rename",
            "pm_action_log",
            "pm_get_capabilities",
        ],
    }
