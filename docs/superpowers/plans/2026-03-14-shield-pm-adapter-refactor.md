# Shield PM Adapter Refactor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the ClickUp MCP server to `shield/adapters/clickup/`, rename tools to the `pm_*` interface, add `pm_get_capabilities`, and update config loading to use `~/.tesseract/`.

**Architecture:** Copy the existing Python MCP server, rename tool functions to match the abstract PM interface, update config loading to read from the new `~/.tesseract/` config paths, and add a capabilities discovery tool. The server code stays Python with the same dependencies (mcp[cli], httpx, beautifulsoup4, pydantic).

**Tech Stack:** Python (MCP server), JSON (config, .mcp.json)

---

## Chunk 1: Copy and Configure

### Task 1: Copy server code to shield/adapters/clickup/

**Files:**
- Copy entire `clickup-sprint-planner/server/` → `shield/adapters/clickup/server/`
- Copy `clickup-sprint-planner/pyproject.toml` → `shield/adapters/clickup/pyproject.toml`

- [ ] **Step 1: Copy all server files**

Copy the entire `server/` directory and `pyproject.toml` from the existing clickup-sprint-planner. This is a verbatim copy — no changes yet.

```bash
cp -r /path/to/tesseract/clickup-sprint-planner/server shield/adapters/clickup/server
cp /path/to/tesseract/clickup-sprint-planner/pyproject.toml shield/adapters/clickup/pyproject.toml
```

