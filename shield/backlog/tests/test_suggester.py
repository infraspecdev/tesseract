"""Tests for shield_backlog.suggester — exact-normalized match for features + epics
(EPIC-2-S2)."""
from shield_backlog.suggester import (
    Candidate,
    normalize,
    suggest_epic,
    suggest_feature,
)


# ----- normalize -----------------------------------------------------------

def test_normalize_casefold_and_collapse():
    assert normalize("Session   Management") == "session management"
    assert normalize("AUTH") == "auth"
    assert normalize("  spaces  in  text  ") == "spaces in text"


# ----- suggest_feature -----------------------------------------------------

def test_suggest_feature_returns_match_when_text_mentions_it():
    manifest = {"features": [
        {"name": "auth", "artifacts": {}},
        {"name": "billing", "artifacts": {}},
    ]}
    assert suggest_feature("rotate the auth refresh tokens", manifest=manifest) == ["auth"]


def test_suggest_feature_returns_empty_when_no_match():
    manifest = {"features": [{"name": "auth", "artifacts": {}}]}
    assert suggest_feature("totally unrelated text", manifest=manifest) == []


def test_suggest_feature_handles_two_way_tie():
    """If text mentions BOTH features by name, both are surfaced and the
    caller auto-picks neither."""
    manifest = {"features": [
        {"name": "auth", "artifacts": {}},
        {"name": "billing", "artifacts": {}},
    ]}
    matches = suggest_feature("auth and billing both broken", manifest=manifest)
    assert set(matches) == {"auth", "billing"}


def test_suggest_feature_unrecognized_shape_returns_empty():
    """A malformed manifest (no features key) returns [] — no crash."""
    assert suggest_feature("auth", manifest=None) == []
    assert suggest_feature("auth", manifest={}) == []
    assert suggest_feature("auth", manifest={"features": "not a list"}) == []


def test_suggest_feature_case_insensitive():
    manifest = {"features": [{"name": "Auth", "artifacts": {}}]}
    assert suggest_feature("the AUTH module", manifest=manifest) == ["Auth"]


def test_suggest_feature_does_not_match_substring_inside_word():
    """A feature 'auth' should NOT match 'authenticate' (whole-word match)."""
    manifest = {"features": [{"name": "auth", "artifacts": {}}]}
    assert suggest_feature("authenticate the user", manifest=manifest) == []


def test_suggest_feature_resolves_to_folder_slug_invariant():
    """The returned value IS the folder slug. Confirms the P1-3 invariant."""
    manifest = {"features": [
        {"name": "backlog-20260527", "artifacts": {}},
    ]}
    # When text mentions the slug, suggestion returns it verbatim.
    assert suggest_feature("look at backlog-20260527 stuff", manifest=manifest) == [
        "backlog-20260527"
    ]


# ----- suggest_epic --------------------------------------------------------

def test_suggest_epic_matches_by_name_not_id():
    """An entry whose text mentions an epic name is surfaced, regardless of EPIC-N id."""
    plans = {"auth": {"epics": [
        {"id": "EPIC-3", "name": "Session management"},
        {"id": "EPIC-7", "name": "Refresh tokens"},
    ]}}
    matches = suggest_epic("touch up refresh tokens", feature="auth", plans=plans)
    assert len(matches) == 1
    assert matches[0].name == "Refresh tokens"
    # id is informational; the test asserts we match by name not by id slot.
    assert matches[0].epic_id == "EPIC-7"
    assert matches[0].match_kind == "name"


def test_suggest_epic_reorder_still_resolves():
    """Same epic NAME with a DIFFERENT EPIC-N id (e.g., after a re-/plan reorder)
    still resolves correctly — the name is the key."""
    plans = {"auth": {"epics": [
        {"id": "EPIC-1", "name": "Session management"},  # now slot 1, was slot 5
    ]}}
    matches = suggest_epic("session management feedback", feature="auth", plans=plans)
    assert len(matches) == 1
    assert matches[0].name == "Session management"


def test_suggest_epic_returns_empty_when_feature_absent():
    """No plan.json for the feature → no candidates (caller falls back to proposed-new)."""
    assert suggest_epic("anything", feature="missing", plans={"auth": {"epics": []}}) == []


def test_suggest_epic_unrecognized_shape_returns_empty():
    assert suggest_epic("x", feature="auth", plans=None) == []
    assert suggest_epic("x", feature="auth", plans={"auth": None}) == []
    assert suggest_epic("x", feature="auth", plans={"auth": {"epics": "bad"}}) == []


def test_suggest_epic_tie_surfaced():
    """Two epics matching the same text → both returned, caller picks none."""
    plans = {"auth": {"epics": [
        {"id": "EPIC-1", "name": "Login flow"},
        {"id": "EPIC-2", "name": "Refresh tokens"},
    ]}}
    matches = suggest_epic("login flow and refresh tokens", feature="auth", plans=plans)
    assert {m.name for m in matches} == {"Login flow", "Refresh tokens"}
