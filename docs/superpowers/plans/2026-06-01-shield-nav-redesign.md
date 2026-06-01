# Shield Nav Bar Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the vague `Docs ▾` header with a breadcrumb (sense of place) + a **Features ▾** panel that has a search filter over a grouped feature→doc→reviews list, all built client-side from `window.SHIELD_MANIFEST`.

**Architecture:** Presentation-only change to the shared template assets from the page-templates work (branch `shield-page-templates`, PR #61). No changes to `render-markdown.py`, the manifest schema, or `write_shield_assets.py`. The breadcrumb is derived in JS from `location.pathname` + `data-shield-root`; the panel reuses the same manifest data with an added live filter.

**Tech Stack:** vanilla JS, CSS, HTML. Render eval via existing `shield/scripts/test_shared_shell_render.py`.

**Spec:** `docs/superpowers/specs/2026-06-01-shield-nav-redesign-design.md`

---

## File Structure

| File | Change |
|---|---|
| `shield/scripts/test_shared_shell_render.py` | MODIFY — assert new nav markup (breadcrumb, Features, search); assert old `Docs ▾` gone |
| `shield/templates/shield.css` | MODIFY — replace header/`.docs-*` block (lines 8-25) with breadcrumb/panel/search/tag styles |
| `shield/templates/shell.html` | MODIFY — new header markup (lines 17-24) |
| `shield/templates/index.html` | MODIFY — same new header markup (lines 13-19) |
| `shield/templates/shield-nav.js` | MODIFY — rewrite: build breadcrumb + filterable panel + ⌘K/Esc/click-outside |

**Shared element contract** (IDs/classes used across all four files + the test):
- `nav.crumb#shield-crumb` — breadcrumb mount (JS-filled)
- `button.feat-btn#docs-toggle` — text `Features ▾`
- `div.feat-panel#docs-panel` — contains `input.docs-search#docs-search` + `div#docs-results`

---

### Task 1: Update the render structural test (RED)

**Files:**
- Modify: `shield/scripts/test_shared_shell_render.py`

- [ ] **Step 1: Replace the assertion block**

In `shield/scripts/test_shared_shell_render.py`, replace the existing header/asset assertions inside `test_shared_shell_wires_assets_at_depth` (the `assert ...` lines after `h = out.read_text()`) with:

```python
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
```

- [ ] **Step 2: Run it to confirm RED**

Run: `cd shield/scripts && uv run --quiet --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_shared_shell_render.py -v`
Expected: FAIL — current `shell.html` still has `Docs ▾` / `id="docs-dropdown"` and lacks `id="shield-crumb"`.

- [ ] **Step 3: Commit the failing test**

```bash
git add shield/scripts/test_shared_shell_render.py
git commit -m "test(shield): RED — redesigned nav markup assertions"
```

---

### Task 2: Replace the nav CSS

**Files:**
- Modify: `shield/templates/shield.css:8-25`

- [ ] **Step 1: Replace the header/docs-menu block**

In `shield/templates/shield.css`, replace lines 8-25 (the `/* Header + nested Docs menu */` block through the `.docs-group` rule) with:

```css
/* Header — breadcrumb + Features panel */
.shield-header { display:flex; align-items:center; gap:12px; padding:10px 18px;
  border-bottom:1px solid var(--border); background:#fff; position:sticky; top:0; z-index:50; font-size:.92rem; }
.shield-header .brand { font-weight:700; color:var(--text); text-decoration:none; white-space:nowrap; }
.shield-header .bar-sep { color:#9aa3af; }
.crumb { color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.crumb a { color:var(--muted); text-decoration:none; }
.crumb a:hover { color:var(--accent); }
.crumb .chev { color:#c2c8d0; margin:0 5px; }
.crumb .here { color:var(--accent); font-weight:600; }
.bar-spacer { flex:1; }
.feat-wrap { position:relative; }
.feat-btn { cursor:pointer; border:1px solid var(--border); background:var(--panel);
  color:var(--accent); border-radius:6px; padding:5px 12px; font-size:.92rem; white-space:nowrap; }
.feat-btn:hover { border-color:var(--accent); }
.feat-panel { display:none; position:absolute; right:0; top:115%; width:330px; background:#fff;
  border:1px solid var(--border); border-radius:10px; box-shadow:0 10px 30px rgba(0,0,0,.12);
  padding:10px; max-height:74vh; overflow:auto; }
.feat-panel.open { display:block; }
.docs-search { width:100%; border:1px solid var(--border); border-radius:7px; padding:8px 10px;
  font-size:.85rem; outline:none; }
.docs-search:focus { border-color:var(--accent); }
.feat-name { font-weight:600; font-size:.82rem; margin:10px 4px 2px; color:var(--text); }
.doc { display:flex; align-items:center; gap:8px; padding:5px 8px 5px 14px; border-radius:6px;
  color:var(--accent); text-decoration:none; font-size:.85rem; }
.doc:hover { background:var(--panel); }
.doc .tag { margin-left:auto; font-size:.62rem; color:var(--muted); background:var(--panel);
  border:1px solid var(--border); border-radius:10px; padding:0 6px; text-transform:uppercase; }
.doc.rev { color:var(--muted); padding-left:22px; }
.docs-empty { color:var(--muted); font-size:.8rem; padding:8px 6px; }
```

- [ ] **Step 2: Verify braces balance**

Run: `python3 -c "s=open('shield/templates/shield.css').read(); assert s.count('{')==s.count('}'), 'unbalanced'; assert '.docs-dropdown' not in s and '.docs-feature' not in s; print('css ok', s.count('{'))"`
Expected: `css ok <N>` (old dropdown classes gone).

- [ ] **Step 3: Commit**

```bash
git add shield/templates/shield.css
git commit -m "feat(shield): nav CSS — breadcrumb + Features panel + search"
```

---

### Task 3: Update the header markup in shell.html and index.html

**Files:**
- Modify: `shield/templates/shell.html:17-24`
- Modify: `shield/templates/index.html:13-19`

- [ ] **Step 1: Replace the header in shell.html**

In `shield/templates/shell.html`, replace the `<header class="shield-header">…</header>` block (lines 17-24) with:

```html
<header class="shield-header">
  <a class="brand" href="{{ROOT}}index.html">🛡 Shield</a>
  <span class="bar-sep">|</span>
  <nav class="crumb" id="shield-crumb"></nav>
  <span class="bar-spacer"></span>
  <div class="feat-wrap">
    <button class="feat-btn" id="docs-toggle" aria-expanded="false">Features ▾</button>
    <div class="feat-panel" id="docs-panel">
      <input class="docs-search" id="docs-search" placeholder="Search docs…  (⌘K)" autocomplete="off" />
      <div id="docs-results"></div>
    </div>
  </div>
</header>
```

- [ ] **Step 2: Replace the header in index.html**

In `shield/templates/index.html`, replace the `<header class="shield-header">…</header>` block (lines 13-19) with the identical markup but with `index.html` instead of `{{ROOT}}index.html` (index sits at the root):

```html
<header class="shield-header">
  <a class="brand" href="index.html">🛡 Shield</a>
  <span class="bar-sep">|</span>
  <nav class="crumb" id="shield-crumb"></nav>
  <span class="bar-spacer"></span>
  <div class="feat-wrap">
    <button class="feat-btn" id="docs-toggle" aria-expanded="false">Features ▾</button>
    <div class="feat-panel" id="docs-panel">
      <input class="docs-search" id="docs-search" placeholder="Search docs…  (⌘K)" autocomplete="off" />
      <div id="docs-results"></div>
    </div>
  </div>
</header>
```

- [ ] **Step 3: Verify markup**

Run: `python3 -c "import sys; [sys.exit('FAIL '+f) for f in ('shield/templates/shell.html','shield/templates/index.html') if 'id=\"shield-crumb\"' not in open(f).read() or 'Docs ▾' in open(f).read()]; print('headers ok')"`
Expected: `headers ok`

- [ ] **Step 4: Commit**

```bash
git add shield/templates/shell.html shield/templates/index.html
git commit -m "feat(shield): header markup — breadcrumb + Features panel"
```

---

### Task 4: Rewrite `shield-nav.js`

**Files:**
- Modify: `shield/templates/shield-nav.js` (full rewrite)

- [ ] **Step 1: Replace the file contents**

Replace all of `shield/templates/shield-nav.js` with:

```javascript
// Builds the header breadcrumb + the filterable Features panel from
// window.SHIELD_MANIFEST. Breadcrumb is derived from the URL path +
// data-shield-root. No fetch — data comes from manifest.js. file:// safe.
(function () {
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  // artifact key -> [label, filename, tag]
  var ARTIFACTS = [
    ["research", "Research", "research.html", "research"],
    ["prd", "PRD", "prd.html", "prd"],
    ["trd", "TRD", "trd.html", "trd"],
    ["plan_md", "Plan", "plan.html", "plan"],
    ["plan_arch_md", "Architecture", "plan-architecture.html", "arch"],
    ["plan_json", "Sidecar JSON", "../plan.json", "json"],
  ];
  // filename -> breadcrumb label for the active doc
  var FILE_LABELS = {
    "prd.html": "PRD", "trd.html": "TRD", "plan.html": "Plan",
    "research.html": "Research", "plan-architecture.html": "Architecture",
    "summary.html": "Review", "enhanced-prd.html": "Enhanced PRD",
    "enhanced-plan.html": "Enhanced Plan", "index.html": "Dashboard",
  };

  function titleize(file) {
    return file.replace(/\.html$/, "").replace(/[-_]/g, " ")
      .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  // ---- Breadcrumb (from path) ----
  function buildCrumb(root) {
    var crumb = document.getElementById("shield-crumb");
    if (!crumb) return;
    var parts = decodeURIComponent(location.pathname).split("/").filter(Boolean);
    var file = parts[parts.length - 1] || "index.html";
    var dash = el("a", null, "Dashboard");
    dash.setAttribute("href", root + "index.html");
    crumb.appendChild(dash);

    var oi = parts.lastIndexOf("outputs");
    if (file === "index.html" || oi <= 0) {
      // dashboard (or unknown) — just mark Dashboard active
      dash.className = "here";
      dash.removeAttribute("href");
      return;
    }
    var feature = parts[oi - 1];
    crumb.appendChild(el("span", "chev", "›"));
    crumb.appendChild(el("span", null, feature));

    var ri = parts.lastIndexOf("reviews");
    crumb.appendChild(el("span", "chev", "›"));
    if (ri !== -1 && ri > oi) {
      var rtype = parts[ri + 1] || "", rdate = parts[ri + 2] || "";
      crumb.appendChild(el("span", "here", rtype + " review · " + rdate));
    } else {
      crumb.appendChild(el("span", "here", FILE_LABELS[file] || titleize(file)));
    }
  }

  // ---- Features panel (grouped, filterable) ----
  function matches(q, s) { return s.toLowerCase().indexOf(q) !== -1; }

  function buildResults(manifest, root, q) {
    var frag = document.createDocumentFragment();
    var features = (manifest && manifest.features) || [];
    var query = (q || "").trim().toLowerCase();
    var shown = 0;
    features.forEach(function (f) {
      var featMatch = matches(query, f.name);
      var docs = [];
      ARTIFACTS.forEach(function (a) {
        if (f.artifacts && f.artifacts[a[0]]) {
          if (!query || featMatch || matches(query, a[1])) docs.push(a);
        }
      });
      var revs = [];
      ["prd", "plan", "code"].forEach(function (rt) {
        var rv = f.reviews && f.reviews[rt];
        if (rv && rv.entries) {
          rv.entries.forEach(function (en) {
            var label = rt + " review · " + en.date;
            if (!query || featMatch || matches(query, label))
              revs.push({ label: label, path: en.path });
          });
        }
      });
      if (!docs.length && !revs.length) return;
      shown++;
      frag.appendChild(el("div", "feat-name", f.name));
      docs.forEach(function (a) {
        var href = a[2].indexOf("../") === 0
          ? root + f.name + "/" + a[2].slice(3)
          : root + f.name + "/outputs/" + a[2];
        var link = el("a", "doc", a[1] + '<span class="tag">' + a[3] + "</span>");
        link.setAttribute("href", href);
        frag.appendChild(link);
      });
      revs.forEach(function (r) {
        var link = el("a", "doc rev", "↳ " + r.label);
        link.setAttribute("href", root + r.path);
        frag.appendChild(link);
      });
    });
    if (!shown) frag.appendChild(el("div", "docs-empty", 'No docs match "' + query + '"'));
    return frag;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.body.dataset.shieldRoot || "";
    buildCrumb(root);

    var btn = document.getElementById("docs-toggle");
    var panel = document.getElementById("docs-panel");
    var search = document.getElementById("docs-search");
    var results = document.getElementById("docs-results");
    if (!btn || !panel || !search || !results) return;

    function paint() {
      results.innerHTML = "";
      results.appendChild(buildResults(window.SHIELD_MANIFEST, root, search.value));
    }
    function open() {
      panel.classList.add("open"); btn.setAttribute("aria-expanded", "true");
      search.value = ""; paint(); search.focus();
    }
    function close() {
      panel.classList.remove("open"); btn.setAttribute("aria-expanded", "false");
    }
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      panel.classList.contains("open") ? close() : open();
    });
    search.addEventListener("input", paint);
    search.addEventListener("click", function (e) { e.stopPropagation(); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); open(); }
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".feat-wrap")) close();
    });
  });
})();
```

- [ ] **Step 2: Verify structural shape**

Run: `python3 -c "s=open('shield/templates/shield-nav.js').read(); [s.index(t) for t in ('buildCrumb','buildResults','docs-results','shieldRoot','metaKey')]; assert 'docs-dropdown' not in s; print('nav js ok')"`
Expected: `nav js ok`

- [ ] **Step 3: Commit**

```bash
git add shield/templates/shield-nav.js
git commit -m "feat(shield): shield-nav.js — breadcrumb + filterable Features panel"
```

---

### Task 5: GREEN, migrate, verify, push

**Files:**
- Generate: `docs/shield/**` re-rendered pages + copied assets
- Modify (commit): spec + plan docs

- [ ] **Step 1: Run the render test — confirm GREEN**

Run: `cd shield/scripts && uv run --quiet --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_shared_shell_render.py -v`
Expected: PASS (1 passed) — the new shell satisfies all redesigned-nav assertions.

- [ ] **Step 2: Run the full render/asset suite — no regressions**

Run: `cd shield/scripts && uv run --quiet --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_render_markdown_toc.py test_render_markdown_links.py test_render_markdown_root.py test_shared_shell_render.py test_write_shield_assets.py test_migrate_outputs_manifest.py -q`
Expected: PASS (all passed).

- [ ] **Step 3: Re-render all pages + refresh assets**

Run (from repo root):
```bash
uv run shield/scripts/rerender_all.py --output-dir docs/shield
uv run shield/scripts/write_shield_assets.py --output-dir docs/shield
```
Expected: `rerender_all: rendered N page(s)`; `docs/shield/shield-nav.js`, `shield.css`, `index.html` updated to the redesigned versions.

- [ ] **Step 4: Manually verify in a browser**

Run: `open docs/shield/index.html && open docs/shield/backlog-20260527/outputs/prd.html`
Expected (visual):
- PRD page breadcrumb reads `Dashboard › backlog-20260527 › PRD` (last segment emphasized).
- `Features ▾` opens a panel with a search box; typing `plan` filters to Plan docs + plan reviews; `Esc` and click-outside close it; `⌘K` opens it.
- Dashboard page breadcrumb shows just `Dashboard` (active).

- [ ] **Step 5: Pre-commit**

Run: `pre-commit run --all-files`
Expected: all hooks Pass or Skip (render-markdown pytest Passes).

- [ ] **Step 6: Commit the regenerated output + spec/plan**

```bash
git add docs/shield docs/superpowers/specs/2026-06-01-shield-nav-redesign-design.md docs/superpowers/plans/2026-06-01-shield-nav-redesign.md
git commit -m "chore(shield): re-render pages with redesigned nav + spec/plan"
```

- [ ] **Step 7: Push to the existing PR #61 branch**

```bash
git push
```
(The branch `shield-page-templates` already backs PR #61; this extends it. Update the PR body to note the nav redesign supersedes the original `Docs ▾`.)

---

## Self-Review

**Spec coverage:**
- Breadcrumb (location), derived from path + data-shield-root → Task 4 `buildCrumb`. ✅
- Features panel replacing "Docs", grouped feature→docs→reviews → Task 3 markup + Task 4 `buildResults`. ✅
- Search filter (feature name OR doc/review label) → Task 4 `buildResults` + `matches`. ✅
- ⌘K / Esc / click-outside → Task 4 keydown + click handlers. ✅
- Type tags on docs; reviews nested with ↳ → Task 4 (`tag` span, `doc rev`). ✅
- Polish/branding (one row, breadcrumb, panel shadow) → Task 2 CSS. ✅
- Remove old `.docs-*` dropdown → Task 2 (verified absent) + Task 3 (old markup replaced). ✅
- Presentation-only (no render-markdown/schema/generator changes) → no tasks touch them. ✅
- Eval coverage → Task 1 (structural assertions) + Tasks 5.1–5.2. ✅
- Migration (re-render all) → Task 5.3. ✅

**Placeholder scan:** No TBD/TODO. All code blocks complete; commands have expected output.

**Type/name consistency:** Element IDs/classes match across test (Task 1), CSS (Task 2), markup (Task 3), and JS (Task 4): `shield-crumb`, `docs-toggle`, `docs-panel`, `docs-search`, `docs-results`, `feat-wrap`, `feat-panel`, `feat-btn`, `crumb`, `doc`, `feat-name`, `docs-empty`. The `plan_json` "../plan.json" relative form is handled in `buildResults` (the `indexOf("../")` branch) so the JSON link resolves to `{feature}/plan.json`, consistent with the dashboard's sidecar link.

**Note (JS has no unit harness):** breadcrumb/filter/⌘K behavior is covered by the structural render test (markup present) + the manual browser check (Task 5.4) + the interactive mockup already validated. Stated in the spec and to be repeated in the PR body.
