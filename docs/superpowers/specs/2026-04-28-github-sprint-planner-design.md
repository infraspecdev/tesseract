# Design: github-sprint-planner plugin

**Date:** 2026-04-28
**Issue:** https://github.com/infraspecdev/tesseract/issues/27
**Status:** Implemented (v1.0.0)

---

## Problem

The `clickup-sprint-planner` plugin solves sprint planning for ClickUp-based teams: parse HTML/markdown plan docs, diff against the task tracker, bulk-create stories with correct naming/relationships, and track progress. Teams using **GitHub Issues + Projects v2** have no equivalent.

---

## Decision

Build a **separate plugin** `github-sprint-planner/` — a structural mirror of `clickup-sprint-planner/` with a GitHub backend. No shared code between plugins at this stage; clean enough to extract a shared core later (Option B future work).

---

## Architecture

### Plugin structure

```
github-sprint-planner/
├── .claude-plugin/plugin.json
├── .mcp.json
├── commands/
│   ├── sprint-sync.md
│   ├── sprint-plan.md
│   └── sprint-status.md
├── skills/sprint-planning/
│   ├── SKILL.md
│   └── card-format.md
├── examples/sprint-planner.example.json
├── server/
│   ├── main.py
│   ├── github_client.py
│   ├── config.py
│   ├── action_log.py           # copied from clickup plugin
│   ├── parsers/                # copied from clickup plugin
│   │   ├── base.py             # Story.clickup_id renamed to Story.issue_number
│   │   ├── html_parser.py
│   │   └── markdown_parser.py
│   └── tools/
│       ├── sync.py
│       ├── bulk_create.py
│       ├── bulk_update.py
│       ├── bulk_rename.py          # added post-design: epic prefix enforcement
│       ├── sprint_status.py
│       ├── action_log_tool.py
│       └── _helpers.py
├── pyproject.toml
└── README.md
```

### Layer responsibilities

| Layer | File(s) | Responsibility |
|-------|---------|----------------|
| Entry | `main.py` | Load config, create client, register tools, run MCP server |
| Config | `config.py` | Parse `sprint-planner.json` into Pydantic models |
| API client | `github_client.py` | GitHub REST + GraphQL calls, no business logic |
| Parsers | `parsers/` | Read HTML/markdown plan docs → `list[Story]` — GitHub-agnostic |
| Tools | `tools/` | Sprint logic: diff, create, update, status |
| Logging | `action_log.py` | Append-only JSON log of all mutations |

---

## Config shape

```json
{
  "version": "1",
  "github": {
    "token_env": "GITHUB_TOKEN",
    "owner": "infraspecdev",
    "repo": "my-repo",
    "project_number": 5
  },
  "team": [
    { "name": "Alice", "github_login": "alice" }
  ],
  "plan_docs": {
    "format": "html",
    "base_path": "./epics",
    "epics": [
      {
        "id": "P1",
        "name": "Epic 1: VPC Setup",
        "plan_doc": "01-epic/detailed-plan.html",
        "epic_issue_number": 42
      }
    ]
  },
  "story_extraction": {
    "html": {
      "story_selector": "div.story[id^='story-']",
      "name_pattern": "Story \\d+: (.+)",
      "github_issue_selector": "a.badge-github",
      "status_selector": ".badge:not(.badge-github):not(.badge-to-create)"
    }
  },
  "action_log": { "path": "./epics/github_actions.json" }
}
```

**Key differences from ClickUp config:**
- `github` block replaces `clickup` block — `owner`, `repo`, `project_number` instead of `workspace_id`, `space`, `folder`, `lists`, `relationship_field`
- `epic_issue_number` (GitHub issue number) instead of `epic_id` (ClickUp task ID)
- `github_login` instead of numeric ClickUp user ID
- No `custom_fields` — GitHub Projects v2 fields handled separately if needed

---

## GitHub API mapping

