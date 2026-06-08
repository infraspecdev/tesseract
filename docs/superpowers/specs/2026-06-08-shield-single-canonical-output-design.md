# Shield: one canonical output (Markdown), HTML as a build artifact

**Date:** 2026-06-08
**Status:** Approved (design) — pending spec review
**Scope:** Shield plugin output artifacts (`docs/shield/`)

## Problem

Shield writes every artifact twice and commits both:

- `docs/shield/{feature}/*.md` — the authored Markdown
- `docs/shield/{feature}/outputs/**/*.html` — an HTML mirror, plus generated
  site assets at the `docs/shield/` root (`index.html`, `manifest.js`,
  `shield.css`, `shield-nav.js`, `shield-dashboard.js`)

Today 41 HTML files are tracked in git alongside their Markdown. This is
confusing and wasteful because the HTML carries **no unique information** — it
is rendered purely from Markdown by `shield/scripts/render-markdown.sh`. The
real dependency chain is one-way:

```
JSON sidecar (plan.json, prd.meta.json)   ← structured source of truth
        ↓ authored or rendered
Markdown (.md)                            ← canonical human deliverable
        ↓ render-markdown.sh (pure render)
HTML (.html) + site assets                ← view-only, regenerable
```

Committing both means: two parallel trees that must stay in sync, doubled diffs
on every change, and a standing drift risk (hand-edited HTML, or stale HTML).

## Decision

**Markdown is the single canonical, committed, authored output.** HTML is
demoted to a **local build artifact** — generated on demand, never committed,
treated like `dist/`.

Chosen over two alternatives:

- **Keep both committed + CI drift-guard** — rejected; keeps the double tree and
  doubled diffs, only papers over the smell.
- **Drop HTML entirely** — rejected; the browsable dashboard (nav, Mermaid,
  cross-linking) is the real consumer.

Confirmed constraint: people open the HTML **locally** in a browser. Nothing
hosts/serves the committed `outputs/` tree, so gitignoring HTML costs only a
"build before you browse" step.

## Design

### 1. What stays committed vs. ignored

**Committed (canonical / source):**
- All `*.md` under `docs/shield/`
- All JSON sidecars: `manifest.json`, `plan.json`, `*.meta.json`,
  `*-comments.json`, `grades.json`

**Gitignored (generated, regenerable):**
- `docs/shield/**/outputs/` — every rendered per-artifact HTML tree
- `docs/shield/index.html`
- `docs/shield/manifest.js`
- `docs/shield/shield.css`, `docs/shield/shield-nav.js`,
  `docs/shield/shield-dashboard.js`

Note: `manifest.json` stays committed (it is the index source); `manifest.js`
is a generated JS mirror and is ignored.

### 2. Remove already-committed HTML

`git rm --cached` the 41 tracked `.html` files plus the tracked root site
assets (`docs/shield/index.html`, `docs/shield/manifest.js`). Add the
`.gitignore` rules above in the same commit so they don't reappear.

### 3. Renderers are unchanged

Skills keep calling `render-markdown.sh` and `write_shield_assets.py` exactly as
they do now. The only difference is the output lands in a gitignored location,
so it never enters a diff. **No renderer code changes.**

### 4. Build script + thin command trigger

Two pieces, clearly separated:

**A. The build script — `shield/scripts/render-output.sh`** (the orchestrator).
This is where all the conversion logic lives. Given an optional feature, it
regenerates the full HTML site from committed Markdown + `manifest.json`:

- No feature arg → rebuild the whole `docs/shield/` site (every feature's
  `outputs/*.html` + the root dashboard `index.html` and assets).
- With a feature arg → rebuild just that feature's `outputs/` + refresh the
  root dashboard/manifest assets.

It is a thin wrapper that drives the **existing** machinery — it loops the
relevant `.md` files through `render-markdown.sh` and then calls
`write_shield_assets.py`. It introduces **no new renderer**. Being a standalone
script, it is runnable and testable on its own (which the eval relies on).

**B. The command — `/shield render [feature]`** (skill). A thin trigger that
just invokes `render-output.sh [feature]` and reports where the built site is.
No conversion logic in the command itself.

This is the "build before you browse / share" entry point, run on demand.

### 5. Skill prose / path references

Audit the authoring skills (`research`, `prd-docs`, `plan-docs`, `lld-docs`,
`prd-review`, `plan-review`, `review`) and the `output-paths.yaml` registry for
any language that presents the `.html`/`outputs/` paths as *committed
deliverables*. Update them to describe HTML as a local build artifact and point
users at `/shield render` to view. Markdown paths remain the deliverables they
report.

## Out of scope (YAGNI)

- New export formats (PDF, Confluence). Markdown-as-source makes these easy
  later, but none are built now.
- Hosting/serving the dashboard. Local-open only.
- Changing the renderer, shell template, or dashboard behavior.
- Touching the JSON sidecar schemas.

## Risks / notes

- **Existing clones with committed HTML:** after this lands, `git rm --cached`
  leaves their working-tree HTML in place but now ignored; harmless. Fresh
  clones simply won't have HTML until they run `/shield render`.
- **"I opened a stale/missing HTML":** mitigated by the explicit `/shield
  render` step and by the fact that rendering is cheap and idempotent.

## Eval coverage (per CLAUDE.md — mandatory for plugin asset changes)

This touches plugin assets (new `/shield render` command + skill-prose edits),
so the PR must ship at least one executable eval. Candidate coverage:

- An eval that runs `render-output.sh` directly against a fixture feature with
  committed `.md` + `manifest.json` and asserts the expected `outputs/*.html`,
  root `index.html`, and assets are produced (and match a render of the
  Markdown). Testing the script directly avoids going through the command layer.
- A repo-hygiene check (eval or test) asserting no `*.html` / generated site
  assets are tracked under `docs/shield/` and that the `.gitignore` rules cover
  them.

## Definition of done

1. `.gitignore` updated; 41 `.html` + root site assets untracked.
2. `render-output.sh` build script added (wraps existing renderers); `/shield
   render` command added as a thin trigger.
3. Skill prose + `output-paths.yaml` updated to call HTML a build artifact.
4. Eval(s) above land in the same PR; RED→GREEN paper trail recorded.
5. Plugin version bumped in `.claude-plugin/marketplace.json` (and
   `pyproject.toml` if applicable).
