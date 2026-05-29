"""Tests for shield/scripts/validate_plan.py — 1.5 schema additions.

Covers the drift gate (persisted touches_lld vs rollup of design_refs[]) and the
lld_components[] integrity check (every design_refs[].component must appear in
the registry when doc=="lld").
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "shield" / "scripts" / "validate_plan.py"
FIXTURES = REPO_ROOT / "shield" / "tests" / "fixtures"


def run_validator(fixture_path):
    """Returns (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(fixture_path)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_valid_15_sidecar_passes():
    """A schema-conformant 1.5 sidecar with consistent touches_lld[] passes."""
    code, out, err = run_validator(FIXTURES / "plan-1.5-valid.json")
    assert code == 0, f"expected exit 0, got {code}; stdout={out!r}; stderr={err!r}"


def test_touches_lld_drift_fails():
    """A 1.5 sidecar whose touches_lld[] mismatches the rollup fails with a named error."""
    code, out, err = run_validator(FIXTURES / "plan-1.5-touches-drift.json")
    assert code != 0, f"expected non-zero exit; stdout={out!r}; stderr={err!r}"
    combined = (out + err).lower()
    assert "touches_lld_drift" in combined, (
        f"expected named error 'touches_lld_drift'; got stdout={out!r}; stderr={err!r}"
    )


def test_lld_component_missing_fails():
    """A 1.5 sidecar with design_refs[].component not in lld_components[] fails."""
    base = json.load(open(FIXTURES / "plan-1.5-valid.json"))
    base["name"] = "schema-test-missing-registry"
    # Drop the vpc-module entry from the registry; the design_refs[] still references it.
    base["lld_components"] = [
        c for c in base["lld_components"] if c["name"] != "vpc-module"
    ]
    # Drop touches_lld 'vpc-module' so we don't conflate with drift error
    base["milestones"][0]["touches_lld"] = ["user-service"]
    tmp = FIXTURES / "plan-1.5-missing-registry.json"
    json.dump(base, open(tmp, "w"), indent=2)
    try:
        code, out, err = run_validator(tmp)
        assert code != 0
        combined = (out + err).lower()
        assert "lld_component_missing" in combined, (
            f"expected named error 'lld_component_missing'; stdout={out!r}; stderr={err!r}"
        )
    finally:
        tmp.unlink(missing_ok=True)


def test_missing_component_when_doc_lld_fails_schema():
    """A 1.5 sidecar with design_refs[].doc==lld and component==null fails schema validation."""
    code, out, err = run_validator(FIXTURES / "plan-1.5-missing-component.json")
    assert code != 0
    combined = (out + err).lower()
    assert "component" in combined, (
        f"expected mention of 'component'; stdout={out!r}; stderr={err!r}"
    )
