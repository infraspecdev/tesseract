# Execute-Steps Redesign: Intra-Phase Step Tracker

**Status:** Approved
**Date:** 2026-03-19

## Problem

execute-steps is a cross-phase orchestrator (research → plan → review → implement) that is rarely useful — skills work standalone. Meanwhile, individual skills do their work in one big pass without trackable intermediate steps, making it hard to resume interrupted work or see progress.

## Solution

Rewrite execute-steps from a cross-phase orchestrator into a thin step-tracking utility. Each skill defines a fixed skeleton of mandatory steps with optional conditional sub-steps, calls execute-steps to register and track them, and execute-steps handles status updates and resume.

## Architecture

### Interaction Model

Skills call execute-steps (option B):
```
User → /research → research skill → calls execute-steps with skeleton
→ execute-steps tracks each step → skill executes steps
→ execute-steps updates status
```

Skills remain the entry point. Commands invoke skills directly. execute-steps is passive — it tracks, it doesn't orchestrate.

### Step Skeleton Format

Each skill has a `## Step Skeleton` section in its SKILL.md:

```markdown
## Step Skeleton

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Clarify topic | skip if user provided context | No |
| 2 | PM framing | always | Yes |
| 3 | Parallel research agents | always | Yes |
```

At startup, the skill evaluates conditions and passes the resolved step list to execute-steps.

### Skeleton Approach: Hybrid (option C)

Each skill has a fixed skeleton of mandatory steps that always run, plus conditional steps that can be added/removed based on context. This prevents agents from rationalizing away critical steps (validated by RED-GREEN testing) while allowing flexibility for context-dependent work.

### steps.json Format

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

Path: `~/.shield/shield/<project>/steps.json`

### Resume Flow (option C — notify + manual)

1. Session starts → hook detects incomplete `steps.json` → shows: "Incomplete: research phase (step 2/5 — Parallel research agents). Run `/research` to resume."
2. User runs `/research` → skill calls execute-steps → finds incomplete steps → asks: "Resume from step 2 (Parallel research agents) or start fresh?"
3. User chooses → execution continues from that step.

## Per-Skill Skeletons

### Research

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Clarify topic | skip if user provided context | No |
| 2 | PM framing | always | Yes |
| 3 | Parallel research agents (3) | always | Yes |
| 4 | Synthesize findings | always | Yes |
| 5 | PM review | always | Yes |
| 6 | Write document + update manifest | always | Yes |

### Plan-docs

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Gather requirements | skip if spec/topic provided | No |
| 2 | Check for prior research | skip if no research exists | No |
| 3 | Generate plan.json sidecar | always | Yes |
| 4 | Generate architecture HTML | always | Yes |
| 5 | Generate plan HTML | always | Yes |
| 6 | Update manifest + index.html | always | Yes |

### Plan-review

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Load plan document | always | Yes |
| 2 | Select reviewer personas | always | Yes |
| 3 | Dispatch selected agents in parallel | always | Yes |
| 4 | Parse grades + calculate scores | always | Yes |
| 5 | Generate enhanced plan | always | Yes |
| 6 | Write summary + detailed findings | always | Yes |
| 7 | Update manifest | always | Yes |

### Review

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Load prior context (plan, research) | skip if none exists | No |
| 2 | Code correctness review | always | Yes |
| 3 | Domain-specific review | skip if no active domains | No |
| 4 | Dispatch agent reviewers | explicit/final review only | No |
| 5 | AC verification | skip if no plan.json | No |
| 6 | Merge + present findings | always | Yes |
| 7 | Apply selected fixes | always | Yes |
| 8 | Write summary + update manifest | always | Yes |

### Implement-feature

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Load story from plan.json | skip if no plan context | No |
| 2 | Confirm acceptance criteria | always | Yes |
| 3 | Write failing test | always (TDD) | Yes |
| 4 | Implement to pass test | always | Yes |
| 5 | Per-step review | always | Yes |
| 6 | Commit | always | Yes |
| 7 | Repeat 3-6 for next AC | loop until all AC done | Yes |
| 8 | Update story status in plan.json | always | Yes |

## File Changes

| Action | File | Change |
|--------|------|--------|
| Rewrite | `skills/general/execute-steps/SKILL.md` | Thin tracker — register, track, resume. Remove cross-phase orchestration. |
| Modify | `skills/general/research/SKILL.md` | Add Step Skeleton, call execute-steps at startup |
| Modify | `skills/general/plan-docs/SKILL.md` | Add Step Skeleton, call execute-steps at startup |
| Modify | `skills/general/plan-review/SKILL.md` | Add Step Skeleton, call execute-steps at startup |
| Modify | `skills/general/review/SKILL.md` | Add Step Skeleton, call execute-steps at startup |
| Modify | `skills/general/implement-feature/SKILL.md` | Add Step Skeleton, call execute-steps at startup |
| Modify | `hooks/scripts/session-start.sh` | Add incomplete steps.json detection |

## What Gets Deleted

- Cross-phase pipeline concept (research → plan → review → implement sequence)
- The Artifact Paths table in execute-steps (each skill knows its own output paths)
- The old "Resume" section (replaced by per-skill resume via execute-steps)

## What Stays the Same

- `steps.json` location (`~/.shield/shield/<project>/`)
- Skills remain the entry point — commands invoke skills directly
- All artifact output paths unchanged
- execute-steps Common Mistakes section (updated for new scope)
