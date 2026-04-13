# Kubernetes Security Audit Report Template

Use this template when producing the final audit report.

```markdown
## Kubernetes Security Audit Report

**Scope:** [namespace/directory/chart name]
**Date:** [date]
**Auditor:** kubernetes-security-audit skill
**EKS-Specific:** [Yes/No]

### Executive Summary

[2-3 sentence summary of security posture]

### RBAC Analysis

| Role/ClusterRole | Scope | Risk Level | Finding | Recommendation |
|-----------------|-------|-----------|---------|----------------|
| ... | Cluster/Namespace | High/Medium/Low | ... | ... |

### Pod Security Findings

| Workload | Container | Risk Level | Finding | Recommendation |
|----------|-----------|-----------|---------|----------------|
| ... | ... | High/Medium/Low | ... | ... |

### Network Policy Coverage

| Namespace | Has Policy | Ingress Restricted | Egress Restricted | Status |
|-----------|-----------|-------------------|-------------------|--------|
| ... | Yes/No | Yes/No/Partial | Yes/No/Partial | OK/Risk |

### Secrets Management

| Secret | Location | Risk Level | Finding | Recommendation |
|--------|----------|-----------|---------|----------------|
| ... | env/volume/manifest | High/Medium/Low | ... | ... |

### Image Security

| Workload | Image | Tag/Digest | Registry | Status |
|----------|-------|-----------|----------|--------|
| ... | ... | latest/v1.2.3/sha256:... | public/private | OK/Risk |

### Service Account Audit

| Workload | Service Account | Auto-Mount | RBAC Scope | Status |
|----------|----------------|-----------|-----------|--------|
| ... | default/custom | Yes/No | ... | OK/Risk |

### Pod Security Standards Compliance

| Workload | Target Level | Violations | Status |
|----------|-------------|-----------|--------|
| ... | Restricted/Baseline | [list] | Pass/Fail |

### EKS-Specific Findings (if applicable)

| Check | Status | Finding | Recommendation |
|-------|--------|---------|----------------|
| IRSA usage | ... | ... | ... |
| aws-auth review | ... | ... | ... |

### Risk Register

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|-----------|-----------|
| 1 | ... | Critical/High/Medium/Low | ... | ... |

## Overall Assessment: [Secure / Acceptable Risk / Needs Remediation / Unsafe]
```
