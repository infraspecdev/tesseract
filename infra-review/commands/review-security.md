---
description: "Run a security-focused review of the current Terraform component (IAM, encryption, network exposure, Checkov)"
disable-model-invocation: true
---

# Security Review

Run a security-focused review of the current Terraform component.

## Step 1: Detect Component

1. Check if `src/versions.tf` exists → single-component repo, review `src/`
2. Check if `components/terraform/` exists → multi-component repo, ask user which component
3. Neither → report "This doesn't appear to be a Terraform component repository"

## Step 2: Run Security Review

Invoke the `infra-review:terraform-security-audit` skill against the detected component. Read all `.tf` files in the component directory and apply the full security audit checklist.

Also dispatch the `infra-review:security-reviewer` agent for its perspective.

## Step 3: Write Report

Write findings to `claude/infra-review/security-review.md` in the repository root.

Present the security posture summary and any critical findings to the user.
