# Tesseract

A Claude Code plugin marketplace for the software development lifecycle.

## What's Inside

Tesseract contains **Shield** — a unified plugin that guides your engineering workflow from research through review. Shield assembles a team of specialist agents (security, architecture, cost, operations, DX) and orchestrates them through a structured pipeline.

| Plugin | Description |
|--------|-------------|
| **[shield](./shield/)** | Full SDLC plugin — research, planning, PM integration, implementation, and continuous review with multi-domain support |

## Why "Tesseract" and "Shield"

In the Marvel universe, the **Tesseract** is the container that holds immense power. **S.H.I.E.L.D.** — the Strategic Homeland Intervention, Enforcement and Logistics Division — is the organization that assembles specialists, gathers intelligence, plans operations, and executes missions.

Except here, the homeland is your codebase. The existential threats are unreviewed PRs, missing test coverage, security holes hiding in plain sight, and acceptance criteria so vague they'd make Nick Fury weep. Tesseract is the marketplace — the container. Shield is the plugin that assembles your engineering team: a security reviewer who thinks like an attacker, a cost analyst who's seen $10k/month NAT gateway bills, an architect who's debugged cascading failures at 3 AM, and a DX engineer who ensures plans are clear enough to execute without questions. It shields you from the mistakes that haunt on-call rotations — because the best incident is the one that never happened.

## Design Philosophy

**One pipeline, many domains.** Shield follows a single workflow — research → plan → build → review — but adapts to the domain you're working in. Terraform gets provider-specific research and HCL-aware review. Atmos gets stack hygiene checks. Future domains (Python, TypeScript, Kubernetes) slot in by adding a directory, not by rewriting orchestration.

**Continuous review, not gatekeeping.** Review isn't a phase at the end — it happens after planning (are the stories actionable?), after each implementation step (did we introduce issues?), and as a final consolidated check. You choose which findings to fix, which to defer, and which to discuss.

**PM tool as a pluggable adapter.** The pipeline doesn't know about ClickUp or Jira. It knows about abstract operations — sync stories, get status, link to epic. Each PM tool implements these operations in its own adapter. Adding a new PM tool means writing an adapter, not touching any skill or agent.

**Agents are specialists, not generalists.** Each agent has a clear domain (security, cost, architecture, operations) and operates in modes depending on context — lightweight checks when reviewing a plan, deep checklists when reviewing Terraform code. One agent file, multiple depths.

**Your config, your rules.** The plugin adapts to your setup:
- Pick your domains (`terraform`, `atmos`, or both)
- Pick your PM tool (`clickup`, `none`, or future adapters)
- Override which reviewers always run or never run
- Enable review-on-commit with configurable severity thresholds

## Pipeline Overview

```
research → planning → [plan review] → PM sync → [confirm AC] → implement → [code review] → final review
                          ↑                          ↑              ↑
                     agents review            confirm acceptance   agents review code +
                     plan quality             criteria per story   verify AC are met
```

Each phase:
1. Does the work (with domain-specific skills when available)
2. Produces a summary of what was done
3. Waits for your confirmation before proceeding

Review findings are presented with severity levels. You pick which fixes to apply, which to skip, and which need discussion. Optionally post findings to your PM tool.

## Plugin Architecture

```
shield/
├── skills/                        # Organized by domain
│   ├── general/                   # Domain-agnostic orchestrators
│   │   ├── research/              # Structured research with citations
│   │   ├── plan-docs/             # Plan document generation (HTML + JSON sidecar)
│   │   ├── plan-review/           # Multi-agent plan review
│   │   ├── implement-feature/     # TDD-based implementation
│   │   ├── code-review/           # Orchestrator: detect domain → dispatch
│   │   └── summarize/             # Phase summary generator
│   ├── terraform/                 # Terraform-specific overrides
│   ├── atmos/                     # Atmos-specific overrides
│   └── github-actions/            # CI/CD review
│
├── agents/                        # Specialist reviewers (multi-mode)
│   ├── security-reviewer.md       # Plan + infra-code + app-code modes
│   ├── cost-reviewer.md
│   ├── architecture-reviewer.md
│   ├── operations-reviewer.md
│   ├── well-architected-reviewer.md
│   ├── agile-coach-reviewer.md
│   └── dx-engineer-reviewer.md
│
├── commands/                      # Slash commands (/research, /plan, /review, etc.)
├── hooks/                         # Session start, post-edit, pre-commit review
├── adapters/clickup/              # ClickUp PM adapter (MCP server)
└── schemas/                       # JSON schemas for config and plan sidecar
```

