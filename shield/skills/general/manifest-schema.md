# Manifest & Index Schema

> For the purpose of each Shield artifact and how they relate, see [`shield/docs/artifacts.md`](../../docs/artifacts.md).

All Shield skills MUST update `{manifest}` = `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html` (the `global_index_html` registry entry) after writing any output.

## manifest.json (v2.1)

Lives at `{output_dir}/manifest.json`. This is the source of truth for which features exist and which artifacts are present per feature. Built deterministically by `shield/scripts/migrate_outputs.py:build_manifest()`; any agent regeneration MUST produce the same shape.

```json
{
  "schema_version": "2.1",
  "features": [
    {
      "name": "vpc-module-20260319",
      "artifacts": {
        "research":     true,
        "prd":          true,
        "trd":          true,
        "plan_json":    true,
        "plan_md":      true,
        "plan_arch_md": true
      },
      "reviews": {
        "prd":  {
          "latest": "2026-03-19",
          "count": 1,
          "entries": [
            {"date": "2026-03-19", "path": "vpc-module-20260319/outputs/reviews/prd/2026-03-19/summary.html"}
          ]
        },
        "plan": {
          "latest": "2026-03-21_2",
          "count": 2,
          "entries": [
            {"date": "2026-03-21",   "path": "vpc-module-20260319/outputs/reviews/plan/2026-03-21/summary.html"},
            {"date": "2026-03-21_2", "path": "vpc-module-20260319/outputs/reviews/plan/2026-03-21_2/summary.html"}
          ]
        },
        "code": {
          "latest": "2026-03-22",
          "count": 1,
          "entries": [
            {"date": "2026-03-22", "path": "vpc-module-20260319/outputs/reviews/code/2026-03-22/summary.html"}
          ]
        }
      },
      "updated": "2026-03-22T14:30:00+00:00"
    }
  ]
}
```

### Field semantics

- **`schema_version`** — string `"2.1"` post-cutover. Tooling that sees `1`, `2`, or any unrecognized value should treat the manifest as legacy and rebuild via `migrate_outputs.py`.
- **`features[].name`** — the feature folder name (`{kebab-case-name}-YYYYMMDD`).
- **`features[].artifacts`** — booleans for each per-feature source file:
  - `research` → `{research}` = `{feature_dir}/research.md`
  - `prd` → `{prd}` = `{feature_dir}/prd.md`
  - `trd` → `{trd}` = `{feature_dir}/trd.md`
  - `plan_json` → `{plan_json}` = `{feature_dir}/plan.json`
  - `plan_md` → `{plan_md}` = `{feature_dir}/plan.md`
  - `plan_arch_md` → `{plan_arch_md}` = `{feature_dir}/plan-architecture.md`
  Each is `true` if the file exists, `false` if not. Rendered HTML siblings land under `{feature_dir}/outputs/` (build artifact — gitignored; rebuild locally with `/shield render`) and are implied by the source presence, not tracked separately.
- **`features[].reviews`** — one entry per review type (`prd`, `plan`, `code`). Each:
  - `latest`: the highest-sorted date-keyed run folder name (e.g. `2026-03-21_2`)
  - `count`: number of run folders under `{feature_dir}/reviews/<type>/`
  - `entries`: list of `{date, path}` dicts, one per run folder, where `path` is the rendered summary at `{feature}/outputs/reviews/{type}/{date}/summary.html`. Entries are sorted ascending by `date`.
  - If no runs exist, the entry is `{ "count": 0, "entries": [] }` (no `latest` key).
- **`features[].updated`** — ISO 8601 UTC timestamp of the last manifest rebuild.

### Page assets

Every Shield page (dashboard, rendered PRD/TRD/Plan/Plan-Architecture, review summaries, detailed-agent reports) is rendered into the shared HTML shell at `shield/templates/shell.html`. The shell provides a single nav, a single stylesheet link, and a single body container; per-page content is substituted into `{{TITLE}}`, `{{META}}`, and `{{BODY}}` by `shield/scripts/render-markdown.py`.

`shield/scripts/write_shield_assets.py` writes the runtime bundle into `{output_dir}/`:

