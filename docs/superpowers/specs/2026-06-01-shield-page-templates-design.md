# Design: Shield page templating (shared chrome, nav, dashboard)

**Date:** 2026-06-01
**Status:** Approved (design); pending implementation plan
**Author:** ashwinimanoj
**Branch:** `shield-page-templates`

## Problem

Shield's HTML output has no shared structure. Each skill emits its own inline
HTML shell with duplicated, divergent CSS (the PRD is light/blue, the example
`index.html` is dark, the plan is a third variant). `index.html` has **no
generator at all** — the only example is hand-written. There is no global
navigation: a reader cannot get from one doc to another. Result: inconsistent,
unconnected pages and a missing dashboard.

## Goal

One shared template system for every Shield page: a single shell, one
stylesheet, a global header with a nested **Docs ▾** menu that reaches every doc
in the project, and a real `index.html` dashboard — all driven by `manifest.json`.

## Decisions (from brainstorming)

| Decision | Choice |
|---|---|
| Nav layout | **A — top-bar dropdown** with a nested flyout (feature → artifacts → reviews) |
| Theme | **Light, doc-first** — one palette, blue `#1a73e8` accent, 🛡 Shield wordmark |
| Dashboard | **Card grid** (one card per feature) **+ a pipeline strip** (Research → PRD → Plan → Implement) |
| Nav data delivery | **Client-side, via a generated `manifest.js`** (not raw `fetch`) — see file:// note |
| Template store | **Shared files + placeholders** under `shield/templates/`; one shared CSS; no Jinja2 |
| Reviews | **In scope** — rendered with the shared shell and nested in the nav |
| Existing pages | **Re-render all** to the new template (one-time migration pass) |
| Mermaid | **Keep CDN** (jsdelivr); diagrams need internet, text/tables don't |

### The file:// constraint (why `manifest.js`, not `fetch`)

Browsers block `fetch()` of a local JSON file over `file://` (CORS). Shield docs
are usually opened straight from disk. A `<script src>` *is* allowed on
`file://`. So nav/dashboard data ships as a generated `manifest.js`
(`window.SHIELD_MANIFEST = {…}`), loaded by every page. Because every page loads
the *same* `manifest.js`, adding a feature and regenerating that one file
refreshes every page's menu — no page re-rendering. Works over `file://` and
`http://`.

## Design

### 1. Shared template assets — new `shield/templates/`

| File | Responsibility |
|---|---|
| `shell.html` | The one HTML shell every rendered page uses: `<head>` (CSS link, mermaid CDN script, asset script tags), header bar with the **Docs ▾** dropdown mount, `{{TOC}}`, `{{BODY}}`, footer. Placeholders: `{{TITLE}}`, `{{ROOT}}`, `{{TOC}}`, `{{BODY}}`, `{{META}}`. |
| `shield.css` | **One** light-theme stylesheet — typography, tables, code, blockquotes, nav/dropdown, dashboard cards, badges, pipeline strip, milestones, story cards. Replaces all three inline themes. |
| `shield-nav.js` | Builds the nested **Docs ▾** dropdown from `window.SHIELD_MANIFEST` (feature → artifacts → reviews → dated entries). |
| `shield-dashboard.js` | Builds the card grid + pipeline strip on `index.html` from `window.SHIELD_MANIFEST`; renders a "no features yet" empty state. |
| `index.html` | The dashboard page: shell + dashboard mount + scripts. Static — never regenerated, always reflects current data. |

### 2. Data: `manifest.js`

The generator writes `docs/shield/manifest.js` (`window.SHIELD_MANIFEST = <manifest
verbatim>`) whenever `manifest.json` changes. Single source of truth for both nav
and dashboard.

### 3. Manifest schema bump (v2 → v2.1)

To nest *dated* review entries in the nav, `reviews` gains an `entries[]` list of
`{date, path}` alongside the existing `{latest, count}`. The manifest builder
already walks the filesystem (`migrate_outputs.py build_manifest`), so
enumerating review folders is cheap and backward-compatible (additive field).

### 4. Asset placement (file:// safe)

The four static assets (`shield.css`, `shield-nav.js`, `shield-dashboard.js`,
`index.html`) plus generated `manifest.js` are copied to `docs/shield/` root.
Every rendered page references them via a `{{ROOT}}` relative path (e.g.
`../../shield.css` from a `outputs/` page), computed at render time.

### 5. `render-markdown.py` changes

- Consume the shared `shell.html` instead of per-skill inline shells.
- Compute `{{ROOT}}` (relative depth from the output file up to `docs/shield/`)
  and substitute it into the CSS link + `<script src>` tags + header.
- Keep existing `{{BODY}}` / `{{TOC}}` substitution and relative-link rewriting.

### 6. New generator script — `shield/scripts/write_shield_assets.py`

After `manifest.json` is written, one idempotent call: (a) emits `manifest.js`,
(b) copies the static assets into `docs/shield/`. Run by every skill that writes
the manifest.

### 7. One-time migration — `shield/scripts/rerender_all.py`

Globs every source markdown under `docs/shield/` (`research.md`, `prd.md`,
`trd.md`, `plan.md`, review summaries) and re-renders each to its `outputs/` HTML
with the shared shell, so the whole project is consistent immediately. Run once
during this change.

### 8. Skill wiring

`prd-docs`, `plan-docs`, and the review skills stop emitting inline HTML/CSS
shells. They point `render-markdown.sh` at the shared `shell.html` and call
`write_shield_assets.py` after manifest writes.

### 9. Eval coverage

Extend the existing `render-markdown` pytest:
- A rendered page contains the header markup, the CSS link, the `manifest.js` +
  `shield-nav.js` script tags, and the correct `{{ROOT}}` depth for its location.
- `write_shield_assets.py` produces a `manifest.js` whose payload is parseable
  JSON assigned to `window.SHIELD_MANIFEST`, and copies all four assets.
- `manifest.js` review `entries[]` are present when review folders exist.

### 10. Version bump

Bump Shield in `.claude-plugin/marketplace.json`.

## Files touched

| File | Change |
|---|---|
| `shield/templates/shell.html` | New — shared shell |
| `shield/templates/shield.css` | New — single stylesheet |
| `shield/templates/shield-nav.js` | New — nested Docs menu builder |
| `shield/templates/shield-dashboard.js` | New — dashboard builder |
| `shield/templates/index.html` | New — dashboard page |
| `shield/scripts/render-markdown.py` | Consume shared shell; `{{ROOT}}` substitution |
| `shield/scripts/write_shield_assets.py` | New — emit manifest.js + copy assets |
| `shield/scripts/rerender_all.py` | New — one-time migration pass |
| `shield/scripts/migrate_outputs.py` | Add `reviews.entries[]` (schema v2.1) |
| `shield/skills/general/prd-docs/*` | Use shared shell; call write_shield_assets |
| `shield/skills/general/plan-docs/*` | Use shared shell; call write_shield_assets |
| `shield/skills/general/manifest-schema.md` | Document v2.1 + asset/templating model |
| review skills | Render review summaries via shared shell |
| `shield/examples/python-api/docs/shield/index.html` | Regenerate to new template |
| `shield/tests/` render-markdown pytest | New assertions (§9) |
| `.claude-plugin/marketplace.json` | Version bump |

## Non-goals (v1)

- No Jinja2 / templating-engine dependency.
- No vendored mermaid (CDN stays).
- No nav search/filter, no per-page theming toggle, no dark mode.
- No server — pages remain static files openable from disk.
