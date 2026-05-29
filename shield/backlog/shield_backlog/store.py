"""Backlog store — atomic capture/remove against docs/shield/backlog.json.

Design (TRD §5 F3, §6 N1/N5; lld-backlog-store §5/§8):

  - Single-writer assumption — no lockfile.
  - Atomic write: full doc → unique .tmp → fsync → os.replace().
  - Validate-or-refuse on read AND write. Malformed/partial store raises
    BacklogInvalid; never silently truncated.
  - Compare-before-replace: capture the on-disk (schema_version, entry_count)
    at read time; just before os.replace(), re-read and refuse if changed.
    Converts a silent lost-update into a loud refusal without a lockfile.

The LOCKED capture() signature is the documented contract for any skill that
captures mid-task.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, ValidationError
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "shield_backlog requires jsonschema; install via uv add jsonschema"
    ) from exc


# ----- Paths ---------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = _REPO_ROOT / "shield" / "schema" / "backlog.schema.json"
DEFAULT_BACKLOG_PATH = _REPO_ROOT / "docs" / "shield" / "backlog.json"
DEFAULT_REMOVED_LOG = _REPO_ROOT / ".shield" / "backlog-removed.log"

CURRENT_SCHEMA_VERSION = 1


# ----- Exceptions ----------------------------------------------------------

class BacklogInvalid(Exception):
    """Raised when the backlog store is malformed, partial, or a concurrent
    on-disk change is detected between read and os.replace()."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# ----- Internals -----------------------------------------------------------

_SCHEMA_CACHE: dict[str, Any] | None = None


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(SCHEMA_PATH.read_text())
    return _SCHEMA_CACHE


def _empty_doc() -> dict[str, Any]:
    return {"schema_version": CURRENT_SCHEMA_VERSION, "entries": []}


def _validate_doc(doc: Any) -> None:
    """Validate a parsed doc against the schema + the duplicate-id check.
    Raises BacklogInvalid with a named code on the first failure.
    """
    if not isinstance(doc, dict):
        raise BacklogInvalid("schema_violation", f"expected object, got {type(doc).__name__}")

    declared = doc.get("schema_version")
    if isinstance(declared, int) and declared > CURRENT_SCHEMA_VERSION:
        raise BacklogInvalid(
            "schema_version_too_new",
            f"schema_version={declared} > current {CURRENT_SCHEMA_VERSION}",
        )

    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    if errors:
        err = errors[0]
        code = _map_error_code(err)
        path = "/".join(str(p) for p in err.path) or "<root>"
        raise BacklogInvalid(code, f"{path}: {err.message}")

    seen: dict[str, int] = {}
    for idx, entry in enumerate(doc.get("entries") or []):
        eid = entry.get("id")
        if eid in seen:
            raise BacklogInvalid(
                "duplicate_entry_id",
                f"entries[{idx}].id={eid!r} duplicates entries[{seen[eid]}].id",
            )
        seen[eid] = idx


def _map_error_code(err: ValidationError) -> str:
    path = [str(p) for p in err.path]
    if err.validator == "required":
        return "missing_required_field"
    if err.validator == "enum":
        if "kind" in path:
            return "unknown_kind_enum"
        if "source" in path:
            return "unknown_source_enum"
    if err.validator == "pattern" and "id" in path:
        return "invalid_id_format"
    return "schema_violation"


def _snapshot(doc: dict[str, Any]) -> tuple[int, int]:
    return (int(doc.get("schema_version", 0)), len(doc.get("entries") or []))


