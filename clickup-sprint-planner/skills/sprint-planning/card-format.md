# Card Content & Ordering Reference

## Task Naming Convention

```
[Project Name] {EpicID}-S{StoryIndex}: {StoryName}
```
Example: `[My Project] P1a-S1: Create new infrastructure in Production VPC`

## Required Sections

Every story card MUST include a full description with these sections. Never create cards with one-line summaries — they are useless for execution.

1. **Summary paragraph** — What this story does and why (2-3 sentences)
2. **Tasks** — Checklist of concrete actions using `- [ ]` markdown format. Each task should be specific enough to execute without ambiguity.
3. **Context / Notes** — Key decisions, existing infrastructure IDs, dependencies, gotchas, or references to other stories. Include resource IDs (subnet IDs, ASG names, security group names) where known.
4. **Acceptance Criteria** — Checklist of verifiable outcomes using `- [ ]` markdown format. These should be testable (e.g., "curl ifconfig.me returns the expected NAT IP" not "networking works").

## Optional Sections (include when relevant)

- **Architecture / Diagrams** — ASCII diagrams showing before/after state or traffic flow
- **Terraform / Config snippets** — Reference code from the plan doc
- **Risk Mitigation** — For high-risk stories (e.g., critical service migrations)
- **Static IP / Cross-Epic Notes** — When this story has implications for other epics (e.g., "outbound IPs will change when migrating to EKS in epic P4")

## Example Card Description

```markdown
Create two new private subnets in the default VPC for us-east-1b and us-east-1c.
Associate them with the existing production-private-route-table so they route outbound
traffic through the same NAT Gateway in us-east-1a (Elastic IP 203.0.113.10).

## Tasks
- [ ] Allocate CIDR blocks for new subnets — pick from available ranges in 10.0.0.0/16
- [ ] Create production-private-subnet-b in us-east-1b with MapPublicIpOnLaunch=false
- [ ] Create production-private-subnet-c in us-east-1c with MapPublicIpOnLaunch=false
- [ ] Associate both new subnets with production-private-route-table (rtb-0123456789abcdef0)
- [ ] Verify outbound connectivity (curl ifconfig.me should return 203.0.113.10)

## Existing Infrastructure
- Private Subnet (1a): production-private-subnet-a (subnet-0123456789abcdef0) — EXISTS
- NAT Gateway: nat-0123456789abcdef0 — EXISTS
- Route Table: production-private-route-table (rtb-0123456789abcdef0) — EXISTS

## Acceptance Criteria
- [ ] Two new private subnets created (1b, 1c) with MapPublicIpOnLaunch=false
- [ ] Both subnets associated with production-private-route-table
- [ ] Outbound traffic from both subnets egresses via 203.0.113.10
```

## Card Ordering

Stories must be ordered by execution sequence using `orderindex` in ClickUp.

### Ordering Rules

1. **Order by epic first, then by story index within the epic.** P1 stories come before P1a, which come before P2, etc.
2. **Use `orderindex` values with gaps** (e.g., 1000, 2000, 3000) to allow inserting stories later without renumbering.
3. **Set orderindex via the ClickUp API** when creating or reordering:
   ```
   PUT /api/v2/task/{task_id}
   { "orderindex": "1000" }
   ```
4. **Cross-epic ordering within the same list:** When stories from multiple epics share a list (e.g., [Infra] Backlog), the orderindex must reflect the global execution order across all epics:
   - P1 stories: orderindex 1000-12000
   - P1a stories: orderindex 13000-16000
   - P2 stories: orderindex 17000-22000
5. **When using `sprint_bulk_create`**, set orderindex on each story in the batch to maintain execution order.

### Ordering Convention

```
orderindex = (global_story_sequence) * 1000
```

Where `global_story_sequence` is the story's position in the full cross-epic execution plan (1-indexed). The 1000x multiplier leaves room for inserting stories between existing ones.

## Custom Fields (Not Yet Automated)

The following ClickUp custom fields exist but are **not set automatically** by the sprint tools. Set them manually in the ClickUp UI after creation:

| Field | List | Purpose |
|-------|------|---------|
| `Categorize` | Backlog | Planned, Adhoc, Oncall/Bug, RCA, Tech Optimisation |
| `Type (Sprint)` | Backlog | User Story, Feature, Task, Bug, Enhancement, Adhoc, DISCOVERY |
| `[Infra] Features` | EPICs | VPC Setup, K8S Migration, Security, etc. |
| `[TKT] POD` | Both | Infra, Platform, Experience, etc. |

Field IDs are in the config under `custom_fields`.
