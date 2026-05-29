"""Backlog reconciler — the single "epic landed" predicate (TRD §5 F8).

`reconcile(entry, *, manifest, plans) -> RemovalDecision` is a **pure function**
over already-read documents. The eager-prune and lazy-sweep paths share this
one engine — no divergent logic.

Predicate (LOCKED, plan-review 2026-05-29 P0-2):
  - Match by casefold + collapsed-whitespace exact epic NAME, for BOTH
    existing and proposed-new entries.
  - Story status is NEVER consulted.
  - Epic id (EPIC-N) is a positional within-plan slot — NEVER a cross-plan key.
  - Cross-feature epic-name collision ⇒ STAY_AMBIGUOUS (the one place a wrong
    removal would be plausible; PRD §10 risk / §14 trigger).
  - A prd-only feature (no plan.json) ⇒ STAY_NO_MATCH.
  - Unrecognized manifest/plan shape ⇒ STAY_DOUBT, never an exception.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from shield_backlog.suggester import normalize


class Verdict(str, Enum):
    REMOVE = "REMOVE"
    STAY_AMBIGUOUS = "STAY_AMBIGUOUS"
    STAY_NO_MATCH = "STAY_NO_MATCH"
    STAY_DOUBT = "STAY_DOUBT"


@dataclass(frozen=True)
class RemovalDecision:
    """Pure-data result of one reconciliation call. F9 log fields are pinned
    here so eager and lazy paths emit the same structured log line."""
    verdict: Verdict
    feature: str
    epic: str
    match_kind: str | None      # "name" on REMOVE; None on STAY_*
    gating_plan_json_path: str | None  # derived path on REMOVE; None otherwise
    reason: str                 # human-readable rationale (includes doubt-warning text)


# ----- internals -----------------------------------------------------------

def _all_matching_features(entry_epic_norm: str, plans: dict[str, Any]) -> list[str]:
    """Walk every (feature, epic) in `plans` and return feature names whose
    plan.json contains an epic with the matching normalized name. Drops
    plans whose shape is unrecognized (silently — caller treats as 'doubt' via
    a separate code path)."""
    matches: list[str] = []
    for feat, plan in plans.items():
        if not isinstance(plan, dict):
            continue
        epics = plan.get("epics")
        if not isinstance(epics, list):
            continue
        for epic in epics:
            if not isinstance(epic, dict):
                continue
            name = epic.get("name")
            if not isinstance(name, str):
                continue
            if normalize(name) == entry_epic_norm:
                matches.append(feat)
                break  # one hit per feature is enough
    return matches


def _manifest_shape_ok(manifest: Any) -> bool:
    if not isinstance(manifest, dict):
        return False
    features = manifest.get("features")
    return isinstance(features, list)


def _feature_has_plan(feature: str, manifest: dict[str, Any]) -> bool | None:
    """Return True if manifest says the feature has a plan.json, False if not,
    None if the feature is absent from manifest."""
    for feat in manifest.get("features") or []:
        if not isinstance(feat, dict):
            continue
        if feat.get("name") == feature:
            return bool((feat.get("artifacts") or {}).get("plan_json"))
    return None


# ----- public --------------------------------------------------------------

def reconcile(
    entry: dict[str, Any],
    *,
    manifest: dict[str, Any] | None,
    plans: dict[str, dict[str, Any]] | None,
) -> RemovalDecision:
    """Decide whether `entry` should be removed. Pure function — no I/O, no
    side effects. The eager-prune and lazy-sweep callers each invoke this
    and act on the verdict.
    """
    feature = entry.get("feature") or ""
    epic_name = entry.get("epic") or ""

    # Doubt: the inputs themselves don't conform to the contract.
    if not _manifest_shape_ok(manifest):
        return RemovalDecision(
            verdict=Verdict.STAY_DOUBT,
            feature=feature, epic=epic_name,
            match_kind=None, gating_plan_json_path=None,
            reason="unrecognized manifest shape — never removing on doubt",
        )
    if not isinstance(plans, dict):
        plans = {}

    if not feature or not epic_name:
        return RemovalDecision(
            verdict=Verdict.STAY_DOUBT,
            feature=feature, epic=epic_name,
            match_kind=None, gating_plan_json_path=None,
            reason="entry missing feature or epic — never removing on doubt",
        )

    # prd-only feature → no plan.json yet → no removal.
    has_plan = _feature_has_plan(feature, manifest)  # type: ignore[arg-type]
    if has_plan is None:
        return RemovalDecision(
            verdict=Verdict.STAY_NO_MATCH,
            feature=feature, epic=epic_name,
            match_kind=None, gating_plan_json_path=None,
            reason=f"feature {feature!r} not in manifest.features[]",
        )
    if has_plan is False:
        return RemovalDecision(
            verdict=Verdict.STAY_NO_MATCH,
            feature=feature, epic=epic_name,
            match_kind=None, gating_plan_json_path=None,
            reason=f"feature {feature!r} has no plan.json (prd-only) — entry stays",
        )

    epic_norm = normalize(epic_name)
    matching_features = _all_matching_features(epic_norm, plans)

    if not matching_features:
        return RemovalDecision(
            verdict=Verdict.STAY_NO_MATCH,
            feature=feature, epic=epic_name,
            match_kind=None, gating_plan_json_path=None,
            reason=f"no epic with normalized name {epic_norm!r} found in any plan.json",
        )

    if len(matching_features) >= 2:
        return RemovalDecision(
            verdict=Verdict.STAY_AMBIGUOUS,
            feature=feature, epic=epic_name,
            match_kind=None, gating_plan_json_path=None,
            reason=(
                f"epic name {epic_name!r} appears in {len(matching_features)} features "
                f"({matching_features}) — cross-feature collision, entry stays"
            ),
        )

    # Exactly one feature's plan has the matching epic.
    matched_feature = matching_features[0]
    if matched_feature != feature:
        # Single match, but in a different feature than the entry's. Stay.
        return RemovalDecision(
            verdict=Verdict.STAY_NO_MATCH,
            feature=feature, epic=epic_name,
            match_kind=None, gating_plan_json_path=None,
            reason=(
                f"single epic-name match is in feature {matched_feature!r}, "
                f"not the entry's feature {feature!r} — entry stays"
            ),
        )

    return RemovalDecision(
        verdict=Verdict.REMOVE,
        feature=feature, epic=epic_name,
        match_kind="name",
        gating_plan_json_path=f"docs/shield/{feature}/plan.json",
        reason=f"epic {epic_name!r} landed in {feature}'s plan.json — eligible for removal",
    )