| Operation | ClickUp | GitHub |
|-----------|---------|--------|
| Create story | `POST /list/{id}/task` | `POST /repos/{owner}/{repo}/issues` |
| Update story | `PUT /task/{id}` | `PATCH /repos/{owner}/{repo}/issues/{number}` |
| Fetch stories | `GET /list/{id}/task` (paginated) | `GET /repos/{owner}/{repo}/issues` (paginated) |
| Link to epic | `POST /task/{id}/field/{field_id}` (relationship field) | `POST /repos/{owner}/{repo}/issues/{epic}/sub_issues` |
| Add to sprint | N/A (list membership) | GraphQL: add to Projects v2 + set iteration field |
| Status update | `PUT /task/{id}` with `status` | `PATCH /repos/{owner}/{repo}/issues/{number}` with `state` + label |

**Projects v2 requires GraphQL** — `add_item_to_project`, `set_field_value` (for iteration). The `github_client.py` must handle both REST and GraphQL endpoints.

---

## Tool: `sprint_sync`

```
sprint_sync(epic="P1a", apply_links=False)

1. Load config → get epic config for "P1a" (epic_issue_number=42)
2. Parse plan doc → list[Story] via parsers/
3. Fetch GitHub issues that are sub-issues of epic #42
   GET /repos/{owner}/{repo}/issues/{epic}/sub_issues
4. Match stories ↔ issues:
   - Exact: story.issue_number == issue.number       → "match" or "to_update"
   - Fuzzy: name similarity >= 0.8                   → "match"
   - Fuzzy: name similarity >= 0.6 but not linked    → "to_link"
   - No match                                         → "to_create"
5. Return diff table
```

## Tool: `sprint_bulk_create`

```
sprint_bulk_create(epic_issue_number, stories, add_to_project=True, iteration_id=None)

For each story:
1. POST /repos/{owner}/{repo}/issues  → create issue
2. POST /repos/{owner}/{repo}/issues/{epic}/sub_issues  → link to epic
3. GraphQL: addProjectV2ItemById  → add to project board
4. GraphQL: updateProjectV2ItemFieldValue  → set iteration (if iteration_id provided)
5. action_log.log_action("bulk_create", ...)
```

## Tool: `sprint_bulk_update`

```
sprint_bulk_update(updates=[{issue_number, assignee, labels, state}])

For each update:
  PATCH /repos/{owner}/{repo}/issues/{number}
  action_log.log_action("bulk_update", ...)
```

## Tool: `sprint_status`

```
sprint_status(epic=None, group_by="epic")

1. For each epic: GET /repos/{owner}/{repo}/issues/{epic}/sub_issues → issues linked to that epic
2. GraphQL: get project items to enrich with iteration/status fields
3. Compute stats: open / closed / in-progress
4. Return table grouped by epic / status / assignee
```

---

## Authentication

Try `GITHUB_TOKEN` env var first, fall back to `gh auth token` output. Raise a clear error if neither is available.

```python
token = os.environ.get("GITHUB_TOKEN") or _get_gh_cli_token()
```

---

## Parser changes

`parsers/base.py` — rename `Story.clickup_id` → `Story.issue_number` (int | None). Update `write_clickup_id` → `write_issue_number`. This is the only change needed to the parser layer.

---

## Commands (mirror ClickUp exactly)

- `/sprint-sync [epic]` — diff plan doc vs GitHub Issues
- `/sprint-plan` — assign, prioritize, push to GitHub
- `/sprint-status [epic]` — project board overview

---

## Action log

Same append-only JSON format as ClickUp plugin. Actions: `bulk_create`, `bulk_update`, `sync_auto_link`.

---

## Future: Option B (shared core)

When extracting a shared core, the natural split is:
- **Shared:** `parsers/`, `action_log.py`, `config.py` base models (`TeamMember`, `EpicConfig`, `PlanDocsConfig`, `StoryExtractionConfig`)
- **Provider-specific:** `*_client.py`, `config.py` provider block, `tools/`

The current design keeps these boundaries clean to make this extraction straightforward.

---

## Out of scope

- GitHub Milestones as sprints (chose Projects v2 Iterations instead)
- GitHub App authentication (PAT / gh CLI token is sufficient)
- `/sprint-retro` and `/sprint-report` (planned for ClickUp plugin, not in initial GitHub scope)
- Markdown plan doc writeback of GitHub issue numbers (can be added later, same pattern as ClickUp)
