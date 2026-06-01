"""Tests for build_manifest schema 2.1 — trd tracking + review entries[]."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

SPEC = Path(__file__).resolve().parent / "migrate_outputs.py"
_spec = importlib.util.spec_from_file_location("migrate_outputs", SPEC)
migrate_outputs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate_outputs)


def _feature(root: Path, name: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    return d


def test_tracks_trd_artifact():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        f = _feature(root, "feat-a")
        (f / "trd.md").write_text("# TRD\n")
        m = migrate_outputs.build_manifest(root)
        assert m["schema_version"] == 2.1 or m["schema_version"] == "2.1"
        assert m["features"][0]["artifacts"]["trd"] is True


def test_review_entries_listed():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        f = _feature(root, "feat-b")
        run = f / "reviews" / "plan" / "2026-05-25"
        run.mkdir(parents=True)
        (run / "summary.md").write_text("# Review\n")
        m = migrate_outputs.build_manifest(root)
        reviews = m["features"][0]["reviews"]["plan"]
        assert reviews["count"] == 1
        assert reviews["latest"] == "2026-05-25"
        assert reviews["entries"] == [
            {"date": "2026-05-25",
             "path": "feat-b/outputs/reviews/plan/2026-05-25/summary.html"}
        ]
