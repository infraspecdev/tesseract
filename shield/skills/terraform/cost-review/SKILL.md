---
name: terraform-cost-review
description: Use when reviewing Terraform components for AWS cost optimization, right-sizing, or identifying unnecessary expensive resources like NAT gateways or over-provisioned subnets
---

# Terraform Cost Review

## Overview

Cost analysis framework for Terraform AWS components. Every resource must be toggleable or right-sizable per environment so non-production environments never pay production prices.

## When to Use

- Reviewing a new Terraform component before deployment
- Evaluating existing components for cost optimization
- Planning environment-specific variable overrides in Atmos stacks
- After receiving a surprisingly high AWS bill
- During FinOps review of infrastructure components

## When NOT to Use

- Pure application code changes with no infrastructure impact
- Reviewing Atmos stack YAML without underlying component changes
- Terraform modules that don't create AWS resources (e.g., label/naming modules)
- When the user explicitly asks for a security or compliance review only

## Cost Analysis Process

### Step 1: Resource Inventory

Read all `.tf` files and inventory every resource that incurs AWS charges. Categorize by networking, compute, storage, database, monitoring, and security. See `pricing-reference.md` for resource categories and approximate costs.

### Step 2: Configuration Analysis

For each cost-driving resource, check:

- **Toggleability** -- Is there an `enable_*` variable to disable in dev?
- **Sizing** -- Are instance types, CIDR sizes, counts configurable via variables?
- **Scaling** -- Can counts be reduced (AZs, replicas, NAT gateways)?
- **Retention** -- Are log retention periods configurable and bounded?
- **Tier selection** -- Are storage classes, instance families configurable?
- **Data transfer** -- Are there unnecessary cross-AZ or cross-region transfers?

### Step 3: Environment-Specific Recommendations

For each variable that affects cost, recommend values for dev, staging, and production. See `pricing-reference.md` for common variable patterns.

## Common Cost Traps

| Trap | Typical Monthly Cost | Fix |
|------|---------------------|-----|
| 3 NAT gateways in dev | ~$100 + data transfer | Add `enable_nat_gateway` and `nat_gateway_count` variables |
| Flow logs to CloudWatch (high traffic) | $50-500 at scale | Set bounded `retention_in_days`, consider S3 destination |
| /16 subnets from IPAM | Wastes IP space | Use /20 or /24, make configurable |
| VPC interface endpoints everywhere | $7.50/endpoint/AZ/month | Toggle with `enable_vpc_endpoints`, use free gateway endpoints for S3/DynamoDB |
| Infinite CloudWatch log retention | Grows unbounded | Always set explicit `retention_in_days` |
| EIPs without NAT gateways | $3.60/month each unused | Conditional creation tied to NAT gateway enable flag |
| Cross-AZ data transfer | $0.01/GB | Co-locate when possible, or accept as HA cost |

## Supporting Files

- **`pricing-reference.md`** -- AWS resource pricing, inventory categories, and environment variable patterns
- **`report-template.md`** -- Full output format template for cost review reports
