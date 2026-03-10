---
name: terraform-cost-review
description: Use when reviewing Terraform components for AWS cost optimization, right-sizing, or identifying unnecessary expensive resources like NAT gateways or over-provisioned subnets
---

# Terraform Cost Review

## Overview

Cost analysis framework for Terraform AWS components. Identifies cost drivers, evaluates configuration for optimization opportunities, and provides environment-specific variable recommendations to reduce AWS spend in non-production environments.

## When to Use

- Reviewing a new Terraform component before deployment
- Evaluating existing components for cost optimization
- Planning environment-specific variable overrides in Atmos stacks
- After receiving a surprisingly high AWS bill
- During FinOps review of infrastructure components

## Cost Analysis Process

### Step 1: Resource Inventory

Read all `.tf` files and inventory every resource that incurs AWS charges:

| Resource Category | Resources to Inventory | Key Cost Factors |
|-------------------|----------------------|-----------------|
| **Networking** | NAT Gateway, EIP, VPC Endpoint, Transit Gateway attachment | Per-hour + data transfer |
| **Compute** | EC2, Lambda, ECS tasks, EKS node groups | Instance type, runtime hours |
| **Storage** | S3 buckets, EBS volumes, EFS | Storage class, IOPS, throughput |
| **Database** | RDS, DynamoDB, ElastiCache | Instance type, storage, backups |
| **Monitoring** | CloudWatch log groups, metrics, alarms | Ingestion rate, retention, custom metrics |
| **Security** | KMS keys, WAF, Shield, GuardDuty | Per-key/month, per-rule evaluations |

### Step 2: Configuration Analysis

For each cost-driving resource, check:

| Analysis | What to Check |
|----------|--------------|
| **Toggleability** | Is there an `enable_*` variable to disable in dev? |
| **Sizing** | Are instance types, CIDR sizes, counts configurable via variables? |
| **Scaling** | Can counts be reduced (AZs, replicas, NAT gateways)? |
| **Retention** | Are log retention periods configurable and bounded? |
| **Tier selection** | Are storage classes, instance families configurable? |
| **Data transfer** | Are there unnecessary cross-AZ or cross-region transfers? |

### Step 3: Environment-Specific Recommendations

For each variable that affects cost, recommend values per environment:

| Variable Pattern | Dev | Staging | Production |
|-----------------|-----|---------|-----------|
| `enable_nat_gateway` | `false` | `true` | `true` |
| `nat_gateway_count` | `0` | `1` | AZ count |
| `az_count` | `1` | `2` | `3` |
| `instance_type` | Smallest viable | Medium | Production-sized |
| `flow_log_retention_days` | `7` | `14` | `90` |
| `enable_vpc_endpoints` | `false` | `false` | `true` |

## Common Cost Traps

| Trap | Typical Monthly Cost | How to Detect | Fix |
|------|---------------------|--------------|-----|
| 3 NAT gateways in dev | ~$100 + data transfer | `count` or `for_each` on `aws_nat_gateway` without variable control | Add `enable_nat_gateway` and `nat_gateway_count` variables |
| Flow logs to CloudWatch (high traffic) | $50-500 at scale | `aws_flow_log` with `log_destination_type = "cloud-watch-logs"` and no retention limit | Set bounded `retention_in_days`, consider S3 destination |
| /16 subnets from IPAM | Wastes IP space for future VPCs | `netmask_length = 16` in IPAM allocation | Use /20 or /24, make configurable |
| VPC interface endpoints everywhere | $7.50/endpoint/AZ/month | `aws_vpc_endpoint` with `type = "Interface"` in all environments | Toggle with `enable_vpc_endpoints`, use gateway endpoints for S3/DynamoDB (free) |
| Infinite CloudWatch log retention | Grows unbounded | `aws_cloudwatch_log_group` without `retention_in_days` | Always set explicit retention |
| EIPs without NAT gateways | $3.60/month each when unused | `aws_eip` created but NAT gateway disabled | Conditional creation tied to NAT gateway enable flag |
| Cross-AZ data transfer | $0.01/GB | Resources in different AZs communicating frequently | Co-locate when possible, or accept as HA cost |

## Output Format

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

## Estimation Methodology

Use these approximate costs for common AWS resources (us-east-1):

| Resource | Approximate Cost |
|----------|-----------------|
| NAT Gateway | $32.40/month + $0.045/GB processed |
| Elastic IP (attached) | $3.60/month |
| VPC Interface Endpoint | $7.30/month/AZ |
| VPC Gateway Endpoint | Free |
| CloudWatch Log Ingestion | $0.50/GB |
| CloudWatch Log Storage | $0.03/GB/month |
| KMS CMK | $1.00/month + $0.03/10K requests |
| S3 Standard | $0.023/GB/month |
| EBS gp3 | $0.08/GB/month |
