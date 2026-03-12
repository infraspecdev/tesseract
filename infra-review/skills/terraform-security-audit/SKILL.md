---
name: terraform-security-audit
description: Use when auditing Terraform code for security vulnerabilities, reviewing IAM policies, checking encryption, or validating network isolation in AWS components
---

# Terraform Security Audit

## Overview

Deep security audit for Terraform AWS components that complements Checkov static analysis. This skill catches patterns that automated scanners miss: overly broad IAM policies, NACL ephemeral port gaps, encryption using AWS-managed keys instead of CMKs, and policy documents that are technically valid but operationally dangerous.

## When to Use

- After Checkov passes but you want deeper policy analysis
- When reviewing IAM policies for least-privilege compliance
- When auditing network security group and NACL configurations
- When validating encryption configuration meets organizational standards
- During security review of new or modified AWS components

## When NOT to Use

- For syntax-only validation -- use `terraform validate` instead
- When Checkov has not been run yet -- run Checkov first, then use this skill for deeper analysis
- For non-AWS providers (this skill is AWS-specific)
- For Terraform module API design reviews -- use a general code review instead
- For runtime security monitoring or incident response -- this is static code audit only

## Workflow

1. **Collect scope**: Identify all `.tf` files in the component
2. **IAM audit**: Read every `aws_iam_policy_document` and inline policy. Expand wildcards, verify resource scoping, check conditions on sensitive actions, flag `"*"` in actions or resources
3. **Network trace**: Map subnets and route tables. Trace paths from Internet through IGW, public subnets, security groups, and NACLs to private resources. Check both IPv4 and IPv6 rules
4. **Encryption check**: List all data-storing resources (S3, RDS, EBS, DynamoDB, CloudWatch). Verify CMK usage, key rotation, encryption in transit, and that logs/backups inherit encryption
5. **Checkov review**: Validate skip justifications are meaningful and scoped. Confirm critical checks are not skipped without strong justification
6. **Produce report**: Use the template from `templates.md`

See `audit-dimensions.md` for detailed check tables and verification steps for each dimension.

## Critical Checks

These are the highest-priority items to flag:

- `Effect = "Allow"` with `Action = "*"` or `Resource = "*"`
- Security groups or NACLs open to `::/0` (IPv6 internet)
- Data resources using `aws/s3` or `aws/rds` managed keys instead of CMKs
- CloudWatch log groups missing `kms_key_id`
- Checkov skips on critical checks (CKV_AWS_144, CKV_AWS_145, CKV2_AWS_19) without strong justification
- Cross-account trust policies missing `sts:ExternalId` condition

## Common Mistakes

| Mistake | Why It Happens | Correct Approach |
|---------|---------------|-----------------|
| Reporting only Checkov findings | Over-reliance on scanner output | Checkov is the baseline; manually expand wildcards and trace network paths |
| Ignoring IPv6 rules | IPv4 rules look secure | Always check both `cidr_blocks` and `ipv6_cidr_blocks` on every SG rule |
| Treating `aws/s3` default key as sufficient | Encryption is technically present | CMK is required for key rotation control and cross-account grant ability |
| Skipping egress rule review | Egress defaults to allow-all | Sensitive subnets need explicit egress restrictions |
| Accepting vague Checkov skip reasons | Skip exists so it must be intentional | Every skip must have a specific, meaningful justification |
| Missing log/backup encryption gaps | Main resource is encrypted | Cross-check that CloudWatch logs, replicas, and backups also use CMKs |

## Supporting Files

- `audit-dimensions.md` -- Detailed check tables for IAM, network, encryption, and Checkov dimensions
- `templates.md` -- Report output template