- `manifest.js` — a JS-loadable mirror of `manifest.json`, assigned to `window.SHIELD_MANIFEST`. This avoids `fetch()` and works under `file://`.
- `shield.css` — single stylesheet for all pages.
- `shield-nav.js` — builds the nested Docs menu client-side from `window.SHIELD_MANIFEST`.
- `shield-dashboard.js` — renders the dashboard grid client-side from `window.SHIELD_MANIFEST`.
- `index.html` — the dashboard shell (loads `manifest.js` + `shield-dashboard.js`).

Nav and dashboard are entirely client-side — there are no fetch calls, so the docs tree opens cleanly from `file://`.

Numbered-run subfolders (`plan/{N}-{slug}/`, `plan-review/{N}-{slug}/`, etc.) are gone. Per-run history for source artifacts is in git, not the manifest. Per-run history for reviews is the file-system listing under `reviews/<type>/`.

## How Skills Update manifest.json

Every skill that writes output MUST follow this sequence:

1. Write the artifact(s) to their registry-declared paths
2. Run the deterministic builder: `uv run --with pyyaml shield/scripts/migrate_outputs.py --root {output_dir}` (or equivalent in-process) to produce the v2 manifest from the file system
3. Write the updated `{manifest}`
4. Regenerate `{output_dir}/index.html` per the section below

The builder is the source of truth — agents SHOULD prefer running it over hand-constructing entries.

## index.html

Lives at `{output_dir}/index.html` (registry entry `global_index_html`). Reads `manifest.json` to render a dashboard.

### Content

- All features sorted by date (newest first, derived from the trailing `-YYYYMMDD` in `name`)
- Per feature card:
  - Feature name + date
  - Artifact links (only show links for `artifacts.<key> == true`):
    - Research → `{feature}/research.md`
    - PRD → `{feature}/prd.md` and `{feature}/outputs/prd.html`
    - Plan → `{feature}/plan.md`, `{feature}/plan-architecture.md`, and `{feature}/outputs/plan.html` + `{feature}/outputs/plan-architecture.html`
  - Review counts per type with link to the latest date-keyed folder:
    - PRD review → `{feature}/reviews/prd/{latest}/summary.md` (when `reviews.prd.count > 0`)
    - Plan review → `{feature}/reviews/plan/{latest}/summary.md`
    - Code review → `{feature}/reviews/code/{latest}/summary.md`
- Embedded `manifest.json` reference via `<script>`:
  ```html
  <script>
    fetch('manifest.json').then(r => r.json()).then(manifest => { /* render */ });
  </script>
  ```

### Navigation Header

All generated HTML files (rendered prd.html, plan.html, plan-architecture.html, review summaries) MUST include this nav header. The relative-path depth depends on where the file lives:

```html
<nav class="shield-nav" style="background:#f8f9fa;padding:8px 16px;border-bottom:1px solid #dee2e6;font-family:system-ui;font-size:14px;">
  <a href="{relative-path-to-index}">← All Features</a> |
  <strong>{feature-name}</strong> |
  <a href="{relative-path-to-prd}">PRD</a> ·
  <a href="{relative-path-to-plan}">Plan</a> ·
  <a href="{relative-path-to-reviews}">Reviews</a>
</nav>
```

Relative-path depth table (post-cutover flat layout):

| Rendered file | Path to index.html |
|---|---|
| `{feature}/outputs/prd.html` | `../../index.html` |
| `{feature}/outputs/plan.html` | `../../index.html` |
| `{feature}/outputs/plan-architecture.html` | `../../index.html` |
| `{feature}/outputs/reviews/{type}/{date}/summary.html` | `../../../../../index.html` |
| `{feature}/outputs/reviews/{type}/{date}/detailed/<agent>.html` | `../../../../../../index.html` |

### Sidecar references in plan.html

The detailed plan HTML (`{plan_html}`) MUST include a meta tag referencing the sidecar at its post-cutover location:

```html
<meta name="sidecar" content="../plan.json">
```

(`../plan.json` because `plan.html` lives in `{feature}/outputs/` and `plan.json` is at `{feature}/plan.json`.)

### Regeneration

`index.html` is regenerated every time `manifest.json` is updated. The HTML is self-contained — no external CSS/JS dependencies beyond what's inlined.
