"""Tests for shield_backlog.reconciler — name-only matching, never-remove-on-doubt,
read-contract drift tolerance, F9 log fields (EPIC-3-S2)."""
from shield_backlog.reconciler import (
    RemovalDecision,
    Verdict,
    reconcile,
)


# ----- fixtures (inline) ---------------------------------------------------

def _entry(feature="auth", epic="Session management", text="t", **extra):
    base = {
        "id": "5b3f1f9c-8e9a-4a31-9d4c-1c2e9e8a4b51",
        "order": 1, "kind": "task", "source": "user",
        "feature": feature, "epic": epic, "text": text,
    }
    base.update(extra)
    return base


def _manifest_with(features):
    return {"schema_version": 2, "features": features}


# ----- happy path ----------------------------------------------------------

def test_remove_when_epic_lands_in_plan():
    """Entry whose feature has plan_json=True AND plan.epics[].name matches → REMOVE."""
    manifest = _manifest_with([
        {"name": "auth", "artifacts": {"plan_json": True}},
    ])
    plans = {"auth": {"epics": [{"id": "EPIC-1", "name": "Session management"}]}}
    decision = reconcile(_entry(), manifest=manifest, plans=plans)
    assert decision.verdict == Verdict.REMOVE
    assert decision.match_kind == "name"
    assert decision.gating_plan_json_path == "docs/shield/auth/plan.json"
    # F9 log fields all present:
    assert decision.feature == "auth"
    assert decision.epic == "Session management"
    assert decision.reason  # human-readable


def test_remove_when_epic_renumbered_across_replan():
    """Same epic NAME, different EPIC-N id (slot reassigned by re-/plan) — STILL REMOVE.
    This is the P0-2 invariant: match by name, never by id."""
    manifest = _manifest_with([{"name": "auth", "artifacts": {"plan_json": True}}])
    plans = {"auth": {"epics": [
        # was slot 7 before re-/plan, now slot 1; name unchanged → still matches
        {"id": "EPIC-1", "name": "Session management"},
    ]}}
    decision = reconcile(_entry(), manifest=manifest, plans=plans)
    assert decision.verdict == Verdict.REMOVE


def test_normalize_match_ignores_case_and_whitespace():
    """Entry epic 'session  MANAGEMENT' should still match plan 'Session management'."""
    manifest = _manifest_with([{"name": "auth", "artifacts": {"plan_json": True}}])
    plans = {"auth": {"epics": [{"id": "EPIC-1", "name": "Session management"}]}}
    decision = reconcile(
        _entry(epic="session  MANAGEMENT"),
        manifest=manifest, plans=plans,
    )
    assert decision.verdict == Verdict.REMOVE


# ----- never-remove-on-doubt ----------------------------------------------

def test_prd_only_feature_stays():
    """Feature exists in manifest but plan_json=False → STAY_NO_MATCH (prd-only)."""
    manifest = _manifest_with([{"name": "auth", "artifacts": {"plan_json": False, "prd": True}}])
    plans = {}
    decision = reconcile(_entry(), manifest=manifest, plans=plans)
    assert decision.verdict == Verdict.STAY_NO_MATCH
    assert "prd-only" in decision.reason


def test_feature_absent_from_manifest_stays():
    """Entry feature not in manifest at all → STAY_NO_MATCH."""
    manifest = _manifest_with([])  # no features
    plans = {}
    decision = reconcile(_entry(), manifest=manifest, plans=plans)
    assert decision.verdict == Verdict.STAY_NO_MATCH


def test_no_match_in_any_plan_stays():
    manifest = _manifest_with([{"name": "auth", "artifacts": {"plan_json": True}}])
    plans = {"auth": {"epics": [{"id": "EPIC-1", "name": "Different epic"}]}}
    decision = reconcile(_entry(), manifest=manifest, plans=plans)
    assert decision.verdict == Verdict.STAY_NO_MATCH


def test_cross_feature_collision_is_ambiguous():
    """Same epic NAME appears in TWO different features' plans → STAY_AMBIGUOUS.
    PRD §10 / §14 risk — the one place a wrong removal would be plausible."""
    manifest = _manifest_with([
        {"name": "auth", "artifacts": {"plan_json": True}},
        {"name": "billing", "artifacts": {"plan_json": True}},
    ])
    plans = {
        "auth": {"epics": [{"id": "EPIC-1", "name": "Refresh tokens"}]},
        "billing": {"epics": [{"id": "EPIC-2", "name": "Refresh tokens"}]},
    }
    decision = reconcile(
        _entry(feature="auth", epic="Refresh tokens"),
        manifest=manifest, plans=plans,
    )
    assert decision.verdict == Verdict.STAY_AMBIGUOUS
    assert "cross-feature collision" in decision.reason


def test_single_match_in_wrong_feature_stays():
    """The only matching plan is NOT the entry's feature → STAY_NO_MATCH.
    Don't remove auth's entry when only billing's plan has the epic."""
    manifest = _manifest_with([
        {"name": "auth", "artifacts": {"plan_json": True}},
        {"name": "billing", "artifacts": {"plan_json": True}},
    ])
    plans = {
        "auth": {"epics": []},  # auth's plan has no matching epic
        "billing": {"epics": [{"id": "EPIC-1", "name": "Refresh tokens"}]},
    }
    decision = reconcile(
        _entry(feature="auth", epic="Refresh tokens"),
        manifest=manifest, plans=plans,
    )
    assert decision.verdict == Verdict.STAY_NO_MATCH


# ----- drift tolerance: never crash ---------------------------------------

def test_malformed_manifest_yields_stay_doubt_not_exception():
    decision = reconcile(_entry(), manifest=None, plans={})
    assert decision.verdict == Verdict.STAY_DOUBT


def test_malformed_plan_shape_treated_as_doubt():
    """A plan.json with epics='not a list' → that plan is silently skipped,
    so the entry stays (no false-positive removal). Never an exception."""
    manifest = _manifest_with([{"name": "auth", "artifacts": {"plan_json": True}}])
    plans = {"auth": {"epics": "not a list"}}
    decision = reconcile(_entry(), manifest=manifest, plans=plans)
    assert decision.verdict in {Verdict.STAY_NO_MATCH, Verdict.STAY_DOUBT}


def test_entry_missing_fields_treated_as_doubt():
    manifest = _manifest_with([{"name": "auth", "artifacts": {"plan_json": True}}])
    decision = reconcile({"id": "x"}, manifest=manifest, plans={})
    assert decision.verdict == Verdict.STAY_DOUBT


# ----- F9 log fields -------------------------------------------------------

def test_remove_decision_carries_all_f9_log_fields():
    """Every REMOVE decision must carry the F9 fields used by the structured
    log line: entry id (passed in by caller), feature, epic, match_kind,
    gating_plan_json_path, plus a reason."""
    manifest = _manifest_with([{"name": "auth", "artifacts": {"plan_json": True}}])
    plans = {"auth": {"epics": [{"id": "EPIC-7", "name": "Session management"}]}}
    decision = reconcile(_entry(), manifest=manifest, plans=plans)
    assert isinstance(decision, RemovalDecision)
    assert decision.verdict == Verdict.REMOVE
    assert decision.feature == "auth"
    assert decision.epic == "Session management"
    assert decision.match_kind == "name"
    assert decision.gating_plan_json_path == "docs/shield/auth/plan.json"
    assert decision.reason
