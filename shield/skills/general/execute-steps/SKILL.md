---
name: execute-steps
description: Use when a skill needs step tracking, progress visibility, and resume support within a single phase. Called by skills, not directly by users.
---

# Execute Steps

Thin step-tracking utility for individual Shield skills. Each skill defines a fixed skeleton of mandatory steps, calls execute-steps to register them, and execute-steps handles status updates and resume.

**This is NOT a cross-phase orchestrator.** Each skill (research, plan-docs, review, etc.) calls execute-steps independently for its own work.

## When to Use

- Called by a skill at startup to register its step skeleton
- Called by a skill after each step to update status
- Called by a skill to check for and resume interrupted work

## When NOT to Use

- Directly by users — skills call this, not users
- As a cross-phase pipeline — each skill manages its own phase

## How Skills Use execute-steps

### 1. At Startup — Register Steps

The skill evaluates its Step Skeleton conditions and registers the resolved step list:

1. Read the skill's `## Step Skeleton` table
2. Evaluate each step's condition against the current context
3. Build the resolved step list (skip steps whose conditions are not met, keep all mandatory steps)
4. Check `~/.shield/shield/<project>/steps.json` for an incomplete run of this skill
   - If found: ask user "Resume from step N (action) or start fresh?"
   - If not found: write new `steps.json` with all steps as `pending`

### 2. Before Each Step — Mark In Progress

Before the skill executes a step:
- Update the step's status to `in_progress` in `steps.json`

### 3. After Each Step — Mark Complete

After the skill finishes a step:
- Update the step's status to `complete` in `steps.json`
- Set `output` to the artifact path if the step produced one
- If the step failed, set status to `failed` and stop execution

### 4. On Completion — Clean Up

When all steps are complete:
- Delete `steps.json` (the work is done, artifacts are in `{output_dir}/`)

## steps.json Format

Path: `~/.shield/shield/<project>/steps.json`

```json
{
  "skill": "research",
  "feature": "vpc-module-20260319",
  "started_at": "2026-03-19T10:00:00Z",
  "steps": [
    {"id": 1, "action": "PM framing", "mandatory": true, "status": "complete", "output": null},
    {"id": 2, "action": "Parallel research agents", "mandatory": true, "status": "in_progress", "output": null},
    {"id": 3, "action": "Synthesize findings", "mandatory": true, "status": "pending", "output": null},
    {"id": 4, "action": "PM review", "mandatory": true, "status": "pending", "output": null},
    {"id": 5, "action": "Write document", "mandatory": true, "status": "pending", "output": "docs/shield/vpc-module-20260319/research/1-topic/findings.md"}
  ]
}
```

## Resume Flow

1. Session starts → session-start hook detects incomplete `steps.json` → shows: `⚠ Incomplete: research phase (step 2/5 — Parallel research agents). Run /research to resume.`
2. User runs `/research` → research skill calls execute-steps → finds incomplete steps
3. execute-steps asks: "Resume from step 2 (Parallel research agents) or start fresh?"
4. If resume: skill skips completed steps, continues from the incomplete step
5. If fresh: overwrite `steps.json` with new run

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping mandatory steps because "the context is clear enough" | Mandatory steps always run — conditions only apply to non-mandatory steps |
| Not checking for incomplete `steps.json` before registering new steps | Always check first — an interrupted run should be offered for resume |
| Leaving `steps.json` after all steps complete | Delete it on completion — stale state causes false resume prompts |
| Writing step state to `{output_dir}/` instead of `~/.shield/` | Step state goes in `~/.shield/shield/<project>/steps.json` — artifacts go in `{output_dir}/` |
| Treating execute-steps as the entry point | Skills are the entry point — execute-steps is a utility they call, not an orchestrator |
