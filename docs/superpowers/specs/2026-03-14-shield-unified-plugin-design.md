# Shield — Unified Plugin Design

**Status:** Draft
**Date:** 2026-03-14
**Marketplace:** Tesseract
**Plugin:** Shield

## Naming

**Tesseract** (marketplace) — In the Marvel universe, the Tesseract is the container that holds immense power. Here, it's the marketplace — the container that holds plugins.

**Shield** (plugin) — **S**trategic **H**omeland **I**ntervention, **E**nforcement and **L**ogistics **D**ivision. Except here, the homeland is your codebase — and the existential threats are unreviewed PRs, missing test coverage, security holes hiding in plain sight, and acceptance criteria so vague they'd make Nick Fury weep. Shield assembles specialist agents, plans operations, and intervenes before bad code ships to production. It shields you from the mistakes that haunt 3 AM on-call rotations — because the best incident is the one that never happened.

## Context

Tesseract currently contains 3 independent plugins — `infra-review`, `clickup-sprint-planner`, and `dev-workflow` — installed separately from a marketplace. These plugins have significant overlap in agent personas (security, cost, architecture reviewers exist in both `infra-review` and `dev-workflow` at different depth levels) and no context flow between them.

The goal is to consolidate all 3 into a single plugin called **Shield** that provides a unified development lifecycle: research → planning → PM integration → implementation → review. The plugin should support multiple domains (infrastructure, application code) and multiple PM tools (ClickUp now, Jira later).

## Pipeline

The Shield workflow is a 5-phase pipeline with continuous review:

```
research → planning → [plan review] → PM sync → [AC confirmation] → implement → [code review per step] → final review
```

Each phase:
1. Does the work
2. Produces a summary file (short bullet points of what was done)
3. Waits for user confirmation before proceeding to the next phase

Review is continuous — it runs as a gate after planning, after each implementation step, and as a final consolidated check.

### Acceptance Criteria Confirmation (Pre-Implementation)

Before implementation begins for each story, the orchestrator presents the acceptance criteria to the user for confirmation. The criteria are gathered from the plan sidecar, PM card, or planning doc (same priority order as verification).

The user is shown:

```
Story: EPIC-1-S1 — IPAM Pool Hierarchy

Acceptance Criteria:
  1. Regional pools allocate /20 CIDRs
  2. No CIDR overlap across regions
  3. Rollback without data loss

Confirm these criteria before starting implementation?
  [a] Proceed as-is
  [b] Edit criteria (add/remove/modify)
  [c] Skip — implement without formal criteria
```

If the user edits criteria, the changes are written back to the plan sidecar JSON (and optionally synced to the PM card). This ensures the criteria verified during code review match what the user actually agreed to, not stale or vague criteria from the original planning phase.

### Acceptance Criteria Verification (Post-Implementation)

When a code review runs during or after implementation, it checks whether the acceptance criteria from the source material have been met. The review looks for criteria from (in priority order):

1. **Plan sidecar JSON** — if a run is active, read the story's `acceptance_criteria` array from the sidecar
2. **PM card** — if the story has a `pm_id`, fetch the card details via the PM adapter and extract acceptance criteria
3. **Planning doc** — if an HTML plan doc exists, parse the acceptance criteria section for the relevant story

The review produces an **Acceptance Criteria Report** alongside the standard findings:

| Criteria | Status | Evidence |
|----------|--------|----------|
| Regional pools allocate /20 CIDRs | Met | `main.tf:42` — `netmask_length = 20` |
| No CIDR overlap across regions | Met | `tests/happy_path.tftest.hcl` — overlap assertion |
| Rollback without data loss | Not verified | No rollback test or documentation found |

Criteria marked "Not verified" or "Not met" are surfaced as findings alongside the standard code review results. The user can then decide to fix them, defer them, or mark them as out of scope.

### Review Output Flow

1. Run review — produces findings with grades, recommendations, and acceptance criteria verification
2. Present findings — summary table of issues (severity, location, recommendation)
3. User picks — which fixes to apply (all, select specific, skip)
4. Apply selected fixes — implement the changes
5. Discuss if needed — findings where the agent cannot determine a single correct fix (e.g., multiple valid approaches, architecture trade-offs, or fixes that change public interfaces) are presented to the user with options before applying. The agent flags these as `NEEDS_DISCUSSION` in its output.
6. Update review summary — record what was fixed, deferred, or discussed
7. User's choice — optionally post findings as comments on PM cards

### Phase Summaries

Each phase writes a summary to the run directory:

```
~/.tesseract/projects/<project>/runs/<date>-<topic>/
├── research-summary.md
├── plan-summary.md
├── plan-review-summary.md
├── sync-summary.md
├── impl-step-1-summary.md
├── impl-step-1-review.md
├── impl-step-2-summary.md
├── impl-step-2-review.md
├── final-review-summary.md
└── plan-sidecar.json
```

## Repository Structure

Tesseract remains a marketplace. Shield is the single plugin inside it.

