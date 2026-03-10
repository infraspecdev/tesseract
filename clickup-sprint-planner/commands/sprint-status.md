---
name: sprint-status
description: Show sprint/epic status overview from ClickUp with story-level detail.
user_invocable: true
---

# /sprint-status [epic] [--by status|assignee]

Show sprint status from ClickUp.

## Steps

1. Call `sprint_status` with the requested grouping
2. Render summary table:

```
Epic   │ Total │ Done │ In Progress │ Ready │ Blocked
───────┼───────┼──────┼─────────────┼───────┼────────
P1     │ 12    │ 8    │ 2           │ 2     │ 0
P1a    │ 5     │ 0    │ 2           │ 3     │ 0
P2     │ 8     │ 0    │ 0           │ 8     │ 0
```

3. If a specific epic was requested, also show story-level detail:

```
# P1a: ECS VPC Migration (2/5 in progress)

│ Status       │ Story                                  │ Assignee       │
│ 🔵 in progress│ S1: Create new Launch Template         │ Alice          │
│ 🔵 in progress│ S2: Create new ALB                     │ Bob            │
│ ⚪ ready      │ S3: Migrate ECS services               │ —              │
```

## Arguments

- `epic` (optional): Epic ID like "P1a" for detailed view
- `--by status`: Group by status instead of epic
- `--by assignee`: Group by assignee instead of epic

## Examples

```
/sprint-status              # Overview of all epics
/sprint-status P1a          # Detailed view of epic P1a
/sprint-status --by assignee # Group all tasks by assignee
```
