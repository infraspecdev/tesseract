---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories
---

# Plan

Invoke the Shield plan-docs skill to create planning documents.

## Usage

`/plan [topic or requirements]`

## Behavior

1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning
3. Invoke the `shield:general:plan-docs` skill
4. The skill generates:
   - Architecture/ADR document (HTML)
   - Detailed execution plan with stories (HTML)
   - Plan sidecar JSON (machine-readable story data)
5. After completion, invoke `shield:general:summarize` to produce a plan summary
6. Write the summary to the run directory
7. Offer next steps:
   - `/plan-review` — run multi-agent review on the plan
   - `/pm-sync` — sync stories to PM tool
