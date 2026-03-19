# Manifest & Index Schema

All Shield skills MUST update `manifest.json` and regenerate `index.html` after writing any output.

## manifest.json

Lives at `{output_dir}/manifest.json`. This is the source of truth for which features exist and where their latest artifacts are.

```json
{
  "version": "1.0",
  "output_dir": "docs/shield",
  "features": {
    "vpc-module-20260319": {
      "name": "vpc-module",
      "created": "2026-03-19",
      "status": "active",
      "plan_json": "vpc-module-20260319/plan.json",
      "latest": {
        "research": "vpc-module-20260319/research/2-regulatory-requirements/",
        "plan": "vpc-module-20260319/plan/1-vpc-module/",
        "plan_review": "vpc-module-20260319/plan-review/1-vpc-module-review/",
        "code_review": "vpc-module-20260319/code-review/2-epic1-s2-vpc-core/",
        "summary": null
      },
      "runs": {
        "research": [
          {"run": 1, "slug": "aws-ipam-patterns", "path": "vpc-module-20260319/research/1-aws-ipam-patterns/"},
          {"run": 2, "slug": "regulatory-requirements", "path": "vpc-module-20260319/research/2-regulatory-requirements/"}
        ],
        "plan": [
          {"run": 1, "slug": "vpc-module", "path": "vpc-module-20260319/plan/1-vpc-module/"}
        ],
        "plan_review": [
          {"run": 1, "slug": "vpc-module-review", "path": "vpc-module-20260319/plan-review/1-vpc-module-review/"}
        ],
        "code_review": [
          {"run": 1, "slug": "epic1-s1-ipam-pools", "path": "vpc-module-20260319/code-review/1-epic1-s1-ipam-pools/"},
          {"run": 2, "slug": "epic1-s2-vpc-core", "path": "vpc-module-20260319/code-review/2-epic1-s2-vpc-core/"}
        ],
        "summary": []
      }
    }
  }
}
```

## Schema Rules

- `latest` always points to the highest-numbered run for each phase
- `latest` value is `null` if no runs exist for that phase
- `runs` is the complete history per phase, ordered by run number
- `status` is `"active"` or `"completed"`
- Feature key format: `{kebab-case-name}-YYYYMMDD`
- Run number = count existing entries in `runs[phase]` + 1
- All paths are relative to `{output_dir}/`

## Slug Derivation

| Phase | Slug source |
|-------|------------|
| Research | Topic argument from `/research` command |
| Plan | Plan name (user confirms during `/plan`) |
| Plan Review | Name of the plan being reviewed (from `plan.json`) + `-review` |
| Code Review | Story ID if available, else branch name |
| Summary | Plan name + `-complete` |

**Slug rules:**
- Lowercase, hyphens only (no spaces, underscores, special chars)
- Truncate at 50 characters
- If no slug source available, use just the run number (e.g., folder name is `1/` not `1-/`)

## How Skills Update manifest.json

Every skill that writes output MUST follow this sequence:

1. Read `{output_dir}/manifest.json` (create empty manifest if not exists: `{"version": "1.0", "output_dir": "<from .shield.json>", "features": {}}`)
2. Find or create the feature entry
3. Add the new run to `runs[phase]`
4. Update `latest[phase]` to point to the new run
5. Write updated `manifest.json`
6. Regenerate `index.html`

## index.html

Lives at `{output_dir}/index.html`. Reads `manifest.json` to render a dashboard.

### Content

- All features sorted by date (newest first)
- Per feature card:
  - Feature name, date, status badge
  - **Latest** links (highlighted): research, plan, plan review, code review, summary
  - Story progress from `plan.json` (if exists)
  - Expandable run history per phase
- Embedded `manifest.json` reference via `<script>`:
  ```html
  <script>
    fetch('manifest.json').then(r => r.json()).then(manifest => { /* render */ });
  </script>
  ```

### Navigation Header

All generated HTML files (architecture.html, plan.html, review summaries) MUST include this nav header:

```html
<nav class="shield-nav" style="background:#f8f9fa;padding:8px 16px;border-bottom:1px solid #dee2e6;font-family:system-ui;font-size:14px;">
  <a href="{relative-path-to-index}">← All Features</a> |
  <strong>{feature-name}</strong> |
  <a href="{relative-path-to-research}">Research</a> ·
  <a href="{relative-path-to-plan}">Plan</a> ·
  <a href="{relative-path-to-reviews}">Reviews</a>
</nav>
```

Where `{relative-path-to-index}` is the relative path from the current file back to `{output_dir}/index.html` (e.g., `../../index.html` from a plan subfolder).

### Regeneration

`index.html` is regenerated every time `manifest.json` is updated. The HTML is self-contained — no external CSS/JS dependencies.
