"""Tests for shield/scripts/validate_backlog.py.

Covers schema conformance, named error mappings (unknown_kind_enum,
duplicate_entry_id, missing_required_field, schema_version_too_new,
invalid_id_format), and the validator-owned duplicate-id check.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "shield" / "scripts" / "validate_backlog.py"
FIXTURES = REPO_ROOT / "shield" / "tests" / "fixtures"


def run_validator(fixture_path):
    """Returns (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(fixture_path)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_valid_backlog_passes():
    """A well-formed backlog.json with unique ids passes."""
    code, out, err = run_validator(FIXTURES / "backlog-1.0-valid.json")
    assert code == 0, f"expected exit 0, got {code}; stderr={err!r}"


def test_unknown_kind_fails_with_named_error():
    """kind='feature' is rejected with unknown_kind_enum."""
    code, out, err = run_validator(FIXTURES / "backlog-1.0-unknown-kind.json")
    assert code == 1, f"expected exit 1, got {code}"
    assert "unknown_kind_enum" in err, f"missing named error in stderr: {err!r}"


def test_duplicate_id_fails_with_named_error():
    """Validator (not schema) catches duplicate entry ids."""
    code, out, err = run_validator(FIXTURES / "backlog-1.0-duplicate-id.json")
    assert code == 1, f"expected exit 1, got {code}"
    assert "duplicate_entry_id" in err, f"missing named error in stderr: {err!r}"


def test_missing_required_field_named_error():
    """An entry missing 'epic' raises missing_required_field."""
    code, out, err = run_validator(FIXTURES / "backlog-1.0-missing-field.json")
    assert code == 1, f"expected exit 1, got {code}"
    assert "missing_required_field" in err, f"missing named error in stderr: {err!r}"


def test_schema_version_too_new_named_error():
    """schema_version=2 (greater than current) fails with schema_version_too_new."""
    code, out, err = run_validator(FIXTURES / "backlog-1.0-too-new.json")
    assert code == 1, f"expected exit 1, got {code}"
    assert "schema_version_too_new" in err, f"missing named error in stderr: {err!r}"


def test_invalid_id_format_named_error():
    """A non-uuid4 id is rejected with invalid_id_format."""
    code, out, err = run_validator(FIXTURES / "backlog-1.0-bad-id.json")
    assert code == 1, f"expected exit 1, got {code}"
    assert "invalid_id_format" in err, f"missing named error in stderr: {err!r}"


def test_empty_entries_passes():
    """An empty backlog (no entries) is valid."""
    tmp = FIXTURES / "backlog-1.0-empty.json"
    tmp.write_text(json.dumps({"schema_version": 1, "entries": []}))
    try:
        code, out, err = run_validator(tmp)
        assert code == 0, f"expected exit 0, got {code}; stderr={err!r}"
    finally:
        tmp.unlink(missing_ok=True)


def test_file_not_found_returns_2():
    """Missing file → exit 2 (usage error)."""
    code, out, err = run_validator(FIXTURES / "does-not-exist.json")
    assert code == 2
