# Research Transcript — Behavior Decomposition for Single-Agent LLM Reviewers

**Date:** 2026-05-20
**Feature folder:** `agent-behavior-decomposition-20260520`
**Depth mode:** standard
**Phase 2 ran:** yes (see `findings.md`)

## Detected Context

### Stack
- Claude Code plugin marketplace (confirmed) — *from `.claude-plugin/marketplace.json`, multiple plugin dirs*
- Markdown-defined agents/skills + Python (uv) for adapters (confirmed) — *from `shield/agents/*.md`, `pyproject.toml` files in adapters*

### Integrations
- N/A — this is a developer-tool plugin, not a product with runtime integrations (confirmed)

### Compliance markers
- None detected — not applicable (confirmed)

### Deployment pattern
- Distributed as a Claude Code plugin via `marketplace.json` (confirmed)

### Recent activity
- `shield/agents/product-manager-reviewer.md` — modified in recent PRs (commits `dcca4ca`, `8dbe455`, `42683e7`) — adding research-framing/research-review modes + PF7/PF8 framework (confirmed) — *git log*
- `shield/skills/general/prd-review/` — added in PR #35 ("Feature: prd and research redesign"), then expanded in #41, #42 (confirmed)

### Past decisions / ADRs
- `docs/adr/0001-introduce-prd-layer.md` (untracked, dated 2026-05-18) — context for the PRD layer (confirmed)
- No ADRs on agent/persona structure (confirmed)

### Prior Shield artifacts
- `docs/shield/devcontainer-implement-20260518/research/1-claude-implement-isolation/` — unrelated topic (confirmed)
- No prior research on agent design / behavior decomposition (confirmed)

### Existing agent inventory (relevant)
- 10 reviewer agents in `shield/agents/` — all single-file, single-persona-per-file (confirmed)
- PM reviewer alone has 4 modes (Research Framing, Research Review, Plan Review, Standalone) and owns 9 of 13 PRD rubric dimensions (confirmed)
- All other reviewers (agile-coach, tech-lead, DX, cost) own 1-2 dimensions each (confirmed)

## Product Context

### Problem
✓ (from invocation topic): PM agent grades 9 dimensions in one shot → shallow output. Want explicit behaviors with name/trigger/checks/exceptions/output_shape so the agent walks each behavior deliberately. Tech-lead agent has the same shape problem in compressed form (2 dims with 6-7 eval points each).

### Users
- Primary: Shield agent authors (the maintainers extending reviewer agents). Direct ergonomic impact.
- Secondary: Shield-marketplace consumers (teams installing Shield plugins) — they consume the depth-of-output improvement.
- Tertiary: PRD authors who get reviewed; orchestrator (`shield:prd-review` skill); future persona authors (security/SRE).

### Evidence
- [unanswered] — Shield-specific quantitative baseline not measured. The FLASK paper (~4 Spearman-point improvement with per-skill scoring) and Gawande's WHO checklist study (~47% complication reduction, mortality ↓40%) are the cited evidence the problem class is real. Addressed in `findings.md` Migration Path via a distinct-finding-count baseline to be captured before PR 1.

### Alternatives
✓ (from invocation topic, surveyed in Phase 2 streams): Anthropic Agent SDK patterns, LangChain `Tool`/`AgentExecutor`, CrewAI `Task`, AutoGen, OpenAI Assistants. Eval frameworks: Inspect AI, promptfoo, OpenAI Evals, G-Eval, MT-Bench, FLASK. Software patterns: Strategy, Chain of Responsibility, BDD. Human review checklists: medical (Gawande, CONSORT), aviation (FMEA), legal due diligence.

### Success criteria
User-selected (multi-select):
- ✓ Eval suite on test PRDs catches more graded gaps
- ✓ Agent file stays under reasonable size
- ✓ Easier to extend (new dim = new behavior file/section, no agent-prompt edits)
- ✗ Per-behavior reasoning visible in agent output (not selected — auditability is secondary)

### Why now
[unanswered] — not asked explicitly. Implicit signal: user is mid-session evaluating whether to ship a refactor PR; the framing brief flagged "decision urgency" accordingly.

## Technical Context

### Existing systems
- `shield/agents/product-manager-reviewer.md` (211 lines) — 4 modes, PF1-PF11 (Research Framing) + PM1-PM11 (Review modes)
- `shield/agents/architecture-reviewer.md` (tech-lead) — owns rubric dims 5 + 6
- `shield/skills/general/prd-review/` — `personas.md` dispatch table (5 personas), `rubric.md` (13 dims), `scoring.md` (composite + P0-gate)
- 8 other reviewer agents in `shield/agents/` (agile-coach, cost, DX, backend, kubernetes, operations, security, well-architected)

