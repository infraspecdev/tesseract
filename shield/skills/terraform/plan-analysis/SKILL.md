---
name: terraform-plan-analyzer
description: Use when analyzing Terraform plan output for security, cost, and operational impact — parses terraform plan JSON to surface destructive changes, IAM modifications, cost-impacting resources, and drift before apply
---

# Terraform Plan Analyzer

## Overview

Analyzes `terraform plan -json` output to surface security-sensitive changes, cost-impacting resources, destructive actions, and drift before `terraform apply`. Complements static code review by showing what will actually change.

**Core principle:** Review the plan, not just the code. Static analysis catches bad patterns; plan analysis catches bad outcomes.

## When to Use

- Before running `terraform apply` on any environment
- After modifying Terraform code, to preview impact
- When reviewing CI/CD plan output from a pull request
- To validate that a code change produces the expected resource changes
- After importing or moving resources, to verify no unintended drift

## When NOT to Use

- For static Terraform code review without a plan (use a linter or code review instead)
- When `terraform init` has not been run and no plan JSON is available
- For non-Terraform IaC tools (CloudFormation, Pulumi, CDK)
- To actually apply changes (this skill is strictly read-only)

## Workflow

Detect Plan Source -> Parse Plan JSON -> Analyze Changes -> Write Report -> Present Summary

Plan source priority: user-provided JSON > existing `.tfplan` file (convert via `terraform show -json`) > generate via `terraform plan -json -lock=false` (requires `.terraform/`). If none available, prompt user to run `terraform init` or provide CI output.

## Critical Rules

1. **NEVER run `terraform apply`** — This skill is read-only. Only `plan` and `show` commands.
2. **Use `-lock=false`** — Don't acquire state lock for analysis.
3. **ALWAYS write report** — Even if no changes detected, document that fact.
4. **Flag destructive actions prominently** — Destroy/replace on stateful resources gets top billing.
5. **Ask before generating plan** — If no plan JSON is provided, confirm with user before running `terraform plan`.

## Steps

### 1. Detect Plan Source

Locate plan data using the priority from the Workflow section above. Ask user before generating a new plan.

### 2. Parse Plan JSON

Extract resource changes, output changes, and diagnostics. Format differs between streamed `plan -json` (line-delimited) and `show -json` (single object with `resource_changes[]`). See **reference-tables.md** for message types and extraction details.

### 3. Analyze Changes

Five analysis passes: change summary (by action type), destructive action warnings (risk-classified), security-sensitive changes (IAM/network/encryption/public access), cost-impacting changes (with estimates), and drift detection. See **reference-tables.md** for all classifications and thresholds.

### 4. Write Report

Write to `claude/infra-review/plan-analysis.md`. Include all analysis sections plus a verdict (Safe to Apply / Review Required / Do Not Apply). See **templates.md** for format and **reference-tables.md** for verdict criteria.

## Common Mistakes

| Mistake | Why It Fails | Do Instead |
|---------|-------------|------------|
| Running `terraform apply` | Causes real infrastructure changes | Only use `plan` and `show` commands |
| Omitting `-lock=false` | Blocks other operations by holding state lock | Always pass `-lock=false` |
| Skipping report when no changes | No record the analysis was performed | Write report documenting "no changes" |
| Treating all destroys equally | Destroying a security group differs from a database | Use risk-level classifications from reference-tables.md |
| Ignoring drift entries | Out-of-band changes may conflict | Always surface drift with likely cause |

## Supporting Files

- **reference-tables.md** — Risk levels, security-sensitive resources, cost estimates, JSON parsing reference, verdict criteria
- **templates.md** — Report template for plan-analysis.md
