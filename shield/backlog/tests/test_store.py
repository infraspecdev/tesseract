"""Tests for shield_backlog.store — capture / remove / read with atomic write
and compare-before-replace (EPIC-1-S2 + EPIC-1-S4)."""
import json
import os
import uuid
from pathlib import Path

import pytest

from shield_backlog.store import (
    BacklogInvalid,
    capture,
    read_backlog,
    remove,
)


# ----- helpers -------------------------------------------------------------

def _empty_store(tmp_path: Path) -> Path:
    p = tmp_path / "backlog.json"
    p.write_text(json.dumps({"schema_version": 1, "entries": []}))
    return p


def _write(p: Path, doc: dict) -> None:
    p.write_text(json.dumps(doc))


# ----- read_backlog --------------------------------------------------------

def test_read_missing_returns_empty_doc(tmp_path):
    p = tmp_path / "backlog.json"  # does not exist
    doc = read_backlog(p)
    assert doc == {"schema_version": 1, "entries": []}


def test_read_invalid_json_raises_named_error(tmp_path):
    p = tmp_path / "backlog.json"
    p.write_text("{ not json")
    with pytest.raises(BacklogInvalid) as exc:
        read_backlog(p)
    assert exc.value.code == "invalid_json"


def test_read_malformed_doc_raises_named_error(tmp_path):
    p = tmp_path / "backlog.json"
    p.write_text(json.dumps({"schema_version": 1, "entries": [{"id": "bad"}]}))
    with pytest.raises(BacklogInvalid) as exc:
        read_backlog(p)
    assert exc.value.code in {"missing_required_field", "invalid_id_format"}


def test_read_partial_doc_refused(tmp_path):
    """A backlog missing required top-level fields is refused — never silently truncated."""
    p = tmp_path / "backlog.json"
    p.write_text(json.dumps({"entries": []}))  # no schema_version
    with pytest.raises(BacklogInvalid) as exc:
        read_backlog(p)
    assert exc.value.code == "missing_required_field"


# ----- capture -------------------------------------------------------------

def test_capture_appends_and_returns_uuid4(tmp_path):
    p = _empty_store(tmp_path)
    new_id = capture(
        "Rotate refresh tokens",
        feature="auth",
        epic="Session mgmt",
        source="user",
        path=p,
    )
    # uuid4 form
    parsed = uuid.UUID(new_id)
    assert parsed.version == 4

    doc = read_backlog(p)
    assert len(doc["entries"]) == 1
    assert doc["entries"][0]["id"] == new_id
    assert doc["entries"][0]["order"] == 1
    assert doc["entries"][0]["kind"] == "task"  # default
    assert doc["entries"][0]["source"] == "user"


def test_capture_assigns_ascending_orders(tmp_path):
    p = _empty_store(tmp_path)
    capture("a", feature="f", epic="e", source="user", path=p)
    capture("b", feature="f", epic="e", source="agent", path=p)
    capture("c", feature="f", epic="e", source="user", path=p)
    doc = read_backlog(p)
    assert [e["order"] for e in doc["entries"]] == [1, 2, 3]


def test_capture_writes_atomically_no_partial_file(tmp_path):
    """After capture, no .tmp files should remain in the directory."""
    p = _empty_store(tmp_path)
    capture("x", feature="f", epic="e", source="agent", path=p)
    leftovers = [f.name for f in tmp_path.iterdir() if ".tmp." in f.name]
    assert leftovers == []


def test_capture_requires_source(tmp_path):
    p = _empty_store(tmp_path)
    with pytest.raises(TypeError):
        capture("x", feature="f", epic="e", path=p)  # missing keyword-only source


def test_capture_rejects_unknown_source(tmp_path):
    p = _empty_store(tmp_path)
    with pytest.raises(BacklogInvalid) as exc:
        capture("x", feature="f", epic="e", source="robot", path=p)
    assert exc.value.code == "unknown_source_enum"


def test_capture_rejects_missing_feature(tmp_path):
    p = _empty_store(tmp_path)
    with pytest.raises(BacklogInvalid) as exc:
        capture("x", feature=None, epic="e", source="user", path=p)
    assert exc.value.code == "missing_required_field"


def test_capture_rejects_missing_epic(tmp_path):
    p = _empty_store(tmp_path)
    with pytest.raises(BacklogInvalid) as exc:
        capture("x", feature="f", epic=None, source="user", path=p)
    assert exc.value.code == "missing_required_field"


def test_capture_rejects_empty_text(tmp_path):
    p = _empty_store(tmp_path)
    with pytest.raises(BacklogInvalid) as exc:
        capture("   ", feature="f", epic="e", source="user", path=p)
    assert exc.value.code == "missing_required_field"


