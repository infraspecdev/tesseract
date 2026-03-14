# Terraform Plan Analyzer — Report Template

Write to `claude/infra-review/plan-analysis.md` in the repository root.

```markdown
# Terraform Plan Analysis

**Component:** [name]
**Date:** [date]
**Plan source:** [generated locally | provided file | converted from .tfplan]

## Change Summary

| Action | Count | Resources |
|--------|-------|-----------|
| Create | N | `resource.name`, ... |
| Update | N | `resource.name`, ... |
| Replace | N | `resource.name`, ... |
| Destroy | N | `resource.name`, ... |
| **Total** | **N** | |

## Destructive Action Warnings

| Resource | Action | Risk | Impact |
|----------|--------|------|--------|
| `aws_rds_instance.main` | destroy | CRITICAL | Data loss |

*None* — if no destructive actions.

## Security-Sensitive Changes

### IAM
| Resource | Change | Concern |
|----------|--------|---------|
| ... | ... | ... |

### Network
| Resource | Change | Concern |
|----------|--------|---------|
| ... | ... | ... |

### Encryption
| Resource | Change | Concern |
|----------|--------|---------|
| ... | ... | ... |

*None* — if no security-sensitive changes.

## Cost Impact

| Resource | Action | Est. Monthly Impact |
|----------|--------|-------------------|
| `aws_nat_gateway.main` | create | +$32/month |
| `aws_eip.nat` | create | +$3.60/month |

**Estimated net change:** +$X/month

*None* — if no cost-impacting changes.

## Drift Detected

| Resource | Expected | Actual | Likely Cause |
|----------|----------|--------|-------------|
| ... | ... | ... | Manual change / provider update |

*None* — if no drift detected.

## Output Changes

| Output | Action | Value |
|--------|--------|-------|
| `vpc_id` | create | (known after apply) |

## Verdict: [Safe to Apply | Review Required | Do Not Apply]

**Rationale:**
- [Key observations driving the verdict]

**Recommendations before applying:**
1. [Any actions to take first]
```
