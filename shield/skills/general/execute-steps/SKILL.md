---
name: execute-steps
description: Use when a skill needs step tracking, progress visibility, and resume support within a single phase. Called by skills, not directly by users.
---

# Execute Steps

Thin step-tracking utility for individual Shield skills. Each skill defines a fixed skeleton of mandatory steps, then drives `shield/scripts/steps_store.py` to register them and update status. The script writes `steps.json` to the exact path the session-start hook reads, so an interrupted run can be offered for resume.

**This is NOT a cross-phase orchestrator.** Each skill calls the script independently for its own work.

**Never hand-write `steps.json` with the Write tool.** Always go through `steps_store.py` — it computes the correct path and the correct schema. Hand-writing puts the file where the hook can't find it.

## When to Use

- Called by a skill at startup to register its step skeleton
- Called by a skill after each step to update status
- Called by a skill to check for and resume interrupted work

## When NOT to Use

- Directly by users — skills call this, not users
- As a cross-phase pipeline — each skill manages its own phase

## Quick Reference

Run with `uv run shield/scripts/steps_store.py <cmd>`. The script resolves the path itself — pass no path.

| Lifecycle Hook | Command |
|----------------|---------|
| **Startup** | `read` first → if it returns an incomplete doc, offer resume or fresh; then `init --skill <name> --feature <slug> --steps-json '<json array>'` |
| **Before step** | `start <id>` |
| **After step** | `complete <id> [--output <path>]` — or `fail <id>` → stop |
| **All done** | `clear` |

The `--steps-json` array holds the skeleton — each step is `{"id": N, "action": "...", "mandatory": true}`. Conditional steps add `"mandatory": false`; `init` defaults status to `pending` and `mandatory` to `true`. See `--help` for all flags.

## Where steps.json lives

`steps_store.py` resolves it to `${SHIELD_HOME:-~/.shield}/projects/<project>/steps.json`, where `<project>` comes from the nearest `.shield.json`. This is the path the session-start hook reads. **You do not compute or type this path** — the script does.

On resume, the session-start hook shows: `Incomplete: research phase (step 2/5 — Research agents). Run the skill command to resume.` The skill then runs `read` and asks: "Resume from step 2 or start fresh?"

## Mandatory vs Conditional Steps

- **Mandatory** steps always run — no exceptions, even under time pressure
- **Conditional** steps (`"mandatory": false`) evaluate their condition at startup and are omitted from the `init` skeleton if not met
- Conditions are evaluated once at registration, not re-evaluated mid-run

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hand-writing `steps.json` with the Write tool | Always use `steps_store.py` — it owns the path and schema |
| Typing the path yourself (e.g. `~/.shield/shield/<project>/`) | Never type the path — the script resolves it. The literal `shield/<project>` form is wrong; the hook reads `projects/<project>` |
| Skipping mandatory steps because "the context is clear enough" | Mandatory steps always run — conditions only apply to non-mandatory steps |
| Not running `read` before `init` | Always check first — an interrupted run should be offered for resume |
| Leaving `steps.json` after all steps complete | Run `clear` on completion — stale state causes false resume prompts |
| Treating execute-steps as the entry point | Skills are the entry point — this script is a utility they call, not an orchestrator |
| Relying on steps.json for loop iteration tracking | steps.json tracks coarse workflow position. For loops (e.g., per-AC), use the domain artifact (plan.json) as the per-item source of truth |
