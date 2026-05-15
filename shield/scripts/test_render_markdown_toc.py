"""Tests for render-markdown.py TOC + mermaid handling.

Invokes render-markdown.sh end-to-end so uv resolves deps the same way
production does. Runnable: `cd shield/scripts && uv run --with pytest pytest -v`.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
RENDER_SH = SCRIPT_DIR / "render-markdown.sh"

SHELL_WITH_TOC = """<!DOCTYPE html>
<html><body>
{{TOC}}
{{BODY}}
</body></html>
"""

SHELL_NO_TOC = """<!DOCTYPE html>
<html><body>
{{BODY}}
</body></html>
"""


def _run(md_text: str, shell_text: str) -> str:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "input.md").write_text(md_text)
        (d / "shell.html").write_text(shell_text)
        result = subprocess.run(
            [str(RENDER_SH),
             "--md", str(d / "input.md"),
             "--shell", str(d / "shell.html"),
             "--out", str(d / "out.html")],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"render-markdown.sh failed: {result.stderr}")
        return (d / "out.html").read_text()


def test_basic_toc_built_from_h2_and_h3():
    md = "# Title\n\n## 1. Header\n\n## 2. Terminologies\n\n### Glossary\n\n## 3. Problem\n"
    out = _run(md, SHELL_WITH_TOC)
    assert '<nav class="toc">' in out
    assert '<div class="toc-title">Contents</div>' in out
    assert '<a href="#1-header">1. Header</a>' in out
    assert '<a href="#2-terminologies">2. Terminologies</a>' in out
    assert '<a href="#3-problem">3. Problem</a>' in out
    assert '<a href="#glossary">Glossary</a>' in out
    assert '<a href="#title">Title</a>' not in out  # h1 excluded


def test_shell_without_toc_placeholder_renders_body_only():
    md = "# Title\n\n## 1. Section\n\nBody.\n"
    out = _run(md, SHELL_NO_TOC)
    assert "<h2" in out
    assert "<nav" not in out
    assert "{{TOC}}" not in out
    assert "{{BODY}}" not in out


def test_empty_doc_produces_no_toc_block():
    out = _run("# Only Title\n\nNo subsections.\n", SHELL_WITH_TOC)
    assert "<nav" not in out
    assert "{{TOC}}" not in out


def test_orphan_h3_before_h2_emitted_top_level():
    md = "# Title\n\n### Orphan\n\n## 1. First\n\n### Child\n"
    out = _run(md, SHELL_WITH_TOC)
    assert '<a href="#orphan">Orphan</a>' in out
    assert '<a href="#1-first">1. First</a>' in out
    assert '<a href="#child">Child</a>' in out


def test_mermaid_fence_emits_pre_class_mermaid():
    md = "# T\n\n## H\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
    out = _run(md, SHELL_WITH_TOC)
    assert '<pre class="mermaid">' in out
    assert "flowchart LR" in out  # source preserved
    assert '<code class="language-mermaid">' not in out  # NOT the default fence
    assert "</pre>" in out


def test_non_mermaid_fence_unchanged():
    md = "# T\n\n## H\n\n```python\nx = 1\n```\n"
    out = _run(md, SHELL_WITH_TOC)
    # Default markdown-it behavior: <pre><code class="language-python">…
    assert 'class="language-python"' in out
    assert '<pre class="mermaid">' not in out


def test_toc_strips_inline_formatting():
    md = "## **Bold** heading\n\n## The `code` section\n"
    out = _run(md, SHELL_WITH_TOC)
    assert ">Bold heading<" in out   # not >**Bold** heading<
    assert ">The code section<" in out


def test_mermaid_with_html_unsafe_content_is_escaped():
    md = '## H\n\n```mermaid\nA["<script>"] --> B\n```\n'
    out = _run(md, SHELL_WITH_TOC)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


@pytest.mark.parametrize("info", ["mermaid", "MERMAID", "Mermaid", "  mermaid  "])
def test_mermaid_fence_case_and_whitespace(info):
    md = f"## H\n\n```{info}\nflowchart LR\n  A --> B\n```\n"
    out = _run(md, SHELL_WITH_TOC)
    assert '<pre class="mermaid">' in out
