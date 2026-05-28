"""Tests for shield/scripts/lld_anchor_heuristic.py.

Token-overlap anchor selection for /implement's design_refs[] back-fill:
given a story name and a template's slug allow-list, pick the best-matching
section anchor. Three match types: exact-match, heuristic, fallback.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "shield" / "scripts"))

from lld_anchor_heuristic import select_anchor  # noqa: E402


BACKEND_SLUGS = [
    "overview",
    "scope-and-non-goals",
    "module-layout",
    "data-model",
    "api-contracts",
    "sequence-flows",
    "error-handling",
    "concurrency-and-state",
    "configuration",
    "observability",
    "security-and-privacy",
    "performance-and-scaling",
    "open-questions",
    "changelog",
]


def test_exact_match_when_story_name_matches_slug_tokens():
    """Story 'data model' tokenizes to {data, model}; slug 'data-model' tokenizes to {data, model}; Jaccard 1.0."""
    slug, match_type = select_anchor("Data model", BACKEND_SLUGS)
    assert slug == "data-model"
    assert match_type == "exact-match"


def test_exact_match_case_insensitive():
    """Case difference doesn't affect exact-match."""
    slug, match_type = select_anchor("API Contracts", BACKEND_SLUGS)
    assert slug == "api-contracts"
    assert match_type == "exact-match"


def test_heuristic_match_partial_overlap():
    """'Implement data validation logic' overlaps 'data' with 'data-model'; expect heuristic."""
    slug, match_type = select_anchor("Implement data validation logic", BACKEND_SLUGS)
    assert slug == "data-model"
    assert match_type == "heuristic"


def test_fallback_to_overview_on_zero_overlap():
    """Story with no token overlap → fallback to #overview."""
    slug, match_type = select_anchor("xyzzy plugh", BACKEND_SLUGS)
    assert slug == "overview"
    assert match_type == "fallback"


def test_tie_break_by_slug_order():
    """When two slugs have equal Jaccard score, the one appearing earlier in the list wins."""
    # 'configuration changelog' — both overlap by 1 with 1/2 score; 'configuration' at index 8 wins over 'changelog' at index 13.
    slug, match_type = select_anchor("configuration changelog", BACKEND_SLUGS)
    assert slug == "configuration"
    assert match_type == "heuristic"


def test_punctuation_and_whitespace_normalised():
    """Punctuation / extra whitespace doesn't affect tokenization."""
    slug, match_type = select_anchor("Data, model!", BACKEND_SLUGS)
    assert slug == "data-model"
    assert match_type == "exact-match"
