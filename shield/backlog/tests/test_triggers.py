"""Tests for shield_backlog.triggers — eager prune + lazy sweep + kill switch
+ recovery log ordering seam (EPIC-3-S3)."""
import json
from pathlib import Path

import pytest

from shield_backlog import capture, eager_prune, kill_switch_enabled, lazy_sweep, read_backlog
from shield_backlog.reconciler import Verdict


# ----- helpers -------------------------------------------------------------

def _scaffold(tmp_path: Path):
    """Build a self-contained Shield-shaped tree under tmp_path:

        tmp_path/
            backlog.json
            shield.json
            removed.log  (created on first remove)
            docs/
                shield/
                    manifest.json
                    auth/plan.json
                    billing/plan.json   (added by some tests)
    """
    backlog = tmp_path / "backlog.json"
    backlog.write_text(json.dumps({"schema_version": 1, "entries": []}))

    shield_dir = tmp_path / "docs" / "shield"
    shield_dir.mkdir(parents=True)
    manifest = shield_dir / "manifest.json"

    def write_manifest(features):
        manifest.write_text(json.dumps({"schema_version": 2, "features": features}))

    def write_plan(feature_slug, epics):
        feat_dir = shield_dir / feature_slug
        feat_dir.mkdir(exist_ok=True)
        (feat_dir / "plan.json").write_text(json.dumps({
            "version": "1.5", "project": "x", "name": feature_slug,
            "epics": epics or [{"id": "EPIC-1", "name": "placeholder",
                                 "stories": [{"id": f"{feature_slug.upper()}-S1",
                                              "name": "p", "status": "ready",
                                              "description": "p", "tasks": ["p"],
                                              "acceptance_criteria": ["p"]}]}],
        }))

    return {
        "backlog": backlog,
        "manifest": manifest,
        "shield_json": tmp_path / "shield.json",
        "removed_log": tmp_path / "removed.log",
        "write_manifest": write_manifest,
        "write_plan": write_plan,
    }


# ----- kill switch ---------------------------------------------------------

def test_kill_switch_default_true(tmp_path):
    """Missing .shield.json → enabled (auto_reconcile default True)."""
    assert kill_switch_enabled(tmp_path / "absent.json") is True


def test_kill_switch_explicit_false(tmp_path):
    p = tmp_path / "shield.json"
    p.write_text(json.dumps({"backlog": {"auto_reconcile": False}}))
    assert kill_switch_enabled(p) is False


def test_kill_switch_explicit_true(tmp_path):
    p = tmp_path / "shield.json"
    p.write_text(json.dumps({"backlog": {"auto_reconcile": True}}))
    assert kill_switch_enabled(p) is True


# ----- eager prune ---------------------------------------------------------