### Constraints
Implicit baseline (asked but not answered explicitly; all four assumed):
- Must remain a Claude Code subagent (markdown frontmatter + Agent tool dispatch)
- Token budget mindful for single-dispatch agent context
- Output must remain JSON-parseable for orchestrator aggregation
- No new runtime dependencies (no new Python packages, no MCP servers)

User-confirmed:
- Backwards-compat: **breaking changes acceptable if migration documented** (NOT "existing dispatches must keep working unchanged")

### Integration points
- `shield:prd-review` orchestrator skill (parses returned JSON, applies `scoring.md` formula)
- `shield:plan-review` skill (uses PM in Plan-Review mode — out of scope for v0)
- `shield:research` skill (uses PM in Research-Framing + Research-Review modes — out of scope for v0)
- `shield/evals/` — needs a mapper between old PM1-PM11 IDs and new behavior names

### Technical risks
Enumerated in `findings.md` Migration Path:
1. Prompt-cache invalidation (cache-miss on first 1-2 dispatches per environment)
2. Token budget per dispatch (~211 → ~400 lines for PM agent)
3. Eval-suite drift (old cases reference PM1-PM11; new ones reference behavior names)
4. Other modes (Research Framing/Review, Plan Review) — preserve PM1-PM11 inside those modes; behaviors are PRD-Review-mode-only initially
5. Markdown-vs-JSON tension (community precedent emits markdown findings; Shield is JSON-first)

### Scope
**In scope:**
- Restructure `shield/agents/product-manager-reviewer.md` and `shield/agents/architecture-reviewer.md` from flat enumeration to named behaviors (in PRD-Review mode only).
- File-format choice + rationale.
- JSON output envelope each agent emits.
- Migration plan documentation.
- Eval-suite implications (new metric: distinct-finding-count baseline).

**Out of scope:**
- agile-coach agent (already has AC1-AC12 behavior-shaped structure — user explicitly excluded)
- Security, SRE, data-PM, design persona agents (future template consumers)
- `shield/rubric.md` dimension-ownership changes
- `shield:prd-review` orchestrator rewrite (only its input contract from PM/tech-lead is touched)
- New runtime deps / harness changes
- Cross-plugin changes (`infra-review`, `clickup-sprint-planner`, `dev-workflow` untouched)

## Open Questions (after Phase 1)

1. **JSON output envelope & orchestrator consumption** — what shape do Anthropic/OpenAI docs recommend? How does the Claude Code subagent format constrain output shape?
2. **Inline vs per-file behavior definitions** — what have other Claude Code / agent projects actually shipped?
3. **Minimum-viable behavior schema** — which fields are mandatory vs optional?
4. **Does decomposition produce deeper LLM-judge output empirically?**
5. **Cross-cutting / conflict handling** — what patterns exist for overlapping behaviors?
6. **Migration mechanics** — any vendor guidance on safely refactoring agent prompts?

All six addressed in `findings.md`. See that file for cited answers.

## Phase 2 — External Findings

See `findings.md` in this directory.

Summary of decision (from findings.md, after revision):

> Adopt a named-behavior structure for the PM and tech-lead reviewer agents, with each behavior defined as its own file under `shield/agents/behaviors/` — a flat catalog read on-demand by the agent. Each agent.md gets a lean `## Behaviors` section that lists owned behavior file paths with the rubric dimension each contributes to. Behavior files are agent-agnostic (frontmatter holds only `name`; no `owned_by` or `owned_dim`); the agent.md is the authoritative index mapping behaviors → dimensions. Output is a JSON envelope wrapping per-behavior findings.

Rejected alternatives:
- **Inline `## Behaviors` section in agent.md** — original recommendation, reversed after recognizing it doubles agent file size and pre-loads behaviors that may not fire
- **Per-agent nested dirs** (`shield/agents/pm/behaviors/`) — risks colliding with Claude Code subagent loader
- **Per-agent metadata in behavior frontmatter** — two sources of truth that drift; pre-commits a behavior to one owner
- **Flat status quo** — anti-pattern producing shallow output today

Final grade from PM research-review: **A-** with one P0 (define a measurable merge-gate metric) — addressed via distinct-finding-count baseline in the Migration Path. *Note: PM review was produced against the earlier inline shape; the scoring stays a useful pressure-test of the underlying "decompose into behaviors" decision, but its specific file-structure commentary is now stale.*

**Revision history:**
- 2026-05-20 initial draft — recommended inline `## Behaviors` section
- 2026-05-20 revised — switched to flat catalog at `shield/agents/behaviors/` with on-demand loading after user pushback on file size and clarification of "read when needed" pattern; dropped `owned_by`/`owned_dim` from behavior frontmatter to preserve single source of truth.
