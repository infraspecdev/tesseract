"""PM adapter contract tests for the GitHub adapter."""
import json
from pathlib import Path


def test_capabilities_lists_all_required_operations(mock_capabilities):
    required = {"pm_sync", "pm_get_status", "pm_get_capabilities"}
    actual = set(mock_capabilities["capabilities"])
    missing = required - actual
    assert not missing, f"Missing required capabilities: {missing}"


def test_capabilities_declares_adapter_name(mock_capabilities):
    assert "adapter" in mock_capabilities
    assert mock_capabilities["adapter"] == "github"


def test_capabilities_declares_adapter_mode(mock_capabilities):
    assert mock_capabilities["adapter_mode"] in ("native", "hybrid", "full")


def test_pm_config_schema_valid():
    schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "pm.schema.json"
    example_path = Path(__file__).parent.parent.parent.parent / "config-examples" / "pm-github.example.json"

    if not schema_path.exists() or not example_path.exists():
        return

    try:
        import jsonschema
    except ImportError:
        return

    with open(schema_path) as f:
        schema = json.load(f)
    with open(example_path) as f:
        example = json.load(f)

    jsonschema.validate(example, schema)


def test_capabilities_only_declares_pm_prefixed_tools(mock_capabilities):
    for cap in mock_capabilities["capabilities"]:
        assert cap.startswith("pm_"), f"Capability '{cap}' doesn't follow pm_* naming convention"
