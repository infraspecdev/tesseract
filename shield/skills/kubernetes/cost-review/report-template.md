# Kubernetes Cost Review Report Template

```markdown
## Kubernetes Cost Review Report

**Scope:** [namespace/directory/chart name]
**Date:** [date]

### Workload Cost Inventory

| Workload | Type | Replicas | CPU Req | CPU Limit | Mem Req | Mem Limit | Scaling |
|----------|------|----------|---------|-----------|---------|-----------|---------|
| ... | Deployment/StatefulSet | X | ... | ... | ... | ... | HPA/VPA/None |

### Storage Inventory

| PVC | Storage Class | Size | Access Mode | Workload | Status |
|-----|--------------|------|------------|----------|--------|
| ... | gp3/gp2/standard | XGi | RWO/RWX | ... | OK/Over-provisioned |

### Cost Optimization Opportunities

| # | Opportunity | Current State | Recommended Change | Est. Impact |
|---|------------|--------------|-------------------|-------------|
| 1 | ... | ... | ... | Reduce X% resource usage |

### Environment-Specific Recommendations

#### Development (minimize cost)
| Workload | Replicas | CPU Req | Mem Req | Notes |
|----------|----------|---------|---------|-------|
| ... | 1 | ... | ... | ... |

#### Staging (balance cost and fidelity)
| Workload | Replicas | CPU Req | Mem Req | Notes |
|----------|----------|---------|---------|-------|
| ... | 2 | ... | ... | ... |

#### Production (optimize, don't sacrifice reliability)
| Workload | Replicas | CPU Req | Mem Req | Notes |
|----------|----------|---------|---------|-------|
| ... | 3+ | ... | ... | ... |

### Missing Cost Controls

| Control | Status | Impact |
|---------|--------|--------|
| Resource requests on all containers | Missing/Present | ... |
| HPA on variable-load workloads | Missing/Present | ... |
| Namespace resource quotas | Missing/Present | ... |
| Environment-specific overlays | Missing/Present | ... |

## Cost Efficiency: [Optimized / Reasonable / Over-provisioned / Missing Controls]

**Key Findings:**
- [Top 3 cost-related observations]
```
