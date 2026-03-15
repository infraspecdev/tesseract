---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories, plus a JSON sidecar for project management sync
---

# Plan

Generate Shield plan documents with a machine-readable sidecar.

## Usage

`/plan [topic or requirements]`

## Behavior

1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning

### Planning Phase

3. If `superpowers:brainstorming` or `superpowers:writing-plans` is available, invoke it first — it handles design thinking, plan structure, and story breakdown well
4. Whether or not superpowers ran, **always invoke `shield:plan-docs` afterward** to generate the plan sidecar JSON
   - If superpowers produced a plan document, pass it to plan-docs as input
   - If superpowers was not available, plan-docs handles the full planning workflow itself

### Sidecar Generation

5. The `shield:plan-docs` skill generates:
   - Architecture/ADR document (HTML)
   - Detailed execution plan with stories (HTML)
   - **Plan sidecar JSON** (`plan.json`) — machine-readable story data
6. Verify the sidecar JSON was created and contains:
   - At least 1 epic with stories
   - Each story has acceptance criteria
7. The sidecar is **required** by downstream phases:
   - `/pm-sync` reads stories from it
   - `/implement` reads acceptance criteria from it
   - `/review` verifies acceptance criteria against it

### Completion

8. Invoke `shield:general:summarize` to produce a plan summary
9. Write the summary to the run directory
10. Offer next steps:
    - `/plan-review` — run multi-agent review on the plan
    - `/pm-sync` — sync stories to project management tool
