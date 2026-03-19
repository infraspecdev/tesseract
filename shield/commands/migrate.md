---
name: migrate
description: Migrate from old plugins (infra-review, clickup-sprint-planner, dev-workflow) to Shield
---

# Shield Migrate

Detect and migrate configuration and plan artifacts from old Tesseract plugins to the Shield structure.

## Phase 1: Detect

Scan for old plugin artifacts:

- `sprint-planner.json` → ClickUp config (clickup-sprint-planner plugin)
- `phases/` directory with HTML plan docs → plan artifacts
- `review/` directory with analysis/plan markdown → review artifacts
- `claude/infra-review/` directory → infra-review was active
- `shield/plan.json` (old single-plan path) → needs migration to `{output_dir}/{feature}/plan.json`

Report findings:
```
Detected old plugin artifacts:
  - sprint-planner.json (ClickUp config with 7 epics)
  - phases/ (7 phase directories with architecture.html + detailed-plan.html)
  - review/ (1 review: 2026-03-12-eks-foundation)
```

If nothing detected, suggest `/shield init` instead.

## Phase 2: Migrate Config

1. **Gather project info:**
   - Ask for project name (default: repo directory name)
   - Infer domains from content (HTML plan docs with Terraform → `terraform`)
   - Ask user to confirm/adjust

2. **Create `.shield.json`** with confirmed project name and domains

3. **Migrate sprint-planner.json** (if found):

   | Old field | New location |
   |-----------|-------------|
   | `clickup.space.id` | `~/.shield/projects/<project>/pm.json` → `space_id` |
   | `clickup.folder.id` | `~/.shield/projects/<project>/pm.json` → `workspace_id` |
   | `clickup.lists.backlog.id` | `~/.shield/projects/<project>/pm.json` → used by pm-sync |
   | `clickup.relationship_field` | `~/.shield/projects/<project>/pm.json` → preserved |
   | `naming.*` | `~/.shield/projects/<project>/pm.json` → `naming.*` |
   | `CLICKUP_API_TOKEN` env var | `~/.shield/credentials.json` → `clickup.api_token` |

   - Set `adapter: "clickup"` and `adapter_mode: "hybrid"` in pm.json
   - **Register the PM adapter MCP server:**
     - Read `${CLAUDE_PLUGIN_ROOT}/adapters/clickup/.mcp.json` to get the server entries
     - Merge those entries into `${CLAUDE_PLUGIN_ROOT}/.mcp.json` → `mcpServers` object

## Phase 3: Migrate Plan Artifacts

This is the most important step — preserves all plan content by parsing HTML into Shield's sidecar JSON format.

### 3a. Detect plan structure

Read `sprint-planner.json` → `plan_docs.epics` array to discover phases:
```json
{ "id": "P1", "name": "VPC Architecture & IPAM", "plan_doc": "01-vpc-architecture/detailed-plan.html", "epic_id": "86d1zm4jf" }
```

Or if no `sprint-planner.json`, scan `phases/*/detailed-plan.html` for HTML plan docs.

### 3b. Parse each HTML plan into a named sidecar JSON

For each phase, parse the HTML `detailed-plan.html` using these selectors:

| Element | Selector | Maps to |
|---------|----------|---------|
| Story container | `div.story[id^="story-"]` | One story object |
| Story name | `.story-header h3` | `story.name` (strip "Story N: " prefix) |
| ClickUp ID | `a.badge-clickup` | `story.pm_id` + `story.pm_url` |
| Status badge | `.badge:not(.badge-clickup)` | `story.status` (map badge text to enum) |
| Description | `.story-description p` | `story.description` |
| Tasks | `ul.checklist li` | `story.tasks[]` |
| Acceptance criteria | `.acceptance ul li` | `story.acceptance_criteria[]` |
| Week/timeline | `.story-meta` | `story.week` |

**Status mapping** from old badge text to Shield enum:

| Old badge | Shield status |
|-----------|--------------|
| `ready for dev` / `ready` | `ready` |
| `in progress` / `in-progress` | `in-progress` |
| `in review` / `review` | `in-review` |
| `done` / `complete` | `done` |
| `blocked` | `blocked` |
| `to create` / `draft` / (no badge) | `draft` |

**Generate sidecar JSON** for each phase and write to `{output_dir}/{feature}/plan.json`:

```json
{
  "version": "1.0",
  "project": "<from .shield.json>",
  "name": "<phase-kebab-name>",
  "phase": "<phase display name>",
  "epics": [{
    "id": "<epic-id from sprint-planner or P1/P2/etc>",
    "name": "<epic name>",
    "stories": [
      {
        "id": "<epic-id>-S1",
        "name": "<parsed from h3>",
        "status": "<mapped status>",
        "description": "<parsed from .story-description>",
        "tasks": ["<parsed from ul.checklist>"],
        "acceptance_criteria": ["<parsed from .acceptance ul>"],
        "pm_id": "<clickup task id>",
        "pm_url": "https://app.clickup.com/t/<clickup-id>",
        "assignee": null,
        "priority": "normal",
        "week": "<parsed from .story-meta>"
      }
    ]
  }],
  "metadata": {
    "created_at": "<today>",
    "domains": ["<from .shield.json>"],
    "migrated_from": "<original HTML path>"
  }
}
```