def _atomic_write(path: Path, doc: dict[str, Any], *, expected: tuple[int, int] | None) -> None:
    """Write doc atomically (full doc → unique .tmp → fsync → os.replace).
    If `expected` is provided, re-read on-disk just before replace and refuse
    when the (schema_version, entry_count) snapshot differs (compare-before-replace).
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Just-before-replace: compare on-disk snapshot to caller's expectation.
    if expected is not None and path.exists():
        try:
            current = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise BacklogInvalid("invalid_json", f"on-disk became malformed: {e.msg}")
        current_snap = _snapshot(current)
        if current_snap != expected:
            raise BacklogInvalid(
                "lost_update",
                f"on-disk store changed between read and write: "
                f"expected snapshot {expected}, found {current_snap}",
            )

    tmp = path.with_name(
        f"{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}"
    )
    payload = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ----- Public API ----------------------------------------------------------

def read_backlog(path: Path | str | None = None) -> dict[str, Any]:
    """Read the backlog store. A missing file yields an empty doc; a malformed
    store raises BacklogInvalid (named errors invalid_json / schema_violation /
    duplicate_entry_id / schema_version_too_new).
    """
    p = Path(path) if path else DEFAULT_BACKLOG_PATH
    if not p.exists():
        return _empty_doc()
    try:
        doc = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        raise BacklogInvalid("invalid_json", f"{p}: {e.msg} at line {e.lineno}")
    _validate_doc(doc)
    return doc


def capture(
    text: str,
    *,
    kind: str = "task",
    feature: str | None = None,
    epic: str | None = None,
    source: str,
    path: Path | str | None = None,
) -> str:
    """Append one entry atomically. Returns the new entry's uuid4 id.

    LOCKED signature (TRD §11, plan-review 2026-05-27). source is keyword-only
    and required. feature/epic must be non-None strings: when the caller has
    no match in mind, pass a proposed-new name (the user-typed value), not None.

    Raises BacklogInvalid on a malformed/partial store, a write-side schema
    failure, or a compare-before-replace lost-update.
    """
    if not isinstance(text, str) or not text.strip():
        raise BacklogInvalid("missing_required_field", "text must be a non-empty string")
    if source not in ("user", "agent"):
        raise BacklogInvalid("unknown_source_enum", f"source={source!r} not in {{user, agent}}")
    if not feature:
        raise BacklogInvalid("missing_required_field", "feature is required (proposed-new is fine)")
    if not epic:
        raise BacklogInvalid("missing_required_field", "epic is required (proposed-new is fine)")

    p = Path(path) if path else DEFAULT_BACKLOG_PATH
    doc = read_backlog(p)
    expected = _snapshot(doc)

    next_order = (max((e["order"] for e in doc["entries"]), default=0) + 1)
    new_id = str(uuid.uuid4())
    entry = {
        "id": new_id,
        "order": next_order,
        "kind": kind,
        "source": source,
        "feature": feature,
        "epic": epic,
        "text": text,
    }
    doc["entries"].append(entry)

    # Write-side validate-before-replace. Refuses *before* writing the .tmp.
    _validate_doc(doc)
    _atomic_write(p, doc, expected=expected)
    return new_id


def remove(
    entry_id: str,
    *,
    path: Path | str | None = None,
    log_to_recovery: bool = False,
    removed_log_path: Path | str | None = None,
    rationale: str | None = None,
) -> dict[str, Any] | None:
    """Remove the entry with the given id. Returns the removed entry dict, or
    None when id was already absent (idempotent).

    When `log_to_recovery=True`, the entry is appended to the recovery log
    *before* the destructive remove (ordering seam for crash recovery).
    Manual /backlog remove leaves the default `False` — recoverability there
    is bounded by git revert of committed state.
    """
    p = Path(path) if path else DEFAULT_BACKLOG_PATH
    doc = read_backlog(p)
    expected = _snapshot(doc)

    entries = doc.get("entries") or []
    idx = next((i for i, e in enumerate(entries) if e.get("id") == entry_id), None)
    if idx is None:
        return None  # idempotent: nothing to do

    removed = entries[idx]

    if log_to_recovery:
        log_path = Path(removed_log_path) if removed_log_path else DEFAULT_REMOVED_LOG
        _append_recovery_log(log_path, removed, rationale=rationale or "removed")

    new_entries = entries[:idx] + entries[idx + 1:]
    doc["entries"] = new_entries
    _validate_doc(doc)
    _atomic_write(p, doc, expected=expected)
    return removed


def _append_recovery_log(log_path: Path, entry: dict[str, Any], *, rationale: str) -> None:
    """Append a JSON-line record to the recovery log. Runs *before* the
    destructive remove — replaying the log restores the entry."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "rationale": rationale,
        "entry": entry,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
