# Security Audit Report Template

Use this template when producing the final audit report.

```markdown
## Security Audit Report

**Component:** [name]
**Date:** [date]
**Auditor:** terraform-security-audit skill

### Executive Summary

[2-3 sentence summary of security posture]

### IAM Policy Analysis

| Policy/Role | Risk Level | Finding | Recommendation |
|------------|-----------|---------|----------------|
| ... | High/Medium/Low | ... | ... |

### Network Exposure Map

| Path | Risk | Status |
|------|------|--------|
| Internet -> Public Subnet | Expected | Controlled by SG-X |
| Public -> Private | ... | ... |

### Encryption Status

| Resource | At Rest | In Transit | Key Type | Status |
|----------|---------|-----------|----------|--------|
| ... | Yes/No | Yes/No | CMK/AWS-managed/None | OK/Risk |

### Checkov Skip Review

| Resource | Skip ID | Reason | Assessment |
|----------|---------|--------|-----------|
| ... | CKV_... | "reason" | Justified/Unjustified |

### Risk Register

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|-----------|-----------|
| 1 | ... | Critical/High/Medium/Low | ... | ... |

## Overall Assessment: [Secure / Acceptable Risk / Needs Remediation / Unsafe]
```
