# Tesseract — Claude Code Plugin Marketplace

## Project Overview

This is a Claude Code plugin marketplace containing multiple independent plugins. Each plugin lives in its own top-level directory and can be installed separately.

## Repository Structure

```
tesseract/
├── .claude-plugin/marketplace.json   # Marketplace registry — lists all plugins
├── infra-review/                     # Plugin: Terraform/Atmos review agents
│   ├── .claude-plugin/plugin.json
│   ├── agents/                       # Subagent definitions (markdown)
│   ├── commands/                     # Slash commands (markdown)
│   ├── hooks/                        # SessionStart + PostToolUse hooks
│   ├── scripts/                      # Helper scripts for hooks
│   └── skills/                       # Auto-invoked skills (SKILL.md)
├── clickup-sprint-planner/           # Plugin: ClickUp sprint planning MCP server
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json                     # MCP server configuration
│   ├── commands/                     # Slash commands
│   ├── server/                       # Python MCP server (mcp[cli] + httpx)
│   ├── skills/                       # Auto-invoked skills
│   └── examples/                     # Example config files
└── dev-workflow/                     # Plugin: Research + TDD skills
    ├── .claude-plugin/plugin.json
    └── skills/                       # Auto-invoked skills
```

## Key Conventions

- **Plugin isolation**: Each plugin is self-contained. Changes to one plugin must not break others.
- **Versioning**: Every plugin has a version in three places that must stay in sync:
  1. `<plugin>/.claude-plugin/plugin.json`
  2. `.claude-plugin/marketplace.json`
  3. `pyproject.toml` (if the plugin has a Python server)
- **Commands** are markdown files in `commands/` — they define slash commands users can invoke.
- **Skills** are markdown files at `skills/<name>/SKILL.md` — they are auto-invoked by Claude when relevant.
- **Agents** are markdown files in `agents/` — they define specialized subagents.
- **Hooks** use `hooks.json` to register shell scripts for Claude Code lifecycle events.
- **MCP servers** are configured in `.mcp.json` at the plugin root.

## Working with the Codebase

- The only Python code is in `clickup-sprint-planner/server/`. Run with `uv run`.
- Everything else is markdown definitions (commands, skills, agents) and shell scripts (hooks).
- Config files with real workspace data (`sprint-planner.json`) are gitignored. Only example configs are tracked.
- Never commit `.env` files or `settings.local.json`.

## Git Conventions

- Keep commits small and focused.
- When bumping a plugin version, update all three version locations in the same commit.
