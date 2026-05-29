"""shield/scripts/lld_anchor_heuristic.py

Token-overlap anchor selection for /implement's design_refs[] back-fill.
Given a story name and a template's slug allow-list, returns the best-matching
section anchor and the match-type label.

Algorithm:
  1. Tokenize story name: lowercase, split on whitespace and punctuation.
  2. For each slug in the allow-list, tokenize the slug (split on '-').
  3. Score each slug by Jaccard similarity (|A∩B| / |A∪B|) against the story tokens.
  4. Pick the highest-scoring slug; tie-break by allow-list order.
  5. If max score == 1.0: match_type = 'exact-match'.
     If max score in (0, 1.0):  match_type = 'heuristic'.
     If max score == 0:          slug = 'overview', match_type = 'fallback'.

Examples:
  story 'Data model'                → ('data-model', 'exact-match')
  story 'Implement data validation' → ('data-model', 'heuristic')   # 'data' overlap
  story 'xyzzy plugh'               → ('overview', 'fallback')
"""
from __future__ import annotations

import re
from typing import Sequence


_TOKEN_SPLIT = re.compile(r"[\s\-_,.;:!?/()\[\]{}'\"`]+")


def _tokenize(text: str) -> set[str]:
    """Lowercase and split on whitespace + common punctuation; drop empties."""
    return {tok for tok in _TOKEN_SPLIT.split(text.lower()) if tok}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def select_anchor(
    story_name: str, slugs: Sequence[str], fallback: str = "overview"
) -> tuple[str, str]:
    """Pick the best-matching slug for a story name.

    Returns (slug, match_type) where match_type ∈ {'exact-match', 'heuristic', 'fallback'}.
    Tie-break: higher position in `slugs` (lower index) wins.
    """
    story_tokens = _tokenize(story_name)
    if not story_tokens:
        return fallback, "fallback"

    best_slug = fallback
    best_score = 0.0
    for slug in slugs:
        slug_tokens = _tokenize(slug)
        score = _jaccard(story_tokens, slug_tokens)
        if score > best_score:
            best_score = score
            best_slug = slug
        # Tie: do nothing (first-seen wins because we only update on strict >).

    if best_score >= 1.0:
        return best_slug, "exact-match"
    if best_score > 0:
        return best_slug, "heuristic"
    return fallback, "fallback"