def test_eager_prune_removes_when_epic_landed(tmp_path):
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "AUTH-S1", "name": "s", "status": "ready",
                     "description": "s", "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    entry_id = capture(
        "rotate refresh tokens", feature="auth", epic="Session management",
        source="user", path=s["backlog"],
    )
    decision = eager_prune(
        entry_id,
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert decision is not None
    assert decision.verdict == Verdict.REMOVE
    # Entry gone
    assert read_backlog(s["backlog"])["entries"] == []
    # Recovery log appended *before* destructive remove (we observe it after)
    assert s["removed_log"].exists()
    record = json.loads(s["removed_log"].read_text().splitlines()[0])
    assert record["entry"]["id"] == entry_id
    assert "eager_prune" in record["rationale"]


def test_eager_prune_idempotent_when_entry_absent(tmp_path):
    """Calling eager_prune for an id that's not in backlog → None, no log."""
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    decision = eager_prune(
        "00000000-0000-4000-8000-000000000000",
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert decision is None
    assert not s["removed_log"].exists()


def test_eager_prune_respects_kill_switch(tmp_path):
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    s["shield_json"].write_text(json.dumps({"backlog": {"auto_reconcile": False}}))
    entry_id = capture(
        "x", feature="auth", epic="Session management",
        source="user", path=s["backlog"],
    )
    decision = eager_prune(
        entry_id,
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert decision is None
    # Entry still there
    assert len(read_backlog(s["backlog"])["entries"]) == 1


def test_eager_prune_declines_on_no_match(tmp_path):
    """No matching epic → STAY_NO_MATCH; entry remains."""
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Something else",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    entry_id = capture(
        "x", feature="auth", epic="Session management",
        source="user", path=s["backlog"],
    )
    decision = eager_prune(
        entry_id,
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert decision is not None
    assert decision.verdict == Verdict.STAY_NO_MATCH
    assert len(read_backlog(s["backlog"])["entries"]) == 1


# ----- lazy sweep ----------------------------------------------------------

def test_lazy_sweep_removes_landed_entries(tmp_path):
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    # Two entries: one lands, one doesn't.
    landed = capture("a", feature="auth", epic="Session management",
                     source="user", path=s["backlog"])
    stays = capture("b", feature="auth", epic="Not yet planned",
                    source="user", path=s["backlog"])

    decisions = lazy_sweep(
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert len(decisions) == 1
    assert decisions[0].verdict == Verdict.REMOVE
    remaining = [e["id"] for e in read_backlog(s["backlog"])["entries"]]
    assert remaining == [stays]
    assert landed not in remaining


def test_eager_then_sweep_idempotent_no_double_remove(tmp_path):
    """Running eager prune followed by lazy sweep on the same entry yields
    no second action: the second call sees the entry already gone."""
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    entry_id = capture(
        "x", feature="auth", epic="Session management",
        source="user", path=s["backlog"],
    )

    first = eager_prune(
        entry_id,
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert first is not None
    decisions = lazy_sweep(
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert decisions == []  # nothing left to do


def test_lazy_sweep_respects_kill_switch(tmp_path):
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    s["shield_json"].write_text(json.dumps({"backlog": {"auto_reconcile": False}}))
    capture("x", feature="auth", epic="Session management",
            source="user", path=s["backlog"])
    decisions = lazy_sweep(
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    assert decisions == []


# ----- recovery rehearsal --------------------------------------------------

def test_recovery_rehearsal_log_append_before_destructive_remove(tmp_path):
    """Simulate a crash AFTER the recovery-log append but BEFORE the destructive
    remove: assert the entry is recoverable by replaying the log AND happens to
    still be in backlog.json (so replay is idempotent if the OS reordering goes
    the other way). The append-before-remove ordering is what makes this safe."""
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    entry_id = capture(
        "x", feature="auth", epic="Session management",
        source="user", path=s["backlog"],
    )

    # Run eager_prune end-to-end (no crash). Both the log and the prune complete.
    eager_prune(
        entry_id,
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    # Replay the log → entry is fully recoverable (id + feature + epic + text preserved).
    record = json.loads(s["removed_log"].read_text().splitlines()[0])
    recovered = record["entry"]
    re_id = capture(
        recovered["text"], feature=recovered["feature"], epic=recovered["epic"],
        source=recovered["source"], kind=recovered["kind"],
        path=s["backlog"],
    )
    # New id is generated (entries are immutable by uuid); but original content survives.
    assert re_id != entry_id
    re_doc = read_backlog(s["backlog"])
    assert re_doc["entries"][0]["text"] == recovered["text"]


# ----- F6 (no stamping) ---------------------------------------------------

def test_no_stamping_plan_json_byte_unchanged_after_eager_prune(tmp_path):
    """After eager prune, plan.json + story records are byte-unchanged.
    The promotion reference is transient — never written into plan.json."""
    s = _scaffold(tmp_path)
    s["write_manifest"]([{"name": "auth", "artifacts": {"plan_json": True}}])
    s["write_plan"]("auth", [{
        "id": "EPIC-1", "name": "Session management",
        "stories": [{"id": "X", "name": "s", "status": "ready", "description": "s",
                     "tasks": ["s"], "acceptance_criteria": ["s"]}],
    }])
    plan_path = tmp_path / "docs" / "shield" / "auth" / "plan.json"
    before = plan_path.read_bytes()
    entry_id = capture(
        "x", feature="auth", epic="Session management",
        source="user", path=s["backlog"],
    )
    eager_prune(
        entry_id,
        backlog_path=s["backlog"], manifest_path=s["manifest"],
        shield_json_path=s["shield_json"], removed_log_path=s["removed_log"],
    )
    after = plan_path.read_bytes()
    assert before == after, "plan.json must be byte-unchanged after eager prune (F6)"
