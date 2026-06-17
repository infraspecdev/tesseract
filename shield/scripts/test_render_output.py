"""Eval for render-output.sh — the full build: pages + dashboard assets."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "render-output.sh"


def test_build_produces_pages_and_assets(tmp_path):
    feat = tmp_path / "feat-x"
    feat.mkdir(parents=True)
    (tmp_path / "manifest.json").write_text(
        json.dumps({"schema_version": "2.1", "features": [{"name": "feat-x"}]})
    )
    (feat / "prd.md").write_text("# PRD\n\nbody\n")

    res = subprocess.run([str(SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    # pages
    assert (feat / "outputs" / "prd.html").is_file()
    # dashboard + shared assets
    for asset in ["manifest.js", "index.html", "shield.css",
                  "shield-nav.js", "shield-dashboard.js"]:
        assert (tmp_path / asset).is_file(), f"missing asset {asset}"


def test_missing_dir_errors(tmp_path):
    res = subprocess.run([str(SCRIPT), str(tmp_path / "nope")],
                         capture_output=True, text=True)
    assert res.returncode == 2
    assert "not a dir" in res.stderr
