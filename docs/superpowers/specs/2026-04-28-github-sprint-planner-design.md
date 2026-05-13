# Design: github-sprint-planner plugin

**Date:** 2026-04-28
**Issue:** https://github.com/infraspecdev/tesseract/issues/27
**Status:** Implemented (v1.0.0)

---

## Problem

Teams using GitHub Issues + Projects v2 have no way to bulk-create sprint stories from plan documents, link them to epics as sub-issues, and add them to a project board — all in one shot. Doing this manually means 40+ permission approvals and copy-pasting from a plan doc into GitHub one issue at a time.

---

## Decision

Build a Claude Code plugin `github-sprint-planner/` — a Python MCP server that reads sprint plan documents (HTML or markdown), diffs them against existing GitHub Issues, and bulk-creates stories with sub-issue linking and Projects v2 support.

---

## Architecture

### Plugin structure

```
github-sprint-planner/
├── .claude-plugin/plugin.json        # Plugin manifest
├── .mcp.json                         # Tells Claude Code how to start the MCP server
├── .gitignore                        # Excludes sprint-planner.json and epics/
├── commands/
│   ├── sprint-sync.md                # /sprint-sync command
│   ├── sprint-plan.md                # /sprint-plan command
│   └── sprint-status.md              # /sprint-status command
├── skills/sprint-planning/
│   ├── SKILL.md                      # Auto-invoked skill
│   └── card-format.md                # Issue body format reference
├── examples/sprint-planner.example.json
├── server/
│   ├── main.py                       # FastMCP entry point, registers all tools
│   ├── github_client.py              # GitHub REST v3 + GraphQL v4 wrapper
│   ├── config.py                     # Pydantic models for sprint-planner.json
│   ├── action_log.py                 # Append-only JSON log of all mutations
│   ├── parsers/
│   │   ├── base.py                   # Story dataclass + parser interface
│   │   ├── html_parser.py            # Parses HTML plan docs via BeautifulSoup
│   │   └── markdown_parser.py        # Markdown stub
│   └── tools/
│       ├── sync.py                   # sprint_sync tool
│       ├── bulk_create.py            # sprint_bulk_create tool
│       ├── bulk_update.py            # sprint_bulk_update tool
│       ├── bulk_rename.py            # sprint_bulk_rename tool
│       ├── sprint_status.py          # sprint_status tool
│       ├── action_log_tool.py        # sprint_action_log tool
│       └── _helpers.py               # Shared status normalisation
├── pyproject.toml
└── README.md
```

### Layer responsibilities

| Layer | File(s) | Responsibility |
|-------|---------|----------------|
| Entry | `main.py` | Load config, create client, register tools, run MCP server |
| Config | `config.py` | Parse `sprint-planner.json` into Pydantic models |
| API client | `github_client.py` | GitHub REST + GraphQL calls, no business logic |
| Parsers | `parsers/` | Read HTML/markdown plan docs → `list[Story]` |
| Tools | `tools/` | Sprint logic: diff, create, update, rename, status |
| Logging | `action_log.py` | Append-only JSON log of all mutations with rollback info |

---

## Config shape

```json
{
  "version": "1",
  "github": {
    "token_env": "GITHUB_TOKEN",
    "owner": "your-org",
    "repo": "your-repo",
    "project_number": 49
  },
  "team": [
    { "name": "Alice", "github_login": "alice" }
  ],
  "plan_docs": {
    "format": "html",
    "base_path": "./epics",
    "epics": [
      {
        "id": "E26",
        "name": "Multi account CUR data",
        "plan_doc": "multi-account-cur/plan.html",
        "epic_issue_number": 26
      }
    ]
  },
  "story_extraction": {
    "html": {
      "story_selector": "div.story[id^='story-']",
      "name_pattern": "Story \\d+: (.+)",
      "issue_selector": "a.badge-github",
      "status_selector": ".badge:not(.badge-github):not(.badge-to-create)"
    }
  },
  "action_log": { "path": "./epics/github_actions.json" }
}
```

---

## GitHub API mapping

| Operation | Endpoint |
|-----------|----------|
| Create issue | `POST /repos/{owner}/{repo}/issues` |
| Update issue | `PATCH /repos/{owner}/{repo}/issues/{number}` |
| Fetch sub-issues | `GET /repos/{owner}/{repo}/issues/{epic}/sub_issues` |
| Link sub-issue | `POST /repos/{owner}/{repo}/issues/{epic}/sub_issues` |
| Add to project | GraphQL: `addProjectV2ItemById` |
| Set iteration | GraphQL: `updateProjectV2ItemFieldValue` |

Projects v2 requires GraphQL — `github_client.py` handles both REST and GraphQL.

---

## Tools

### `sprint_sync`
1. Load config → get epic config (epic_issue_number)
2. Parse plan doc → `list[Story]`
3. Fetch sub-issues of the epic from GitHub
4. Match stories ↔ issues (exact by issue number, fuzzy by name)
5. Return diff: `match / to_create / to_update / to_link`

### `sprint_bulk_create`
For each story:
1. `POST /repos/{owner}/{repo}/issues` → create issue
2. `POST /repos/{owner}/{repo}/issues/{epic}/sub_issues` → link to epic
3. GraphQL: `addProjectV2ItemById` → add to project board
4. GraphQL: `updateProjectV2ItemFieldValue` → set iteration (if provided)
5. Log action with rollback info

### `sprint_bulk_update`
For each update: `PATCH /repos/{owner}/{repo}/issues/{number}` + log action

### `sprint_bulk_rename`
1. Fetch sub-issues for each epic
2. Compare current title against `naming.story_format`
3. Preview mode (default): return list of proposed renames
4. Apply mode: `PATCH` each non-compliant title + log action with rollback

### `sprint_status`
1. For each epic: fetch sub-issues
2. Normalise state + labels → status (open/in-progress/done/blocked)
3. Return table grouped by epic/status/assignee

---

## Authentication

Tries `GITHUB_TOKEN` env var first, falls back to `gh auth token` output.

```python
token = os.environ.get("GITHUB_TOKEN") or _get_gh_cli_token()
```
