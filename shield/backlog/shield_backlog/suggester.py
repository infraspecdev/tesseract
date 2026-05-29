"""Epic suggester — at capture time, propose feature + epic candidates.

LOCKED (plan-review 2026-05-27/29):
  - Match = exact normalized: casefold + collapsed whitespace, word-boundary.
  - Both existing AND proposed-new epics match by NAME — positional EPIC-N
    id is NOT a cross-plan identity.
  - Ties (>=2 matches) are surfaced in full; the caller auto-picks none.
  - Suggestion never blocks capture: an empty result list is valid.

The same `normalize()` is reused by the reconciler so the matching predicate is
single-sourced.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def normalize(s: str) -> str:
    """Canonical normalization: casefold + collapsed whitespace.
    The reconciler reuses this so suggest/reconcile match the same way."""
    if not isinstance(s, str):
        return ""
    return " ".join(s.split()).casefold()


def _appears_as_whole_word(needle_norm: str, haystack_norm: str) -> bool:
    """Word-boundary match on already-normalized strings. Hyphens are treated
    as word characters so kebab-case slugs match verbatim (no partial matches
    into hyphenated names)."""
    if not needle_norm:
        return False
    # Word characters here include letters, digits, underscore, hyphen.
    pattern = r"(?:^|[^\w-])" + re.escape(needle_norm) + r"(?:[^\w-]|$)"
    return re.search(pattern, haystack_norm) is not None


@dataclass(frozen=True)
class Candidate:
    """An epic suggestion. `epic_id` is informational only — never used for
    matching or removal (it's a positional within-plan slot reassigned on
    every re-/plan run). `name` is the source of truth for matching."""
    epic_id: str
    name: str
    match_kind: str = "name"


def suggest_feature(text: str, *, manifest: dict[str, Any] | None) -> list[str]:
    """Return manifest.features[].name values whose normalized name appears as
    a whole word in the normalized text. Empty list ⇒ no match (caller falls
    back to proposed-new).

    Read-contract drift tolerance: an unrecognized manifest shape returns [].
    `features[].name` IS the feature folder slug (invariant pinned in
    backlog SKILL.md), so the caller can both render and reconcile by name.
    """
    if not isinstance(manifest, dict):
        return []
    features = manifest.get("features")
    if not isinstance(features, list):
        return []

    text_norm = normalize(text)
    matches: list[str] = []
    seen: set[str] = set()
    for feat in features:
        if not isinstance(feat, dict):
            continue
        name = feat.get("name")
        if not isinstance(name, str) or not name:
            continue
        if name in seen:
            continue
        if _appears_as_whole_word(normalize(name), text_norm):
            matches.append(name)
            seen.add(name)
    return matches


def suggest_epic(
    text: str,
    *,
    feature: str,
    plans: dict[str, dict[str, Any]] | None,
) -> list[Candidate]:
    """Return epic Candidates from plans[feature] whose normalized epic NAME
    appears as a whole word in the normalized text.

    `plans` maps feature-slug → already-parsed plan.json. Path derivation is
    the caller's job (`docs/shield/<feature>/plan.json`); the suggester is a
    pure function over read documents.

    Matching is by epic NAME — never by positional EPIC-N id. Ties (>=2)
    are returned in full; the caller surfaces them all and auto-picks none.
    """
    if not isinstance(plans, dict):
        return []
    plan = plans.get(feature)
    if not isinstance(plan, dict):
        return []
    epics = plan.get("epics")
    if not isinstance(epics, list):
        return []

    text_norm = normalize(text)
    matches: list[Candidate] = []
    seen_names: set[str] = set()
    for epic in epics:
        if not isinstance(epic, dict):
            continue
        name = epic.get("name")
        if not isinstance(name, str) or not name:
            continue
        norm_name = normalize(name)
        if norm_name in seen_names:
            continue
        if _appears_as_whole_word(norm_name, text_norm):
            matches.append(Candidate(
                epic_id=str(epic.get("id") or ""),
                name=name,
            ))
            seen_names.add(norm_name)
    return matches