```
tesseract/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace registry pointing to shield/
│
├── release-please-config.json        # Monorepo release config
├── .release-please-manifest.json     # Version manifest
│
└── shield/
    ├── .claude-plugin/
    │   └── plugin.json               # Shield plugin manifest (includes permissions)
    ├── CHANGELOG.md                   # Auto-generated by Release Please
    │
    ├── skills/
    │   ├── general/                   # Domain-agnostic orchestrators/defaults
    │   │   ├── research/SKILL.md
    │   │   ├── plan-docs/SKILL.md
    │   │   ├── plan-review/SKILL.md
    │   │   ├── implement-feature/SKILL.md
    │   │   ├── review/SKILL.md         # Orchestrator: code + domain + agents + AC
    │   │   └── summarize/SKILL.md     # Phase summary generator
    │   │
    │   ├── terraform/                 # Terraform/HCL domain
    │   │   ├── research/SKILL.md      # Provider docs, module patterns
    │   │   ├── plan-docs/SKILL.md     # Infra plan format, TF-specific stories
    │   │   ├── implement/SKILL.md     # Plan → apply workflow, state mgmt
    │   │   ├── review/SKILL.md        # HCL lint, Checkov, security audit
    │   │   └── plan-analysis/SKILL.md # terraform plan -json analysis
    │   │
    │   ├── atmos/                     # Atmos-specific overrides
    │   │   ├── review/SKILL.md        # Stack YAML, catalog, hygiene
    │   │   └── repo-review/SKILL.md   # Full repo assessment
    │   │
    │   ├── github-actions/            # CI/CD domain
    │   │   └── review/SKILL.md        # Workflow audit
    │   │
    │   └── pm-sync/SKILL.md           # PM integration (domain-agnostic)
    │
    ├── agents/                        # Flat — all reviewer agents
    │   ├── security-reviewer.md       # Modes: plan / infra-code / app-code
    │   ├── cost-reviewer.md           # Modes: plan / infra-code
    │   ├── architecture-reviewer.md   # Modes: plan / infra-code / app-code
    │   ├── operations-reviewer.md     # Modes: plan / infra-code
    │   ├── well-architected-reviewer.md  # Infra-code only
    │   ├── agile-coach-reviewer.md       # Plan only
    │   └── dx-engineer-reviewer.md       # Plan only
    │
    ├── commands/                      # Slash commands
    │   ├── init.md                    # Fresh setup
    │   ├── migrate.md                 # Migrate from v1.x
    │   ├── research.md
    │   ├── plan.md
    │   ├── plan-review.md
    │   ├── pm-sync.md
    │   ├── pm-status.md
    │   ├── implement.md
    │   ├── review.md                  # Full review orchestrator (see Review Command Hierarchy)
    │   ├── review-security.md         # Single-agent review
    │   ├── review-cost.md
    │   ├── review-well-architected.md
    │   └── analyze-plan.md            # Terraform plan analysis
    │
    ├── hooks/
    │   ├── hooks.json
    │   └── scripts/
    │       ├── session-start.sh       # See Hooks section below
    │       ├── post-edit.sh           # See Hooks section below
    │       └── pre-commit-review.sh   # See Review on Commit section below
    │
    ├── adapters/                      # PM tool adapters
    │   └── clickup/
    │       ├── .mcp.json              # MCP server config
    │       ├── server/
    │       │   ├── main.py
    │       │   ├── config.py
    │       │   ├── clickup_client.py
    │       │   ├── action_log.py
    │       │   ├── tools/             # Implements PM adapter interface
    │       │   └── parsers/           # Plan sidecar JSON → ClickUp format
    │       └── pyproject.toml
    │
    ├── schemas/                       # JSON schemas
    │   ├── plan-sidecar.schema.json
    │   ├── config.schema.json
    │   └── pm.schema.json
    │
    ├── examples/
    │   ├── terraform-vpc/             # Infra example with walkthrough + GIFs
    │   └── python-api/               # App example with walkthrough + GIFs
    │
    ├── tests/                         # Plugin tests
    │   ├── test_config.sh
    │   ├── test_sidecar_schema.sh
    │   └── test_skill_resolution.sh
    │
    ├── evals/                         # Agent/skill golden-file evals
    │   ├── inputs/                    # Known inputs (sample TF, sample plans)
    │   ├── expected/                  # Expected findings (golden files)
    │   └── run-evals.sh
    │
    └── config-examples/
        ├── tesseract.example.json     # Example project marker
        ├── config.example.json
        └── pm-clickup.example.json
```

## Skills: Domain-Based Organization

Skills are organized by domain, with each domain containing phase-specific skills. The `general/` directory holds domain-agnostic orchestrators that detect the active domain and delegate to domain-specific skills when available, falling back to general defaults when not.

### Resolution Logic

When a phase runs (e.g., "review"):
1. Read `.tesseract.json` to get active domains
2. Check if `skills/<domain>/review/SKILL.md` exists for each active domain
3. **All matching domain skills run** (fan-out). If a project has `domains: ["terraform", "atmos"]` and both have `review/SKILL.md`, both run. The orchestrator dispatches them in parallel and merges findings.
4. If no domain-specific skill exists for any active domain, fall back to `skills/general/code-review/SKILL.md`
5. The `general/` skill always runs as a baseline — domain-specific skills add to it, they don't replace it

### Adding a New Domain

To add support for a new language/framework (e.g., Python):
1. Create `skills/python/` directory
2. Add only the phase skills that need domain-specific behavior (e.g., `review/SKILL.md`, `implement/SKILL.md`)
3. Phases without a domain-specific skill fall back to `general/`
4. No changes needed to orchestrators or agents

## Agents: Multi-Mode Reviewers

10 agents across 2 plugins → 7 multi-mode agents in one location.

Each agent file contains:
- A shared persona section (voice, expertise, mindset)
- A plan review checklist (lightweight, 10-15 checks)
- An infra-code review checklist (deep, 25-40 checks) — where applicable
- An app-code review checklist — where applicable
- The dispatching skill tells the agent which mode to use

### Agent Inventory

| Agent | Plan Review | Infra Code Review | App Code Review |
|-------|:-----------:|:-----------------:|:---------------:|
| security-reviewer | 14 checks | 29 checks | Deferred to v2 (OWASP, auth, data exposure) |
| cost-reviewer | 10 checks | 24 checks | — |
| architecture-reviewer | 8 checks | 42 checks | Deferred to v2 (service design, API quality) |
| operations-reviewer | 7 checks | 31 checks | Deferred to v2 (logging, monitoring, CI/CD) |
| well-architected-reviewer | — | 6 pillars | — |
| agile-coach-reviewer | 10 checks | — | — |
| dx-engineer-reviewer | 15 checks | — | — |

### Review Command Hierarchy

`/review` is the top-level orchestrator. It invokes everything — domain skills, reviewer agents, and acceptance criteria verification. Single-agent commands (`/review-security`, `/review-cost`, etc.) run one specific agent in isolation.

```
/review (comprehensive — one command does everything)
├── 1. Code correctness review
│   ├── Logic bugs, error handling, edge cases
│   ├── Style and consistency
│   └── Test coverage gaps
├── 2. Domain-specific review skills
│   ├── terraform/review (HCL lint, Checkov, provider patterns)
│   ├── atmos/review (stack YAML, catalog, hygiene)
│   └── ... (based on detected domains and changed files)
├── 3. Agent reviews (selected by auto-detect + user overrides)
│   ├── security-reviewer
│   ├── cost-reviewer
│   ├── architecture-reviewer
│   ├── operations-reviewer
│   └── ...
├── 4. Acceptance criteria verification (if active story context)
├── 5. Merge all findings, deduplicate, sort by severity
└── 6. Present to user (pick fixes, discuss, optionally post to PM)

/review-security (single agent shortcut)
└── Dispatch security-reviewer only

/review-cost, /review-well-architected, etc.
└── Single agent shortcuts for targeted re-runs
```

