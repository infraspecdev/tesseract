# Behavior Decomposition for Single-Agent LLM Reviewers

**Status:** Proposed (revised after PM review)
**Date:** 2026-05-20
**Last revision:** 2026-05-20 — file structure changed from "inline `## Behaviors` section" to "flat catalog at `shield/agents/behaviors/` with on-demand loading" after user-directed re-examination of file-size, on-demand loading, and single-source-of-truth tradeoffs. See revised Decision section. The Product Lens (PM Research Review) below was produced against the earlier inline shape; its scores remain a useful pressure-test of the underlying decision (decompose into behaviors) but its specific commentary on file structure is now stale.
**Context:** Shield's PM reviewer agent grades 9 of 13 PRD-review rubric dimensions in a single dispatch, producing visibly shallow output. We're considering restructuring `shield/agents/product-manager-reviewer.md` and `shield/agents/architecture-reviewer.md` around named, explicit *behaviors* — each with name, trigger, purpose, inputs, checks with severities, exceptions, and output shape. This research informs the file-structure choice, schema, output envelope, and migration path.

## Decision

**Adopt a named-behavior structure for the PM and tech-lead reviewer agents, with each behavior defined as its own file under `shield/agents/behaviors/` — a flat catalog read on-demand by the agent.** Each agent.md gets a lean `## Behaviors` section that lists owned behavior file paths with the rubric dimension each contributes to; at dispatch time, the agent Reads each behavior file in sequence and applies it.

**Behavior files are agent-agnostic.** Frontmatter holds only `name` (kebab-case, matches filename). Body holds description, when_active, inputs, checks-with-severity, exceptions, output_shape. The agent.md is the **authoritative index** that maps a behavior to a rubric dimension and an execution order — *not* the behavior file itself. This keeps single-source-of-truth clean and enables future cross-agent sharing without renaming or rewriting behavior files.

Rationale: matches Shield's existing skill→helper pattern (`SKILL.md` references `repo-scan.md` etc.), keeps each agent.md lean (~150 lines instead of doubling to ~400+), pays token cost on-demand (a 9-behavior PM dispatch reads 9 files; a 3-behavior partial run reads 3), and makes adding a behavior a one-file PR. Hits all three user-confirmed success criteria: eval-targetable per behavior, agent file stays bounded, new dim = new file with no agent-prompt edits.

**Reject:**
- **Inline `## Behaviors` in agent.md** (original recommendation) — doubles agent file size; pre-loads full behavior surface on every dispatch even when behaviors don't fire; harder to share across agents later.
- **Per-agent nested dirs** (e.g., `shield/agents/pm/behaviors/`) — risks colliding with the Claude Code subagent loader which expects `agents/<name>.md`. Adjacent same-stem directory is ambiguous.
- **Per-agent metadata in behavior frontmatter** (`owned_by`, `owned_dim`) — two sources of truth that drift; pre-commits a behavior to one owner and blocks future reuse.
- **Flat PM1-PM11 / dim1-dim13 status quo** — the anti-pattern producing shallow output today; what VoltAgent's 20.2k★ catalog ships.

## Why Not [Alternative]?

| Option | Verdict | Why |
|---|---|---|
| **A. Shared catalog + on-demand load** (`shield/agents/behaviors/*.md`, referenced from agent.md) | **Selected** | Smallest agent.md (~150 lines); pay-per-use token cost (only fires-then-reads behaviors that run); mechanical to add a behavior; enables cross-agent sharing without rename. Mirrors Shield's existing skill→helper pattern. |
| B. Inline `## Behaviors` section in agent.md | Reject (revised) | Doubles agent file size (~211 → ~400+ lines); pre-loads full behavior surface on every dispatch even for behaviors that don't fire; harder to share. *Was originally the recommendation; reversed after recognizing on-demand load avoids both costs.* |
| C. Per-agent nested dirs (`shield/agents/pm/behaviors/`) | Reject | Risks colliding with the Claude Code subagent loader which expects `agents/<name>.md`. Adjacent same-stem directory is ambiguous; can break discovery. |
| D. One file per behavior, but with `owned_by`/`owned_dim` in behavior frontmatter | Reject | Two sources of truth between behavior file and agent.md → drift. Pre-commits a behavior to one owner, blocking future reuse without rename. Agent.md should be the *only* place ownership lives. |
| E. Keep flat PM1-PM11 / dim1-dim13 enumeration | Reject | Status quo. FLASK empirically beats this design by ~4 Spearman points; Schluntz/Zhang explicitly warn against it; Gawande's surgical study shows ~47% complication reduction switching *from* this pattern. |
| (Note on BMAD precedent) | N/A | BMAD ships a *single shared rubric file* referenced by one validator subagent. Shield's catalog is the multi-agent generalization of that pattern — one rubric per behavior, an agent picks which to compose. |

