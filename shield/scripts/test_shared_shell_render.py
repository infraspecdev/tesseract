"""End-to-end: a page rendered into the shared shell wires up all assets."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RENDER_SH = SCRIPT_DIR / "render-markdown.sh"
SHELL = SCRIPT_DIR.parent / "templates" / "shell.html"


def test_shared_shell_wires_assets_at_depth():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        feat = root / "feat-a"
        (feat).mkdir()
        (feat / "prd.md").write_text("# PRD\n\n## Section\n\nbody\n")
        out = feat / "outputs" / "prd.html"
        r = subprocess.run(
            [str(RENDER_SH), "--md", str(feat / "prd.md"), "--shell", str(SHELL),
             "--out", str(out), "--assets-root", str(root), "--title", "PRD — feat-a"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, r.stderr
        h = out.read_text()
        # assets wired at correct depth
        assert 'href="../../shield.css"' in h
        assert 'src="../../manifest.js"' in h
        assert 'src="../../shield-nav.js"' in h
        assert 'data-shield-root="../../"' in h
        assert "<title>PRD — feat-a</title>" in h
        # redesigned nav markup
        assert 'id="shield-crumb"' in h          # breadcrumb mount
        assert 'id="docs-toggle"' in h           # Features button
        assert ">Features" in h                  # button label (not "Docs")
        assert 'id="docs-search"' in h           # panel search input
        assert 'id="docs-results"' in h          # results mount
        # old vague nav removed
        assert "Docs ▾" not in h
        assert 'id="docs-dropdown"' not in h
        assert "{{" not in h                     # no unsubstituted placeholders
