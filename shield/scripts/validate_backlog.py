#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jsonschema>=4.0",
# ]
# ///
"""validate_backlog.py — JSON Schema validator for shield backlog.json.

Invoked by /backlog (read-side validate-or-refuse), shield/scripts/backlog_store.py
(write-side validate-before-replace), and the shield/evals/run.py eval runner.

Exit codes:
  0  — backlog.json is valid.
  1  — backlog.json fails validation (named error printed to stderr).
  2  — usage error (file not found, malformed JSON, missing jsonschema).

Named errors (stderr prefix on FAIL):
  schema_violation        — JSON Schema rejected the doc (default mapping)
  unknown_kind_enum       — entries[].kind not in {epic, story, task}
  unknown_source_enum     — entries[].source not in {user, agent}
  missing_required_field  — required field absent from doc/entry
  duplicate_entry_id      — entries[] contains 2+ items sharing the same id
  schema_version_too_new  — schema_version > current; doc-only forward-compat
  invalid_id_format       — entries[].id is not a uuid4

Usage:
  uv run shield/scripts/validate_backlog.py PATH_TO_BACKLOG_JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    print("validate_backlog: requires jsonschema (uv run will install it)", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "shield" / "schema" / "backlog.schema.json"

CURRENT_SCHEMA_VERSION = 1


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


def _emit(severity: str, code: str, message: str) -> None:
    print(f"{severity}: {code}: {message}", file=sys.stderr)


def _map_schema_error_code(err: Any) -> str:
    """Map a jsonschema ValidationError to one of the stable named error codes."""
    path = [str(p) for p in err.path]
    msg = err.message
    validator = err.validator

    if validator == "required":
        return "missing_required_field"
    if validator == "enum":
        if "kind" in path:
            return "unknown_kind_enum"
        if "source" in path:
            return "unknown_source_enum"
    if validator == "pattern" and "id" in path:
        return "invalid_id_format"
    return "schema_violation"


def validate(path: Path) -> int:
    if not path.is_file():
        _emit("FAIL", "file_not_found", str(path))
        return 2
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        _emit("FAIL", "invalid_json", f"{path}: {e.msg} at line {e.lineno}")
        return 2

    # Forward-compat policy: doc-only migration until schema_version 2.
    declared = doc.get("schema_version")
    if isinstance(declared, int) and declared > CURRENT_SCHEMA_VERSION:
        _emit(
            "FAIL",
            "schema_version_too_new",
            f"backlog schema_version {declared} > current {CURRENT_SCHEMA_VERSION}",
        )
        return 1

    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    fail = False

    for err in errors:
        code = _map_schema_error_code(err)
        path_str = "/".join(str(p) for p in err.path) or "<root>"
        _emit("FAIL", code, f"{path_str}: {err.message}")
        fail = True

    if fail:
        return 1

    # Validator-owned check: id uniqueness across entries[] (cannot express
    # property-level uniqueness in draft 2020-12).
    entries = doc.get("entries") or []
    seen: dict[str, int] = {}
    for idx, entry in enumerate(entries):
        eid = entry.get("id")
        if eid in seen:
            _emit(
                "FAIL",
                "duplicate_entry_id",
                f"entries[{idx}].id={eid!r} duplicates entries[{seen[eid]}].id",
            )
            fail = True
        else:
            seen[eid] = idx

    return 1 if fail else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("path", type=Path, help="Path to backlog.json")
    args = p.parse_args()
    return validate(args.path)


if __name__ == "__main__":
    sys.exit(main())
