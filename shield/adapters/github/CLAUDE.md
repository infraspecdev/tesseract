# GitHub PM Adapter — Contributor Guide

## What this is

MCP server that exposes `pm_*` tools for GitHub Issues + Projects v2. Implements the same interface as `shield/adapters/clickup/` — both adapters are interchangeable from Shield's perspective.

## Structure

```
server/
├── main.py          # FastMCP entry point, _LazyProxy/_DepsLoader pattern
├── config.py        # Config loading: .shield.json → pm.json → sprint-planner.json
├── github_client.py # Async GitHub REST v3 + GraphQL v4 wrapper (httpx)
├── action_log.py    # Append-only JSONL log of all write operations
├── parsers/         # HTML plan doc parsers (shared with ClickUp adapter)
└── tools/
    ├── capabilities.py      # pm_get_capabilities — static, no config needed
    ├── status.py            # pm_get_status — sub-issues + grouping
    ├── sync.py              # pm_sync — diff plan doc vs GitHub Issues
    ├── bulk_create.py       # pm_bulk_create — create + link issues
    ├── bulk_update.py       # pm_bulk_update — batch state/label/assignee changes
    ├── rename.py            # pm_bulk_rename — preview or apply title renames
    ├── relationships.py     # pm_link_story_to_epic — add sub-issues
    ├── action_log_tool.py   # pm_action_log — query the action log
    └── _helpers.py          # normalize_status(), shared utils
tests/
├── conftest.py      # Shared fixtures (mock capabilities, config)
└── test_contract.py # Contract tests — adapter declares correct capabilities
```

## Lazy loading pattern

The server starts without config so it doesn't fail when no `.shield.json` exists. Config is loaded on first tool call that needs it (`_DepsLoader.ensure_loaded()`). `pm_get_capabilities` is the only tool that never triggers loading.

Do not move config loading into `__init__` or module-level code — this would break the MCP server startup.

## Adding a new tool

1. Create `server/tools/my_tool.py` with a `register(mcp, client, ...)` function
2. Add `@mcp.tool()` inside `register()`
3. Import and call `my_tool.register(mcp, ...)` in `server/main.py`
4. Add the tool name to the `capabilities` list in `server/tools/capabilities.py`
5. Add a contract test in `tests/test_contract.py` if the tool has a new pm_* name
6. Mirror the same tool in `shield/adapters/clickup/server/tools/` if it belongs in the shared interface

## Config loading order

`load_shield_config()` in `config.py`:
1. Walk up from `cwd` to find `.shield.json` → read `project` name
2. Read `~/.shield/projects/<project>/pm.json`
3. Token: `~/.shield/credentials.json` → `GITHUB_TOKEN` env → `gh auth token`

Falls back to `load_config()` (legacy `sprint-planner.json`) if no `.shield.json` found.

## GitHub API notes

- Sub-issues use the REST endpoint `POST /repos/{owner}/{repo}/issues/{parent}/sub_issues` — this is a newer API, requires `repo` scope
- Projects v2 uses GraphQL v4 — requires `project` scope
- `get_sub_issues()` returns `[]` (not 404) if the issue has no sub-issues

## Tests

```bash
uv run pytest tests/ -v
```

Contract tests verify the adapter declares the right capabilities and the config schema is valid. They do not hit the network. Add integration tests under `tests/integration/` (gitignored) for live API tests.

## Versioning

Version lives in `pyproject.toml` only. Do not add a `version` field to `.claude-plugin/plugin.json` — per the project's versioning convention, the marketplace version in `.claude-plugin/marketplace.json` takes precedence for relative-path plugins.
