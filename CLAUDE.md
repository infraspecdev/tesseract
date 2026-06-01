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
- **Versioning**: For relative-path plugins (all plugins in this repo), the version lives **only in `.claude-plugin/marketplace.json`** — NOT in `plugin.json`. The `plugin.json` manifest wins silently and can cause the marketplace version to be ignored. Additionally, bump `pyproject.toml` if the plugin has a Python server.
  - Reference: https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels
  - Reference: https://code.claude.com/docs/en/plugins
- **Commands** are markdown files in `commands/` — they define slash commands users can invoke.
- **Skills** are markdown files at `skills/<name>/SKILL.md` — they are auto-invoked by Claude when relevant.
- **Agents** are markdown files in `agents/` — they define specialized subagents.
- **Hooks** use `hooks.json` to register shell scripts for Claude Code lifecycle events.
- **MCP servers** are configured in `.mcp.json` at the plugin root.
- **Doc-authoring skills** (any skill that writes a doc to `docs/shield/`) MUST apply the `shield:writing-style` skill to their author-written prose before writing — see `shield/skills/general/writing-style/SKILL.md`. This keeps generated docs simple, clear, and concise. It applies to prose only, never to rendered/marker-wrapped sections or JSON sidecars.

## Working with the Codebase

- Python runs through `uv` only: `pyproject.toml`-packaged (`clickup-sprint-planner/server/`, `shield/adapters/*/`) for shipped components, and `uv run --with <deps>` for standalone scripts (`shield/scripts/`, `shield/evals/`). No system pip, no `requirements.txt`.
- Everything else is markdown definitions (commands, skills, agents) and shell scripts (hooks).
- Config files with real workspace data (`sprint-planner.json`) are gitignored. Only example configs are tracked.
- Never commit `.env` files or `settings.local.json`.

## Skill Quality

- **RED-GREEN testing is mandatory** when creating or modifying any skill, agent, or command. Before considering the work complete:
  1. **RED**: Run a subagent WITHOUT the skill against a test scenario. Document baseline behavior — what it catches, what it misses, severity accuracy.
  2. **GREEN**: Run a subagent WITH the skill loaded against the same scenario. Verify it catches more issues, grades severity correctly, and handles edge cases.
  3. **REFACTOR**: If GREEN reveals gaps (agents skipping checks, missing edge cases), fix the skill and re-test.
- Create test fixtures with intentional issues that exercise the skill's checks, including edge cases from the Common Mistakes table.
- Skills should follow the `superpowers:writing-skills` guide for CSO, frontmatter, structure, and token efficiency.

## Eval coverage — MANDATORY for plugin updates

> **Procedure:** see `.claude/skills/updating-plugin-assets/SKILL.md` (auto-loads when editing plugin assets) for framework choice, RED→GREEN steps, and PR definition-of-done.

**Every new or changed plugin asset (skill, agent, command, prompt, or skill-orchestrator wiring) MUST land in the same PR as at least one executable eval that exercises the new behavior.** In-conversation GREEN dispatches during implementation are *necessary but not sufficient* — they do not survive into the repo and cannot regression-test future changes.

If a change genuinely has no eval-shaped surface (e.g., a typo fix in a doc, a rename, a comment), state that explicitly in the PR body. Default is "eval required."

## Git Conventions

- Keep commits small and focused.
- When updating any plugin, bump its version in both `.claude-plugin/marketplace.json` and `pyproject.toml` (if the plugin has one) in the same commit. Do NOT put version in `plugin.json` for relative-path plugins.
