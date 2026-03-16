---
name: summarize
description: Use when a pipeline phase completes and needs an audit trail summary. Called by other skills, not directly by users.
---

# Phase Summarize

## Output Path — MANDATORY

Write the summary using the Write tool to **exactly** this path:

```
shield/docs/<phase_name>-summary-YYYYMMDD-HHMMSS.md
```

Replace `<phase_name>` with the phase (e.g. `research`, `plan`, `review`) and `YYYYMMDD-HHMMSS` with the current date and time. **Do NOT** use any other path, filename, or directory. No `latest/`, no custom filenames. The Write tool creates `shield/docs/` automatically.

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
3. Write to `shield/docs/<phase_name>-summary-YYYYMMDD-HHMMSS.md`
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

## Rules

- Keep summaries concise — 5-10 bullets per section max
- Include only information relevant to the next phase or audit trail
- Do not repeat full review findings — reference the review summary file
- Always include the "Next" section so the user knows what's coming
