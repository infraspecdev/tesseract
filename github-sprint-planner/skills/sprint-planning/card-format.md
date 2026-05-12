# Card Content Reference (GitHub Issues)

## Issue Title Convention

```
{EpicID} - {StoryName}
```
Example: `P1a - Create new ECS infrastructure in Production VPC`

## Required Sections

Every issue body MUST include these sections. Never create issues with one-line bodies — they are useless for execution.

1. **Summary paragraph** — What this story does and why (2-3 sentences)
2. **## Tasks** — Checklist of concrete actions using `- [ ]` markdown format. Each task specific enough to execute without ambiguity.
3. **## Context / Notes** — Key decisions, existing infrastructure IDs, dependencies, gotchas, or references to other stories.
4. **## Acceptance Criteria** — Checklist of verifiable outcomes using `- [ ]` markdown format.

## Example Issue Body

```markdown
Create two new private subnets in the default VPC for us-east-1b and us-east-1c.
Associate them with the existing production-private-route-table so they route outbound
traffic through the same NAT Gateway in us-east-1a (Elastic IP 203.0.113.10).

## Tasks
- [ ] Allocate CIDR blocks for new subnets from available ranges in 10.0.0.0/16
- [ ] Create production-private-subnet-b in us-east-1b with MapPublicIpOnLaunch=false
- [ ] Create production-private-subnet-c in us-east-1c with MapPublicIpOnLaunch=false
- [ ] Associate both subnets with production-private-route-table (rtb-0123456789abcdef0)
- [ ] Verify outbound connectivity (curl ifconfig.me should return 203.0.113.10)

## Context / Notes
- Private Subnet (1a): production-private-subnet-a (subnet-0123456789abcdef0) — EXISTS
- NAT Gateway: nat-0123456789abcdef0 — EXISTS
- Route Table: production-private-route-table (rtb-0123456789abcdef0) — EXISTS

## Acceptance Criteria
- [ ] Two new private subnets created (1b, 1c) with MapPublicIpOnLaunch=false
- [ ] Both subnets associated with production-private-route-table
- [ ] Outbound traffic from both subnets egresses via 203.0.113.10
```
