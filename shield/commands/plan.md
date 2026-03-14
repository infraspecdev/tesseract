---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories, plus a JSON sidecar for project management sync
---

# Plan

Generate Shield plan documents with a machine-readable sidecar.

## Usage

`/plan [topic or requirements]`

## CRITICAL: Use Shield's Plan Skill

This command MUST invoke `shield:general:plan-docs` — NOT superpowers:brainstorming, superpowers:writing-plans, or any other external planning skill. Shield's plan-docs skill generates the **plan sidecar JSON** that the rest of the pipeline depends on (PM sync, acceptance criteria confirmation, review verification). External planning skills do not produce this sidecar.

If superpowers or other planning plugins are installed, they should NOT be used for this command. Use the Skill tool to invoke `shield:plan-docs` directly.

## Behavior

1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning
3. **Invoke the `shield:plan-docs` skill using the Skill tool** — this is mandatory
4. The skill generates:
   - Architecture/ADR document (HTML)
   - Detailed execution plan with stories (HTML)
   - **Plan sidecar JSON** (machine-readable story data at `plan-sidecar.json`)
5. Verify the sidecar JSON was created and contains:
   - At least 1 epic with stories
   - Each story has acceptance criteria
   - Validates against the plan-sidecar schema
6. After completion, invoke `shield:general:summarize` to produce a plan summary
7. Write the summary to the run directory
8. Offer next steps:
   - `/plan-review` — run multi-agent review on the plan
   - `/pm-sync` — sync stories to project management tool
