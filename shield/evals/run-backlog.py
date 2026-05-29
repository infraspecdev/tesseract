#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jsonschema>=4.0",
# ]
# ///
"""shield/evals/run-backlog.py — end-to-end eval runner for the backlog feature.

Each case scaffolds a self-contained Shield-shaped tree under tempfile, runs
one lifecycle path through the public Python API + CLI, and asserts the
invariant. The whole suite exercises:

  capture (user + agent) — view + badges — manual remove — eager prune —
  lazy sweep — kill switch — name-match-key — cross-feature ambiguity —
  drift tolerance — compare-before-replace — write-side refusal — F6 — recovery.

Exit codes: 0 — all cases pass; 1 — one or more failures.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "shield" / "backlog"))

from shield_backlog import (  # noqa: E402
    BacklogInvalid,
    capture,
    eager_prune,
    lazy_sweep,
    read_backlog,
    remove,
)
from shield_backlog.reconciler import Verdict, reconcile  # noqa: E402
from shield_backlog.view import render  # noqa: E402


VALIDATE_BACKLOG = REPO_ROOT / "shield" / "scripts" / "validate_backlog.py"


# ----- scaffolding ---------------------------------------------------------

@dataclass
class World:
    root: Path
    backlog: Path
    manifest: Path
    shield_json: Path
    removed_log: Path

    def write_manifest(self, features):
        self.manifest.write_text(json.dumps({"schema_version": 2, "features": features}))

    def write_plan(self, feature_slug, epics):
        feat = self.root / "docs" / "shield" / feature_slug
        feat.mkdir(parents=True, exist_ok=True)
        (feat / "plan.json").write_text(json.dumps({
            "version": "1.5", "project": "x", "name": feature_slug,
            "epics": epics,
        }, indent=2))

    def write_killswitch(self, auto_reconcile: bool):
        self.shield_json.write_text(json.dumps({"backlog": {"auto_reconcile": auto_reconcile}}))


@contextmanager
def scaffold():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backlog = root / "backlog.json"
        backlog.write_text(json.dumps({"schema_version": 1, "entries": []}))
        shield_dir = root / "docs" / "shield"
        shield_dir.mkdir(parents=True)
        yield World(
            root=root,
            backlog=backlog,
            manifest=shield_dir / "manifest.json",
            shield_json=root / "shield.json",
            removed_log=root / "removed.log",
        )


def _story():
    """Minimal valid stories[] entry so plan.json passes its own schema."""
    return [{
        "id": "EPIC-1-S1", "name": "s", "status": "ready",
        "description": "s", "tasks": ["s"], "acceptance_criteria": ["s"],
    }]


# ----- assertion harness ---------------------------------------------------

class CaseFailure(Exception):
    pass


def _expect(condition, message):
    if not condition:
        raise CaseFailure(message)


# ----- cases ---------------------------------------------------------------

def case_capture_user_and_agent_both_succeed():
    with scaffold() as w:
        a = capture("u idea", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        b = capture("agent idea", feature="auth", epic="Session mgmt", source="agent", path=w.backlog)
        doc = read_backlog(w.backlog)
        _expect(len(doc["entries"]) == 2, f"expected 2 entries, got {len(doc['entries'])}")
        _expect([e["id"] for e in doc["entries"]] == [a, b], "order/identity drift")
        _expect(doc["entries"][0]["source"] == "user", "first entry source wrong")
        _expect(doc["entries"][1]["source"] == "agent", "second entry source wrong")


def case_view_renders_with_status_badges_pinned_format():
    with scaffold() as w:
        w.write_manifest([
            {"name": "auth", "artifacts": {"research": True, "prd": True, "plan_json": False}}
        ])
        capture("rotate", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        manifest = json.loads(w.manifest.read_text())
        out = render(read_backlog(w.backlog), manifest=manifest)
        _expect("research ✓" in out, f"missing research badge: {out!r}")
        _expect("prd ✓" in out, f"missing prd badge: {out!r}")
        _expect("plan –" in out, f"missing plan – badge: {out!r}")
        _expect("(auth / Session mgmt, user)" in out, f"line-format drift: {out!r}")


def case_empty_view_message():
    with scaffold() as w:
        out = render(read_backlog(w.backlog))
        _expect("no entries" in out.lower(), f"missing empty-message: {out!r}")


def case_manual_remove_deletes_entry():
    with scaffold() as w:
        a = capture("a", feature="auth", epic="e", source="user", path=w.backlog)
        capture("b", feature="auth", epic="e", source="user", path=w.backlog)
        removed = remove(a, path=w.backlog)
        _expect(removed is not None and removed["id"] == a, "manual remove returned wrong entry")
        _expect(len(read_backlog(w.backlog)["entries"]) == 1, "manual remove didn't reduce count")


def case_eager_prune_removes_when_epic_landed():
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Session mgmt", "stories": _story()}])
        eid = capture("x", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        decision = eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(decision is not None and decision.verdict == Verdict.REMOVE, "expected REMOVE")
        _expect(read_backlog(w.backlog)["entries"] == [], "entry not removed")
        _expect(w.removed_log.exists(), "recovery log missing")


def case_eager_prune_idempotent_on_already_gone():
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Session mgmt", "stories": _story()}])
        decision = eager_prune(
            "00000000-0000-4000-8000-000000000000",
            backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(decision is None, "expected None for absent id (idempotent no-op)")
        _expect(not w.removed_log.exists(), "no-op MUST NOT write recovery log")


def case_eager_prune_respects_kill_switch():
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Session mgmt", "stories": _story()}])
        w.write_killswitch(auto_reconcile=False)
        eid = capture("x", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        decision = eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(decision is None, "kill switch must suppress eager prune")
        _expect(len(read_backlog(w.backlog)["entries"]) == 1, "entry must survive kill-switch")


def case_lazy_sweep_removes_landed_entries():
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Session mgmt", "stories": _story()}])
        landed = capture("a", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        stays = capture("b", feature="auth", epic="Pending", source="user", path=w.backlog)
        decisions = lazy_sweep(
            backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(len(decisions) == 1, f"expected 1 removal, got {len(decisions)}")
        remaining = [e["id"] for e in read_backlog(w.backlog)["entries"]]
        _expect(remaining == [stays], f"unexpected remaining: {remaining}")
        _expect(landed not in remaining, "landed entry was not removed")


def case_eager_then_sweep_no_double_remove():
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Session mgmt", "stories": _story()}])
        eid = capture("x", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        decisions = lazy_sweep(
            backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(decisions == [], "second pass must be a no-op (idempotent)")


def case_epic_renumber_across_replan_still_resolves():
    """Same epic NAME, different EPIC-N id (after re-/plan reorder) → still REMOVE."""
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        # Before re-/plan, epic was EPIC-7 'Session mgmt'.
        # After re-/plan, same name, now EPIC-1.
        w.write_plan("auth", [
            {"id": "EPIC-1", "name": "Session mgmt", "stories": _story()},
        ])
        eid = capture("x", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        decision = eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(decision is not None and decision.verdict == Verdict.REMOVE,
                "epic-name match must survive id reorder")


def case_cross_feature_epic_collision_stays_ambiguous():
    """Same epic NAME in 2 features → STAY_AMBIGUOUS, entry not removed."""
    with scaffold() as w:
        w.write_manifest([
            {"name": "auth", "artifacts": {"plan_json": True}},
            {"name": "billing", "artifacts": {"plan_json": True}},
        ])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Refresh tokens", "stories": _story()}])
        w.write_plan("billing", [{"id": "EPIC-1", "name": "Refresh tokens", "stories": _story()}])
        eid = capture("x", feature="auth", epic="Refresh tokens", source="user", path=w.backlog)
        decision = eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(decision is not None, "expected a decision object on real-shaped manifest")
        _expect(decision.verdict == Verdict.STAY_AMBIGUOUS, f"got {decision.verdict}")
        _expect(len(read_backlog(w.backlog)["entries"]) == 1, "entry must remain")


def case_malformed_manifest_stays_doubt_no_crash():
    """A malformed plan.json shape → STAY_DOUBT (or NO_MATCH), never an exception."""
    with scaffold() as w:
        # Write a plan_json file that's invalid JSON.
        feat = w.root / "docs" / "shield" / "auth"
        feat.mkdir(parents=True)
        (feat / "plan.json").write_text("{ not json")
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        eid = capture("x", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        # Should NOT raise even with malformed plan.
        decision = eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        _expect(decision is not None, "expected a decision object on malformed plan")
        _expect(decision.verdict != Verdict.REMOVE, f"must not remove on doubt, got {decision.verdict}")
        _expect(len(read_backlog(w.backlog)["entries"]) == 1, "entry must remain")


def case_concurrency_lost_update_refused():
    """A concurrent on-disk change between read and replace raises lost_update."""
    from shield_backlog import store as store_mod
    with scaffold() as w:
        capture("first", feature="auth", epic="e", source="user", path=w.backlog)

        orig = store_mod._atomic_write

        def racing(path, doc, *, expected):
            cur = json.loads(path.read_text())
            cur["entries"].append({
                "id": "11111111-1111-4111-8111-111111111111",
                "order": 99, "kind": "task", "source": "agent",
                "feature": "auth", "epic": "e", "text": "concurrent",
            })
            path.write_text(json.dumps(cur))
            try:
                return orig(path, doc, expected=expected)
            except BacklogInvalid:
                raise

        store_mod._atomic_write = racing  # type: ignore[attr-defined]
        try:
            try:
                capture("second", feature="auth", epic="e", source="user", path=w.backlog)
            except BacklogInvalid as exc:
                _expect(exc.code == "lost_update", f"wrong code: {exc.code}")
                return
            raise CaseFailure("expected BacklogInvalid(lost_update) but capture succeeded")
        finally:
            store_mod._atomic_write = orig  # type: ignore[attr-defined]


def case_write_side_schema_refusal_leaves_store_unchanged():
    """capture() that would produce a schema-invalid doc raises BacklogInvalid
    and leaves backlog.json byte-unchanged (security P1-b)."""
    with scaffold() as w:
        before = w.backlog.read_bytes()
        # Force a schema failure: source='robot' is rejected at the helper boundary.
        try:
            capture("x", feature="auth", epic="e", source="robot", path=w.backlog)  # type: ignore[arg-type]
        except BacklogInvalid as exc:
            _expect(exc.code == "unknown_source_enum", f"got {exc.code}")
        else:
            raise CaseFailure("expected BacklogInvalid; capture succeeded")
        after = w.backlog.read_bytes()
        _expect(before == after, "store must be byte-unchanged after refusal")


def case_no_stamping_plan_json_byte_unchanged_post_promotion():
    """F6: after eager prune, plan.json + story records are byte-unchanged."""
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Session mgmt", "stories": _story()}])
        plan_path = w.root / "docs" / "shield" / "auth" / "plan.json"
        before = plan_path.read_bytes()
        eid = capture("x", feature="auth", epic="Session mgmt", source="user", path=w.backlog)
        eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        after = plan_path.read_bytes()
        _expect(before == after, "plan.json must be byte-unchanged after promotion (F6)")


def case_ordering_seam_recovery_rehearsal():
    """Recovery log is appended BEFORE the destructive remove. After a normal
    eager_prune, the log carries the full pre-remove entry — sufficient to
    recover by re-capturing."""
    with scaffold() as w:
        w.write_manifest([{"name": "auth", "artifacts": {"plan_json": True}}])
        w.write_plan("auth", [{"id": "EPIC-1", "name": "Session mgmt", "stories": _story()}])
        eid = capture("rotate tokens", feature="auth", epic="Session mgmt",
                      source="user", path=w.backlog)
        original = next(e for e in read_backlog(w.backlog)["entries"] if e["id"] == eid)
        eager_prune(
            eid, backlog_path=w.backlog, manifest_path=w.manifest,
            shield_json_path=w.shield_json, removed_log_path=w.removed_log,
        )
        records = [json.loads(l) for l in w.removed_log.read_text().splitlines()]
        _expect(len(records) == 1, "exactly one recovery record expected")
        _expect(records[0]["entry"] == original, "recovery record must carry full entry")

        # Replay: capture from the record to confirm the data round-trips.
        rec = records[0]["entry"]
        re_id = capture(rec["text"], feature=rec["feature"], epic=rec["epic"],
                        source=rec["source"], kind=rec["kind"], path=w.backlog)
        _expect(re_id != eid, "replay mints a new uuid4 id")
        _expect(read_backlog(w.backlog)["entries"][0]["text"] == rec["text"],
                "replayed text must match recovered text")


def case_validator_rejects_duplicate_entry_id():
    """Subprocess test of the CLI validator: a backlog with two same-id entries
    fails with named error 'duplicate_entry_id' (EPIC-1-S1 AC)."""
    with scaffold() as w:
        w.backlog.write_text(json.dumps({
            "schema_version": 1,
            "entries": [
                {"id": "5b3f1f9c-8e9a-4a31-9d4c-1c2e9e8a4b51", "order": 1, "kind": "task",
                 "source": "user", "feature": "f", "epic": "e", "text": "a"},
                {"id": "5b3f1f9c-8e9a-4a31-9d4c-1c2e9e8a4b51", "order": 2, "kind": "task",
                 "source": "user", "feature": "f", "epic": "e", "text": "b"},
            ],
        }))
        proc = subprocess.run(
            [sys.executable, str(VALIDATE_BACKLOG), str(w.backlog)],
            capture_output=True, text=True,
        )
        _expect(proc.returncode == 1, f"expected exit 1, got {proc.returncode}")
        _expect("duplicate_entry_id" in proc.stderr,
                f"missing named error in stderr: {proc.stderr!r}")


# ----- runner --------------------------------------------------------------

CASES = [
    case_capture_user_and_agent_both_succeed,
    case_view_renders_with_status_badges_pinned_format,
    case_empty_view_message,
    case_manual_remove_deletes_entry,
    case_eager_prune_removes_when_epic_landed,
    case_eager_prune_idempotent_on_already_gone,
    case_eager_prune_respects_kill_switch,
    case_lazy_sweep_removes_landed_entries,
    case_eager_then_sweep_no_double_remove,
    case_epic_renumber_across_replan_still_resolves,
    case_cross_feature_epic_collision_stays_ambiguous,
    case_malformed_manifest_stays_doubt_no_crash,
    case_concurrency_lost_update_refused,
    case_write_side_schema_refusal_leaves_store_unchanged,
    case_no_stamping_plan_json_byte_unchanged_post_promotion,
    case_ordering_seam_recovery_rehearsal,
    case_validator_rejects_duplicate_entry_id,
]


def main() -> int:
    print(f"=== eval suite: backlog ({len(CASES)} cases) ===")
    passed = 0
    failed = 0
    for case in CASES:
        name = case.__name__.removeprefix("case_")
        try:
            case()
        except CaseFailure as exc:
            print(f"  FAIL {name}: {exc}")
            failed += 1
            continue
        except Exception as exc:  # pragma: no cover
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
            continue
        passed += 1
        print(f"  PASS {name}")
    print(f"=== {passed}/{len(CASES)} cases passed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
