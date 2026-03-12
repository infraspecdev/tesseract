---
name: sprint-sync
description: Sync plan documents against ClickUp state, showing diffs and optionally creating/updating tasks.
user_invocable: true
---

# /sprint-sync [epic]

Sync plan documents against ClickUp, then optionally apply changes.

**IMPORTANT:** Never use raw ClickUp MCP tools (`clickup_create_task`, `clickup_update_task`, etc.) for sprint operations. Always use the `sprint_*` tools which handle action logging, naming conventions, and relationship linking automatically.

## Steps

1. Load `sprint-planner.json` config
2. Call `sprint_sync` for the specified epic (or all epics if none given)
3. Present the diff as a table:

```
┌──────────┬─────────────────────────────────────────┬──────────┐
│ Status   │ Story                                   │ Action   │
├──────────┼─────────────────────────────────────────┼──────────┤
│ ✅ match  │ S1: Create new ECS infrastructure       │ none     │
│ ⚠️ diff   │ S3: Create new ALB — name diverged      │ update   │
│ 🔗 link   │ S4: Set up monitoring — unlinked task   │ link     │
│ 🆕 new    │ S6: Configure CloudWatch alarms         │ create   │
└──────────┴─────────────────────────────────────────┴──────────┘
```

4. Ask the user: **apply all** / **pick which** / **cancel**
5. For "to_create" stories: call `sprint_bulk_create` with `set_relationships: true`
6. For "to_update" stories: call `sprint_bulk_update` with the relevant changes
7. For "to_link" stories (unlinked tasks matched by fuzzy name):
   - Show candidates with match confidence
   - If user approves: call `sprint_sync(apply_links=true)` to auto-set relationship fields
8. Show results + any failures
9. Offer to write ClickUp IDs back into the plan document

## Arguments

- `epic` (optional): Epic ID like "P1a", "P2", "P3". Omit for all epics.

## Examples

```
/sprint-sync P1a       # Sync epic P1a only
/sprint-sync            # Sync all epics
```