### Review Depth by Context

The same `/review` command adapts its depth based on how it's invoked:

| Context | Scope | What runs | Speed |
|---------|-------|----------|-------|
| Pre-commit hook | Staged files only | Checks at/above `block_threshold` severity only | Seconds |
| Per-step (during implementation) | Changed files for current story | Full review: code + domain + agents + AC for current story | Minutes |
| Final review | All files in scope | Full review: code + domain + agents + AC for all stories | Minutes |
| `/review-security` | All files in scope | Security agent only, full depth | Fast |

The single-agent commands are useful for:
- Re-running a specific agent after fixing its findings
- Quick targeted checks (e.g., just security before pushing)

### Reviewer Selection

Reviewers are selected automatically based on content, with user overrides:

- **Auto-select (default):** detect file types and plan keywords → pick relevant reviewers
- **`always_include`:** these reviewers run regardless of auto-detection
- **`never_include`:** these reviewers are skipped even if auto-detected
- **Minimum 3 reviewers** for plan review (backfill by trigger keyword count)
- **DX Engineer + Agile Coach** always included when plan contains stories

## PM Adapter Interface

Abstract operations that every PM adapter must implement. Skills call these operations by name — never PM-specific tools directly.

| Operation | Description | ClickUp Implementation |
|-----------|-------------|----------------------|
| `pm_sync` | Diff plan sidecar JSON against PM state | `sprint_sync` (reads `list_relationship`) |
| `pm_bulk_create` | Create stories from sidecar, link to epics | `sprint_bulk_create` + `set_relationship` |
| `pm_bulk_update` | Batch update status/assignee/priority | `sprint_bulk_update` |
| `pm_get_status` | Get epic/story status overview | `sprint_status` |
| `pm_get_stories_for_epic` | Find stories linked to an epic | `list_relationship` query |
| `pm_link_story_to_epic` | Associate a story with its parent epic | Set `list_relationship` field |
| `pm_action_log` | Query past operations for audit | `sprint_action_log` |

### Adding a New PM Tool

To add Jira support:
1. Create `adapters/jira/` with its own MCP server
2. Implement the same tool names (`pm_sync`, `pm_bulk_create`, etc.)
3. Map Jira concepts (epics → epics, stories → issues, `list_relationship` → epic link)
4. No changes to skills or agents — they call the abstract operations

### Adapter Tiers

Not every PM tool needs a full custom adapter. The adapter layer is tiered based on what the PM tool's native MCP server already provides:

| Tier | When to use | What Shield provides | Example |
|------|-------------|---------------------|---------|
| **Tier 1: Native MCP covers full interface** | The PM tool's official MCP server already implements all `pm_*` operations (or equivalents) | A thin config mapping that renames native tools to the `pm_*` interface. No custom server code. | A hypothetical PM tool with bulk operations, sync, and relationship management built into its MCP server |
| **Tier 2: Native MCP is partial** | The PM tool's MCP server handles basic CRUD but lacks bulk operations, sync, or relationships | A custom adapter that wraps the native MCP server — delegates what it can, implements the rest. | ClickUp today — native MCP has task CRUD, Shield's adapter adds bulk ops, sync, relationships |
| **Tier 3: No MCP server** | The PM tool has only a REST API, no MCP server | A full adapter that implements the entire `pm_*` interface from scratch using the REST API. | A PM tool with only an HTTP API |

### Adapter Configuration

The PM config specifies which tier the adapter uses:

```json
// ~/.tesseract/projects/<project>/pm.json

// Tier 1 — native MCP, just map tool names
{
  "adapter": "linear",
  "adapter_mode": "native",
  "tool_mapping": {
    "pm_sync": "linear_sync_issues",
    "pm_bulk_create": "linear_bulk_create_issues",
    "pm_get_status": "linear_get_project_status"
  }
}

// Tier 2 — custom adapter wraps native (ClickUp)
{
  "adapter": "clickup",
  "adapter_mode": "hybrid",
  "workspace_id": "12345"
}

// Tier 3 — full custom adapter
{
  "adapter": "some-tool",
  "adapter_mode": "full",
  "base_url": "https://api.some-tool.com/v1"
}
```

For Tier 1, no custom server code is needed — Shield reads the `tool_mapping` and calls the native MCP tools directly using the mapped names. For Tiers 2 and 3, the adapter in `adapters/<tool>/` provides the MCP server.

### Capability Declaration

Each adapter (or native MCP server via tool mapping) exposes a `pm_get_capabilities` tool that returns a list of supported operation names. Skills call `pm_get_capabilities` once at the start of a PM interaction and skip any operations not in the returned list. For example, a minimal PM adapter might return `["pm_sync", "pm_get_status"]` — skills that need `pm_bulk_create` would inform the user that bulk creation is not available and offer manual alternatives.

## Plan Sidecar Format

Plan documents produce both human-readable HTML and a machine-readable JSON sidecar. PM adapters consume only the JSON.

```json
{
  "version": "1.0",
  "project": "VPC Redesign",
  "phase": "Phase 3 — Multi-Region Networking",
  "epics": [
    {
      "id": "EPIC-1",
      "name": "Base VPC with IPAM",
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "IPAM Pool Hierarchy",
          "status": "ready",
          "assignee": null,
          "priority": "high",
          "week": "W1-W2",
          "description": "Set up 3-tier IPAM pool hierarchy...",
          "tasks": [
            "Create top-level pool",
            "Create regional sub-pools",
            "Configure allocation rules"
          ],
          "acceptance_criteria": [
            "Regional pools allocate /20 CIDRs",
            "No CIDR overlap across regions"
          ],
          "pm_id": null,
          "pm_url": null
        }
      ]
    }
  ],
  "metadata": {
    "created_at": "2026-03-14",
    "domains": ["terraform"],
    "reviewer_grades": {}
  }
}
```

### Sidecar as Source of Truth

The plan sidecar JSON is the **single source of truth** for all structured data — stories, acceptance criteria, status, assignees, PM IDs. The HTML plan document is a rendered view that references the sidecar, not an independent copy of the data.

**How it works:**
- The `plan-docs` skill generates the sidecar JSON first, then renders the HTML from it
- The HTML embeds a reference to the sidecar path (e.g., `<meta name="sidecar" content="./plan-sidecar.json">`) so tools can locate the data source
- When acceptance criteria are edited (during AC confirmation or review), only the sidecar is updated — the HTML can be re-rendered from the updated sidecar
- PM adapters read the sidecar directly, never the HTML
- Review agents read acceptance criteria from the sidecar directly

