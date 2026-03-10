# Future: sprint-retro & sprint-report

Status: **planned** | Created: 2026-03-02

Two new skills/tools to close the feedback loop between ClickUp and plan documents.

---

## 1. sprint-retro (reverse sync: ClickUp → plan docs)

### Problem

Sync is currently one-way: plan docs → ClickUp. As work progresses, ClickUp task statuses change ("ready for dev" → "in dev" → "done") but the plan doc badges stay stale. There's no way to see actual progress by looking at the HTML plan docs.

### Proposed solution

A new MCP tool `sprint_retro` and `/sprint-retro` command that:

1. For each epic, fetches ClickUp task statuses via the existing `clickup_id` badges in plan docs
2. Compares ClickUp status against the plan doc badge status
3. Reports diffs (e.g., "S3 plan says `ready_for_dev` but ClickUp says `done`")
4. Optionally updates the plan doc status badges to match ClickUp

### Implementation notes

**New MCP tool: `sprint_retro`**
- Params: `epic` (optional), `apply` (bool, default false)
- Read-only by default — returns diff. Set `apply: true` to write changes.
- Uses the existing `HtmlPlanParser` to read current plan doc status
- Fetches task status from ClickUp by ID (already linked after writeback)
- Updates `<span class="badge badge-{status}">` in both summary table and story detail

**HTML badge mapping** (ClickUp status → CSS class):
```
ready for dev  → badge-ready
in dev         → badge-in-dev
in review      → badge-in-review
done           → badge-done
closed         → badge-done
```

**New skill file: `commands/sprint-retro.md`**
```
/sprint-retro [epic]     # Show what changed in ClickUp since last sync
/sprint-retro P1a apply  # Update P1a plan doc badges to match ClickUp
```

**Changes to existing code:**
- `server/parsers/html_parser.py` — add `write_status(file_path, story_index, new_status)` method
- `server/parsers/base.py` — add `write_status` to `PlanParser` ABC
- `server/tools/` — new `retro.py` module
- `server/main.py` — register retro tool

**Summary table row update:**
The summary table currently has a status column with badges. Retro should update these too, not just the story detail section. Pattern:
```html
<!-- Before -->
<td><span class="badge badge-ready">ready for dev</span></td>
<!-- After -->
<td><span class="badge badge-done">done</span></td>
```

**Also update the `<tr class="to-create">` → remove class when task exists.**

---

## 2. sprint-report (status report generation)

### Problem

Generating sprint/epic status reports requires manually checking ClickUp, counting stories by status, figuring out who's working on what, and writing it up. This is tedious for standups and weekly updates.

### Proposed solution

A new MCP tool `sprint_report` and `/sprint-report` command that generates a formatted status report from live ClickUp data.

### Implementation notes

**New MCP tool: `sprint_report`**
- Params: `epic` (optional), `format` ("markdown" | "summary"), `group_by` ("status" | "assignee" | "epic")
- Fetches tasks from ClickUp backlog (reuses existing `get_tasks_by_list` with pagination)
- Aggregates by requested grouping
- Returns structured data that the skill formats into a readable report

**Report content:**

```markdown
## Sprint Report — P1: VPC Architecture & IPAM
Generated: 2026-03-02

### Progress
[████████░░] 67% (8/12 stories)

### By Status
| Status       | Count | Stories |
|-------------|-------|---------|
| done        | 2     | S1, S2  |
| in dev      | 2     | S3, S4  |
| ready for dev | 8   | S5-S12  |

### By Assignee
| Assignee        | Total | Done | In Progress | Ready |
|----------------|-------|------|-------------|-------|
| Alice          | 8     | 1    | 2           | 5     |
| Bob            | 4     | 1    | 0           | 3     |

### Blocked / At Risk
- None identified

### Notes
- S3 (VPC module) and S4 (VPC creation) in active development
- S7-S8, S11-S12 created this sprint, not yet assigned
```

**All-epics summary mode:**
When no epic is specified, generate a high-level overview:
```
| Epic  | Stories | Done | In Progress | Ready | % Complete |
|-------|---------|------|-------------|-------|------------|
| P1    | 12      | 2    | 2           | 8     | 17%        |
| P1a   | 5       | 0    | 0           | 5     | 0%         |
| ...   | ...     | ...  | ...         | ...   | ...        |
```

**New skill file: `commands/sprint-report.md`**
```
/sprint-report           # All-epics overview
/sprint-report P1        # Detailed report for epic P1
/sprint-report P1 P1a    # Multiple epics
```

**Changes to existing code:**
- `server/tools/` — new `report.py` module (or extend `sprint_status.py`)
- `server/main.py` — register report tool
- Reuses `sprint_status` data fetching but with richer formatting

**Difference from `sprint_status`:**
`sprint_status` returns raw structured data. `sprint_report` is presentation-focused — it formats the data into a human-readable report with progress bars, percentages, and actionable notes. The skill/command layer formats the tool output into the final markdown.

---

## Dependencies

Both features depend on ClickUp IDs being present in plan docs (completed via writeback in session 2026-03-02).

### Build order

1. `sprint_retro` first — it's the higher-value feature (keeps plan docs alive)
2. `sprint_report` second — extends existing `sprint_status` with better formatting

### Estimated scope

- `sprint_retro`: ~150 lines new code + parser method + command file
- `sprint_report`: ~100 lines new code + command file (reuses status data fetching)
