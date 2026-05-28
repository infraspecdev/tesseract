"""Tests for shield/scripts/render_trd_section.py — TRD section renderer.

This file codifies the §10 milestone-renderer contract before any
implementation exists (RED step). The renderer is the single-source-of-truth
seam: `plan.json` `milestones[]` is upstream, `trd.md` §10 is rendered.

Run via uv from the repo root:

    uv run shield/scripts/test_render_trd_section.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from render_trd_section import (  # noqa: E402  (path-injected import)
    BEGIN_MARKER,
    END_MARKER,
    render_milestones,
    render_section_with_markers,
)


# ───────────────────────────── format ─────────────────────────────

def test_renders_single_milestone_no_deps() -> None:
    out = render_milestones([
        {
            "id": "M1",
            "name": "Capture + store + view",
            "outcome": "A global backlog exists",
            "exit_criteria": ["validator behaves"],
            "depends_on": [],
        },
    ])
    assert "### M1 — Capture + store + view  *(no deps)*" in out
    assert "**Outcome:** A global backlog exists" in out
    assert "**Exit criteria:**\n- validator behaves" in out


def test_renders_dep_string_for_single_dep() -> None:
    out = render_milestones([
        {
            "id": "M2", "name": "Association", "outcome": "x",
            "exit_criteria": ["y"], "depends_on": ["M1"],
        },
    ])
    assert "*(deps M1)*" in out


def test_renders_dep_string_for_multiple_deps() -> None:
    out = render_milestones([
        {
            "id": "M3", "name": "Final", "outcome": "ship",
            "exit_criteria": ["a"], "depends_on": ["M1", "M2"],
        },
    ])
    assert "*(deps M1, M2)*" in out


def test_renders_multiple_exit_criteria_as_bullets() -> None:
    out = render_milestones([
        {
            "id": "M1", "name": "X", "outcome": "y",
            "exit_criteria": ["ec one.", "ec two.", "ec three."],
            "depends_on": [],
        },
    ])
    assert "**Exit criteria:**\n- ec one.\n- ec two.\n- ec three." in out


# ───────────────────────────── determinism ─────────────────────────────

def test_id_sort_is_deterministic() -> None:
    """Input order M3, M1, M2 → output order M1, M2, M3."""
    ms = [
        {"id": "M3", "name": "Three", "outcome": "c",
         "exit_criteria": ["x"], "depends_on": ["M2"]},
        {"id": "M1", "name": "One", "outcome": "a",
         "exit_criteria": ["x"], "depends_on": []},
        {"id": "M2", "name": "Two", "outcome": "b",
         "exit_criteria": ["x"], "depends_on": ["M1"]},
    ]
    out = render_milestones(ms)
    pos1 = out.index("M1 — One")
    pos2 = out.index("M2 — Two")
    pos3 = out.index("M3 — Three")
    assert pos1 < pos2 < pos3, "milestones must render in ascending id order"


def test_render_is_idempotent() -> None:
    """Same input → byte-identical output (no nondeterministic ordering)."""
    ms = [
        {"id": "M2", "name": "B", "outcome": "b",
         "exit_criteria": ["1", "2"], "depends_on": ["M1"]},
        {"id": "M1", "name": "A", "outcome": "a",
         "exit_criteria": ["x"], "depends_on": []},
    ]
    assert render_milestones(ms) == render_milestones(ms)


# ───────────────────────────── edge cases ─────────────────────────────

def test_empty_milestones_returns_opt_out_marker() -> None:
    """When sidecar opts out of milestone tracking the rendered region
    is a single italic line so the validator still has bytes to compare."""
    out = render_milestones([])
    assert "No milestones" in out
    assert "opts out" in out


def test_strips_surrounding_whitespace_in_outcome_and_exit_criteria() -> None:
    out = render_milestones([
        {
            "id": "M1", "name": "X",
            "outcome": "  padded outcome  \n",
            "exit_criteria": ["  ec one  ", "ec two\t"],
            "depends_on": [],
        },
    ])
    assert "**Outcome:** padded outcome" in out
    assert "- ec one" in out
    assert "- ec two" in out
    # no leading/trailing whitespace artifacts
    assert "  padded outcome" not in out
    assert "- " + "  ec" not in out


# ───────────────────────────── marker wrapping ─────────────────────────────

def test_section_wraps_body_with_begin_and_end_markers() -> None:
    out = render_section_with_markers([
        {"id": "M1", "name": "A", "outcome": "a",
         "exit_criteria": ["x"], "depends_on": []},
    ])
    assert out.startswith(BEGIN_MARKER)
    assert out.endswith(END_MARKER)
    # body lives strictly between the markers
    body = out[len(BEGIN_MARKER):-len(END_MARKER)].strip()
    assert body.startswith("### M1 — A")


def test_begin_marker_explains_do_not_edit() -> None:
    """Future maintainers reading the raw TRD must see the directive."""
    assert "do not edit" in BEGIN_MARKER.lower()
    assert "plan.json" in BEGIN_MARKER


# ───────────────────────────── runner ─────────────────────────────

def _run() -> int:
    failures: list[str] = []
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as e:
            failures.append(f"  FAIL {name}: {e}")
            print(failures[-1])
        except Exception as e:  # noqa: BLE001
            failures.append(f"  ERR  {name}: {type(e).__name__}: {e}")
            print(failures[-1])
    print(f"\n{len(failures)} failure(s)" if failures else "\nall green")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
