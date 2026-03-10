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
  "version": "1.0.0",
  "description": "Short description of what the plugin does.",
  "author": {
    "name": "Your Name"
  },
  "repository": "https://github.com/infraspecdev/tesseract",
  "license": "MIT",
  "keywords": ["relevant", "keywords"]
}
```

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

When releasing changes to a plugin, bump the version in all three places:

1. `<plugin>/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`
3. `pyproject.toml` (if applicable)

## Testing

Install your plugin locally before submitting:

```bash
claude --plugin-dir ./my-plugin
```

Verify that:
- Skills trigger on the expected inputs
- Commands are listed and work correctly
- MCP tools respond as expected
- Hooks fire without errors

## Submitting

1. Fork the repository
2. Create a branch for your plugin
3. Add your plugin following the structure above
4. Open a pull request with a description of what the plugin does
