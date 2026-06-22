# Shield GitHub Adapter

GitHub Issues + Projects v2 PM adapter for Shield. Implements the `pm_*` tool interface so Shield's sprint planning commands (`/pm-status`, `/pm-sync`) work against GitHub repos.

## How it fits in

```
shield/
└── adapters/
    ├── clickup/   ← ClickUp adapter (same interface)
    └── github/    ← this adapter
```

When you run `/shield init` and select `github` as your PM tool, Shield wires this adapter's MCP server into your session. All `pm_*` tools then talk to GitHub instead of ClickUp — the commands are identical.

## Setup

### 1. Prerequisites

- `uv` installed (`brew install uv`)
- GitHub token with `repo` + `project` scopes, **or** `gh` CLI authenticated (`gh auth login`)

### 2. Token resolution (automatic)

The adapter resolves your token in this order:

1. `github.api_token` in `~/.shield/credentials.json`
2. `GITHUB_TOKEN` environment variable
3. `gh auth token` CLI fallback (works out of the box if you use `gh`)

### 3. Shield-native config (recommended)

Create `.shield.json` in your project root:

```json
{ "project": "my-project" }
```

Create `~/.shield/projects/my-project/pm.json`:

```json
{
  "owner": "infraspecdev",
  "repo": "aws-cost-analytics-ruby-backend",
  "project_number": 49,
  "naming": {
    "story_format": "[{epic_id}] {name}"
  },
  "epics": [
    {
      "id": "E26",
      "name": "Multi account CUR data",
      "epic_issue_number": 26,
      "plan_doc": "docs/epics/e26.html"
    }
  ],
  "team": [
    { "name": "Rahul", "github_login": "rahul-infra" }
  ]
}
```

`project_number` is optional — only needed for Projects v2 board operations. Leave it as `0` if you only use Issues.

### 4. Legacy config (standalone mode)

Create `sprint-planner.json` in the project root (or set `SPRINT_PLANNER_CONFIG` env var):

```json
{
  "github": {
    "owner": "infraspecdev",
    "repo": "aws-cost-analytics-ruby-backend",
    "project_number": 49
  },
  "plan_docs": {
    "format": "html",
    "base_path": "./epics",
    "epics": [
      {
        "id": "E26",
        "name": "Multi account CUR data",
        "epic_issue_number": 26,
        "plan_doc": "e26.html"
      }
    ]
  },
  "naming": {
    "story_format": "[{epic_id}] {name}"
  }
}
```

See `../../config-examples/pm-github.example.json` for a minimal template.

## Tools

| Tool | Description |
|------|-------------|
| `pm_get_capabilities` | Returns adapter name, mode, and list of supported tools |
| `pm_get_status` | Epic overview — sub-issue counts, states, assignees. Group by epic/status/assignee |
| `pm_sync` | Diffs plan HTML doc against GitHub Issues — finds missing stories, title mismatches |
| `pm_bulk_create` | Creates multiple issues and links them as sub-issues of their epic |
| `pm_bulk_update` | Batch update assignees, labels, or state on multiple issues |
| `pm_bulk_rename` | Preview or apply epic prefix renames on issue titles |
| `pm_link_story_to_epic` | Links existing issues as sub-issues of a parent epic issue |
| `pm_action_log` | Query history of all actions taken in this session |

## Running locally (without plugin install)

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "shield-pm-adapter": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/tesseract/shield/adapters/github",
        "python",
        "server/main.py"
      ]
    }
  }
}
```

## Running tests

```bash
cd shield/adapters/github
uv run pytest tests/ -v
```

## Config reference

### `pm.json` / `sprint-planner.json` fields

| Field | Required | Description |
|-------|----------|-------------|
| `owner` | yes | GitHub org or user login |
| `repo` | yes | Repository name |
| `project_number` | no | GitHub Projects v2 number (0 = disabled) |
| `naming.story_format` | no | Issue title template. Placeholders: `{epic_id}`, `{name}` |
| `epics[].id` | yes | Short epic ID (e.g. `E26`) used in naming and filtering |
| `epics[].epic_issue_number` | yes | The GitHub issue number that acts as the epic |
| `epics[].plan_doc` | yes (for sync) | Path to the HTML plan doc, relative to `base_path` |
| `team[].github_login` | no | Used to resolve login → display name in status output |
