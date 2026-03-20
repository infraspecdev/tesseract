---
name: execute-steps
description: Use when a skill needs step tracking, progress visibility, and resume support within a single phase. Called by skills, not directly by users.
---

# Execute Steps

Thin step-tracking utility for individual Shield skills. Each skill defines a fixed skeleton of mandatory steps, calls execute-steps to register them, and execute-steps handles status updates and resume.

**This is NOT a cross-phase orchestrator.** Each skill calls execute-steps independently for its own work.

## When to Use

- Called by a skill at startup to register its step skeleton
- Called by a skill after each step to update status
- Called by a skill to check for and resume interrupted work

## When NOT to Use

- Directly by users — skills call this, not users
- As a cross-phase pipeline — each skill manages its own phase

## Quick Reference

| Lifecycle Hook | What to Do |
|----------------|------------|
| **Startup** | Evaluate Step Skeleton conditions → check for incomplete `steps.json` (offer resume or fresh) → write `steps.json` |
| **Before step** | Set step status to `in_progress` |
| **After step** | Set status to `complete` (or `failed` → stop). Record output path if applicable. |
| **All done** | Delete `steps.json` |

## steps.json

Path: `~/.shield/shield/<project>/steps.json`

```json
{"skill": "research", "feature": "vpc-module-20260319", "started_at": "...",
 "steps": [
   {"id": 1, "action": "PM framing", "mandatory": true, "status": "complete", "output": null},
   {"id": 2, "action": "Research agents", "mandatory": true, "status": "in_progress", "output": null}
 ]}
```

On resume, the session-start hook shows: `⚠ Incomplete: research phase (step 2/5 — Research agents). Run /research to resume.` The skill then asks: "Resume from step 2 or start fresh?"

## Mandatory vs Conditional Steps

- **Mandatory** steps always run — no exceptions, even under time pressure
- **Conditional** steps evaluate their condition at startup and are skipped if not met
- Conditions are evaluated once at registration, not re-evaluated mid-run

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping mandatory steps because "the context is clear enough" | Mandatory steps always run — conditions only apply to non-mandatory steps |
| Not checking for incomplete `steps.json` before registering new steps | Always check first — an interrupted run should be offered for resume |
| Leaving `steps.json` after all steps complete | Delete it on completion — stale state causes false resume prompts |
| Writing step state to `{output_dir}/` instead of `~/.shield/` | Step state goes in `~/.shield/shield/<project>/steps.json` — artifacts go in `{output_dir}/` |
| Treating execute-steps as the entry point | Skills are the entry point — execute-steps is a utility they call, not an orchestrator |
| Relying on steps.json for loop iteration tracking | steps.json tracks coarse workflow position. For loops (e.g., per-AC), use the domain artifact (plan.json) as the per-item source of truth |
