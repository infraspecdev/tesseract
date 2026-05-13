---
name: sprint-sync
description: Sync plan documents against GitHub Issues state, showing diffs and optionally creating/linking issues.
user_invocable: true
---

# /sprint-sync [epic]

Sync plan documents against GitHub Issues, then optionally apply changes.

**IMPORTANT:** Never use raw GitHub tools for sprint write operations. Always use the `sprint_*` tools which handle action logging, naming conventions, and sub-issue linking automatically.

## Steps

1. Load `sprint-planner.json` config
2. Call `sprint_sync` for the specified epic (or all epics if none given)
3. Present the diff as a table:

```
┌──────────┬─────────────────────────────────────────┬──────────┐
│ Status   │ Story                                   │ Action   │
├──────────┼─────────────────────────────────────────┼──────────┤
│ ✅ match  │ S1: Create new ECS infrastructure       │ none     │
│ ⚠️ diff   │ S3: Create new ALB — title diverged     │ update   │
│ 🔗 link   │ S4: Set up monitoring — unlinked issue  │ link     │
│ 🆕 new    │ S6: Configure CloudWatch alarms         │ create   │
└──────────┴─────────────────────────────────────────┴──────────┘
```

4. Ask the user: **apply all** / **pick which** / **cancel**
5. For "to_create" stories: call `sprint_bulk_create` with the epic issue number
6. For "to_update" stories: call `sprint_bulk_update` with the relevant changes
7. For "to_link" stories (unlinked issues matched by fuzzy name):
   - Show candidates with match confidence
   - If user approves: call `sprint_sync(apply_links=true)` to auto-add as sub-issues
8. Show results + any failures

## Arguments

- `epic` (optional): Epic ID like "P1a", "P2". Omit for all epics.

## Examples

```
/sprint-sync P1a       # Sync epic P1a only
/sprint-sync            # Sync all epics
```
