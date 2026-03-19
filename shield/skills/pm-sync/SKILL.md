---
name: pm-sync
description: Use when the user asks about sprint planning, syncing plan docs to a PM tool, managing stories/tasks in bulk, or checking sprint status. Triggers on mentions of sprint, sync, stories, PM bulk operations, or epic planning.
---

# PM Sync Skill

> **This skill uses abstract PM operations.** The actual PM adapter (ClickUp, Jira, etc.) is configured in `~/.shield/projects/<project>/pm.json`.

> **Before calling any `pm_*` tool**, call `pm_get_capabilities` to check which operations the adapter supports. Skip unsupported operations gracefully.

## Overview

Orchestrate project management operations through abstract PM adapters — sync plan documents, create story cards in bulk, and track sprint progress.

**Core principle:** Always sync before mutating. Show the user the diff, get confirmation, then execute.

## When to Use

- Syncing plan docs to PM tool (creating/updating stories)
- Bulk operations on PM tasks (create, update, reorder)
- Sprint status checks and epic progress tracking
- Setting EPIC relationship fields on tasks

## When NOT to Use

- Individual task updates — use PM tool UI directly
- Creating plan documents — use the `plan-review` skill
- Non-sprint project management

## Available Tools

| Tool | Purpose |
|------|---------|
| `pm_get_capabilities` | Check which operations the configured adapter supports |
| `pm_sync` | Diff plan sidecar JSON against PM tool state (read-only) |
| `pm_bulk_create` | Create multiple tasks + set EPIC relationships |
| `pm_link_story_to_epic` | Set list_relationship custom fields directly |
| `pm_bulk_update` | Batch update status/assignee/priority |
| `pm_get_status` | Get epic overview with stats |
| `pm_action_log` | Query past operations |

## Rules

1. **Check capabilities first.** Always call `pm_get_capabilities` before any other `pm_*` call. If an operation is unsupported, inform the user and skip it.
2. **Sync before mutating.** Always call `pm_sync` first. Present the diff and get confirmation.
3. **Use bulk operations.** Never create tasks one-by-one. Use `pm_bulk_create` with `set_relationships: true`.
4. **Read config, don't hardcode.** All IDs come from `~/.shield/projects/<project>/pm.json`. Never hardcode PM tool IDs.
5. **Always locate and read plan sidecar JSONs first.** Read `output_dir` from `.shield.json` (default `docs/shield`), then run `Glob("{output_dir}/*/plan.json")` to find all sidecars. Read the relevant sidecar for story data — not raw HTML or plan docs. If multiple plans exist and no name specified, list them and ask. Never claim sidecars don't exist without searching first.
6. **Confirm before mutating.** Show the user exactly what will happen and ask for confirmation.
7. **Surface errors clearly.** If tools report failure, it's real. Show which operations succeeded vs failed.
8. **Present results as tables.** After any operation, show task names, IDs, statuses, and any failures.
9. **Never use raw PM tool APIs for sprint write operations.** Always use `pm_bulk_create` / `pm_bulk_update` / `pm_link_story_to_epic` — raw API calls bypass the action log and skip naming/relationship logic.

## Workflows

### Creating Stories

```
1. pm_get_capabilities()              → verify adapter supports bulk_create, sync
2. pm_sync(plan="<name>", epic="P1a") → see what exists vs named plan sidecar JSON
3. Present diff table to user         → match / to_create / to_update / to_link
4. User confirms which to create
5. pm_bulk_create(list_id=config.lists.backlog.id, stories=[...], set_relationships=true)
   - Names auto-formatted as "{epic_id} - {name}" (e.g. "P3 - Install Istio")
   - Include orderindex with sequence * 1000 gaps
   - Include full card descriptions with all required sections
6. Show results table                 → created tasks with IDs and URLs
7. If pm_sync flagged "to_link" items:
   pm_sync(apply_links=true)          → auto-set relationship fields + log action
```

### Updating Stories

```
1. pm_sync(epic="P1")                → identify stale stories
2. Present diff to user
3. User confirms which to update
4. pm_bulk_update(updates=[{ "task_id": "...", "description": "...", "orderindex": "1000" }])
5. Show results table                 → success/failure per task
```

The `description` field accepts full markdown — include all required card sections. See `card-format.md` for card content requirements, examples, and ordering rules.

### Sprint Status Check

```
1. pm_get_status(group_by="epic"|"status"|"assignee")
2. Present summary table
3. User drills into specific epic for story-level detail
```

## Card Format

Task naming: `[Project Name] {EpicID}-S{StoryIndex}: {StoryName}`

Every card MUST include: Summary, Tasks checklist, Context/Notes, Acceptance Criteria. See `card-format.md` for full requirements, example card, ordering rules, and custom field reference.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Creating tasks one-by-one | Use `pm_bulk_create` for all stories in one call |
| Not syncing before creating | Always `pm_sync` first — avoids duplicating existing tasks |
| One-line card descriptions | Include all 4 required sections (see `card-format.md`) |
| Hardcoding PM tool IDs | Read from `~/.shield/projects/<project>/pm.json` config |
| Setting orderindex without gaps | Use `sequence * 1000` to leave room for inserts |
| Using raw PM tool APIs for sprint ops | Always use `pm_bulk_create` / `pm_bulk_update` / `pm_link_story_to_epic` — raw APIs bypass the action log and skip naming/relationship logic |
| Skipping capability check | Always call `pm_get_capabilities` first — adapters may not support all operations |
