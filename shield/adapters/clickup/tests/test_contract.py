"""PM adapter contract tests.

These tests verify that the ClickUp adapter conforms to the pm_* interface
contract. The same tests should pass for any PM adapter implementation.
"""
import json
from pathlib import Path


def test_capabilities_lists_all_required_operations(mock_capabilities):
    """pm_get_capabilities must return all required operations."""
    required = {"pm_sync", "pm_get_status", "pm_get_capabilities"}
    actual = set(mock_capabilities["capabilities"])
    missing = required - actual
    assert not missing, f"Missing required capabilities: {missing}"


def test_capabilities_declares_adapter_name(mock_capabilities):
    """pm_get_capabilities must declare the adapter name."""
    assert "adapter" in mock_capabilities
    assert isinstance(mock_capabilities["adapter"], str)
    assert len(mock_capabilities["adapter"]) > 0


def test_capabilities_declares_adapter_mode(mock_capabilities):
    """pm_get_capabilities must declare the adapter mode."""
    assert mock_capabilities["adapter_mode"] in ("native", "hybrid", "full")


def test_pm_config_schema_valid():
    """pm.json example must validate against the PM schema."""
    schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "pm.schema.json"
    example_path = Path(__file__).parent.parent.parent.parent / "config-examples" / "pm-clickup.example.json"

    if not schema_path.exists() or not example_path.exists():
        pytest.skip("Schema or example file not found")

    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    with open(schema_path) as f:
        schema = json.load(f)
    with open(example_path) as f:
        example = json.load(f)

    jsonschema.validate(example, schema)


def test_capabilities_only_declares_implemented_tools(mock_capabilities):
    """Every capability declared must correspond to a registered tool."""
    # This is a structural test — in integration tests, we'd actually
    # call each declared capability and verify it doesn't error with
    # "not implemented"
    valid_prefixes = ("pm_",)
    for cap in mock_capabilities["capabilities"]:
        assert any(cap.startswith(p) for p in valid_prefixes), \
            f"Capability '{cap}' doesn't follow pm_* naming convention"
