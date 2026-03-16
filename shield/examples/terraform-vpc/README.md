# Terraform VPC Example

A sample Terraform VPC module that demonstrates Shield's full pipeline.

## What This Shows

This example walks through Shield's pipeline phases using a Terraform VPC module with intentional issues for reviewers to find:

- **Security issues**: Open SSH port, wildcard IAM policy, missing encryption
- **Cost issues**: 3 NAT gateways without disable toggle, no log retention
- **Architecture issues**: Missing IPAM pool hierarchy, no deletion protection
- **Operations issues**: No backup config, missing monitoring

## Pipeline Walkthrough

### 1. Research (`/research`)
Research AWS VPC best practices, IPAM patterns, and multi-AZ networking.

### 2. Planning (`/plan`)
Generate an architecture doc and execution plan with stories for the VPC module.

### 3. Plan Review (`/plan-review`)
Shield dispatches reviewer agents to evaluate the plan:
- Security reviewer checks for threat model coverage
- Architecture reviewer checks service topology
- Cost reviewer checks environment tiering
- DX engineer checks story actionability

### 4. PM Sync (`/pm-sync`)
Sync stories from the plan sidecar JSON to ClickUp (or skip if no PM configured).

### 5. AC Confirmation (`/implement`)
Before implementation, Shield presents acceptance criteria for confirmation.

### 6. Implementation (`/implement`)
TDD-based implementation with lightweight review after each step.

### 7. Code Review (`/review`)
Comprehensive review with all agents:
- Security reviewer finds the wildcard IAM policy and open SSH port
- Cost reviewer flags the 3 NAT gateways
- Architecture reviewer checks Terraform structure
- AC verification confirms criteria are met

### 8. Final Review
Consolidated review across all stories with full agent suite.

## Try It

1. Install Shield: `/plugin install shield@tesseract`
2. `cd` into this directory
3. Run `/research VPC best practices for multi-AZ deployment`
4. Follow the pipeline from there

## Source Files

- `src/main.tf` — VPC module with intentional issues
- `src/variables.tf` — Input variables
- `src/outputs.tf` — Module outputs
- `src/versions.tf` — Provider requirements
- `.shield.json` — Shield project marker
