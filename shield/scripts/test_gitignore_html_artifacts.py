"""Eval: .gitignore demotes Shield HTML to a build artifact."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
GITIGNORE = ROOT / ".gitignore"

REQUIRED_PATTERNS = [
    "**/docs/shield/*/outputs/",
    "**/docs/shield/index.html",
    "**/docs/shield/manifest.js",
]


def test_gitignore_has_html_artifact_rules():
    text = GITIGNORE.read_text()
    for pat in REQUIRED_PATTERNS:
        assert pat in text, f".gitignore missing rule: {pat}"


def test_no_shield_html_tracked():
    out = subprocess.run(
        ["git", "ls-files", "docs/shield/**/*.html", "docs/shield/manifest.js"],
        cwd=ROOT, capture_output=True, text=True,
    )
    tracked = [l for l in out.stdout.splitlines() if l.strip()]
    assert tracked == [], f"HTML/assets still tracked: {tracked}"
