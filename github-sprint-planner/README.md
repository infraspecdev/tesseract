# github-sprint-planner

Claude Code plugin for sprint planning with GitHub Issues + Projects v2. Provides bulk operations, sub-issue linking, plan document sync, and action logging.

## Why

Teams already writing sprint plan documents (HTML/markdown) shouldn't have to manually create 40+ GitHub issues, link them to epics as sub-issues, and add them to a project iteration one by one.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the MCP server runs via `uv run`. Install with:
  ```bash
  brew install uv
  ```
- **GitHub token** — Personal Access Token with `repo`, `project` (full control), and `read:org` scopes. Or use `gh auth login` and the token is picked up automatically.

## Install

```bash
claude --plugin-dir ./github-sprint-planner
```

## Setup

1. **Authenticate with GitHub** (recommended — no manual token needed):
   ```bash
   gh auth login
   # Choose: GitHub.com → HTTPS → Paste an authentication token
   # Token needs scopes: repo, project (full control), read:org
   ```
   Or set a token manually:
   ```bash
   export GITHUB_TOKEN=ghp_XXXXXXXXX
   ```

2. **Install dependencies:**
   ```bash
   cd github-sprint-planner
   uv sync
   ```

3. **Copy and edit the config:**
   ```bash
   cp examples/sprint-planner.example.json ./sprint-planner.json
   # Edit with your org, repo, project number, epics, and team
   ```

4. **Set the config path** (or place at `./sprint-planner.json`):
   ```bash
   export SPRINT_PLANNER_CONFIG=/path/to/sprint-planner.json
   ```

## Usage

Once the plugin is loaded (`claude --plugin-dir ./github-sprint-planner`):

1. **Check sprint status:**
   ```
   /sprint-status
   ```
   Shows all epics with story counts, assignees, and progress.

2. **Sync a plan doc to GitHub Issues:**
   ```
   /sprint-sync E26
   ```
   Diffs your plan doc against existing GitHub Issues. Shows what will be created — no writes until you confirm.

3. **Interactive sprint planning:**
   ```
   /sprint-plan
   ```
   Assign stories to team members, set labels, push to GitHub.

4. **Enforce issue title format (preview first, then apply):**
   ```
   Use sprint_bulk_rename with epic="E26" and apply=false
   Use sprint_bulk_rename with epic="E26" and apply=true
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/sprint-sync [epic]` | Diff plan docs against GitHub Issues, optionally create/update/link |
| `/sprint-plan` | Interactive sprint planning — assign, label, push |
| `/sprint-status [epic]` | Epic overview with story-level detail |

## MCP Tools

| Tool | Description |
|------|-------------|
| `sprint_sync` | Read-only diff of plan docs vs GitHub Issues |
| `sprint_bulk_create` | Create multiple issues + link as sub-issues + add to project |
| `sprint_bulk_update` | Batch update assignees/labels/state |
| `sprint_bulk_rename` | Preview or apply epic prefix renames on issue titles |
| `sprint_status` | Aggregated epic/status/assignee overview |
| `sprint_action_log` | Query the append-only action log |

## Config

See `examples/sprint-planner.example.json` for a complete example. Key sections:

- **github** — repo owner, repo name, Projects v2 project number
- **team** — team members with GitHub logins
- **plan_docs** — format, base path, epic-to-plan-doc mapping with parent issue numbers
- **story_extraction** — CSS selectors/regex for parsing plan documents
- **action_log** — path to the append-only JSON log

## Development

```bash
uv sync
cd server && uv run main.py
```

### Adding a new plan doc format

1. Create `server/parsers/my_format_parser.py` implementing `PlanParser`
2. Register it in `server/parsers/base.py` inside `get_parser()`
3. Add extraction config under `story_extraction` in your `sprint-planner.json`
