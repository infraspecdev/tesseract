"""Tests for render-markdown.py relative-link rewriting.

When markdown at {feature}/trd.md renders to {feature}/outputs/trd.html, all
relative body links must be prefixed by the md→out directory delta so they
keep resolving. Invokes render-markdown.sh end-to-end.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RENDER_SH = SCRIPT_DIR / "render-markdown.sh"
SHELL = "<!DOCTYPE html>\n<html><body>\n{{BODY}}\n</body></html>\n"


def _run(md_text: str, *, out_subdir: str) -> str:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        outdir = d / out_subdir if out_subdir else d
        outdir.mkdir(parents=True, exist_ok=True)
        (d / "input.md").write_text(md_text)
        (d / "shell.html").write_text(SHELL)
        result = subprocess.run(
            [str(RENDER_SH), "--md", str(d / "input.md"),
             "--shell", str(d / "shell.html"), "--out", str(outdir / "out.html")],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"render-markdown.sh failed: {result.stderr}")
        return (outdir / "out.html").read_text()


def test_dot_relative_link_prefixed_when_out_is_subdir():
    out = _run("[plan](./plan.json)\n", out_subdir="outputs")
    assert 'href="../plan.json"' in out


def test_bare_relative_link_prefixed():
    out = _run("[prd](prd/1/prd.md)\n", out_subdir="outputs")
    assert 'href="../prd/1/prd.md"' in out


def test_relative_image_src_prefixed():
    out = _run("![d](diagrams/a.png)\n", out_subdir="outputs")
    assert 'src="../diagrams/a.png"' in out


def test_absolute_url_untouched():
    out = _run("[x](https://example.com/a)\n", out_subdir="outputs")
    assert 'href="https://example.com/a"' in out


def test_anchor_link_untouched():
    out = _run("[x](#section)\n", out_subdir="outputs")
    assert 'href="#section"' in out


def test_root_relative_untouched():
    out = _run("[x](/abs/path)\n", out_subdir="outputs")
    assert 'href="/abs/path"' in out


def test_no_prefix_when_md_and_out_share_dir():
    out = _run("[plan](./plan.json)\n", out_subdir="")
    assert 'href="./plan.json"' in out


def test_relative_link_with_fragment_prefixed_and_fragment_kept():
    out = _run("[x](./prd.md#sec)\n", out_subdir="outputs")
    assert 'href="../prd.md#sec"' in out


def test_data_uri_untouched():
    # data: URIs have no :// and no leading / # mailto, so without an explicit
    # guard they would be mangled into ../data:image/... by the prefixer.
    md = "![img](data:image/png;base64,iVBOR)\n"
    out = _run(md, out_subdir="outputs")
    assert 'src="data:image/png;base64,iVBOR"' in out


def test_query_only_url_untouched():
    # ?query-only hrefs should pass through unchanged.
    out = _run("[x](?q=1)\n", out_subdir="outputs")
    assert 'href="?q=1"' in out


TRD_FIXTURE = """# T

## §7 High-Level Design {#high-level-design}

```mermaid
flowchart LR
  A --> B
```

```mermaid
sequenceDiagram
  A->>B: quote
```

```mermaid
flowchart TB
  subgraph ap-south-1
    L[ledger]
  end
```

## §10 Milestones {#milestones}

### M1 — Foundation  *(no deps)*

**Detailed design:** [`core-svc`](lld-core-svc.md)

## §13 References {#references}

- LLD: [`core-svc`](./lld-core-svc.md) — drafted by /plan.
"""


def test_section7_emits_three_mermaid_diagrams():
    out = _run(TRD_FIXTURE, out_subdir="outputs")
    assert out.count('<pre class="mermaid">') == 3


def test_milestone_and_reference_lld_links_rewritten_into_outputs():
    out = _run(TRD_FIXTURE, out_subdir="outputs")
    # §10 link 'lld-core-svc.md' and §13 './lld-core-svc.md' both land one dir up
    assert 'href="../lld-core-svc.md"' in out
    assert 'href="lld-core-svc.md"' not in out
    assert 'href="./lld-core-svc.md"' not in out
