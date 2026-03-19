# Tesseract

A [Claude Code](https://claude.ai/claude-code) plugin marketplace.

> *In the Marvel universe, the Tesseract was a crystalline container that held the Space Stone — one of the six Infinity Stones, each holding power over a fundamental aspect of existence. Whoever possessed the Tesseract didn't just hold an object; they held the potential to reshape reality itself.*
>
> *This Tesseract holds something similar. Not Infinity Stones, but plugins — each one a concentrated capability that transforms how you build software. The container is simple. What it holds is powerful.*

---

## What's Inside

| Plugin | What It Does |
|--------|-------------|
| **[Shield](./shield/)** | A unified software development lifecycle plugin — research, planning, project management integration, implementation, and continuous code review with specialist agents |

### Deprecated Plugins

The following plugins have been consolidated into Shield and are no longer maintained as separate plugins:

| Plugin | Replaced By |
|--------|------------|
| `infra-review` | Shield's domain-specific review skills (`terraform/`, `atmos/`, `github-actions/`) and multi-mode reviewer agents |
| `clickup-sprint-planner` | Shield's PM adapter system (`/pm-sync`, `/pm-status`) with the ClickUp adapter at `shield/adapters/clickup/` |
| `dev-workflow` | Shield's general skills (`/research`, `/implement`, `/plan`) and superpowers integration |

If you have existing projects using these plugins (e.g., `infra-plans/` directories with `sprint-planner.json`), run `/shield init` in your project to migrate. Shield detects old plugin config and offers to set up the new `.shield.json` marker and `~/.shield/` config structure.

---

## Tesseract: The Marketplace

Tesseract is a **plugin marketplace** — a registry that contains one or more Claude Code plugins. You add the marketplace once, then install whichever plugins you need.

```bash
# Add the marketplace (one-time)
/plugin marketplace add infraspecdev/tesseract

# Install a plugin from it
/plugin install shield@tesseract

# Enable auto-updates to stay current
/plugin update --auto-update shield@tesseract
```

Each plugin in the marketplace is independently versioned and released. You can install one, some, or all of them.

---

## Plugins

### Shield

Named after Marvel's S.H.I.E.L.D. — the **Strategic Homeland Intervention, Enforcement and Logistics Division** — the organization that gathers intelligence, plans operations, assembles specialists, and executes missions.

Except here, the homeland is your codebase — and the existential threats are unreviewed pull requests, missing test coverage, security holes hiding in plain sight, and acceptance criteria so vague they'd make Nick Fury weep.

Shield assembles a team of specialist agents and orchestrates them through a structured engineering pipeline. A planner who breaks initiatives into executable stories with testable acceptance criteria. A security reviewer who thinks like an attacker. A cost analyst who's seen $10k/month NAT gateway bills in dev environments. An architect who's debugged cascading failures at 3 AM. An agile coach who ensures stories are sprint-ready. A developer experience engineer who ensures plans are clear enough to execute without questions.

It shields you from the mistakes that haunt on-call rotations — because the best incident is the one that never happened.

---

#### Design Philosophy

**One pipeline, many domains.** Shield follows a single workflow — research, plan, build, review — but adapts to the domain you're working in. Terraform gets provider-specific research and HashiCorp Configuration Language-aware review. Atmos gets stack hygiene checks. Future domains (Python, TypeScript, Kubernetes) slot in by adding a directory, not by rewriting orchestration.

**Continuous review, not gatekeeping.** Review isn't a phase at the end — it happens after planning (are the stories actionable?), after each implementation step (did we introduce issues?), and as a final consolidated check. You choose which findings to fix, which to defer, and which to discuss.

**Project management as a pluggable adapter.** The pipeline doesn't know about ClickUp or Jira. It knows about abstract operations — sync stories, get status, link to epic. Each project management tool implements these operations through its own adapter. Adding a new tool means writing an adapter, not touching any skill or agent.

**Agents are specialists.** Each agent has a clear domain (security, cost, architecture, operations) and operates in modes depending on context — lightweight checks when reviewing a plan document, deep checklists when reviewing Terraform code. One agent file, multiple depths.

**Your config, your rules.** The plugin adapts to your setup:
- Pick your domains (`terraform`, `atmos`, or both)
- Pick your project management tool per project (`clickup`, `jira`, or future adapters)
- Override which reviewers always run or never run per project

#### Usage

Shield is a multi-phase pipeline. **Every phase is standalone** — you can run any phase independently, skip phases you don't need, or run the full pipeline end-to-end.

```
/research ──→ /plan ──→ /plan-review ──→ /pm-sync ──→ /implement ──→ /review
     │            │            │              │             │            │
     ▼            ▼            ▼              ▼             ▼            ▼
  Research    Architecture   Scored       Stories      TDD-based    Multi-agent
  findings    + execution    analysis     synced to    feature      code review
  with        plan with      with P0/     your PM      impl with    with detailed
  citations   stories        P1/P2 recs   tool         AC tracking  per-agent findings
```

**First time?** Run `/shield init` to set up your project config (`.shield.json`). Migrating from older plugins? Use `/shield migrate`.

**Pick your entry point:**
- Starting fresh? Begin with `/research` to build domain context
- Have a plan already? Jump to `/plan-review` to get it scored
- Code written? Run `/review` directly for a comprehensive code review
- Just want security? `/review-security` for a single-agent pass

Each phase:
1. Does the work (with domain-specific skills when available)
2. Produces output to `{output_dir}/` (default `docs/shield/`) inside feature folders
3. Waits for your confirmation before proceeding

Review findings are presented with severity levels. You pick which fixes to apply, which to skip, and which need discussion. Optionally post findings to your project management tool.

**What to commit vs gitignore:**

| Path | Commit? | Why |
|------|---------|-----|
| `.shield.json` | Yes | Project config — domains, reviewer settings, output_dir |
| `{output_dir}/manifest.json` | Yes | Feature index — tracks latest artifacts per feature |
| `{output_dir}/index.html` | Yes | Dashboard — navigable overview of all features |
| `{output_dir}/{feature}/plan.json` | Yes | Plan sidecars — source of truth for stories and status |
| `{output_dir}/{feature}/plan/` | Yes | Architecture and plan docs — team reference |
| `{output_dir}/{feature}/research/` | Yes | Research findings — useful context |
| `{output_dir}/{feature}/summary/` | Yes | Phase completion records |
| `{output_dir}/{feature}/plan-review/` | No | Ephemeral — findings feed back into plan revisions |
| `{output_dir}/{feature}/code-review/` | No | Ephemeral — fixes become commits |
| `~/.shield/` | N/A | User-local config (PM credentials, project settings) — never in repo |

#### Installation

**1. Install Shield:**

```bash
/plugin marketplace add infraspecdev/tesseract
/plugin install shield@tesseract
/plugin update --auto-update shield@tesseract
```

**2. Set up your project:**

Run `/shield init` in your repository root. This creates a `.shield.json` project config (domains, reviewer settings) and optionally sets up PM integration at `~/.shield/projects/<name>/pm.json`.

Or do it manually:

```json
// .shield.json (committed to your repo)
{
  "project": "my-project",
  "domains": ["terraform"],
  "reviewers": {
    "auto_select": true,
    "always_include": ["security"]
  }
}
```

**3. Set up project management integration (optional):**

```json
// ~/.shield/projects/my-project/pm.json
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
// ~/.shield/credentials.json (never committed anywhere)
{
  "clickup": { "api_token": "pk_..." }
}
```

**4. Start using the pipeline:**

| Command | What it does |
|---------|-------------|
| `/shield init` | Set up Shield for a new project (creates config files) |
| `/shield migrate` | Migrate from older plugin versions |
| `/research` | Research a technical topic with structured citations and expert sources |
| `/plan` | Generate plan documents — architecture decisions and execution plans with stories |
| `/plan-review` | Run multi-agent plan review with scoring |
| `/pm-sync` | Sync plan stories to your project management tool |
| `/pm-status` | Show sprint or epic status from your project management tool |
| `/implement` | Test-driven development-based feature implementation with progress tracking |
| `/review` | Run comprehensive code review with domain-specific agents |
| `/review-security` | Security-focused review only |
| `/review-cost` | Cost optimization review only |
| `/review-well-architected` | Amazon Web Services Well-Architected Framework review |
| `/analyze-plan` | Analyze `terraform plan` output for security, cost, and operational impact |

#### External Plugin Integration

Shield discovers and leverages skills from other installed Claude Code plugins. It auto-detects domain-relevant plugins (like `terraform-skills`) and offers to integrate them. You can also explicitly map external skills to phases in `.shield.json`:

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

Use `"general"` for workflow-level plugins that enhance all domains, and domain names for domain-specific plugins. Shield works standalone — all external integrations are optional with built-in fallbacks.

#### Architecture

```
shield/
├── skills/                        # Organized by domain
│   ├── general/                   # Domain-agnostic orchestrators
│   │   ├── research/              # Structured research with citations
│   │   ├── plan-docs/             # Plan document generation (HTML + JSON sidecar)
│   │   ├── plan-review/           # Multi-agent plan review
│   │   ├── implement-feature/     # Test-driven development-based implementation
│   │   ├── review/                # Review orchestrator: detect domain, dispatch agents
│   │   └── summarize/             # Phase summary generator
│   ├── terraform/                 # Terraform-specific overrides
│   ├── atmos/                     # Atmos-specific overrides
│   └── github-actions/            # Continuous integration and delivery review
│
├── agents/                        # Specialist reviewers (multi-mode)
│   ├── security-reviewer.md       # Plan + infrastructure code + application code modes
│   ├── cost-reviewer.md
│   ├── architecture-reviewer.md
│   ├── operations-reviewer.md
│   ├── well-architected-reviewer.md
│   ├── agile-coach-reviewer.md
│   └── dx-engineer-reviewer.md    # Developer experience reviewer
│
├── commands/                      # Slash commands (/research, /plan, /review, etc.)
├── hooks/                         # Session start, post-edit
├── adapters/clickup/              # ClickUp project management adapter (Model Context Protocol server)
└── schemas/                       # JSON schemas for config and plan sidecar
```

#### Examples

See Shield in action with two example projects:

- **[terraform-vpc](./shield/examples/terraform-vpc/)** — a Terraform VPC module walkthrough showing infrastructure review agents catching security, cost, and architecture issues
- **[python-api](./shield/examples/python-api/)** — a FastAPI application walkthrough showing the general review pipeline

Each example includes a step-by-step README.

---

## Releases

Releases are triggered by version bumps in `.claude-plugin/marketplace.json`. To release a plugin:

1. Bump the `version` field for the plugin in `marketplace.json`
2. Merge to `main`
3. A GitHub Actions workflow detects the change, creates a git tag (for example, `v2.1.0`), and publishes a GitHub Release with auto-generated release notes

---

## Contributing

### Adding a New Plugin

1. Create a new directory at the repository root (for example, `my-plugin/`)
2. Add `.claude-plugin/plugin.json` with the plugin manifest
3. Add skills, agents, commands, and hooks as needed
4. Register the plugin in `.claude-plugin/marketplace.json` with a name, description, version, and source path
5. Update this README with a new entry in the "What's Inside" table and a section under "Plugins"

### Adding a Domain to Shield

1. Create `shield/skills/<domain>/` directory
2. Add phase-specific skills that need domain behavior (for example, `review/SKILL.md`)
3. Phases without a domain-specific skill fall back to `general/`
4. Add the domain name to the `domains` array in `.shield.json`

### Adding a Project Management Adapter to Shield

1. Create `shield/adapters/<tool>/` with its own Model Context Protocol server
2. Implement the standard tool interface: `pm_sync`, `pm_bulk_create`, `pm_bulk_update`, `pm_get_status`, `pm_get_stories_for_epic`, `pm_link_story_to_epic`, `pm_action_log`, `pm_get_capabilities`
3. Add `.mcp.json` and server code
4. Set `"adapter": "<tool>"` in the project's `pm.json`

---

## License

MIT
