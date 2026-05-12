---
name: sprint-plan
description: Interactive sprint planning — assign stories to team members, set labels, and push to GitHub.
user_invocable: true
---

# /sprint-plan

Interactive sprint planning workflow.

## Steps

1. Call `sprint_status` grouped by epic to see the current state
2. Show overview: which epics have stories ready, in progress, done
3. Ask the user: **Which epic/stories to include in the next sprint?**
4. For selected stories, let the user:
   - Assign to team members (show team from config, use github_login)
   - Set labels (e.g. "in-progress", "high-priority")
   - Set iteration ID (for Projects v2 sprint assignment)
5. Apply changes via `sprint_bulk_update`
6. Show confirmation table with all changes applied

## Notes

- Always show current state before asking for changes
- Validate assignee logins against the team list in config
- Group changes by type (assignees, labels, state) in the confirmation
