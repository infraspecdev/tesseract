---
name: summarize
description: Use when a pipeline phase completes and needs an audit trail summary. Called by other skills, not directly by users.
---

# Phase Summarize

## Output Path — MANDATORY

Write the summary using the Write tool to **exactly** this path:

```
{output_dir}/{feature}/summary/{N}-{slug}/summary.md
```

Where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`), `{feature}` is the feature folder name (`{feature-name}-YYYYMMDD`), `{N}` is a sequential number, and `{slug}` is a short kebab-case descriptor (e.g., `1-research`, `2-plan-review`). **Do NOT** use any other path, filename, or directory. The Write tool creates directories automatically.

After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

## When to Use

Called automatically by each phase's orchestrator at the end of execution. Not invoked directly by users.

## Input

The orchestrator passes:
- `phase_name`: The pipeline phase that just completed (research, plan, plan-review, sync, implement-step-N, review-step-N, final-review)
- `phase_output`: Structured data about what was done
- `project_name`: From `.shield.json`
- `run_id`: The current run identifier (date-topic)

## Process

1. Format the phase output as concise bullet points (5-10 bullets max)
2. Include: what was done, key decisions made, findings if any, next phase
3. Write to `{output_dir}/{feature}/summary/{N}-{slug}/summary.md`
4. Return the summary text to the orchestrator for display

## Summary Format

```
# <Phase Name> Summary

**Run:** <run_id>
**Date:** <timestamp>

## What was done
- Bullet 1
- Bullet 2

## Key decisions
- Decision 1 (if any)

## Findings
- Finding 1 (if any review findings)

## Next
- What the next phase will do
```

### Plan Summary Template

When `phase_name` is `plan`, replace the generic "What was done" bullets with the plan-specific template below. Read the sidecar at `{output_dir}/{feature}/plan.json` to populate the structural counts.

```
# Plan Summary

**Run:** <run_id>
**Date:** <timestamp>

## What was done
- **Plan:** <plan name> (<phase>)
- **Milestones (N):** M1 Login core; M2 Password recovery (depends on M1); …
  _(Omit this bullet entirely when `sidecar.milestones` is empty.)_
  _(For each milestone: `<id> <name>`. Append ` (depends on <id1>, <id2>)` only when depends_on is non-empty.)_
- **Epics:** N epic(s) — <Epic-1 name>, <Epic-2 name>, …
- **Stories:** N total (N ready, N in-progress, N done)
- Architecture doc and detailed execution plan written to <relative path>

## Key decisions
- Decision 1 (if any)

## Next
- Suggested next step (e.g., /plan-review, /pm-sync)
```

**Milestone rendering rules:**
- If `sidecar.milestones` has ≥ 1 entry → render the Milestones bullet: `- **Milestones (N):** M1 <name>; M2 <name> (depends on M1); …`
- If `sidecar.milestones` is empty (`[]`) → omit the Milestones bullet entirely (back-compat path, no milestones defined)
- Count N from `sidecar.milestones.length`
- Inline list format: `<id> <name>` separated by `; `. Append ` (depends on <ids>)` when `depends_on` is non-empty for that milestone.

## Rules

- Keep summaries concise — 5-10 bullets per section max
- Include only information relevant to the next phase or audit trail
- Do not repeat full review findings — reference the review summary file
- Always include the "Next" section so the user knows what's coming
