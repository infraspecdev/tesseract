---
description: "Analyze a Terraform plan for security, cost, and destructive action impact before applying"
disable-model-invocation: true
---

# Plan Analysis

Analyze a Terraform execution plan to surface security-sensitive changes, cost impacts, destructive actions, and drift before `terraform apply`.

## Step 1: Detect Component

1. Check if `src/versions.tf` exists → single-component repo, component at `src/`
2. Check if `components/terraform/` exists → multi-component repo, ask user which component
3. Neither → report "This doesn't appear to be a Terraform component repository"

## Step 2: Locate or Generate Plan

Check for plan sources in this order:

1. **User provided a file path** → Read it directly as plan JSON
2. **`plan.tfplan` exists in component dir** → Convert: `terraform show -json plan.tfplan`
3. **`.terraform/` exists in component dir** → Ask user before generating:
   > "No plan file found. I can run `terraform plan -json -lock=false` to generate one. This is read-only and won't modify state. Proceed?"
4. **None of the above** → Tell user:
   > "No plan available. Either run `terraform init && terraform plan -out=plan.tfplan` first, or provide a plan JSON file path."

## Step 3: Run Plan Analysis

Invoke the `infra-review:terraform-plan-analyzer` skill against the plan JSON.

**IMPORTANT:** Never run `terraform apply`. This is analysis only.

## Step 4: Write Report

Write findings to `claude/infra-review/plan-analysis.md` in the repository root.

Present the change summary, any destructive warnings, security concerns, and the verdict to the user.
