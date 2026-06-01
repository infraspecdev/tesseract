# Contributing to Tesseract

## Adding a New Plugin

### 1. Create the plugin directory

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── my-skill/
        └── SKILL.md
```

### 2. Add `plugin.json`

```json
{
  "name": "my-plugin",
  "description": "Short description of what the plugin does.",
  "author": {
    "name": "Your Name"
  },
  "repository": "https://github.com/infraspecdev/tesseract",
  "license": "MIT",
  "keywords": ["relevant", "keywords"]
}
```

> **Do not put a `version` field in `plugin.json`.** For relative-path plugins (all plugins in this repo) the version lives **only** in `marketplace.json`. A `version` in `plugin.json` silently wins and causes the marketplace version to be ignored. See [Versioning](#versioning).

### 3. Register in the marketplace

Add your plugin to `.claude-plugin/marketplace.json` under the `plugins` array:

```json
{
  "name": "my-plugin",
  "description": "Short description",
  "version": "1.0.0",
  "source": "./my-plugin",
  "category": "development"
}
```

Categories: `development`, `productivity`.

### 4. Add content

Plugins can include any combination of:

| Type | Location | Purpose |
|------|----------|---------|
| **Skills** | `skills/<name>/SKILL.md` | Auto-invoked by Claude when the task matches the skill's description |
| **Commands** | `commands/<name>.md` | Slash commands users invoke explicitly (e.g. `/my-command`) |
| **Agents** | `agents/<name>.md` | Specialized subagents dispatched via the Agent tool |
| **Hooks** | `hooks/hooks.json` + scripts | Shell scripts triggered on Claude Code events (SessionStart, PostToolUse, etc.) |
| **MCP Server** | `.mcp.json` + server code | MCP servers that provide tools to Claude |

### 5. Add a README

Create a `README.md` in your plugin directory explaining:
- What the plugin does and why
- Prerequisites (e.g. `uv`, API tokens)
- Available commands, skills, and agents
- Configuration steps

## Plugin Types by Example

### Skills-only plugin (simplest)

Like `dev-workflow` — just markdown skill files, no server or hooks:

```
my-plugin/
├── .claude-plugin/plugin.json
└── skills/
    └── my-skill/SKILL.md
```

### Plugin with commands and agents

Like `infra-review` — slash commands, subagents, and hooks:

```
my-plugin/
├── .claude-plugin/plugin.json
├── agents/reviewer.md
├── commands/review.md
├── hooks/hooks.json
├── hooks/my-hook.sh
└── skills/my-skill/SKILL.md
```

### Plugin with an MCP server

Like `clickup-sprint-planner` — a Python MCP server providing tools:

```
my-plugin/
├── .claude-plugin/plugin.json
├── .mcp.json
├── pyproject.toml
├── server/
│   ├── main.py
│   └── ...
├── commands/my-command.md
└── skills/my-skill/SKILL.md
```

The `.mcp.json` registers the server:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "python", "server/main.py"]
    }
  }
}
```

## Writing Skills

Skills are the most common plugin component. A skill file (`SKILL.md`) has:

```markdown
---
name: my-skill
description: When to auto-invoke this skill. Be specific about trigger conditions.
---

# My Skill

Instructions for Claude when this skill is active.

## Rules
1. Rule one
2. Rule two

## Workflow
Steps Claude should follow.
```

The `description` in the frontmatter determines when Claude auto-invokes the skill — make it specific.

## Writing Commands

Commands define slash commands. Add `user_invocable: true` to the frontmatter:

```markdown
---
name: my-command
description: What this command does.
user_invocable: true
---

# /my-command [args]

Steps Claude should follow when the user runs this command.
```

## Versioning

For relative-path plugins (all plugins in this repo), the version lives in **`.claude-plugin/marketplace.json` only** — never in `plugin.json` (the manifest version silently wins and causes the marketplace version to be ignored). When releasing changes to a plugin, bump:

1. `.claude-plugin/marketplace.json` (the plugin's `version` field) — **required**
2. `<plugin>/pyproject.toml` — **only if** the plugin ships a Python server (e.g. `clickup-sprint-planner`), bumped in the same commit

Reference: [plugin marketplace version resolution](https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels).

## Eval coverage (required)

Every new or changed plugin asset (skill, agent, command, MCP prompt, hook, or skill-orchestrator wiring) **must land in the same PR as at least one executable eval** that exercises the new behavior. In-conversation testing during development does not survive into the repo and cannot regression-test future changes.

If a change genuinely has no eval-shaped surface (a doc typo, a rename, a comment), state that explicitly in the PR body. The default is "eval required." See `.claude/skills/updating-plugin-assets/SKILL.md` for the RED→GREEN procedure and framework choice.

## Testing

The repo's test suite runs via `make` (mirrors what pre-commit and CI run):

```bash
make install   # ensure uv is present (test deps are pulled in per-run via uv run --with)
make test      # run shield/tests/run-all.sh — schema, structure, hooks, evals, adapters
make lint      # shellcheck shipped shell scripts
make ci        # install + test + lint (what GitHub Actions runs)
```

Python runs through `uv` only — no system `pip`, no `requirements.txt`. Adapter contract tests live under `shield/adapters/*/tests/` (`uv run --extra test pytest`); evals live under `shield/evals/`.

Before submitting, also smoke-test the plugin in Claude Code via the marketplace flow and verify that:
- Skills trigger on the expected inputs
- Commands are listed and work correctly
- MCP tools respond as expected
- Hooks fire without errors

## Submitting

1. Fork the repository
2. Create a branch for your plugin
3. Add your plugin following the structure above
4. Open a pull request with a description of what the plugin does
