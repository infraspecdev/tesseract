---
name: sprint-planning
description: Use when the user asks about sprint planning, syncing plan docs to GitHub, managing issues in bulk, or checking sprint status. Triggers on mentions of sprint, sync, stories, GitHub Issues, bulk operations, or epic planning.
---

# Sprint Planning Skill (GitHub)

## Overview

Orchestrate GitHub sprint operations through the github-sprint-planner MCP server — sync plan documents, create story issues in bulk, and track sprint progress.

**Core principle:** Always sync before mutating. Show the user the diff, get confirmation, then execute.

## When to Use

- Syncing plan docs to GitHub Issues (creating/updating stories)
- Bulk operations on GitHub Issues (create, update, assign)
- Sprint status checks and epic progress tracking
- Linking issues as sub-issues of epics

## When NOT to Use

- Individual issue updates — use GitHub UI directly
- Creating plan documents — use `dev-workflow:plan-docs` skill
- ClickUp-based project management — use `clickup-sprint-planner`

## Available Tools

| Tool | Purpose |
|------|---------|
| `sprint_sync` | Diff plan docs against GitHub Issues (read-only) |
| `sprint_bulk_create` | Create multiple issues + link as sub-issues + add to project |
| `sprint_bulk_update` | Batch update assignees/labels/state |
| `sprint_bulk_rename` | Preview or apply epic prefix renames on issue titles |
| `sprint_status` | Get epic overview with stats |
| `sprint_action_log` | Query past operations |

## Rules

1. **Sync before mutating.** Always call `sprint_sync` first. Present the diff and get confirmation.
2. **Use bulk operations.** Never create issues one-by-one. Use `sprint_bulk_create`.
3. **Read config, don't hardcode.** All IDs come from `sprint-planner.json`. Never hardcode issue numbers or project IDs.
4. **Confirm before mutating.** Show the user exactly what will happen and ask for confirmation.
5. **Surface errors clearly.** Show which operations succeeded vs failed.
6. **Present results as tables.** After any operation, show issue numbers, titles, URLs, and any failures.
7. **Never use raw GitHub tools for sprint write operations.** Do not call `create_issue`, `update_issue`, or any native GitHub MCP tools directly — always go through `sprint_bulk_create`, `sprint_bulk_update`, or `sprint_bulk_rename` so actions are logged and reversible.

## Workflows

### Creating Stories

```
1. sprint_sync(epic="P1a")            → see what exists vs plan doc
2. Present diff table to user         → match / to_create / to_update / to_link
3. User confirms which to create
4. sprint_bulk_create(epic_issue_number=42, stories=[...], add_to_project=true)
   - Titles auto-formatted as "{epic_id} - {name}" (e.g. "P1a - Create VPC")
   - Include full issue body with all required sections
5. Show results table                 → created issues with numbers and URLs
6. If sprint_sync flagged "to_link" items:
   sprint_sync(apply_links=true)      → auto-add as sub-issues + log action
```

### Updating Stories

```
1. sprint_sync(epic="P1")             → identify stale stories
2. Present diff to user
3. User confirms which to update
4. sprint_bulk_update(updates=[{"issue_number": 99, "title": "...", "body": "..."}])
5. Show results table
```

### Sprint Status Check

```
1. sprint_status(group_by="epic"|"status"|"assignee")
2. Present summary table
3. User drills into specific epic for story-level detail
```

## Card Format

Issue title: `{EpicID} - {StoryName}` (e.g. `P1a - Create new ECS infrastructure`)

Every issue body MUST include: Summary, Tasks checklist, Context/Notes, Acceptance Criteria. See `card-format.md` for full requirements.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Creating issues one-by-one | Use `sprint_bulk_create` for all stories in one call |
| Not syncing before creating | Always `sprint_sync` first — avoids duplicating existing issues |
| One-line issue bodies | Include all 4 required sections (see `card-format.md`) |
| Hardcoding issue numbers | Read `epic_issue_number` from `sprint-planner.json` config |
| Using wrong assignee format | Use `github_login` (e.g. "alice"), not display name |
