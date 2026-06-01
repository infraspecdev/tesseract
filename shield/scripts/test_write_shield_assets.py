"""Tests for write_shield_assets.py — manifest.js + asset copy."""
from __future__ import annotations

import importlib.util
import json
import re
import tempfile
from pathlib import Path

SPEC = Path(__file__).resolve().parent / "write_shield_assets.py"
_spec = importlib.util.spec_from_file_location("write_shield_assets", SPEC)
wsa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wsa)

ASSETS = ["shield.css", "shield-nav.js", "shield-dashboard.js", "index.html"]


def test_emits_manifest_js_and_copies_assets():
    with tempfile.TemporaryDirectory() as t:
        out = Path(t)
        manifest = {"schema_version": "2.1", "features": [{"name": "feat-a"}]}
        (out / "manifest.json").write_text(json.dumps(manifest))
        wsa.write_assets(out)
        mjs = (out / "manifest.js").read_text()
        assert mjs.startswith("window.SHIELD_MANIFEST = ")
        payload = re.sub(r"^window\.SHIELD_MANIFEST = ", "", mjs).rstrip().rstrip(";")
        assert json.loads(payload) == manifest
        for a in ASSETS:
            assert (out / a).is_file(), f"missing copied asset {a}"
