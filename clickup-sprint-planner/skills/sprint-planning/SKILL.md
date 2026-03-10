---
name: sprint-planning
description: Use when the user asks about sprint planning, syncing plan docs to ClickUp, managing stories/tasks in bulk, or checking sprint status. Triggers on mentions of sprint, sync, stories, ClickUp bulk operations, or epic planning.
---

# Sprint Planning Skill

You have access to the `clickup-sprint-planner` MCP server with these tools:

| Tool | Purpose |
|------|---------|
| `sprint_sync` | Diff plan docs against ClickUp state (read-only) |
| `sprint_bulk_create` | Create multiple tasks + set EPIC relationships |
| `sprint_set_relationship` | Set list_relationship custom fields directly |
| `sprint_bulk_update` | Batch update status/assignee/priority |
| `sprint_status` | Get epic overview with stats |
| `sprint_action_log` | Query past operations |

## Rules

1. **Sync before mutating.** Always call `sprint_sync` first to see the current diff before creating or updating tasks. Present the diff to the user and get confirmation.

2. **Use bulk operations.** Never create tasks one-by-one. Use `sprint_bulk_create` with `set_relationships: true` to create all stories for an epic in one call.

3. **Read config, don't hardcode.** All IDs (list IDs, field IDs, EPIC IDs, user IDs) come from `sprint-planner.json`. Never hardcode ClickUp IDs in tool calls.

4. **Surface errors clearly.** Relationship field operations can fail silently in other tools. Our tools use the direct REST endpoint — if they report failure, it's real. Always show the user which operations succeeded and which failed.

5. **Confirm before mutating.** Before any bulk create, bulk update, or relationship change, show the user exactly what will happen and ask for confirmation.

6. **Log everything.** Actions are logged automatically by the tools. If logging fails, warn the user but don't block the operation.

7. **Present results as tables.** After any operation, show a summary table with task names, IDs, statuses, and any failures.

## Config Location

The project config is at the path specified by `SPRINT_PLANNER_CONFIG` env var, or `./sprint-planner.json`. It contains:

- ClickUp workspace structure (space, folder, lists, relationship field)
- Team members with IDs
- Epic-to-plan-doc mapping with EPIC IDs
- Story extraction selectors
- Action log path

## Workflow: Creating Stories for an Epic

```
1. sprint_sync(epic="P1a")            → see what exists vs what's in the plan doc
2. Present diff table to user         → match / to_create / to_update
3. User confirms which to create
4. sprint_bulk_create(                 → create all at once
     list_id=config.lists.backlog.id,
     stories=[...],
     set_relationships=true
   )
5. Show results table                  → created tasks with IDs and URLs
6. Optionally write IDs back to plan doc
```

## Workflow: Updating Existing Stories

```
1. sprint_sync(epic="P1")             → identify stories that need updates
2. Present diff to user               → which stories are stale or missing content
3. User confirms which to update
4. sprint_bulk_update(                 → update all at once
     updates=[
       { "task_id": "...", "description": "full markdown content", "orderindex": "1000" },
       ...
     ]
   )
5. Show results table                  → updated tasks with success/failure
```

Use this workflow when stories exist in ClickUp but need updated descriptions, reordering, or status changes. The `description` field accepts full markdown — include all required card sections (summary, tasks, context, acceptance criteria).

## Workflow: Sprint Status Check

```
1. sprint_status(group_by="epic")     → overview of all epics
2. Present summary table              → epic / total / done / in_progress / ready
3. User drills into specific epic     → show story-level detail
```

### group_by Options

| Value | Behavior |
|-------|----------|
| `"epic"` (default) | Group by epic with per-epic stats |
| `"status"` | Group by status category (done / in_progress / ready / blocked) |
| `"assignee"` | Group by assignee with per-person stats |

## Task Naming Convention

Tasks should follow this pattern:
```
[Project Name] {EpicID}-S{StoryIndex}: {StoryName}
```
Example: `[My Project] P1a-S1: Create new infrastructure in Production VPC`

## Card Content Requirements

Every story card MUST include a full description with these sections. Never create cards with one-line summaries — they are useless for execution.

### Required Sections

1. **Summary paragraph** — What this story does and why (2-3 sentences)
2. **Tasks** — Checklist of concrete actions using `- [ ]` markdown format. Each task should be specific enough to execute without ambiguity.
3. **Context / Notes** — Key decisions, existing infrastructure IDs, dependencies, gotchas, or references to other stories. Include resource IDs (subnet IDs, ASG names, security group names) where known.
4. **Acceptance Criteria** — Checklist of verifiable outcomes using `- [ ]` markdown format. These should be testable (e.g., "curl ifconfig.me returns the expected NAT IP" not "networking works").

### Optional Sections (include when relevant)

- **Architecture / Diagrams** — ASCII diagrams showing before/after state or traffic flow
- **Terraform / Config snippets** — Reference code from the plan doc
- **Risk Mitigation** — For high-risk stories (e.g., critical service migrations)
- **Static IP / Cross-Epic Notes** — When this story has implications for other epics (e.g., "outbound IPs will change when migrating to EKS in epic P4")

### Example Card Description

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

Stories must be ordered by execution sequence using `orderindex` in ClickUp. This determines the display order in List view and reflects the actual dependency chain.

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
   - ...and so on
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
| `🏷️ Type (Sprint)` | Backlog | User Story, Feature, Task, Bug, Enhancement, Adhoc, DISCOVERY |
| `💣 [Infra] Features` | EPICs | VPC Setup, K8S Migration, Security, etc. |
| `🏷️ [TKT] POD` | Both | Infra, Platform, Experience, etc. |

Field IDs are in the config under `custom_fields`.
