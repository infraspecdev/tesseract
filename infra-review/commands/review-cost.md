---
description: "Run a cost optimization review of the current Terraform component (NAT patterns, right-sizing, environment recommendations)"
disable-model-invocation: true
---

# Cost Review

Run a cost optimization review of the current Terraform component.

## Step 1: Detect Component

1. Check if `src/versions.tf` exists → single-component repo, review `src/`
2. Check if `components/terraform/` exists → multi-component repo, ask user which component
3. Neither → report "This doesn't appear to be a Terraform component repository"

## Step 2: Run Cost Review

Invoke the `infra-review:terraform-cost-review` skill against the detected component. Read all `.tf` files and identify cost-driving resources.

Also dispatch the `infra-review:cost-reviewer` agent for its perspective.

## Step 3: Write Report

Write findings to `claude/infra-review/cost-review.md` in the repository root.

Present the cost efficiency assessment, resource inventory, and environment-specific variable recommendations to the user.
