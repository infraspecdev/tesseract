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
- `shield/plan.json` (old single-plan path) → needs rename to `shield/docs/plans/<name>.json`

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

4. **Create `~/.shield/config.json`** with defaults

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

**Generate sidecar JSON** for each phase and write to `shield/docs/plans/<phase-name>.json`:

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

### 3c. Copy HTML docs to shield/docs/

For each phase:
- Copy `phases/<phase>/architecture.html` → `shield/docs/architecture-<phase-name>.html`
- Copy `phases/<phase>/detailed-plan.html` → `shield/docs/plan-<phase-name>.html`

Update the `<meta name="sidecar">` tag in each plan HTML to point to the new sidecar path:
```html
<meta name="sidecar" content="./plans/<phase-name>.json">
```

### 3d. Copy review artifacts

For each review directory:
- Copy `review/<date>-<name>/analysis.md` → `shield/docs/analysis-<date>-<name>.md`
- Copy `review/<date>-<name>/plan.md` → `shield/docs/plan-enhanced-<date>-<name>.md`

### 3e. Migrate legacy shield/plan.json

If `shield/plan.json` exists (old single-plan path):
- Read the JSON, derive a name from the `project` or `phase` field
- Write to `shield/docs/plans/<name>.json`, adding the `name` field
- Delete `shield/plan.json`

## Phase 4: Summary

Present the full migration report:

```
Migration complete:

Config:
  ✓ .shield.json (project marker)
  ✓ ~/.shield/projects/<project>/pm.json (ClickUp config)
  ✓ ~/.shield/config.json (global defaults)

Plans (7 phases migrated):
  ✓ shield/docs/plans/vpc-architecture.json (P1 — 5 stories, 5 with ClickUp IDs)
  ✓ shield/docs/plans/ecs-vpc-migration.json (P1a — 8 stories, 8 with ClickUp IDs)
  ✓ shield/docs/plans/database-migration.json (P2 — 6 stories, 6 with ClickUp IDs)
  ✓ shield/docs/plans/eks-foundation.json (P3 — 11 stories, 11 with ClickUp IDs)
  ✓ shield/docs/plans/full-migration.json (P4 — 9 stories, 9 with ClickUp IDs)
  ✓ shield/docs/plans/multi-account.json (P5 — 7 stories, 7 with ClickUp IDs)
  ✓ shield/docs/plans/account-migration.json (P6 — 5 stories, 5 with ClickUp IDs)

HTML docs copied to shield/docs/:
  ✓ 14 architecture + plan HTML files
  ✓ Meta tags updated to reference sidecar JSON

Reviews:
  ✓ shield/docs/analysis-2026-03-12-eks-foundation.md
  ✓ shield/docs/plan-enhanced-2026-03-12-eks-foundation.md

Old files left in place (safe to delete after verifying):
  - sprint-planner.json
  - phases/
  - review/

Next steps:
  1. Verify plan sidecars: cat shield/docs/plans/eks-foundation.json | jq '.epics[0].stories | length'
  2. Run /pm-status to verify ClickUp connection
  3. Run /pm-sync to verify stories match ClickUp state
  4. Uninstall old plugins: infra-review, clickup-sprint-planner, dev-workflow
```

## Important

- Do NOT delete old files — leave them for user to verify
- Do NOT overwrite existing `~/.shield/` files — warn and ask
- Do NOT store API tokens in `.shield.json` or pm.json
- Validate migrated config against schemas in `${CLAUDE_PLUGIN_ROOT}/schemas/`
- Validate generated sidecar JSON against `${CLAUDE_PLUGIN_ROOT}/schemas/plan.schema.json`
- If HTML parsing fails for a story (missing selectors, unexpected structure), skip it and warn — do not fail the entire migration
- Preserve ClickUp IDs (`pm_id`, `pm_url`) from the HTML — these are critical for `/pm-sync` to match existing tasks
