# Plan Sidecar JSON Schema

```json
{
  "version": "1.0",
  "project": "<project name from .shield.json>",
  "name": "<kebab-case-plan-name>",
  "phase": "<phase name>",
  "epics": [
    {
      "id": "EPIC-1",
      "name": "<epic name>",
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "<story name>",
          "status": "ready",
          "assignee": null,
          "priority": "high",
          "week": null,
          "description": "<2-3 sentences describing what needs to happen>",
          "tasks": [
            "Concrete action 1",
            "Concrete action 2"
          ],
          "acceptance_criteria": [
            "Verifiable outcome 1 (testable, not vague)",
            "Verifiable outcome 2"
          ],
          "pm_id": null,
          "pm_url": null
        }
      ]
    }
  ],
  "metadata": {
    "created_at": "<YYYY-MM-DD>",
    "domains": ["<from .shield.json>"],
    "reviewer_grades": {}
  }
}
```

## Rules

- Every epic MUST have at least 1 story
- Every story MUST have at least 1 acceptance criterion
- Acceptance criteria must be testable — not "it works" but "VPC has DNS support enabled"
- Tasks must be specific enough to execute without questions
- Status starts as `"ready"` for new stories
- `pm_id` and `pm_url` start as `null` — populated by `/pm-sync`
- Plan name must be kebab-case (`^[a-z0-9-]+$`)
- Each plan lives at `shield/docs/plans/<name>.json`
- Story IDs must be unique across all plans in a project
