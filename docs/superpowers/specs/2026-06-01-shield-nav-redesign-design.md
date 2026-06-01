# Design: Shield nav bar redesign (breadcrumb + Features panel + search)

**Date:** 2026-06-01
**Status:** Approved (design); pending implementation plan
**Branch:** `shield-page-templates` (extends the unmerged page-templates work, PR #61)
**Author:** ashwinimanoj

## Problem

The shipped nav (`🛡 Shield · Dashboard · Docs ▾`) is too vague. Per the user, all
four of: (1) no sense of place — you can't tell which feature/doc you're viewing;
(2) "Docs" is a generic catch-all that hides the project's feature→artifact
structure; (3) it looks plain/unbranded; (4) the open dropdown is a long flat
tree that's hard to scan.

## Goal

Replace the header with a breadcrumb (location), a **Features ▾** panel that
exposes the project's structure with a **search filter** over a grouped list, and
a more polished bar — all still built client-side from `window.SHIELD_MANIFEST`.

## Decision (chosen design: "A + C-search")

A single-row header:

```
🛡 Shield  |  Dashboard › {feature} › {docType}            [ Features ▾ ]
```

- **Breadcrumb** (left): `Dashboard › {feature} › {docType}`, the last segment
  emphasized. Derived client-side from `location.pathname` + the page's
  `data-shield-root` depth — no render-time plumbing.
- **Features ▾** (right): opens a panel containing a **search box** over a
  **grouped list** (feature → its docs → nested reviews). Each doc shows a small
  type tag (`prd`/`trd`/`plan`/`research`/`arch`/`json`); reviews nest with `↳`.
- **Interactions:** `⌘K`/`Ctrl-K` opens the panel and focuses search; typing
  filters live (matches feature name OR doc/review label); `Esc` and
  click-outside close; the panel is keyboard-reachable.
- Validated via an interactive mockup against real project features.

## Design

### Breadcrumb derivation (client-side, file:// safe)

`shield-nav.js` computes the breadcrumb from the path:
- Read `document.body.dataset.shieldRoot` (already injected — relative prefix to
  `docs/shield/`).
- Split `location.pathname`; take the segments after the shield root.
- Map: `index.html` → `Dashboard` only; `{feature}/outputs/{file}.html` →
  `Dashboard › {feature} › LABEL[file]`; review paths
  `{feature}/outputs/reviews/{type}/{date}/summary.html` →
  `Dashboard › {feature} › {type} review · {date}`.
- Filename→label map: `prd.html`→PRD, `trd.html`→TRD, `plan.html`→Plan,
  `research.html`→Research, `plan-architecture.html`→Architecture,
  `summary.html`→Review. Unknown → title-cased stem.
- `Dashboard` links to `{ROOT}index.html`; `{feature}` links to its primary doc
  (first present of prd/trd/plan/research) or the dashboard anchor.

### Features panel + search

Rebuilds the existing manifest-driven menu as a filterable panel:
- A `<input>` search at the top of the panel.
- Below it, the grouped list built from `window.SHIELD_MANIFEST.features[]`
  (same artifact + `reviews[].entries[]` data as today).
- Filter: case-insensitive substring over feature name and each doc/review
  label; a feature shows if its name matches (all its docs) or any of its
  docs/reviews match. Empty query shows everything. No matches → "No docs match".
- Links use `data-shield-root` prefix so they resolve from any page depth
  (unchanged from current behavior).

### Files touched

| File | Change |
|---|---|
| `shield/templates/shell.html` | Replace header block: brand + breadcrumb container + Features button + panel (search input + results mount) |
| `shield/templates/index.html` | Same header markup (breadcrumb resolves to just "Dashboard") |
| `shield/templates/shield.css` | Header/breadcrumb/panel/search/tag styles; remove old `.docs-*` dropdown styles |
| `shield/templates/shield-nav.js` | Build breadcrumb from path; build filterable panel; `⌘K`/`Esc`/click-outside handlers |

No changes to `render-markdown.py`, the manifest schema, or `write_shield_assets.py` — the redesign is presentation-only over the same data and the same `{{ROOT}}`/`data-shield-root` mechanism.

### Eval coverage

Extend `shield/scripts/test_shared_shell_render.py` (and re-run after copying
assets): assert the rendered header contains the breadcrumb container, the
**Features** button, and the search input; assert no stale `Docs ▾` text remains.
JS behavior (filter, breadcrumb, ⌘K) has no unit harness — covered by structural
assertions + the interactive review already done. State this in the PR body.

### Migration

Re-run `rerender_all.py` + `write_shield_assets.py` so existing pages pick up the
new shell/CSS/JS (same one-time pass as the parent work).

## Non-goals

- No always-visible standalone search field (search lives inside the panel).
- No option-B artifact tabs / second row.
- No server-side breadcrumb injection (derived client-side).
- No dark mode, no nav search across doc *body* text (only doc titles/features).

## Version

Folds into the page-templates change; keep the same `2.25.0` bump (no separate
bump — this lands in the same PR before merge).