**Auto-render on change:** Any operation that modifies the sidecar (AC confirmation edits, PM sync adding IDs, status updates during implementation) automatically re-renders the HTML afterward. The user never needs to manually re-render — the HTML file stays current as the pipeline progresses. Just refresh the browser tab to see the latest state.

This eliminates:
- Dual-write inconsistencies between HTML and JSON
- HTML parsing for structured data extraction
- Sync issues when criteria or status change mid-pipeline
- Manual re-render steps — the pipeline handles it

The sidecar is:
- Generated first during the planning phase, then used to render the HTML
- Updated throughout the pipeline (PM IDs added after sync, status updated during implementation, AC edited during confirmation)
- Stored in the run directory as the single source of truth for story state
- Every sidecar write triggers an HTML re-render automatically

## Configuration

### Project Marker (committed to repo)

```json
// .tesseract.json
{
  "project": "vpc-redesign",
  "domains": ["terraform", "atmos"],
  "external_skills": {
    "terraform": {
      "review": ["terraform-skills:validate"]
    }
  }
}
```

Identifies the project, declares active domains, and optionally maps external plugin skills to phases. Safe to commit — no sensitive data.

### Global Config (user home directory)

```
~/.tesseract/
├── config.json              # Global defaults
├── credentials.json         # All PM tokens
└── projects/
    └── vpc-redesign/        # Keyed by .tesseract.json "project"
        ├── pm.json          # PM adapter: workspace, naming config
        └── runs/            # Phase summary audit trail
```

### Config Files

**`~/.tesseract/config.json`** — Global defaults:
```json
{
  "reviewers": {
    "auto_select": true,
    "always_include": ["security"],
    "never_include": []
  },
  "pm_tool": "clickup",
  "review_on_commit": {
    "enabled": false,
    "block_threshold": "critical",
    "warn_threshold": "important"
  },
  "defaults": {
    "plan_format": "html",
    "summary_detail": "concise"
  }
}
```

**`~/.tesseract/credentials.json`** — PM tokens:
```json
{
  "clickup": {
    "api_token": "pk_..."
  },
  "jira": {
    "api_token": null,
    "base_url": null
  }
}
```

**`~/.tesseract/projects/<project>/pm.json`** — Project-specific PM config:
```json
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

### Resolution Order

When Shield needs a config value, it merges in this order (later wins):

1. **Plugin defaults** — hardcoded fallbacks in skill/agent logic
2. **`~/.tesseract/config.json`** — global user preferences
3. **`.tesseract.json`** — project marker (domains, project name)
4. **`~/.tesseract/projects/<project>/pm.json`** — project-specific PM config

## MCP Server Discovery

Claude Code looks for `.mcp.json` at the plugin root. Since adapters live in subdirectories (`adapters/clickup/`), the plugin root `.mcp.json` is generated dynamically based on the user's configured `pm_tool`.

The `session-start.sh` hook reads `~/.tesseract/config.json` to determine the active PM tool, then symlinks or copies the appropriate adapter's `.mcp.json` to the plugin root. If `pm_tool` is `"none"`, no MCP server is registered.

```
shield/.mcp.json  →  generated by session-start.sh from adapters/<pm_tool>/.mcp.json
```

## Hooks

### `session-start.sh` (SessionStart — runs on session start/resume)

1. Detect `.tesseract.json` in the working directory (walk up to repo root if needed)
2. Read the project name and active domains
3. Load `~/.tesseract/config.json` and `~/.tesseract/projects/<project>/pm.json`
4. If a PM tool is configured, set up MCP server config — copy the active adapter's `.mcp.json` to plugin root
5. Output a context summary to Claude: project name, active domains, PM tool, reviewer config
6. If `~/.tesseract/` or `.tesseract.json` is missing, output a setup prompt suggesting `shield init`

Note: dependency checks (e.g., `uv` for PM adapters) are **not** done at session start. They happen at the point of use — when a PM operation fails because `uv` is missing, the error handler prompts the user with install instructions. This keeps session start fast and avoids unnecessary warnings.

### `post-edit.sh` (PostToolUse — runs after Write/Edit on tracked file types)

1. Detect the file type of the edited file (`.tf`, `.yaml`, `.py`, etc.)
2. If the file matches an active domain, run lightweight lint checks:
   - Terraform: `terraform fmt -check`, `tflint` if available
   - YAML: basic schema validation if a schema is referenced
3. Output warnings to Claude context if lint fails — does not block the edit

## Plugin Permissions

The plugin's `plugin.json` must declare permissions to avoid prompting users for read access to files within the plugin directory. Without this, every time a skill reads a reference file or an orchestrator reads an agent definition, Claude Code asks for user permission.

```json
// shield/.claude-plugin/plugin.json
{
  "name": "shield",
  "permissions": {
    "allow": [
      "Read(${CLAUDE_PLUGIN_ROOT}/**)",
      "Glob(${CLAUDE_PLUGIN_ROOT}/**)",
      "Grep(${CLAUDE_PLUGIN_ROOT}/**)"
    ]
  }
}
```

This grants the plugin read-only access to its own directory tree. Skills, agents, hooks, and adapters can all reference each other's files without triggering permission prompts. No write permissions are declared — the plugin never modifies its own files at runtime.

## Review on Commit

Shield can optionally run a code review on staged changes before each commit. This is a `PreCommit` hook that is **disabled by default** and must be explicitly enabled by the user.

### Configuration

```json
// .tesseract.json or ~/.tesseract/config.json
{
  "review_on_commit": {
    "enabled": false,
    "block_threshold": "critical",
    "warn_threshold": "important"
  }
}
```

### Severity Levels

| Level | Examples | Description |
|-------|---------|-------------|
| **critical** | Wildcard IAM policies, hardcoded secrets, 0.0.0.0/0 on SSH, missing encryption on sensitive data | Must fix — security vulnerabilities or data exposure risks |
| **important** | Missing deletion protection, no backup config, overly broad security groups, missing cost controls | Should fix — reliability or cost risks |
| **warning** | Missing variable descriptions, style inconsistencies, missing tags, suboptimal patterns | Nice to fix — quality and maintainability |

### Threshold Behavior

The `block_threshold` controls what **blocks** the commit. The `warn_threshold` controls what gets **printed as a warning** even when the commit proceeds.

| Finding Severity | `block: critical` / `warn: important` | `block: important` / `warn: warning` | `block: none` (advisory only) |
|-----------------|---------------------------------------|--------------------------------------|-------------------------------|
| **Critical** | Blocks commit | Blocks commit | Warns only |
| **Important** | Warns, commit proceeds | Blocks commit | Warns only |
| **Warning** | Silent | Warns, commit proceeds | Warns only |

### How It Works

1. `pre-commit-review.sh` runs as a `PreCommit` hook
2. Reads `review_on_commit` config — if `enabled: false`, exits immediately (zero overhead)
3. Gets the list of staged files (`git diff --cached --name-only`)
4. Detects which domains are affected based on file types
5. Runs the relevant review agents in lightweight mode (only checks at or above `warn_threshold` severity)
6. Collects findings and applies threshold logic:
   - Findings at or above `block_threshold` → print errors, exit non-zero (commit blocked)
   - Findings between `warn_threshold` and `block_threshold` → print warnings, exit zero (commit proceeds)
   - Findings below `warn_threshold` → suppressed
7. If blocked, the user sees the findings and can fix them or bypass with `--no-verify` (standard git escape hatch)

### Lightweight Review Mode

The pre-commit review runs a **subset** of the full review — it only checks for issues at or above the `warn_threshold` severity. This keeps the review fast (seconds, not minutes) by skipping lower-priority checks. A full review with all agents and all severity levels is still available via `/review`.

## Schema Validation

JSON schemas in `schemas/` are validated programmatically:

- **`plan-sidecar.schema.json`** — validated when the sidecar is written (by `plan-docs` skill) and when read (by `pm-sync` skill). Write-time validation prevents malformed data from entering the pipeline. Read-time validation catches manual edits or version mismatches.
- **`config.schema.json`** — validated by `session-start.sh` when loading config. Invalid config produces a warning with the specific validation error, and falls back to plugin defaults.
- **`pm.schema.json`** — validated when `pm-sync` skill loads PM config. Missing required fields (e.g., `workspace_id`) produce a clear error prompting the user to run setup.

## Phase Summary Triggering

The `general/summarize/SKILL.md` skill is invoked automatically by each phase's orchestrator skill at the end of its execution. The orchestrator passes the phase name and a structured summary of what was done. The summarize skill:

1. Formats the summary as concise bullet points
2. Writes it to `~/.tesseract/projects/<project>/runs/<date>-<topic>/<phase>-summary.md`
3. Returns the summary text to the orchestrator, which displays it to the user
4. The user confirms before the next phase begins

Individual domain skills do not call summarize directly — only the `general/` orchestrator does, after collecting outputs from all domain skills that ran.

## Failure Modes

### PM connectivity failures
If the PM adapter's MCP server is unreachable or returns errors during `pm-sync`:
- The skill retries once after a 3-second delay
- If still failing, it informs the user with the error details and offers two options: skip PM sync and continue the pipeline, or abort and retry later
- The pipeline can proceed without PM sync — stories stay in the sidecar JSON and can be synced later

### Malformed sidecar JSON
If the plan sidecar fails schema validation on read:
- The skill reports the specific validation errors to the user
- Offers to regenerate the sidecar from the HTML plan document (using parsers as fallback)
- If the HTML is also missing or unparseable, the user must re-run the planning phase

### Missing dependencies
If a PM operation fails because a required tool (e.g., `uv`) is not on PATH:
- The skill detects the error and presents the user with install instructions (e.g., `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Offers to retry after installation or skip the PM operation
- Non-PM phases continue normally

