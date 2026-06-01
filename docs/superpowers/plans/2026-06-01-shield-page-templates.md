# Shield Page Templating Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> REQUIRED SUB-SKILL when editing any `SKILL.md` / script / eval: also load `updating-plugin-assets` (this repo's eval-coverage procedure).

**Goal:** Give every Shield HTML page one shared shell, one stylesheet, a global header with a nested **Docs ▾** menu reaching all docs, and a real `index.html` dashboard — all driven by `manifest.json` via a generated `manifest.js`.

**Architecture:** Static template assets live in `shield/templates/`. `render-markdown.py` renders doc pages into the shared `shell.html`, substituting `{{ROOT}}` (relative path to the `docs/shield/` root) so each page links the shared CSS/JS. A generated `manifest.js` (`window.SHIELD_MANIFEST = {…}`) feeds two small client scripts that build the nested nav (every page) and the dashboard cards (`index.html`). Because every page loads the same `manifest.js`, adding a feature refreshes all menus with no page re-render. Works over `file://` (no `fetch`).

**Tech Stack:** Python (`uv run`), markdown-it-py, vanilla JS, CSS. No new runtime deps.

**Spec:** `docs/superpowers/specs/2026-06-01-shield-page-templates-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `shield/templates/shell.html` | NEW — shared HTML shell; placeholders `{{TITLE}}`,`{{ROOT}}`,`{{META}}`,`{{TOC}}`,`{{BODY}}`; header + Docs menu mount; mermaid CDN |
| `shield/templates/shield.css` | NEW — single light theme: typography, tables, code, nav/dropdown, dashboard cards, pipeline strip, badges, milestones, story cards |
| `shield/templates/shield-nav.js` | NEW — builds nested Docs dropdown from `window.SHIELD_MANIFEST` |
| `shield/templates/shield-dashboard.js` | NEW — builds dashboard card grid + pipeline strip from `window.SHIELD_MANIFEST` |
| `shield/templates/index.html` | NEW — dashboard page (shell + dashboard mount + scripts) |
| `shield/scripts/render-markdown.py` | MODIFY — add `--assets-root` + `--title`; substitute `{{ROOT}}`,`{{TITLE}}`,`{{META}}` |
| `shield/scripts/migrate_outputs.py` | MODIFY — track `trd`; add `reviews[].entries[]`; bump schema to 2.1 |
| `shield/scripts/write_shield_assets.py` | NEW — emit `manifest.js`, copy static assets into `docs/shield/` |
| `shield/scripts/rerender_all.py` | NEW — one-time pass: re-render every source md to the shared shell |
| `shield/scripts/test_render_markdown_root.py` | NEW — tests for `{{ROOT}}`/`{{TITLE}}` |
| `shield/scripts/test_write_shield_assets.py` | NEW — tests for manifest.js + asset copy |
| `shield/scripts/test_migrate_outputs_manifest.py` | NEW — tests for schema 2.1 |
| `shield/skills/general/prd-docs/*`, `plan-docs/*`, `prd-review/*`, `plan-review/*`, `review/*` | MODIFY — render via shared shell; call `write_shield_assets.py` |
| `shield/skills/general/manifest-schema.md` | MODIFY — document schema 2.1 + templating model |
| `shield/examples/python-api/docs/shield/index.html` | MODIFY — regenerate to new template |
| `.pre-commit-config.yaml` | MODIFY — add new pytests to the render hook |
| `.claude-plugin/marketplace.json` | MODIFY — bump Shield version |

**Version note:** Shield is `2.24.1` on `main` (writing-style PR #59 → 2.24.0, CI-hygiene PR #60 → 2.24.1, both merged 2026-06-01). This branch bumps to **`2.25.0`**.

**Convention note:** Per CLAUDE.md, JS/CSS static assets have no Python unit surface; their GREEN is (a) the render pytest asserting the page wires them in, and (b) structural assertions that the asset files contain the expected entry points. State this in the PR body.

---

### Task 1: Manifest schema 2.1 — track `trd`, add review `entries[]`

**Files:**
- Modify: `shield/scripts/migrate_outputs.py:163-209`
- Test: `shield/scripts/test_migrate_outputs_manifest.py`

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_migrate_outputs_manifest.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pytest pytest test_migrate_outputs_manifest.py -v`
Expected: FAIL — `trd` KeyError and `entries` KeyError.

- [ ] **Step 3: Implement schema 2.1**

In `shield/scripts/migrate_outputs.py`, add to `TRACKED_ARTIFACTS` (after `"plan_arch_md"`):

```python
    "trd":          "trd.md",
```

Replace `_summarize_reviews` with:

```python
def _summarize_reviews(feature_dir: Path, review_type: str) -> dict[str, object]:
    review_root = feature_dir / "reviews" / review_type
    if not review_root.exists():
        return {"count": 0, "entries": []}
    runs = sorted(d.name for d in review_root.iterdir() if d.is_dir())
    if not runs:
        return {"count": 0, "entries": []}
    entries = [
        {
            "date": run,
            "path": f"{feature_dir.name}/outputs/reviews/{review_type}/{run}/summary.html",
        }
        for run in runs
    ]
    return {"latest": runs[-1], "count": len(runs), "entries": entries}
```

In `build_manifest`, change the return line:

```python
    return {"schema_version": "2.1", "features": features}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pytest pytest test_migrate_outputs_manifest.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs_manifest.py
git commit -m "feat(shield): manifest schema 2.1 — track trd + review entries[]"
```

---

### Task 2: `render-markdown.py` — `{{ROOT}}`, `{{TITLE}}`, `{{META}}`

**Files:**
- Modify: `shield/scripts/render-markdown.py:30-31,172-206`
- Test: `shield/scripts/test_render_markdown_root.py`

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_render_markdown_root.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_render_markdown_root.py -v`
Expected: FAIL — `--assets-root` is an unrecognized argument.

- [ ] **Step 3: Implement the substitutions**

In `shield/scripts/render-markdown.py`, after line 31 add:

```python
ROOT_PLACEHOLDER = "{{ROOT}}"
TITLE_PLACEHOLDER = "{{TITLE}}"
META_PLACEHOLDER = "{{META}}"
```

In `main()`, add args after the `--out` arg (around line 177):

```python
    parser.add_argument("--assets-root", type=Path, default=None,
        help="docs/shield root; used to compute {{ROOT}} relative prefix")
    parser.add_argument("--title", default="", help="page <title> text")
    parser.add_argument("--meta", default="", help="optional meta-banner HTML")
```

After the `out = shell` line (currently line 199), before the `{{TOC}}` block, insert:

```python
    root_prefix = ""
    if args.assets_root is not None:
        rel = os.path.relpath(
            args.assets_root.resolve(), args.out.resolve().parent
        ).replace(os.sep, "/")
        root_prefix = "" if rel == "." else rel + "/"
    out = out.replace(ROOT_PLACEHOLDER, root_prefix)
    out = out.replace(TITLE_PLACEHOLDER, html.escape(args.title))
    out = out.replace(META_PLACEHOLDER, args.meta)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_render_markdown_root.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Confirm existing render tests still pass**

Run: `cd shield/scripts && uv run --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_render_markdown_toc.py test_render_markdown_links.py -v`
Expected: PASS (no regressions — new args are optional).

- [ ] **Step 6: Commit**

```bash
git add shield/scripts/render-markdown.py shield/scripts/test_render_markdown_root.py
git commit -m "feat(shield): render-markdown {{ROOT}}/{{TITLE}}/{{META}} substitution"
```

---

### Task 3: The single stylesheet — `shield.css`

**Files:**
- Create: `shield/templates/shield.css`

- [ ] **Step 1: Create the stylesheet**

Create `shield/templates/shield.css` (light theme; consolidates PRD + plan + index styles):

```css
:root {
  --accent:#1a73e8; --bg:#ffffff; --panel:#f7f9fc; --text:#1f1f1f;
  --muted:#5a6370; --border:#e4e8ee; --green:#3fb950; --green-bg:#e9f7ee;
}
* { box-sizing:border-box; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  line-height:1.6; color:var(--text); background:var(--bg); }
/* Header + nested Docs menu */
.shield-header { display:flex; align-items:center; gap:18px; padding:10px 20px;
  border-bottom:1px solid var(--border); background:#fff; position:sticky; top:0; z-index:50; }
.shield-header .brand { font-weight:700; color:var(--text); text-decoration:none; }
.shield-header .nav-link { color:var(--accent); text-decoration:none; font-size:.92rem; }
.docs-menu { position:relative; }
.docs-toggle { cursor:pointer; border:1px solid var(--border); background:var(--panel);
  color:var(--accent); border-radius:6px; padding:4px 10px; font-size:.92rem; }
.docs-dropdown { display:none; position:absolute; top:110%; left:0; min-width:240px;
  background:#fff; border:1px solid var(--border); border-radius:8px; padding:6px;
  box-shadow:0 6px 20px rgba(0,0,0,.08); max-height:70vh; overflow:auto; }
.docs-dropdown.open { display:block; }
.docs-feature > summary { cursor:pointer; font-weight:600; padding:5px 8px; list-style:none; }
.docs-feature[open] > summary { color:var(--accent); }
.docs-link { display:block; padding:4px 8px 4px 22px; color:var(--accent);
  text-decoration:none; font-size:.9rem; border-radius:4px; }
.docs-link:hover { background:var(--panel); }
.docs-group { padding:4px 8px 0 16px; font-size:.78rem; text-transform:uppercase; color:var(--muted); }
/* Main content */
.shield-main { max-width:960px; margin:0 auto; padding:36px 28px 96px; }
h1,h2,h3,h4 { color:var(--accent); line-height:1.25; }
h1 { font-size:2rem; border-bottom:2px solid var(--accent); padding-bottom:8px; margin-bottom:24px; }
h2 { font-size:1.45rem; margin-top:40px; padding-top:12px; border-top:1px solid var(--border); }
h3 { font-size:1.15rem; margin-top:28px; }
h4 { font-size:1rem; color:var(--text); margin-top:20px; }
p,ul,ol { margin:12px 0; } li { margin:4px 0; }
table { border-collapse:collapse; width:100%; margin:16px 0; font-size:.94rem; }
th,td { padding:8px 12px; border:1px solid var(--border); text-align:left; vertical-align:top; }
th { background:var(--panel); font-weight:600; }
tr:nth-child(even) td { background:#fbfcfd; }
blockquote { border-left:3px solid var(--accent); margin:16px 0; padding:4px 16px;
  color:var(--muted); background:var(--panel); }
code { background:#f1f3f6; padding:2px 6px; border-radius:3px;
  font-family:"JetBrains Mono","SF Mono",Consolas,monospace; font-size:.9em; }
pre { background:var(--panel); padding:12px 16px; border-radius:6px; overflow-x:auto;
  border:1px solid var(--border); }
pre.mermaid { background:transparent; border:none; padding:0; text-align:center; }
a { color:var(--accent); }
hr { border:none; border-top:1px solid var(--border); margin:32px 0; }
.toc,.meta-banner { background:var(--panel); border:1px solid var(--border);
  border-left:3px solid var(--accent); border-radius:6px; padding:16px 20px; margin-bottom:28px; font-size:.94rem; }
.toc-title { font-weight:600; margin-bottom:6px; }
.shield-footer { max-width:960px; margin:0 auto; padding:24px 28px; color:var(--muted);
  font-size:.85rem; border-top:1px solid var(--border); }
/* Dashboard */
.dash-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }
.dash-card { border:1px solid var(--border); border-radius:8px; padding:16px; background:#fff; }
.dash-card h3 { margin:0 0 4px; color:var(--text); font-size:1.05rem; }
.dash-card .date { color:var(--muted); font-size:.8rem; }
.dash-links { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
.dash-links a { font-size:.85rem; border:1px solid var(--border); border-radius:6px;
  padding:3px 9px; text-decoration:none; }
.pipeline { display:flex; gap:4px; margin-top:10px; font-size:.72rem; }
.pipe-step { border-radius:8px; padding:1px 7px; background:#f1f3f6; color:var(--muted); }
.pipe-step.done { background:var(--green-bg); color:var(--green); }
.badge { display:inline-block; background:var(--green-bg); color:var(--green);
  border-radius:12px; padding:.1em .6em; font-size:.75rem; font-weight:600; }
.dash-empty { color:var(--muted); padding:40px; text-align:center; }
/* Plan story components */
.story { border:1px solid var(--border); border-radius:8px; padding:20px; margin:25px 0; }
.epic-meta { background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:15px 20px; margin:20px 0; }
.milestone { margin:16px 0; padding:12px 16px; border-left:3px solid var(--accent); background:var(--panel); }
```

- [ ] **Step 2: Verify it is valid CSS (no syntax errors via a quick brace check)**

Run: `python3 -c "s=open('shield/templates/shield.css').read(); assert s.count('{')==s.count('}'), 'unbalanced braces'; print('braces ok', s.count('{'))"`
Expected: `braces ok <N>`

- [ ] **Step 3: Commit**

```bash
git add shield/templates/shield.css
git commit -m "feat(shield): single shared stylesheet (light theme)"
```

---

### Task 4: The shared shell — `shell.html`

**Files:**
- Create: `shield/templates/shell.html`

- [ ] **Step 1: Create the shell**

Create `shield/templates/shell.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{{TITLE}}</title>
<link rel="stylesheet" href="{{ROOT}}shield.css" />
<script defer src="{{ROOT}}manifest.js"></script>
<script defer src="{{ROOT}}shield-nav.js"></script>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
  mermaid.initialize({ startOnLoad: false, theme: "default" });
  document.addEventListener("DOMContentLoaded", () => mermaid.run({ querySelector: "pre.mermaid" }));
</script>
</head>
<body data-shield-root="{{ROOT}}">
<header class="shield-header">
  <a class="brand" href="{{ROOT}}index.html">🛡 Shield</a>
  <a class="nav-link" href="{{ROOT}}index.html">Dashboard</a>
  <div class="docs-menu">
    <button class="docs-toggle" id="docs-toggle" aria-expanded="false">Docs ▾</button>
    <div class="docs-dropdown" id="docs-dropdown"></div>
  </div>
</header>
<main class="shield-main">
{{META}}
{{TOC}}
{{BODY}}
</main>
<footer class="shield-footer">Generated by Shield</footer>
</body>
</html>
```

- [ ] **Step 2: Verify all placeholders present**

Run: `python3 -c "s=open('shield/templates/shell.html').read(); [print(p, p in s) for p in ('{{TITLE}}','{{ROOT}}','{{META}}','{{TOC}}','{{BODY}}')]"`
Expected: all five print `True`.

- [ ] **Step 3: Commit**

```bash
git add shield/templates/shell.html
git commit -m "feat(shield): shared HTML shell with header + Docs menu mount"
```

---

### Task 5: Nav builder — `shield-nav.js`

**Files:**
- Create: `shield/templates/shield-nav.js`
- Test: extend `shield/scripts/test_write_shield_assets.py` (created in Task 7) — structural check that the file defines `buildDocsMenu`. For now, a standalone structural assertion in Step 2.

- [ ] **Step 1: Create the nav builder**

Create `shield/templates/shield-nav.js`:

```javascript
// Builds the nested Docs ▾ dropdown from window.SHIELD_MANIFEST.
// Link paths are prefixed with document.body.dataset.shieldRoot so they
// resolve from any page depth. No fetch — data comes from manifest.js.
(function () {
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  var ARTIFACTS = [
    ["research", "Research", "research.html"],
    ["prd", "PRD", "prd.html"],
    ["trd", "TRD", "trd.html"],
    ["plan_md", "Plan", "plan.html"],
    ["plan_arch_md", "Architecture", "plan-architecture.html"],
  ];
  function buildDocsMenu(manifest, root) {
    var frag = document.createDocumentFragment();
    var features = (manifest && manifest.features) || [];
    if (!features.length) {
      frag.appendChild(el("div", "docs-group", "No docs yet"));
      return frag;
    }
    features.forEach(function (f) {
      var det = el("details", "docs-feature");
      det.appendChild(el("summary", null, f.name));
      ARTIFACTS.forEach(function (a) {
        if (f.artifacts && f.artifacts[a[0]]) {
          var href = root + f.name + "/outputs/" + a[2];
          var link = el("a", "docs-link", a[1]);
          link.setAttribute("href", href);
          det.appendChild(link);
        }
      });
      ["prd", "plan", "code"].forEach(function (rt) {
        var rv = f.reviews && f.reviews[rt];
        if (rv && rv.entries && rv.entries.length) {
          det.appendChild(el("div", "docs-group", rt + " reviews"));
          rv.entries.forEach(function (en) {
            var link = el("a", "docs-link", en.date);
            link.setAttribute("href", root + en.path);
            det.appendChild(link);
          });
        }
      });
      frag.appendChild(det);
    });
    return frag;
  }
  document.addEventListener("DOMContentLoaded", function () {
    var root = document.body.dataset.shieldRoot || "";
    var dropdown = document.getElementById("docs-dropdown");
    var toggle = document.getElementById("docs-toggle");
    if (dropdown) dropdown.appendChild(buildDocsMenu(window.SHIELD_MANIFEST, root));
    if (toggle && dropdown) {
      toggle.addEventListener("click", function () {
        var open = dropdown.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(open));
      });
      document.addEventListener("click", function (e) {
        if (!e.target.closest(".docs-menu")) dropdown.classList.remove("open");
      });
    }
  });
})();
```

- [ ] **Step 2: Verify structural shape**

Run: `python3 -c "s=open('shield/templates/shield-nav.js').read(); assert 'SHIELD_MANIFEST' in s and 'docs-dropdown' in s and 'shieldRoot' in s; print('nav ok')"`
Expected: `nav ok`

- [ ] **Step 3: Commit**

```bash
git add shield/templates/shield-nav.js
git commit -m "feat(shield): nested Docs menu builder (shield-nav.js)"
```

---

### Task 6: Dashboard builder + `index.html`

**Files:**
- Create: `shield/templates/shield-dashboard.js`
- Create: `shield/templates/index.html`

- [ ] **Step 1: Create the dashboard builder**

Create `shield/templates/shield-dashboard.js`:

```javascript
// Builds the dashboard card grid + pipeline strip from window.SHIELD_MANIFEST.
// index.html sits at docs/shield root, so root prefix is "".
(function () {
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  var LINKS = [
    ["research", "Research", "research.html"],
    ["prd", "PRD", "prd.html"],
    ["trd", "TRD", "trd.html"],
    ["plan_md", "Plan", "plan.html"],
  ];
  var PIPELINE = [
    ["Research", function (a) { return a.research; }],
    ["PRD", function (a) { return a.prd; }],
    ["Plan", function (a) { return a.plan_md || a.plan_json; }],
    ["Implement", function (a, f) { return (f.reviews && f.reviews.code && f.reviews.code.count) > 0; }],
  ];
  function card(f) {
    var c = el("div", "dash-card");
    var head = el("div");
    head.appendChild(el("h3", null, f.name));
    head.appendChild(el("span", "date", f.updated ? f.updated.slice(0, 10) : ""));
    c.appendChild(head);
    var pipe = el("div", "pipeline");
    PIPELINE.forEach(function (p) {
      var done = !!p[1](f.artifacts || {}, f);
      pipe.appendChild(el("span", "pipe-step" + (done ? " done" : ""), p[0]));
    });
    c.appendChild(pipe);
    var links = el("div", "dash-links");
    LINKS.forEach(function (l) {
      if (f.artifacts && f.artifacts[l[0]]) {
        var a = el("a", null, l[1]);
        a.setAttribute("href", f.name + "/outputs/" + l[2]);
        links.appendChild(a);
      }
    });
    if (f.artifacts && f.artifacts.plan_json) {
      var aj = el("a", null, "Sidecar JSON");
      aj.setAttribute("href", f.name + "/plan.json");
      links.appendChild(aj);
    }
    c.appendChild(links);
    return c;
  }
  document.addEventListener("DOMContentLoaded", function () {
    var mount = document.getElementById("shield-dashboard");
    if (!mount) return;
    var features = (window.SHIELD_MANIFEST && window.SHIELD_MANIFEST.features) || [];
    if (!features.length) {
      mount.appendChild(el("div", "dash-empty", "No features yet — run /research or /plan to get started."));
      return;
    }
    var grid = el("div", "dash-grid");
    features.forEach(function (f) { grid.appendChild(card(f)); });
    mount.appendChild(grid);
  });
})();
```

- [ ] **Step 2: Create the dashboard page**

Create `shield/templates/index.html` (root page — `{{ROOT}}` is empty so links are bare):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Shield Dashboard</title>
<link rel="stylesheet" href="shield.css" />
<script defer src="manifest.js"></script>
<script defer src="shield-nav.js"></script>
<script defer src="shield-dashboard.js"></script>
</head>
<body data-shield-root="">
<header class="shield-header">
  <a class="brand" href="index.html">🛡 Shield</a>
  <a class="nav-link" href="index.html">Dashboard</a>
  <div class="docs-menu">
    <button class="docs-toggle" id="docs-toggle" aria-expanded="false">Docs ▾</button>
    <div class="docs-dropdown" id="docs-dropdown"></div>
  </div>
</header>
<main class="shield-main">
  <h1>Shield Dashboard</h1>
  <p class="subtitle">Plan &amp; review artifacts across the project.</p>
  <div id="shield-dashboard"></div>
</main>
<footer class="shield-footer">Generated by Shield</footer>
</body>
</html>
```

- [ ] **Step 3: Verify structural shape**

Run: `python3 -c "d=open('shield/templates/shield-dashboard.js').read(); h=open('shield/templates/index.html').read(); assert 'shield-dashboard' in d and 'dash-grid' in d; assert 'shield-dashboard' in h and 'shield-dashboard.js' in h; print('dashboard ok')"`
Expected: `dashboard ok`

- [ ] **Step 4: Commit**

```bash
git add shield/templates/shield-dashboard.js shield/templates/index.html
git commit -m "feat(shield): dashboard builder + index.html template"
```

---

### Task 7: Asset generator — `write_shield_assets.py`

**Files:**
- Create: `shield/scripts/write_shield_assets.py`
- Test: `shield/scripts/test_write_shield_assets.py`

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_write_shield_assets.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pytest pytest test_write_shield_assets.py -v`
Expected: FAIL — `write_shield_assets.py` does not exist.

- [ ] **Step 3: Implement the generator**

Create `shield/scripts/write_shield_assets.py`:

```python
#!/usr/bin/env python3
"""Emit manifest.js and copy static page assets into the Shield output dir.

manifest.js is a JS-loadable mirror of manifest.json (assigned to
window.SHIELD_MANIFEST) so pages can build nav/dashboard without a fetch()
(which browsers block over file://). The four static assets are copied from
shield/templates/ so the output dir is self-contained.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_ASSETS = ["shield.css", "shield-nav.js", "shield-dashboard.js", "index.html"]


def write_assets(output_dir: Path) -> None:
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json not found in {output_dir}")
    manifest = json.loads(manifest_path.read_text())
    (output_dir / "manifest.js").write_text(
        "window.SHIELD_MANIFEST = " + json.dumps(manifest, indent=2) + ";\n"
    )
    for name in STATIC_ASSETS:
        shutil.copyfile(TEMPLATES_DIR / name, output_dir / name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True, type=Path,
                    help="Shield output dir (contains manifest.json)")
    args = ap.parse_args()
    try:
        write_assets(args.output_dir)
    except FileNotFoundError as e:
        print(f"write_shield_assets: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pytest pytest test_write_shield_assets.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/write_shield_assets.py shield/scripts/test_write_shield_assets.py
git commit -m "feat(shield): write_shield_assets — manifest.js + asset copy"
```

---

### Task 8: One-time migration — `rerender_all.py`

**Files:**
- Create: `shield/scripts/rerender_all.py`

- [ ] **Step 1: Create the migration script**

Create `shield/scripts/rerender_all.py`:

```python
#!/usr/bin/env python3
"""Re-render every Shield source markdown into the shared shell.

Walks {output_dir} for known source docs (and review summaries) and renders
each to its outputs/ HTML via render-markdown.sh + templates/shell.html, then
writes the shared assets. Idempotent — safe to re-run.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SHELL = SCRIPT_DIR.parent / "templates" / "shell.html"
RENDER_SH = SCRIPT_DIR / "render-markdown.sh"

# (source-md-relative-to-feature, output-html-relative-to-feature, title-prefix)
DOC_MAP = [
    ("research.md", "outputs/research.html", "Research"),
    ("prd.md", "outputs/prd.html", "PRD"),
    ("trd.md", "outputs/trd.html", "TRD"),
    ("plan.md", "outputs/plan.html", "Plan"),
    ("plan-architecture.md", "outputs/plan-architecture.html", "Architecture"),
]


def _render(md: Path, out: Path, title: str, output_dir: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(RENDER_SH), "--md", str(md), "--shell", str(SHELL),
         "--out", str(out), "--assets-root", str(output_dir), "--title", title],
        check=True,
    )


def rerender_all(output_dir: Path) -> int:
    count = 0
    for feature in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        if feature.name == "outputs":
            continue
        for src_name, out_rel, prefix in DOC_MAP:
            md = feature / src_name
            if md.is_file():
                _render(md, feature / out_rel, f"{prefix} — {feature.name}", output_dir)
                count += 1
        for summary in feature.glob("reviews/*/*/summary.md"):
            rel = summary.relative_to(feature).with_suffix(".html")
            _render(summary, feature / "outputs" / rel,
                    f"Review — {feature.name}", output_dir)
            count += 1
    print(f"rerender_all: rendered {count} page(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args()
    if not args.output_dir.is_dir():
        print(f"rerender_all: not a dir: {args.output_dir}", file=sys.stderr)
        return 2
    return rerender_all(args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke-test the script against a temp tree**

Run:
```bash
uv run python3 - <<'PY'
import subprocess, tempfile, pathlib
d = pathlib.Path(tempfile.mkdtemp())
f = d / "feat-a"; f.mkdir()
(f / "prd.md").write_text("# PRD\n\nbody\n")
r = subprocess.run(["shield/scripts/rerender_all.py", "--output-dir", str(d)],
                   capture_output=True, text=True)
print(r.stdout, r.stderr)
out = (f / "outputs" / "prd.html")
assert out.is_file(), "prd.html not rendered"
assert 'href="../../shield.css"' in out.read_text()
print("rerender smoke OK")
PY
```
Expected: `rerender_all: rendered 1 page(s)` then `rerender smoke OK`.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/rerender_all.py
git commit -m "feat(shield): rerender_all migration script"
```

---

### Task 9: Wire the doc + review skills to the shared shell

**Files:**
- Modify: `shield/skills/general/prd-docs/SKILL.md` (HTML render step, ~lines 286-303)
- Modify: `shield/skills/general/plan-docs/SKILL.md` (HTML render step, lines 99-123)
- Modify: `shield/skills/general/prd-docs/templates.md` (remove inline shell, ~lines 249-349)
- Modify: `shield/skills/general/plan-docs/templates.md` (remove inline shells, lines 3-387)
- Modify: `shield/skills/general/prd-review/SKILL.md`, `plan-review/SKILL.md`, `review/SKILL.md` (review-render steps)

- [ ] **Step 1: Replace the plan-docs HTML render block**

In `shield/skills/general/plan-docs/SKILL.md`, the HTML render section (lines ~99-123) currently writes a `plan.shell.html` then calls `render-markdown.sh`. Replace the render commands with the shared-shell form:

```bash
# Render TRD + plan into the shared shell (no per-skill shell file)
"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    trd.md \
  --shell "$CLAUDE_PLUGIN_ROOT/templates/shell.html" \
  --out   outputs/trd.html \
  --assets-root "{output_dir}" \
  --title "TRD — {feature}"

"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    plan.md \
  --shell "$CLAUDE_PLUGIN_ROOT/templates/shell.html" \
  --out   outputs/plan.html \
  --assets-root "{output_dir}" \
  --title "Plan — {feature}"

# Refresh manifest-derived page assets (manifest.js + static assets)
uv run "$CLAUDE_PLUGIN_ROOT/scripts/write_shield_assets.py" --output-dir "{output_dir}"
```

Delete the now-unused "write plan.shell.html" and "delete the shell" instructions in this section.

- [ ] **Step 2: Replace the prd-docs HTML render block**

In `shield/skills/general/prd-docs/SKILL.md` render step (~lines 286-303), replace the shell-write + render with:

```bash
"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    prd.md \
  --shell "$CLAUDE_PLUGIN_ROOT/templates/shell.html" \
  --out   outputs/prd.html \
  --assets-root "{output_dir}" \
  --title "PRD — {feature}"

uv run "$CLAUDE_PLUGIN_ROOT/scripts/write_shield_assets.py" --output-dir "{output_dir}"
```

- [ ] **Step 3: Strip the inline shell templates from templates.md**

In `shield/skills/general/prd-docs/templates.md` (~lines 249-349) and `shield/skills/general/plan-docs/templates.md` (lines 3-387), replace each inline `<!DOCTYPE html>…</html>` shell block with a one-line pointer:

```markdown
> The HTML shell is now shared — see `shield/templates/shell.html` and `shield/templates/shield.css`. Skills render via `render-markdown.sh --shell $CLAUDE_PLUGIN_ROOT/templates/shell.html`. Do not inline HTML/CSS here.
```

Keep any markdown body/story templates that are NOT HTML shells.

- [ ] **Step 4: Point the review skills at the shared shell**

In `shield/skills/general/prd-review/SKILL.md`, `plan-review/SKILL.md`, and `review/SKILL.md`, find each `render-markdown.sh` invocation that renders `summary.md`/`enhanced-*.md` to `outputs/reviews/...` and add `--shell "$CLAUDE_PLUGIN_ROOT/templates/shell.html" --assets-root "{output_dir}" --title "Review — {feature}"`, removing any inline review shell. After the render, ensure each calls:

```bash
uv run "$CLAUDE_PLUGIN_ROOT/scripts/write_shield_assets.py" --output-dir "{output_dir}"
```

- [ ] **Step 5: Verify no inline DOCTYPE shells remain in the skill templates**

Run: `grep -rl "<!DOCTYPE html>" shield/skills/general/prd-docs shield/skills/general/plan-docs`
Expected: no output (all inline shells removed).

- [ ] **Step 6: Commit**

```bash
git add shield/skills/general/prd-docs shield/skills/general/plan-docs shield/skills/general/prd-review shield/skills/general/plan-review shield/skills/general/review
git commit -m "feat(shield): render docs + reviews via shared shell, refresh assets"
```

---

### Task 10: End-to-end render eval + extend pre-commit

**Files:**
- Create: `shield/scripts/test_shared_shell_render.py`
- Modify: `.pre-commit-config.yaml:34-38`

- [ ] **Step 1: Write the end-to-end test**

Create `shield/scripts/test_shared_shell_render.py`:

```python
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
        assert 'href="../../shield.css"' in h
        assert 'src="../../manifest.js"' in h
        assert 'src="../../shield-nav.js"' in h
        assert 'data-shield-root="../../"' in h
        assert "<title>PRD — feat-a</title>" in h
        assert 'id="docs-dropdown"' in h
        assert "{{" not in h  # no unsubstituted placeholders
```

- [ ] **Step 2: Run it to confirm PASS**

Run: `cd shield/scripts && uv run --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_shared_shell_render.py -v`
Expected: PASS (1 passed).

- [ ] **Step 3: Extend the pre-commit render hook**

In `.pre-commit-config.yaml`, update the `render-markdown-tests` hook (lines 34-38):

```yaml
      - id: render-markdown-tests
        name: render-markdown pytest
        entry: bash -c 'cd shield/scripts && uv run --quiet --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_render_markdown_toc.py test_render_markdown_root.py test_shared_shell_render.py test_write_shield_assets.py test_migrate_outputs_manifest.py'
        language: system
        files: '^shield/(scripts/(render-markdown\.py|write_shield_assets\.py|migrate_outputs\.py|test_.*\.py)|templates/.*)$'
        pass_filenames: false
```

- [ ] **Step 4: Run the full render hook locally**

Run: `pre-commit run render-markdown-tests --all-files`
Expected: `Passed`.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/test_shared_shell_render.py .pre-commit-config.yaml
git commit -m "test(shield): end-to-end shared-shell render eval + pre-commit wiring"
```

---

### Task 11: Run migration, update example, docs, version bump, verify

**Files:**
- Generate/modify: `docs/shield/**/outputs/*.html`, `docs/shield/{index.html,manifest.js,shield.css,shield-nav.js,shield-dashboard.js}`
- Modify: `shield/examples/python-api/docs/shield/index.html`
- Modify: `shield/skills/general/manifest-schema.md`
- Modify: `.claude-plugin/marketplace.json:12`

- [ ] **Step 1: Rebuild manifest then re-render all existing docs**

Run:
```bash
# Rebuild manifest.json (schema 2.1) — migrate_outputs writes it under --apply
uv run shield/scripts/migrate_outputs.py --root docs/shield --apply --yes
# Re-render every source doc + review summary into the shared shell
uv run shield/scripts/rerender_all.py --output-dir docs/shield
# Emit manifest.js + copy the four static assets into docs/shield/
uv run shield/scripts/write_shield_assets.py --output-dir docs/shield
```
Expected: `wrote manifest: docs/shield/manifest.json`, then `rerender_all: rendered N page(s)`, and `docs/shield/` now contains `index.html`, `manifest.js`, `shield.css`, `shield-nav.js`, `shield-dashboard.js`.

Verify: `python3 -c "import json;print(json.load(open('docs/shield/manifest.json'))['schema_version'])"` → `2.1`.

- [ ] **Step 2: Manually open the dashboard and one doc page**

Run: `open docs/shield/index.html`
Expected (visual): the dashboard shows a card per feature with a pipeline strip; the **Docs ▾** menu opens and lists features → artifacts → reviews; clicking a doc link opens a page with the same header. Confirm a rendered doc (e.g. `docs/shield/backlog-20260527/outputs/prd.html`) shows the shared header and its Docs menu is populated.

- [ ] **Step 3: Regenerate the example index**

Replace `shield/examples/python-api/docs/shield/index.html` with the new `shield/templates/index.html` content (copy verbatim), so the example reflects the new template:

```bash
cp shield/templates/index.html shield/examples/python-api/docs/shield/index.html
```

Also copy the static assets next to it so the example is self-contained:
```bash
cp shield/templates/shield.css shield/templates/shield-nav.js shield/templates/shield-dashboard.js shield/examples/python-api/docs/shield/
```
(If the example has a committed `manifest.json`, run `uv run shield/scripts/write_shield_assets.py --output-dir shield/examples/python-api/docs/shield` instead to also emit its `manifest.js`.)

- [ ] **Step 4: Document schema 2.1 + the templating model**

In `shield/skills/general/manifest-schema.md`, update the schema block to `schema_version: "2.1"`, add the `trd` artifact and `reviews[].entries[]` (`{date, path}`), and add a short "Page assets" subsection: pages are rendered into `shield/templates/shell.html`; `manifest.js` + the four static assets are written to `docs/shield/` by `write_shield_assets.py`; nav/dashboard are built client-side from `window.SHIELD_MANIFEST` (no fetch, file:// safe).

- [ ] **Step 5: Bump the Shield version**

In `.claude-plugin/marketplace.json`, change the `shield` block `"version": "2.24.1"` → `"version": "2.25.0"`.

Run: `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 6: Full pre-commit + render hook**

Run: `pre-commit run --all-files`
Expected: all hooks Pass or Skip.

- [ ] **Step 7: Commit**

```bash
git add docs/shield shield/examples shield/skills/general/manifest-schema.md .claude-plugin/marketplace.json
git commit -m "chore(shield): migrate all pages to shared template + bump to 2.25.0"
```

- [ ] **Step 8: Push and open PR**

```bash
git push -u origin shield-page-templates
```
PR body MUST include: the new eval/test paths and their PASS output; a note that JS/CSS assets are statically asserted + covered by the end-to-end render test (no JS unit harness exists); the schema 2.1 bump; the version-bump merge-order caveat; and a screenshot or description of the rendered dashboard.

---

## Self-Review

**Spec coverage:**
- Shared shell + CSS + nav.js + dashboard.js + index.html → Tasks 3,4,5,6. ✅
- `manifest.js` generated, file:// safe → Task 7. ✅
- Manifest schema 2.1 (trd + review entries) → Task 1. ✅
- `{{ROOT}}` asset-path substitution → Task 2. ✅
- Asset placement at docs/shield root → Task 7 (`write_shield_assets`). ✅
- Generator script → Task 7. ✅
- One-time migration (re-render all, reviews included) → Tasks 8 + 11. ✅
- Skill wiring (prd/plan/review) → Task 9. ✅
- Eval coverage → Tasks 1,2,7,10 (pytests) + pre-commit wiring Task 10. ✅
- Example page update + manifest-schema docs → Task 11. ✅
- Version bump → Task 11. ✅
- Decisions honored: nav layout A (Task 4/5 dropdown), light theme (Task 3), card+pipeline dashboard (Task 6), client-side via manifest.js (Task 7), shared-files+placeholders (Tasks 2-4), reviews in scope (Tasks 1,9), re-render all (Task 8/11), CDN mermaid (Task 4 shell). ✅

**Placeholder scan:** No TBD/TODO. All code blocks complete; commands have expected output.

**Type/name consistency:** `write_assets(output_dir)` defined in Task 7 and called in tests/Task 11 consistently. `build_manifest` returns `schema_version: "2.1"` (Task 1) and Task 11 Step 1 verifies the same string. Artifact keys (`research, prd, trd, plan_md, plan_arch_md, plan_json`) match between `migrate_outputs.TRACKED_ARTIFACTS`, `shield-nav.js` `ARTIFACTS`, and `shield-dashboard.js` `LINKS`. `{{ROOT}}` / `data-shield-root` / `dataset.shieldRoot` consistent across shell.html (Task 4), render-markdown.py (Task 2), shield-nav.js (Task 5). Review entry path `{feature}/outputs/reviews/{type}/{date}/summary.html` consistent between Task 1 (manifest) and Task 8 (rerender output location).

**Resolved:** `migrate_outputs.py` writes `manifest.json` via `--root docs/shield --apply --yes` (verified at `migrate_outputs.py:285-288`). Task 11 Step 1 uses that exact invocation.
