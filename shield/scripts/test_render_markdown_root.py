"""Tests for render-markdown.py {{ROOT}} / {{TITLE}} substitution."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RENDER_SH = SCRIPT_DIR / "render-markdown.sh"
SHELL = (
    '<!DOCTYPE html><html><head><title>{{TITLE}}</title>'
    '<link rel="stylesheet" href="{{ROOT}}shield.css"></head>'
    '<body data-shield-root="{{ROOT}}">{{META}}{{TOC}}{{BODY}}</body></html>\n'
)


def _run(out_subdir: str, *, title: str) -> str:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        outdir = d / out_subdir if out_subdir else d
        outdir.mkdir(parents=True, exist_ok=True)
        (d / "input.md").write_text("# Hello\n\nbody\n")
        (d / "shell.html").write_text(SHELL)
        r = subprocess.run(
            [str(RENDER_SH), "--md", str(d / "input.md"),
             "--shell", str(d / "shell.html"), "--out", str(outdir / "out.html"),
             "--assets-root", str(d), "--title", title],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise AssertionError(f"render failed: {r.stderr}")
        return (outdir / "out.html").read_text()


def test_root_empty_at_root():
    out = _run("", title="X")
    assert 'href="shield.css"' in out
    assert 'data-shield-root=""' in out


def test_root_prefix_in_subdir():
    out = _run("feat/outputs", title="X")
    assert 'href="../../shield.css"' in out
    assert 'data-shield-root="../../"' in out


def test_title_substituted():
    out = _run("", title="PRD — Backlog")
    assert "<title>PRD — Backlog</title>" in out


def test_meta_blank_when_absent():
    out = _run("", title="X")
    assert "{{META}}" not in out