## What the Industry Recommends

### Atul Gawande (*The Checklist Manifesto*, 2009)
> *"Good checklists, on the other hand, are precise. They are efficient, to the point, and easy to use even in the most difficult situations. They do not try to spell out everything—a checklist cannot fly a plane. Instead, they provide reminders of only the most critical and important steps—the ones that even the highly skilled professional using them could miss. Good checklists are, above all, practical."*
> — Gawande, *The Checklist Manifesto*, ch. 6 ("The Checklist Factory"), Metropolitan Books, 2009

> *"You must define a clear pause point at which the checklist is supposed to be used... You must decide whether you want a DO-CONFIRM checklist or a READ-DO checklist."*
> — Gawande, same, ch. 6

> *"The rate of major in-patient complications following surgery fell from 11% in the baseline period to 7% after introduction of the checklist, a reduction of one third. Inpatient deaths following major operations fell by more than 40%."*
> — WHO press release on Haynes et al., *NEJM* 2009 ([who.int](https://www.who.int/news/item/11-12-2010-checklist-helps-reduce-surgical-complications-deaths))

This is the empirical warrant for the refactor. The current PM agent is functionally a "bad checklist" — it tries to spell out everything, has no pause points between dimensions, and turns the reviewer's deliberation off. Named behaviors with explicit `when_active` triggers are the DO-CONFIRM pattern applied to LLM grading.

### Dan North ("Introducing BDD", *Better Software*, 2006)
> *"What to call your test is easy: it's a sentence describing the next behaviour in which you are interested. How much to test becomes moot: you can only describe so much behaviour in a single sentence."*
> — Dan North, "Introducing BDD", *Better Software*, March 2006, [dannorth.net/introducing-bdd](https://dannorth.net/introducing-bdd/)

The load-bearing insight: a behavior is bounded by its name. `check_acceptance_criteria_are_testable` has natural scope; "grade dimension 4" does not. Shield's behavior names must be sentence-like statements of what the agent should look for.

### Liz Keogh ("Conversational Patterns in BDD", 2011)
> *"BDD isn't about the tools. It's about the conversations you have, exploring examples (or scenarios) of an application's behaviour, to see if everyone has the right understanding."*
> — Keogh, [lizkeogh.com](https://lizkeogh.com/2011/09/22/conversational-patterns-in-bdd/)

> *"You can sometimes learn a lot about a business domain this way, even if the behaviour of the application isn't going to change immediately!"*
> — Keogh, same

Implication: Shield's behavior definitions must be readable by humans (PMs, agent authors), not just by the LLM. The act of naming + exemplifying surfaces things the author didn't know needed checking. This argues for prose-readable behavior files over compact YAML.

### Erik Schluntz & Barry Zhang ("Building effective agents", Anthropic, Dec 2024)
> *"For complex tasks with multiple considerations, LLMs generally perform better when each consideration is handled by a separate LLM call, allowing focused attention on each specific aspect."*
> — Schluntz & Zhang, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

> *"Prompt chaining decomposes a task into a sequence of steps, where each LLM call processes the output of the previous one... This workflow is ideal for situations where the task can be easily and cleanly decomposed into fixed subtasks. The main goal is to trade off latency for higher accuracy, by making each LLM call an easier task."*
> — Schluntz & Zhang, same

Direct vendor endorsement of the refactor. Of their Five Patterns, **Prompt Chaining** maps cleanest — fixed sequence of named behaviors, each producing structured output for the next. Not Orchestrator-Workers (dynamic decomposition at runtime, overkill); not pure Parallelization (behaviors may depend on each other). Note: Shield does the chaining *within* a single subagent prompt by walking sections sequentially, rather than spawning N subagent calls — this is the cheaper variant that stays in budget.

### FLASK (Ye et al., ICLR 2024) — empirical evidence
> *"evaluators assess the target model's response by assigning scores ranging from 1 to 5, following skill-specific scoring rubrics"*
> — Ye et al., [FLASK](https://arxiv.org/abs/2307.10928), §3.3

> *"Fine-graininess leads to a high correlation between human-based and model-based evaluation"*
> — Ye et al., same, §4 (Spearman 0.680 skill-specific vs 0.641 skill-agnostic with GPT-4)

This is the cleanest experimental win for decomposition: same model, same task, per-skill scoring beats coarse scoring by ~4 Spearman points, and exposes per-skill failure modes invisible to a single overall score. Direct empirical justification for the refactor.

### Anthropic tool-definition schema (vendor spec)
> *"Each tool definition includes: `name` … `description` … `input_schema` — A JSON Schema object defining the expected parameters for the tool."*
> — [Define tools — Claude API Docs](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use)

> *"Provide extremely detailed descriptions. This is by far the most important factor in tool performance. Your descriptions should explain ... What the tool does ... When it should be used (and when it shouldn't) ... What each parameter means ... Any important caveats or limitations ..."*
> — Same source, "Best practices for tool definitions"

Shield's behavior schema should *inherit* Anthropic's tool-definition shape — `name + description + input_schema` is the vendor-canonical contract. Adding `when_active`, `checks`, `exceptions`, `owned_dim`, `output_shape` is a superset; the core (`name`, `description`) maps 1:1. Rename `when_active` → fold into `description` to stay aligned with Anthropic's "extremely detailed" guidance.

### Community precedent: BMAD-METHOD (47.7k★)
> *Path:* `src/bmm-skills/2-plan-workflows/bmad-prd/assets/prd-validation-checklist.md`
> *Structure:* shared rubric file referenced by a validator subagent; 7 named dimensions; each dimension has `Look for:` + `Red flag:` blocks + a verdict scale (`strong | adequate | thin | broken`) + severity tier (`critical | high | medium | low`); output is markdown, not JSON.

BMAD is the closest precedent in the open-source world to what Shield is building. The differences from Shield's proposed shape: BMAD uses one shared rubric file for one agent (not multiple agents); BMAD emits markdown findings (not JSON); BMAD calls them "dimensions" (not "behaviors"). The structural similarity is striking enough to warrant studying their file format directly during implementation.

### Community precedent: VoltAgent/awesome-claude-code-subagents (20.2k★)
~18 reviewer subagents at `categories/04-quality-security/*-reviewer.md`. **Pattern: flat inline bulleted checks, no severities, no triggers, no per-check structure.** This is the popular community default — and it produces exactly the shallow output Shield is trying to escape. Surfacing this as the **anti-pattern** to avoid.

## How This Works in Practice

### Repo layout

```
shield/agents/
├── product-manager-reviewer.md        ← lean agent.md (loaded by Claude Code)
├── architecture-reviewer.md            ← lean agent.md
├── ...8 other reviewer agents...
└── behaviors/                          ← flat shared catalog
    ├── problem-clarity.md              ← composed by PM
    ├── scope-discipline.md             ← composed by PM
    ├── measurable-success.md           ← composed by PM
    ├── raci-and-approvals.md           ← composed by PM
    ├── compliance-posture.md           ← composed by PM
    ├── gtm-comms.md                    ← composed by PM
    ├── support-readiness.md            ← composed by PM
    ├── strategic-timing.md             ← composed by PM
    ├── risk-articulation.md            ← composed by PM
    ├── perf-budget.md                  ← composed by tech-lead (dim 5a)
    ├── security-threat-model.md        ← composed by tech-lead (dim 5b)
    ├── rbac-matrix.md                  ← composed by tech-lead (dim 5c)
    ├── accessibility.md                ← composed by tech-lead (dim 5d)
    ├── privacy-and-retention.md        ← composed by tech-lead (dim 5e)
    ├── telemetry-completeness.md       ← composed by tech-lead (dim 5f)
    ├── i18n-l10n.md                    ← composed by tech-lead (dim 5g)
    ├── flag-plan.md                    ← composed by tech-lead (dim 6a)
    ├── canary-rollout.md               ← composed by tech-lead (dim 6b)
    ├── kill-switch.md                  ← composed by tech-lead (dim 6c)
    ├── abort-thresholds.md             ← composed by tech-lead (dim 6d)
    ├── data-migration.md               ← composed by tech-lead (dim 6e)
    └── backward-compatibility.md       ← composed by tech-lead (dim 6f)
```

The `behaviors/` directory is a sibling of the agent files at `shield/agents/`. Claude Code's subagent loader looks for `agents/<name>.md` and ignores subdirectories, so `behaviors/` doesn't interfere with agent discovery.

### Agent file (lean index)

`shield/agents/product-manager-reviewer.md`:

```markdown
---
name: product-manager-reviewer
description: Use this agent when evaluating user impact, scope discipline, ...
model: inherit
---

# Product Manager Reviewer

## Persona
[unchanged — Technical PM framing]

## Modes
[unchanged — Research Framing / Research Review / Plan Review / Standalone]

## Behaviors (PRD-Review mode)

When dispatched in PRD-Review mode, Read each behavior file below in order
and apply it to the PRD source. Emit a finding block per behavior, then a
final JSON envelope.

| # | Behavior file | Contributes to dim | Severity max |
|---|---|---|---|
| 1 | `shield/agents/behaviors/problem-clarity.md`       | 1  | Critical |
| 2 | `shield/agents/behaviors/scope-discipline.md`      | 2  | Critical |
| 3 | `shield/agents/behaviors/measurable-success.md`    | 3  | Critical |
| 4 | `shield/agents/behaviors/raci-and-approvals.md`    | 7  | Critical |
| 5 | `shield/agents/behaviors/compliance-posture.md`    | 8  | Critical |
| 6 | `shield/agents/behaviors/gtm-comms.md`             | 9  | Important |
| 7 | `shield/agents/behaviors/support-readiness.md`     | 10 | Critical |
| 8 | `shield/agents/behaviors/strategic-timing.md`      | 11 | Critical |
| 9 | `shield/agents/behaviors/risk-articulation.md`     | 12 | Critical |

## Execution protocol

For each behavior in the table above (in order):
1. Use the Read tool to load the behavior file.
2. Identify the PRD sections listed in the behavior's `Inputs`.
3. Evaluate each check in the behavior, producing per-check grades.
4. Apply any `Exceptions` (with reasoning) before grading.
5. Emit the per-behavior finding using the behavior's `Output shape`.

After all behaviors, emit the JSON envelope:

```json
{
  "persona": "shield:product-manager-reviewer",
  "persona_grade": "B",
  "behaviors": [
    { "name": "problem-clarity",   "dim": 1, "grade": "A", "checks": [...] },
    { "name": "scope-discipline",  "dim": 2, "grade": "C", "checks": [...] },
    ...
  ]
}
```

## Common Mistakes
[unchanged + new entries: forgetting to Read a behavior file; grading
without applying behavior's exception clauses; emitting findings without
the per-behavior output_shape]
```

### Behavior file (agent-agnostic)

`shield/agents/behaviors/problem-clarity.md`:

```markdown
---
name: problem-clarity
---

# Problem Clarity

**Description:** Verify the PRD names a specific persona (not "users") and grounds the problem in baseline data and urgency.

**When active:** PRD-Review mode, all PRD types.

**Inputs:**
- PRD §3 (Problem)
- PRD §4 (Personas)
- PRD §11 (Why now)

**Checks:**
- `1a` Named user/persona present (not "users") — **Critical**
- `1b` Baseline data (current state, numbers) — **Important**
- `1c` "Why now" articulated (urgency, opportunity cost) — **Warning**
- `1d` First-person user evidence or quotes — **Warning**

**Exceptions:**
- Single-purpose infrastructure features (e.g., cron job, backfill) may grade `1d` N/A with reasoning.

**Output shape:**
```json
{
  "name": "problem-clarity",
  "grade": "A|B|C|D|F",
  "checks": [
    { "id": "1a", "grade": "...", "severity": "Critical", "gap": "...", "suggestion": "..." },
    { "id": "1b", ... }
  ]
}
```
```

Notice: no `owned_by`, no `owned_dim` in the behavior frontmatter — those live in the agent.md's table above. The behavior file is reusable as-is by any future agent that wants to compose it.

### Tech-lead gets the same shape

`shield/agents/architecture-reviewer.md` lists ~13 behaviors covering dim 5 (NFR — perf-budget, security-threat-model, rbac-matrix, accessibility, privacy-and-retention, telemetry-completeness, i18n-l10n) and dim 6 (rollout — flag-plan, canary-rollout, kill-switch, abort-thresholds, data-migration, backward-compatibility). This is where the largest depth gain lives — tech-lead's 2 dims today carry 13 eval points; one deliberate pass per check is a major upgrade.

### Orchestrator changes

`shield:prd-review` already expects per-dim grades; the new envelope just adds the `behaviors[]` array as additional structure. The orchestrator can ignore behavior names initially and aggregate by `dim`. Behavior-level data becomes addressable in v2 (e.g., "show me only `compliance-posture` findings across last 10 PRDs"; "track regression in `external-dependency-resilience` checks over time").

## Migration Path / Reversibility

**Migration plan (3 PRs total — catalog convention first, then per-agent migrations):**

1. **PR 0 — Catalog convention.** Add empty `shield/agents/behaviors/` directory; document the convention in `shield/agents/behaviors/README.md` (file naming = kebab-case, frontmatter = `name` only, body schema = description/when_active/inputs/checks/exceptions/output_shape). Add a CONVENTIONS section to `CLAUDE.md`. Zero behavior changes; pure scaffolding so PR 1 + PR 2 land on a defined contract. *Tiny, mechanical, reviewable in 5 minutes.*

2. **PR 1 — PM agent restructure.** Create 9 behavior files in `shield/agents/behaviors/` for the PM-owned dims. Add `## Behaviors (PRD-Review mode)` section to `product-manager-reviewer.md` with the order/dim table and execution protocol. Update `shield/skills/general/prd-review/personas.md` dispatch prompt to reference the behavior protocol. Update `scoring.md` to consume the new envelope (with both-shapes acceptance). Keep PM1-PM11 in the file under "Legacy framework — used in Research-Review / Plan-Review / Standalone modes" so the agent's other 3 modes don't break. Eval suite verifies merge gate (see below).

3. **PR 2 — Tech-lead agent restructure.** Same treatment for `architecture-reviewer.md`. Create ~13 behavior files (dim 5 + dim 6 sub-behaviors). The biggest user-visible depth gain ships here because each tech-lead dim has 6-7 eval points today.

**Reversibility:** Each PR is reviewable in isolation. PR 0 is pure addition (no behavior change). PR 1 and PR 2 are single-agent edits — reverting one doesn't affect the other. The orchestrator's envelope reader stays backwards-compat-tolerant — accept both old (`{dim_grades:{}}`) and new (`{behaviors:[]}`) shapes during a transition window.

**Sequencing note (addresses PM review P1):** PM is sequenced first for *learning* — it has the larger surface area (9 of 13 dims), so structural issues with the catalog pattern surface earlier and inform PR 2. But tech-lead may carry the larger *user-visible depth gain* (2 dims → 13 behaviors). Reviewers should watch tech-lead's eval delta most closely.

**Merge-gate metric (addresses PM review P0):** Before merging PR 1, capture a baseline on `main` and gate the merge on a non-regression. Concrete proposal:

- **Metric:** *Distinct-finding count per fixture* — run the current PM agent against the 4 PRD-review test fixtures (`well-formed-standard.md`, `standard-with-gaps.md`, `lean-with-gaps.md`, `internal-tool.md`); count distinct, non-duplicate findings per fixture; sum across fixtures = baseline.
- **Gate:** PR 1 must produce ≥ baseline total finding count, AND no fixture regresses by more than 10%. Stretch goal: 1.3× baseline.
- **Why this metric:** measurable, automatable (no human judgment needed for v1), proxies "depth" via finding count, and directly answers "did decomposition produce more grounded findings or just longer prose?"
- **Where it lives:** `shield/evals/agent-decomposition/baseline.json` captured pre-PR; CI gate runs the fixture pass and asserts the comparison.
- A separate manual qualitative review (PM owner reads 1 fixture's findings pre and post) is also valuable but doesn't gate merge.

**Risks to enumerate in the migration doc:**
- **Prompt-cache invalidation** — the new agent.md is structurally different; expect a cache-miss on the first 1-2 dispatches per environment. Mitigated by Anthropic's caching being keyed on prefix; non-issue after first dispatch warms.
- **N+1 Reads per dispatch** — agent now reads 9 (PM) or 13 (tech-lead) behavior files per run. Each file is ~30 lines; total added tokens ~3-5k. Well within budget; flag for monitoring.
- **Eval-suite drift** — old eval cases reference `PM1`-`PM11` grades; new ones reference `behavior.problem-clarity.checks.1a`. Provide a one-time mapper script in PR 1.
- **Other modes (Research Framing/Review, Plan Review)** — preserve PM1-PM11 grading inside those modes. Behaviors are PRD-Review-mode only initially; expand later if signal is good.
- **Catalog drift** — agent.md's table could fall out of sync with files in `behaviors/`. Mitigated by a tiny lint script (`shield/scripts/verify-behavior-references.sh`) that errors if an agent references a non-existent behavior file. Add to CI.
- **Behavior file proliferation** — if every agent migration adds N files, `behaviors/` could grow to 50-100 entries. Acceptable for v0 (still grep-able), but flag for a v2 review if 3+ more agents migrate.

**Risks to enumerate in the migration doc:**
- **Prompt-cache invalidation** — the new agent.md is structurally different; expect a cache-miss on the first 1-2 dispatches per environment.
- **Token budget per dispatch** — adding ~200 lines of behavior structure to product-manager-reviewer.md (currently 211 lines → ~400 lines) is well within Claude Code subagent budget but worth measuring before/after.
- **Eval-suite drift** — old eval cases reference `PM1`-`PM11` grades; new ones reference `behavior.problem-clarity.checks.1a`. Provide a one-time mapper script in the PR.
- **Other modes (Research Framing/Review, Plan Review)** — preserve PM1-PM11 grading inside those modes. Behaviors are PRD-Review-mode only initially; expand later if signal is good.
- **Markdown-vs-JSON tension** — community precedent (BMAD, OpenMontage) emits structured markdown. Shield's orchestrator is JSON-first. Keep JSON envelope, but also write a per-behavior `findings.md` artifact for human readers.

## Summary

Four independent traditions — surgical safety (Gawande, 47% complication reduction), BDD (North, Keogh), LLM evaluation research (FLASK's 4-point Spearman improvement), and agent engineering (Schluntz/Zhang's explicit vendor endorsement) — converge on the same prescription: when an expert evaluates multiple aspects of a complex artifact, decompose into named, bounded, individually-checkable behaviors with explicit triggers and exceptions.

The community has *not* converged on a file structure for LLM agents. The strongest precedents (BMAD, OpenMontage, jkp-data) all keep behaviors inline in a single markdown file. Shield is taking one step beyond that: a **flat catalog at `shield/agents/behaviors/` with on-demand loading from each agent.md**. This is novel for LLM-agent design but is a direct generalization of two established patterns — BMAD's "single shared rubric file referenced by an agent" and Shield's existing skill→helper convention (`SKILL.md` references `repo-scan.md` etc.). The deviation from community precedent is justified by Shield's scale (10 reviewer agents, not 1) and by the user-confirmed success criteria (file-size-bounded, easy to extend, eval-targetable) which all favor catalog-with-on-demand over inline.

## Product Lens

### Product Manager Review (Grade: A-)

#### User Impact Analysis

**Who benefits:**
- **Shield agent authors** (primary) — the people maintaining `product-manager-reviewer.md` and `architecture-reviewer.md`. They gain a bounded, eval-targetable structure instead of a flat enumeration that hides depth gaps.
- **PRD authors and reviewees** (secondary) — get reviews that deliberate on each behavior rather than producing shallow grades across 9 of 13 dimensions.
- **Shield's orchestrator and eval suite** (tertiary) — gain structured `behaviors[]` data addressable by name, enabling per-behavior regression tracking.

**How much:** The empirical anchor (FLASK ~4 Spearman-point improvement, Gawande ~47% complication reduction, surgical mortality ↓40%) is quantified. The Shield-specific quantification is implicit ("visibly shallow output on 9 of 13 dimensions"), not measured — there's no current eval baseline cited, which is a gap.

**Risk of not doing it:** Document is explicit — the status quo (PM1-PM11 flat enumeration) is the exact anti-pattern that VoltAgent (20.2k★) ships and that produces the shallow output Shield is trying to escape. Cost of inaction is continued reviewer-agent degradation as Shield scales to more agents.

#### Scope Recommendation

The scope is well-disciplined — this is a tightly-bounded refactor, not a re-platform. Three things stand out as right-sized:

1. **2 PRs, one per agent.** Single-file reverts. Hard to over-scope.
2. **Reject one-file-per-behavior and reject shared cross-agent registry.** Both rejected with cited reasoning (no LLM-agent precedent for the former; premature abstraction for the latter). This is real scope discipline — the document closes doors deliberately.
3. **Behaviors are PRD-Review-mode only initially.** The other 3 modes (Research Framing, Research Review, Plan Review, Standalone) keep PM1-PM11. This is the right MVP cut — minimizes blast radius and creates a learn-before-expand loop.

**What could still be cut for v0:** The per-behavior `findings.md` artifact (mentioned under "Markdown-vs-JSON tension"). The JSON envelope alone is enough for the orchestrator; the human-readable markdown artifact can wait until a second iteration if reviewers ask for it.

#### Prioritization Framework

**Sequencing is justified and load-bearing:** PR 1 (PM agent) first because PM has the larger surface area (9 of 13 dims), so any structural issues with the new shape surface faster. PR 2 (tech-lead) reuses validated patterns. This is correct ordering.

**Effort vs. impact:** Document notes the largest depth gain is in tech-lead (2 dims → ~10 behaviors). That's an implicit signal that PR 2 may actually carry more user-visible win than PR 1, even though PR 1 is sequenced first for learning. Worth surfacing in the migration doc so reviewers know what to look for in eval deltas.

**Dependencies mapped:** Yes — `personas.md` dispatch prompt, `scoring.md` envelope consumer, eval-suite mapper script. All called out. Migration doc explicitly addresses orchestrator backward compatibility (accept both old and new envelope shapes during transition).

#### Stakeholder Summary

> Shield's PRD reviewer currently produces shallow grades across 9 of 13 dimensions because each dimension is just a row in a flat checklist. Four independent traditions — surgical safety checklists, behavior-driven development, LLM evaluation research, and Anthropic's own agent-engineering guidance — all prescribe the same fix: break the work into named, bounded behaviors with explicit triggers and per-check severities. We will refactor two reviewer agents (PM and tech-lead) in two single-file PRs. Each PR is independently revertible. The orchestrator stays backward-compatible during the transition. The closest open-source precedent (BMAD-METHOD, 47.7k stars) ships this exact pattern. The change is low-risk infrastructure work that materially improves the depth of every PRD review Shield runs.

#### Scorecard

| # | Evaluation Point | Grade | Notes |
|---|-----------------|-------|-------|
| PM1 | User impact clarity | B+ | Primary/secondary users clear; impact empirically warranted by FLASK/Gawande numbers, but Shield-specific baseline not quantified. *Addressed in revision: distinct-finding-count baseline now defined in Migration Path.* |
| PM2 | Problem-solution fit | A | "Bad checklist" diagnosis maps cleanly to Gawande's; solution is the same tradition's prescription. Tight loop. |
| PM3 | Scope discipline | A | MVP cut explicit (PRD-Review mode only, 2 PRs, behaviors-mode-only initially). Two doors explicitly closed. |
| PM4 | Prioritization rationale | B+ | PR sequencing justified. Could be sharper on PM-first-vs-tech-lead-first tradeoff. |
| PM5 | Stakeholder communicability | A- | "Bad checklist" → "good checklist" is non-technical. Convergence-of-four-traditions framing is accessible. |
| PM6 | Market/competitive awareness | A | BMAD, VoltAgent, OpenMontage, jkp-data, Inspect AI surveyed. Anti-pattern explicitly named. Strongest section. |
| PM7 | Adoption & rollout risk | A- | 5 named risks with mitigations: cache invalidation, token budget, eval drift, other-mode preservation, markdown/JSON tension. |
| PM8 | Success metrics | **A-** *(revised from C)* | *Addressed in revision: distinct-finding-count metric + merge gate now defined.* |
| PM9 | Reversibility & exit cost | A | Single-file revert per PR; orchestrator backward-compatible during window. |
| PM10 | Business value alignment | A- | Empirical baseline (FLASK, Gawande) carries ROI argument. Not engineering-driven scope creep. |
| PM11 | Framing coverage honored | A | All required PF7 voices present in body with direct quotes (Gawande, North, Keogh, Schluntz/Zhang). PF8 categories covered: vendor docs, peer-reviewed empirical, definitional, practitioner experience. Minor gap: no conference-talk direct quote in body (Gawande TED in Further Exploration only). |

**Key Finding:** Strong synthesis — framing brief's PF7/PF8 honored in the body (not just References), document closes doors deliberately. After revision, the PM8 gap (no measurable success threshold) is addressed via the distinct-finding-count merge gate.

#### Recommendations

| Priority | Point | Recommendation | Status |
|----------|-------|---------------|---|
| ~~P0~~ | PM8 | Define a concrete pre/post eval metric before merging PR 1. | **Addressed** — distinct-finding-count baseline + merge gate added to Migration Path |
| P1 | PM1 | Capture and cite Shield's *current* eval baseline (or qualitative output samples) in the migration doc. | Open — to be done as first step of PR 1 |
| P1 | PM4 | Add a sentence to the migration doc naming the PM-first-vs-tech-lead-first tradeoff (PM-first for learning; tech-lead may carry larger user-visible depth gain). | Open — to be added to PR 1 description |
| P2 | PM11 | Minor PF8 gap: no direct quote from a conference talk in body. Pull a Gawande TED quote into body OR document the carve-out. | Open — defer |
| P2 | PM3 | Explicitly defer the per-behavior `findings.md` artifact to v2; JSON envelope alone is sufficient for orchestrator. | Open — captured in v0 scope |

## References

- [Building effective agents — Schluntz & Zhang, Anthropic, Dec 2024](https://www.anthropic.com/engineering/building-effective-agents)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Define tools — Claude API Docs](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use)
- [G-Eval (Liu et al., EMNLP 2023)](https://arxiv.org/abs/2303.16634)
- [Judging LLM-as-a-Judge with MT-Bench (Zheng et al., NeurIPS 2023)](https://arxiv.org/html/2306.05685v4)
- [FLASK (Ye et al., ICLR 2024)](https://arxiv.org/abs/2307.10928)
- [Atul Gawande, *The Checklist Manifesto*, Metropolitan Books, 2009](https://en.wikipedia.org/wiki/The_Checklist_Manifesto)
- [Haynes AB et al., "A Surgical Safety Checklist to Reduce Morbidity and Mortality in a Global Population", *NEJM* 360:491-499, 2009](https://www.nejm.org/doi/full/10.1056/NEJMsa0810119)
- [Dan North, "Introducing BDD", *Better Software*, March 2006](https://dannorth.net/introducing-bdd/)
- [Liz Keogh, "Conversational Patterns in BDD", 22 Sept 2011](https://lizkeogh.com/2011/09/22/conversational-patterns-in-bdd/)
- [BMAD-METHOD: `prd-validation-checklist.md`](https://github.com/bmad-code-org/BMAD-METHOD)
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [jxnl, "Slash Commands vs Subagents", Aug 2025](https://jxnl.co/writing/2025/08/06/context-engineering-slash-commands-subagents/)

## Further Exploration

*Curated recommendations not cited in body above. Useful for going deeper.*

### Books
- James Reason, *Human Error* (Cambridge, 1990) — the Swiss-cheese model Gawande builds on; useful if framing behaviors as defense-in-depth layers.
- Daniel Kahneman, *Thinking, Fast and Slow* (2011), ch. 21 — "formulas vs. intuition" gives a second empirical leg for structured checks beating expert gestalt.

### Long-form blogs / articles
- Anthropic, [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — companion to "Building effective agents"; deeper on tool-description craft, directly applicable to behavior `description` fields.
- Hamel Husain, ["Your AI product needs evals"](https://hamel.dev/blog/posts/evals/) — argues the eval suite *is* the spec; parallel to North's behavior-as-unit.
- Liz Keogh, "Behavior-Driven Development – Shallow and Deep" (July 2013) — directly relevant title; on the gap between performative BDD and the version that actually works.
- Dan North, ["Let your examples flow"](https://dannorth.net/2008/06/30/let-your-examples-flow/) (2008) — follow-up on scenario authoring.
- Schluntz & Zhang, "How we built our multi-agent research system", Anthropic Engineering, June 2025 — production lessons on orchestrator-worker boundaries.
- Eugene Yan, "Patterns for building LLM-based systems & products" — clean taxonomy of evaluator patterns.

### Videos / talks
- Atul Gawande, ["How do we heal medicine?"](https://www.ted.com/talks/atul_gawande_how_do_we_heal_medicine), TED 2012 — 18-min summary, useful for stakeholder framing.
- Dan North, "BDD: Better Done Differently" — multiple InfoQ recordings.

### Papers
- Pronovost P et al., "An intervention to decrease catheter-related bloodstream infections in the ICU", *NEJM* 355:2725-2732, 2006 — the Keystone ICU study Gawande draws on; second empirical leg.
- Chiang et al., ["A Closer Look into Automatic Evaluation Using LLMs"](https://arxiv.org/html/2310.05657) — compares evaluation-prompt designs; potential direct monolithic-vs-decomposed evidence.

### GitHub repos to study during implementation
- [BMAD-METHOD `prd-validation-checklist.md`](https://github.com/bmad-code-org/BMAD-METHOD) — closest structural precedent to Shield's planned shape.
- [OpenMontage `reviewer.md`](https://github.com/calesthio/OpenMontage) — manifest-driven `review_focus` + severity-carries-required-fields pattern.
- [FLASK GitHub repo](https://github.com/kaistAI/FLASK) — contains the actual per-skill rubric YAML files; structural template.
- [Inspect AI scorer modules](https://github.com/UKGovernmentBEIS/inspect_ai) — one-file-per-scorer at code level (not LLM, but useful adjacent).

### Open issues to watch
- [anthropics/claude-code #52502](https://github.com/anthropics/claude-code/issues/52502) — parent+child token accounting; relevant if Shield ever splits behaviors into separate subagent calls.