- [ ] **Step 2: Remove .gitkeep from adapters/clickup/**

- [ ] **Step 3: Commit**

```
feat: copy clickup MCP server to shield adapter directory

Verbatim copy of the existing clickup-sprint-planner server code
and pyproject.toml. Will be refactored to pm_* interface in
subsequent commits.
```

### Task 2: Create .mcp.json for ClickUp adapter

**Files:**
- Create: `shield/adapters/clickup/.mcp.json`

- [ ] **Step 1: Create .mcp.json**

```json
{
  "mcpServers": {
    "clickup": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.clickup.com/mcp"]
    },
    "shield-pm-adapter": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}/adapters/clickup", "python", "server/main.py"]
    }
  }
}
```

Note: renamed from `clickup-sprint-planner` to `shield-pm-adapter` since the session-start hook copies this to the plugin root.

- [ ] **Step 2: Commit**

```
feat: add clickup adapter MCP server config
```

### Task 3: Update pyproject.toml

**Files:**
- Modify: `shield/adapters/clickup/pyproject.toml`

- [ ] **Step 1: Update project metadata**

Change:
- `name` from `clickup-sprint-planner` to `shield-clickup-adapter`
- `description` to reflect it's a PM adapter
- `version` to `2.0.0`
- Keep all dependencies the same

- [ ] **Step 2: Commit**

```
chore: update clickup adapter pyproject.toml metadata
```

## Chunk 2: Rename Tools to pm_* Interface

### Task 4: Rename tool functions

**Files:**
- Modify: `shield/adapters/clickup/server/tools/sync.py`
- Modify: `shield/adapters/clickup/server/tools/bulk_create.py`
- Modify: `shield/adapters/clickup/server/tools/bulk_update.py`
- Modify: `shield/adapters/clickup/server/tools/sprint_status.py`
- Modify: `shield/adapters/clickup/server/tools/relationships.py`
- Modify: `shield/adapters/clickup/server/tools/rename.py`
- Modify: `shield/adapters/clickup/server/tools/action_log_tool.py`
- Modify: `shield/adapters/clickup/server/main.py`

- [ ] **Step 1: Rename tool function names in each tool module**

In each file, rename the `@mcp.tool()` decorated function:

| File | Old function name | New function name |
|------|------------------|-------------------|
| `sync.py` | `sprint_sync` | `pm_sync` |
| `bulk_create.py` | `sprint_bulk_create` | `pm_bulk_create` |
| `bulk_update.py` | `sprint_bulk_update` | `pm_bulk_update` |
| `sprint_status.py` | `sprint_status` | `pm_get_status` |
| `relationships.py` | `sprint_set_relationship` | `pm_link_story_to_epic` |
| `rename.py` | `sprint_bulk_rename` | `pm_bulk_rename` |
| `action_log_tool.py` | `sprint_action_log` | `pm_action_log` |

Also update `main.py` if it references the old function names in any way (it shouldn't since registration is via `register()` functions, but verify).

- [ ] **Step 2: Commit**

```
refactor: rename tool functions to pm_* interface

Rename sprint_sync → pm_sync, sprint_bulk_create → pm_bulk_create,
sprint_bulk_update → pm_bulk_update, sprint_status → pm_get_status,
sprint_set_relationship → pm_link_story_to_epic,
sprint_bulk_rename → pm_bulk_rename, sprint_action_log → pm_action_log.
```

### Task 5: Add pm_get_capabilities tool

**Files:**
- Create or modify: `shield/adapters/clickup/server/tools/capabilities.py`
- Modify: `shield/adapters/clickup/server/main.py`

- [ ] **Step 1: Create capabilities.py**

```python
"""PM adapter capabilities discovery tool."""


def register(mcp):
    """Register the pm_get_capabilities tool."""

    @mcp.tool()
    async def pm_get_capabilities() -> dict:
        """Return the list of PM operations this adapter supports.

        Skills call this once at the start of a PM interaction to discover
        which operations are available. Unsupported operations should be
        skipped gracefully.
        """
        return {
            "adapter": "clickup",
            "adapter_mode": "hybrid",
            "capabilities": [
                "pm_sync",
                "pm_bulk_create",
                "pm_bulk_update",
                "pm_get_status",
                "pm_link_story_to_epic",
                "pm_bulk_rename",
                "pm_action_log",
                "pm_get_capabilities",
            ],
        }
```

- [ ] **Step 2: Register in main.py**

Add `from server.tools import capabilities` and call `capabilities.register(mcp)` in `_register_tools()`.

- [ ] **Step 3: Commit**

```
feat: add pm_get_capabilities tool

Returns the list of operations this adapter supports so skills
can gracefully skip unsupported operations.
```

## Chunk 3: Update Config Loading

### Task 6: Update config.py for new config paths

**Files:**
- Modify: `shield/adapters/clickup/server/config.py`
- Modify: `shield/adapters/clickup/server/main.py`

- [ ] **Step 1: Update config loading**

The config loading needs to support two modes:
1. **New mode (default):** Read from `~/.tesseract/` paths
   - PM config: `~/.tesseract/projects/<project>/pm.json`
   - Credentials: `~/.tesseract/credentials.json`
   - Project name: from `.tesseract.json` in the working directory
2. **Legacy mode:** Read from `sprint-planner.json` (for backward compatibility during migration)

Update `config.py`:
- Add a `load_shield_config()` function that:
  1. Looks for `.tesseract.json` in the working directory (walk up)
  2. Reads the project name
  3. Loads `~/.tesseract/projects/<project>/pm.json` for workspace/space IDs and naming
  4. Loads `~/.tesseract/credentials.json` for the API token
  5. Constructs a `SprintPlannerConfig` (keep the internal model for now) from these sources
- Keep the existing `load_config()` as fallback
- In `main.py`, try `load_shield_config()` first, fall back to `load_config()` if `.tesseract.json` is not found

- [ ] **Step 2: Commit**

```
feat: update config loading for ~/.tesseract/ paths

Config now loads from ~/.tesseract/projects/<project>/pm.json and
~/.tesseract/credentials.json by default. Falls back to legacy
sprint-planner.json for backward compatibility during migration.
```

### Task 7: Rename sprint_status.py file

**Files:**
- Rename: `shield/adapters/clickup/server/tools/sprint_status.py` → `shield/adapters/clickup/server/tools/status.py`

- [ ] **Step 1: Rename the file and update imports**

```bash
mv shield/adapters/clickup/server/tools/sprint_status.py shield/adapters/clickup/server/tools/status.py
```

Update the import in `main.py` from `from server.tools import sprint_status` to `from server.tools import status`, and update the `register()` call.

- [ ] **Step 2: Commit**

```
refactor: rename sprint_status.py to status.py
```