### Missing credentials
If `~/.tesseract/credentials.json` is missing or lacks the required PM token:
- `session-start.sh` detects this and warns the user at session start
- PM-related commands (`/pm-sync`, `/pm-status`) fail gracefully with a message pointing to the setup steps
- Non-PM phases (research, planning, implementation, review) work normally without credentials

### Partial agent failures
If a reviewer agent fails mid-run (timeout, context overflow, unexpected error):
- The orchestrator continues with remaining agents — one agent's failure does not block others
- The final review summary notes which agents completed and which failed
- The user can re-run failed reviewers individually via single-domain commands (e.g., `/review-security`)

## Releases and Changelog

### Versioning

Shield follows [Semantic Versioning](https://semver.org/). The version lives in `.claude-plugin/marketplace.json` (for the marketplace) and `shield/.claude-plugin/plugin.json` is version-free (per Claude Code convention for relative-path plugins).

### Automated Releases with Release Please

Releases are automated using [Release Please](https://github.com/googleapis/release-please). The workflow:

1. Developers write commits using [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat:` — new feature (bumps minor)
   - `fix:` — bug fix (bumps patch)
   - `feat!:` or `BREAKING CHANGE:` — breaking change (bumps major)
   - `chore:`, `docs:`, `refactor:` — no version bump
2. On merge to `main`, Release Please opens/updates a release PR that:
   - Bumps the version in `.claude-plugin/marketplace.json`
   - Bumps `pyproject.toml` in the ClickUp adapter (if changed)
   - Updates `CHANGELOG.md` from commit messages
3. When the release PR is merged, Release Please:
   - Creates a git tag (e.g., `v2.0.0`)
   - Creates a GitHub Release with the same changelog content

### Changelog

Each plugin has its own `CHANGELOG.md` inside its directory (e.g., `shield/CHANGELOG.md`), following [Keep a Changelog](https://keepachangelog.com/) format. It is auto-generated by Release Please from conventional commits scoped to that plugin's directory, grouped by type (Added, Changed, Fixed, Removed).

The same content is mirrored to GitHub Release notes, so users can see the changelog either in the repo or on the Releases page.

### GitHub Actions Workflow

```yaml
# .github/workflows/release-please.yml
name: Release Please
on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: simple
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

### Monorepo Release Strategy

Tesseract is a marketplace that may contain multiple plugins over time. Each plugin is treated as a **separate Release Please package** with its own version, changelog, and release tag.

Release Please's `extra-files` jsonpath does not reliably support array filter expressions for targeting a specific plugin's version in `marketplace.json`. Instead, a post-release GitHub Actions step uses `jq` to update `marketplace.json` after Release Please creates the release.

### Release Please Config

```json
// release-please-config.json
{
  "packages": {
    "shield": {
      "release-type": "simple",
      "component": "shield",
      "changelog-path": "shield/CHANGELOG.md"
    }
  }
}
```

```json
// .release-please-manifest.json
{
  "shield": "2.0.0"
}
```

Adding a future plugin means adding another entry to both files. Each plugin gets independent versioning and release cycles.

### GitHub Actions Workflow

```yaml
# .github/workflows/release-please.yml
name: Release Please
on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4  # Latest major as of 2026-03
        id: release
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json

      - uses: actions/checkout@v6
        if: steps.release.outputs.releases_created
        with:
          ref: main

      - name: Update marketplace.json versions
        if: steps.release.outputs.releases_created
        run: |
          for path in $(echo '${{ steps.release.outputs.paths_released }}' | jq -r '.[]'); do
            plugin_name=$(basename "$path")
            version=$(jq -r --arg p "$path" '.[$p]' .release-please-manifest.json)
            jq --arg name "$plugin_name" --arg ver "$version" \
              '(.plugins[] | select(.name == $name)).version = $ver' \
              .claude-plugin/marketplace.json > tmp && mv tmp .claude-plugin/marketplace.json
          done
          git add .claude-plugin/marketplace.json
          git commit -m "chore: update marketplace plugin versions"
          git push

```

When Release Please creates a release, the full update flow is:
1. `shield/CHANGELOG.md` — new version section with grouped commit messages
2. `.release-please-manifest.json` — the tracked version for the released plugin
3. Git tag — e.g., `shield-v2.1.0`
4. GitHub Release — with the changelog content
5. `.claude-plugin/marketplace.json` — the plugin's `version` field (via post-release script)

## External Plugin Integration

Shield can leverage skills from other installed Claude Code plugins during its pipeline phases. This works through two mechanisms: auto-discovery and explicit configuration.

### Auto-Discovery

At session start, Shield scans the available skills list (injected into conversation context by Claude Code) for domain-relevant skills from other plugins. It matches by keyword — any skill name containing an active domain keyword (`terraform`, `python`, `kubernetes`, etc.) is flagged as a candidate.

When a candidate is found, Shield suggests it to the user during the relevant phase:

```
Discovered external skills for terraform:
  - terraform-skills:validate (from terraform-skills plugin)
  - terraform-skills:lint

Add these to your terraform workflow? [Y/n/pick]:
```

If the user accepts, Shield writes the mapping to `.tesseract.json` so it's remembered for future sessions. Auto-discovery runs again if new plugins are installed.

### Explicit Configuration

Users can directly map external plugin skills to Shield phases in `.tesseract.json`. Use domain names for domain-specific skills, and `"general"` for workflow-level skills that apply across all domains:

```json
{
  "project": "vpc-redesign",
  "domains": ["terraform", "atmos"],
  "external_skills": {
    "general": {
      "implement": ["superpowers:test-driven-development", "superpowers:executing-plans"],
      "review": ["superpowers:verification-before-completion"],
      "debug": ["superpowers:systematic-debugging"]
    },
    "terraform": {
      "implement": ["terraform-skills:scaffold"],
      "review": ["terraform-skills:validate", "terraform-skills:lint"]
    }
  }
}
```

### How It Works

1. During each phase, Shield checks `external_skills` config for both `"general"` and the active domain
2. External skills are invoked **alongside** Shield's own skills, not as replacements
3. `"general"` external skills run for every phase regardless of domain — these are workflow-level enhancements (e.g., TDD, plan execution, debugging from superpowers)
4. Domain external skills run only when that domain is active
5. Findings from external skills are merged into the same review output / summary
6. If an external skill is unavailable (plugin uninstalled), Shield warns and continues without it — the built-in fallback handles the workflow

### Design Principles

- **Shield always works standalone** — no feature is gated behind external plugins. Built-in fallbacks are functional, just less sophisticated.
- **No coupled releases** — external plugins can update independently. If a skill interface changes, Shield gracefully falls back to built-in logic.
- **Enhancement, not replacement** — external plugins make Shield better, but Shield's core value (review agents, PM adapters, AC verification, sidecar format) works regardless.

## Testing

Shield has three layers of testing to ensure plugin quality.

### Plugin Tests

Verify that Shield's components load and function correctly when installed.

- **Config parsing** — valid configs load correctly, invalid configs produce clear errors and fall back to defaults
- **Sidecar schema validation** — valid sidecar JSON passes, malformed JSON fails with specific errors
- **Command registration** — all slash commands are discoverable after install
- **Hook execution** — `session-start.sh` detects project markers, `post-edit.sh` runs lint, `pre-commit-review.sh` respects threshold config
- **Skill resolution** — domain-specific skills are selected when available, general fallbacks work when not
- **External plugin discovery** — auto-discovery correctly identifies domain-relevant skills from mock plugin lists

### MCP Server Tests

Unit and integration tests for the PM adapter Python code (pytest).

- **Unit tests** — each tool (`pm_sync`, `pm_bulk_create`, etc.) tested with mocked ClickUp API responses
- **Parser tests** — sidecar JSON correctly transforms to ClickUp task format and back
- **Config tests** — credentials loading, project config resolution, missing field handling
- **Action log tests** — operations are logged correctly, queryable by date/type
- **Integration tests** — end-to-end flow against a ClickUp sandbox workspace (optional, requires API token)

### Agent/Skill Evals

Criteria-based evals that verify agents and skills produce correct findings. Since LLM output is non-deterministic, evals use **must-find / should-find / must-not-false-positive** criteria instead of exact golden-file matches.

#### Agent Evals

Each agent is fed a known input (a sample Terraform module with deliberate issues, a plan doc with gaps) and evaluated against criteria:

```yaml
# evals/criteria/security-reviewer-terraform.yaml
input: evals/inputs/insecure-vpc-module/
mode: infra-code
must_find:
  - id: wildcard-iam
    description: "Flags Action = * in IAM policy"
    match: "wildcard|Action.*\\*"
  - id: open-sg
    description: "Flags 0.0.0.0/0 on port 22"
    match: "0\\.0\\.0\\.0/0.*22|SSH.*open"
  - id: hardcoded-secret
    description: "Flags hardcoded API key in variables.tf"
    match: "hardcoded|secret|credential"
should_find:
  - id: missing-encryption
    description: "Flags CloudWatch log group without KMS"
    match: "kms_key_id|encryption"
must_not_false_positive:
  - id: valid-sg-rule
    description: "Should not flag port 443 open to 0.0.0.0/0 (intentional for ALB)"
    match_absence_in: "443.*0\\.0\\.0\\.0/0"
```

- **must_find** — eval fails if the agent does not surface this finding. Regex match against agent output.
- **should_find** — eval warns but does not fail. Tracks improvement over time.
- **must_not_false_positive** — eval fails if the agent flags this as an issue (it's intentionally correct).

Eval results:
- All `must_find` matched + no `must_not_false_positive` triggered = **PASS**
- Any `must_find` missed = **FAIL**
- Any `must_not_false_positive` triggered = **FAIL**
- `should_find` misses = **WARN** (logged for tracking, does not fail CI)

#### Skill Evals

- **Plan-docs** — given requirements, produces sidecar JSON that passes schema validation. Verifies epics, stories, acceptance criteria are present.
- **Plan-review** — given a plan with specific keywords, dispatches correct reviewers. Verified by checking agent dispatch calls.
- **Summarize** — given phase output, produces concise bullet points under a line count threshold. Writes to correct path.
- **Skill resolution** — given a domain config, selects the correct domain-specific skill or falls back to general.

### PM Adapter Contract Tests

Verify that every PM adapter conforms to the `pm_*` interface contract. These tests are adapter-agnostic — the same test suite runs against any adapter.

- **Schema compliance** — each `pm_*` tool accepts the documented input schema and returns the documented output schema
- **Capability honesty** — `pm_get_capabilities` returns only operations the adapter actually implements. Calling a declared capability must not error with "not implemented".
- **Idempotency** — `pm_sync` called twice with no changes produces the same diff (empty)
- **Error handling** — adapter returns structured errors (not stack traces) for invalid inputs, missing auth, network failures

For the ClickUp adapter, contract tests run against mocked API responses. For Tier 1 (native MCP) adapters, contract tests verify tool name mapping translates inputs and outputs correctly.

```bash
# Run contract tests against a specific adapter
./scripts/test-adapter-contract.sh clickup
```

### Pipeline Integration Tests

End-to-end tests that verify the full pipeline using the example projects. These catch broken handoffs between phases.

- **Sidecar lifecycle** — verify the sidecar is created during planning, updated during PM sync (IDs added), updated during AC confirmation (criteria edited), updated during implementation (status changes), and read correctly during review. Each mutation triggers HTML re-render.
- **Phase handoff** — verify each phase's summary is written to the correct path and the next phase can read the previous phase's output
- **Config resolution** — verify the merge order (plugin defaults → global → project marker → project PM config) produces the expected resolved config
- **Review depth** — verify per-step review only checks changed files, final review checks all files

These tests run against the `terraform-vpc` and `python-api` example projects with mocked PM responses.

### External Plugin Integration Tests

Test Shield's external plugin discovery and invocation without requiring real external plugins.

- **Auto-discovery tests** — inject a mock available skills list into the test context and verify:
  - Domain-relevant skills are correctly identified (e.g., `terraform-skills:validate` matched for `terraform` domain)
  - Irrelevant skills are ignored (e.g., `cooking-tips:recipe` not suggested)
  - Suggested skills are written to `.tesseract.json` when accepted
- **Invocation tests** — create stub skill files that accept known inputs and return predictable output, then verify:
  - Shield invokes the correct external skill at the correct phase
  - External skill output is merged into Shield's findings/summary
  - Findings are deduplicated when external and internal skills flag the same issue
- **Fallback tests** — configure external skills in `.tesseract.json`, then remove them and verify:
  - Shield warns that the skill is unavailable
  - Built-in fallback handles the phase without errors
  - No crash or hang when an external skill is missing
- **Tier 1 tool mapping tests** — mock a native MCP server's responses and verify:
  - Tool name mapping translates `pm_sync` → native tool name correctly
  - Input/output schemas are translated between Shield's format and native format
  - Unmapped capabilities are correctly excluded from `pm_get_capabilities`

### CI Integration

All three test layers run in GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  plugin-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: Run plugin tests
        run: ./scripts/test-plugin.sh

  mcp-server-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v4
      - name: Run MCP server tests
        run: cd shield/adapters/clickup && uv run pytest

  agent-evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: Run agent evals
        run: ./scripts/run-evals.sh
```

## Examples

Two example projects demonstrate the full Shield pipeline. Each includes a walkthrough README and per-phase GIFs recorded with [VHS](https://github.com/charmbracelet/vhs).

### Directory Structure

```
shield/examples/
├── terraform-vpc/                    # Infrastructure example
│   ├── README.md                     # Step-by-step walkthrough
│   ├── .tesseract.json               # Pre-configured project marker
│   ├── src/                          # Sample Terraform VPC module
│   │   ├── main.tf                   # Deliberately includes reviewable issues
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── gifs/                         # Per-phase recordings
│   │   ├── 01-research.gif
│   │   ├── 02-planning.gif
│   │   ├── 03-plan-review.gif
│   │   ├── 04-pm-sync.gif
│   │   ├── 05-ac-confirmation.gif
│   │   ├── 06-implement.gif
│   │   ├── 07-code-review.gif
│   │   └── 08-final-review.gif
│   └── tapes/                        # VHS tape scripts (reproducible)
│       ├── 01-research.tape
│       ├── 02-planning.tape
│       └── ...
│
└── python-api/                       # Application example
    ├── README.md
    ├── .tesseract.json
    ├── src/                          # Sample FastAPI application
    │   ├── main.py
    │   ├── routes/
    │   └── tests/
    ├── gifs/
    │   ├── 01-research.gif
    │   └── ...
    └── tapes/
        └── ...
```

### Infrastructure Example (terraform-vpc)

A Terraform VPC module with deliberate issues for the reviewers to find:
- A wildcard IAM policy (security reviewer catches it)
- NAT gateways without a disable flag (cost reviewer catches it)
- Missing IPAM pool hierarchy layer (architecture reviewer catches it)
- No deletion protection on stateful resources (operations reviewer catches it)
- Acceptance criteria that can be verified against the implementation

The walkthrough takes users through the full pipeline: research AWS VPC best practices → plan the module → review the plan → sync to ClickUp → confirm AC → implement → code review per step → final review.

### Application Example (python-api)

A FastAPI application with typical issues:
- Missing input validation (security reviewer catches it)
- No error handling on external API calls (operations reviewer catches it)
- Vague acceptance criteria in the plan (agile coach catches it)
- Missing test coverage (DX engineer catches it)

Shows Shield working outside the infrastructure domain with the general review pipeline.

### GIF Recording

GIFs are recorded using VHS tape scripts — deterministic, reproducible, and version-controlled. To regenerate all GIFs:

```bash
cd shield/examples/terraform-vpc
for tape in tapes/*.tape; do vhs "$tape"; done
```

GIFs are committed to the repo so users see them immediately in the README without running anything.

## Migration from v1.x

Existing users have individual plugins installed from the Tesseract marketplace. Shield provides a `/shield migrate` command that automates the migration.

### Migration Command

`/shield migrate` detects the old plugin setup and migrates configuration automatically.

**What it does:**

1. **Detect old plugins** — scans for `sprint-planner.json`, `claude/infra-review/` directory, and old plugin markers in the project
2. **Create project marker** — generates `.tesseract.json` with project name (inferred from repo name or asked) and domains (inferred from detected plugins: `clickup-sprint-planner` → adds PM config, `infra-review` → adds `terraform`/`atmos` domains)
3. **Create `~/.tesseract/` directory structure** — sets up `config.json`, `credentials.json`, and `projects/<project>/`
4. **Migrate `sprint-planner.json`** — reads the old config and maps fields to the new format:
   | Old field (`sprint-planner.json`) | New location |
   |----------------------------------|-------------|
   | `workspace_id` | `~/.tesseract/projects/<project>/pm.json` → `workspace_id` |
   | `space_id` | `~/.tesseract/projects/<project>/pm.json` → `space_id` |
   | `naming.*` | `~/.tesseract/projects/<project>/pm.json` → `naming.*` |
   | `api_token` (if present) | `~/.tesseract/credentials.json` → `clickup.api_token` |
   | `CLICKUP_API_TOKEN` env var | Prompts user to add to `~/.tesseract/credentials.json` |
5. **Set global defaults** — creates `~/.tesseract/config.json` with sensible defaults (`pm_tool`, `reviewers`, `review_on_commit: false`)
6. **Show summary** — displays what was migrated, what needs manual action, and next steps

**Interactive flow:**

```
$ /shield migrate

Detected old plugins:
  - clickup-sprint-planner (sprint-planner.json found)
  - infra-review (claude/infra-review/ directory found)
  - dev-workflow (commands detected)

Project name [vpc-redesign]: ↵
Domains detected: terraform, atmos. Correct? [Y/n]: ↵

Migrating sprint-planner.json...
  ✓ workspace_id → ~/.tesseract/projects/vpc-redesign/pm.json
  ✓ space_id → ~/.tesseract/projects/vpc-redesign/pm.json
  ✓ naming config → ~/.tesseract/projects/vpc-redesign/pm.json
  ⚠ No API token found in config. Add to ~/.tesseract/credentials.json manually.

Created:
  ✓ .tesseract.json (project marker)
  ✓ ~/.tesseract/config.json (global defaults)
  ✓ ~/.tesseract/projects/vpc-redesign/pm.json (PM config)

Old files left in place (safe to delete after verifying):
  - sprint-planner.json
  - claude/infra-review/

Next steps:
  1. Add API token to ~/.tesseract/credentials.json
  2. Uninstall old plugins: infra-review, clickup-sprint-planner, dev-workflow
  3. Run /pm-status to verify ClickUp connection
```

### Fresh Setup

For new users without old plugins, `/shield init` runs the setup without migration:

1. Asks for project name and domains
2. Creates `.tesseract.json`
3. Creates `~/.tesseract/` directory structure with defaults
4. If PM tool is configured:
   - Checks for `uv` on PATH — if missing, offers to install it (`curl -LsSf https://astral.sh/uv/install.sh | sh`) or skip PM setup for now
   - Prompts for workspace details and credentials
   - Validates the setup (tests PM connection if credentials provided)
5. If PM tool is skipped or set to `"none"`, completes setup without PM — user can add it later by editing config and re-running `/shield init`

### Data Continuity

- **Existing sprint state in ClickUp is unaffected.** The PM adapter reads from ClickUp directly — there is no local sprint state to migrate. Stories, epics, and relationships in ClickUp remain intact.
- **Action logs from the old plugin are not migrated.** The old `clickup-sprint-planner` action log format is incompatible with the new run directory structure. Old logs can be kept for reference but are not read by Shield.
- **Old review reports** (e.g., `claude/infra-review/review.md`) are not migrated. They remain in the project directory as static files. Shield writes new reviews to `~/.tesseract/projects/<project>/runs/`.
- **In-flight work:** If a user has an active sprint mid-sync, they should complete the sync with the old plugin before migrating, or re-sync from the plan document after installing Shield.
- **Old config files are not deleted.** The migration command leaves `sprint-planner.json` and other old files in place. The user deletes them after verifying the migration worked.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Plugin structure | Single plugin (Shield) in marketplace (Tesseract) | Keeps marketplace for future extensibility, single plugin eliminates agent duplication |
| Skill organization | By domain (`terraform/`, `atmos/`), then by phase | Adding a new domain = one directory. Each domain is self-contained. |
| Agent organization | Flat, multi-mode | One file per domain persona. Mode (plan/infra/app) selected by dispatcher. |
| PM abstraction | Tiered adapters with shared interface | Tier 1: tool name mapping to native MCP. Tier 2: custom adapter wrapping native MCP. Tier 3: full adapter from REST API. Skills always call abstract `pm_*` operations. |
| Plan format | JSON sidecar (source of truth) + HTML (rendered view) | Sidecar is the single source of truth. HTML references and renders from the sidecar. No dual-write, no HTML parsing. |
| Config storage | Project marker in repo + `~/.tesseract/` for everything else | Clean project root. No sensitive data in repo. Team shares domain config via marker. |
| Review model | Continuous with user-driven fix selection | Review after planning and each impl step. User picks which fixes to apply. Optionally posts findings to PM. |
| Domain support | Infrastructure + application, user-configured | `domains` field in `.tesseract.json`. Skills fall back to `general/` when no domain-specific override exists. |
| Review on commit | PreCommit hook, disabled by default, severity thresholds | Lightweight review on staged changes. `block_threshold` controls what blocks, `warn_threshold` controls what prints. |
| Plugin permissions | Pre-authorized read access to own directory | Eliminates permission prompts when skills/agents read reference files within the plugin. |
| Releases | Automated via Release Please with conventional commits | Auto-generated changelog, git tags, and GitHub Releases on merge to main. |
| External plugins | Auto-discover + explicit config, `"general"` for workflow-level skills | Discover and integrate skills from any installed plugin (superpowers, terraform-skills, etc.). Domain skills mapped by domain name, workflow skills mapped to `"general"`. All optional with built-in fallbacks. |