def test_capture_into_missing_store_creates_it(tmp_path):
    """Calling capture against a path that doesn't yet exist creates the file."""
    p = tmp_path / "subdir" / "backlog.json"
    new_id = capture("x", feature="f", epic="e", source="user", path=p)
    assert p.exists()
    doc = read_backlog(p)
    assert len(doc["entries"]) == 1
    assert doc["entries"][0]["id"] == new_id


# ----- compare-before-replace ---------------------------------------------

def test_concurrent_change_refused_with_lost_update(tmp_path, monkeypatch):
    """End-to-end: a concurrent on-disk change between read_backlog() and the
    just-before-replace check inside _atomic_write refuses with
    BacklogInvalid(lost_update). We simulate the race by patching _atomic_write
    so a concurrent writer slips in an extra entry just before the snapshot
    re-check fires."""
    import shield_backlog.store as store

    p = _empty_store(tmp_path)
    capture("first", feature="f", epic="e", source="user", path=p)

    original_atomic_write = store._atomic_write

    def racing_atomic_write(path, doc, *, expected):
        # Simulate concurrent writer slipping in an extra entry.
        if str(path) == str(p):
            current = json.loads(path.read_text())
            current["entries"].append({
                "id": "11111111-1111-4111-8111-111111111111",
                "order": 99, "kind": "task", "source": "agent",
                "feature": "f", "epic": "e", "text": "concurrent",
            })
            path.write_text(json.dumps(current))
        return original_atomic_write(path, doc, expected=expected)

    monkeypatch.setattr(store, "_atomic_write", racing_atomic_write)

    with pytest.raises(BacklogInvalid) as exc:
        capture("second", feature="f", epic="e", source="user", path=p)
    assert exc.value.code == "lost_update"


def test_compare_before_replace_unit(tmp_path):
    """Direct unit-test of the compare-before-replace check: when the on-disk
    snapshot drifts from the caller's expectation, _atomic_write raises
    lost_update before performing the replace."""
    from shield_backlog.store import _atomic_write

    p = _empty_store(tmp_path)
    # On-disk now has 1 entry, but the caller's snapshot says "0 entries".
    p.write_text(json.dumps({
        "schema_version": 1,
        "entries": [{
            "id": "22222222-2222-4222-8222-222222222222",
            "order": 1, "kind": "task", "source": "user",
            "feature": "f", "epic": "e", "text": "sneaky concurrent",
        }],
    }))
    with pytest.raises(BacklogInvalid) as exc:
        _atomic_write(p, {"schema_version": 1, "entries": []}, expected=(1, 0))
    assert exc.value.code == "lost_update"


# ----- remove --------------------------------------------------------------

def test_remove_deletes_entry(tmp_path):
    p = _empty_store(tmp_path)
    a = capture("a", feature="f", epic="e", source="user", path=p)
    b = capture("b", feature="f", epic="e", source="user", path=p)
    removed = remove(a, path=p)
    assert removed["id"] == a
    doc = read_backlog(p)
    assert [e["id"] for e in doc["entries"]] == [b]


def test_remove_absent_id_is_idempotent(tmp_path):
    p = _empty_store(tmp_path)
    capture("a", feature="f", epic="e", source="user", path=p)
    # remove a non-existent id — returns None, no-op
    result = remove("00000000-0000-4000-8000-000000000000", path=p)
    assert result is None
    doc = read_backlog(p)
    assert len(doc["entries"]) == 1


def test_remove_with_recovery_log_appends_before_remove(tmp_path):
    p = _empty_store(tmp_path)
    a = capture("a", feature="f", epic="e", source="user", path=p)
    log_path = tmp_path / ".shield" / "backlog-removed.log"
    remove(a, path=p, log_to_recovery=True, removed_log_path=log_path, rationale="eager_prune")

    assert log_path.exists()
    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["rationale"] == "eager_prune"
    assert record["entry"]["id"] == a
    # backlog itself is now empty
    assert read_backlog(p)["entries"] == []


def test_manual_remove_does_not_write_recovery_log(tmp_path):
    p = _empty_store(tmp_path)
    a = capture("a", feature="f", epic="e", source="user", path=p)
    log_path = tmp_path / ".shield" / "backlog-removed.log"
    remove(a, path=p, log_to_recovery=False, removed_log_path=log_path)
    assert not log_path.exists()


def test_recovery_log_replay_restores_entry(tmp_path):
    """The append-before-remove ordering means a crash *after* log append but
    *before* the destructive remove leaves the entry recoverable from the log
    AND still present in backlog.json — replay is an upsert-style no-op."""
    p = _empty_store(tmp_path)
    a_id = capture("a", feature="f", epic="e", source="user", path=p)
    a = read_backlog(p)["entries"][0]
    log_path = tmp_path / ".shield" / "backlog-removed.log"
    remove(a_id, path=p, log_to_recovery=True, removed_log_path=log_path)

    # Simulate replay: read the log, the entry is fully recoverable from its record.
    record = json.loads(log_path.read_text().splitlines()[0])
    assert record["entry"] == a