### 3c. Copy HTML docs to feature folder

For each phase:
- Copy `phases/<phase>/architecture.html` → `{output_dir}/{feature}/plan/{N}-{slug}/architecture.html`
- Copy `phases/<phase>/detailed-plan.html` → `{output_dir}/{feature}/plan/{N}-{slug}/plan.html`

Update the `<meta name="sidecar">` tag in each plan HTML to point to the new sidecar path:
```html
<meta name="sidecar" content="../../plan.json">
```

Replace any old `nav.js` script references (e.g., `<script src="../nav.js">`) with the new path:
```html
<script src="nav.js"></script>
```

### 3d. Generate navigation

**`{output_dir}/index.html`** — a card-grid overview page linking to all feature folders and their artifacts. For each feature, show:
- Phase tag with color (P1=purple, P2=teal, P3=blue, P4=orange, P5=red, P6=brown)
- Phase name, timeline, description
- Links: Architecture, Detailed Plan, Sidecar JSON (`{feature}/plan.json`)
- Story count
- Deprioritised/rejected phases shown with reduced opacity and status labels

Also include sections for Reviews and Plan Sidecars at the bottom.

**`{output_dir}/manifest.json`** — registry of all feature folders and their metadata, used by nav and index generation.

### 3e. Copy review artifacts

For each review directory:
- Copy `review/<date>-<name>/analysis.md` → `{output_dir}/{feature}/plan-review/{N}-{slug}/summary.md`
- Copy `review/<date>-<name>/plan.md` → `{output_dir}/{feature}/plan-review/{N}-{slug}/enhanced-plan.md`

### 3f. Migrate legacy shield/plan.json

If `shield/plan.json` exists (old single-plan path):
- Read the JSON, derive a feature name from the `project` or `phase` field
- Write to `{output_dir}/{feature}/plan.json`, adding the `name` field
- Delete `shield/plan.json`

## Phase 4: Summary

Present the full migration report:

```
Migration complete:

Config:
  ✓ .shield.json (project config + reviewer settings)
  ✓ ~/.shield/projects/<project>/pm.json (ClickUp config)
  ✓ PM adapter MCP server registered

Plans (7 phases migrated):
  ✓ {output_dir}/vpc-architecture-YYYYMMDD/plan.json (P1 — 5 stories, 5 with ClickUp IDs)
  ✓ {output_dir}/ecs-vpc-migration-YYYYMMDD/plan.json (P1a — 8 stories, 8 with ClickUp IDs)
  ✓ {output_dir}/database-migration-YYYYMMDD/plan.json (P2 — 6 stories, 6 with ClickUp IDs)
  ✓ {output_dir}/eks-foundation-YYYYMMDD/plan.json (P3 — 11 stories, 11 with ClickUp IDs)
  ✓ {output_dir}/full-migration-YYYYMMDD/plan.json (P4 — 9 stories, 9 with ClickUp IDs)
  ✓ {output_dir}/multi-account-YYYYMMDD/plan.json (P5 — 7 stories, 7 with ClickUp IDs)
  ✓ {output_dir}/account-migration-YYYYMMDD/plan.json (P6 — 5 stories, 5 with ClickUp IDs)

HTML docs copied to feature folders:
  ✓ 14 architecture + plan HTML files under {output_dir}/{feature}/plan/{N}-{slug}/
  ✓ Meta tags updated to reference sidecar JSON
  ✓ {output_dir}/index.html — card-grid overview linking all artifacts
  ✓ {output_dir}/manifest.json — feature folder registry

Reviews:
  ✓ {output_dir}/{feature}/plan-review/{N}-{slug}/summary.md
  ✓ {output_dir}/{feature}/plan-review/{N}-{slug}/enhanced-plan.md

Old files left in place (safe to delete after verifying):
  - sprint-planner.json
  - phases/
  - review/

⚠ Reload the Shield plugin to start the PM adapter:
  /plugin update shield@tesseract

Next steps:
  1. Reload Shield plugin (see above)
  2. Verify plan sidecars: cat {output_dir}/eks-foundation-YYYYMMDD/plan.json | jq '.epics[0].stories | length'
  3. Run /pm-status to verify ClickUp connection
  4. Run /pm-sync to verify stories match ClickUp state
  5. Uninstall old plugins: infra-review, clickup-sprint-planner, dev-workflow
```

## Important

- Do NOT delete old files — leave them for user to verify
- Do NOT overwrite existing `~/.shield/` files — warn and ask
- Do NOT store API tokens in `.shield.json` or pm.json
- Validate migrated config against schemas in `${CLAUDE_PLUGIN_ROOT}/schemas/`
- Validate generated sidecar JSON against `${CLAUDE_PLUGIN_ROOT}/schemas/plan.schema.json`
- If HTML parsing fails for a story (missing selectors, unexpected structure), skip it and warn — do not fail the entire migration
- Preserve ClickUp IDs (`pm_id`, `pm_url`) from the HTML — these are critical for `/pm-sync` to match existing tasks
