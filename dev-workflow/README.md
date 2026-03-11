# dev-workflow

General-purpose development workflow skills for Claude Code.

## Skills

| Skill | Description |
|-------|-------------|
| **research** | Research a technical topic and produce a well-sourced document with citations and expert opinions |
| **implement-feature** | Structured feature implementation: requirements gathering, planning, TDD, and progress tracking. Accepts Jira or ClickUp ticket URLs. |
| **plan-docs** | Generate infrastructure planning documents — architecture/ADR docs and detailed execution plans with stories that sync to ClickUp via `clickup-sprint-planner` |

## Installation

```
/plugin marketplace add infraspecdev/tesseract
/plugin install dev-workflow@tesseract
```

## plan-docs + clickup-sprint-planner

The `plan-docs` skill generates HTML (or Markdown) documents whose story structure is directly parseable by the `clickup-sprint-planner` plugin. The workflow:

1. Use `plan-docs` to generate `architecture.html` and `detailed-plan.html` for a phase
2. Add the phase to `sprint-planner.json` config
3. Run `/sprint-sync` to create ClickUp cards from the stories

See `skills/plan-docs/SKILL.md` for full conventions and `skills/plan-docs/templates.md` for HTML/Markdown templates.
