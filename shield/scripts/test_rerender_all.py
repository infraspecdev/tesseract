"""Eval for rerender_all.py — renders the COMPLETE committed HTML set,
including enhanced-* and detailed/* review docs (regression: those were skipped)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

SPEC = Path(__file__).resolve().parent / "rerender_all.py"
_spec = importlib.util.spec_from_file_location("rerender_all", SPEC)
ra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ra)


def _fixture(root: Path) -> None:
    """A feature with a main doc + a plan review that has summary, enhanced, detailed."""
    feat = root / "feat-x"
    (feat).mkdir(parents=True)
    (root / "manifest.json").write_text(json.dumps({"schema_version": "2.1", "features": []}))
    (feat / "prd.md").write_text("# PRD\n\nbody\n")
    rev = feat / "reviews" / "plan" / "2026-06-08"
    (rev / "detailed").mkdir(parents=True)
    (rev / "summary.md").write_text("# Summary\n\nbody\n")
    (rev / "enhanced-plan.md").write_text("# Enhanced\n\nbody\n")
    (rev / "detailed" / "agile-coach.md").write_text("# Agile\n\nbody\n")


def test_renders_enhanced_and_detailed(tmp_path):
    _fixture(tmp_path)
    rc = ra.rerender_all(tmp_path)
    assert rc == 0
    out = tmp_path / "feat-x" / "outputs"
    expected = [
        out / "prd.html",
        out / "reviews" / "plan" / "2026-06-08" / "summary.html",
        out / "reviews" / "plan" / "2026-06-08" / "enhanced-plan.html",
        out / "reviews" / "plan" / "2026-06-08" / "detailed" / "agile-coach.html",
    ]
    for p in expected:
        assert p.is_file(), f"missing rendered page: {p}"
