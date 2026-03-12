---
name: sprint-planning
description: Use when the user asks about sprint planning, syncing plan docs to ClickUp, managing stories/tasks in bulk, or checking sprint status. Triggers on mentions of sprint, sync, stories, ClickUp bulk operations, or epic planning.
---

# Sprint Planning Skill

## Overview

Orchestrate ClickUp sprint operations through the sprint-planner MCP server — sync plan documents, create story cards in bulk, and track sprint progress.

**Core principle:** Always sync before mutating. Show the user the diff, get confirmation, then execute.

## When to Use

- Syncing plan docs to ClickUp (creating/updating stories)
- Bulk operations on ClickUp tasks (create, update, reorder)
- Sprint status checks and epic progress tracking
- Setting EPIC relationship fields on tasks

## When NOT to Use

- Individual task updates — use ClickUp UI directly
- Creating plan documents — use `dev-workflow:plan-docs` skill
- Non-ClickUp project management

## Available Tools

| Tool | Purpose |
|------|---------|
| `sprint_sync` | Diff plan docs against ClickUp state (read-only) |
| `sprint_bulk_create` | Create multiple tasks + set EPIC relationships |
| `sprint_set_relationship` | Set list_relationship custom fields directly |
| `sprint_bulk_update` | Batch update status/assignee/priority |
| `sprint_status` | Get epic overview with stats |
| `sprint_action_log` | Query past operations |

## Rules

1. **Sync before mutating.** Always call `sprint_sync` first. Present the diff and get confirmation.
2. **Use bulk operations.** Never create tasks one-by-one. Use `sprint_bulk_create` with `set_relationships: true`.
3. **Read config, don't hardcode.** All IDs come from `sprint-planner.json` (path via `SPRINT_PLANNER_CONFIG` env var). Never hardcode ClickUp IDs.
4. **Confirm before mutating.** Show the user exactly what will happen and ask for confirmation.
5. **Surface errors clearly.** Our tools use the direct REST endpoint — if they report failure, it's real. Show which operations succeeded vs failed.
6. **Present results as tables.** After any operation, show task names, IDs, statuses, and any failures.

## Workflows

### Creating Stories

```
1. sprint_sync(epic="P1a")            → see what exists vs plan doc
2. Present diff table to user         → match / to_create / to_update
3. User confirms which to create
4. sprint_bulk_create(list_id=config.lists.backlog.id, stories=[...], set_relationships=true)
5. Show results table                 → created tasks with IDs and URLs
```

### Updating Stories

```
1. sprint_sync(epic="P1")             → identify stale stories
2. Present diff to user
3. User confirms which to update
4. sprint_bulk_update(updates=[{ "task_id": "...", "description": "...", "orderindex": "1000" }])
5. Show results table                 → success/failure per task
```

The `description` field accepts full markdown — include all required card sections. See `card-format.md` for card content requirements, examples, and ordering rules.

### Sprint Status Check

```
1. sprint_status(group_by="epic"|"status"|"assignee")
2. Present summary table
3. User drills into specific epic for story-level detail
```

## Card Format

Task naming: `[Project Name] {EpicID}-S{StoryIndex}: {StoryName}`

Every card MUST include: Summary, Tasks checklist, Context/Notes, Acceptance Criteria. See `card-format.md` for full requirements, example card, ordering rules, and custom field reference.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Creating tasks one-by-one | Use `sprint_bulk_create` for all stories in one call |
| Not syncing before creating | Always `sprint_sync` first — avoids duplicating existing tasks |
| One-line card descriptions | Include all 4 required sections (see `card-format.md`) |
| Hardcoding ClickUp IDs | Read from `sprint-planner.json` config |
| Setting orderindex without gaps | Use `sequence * 1000` to leave room for inserts |
