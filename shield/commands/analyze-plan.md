---
name: analyze-plan
description: Analyze terraform plan output for security, cost, and destructive action impact
args: "[path to plan JSON]"
---

# Analyze Terraform Plan

Analyze `terraform plan -json` output for security, cost, and operational impact.

## Usage

`/analyze-plan [path to plan JSON]`

## Behavior

1. Detect the component (src/ vs components/terraform/)
2. Locate or generate plan:
   - User-provided JSON path
   - Existing .tfplan file
   - Or offer to run `terraform plan -json` (NEVER `terraform apply`)
3. Invoke `shield:terraform:plan-analysis` skill
4. The skill analyzes: change summary, destructive actions, security changes, cost impact, drift
5. Write report to `{output_dir}/{feature}/` structure (under the appropriate subdirectory)
6. Present summary with flagged items

## Important

- NEVER run `terraform apply`
- Use `-lock=false` when generating plans
- Flag destructive actions (destroy, replace) prominently
