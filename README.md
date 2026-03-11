# Tesseract

Claude Code plugins for infrastructure review, sprint planning, and development workflows.

## Plugins

| Plugin | Description |
|--------|-------------|
| **[infra-review](./infra-review/)** | Terraform/Atmos infrastructure review agents — security, architecture, operations, cost, and AWS Well-Architected Framework analysis |
| **[clickup-sprint-planner](./clickup-sprint-planner/)** | ClickUp sprint planning with bulk operations, relationship field management, plan-doc sync, and action logging via MCP server |
| **[dev-workflow](./dev-workflow/)** | General-purpose skills for structured research, TDD-based feature implementation, and infrastructure planning document generation (ADR + detailed plans) |

## Installation

Add the marketplace and install the plugins you need:

```
/plugin marketplace add infraspecdev/tesseract
/plugin install infra-review@tesseract
/plugin install clickup-sprint-planner@tesseract
/plugin install dev-workflow@tesseract
```

### clickup-sprint-planner setup

1. Copy the example config and fill in your ClickUp workspace details:
   ```bash
   cp clickup-sprint-planner/examples/sprint-planner.example.json clickup-sprint-planner/examples/sprint-planner.json
   ```
2. Set `CLICKUP_API_TOKEN` in your environment.

## License

MIT
