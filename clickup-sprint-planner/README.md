# clickup-sprint-planner

Claude Code plugin for sprint planning with ClickUp. Provides bulk operations, relationship field support (that actually works), plan document sync, and action logging.

## Why

The built-in ClickUp MCP server has critical gaps:

- **Relationship fields silently fail** via `update_task` — this plugin uses the direct `POST /task/{id}/field/{field_id}` endpoint
- **No bulk operations** — creating 40+ stories one-by-one requires 40 permission approvals
- **No plan-doc awareness** — stories in HTML plan docs must be manually transcribed to ClickUp

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the MCP server runs via `uv run`. Install with:
  ```bash
  brew install uv
  ```
  Or: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Install

```bash
# From the plugin directory
claude --plugin-dir ./clickup-sprint-planner
```

Or add to your Claude Code settings to load automatically.

## Setup

1. **Get a ClickUp personal API token** from Settings > Apps > API Token

2. **Set the environment variable:**
   ```bash
   export CLICKUP_API_TOKEN=pk_XXXXXXXXX_YYYYYYYYYYYYYYYYYYYY
   ```

3. **Copy and edit the config:**
   ```bash
   cp examples/sprint-planner.json ./sprint-planner.json
   # Edit with your workspace IDs, lists, epics, and team members
   ```

4. **Set the config path** (or place at `./sprint-planner.json`):
   ```bash
   export SPRINT_PLANNER_CONFIG=/path/to/sprint-planner.json
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/sprint-sync [epic]` | Diff plan docs against ClickUp, optionally create/update tasks |
| `/sprint-plan` | Interactive sprint planning — assign, prioritize, push |
| `/sprint-status [epic]` | Epic overview with story-level detail |

## MCP Tools

| Tool | Description |
|------|-------------|
| `sprint_sync` | Read-only diff of plan docs vs ClickUp state |
| `sprint_bulk_create` | Create multiple tasks + set EPIC relationships |
| `sprint_set_relationship` | Set `list_relationship` fields directly |
| `sprint_bulk_update` | Batch update status/assignee/priority |
| `sprint_status` | Aggregated epic/status/assignee overview |
| `sprint_action_log` | Query the append-only action log |

## Config

See `examples/sprint-planner.json` for a complete example. Key sections:

- **clickup** — workspace structure: space, folder, lists, relationship field ID
- **team** — team members with ClickUp user IDs
- **plan_docs** — format, base path, epic-to-plan-doc mapping with EPIC IDs
- **story_extraction** — CSS selectors/regex for parsing plan documents
- **action_log** — path to the append-only JSON log

## Development

```bash
# Install dependencies
uv sync

# Run the MCP server directly (stdio mode)
cd server && uv run main.py

# Test with Claude Code
claude --plugin-dir .
```

### Adding a new plan doc format

1. Create `server/parsers/my_format_parser.py` implementing `PlanParser`
2. Register it in `server/parsers/base.py:get_parser()`
3. Add extraction config under `story_extraction` in your config file
