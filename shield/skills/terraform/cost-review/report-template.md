# Cost Review Report Template

```markdown
## Cost Review Report

**Component:** [name]
**Date:** [date]

### Resource Cost Inventory

| Resource Type | Count | Key Cost Driver | Est. Monthly (Prod) | Est. Monthly (Dev) |
|--------------|-------|-----------------|--------------------|--------------------|
| NAT Gateway | X | Hourly + data transfer | $X | $X |
| Elastic IP | X | Hourly when attached | $X | $X |
| ... | ... | ... | ... | ... |

### Cost Optimization Opportunities

| # | Opportunity | Current State | Recommended Change | Est. Savings |
|---|------------|--------------|-------------------|-------------|
| 1 | ... | ... | ... | $X/mo |

### Environment Variable Recommendations

#### Development (minimize cost)
| Variable | Recommended Value | Rationale |
|----------|------------------|-----------|
| ... | ... | ... |

#### Staging (balance cost and fidelity)
| Variable | Recommended Value | Rationale |
|----------|------------------|-----------|
| ... | ... | ... |

#### Production (optimize, don't sacrifice reliability)
| Variable | Recommended Value | Rationale |
|----------|------------------|-----------|
| ... | ... | ... |

### Missing Cost Controls

| Control | Status | Impact |
|---------|--------|--------|
| Toggle for expensive resources | Missing/Present | ... |
| Configurable retention | Missing/Present | ... |
| Configurable sizing | Missing/Present | ... |

## Cost Efficiency: [Optimized / Reasonable / Over-provisioned / Missing Controls]

**Key Findings:**
- [Top 3 cost-related observations]

**Estimated Savings if Recommendations Applied:**
- Dev: ~$X/month
- Staging: ~$X/month
```
