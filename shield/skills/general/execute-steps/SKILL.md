---
name: execute-steps
description: Optional orchestrator for running multiple Shield phases in sequence. Not required — each skill works standalone by writing directly to shield/.
---

# Execute Steps

**Optional** multi-phase orchestrator. Individual Shield skills work standalone — they write directly to `shield/` using the Write tool (which creates directories automatically). This skill is only needed when running multiple phases in sequence and you want step tracking and resume support.

## When to Use

- Running a full pipeline (research → plan → review → implement → review)
- Resuming a multi-phase run that was interrupted
- When the user explicitly asks for orchestrated execution

## When NOT to Use

- Running a single skill (research, plan-docs, review, etc.) — just invoke it directly
- Skills no longer require this as a prerequisite

## Artifact Paths

All artifacts go to `shield/` with timestamps in filenames:

| Phase | Output |
|-------|--------|
| Research | `shield/docs/research-YYYYMMDD-HHMMSS.md` |
| Planning | `shield/docs/plans/<name>.json` + `shield/docs/architecture-YYYYMMDD-HHMMSS.html` + `shield/docs/plan-YYYYMMDD-HHMMSS.html` |
| Plan Review | `shield/docs/reviews-YYYYMMDD-HHMMSS/summary/plan-review-summary.md` |
| Implementation | Updates `shield/docs/plans/<name>.json` status |
| Code Review | `shield/docs/reviews-YYYYMMDD-HHMMSS/summary/code-review-summary.md` |
| Summarize | `shield/docs/<phase>-summary-YYYYMMDD-HHMMSS.md` |

## Step Tracking (optional)

If tracking is desired, write state to `~/.shield/shield/<project>/steps.json`:

```json
{
  "phase": "<phase name>",
  "started_at": "<ISO timestamp>",
  "artifact_dir": "shield/",
  "steps": [
    {"id": 1, "action": "<description>", "output": "<expected file path>", "status": "pending"},
    {"id": 2, "action": "<description>", "output": "<expected file path>", "status": "pending"}
  ]
}
```

After each step completes, update its status to `"complete"`. If a step fails, set status to `"failed"` and stop.

## Resume

If `steps.json` exists with incomplete steps, resume from the last incomplete step instead of starting over.
