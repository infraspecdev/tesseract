---
name: execute-steps
description: Optional orchestrator for running multiple Shield phases in sequence. Not required — each skill works standalone by writing directly to {output_dir}/.
---

# Execute Steps

**Optional** multi-phase orchestrator. Individual Shield skills work standalone — they write directly to `{output_dir}/` (from `.shield.json` `output_dir` field, default `docs/shield`) using the Write tool (which creates directories automatically). This skill is only needed when running multiple phases in sequence and you want step tracking and resume support.

## When to Use

- Running a full pipeline (research → plan → review → implement → review)
- Resuming a multi-phase run that was interrupted
- When the user explicitly asks for orchestrated execution

## When NOT to Use

- Running a single skill (research, plan-docs, review, etc.) — just invoke it directly
- Skills no longer require this as a prerequisite

## Artifact Paths

All artifacts go to `{output_dir}/{feature}/` where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`) and `{feature}` is the feature folder name (`{feature-name}-YYYYMMDD`):

| Phase | Output |
|-------|--------|
| Research | `{output_dir}/{feature}/research/{N}-{slug}/findings.md` |
| Planning | `{output_dir}/{feature}/plan.json` + `{output_dir}/{feature}/plan/{N}-{slug}/architecture.html` + `plan.html` |
| Plan Review | `{output_dir}/{feature}/plan-review/{N}-{slug}/summary.md` |
| Implementation | Updates `{output_dir}/{feature}/plan.json` status |
| Code Review | `{output_dir}/{feature}/code-review/{N}-{slug}/summary.md` |
| Summarize | `{output_dir}/{feature}/summary/{N}-{slug}/summary.md` |

## Step Tracking (optional)

If tracking is desired, write state to `~/.shield/shield/<project>/steps.json`:

```json
{
  "phase": "<phase name>",
  "started_at": "<ISO timestamp>",
  "artifact_dir": "{output_dir}/{feature}/",
  "steps": [
    {"id": 1, "action": "<description>", "output": "<expected file path>", "status": "pending"},
    {"id": 2, "action": "<description>", "output": "<expected file path>", "status": "pending"}
  ]
}
```

After each step completes, update its status to `"complete"`. If a step fails, set status to `"failed"` and stop.

## Resume

If `steps.json` exists with incomplete steps, resume from the last incomplete step instead of starting over.
