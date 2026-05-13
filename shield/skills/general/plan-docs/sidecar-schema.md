# Plan Sidecar JSON Schema

```jsonc
{
  "version": "1.1",
  "project": "<project name from .shield.json>",
  "name": "<kebab-case-plan-name>",
  "phase": "<phase name>",
  "milestones": [
    {
      "id": "M1",
      "name": "<short user-language name>",
      "outcome": "<what ships, in user language>",
      "exit_criteria": [
        "<testable fact 1>",
        "<testable fact 2>"
      ],
      "depends_on": []
    }
  ],
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
          "milestone_id": "M1",
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

- `version` is now `"1.1"` (was `"1.0"` pre-milestones). Older sidecars (`"1.0"` or missing `version`) are treated as back-compat — see below.
- Every epic MUST have at least 1 story.
- Every story MUST have at least 1 acceptance criterion.
- Acceptance criteria must be testable — not "it works" but "VPC has DNS support enabled".
- Tasks must be specific enough to execute without questions.
- Status starts as `"ready"` for new stories.
- `pm_id` and `pm_url` start as `null` — populated by `/pm-sync`.
- Plan name must be kebab-case (`^[a-z0-9-]+$`).
- Each plan lives at `{output_dir}/{feature}/plan.json`.
- Story IDs must be unique across all plans in a project.

### Milestones

- `milestones[]` is the roadmap. Each milestone has `id` (`M1`, `M2`, …), `name`, `outcome`, `exit_criteria` (≥1 testable item), and `depends_on` (array of milestone IDs; empty = no prerequisites).
- Every milestone in `milestones[]` MUST have at least one covering story (any story whose `milestone_id` equals this milestone's `id`).
- Exit criteria follow the same testable standard as story acceptance criteria.
- `depends_on` forms a DAG — cycles are rejected by `plan-review`.

### Story → Milestone linkage

- Each story has a `milestone_id` field. It is either a valid `id` from `milestones[]` or `null`.
- `null` is permitted only when `milestones[]` is empty (back-compat case below) OR when the story is intentionally scoped outside any milestone.

### Back-compat (single implicit milestone)

A sidecar with `milestones: []` and every story's `milestone_id: null` is treated as a **single implicit milestone covering all stories**. `plan-review` does not flag this — it is the back-compat path for plans authored before this schema version or for explicit user opt-out.
