---
description: "Run a full AWS Well-Architected Framework review across all 6 pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability"
disable-model-invocation: true
---

# Well-Architected Review

Run a comprehensive AWS Well-Architected Framework review of the current Terraform component.

## Step 1: Detect Component

1. Check if `src/versions.tf` exists → single-component repo, review `src/`
2. Check if `components/terraform/` exists → multi-component repo, ask user which component
3. Neither → report "This doesn't appear to be a Terraform component repository"

## Step 2: Run Well-Architected Review

Dispatch the `infra-review:well-architected-reviewer` agent against the detected component. Read all `.tf` files in the component directory and evaluate against all 6 AWS Well-Architected Framework pillars.

For a thorough review, also cross-reference with findings from the specialized agents:
- `infra-review:security-reviewer` for deep Security pillar analysis
- `infra-review:cost-reviewer` for deep Cost Optimization pillar analysis
- `infra-review:operations-reviewer` for deep Operational Excellence pillar analysis
- `infra-review:architecture-reviewer` for structural and pattern analysis

## Step 3: Write Report

Write the complete Well-Architected Review to `claude/infra-review/well-architected-review.md` in the repository root.

Present the pillar scores summary, overall verdict, and top 3 prioritized remediation items to the user.
