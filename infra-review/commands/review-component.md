---
description: "Run a comprehensive 4-perspective review of the current Terraform component (security, architecture, operations, cost)"
disable-model-invocation: true
---

# Full Component Review

Run a comprehensive review of the current Terraform component from 4 perspectives. Follow this process exactly:

## Pre-flight: Atmos Hygiene Check

Before dispatching agents, invoke the `infra-review:atmos-component-hygiene` skill to run a quick hygiene check. If critical issues are found (missing versions.tf, committed backend.tf), report them immediately — they should be fixed before a full review.

## Step 1: Detect Component

Identify the component to review:
1. Check if `src/versions.tf` exists → single-component repo, review `src/`
2. Check if `components/terraform/` exists → multi-component repo, ask user which component
3. Neither → report "This doesn't appear to be a Terraform component repository"

## Step 2: Dispatch Reviewers

Run all 4 reviewer agents sequentially against the component. For each agent, use the Agent tool with the appropriate agent type:

1. **Security Review** — Dispatch the `infra-review:security-reviewer` agent
   - Provide all `.tf` files from the component directory
   - Collect findings

2. **Architecture Review** — Dispatch the `infra-review:architecture-reviewer` agent
   - Provide all `.tf` files from the component directory
   - Collect findings

3. **Operations Review** — Dispatch the `infra-review:operations-reviewer` agent
   - Provide all `.tf` files and CI workflows from `.github/workflows/`
   - Collect findings

4. **Cost Review** — Dispatch the `infra-review:cost-reviewer` agent
   - Provide all `.tf` files from the component directory
   - Collect findings

## Step 3: Consolidated Report

After all 4 agents complete, write a consolidated report to `claude/infra-review/review.md` in the repository root:

```markdown
# Terraform Component Review

**Component:** [name]
**Date:** [date]
**Reviewers:** Security, Architecture, Operations, Cost

## Summary

| Dimension | Grade/Score | Key Finding |
|-----------|------------|-------------|
| Security | [posture] | [top finding] |
| Architecture | [grade] | [top finding] |
| Operations | [score]/10 | [top finding] |
| Cost | [efficiency] | [top finding] |

## Critical Issues (Action Required)

[List any Critical/Must-Fix issues from all 4 reviews]

## Detailed Findings

### Security
[Full security review output]

### Architecture
[Full architecture review output]

### Operations
[Full operations review output]

### Cost
[Full cost review output]

## Recommended Priority Order

1. [Most important fix across all dimensions]
2. [Second]
3. [Third]
```

Present the summary table to the user and note where the full report was written.