## Quick Start

1. **Add the marketplace and install Shield:**
   ```
   /plugin marketplace add infraspecdev/tesseract
   /plugin install shield@tesseract
   ```
   Enable auto-updates to stay current:
   ```
   /plugin update --auto-update shield@tesseract
   ```

2. **Create a project marker** in your repo root:
   ```json
   // .tesseract.json
   {
     "project": "my-project",
     "domains": ["terraform"]
   }
   ```

3. **Configure globally** (one-time setup):
   ```bash
   mkdir -p ~/.tesseract
   ```
   ```json
   // ~/.tesseract/config.json
   {
     "pm_tool": "clickup",
     "reviewers": {
       "auto_select": true,
       "always_include": ["security"]
     },
     "review_on_commit": {
       "enabled": false,
       "block_threshold": "critical",
       "warn_threshold": "important"
     }
   }
   ```

4. **Set up PM integration** (optional):
   ```json
   // ~/.tesseract/projects/my-project/pm.json
   {
     "adapter": "clickup",
     "workspace_id": "12345",
     "space_id": "67890",
     "naming": {
       "project_prefix": "PROJ",
       "story_format": "[{prefix}] {epic_id}-S{index}: {name}"
     }
   }
   ```
   ```json
   // ~/.tesseract/credentials.json
   {
     "clickup": { "api_token": "pk_..." }
   }
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/shield init` | Set up Shield for a new project (creates config files) |
| `/shield migrate` | Migrate from old plugins (infra-review, clickup-sprint-planner, dev-workflow) |
| `/research` | Research a technical topic with citations and expert sources |
| `/plan` | Generate plan documents (architecture/ADR + execution plan with stories) |
| `/plan-review` | Run multi-agent plan review with scoring |
| `/pm-sync` | Sync plan stories to your PM tool |
| `/pm-status` | Show sprint/epic status from PM tool |
| `/implement` | TDD-based feature implementation with progress tracking |
| `/review` | Run code review with domain-specific agents |
| `/review-security` | Security-focused review only |
| `/review-cost` | Cost optimization review only |
| `/review-well-architected` | AWS Well-Architected Framework review |
| `/analyze-plan` | Analyze `terraform plan` output for impact |

## External Plugin Integration

Shield discovers and leverages skills from other installed Claude Code plugins. It auto-detects domain-relevant plugins (like `terraform-skills`) and offers to integrate them. You can also explicitly map external skills to phases in `.tesseract.json`:

```json
{
  "external_skills": {
    "general": {
      "implement": ["superpowers:test-driven-development"],
      "review": ["superpowers:verification-before-completion"],
      "debug": ["superpowers:systematic-debugging"]
    },
    "terraform": {
      "review": ["terraform-skills:validate", "terraform-skills:lint"]
    }
  }
}
```

Use `"general"` for workflow-level plugins (like superpowers) that enhance all domains, and domain names for domain-specific plugins. Shield works standalone — all external integrations are optional with built-in fallbacks.

## Examples

See Shield in action with two example projects:

- **[terraform-vpc](./shield/examples/terraform-vpc/)** — a Terraform VPC module walkthrough showing infra review agents catching security, cost, and architecture issues
- **[python-api](./shield/examples/python-api/)** — a FastAPI application walkthrough showing general review pipeline

Each example includes per-phase GIFs and a step-by-step README.

## Releases

Releases are automated with [Release Please](https://github.com/googleapis/release-please). Write commits using [Conventional Commits](https://www.conventionalcommits.org/) format:

- `feat: add Python domain support` → bumps minor version
- `fix: correct Checkov skip detection` → bumps patch version
- `feat!: restructure config format` → bumps major version

On merge to `main`, Release Please opens a release PR. Merging that PR creates a git tag, GitHub Release, and updates `CHANGELOG.md`.

## Contributing

### Adding a New Domain

1. Create `shield/skills/<domain>/` directory
2. Add phase-specific skills that need domain behavior (e.g., `review/SKILL.md`)
3. Phases without a domain skill fall back to `general/`
4. Add the domain name to the `domains` array in `.tesseract.json`

### Adding a PM Adapter

1. Create `shield/adapters/<tool>/` with its own MCP server
2. Implement the standard tool interface: `pm_sync`, `pm_bulk_create`, `pm_bulk_update`, `pm_get_status`, `pm_get_stories_for_epic`, `pm_link_story_to_epic`, `pm_action_log`, `pm_get_capabilities`
3. Add `.mcp.json` and server code
4. Set `"pm_tool": "<tool>"` in config

## License

MIT
