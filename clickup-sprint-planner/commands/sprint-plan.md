---
name: sprint-plan
description: Interactive sprint planning — assign stories to team members, set priorities, and push to ClickUp.
user_invocable: true
---

# /sprint-plan

Interactive sprint planning workflow.

## Steps

1. Call `sprint_status` grouped by epic to see the current state
2. Show overview: which epics have stories ready, in progress, done
3. Ask the user: **Which epic/stories to include in the next sprint?**
4. For selected stories, let the user:
   - Assign to team members (show team from config)
   - Set priorities (urgent / high / normal / low)
   - Set status (e.g. "ready for dev")
5. Apply changes via `sprint_bulk_update`
6. Show confirmation table with all changes applied

## Notes

- Always show current state before asking for changes
- Validate assignee IDs against the team list in config
- Group changes by type (status, assignee, priority) in the confirmation
