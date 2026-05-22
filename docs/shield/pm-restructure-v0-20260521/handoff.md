# PM Restructure v0 — Design Handoff

**Status:** Ready for implementation via `/shield implement` inside devcontainer
**Branch:** `refactor/rename-reviewer-agents-to-roles`
**Plan:** `docs/shield/pm-restructure-v0-20260521/plan.json`
**Baseline:** `shield/evals/baselines/prd-review-pm.json` (committed in this branch)

## Problem

Today's PM persona agent (`shield/agents/product-manager.md`) is a single multi-mode file (4 modes: Research-Framing, Research-Review, Plan-Review, Standalone). One LLM dispatch handles all 9 of PM's owned PRD rubric dimensions in one prompt. Research (FLASK ICLR 2024, Schluntz/Zhang Anthropic) shows depth degrades when one LLM dispatch handles many considerations at once. CLAUDE.md mandates RED-GREEN-REFACTOR for skill/agent changes.

## Architectural decisions

These were reached after extensive design discussion. Reading them lets `/shield implement` proceed without re-litigating.

### Decision 1 — Two primitives, clean responsibilities

| Primitive | Owns | Doesn't own |
|---|---|---|
| **Skill** | Workflow steps, dispatch decisions, aggregation, persona-grouping metadata, user-facing output | Execution criteria, focused-task logic |
| **Subagent** | Focused execution (graders, authoring units), the criteria it applies, its output shape | Workflow awareness, mode-switching, dispatch logic |

Applied test:
- "Does this content describe HOW to grade something?" → subagent
- "Does this content describe WHEN to dispatch what?" → skill
- "Does this content describe MULTIPLE modes the same actor does?" → split into N focused subagents

### Decision 2 — Personas live in skills, not in agents

Personas are workflow-level groupings used for aggregation in user-facing output. They are **tags + aggregation rules** in skills, NOT agent files. `shield/agents/` contains focused subagents (named for WHAT THEY DO, not WHO THEY EMULATE).

### Decision 3 — Two dispatch patterns

| Pattern | Used for | Example |
|---|---|---|
| **A. Global named subagents** (`shield/agents/<name>.md`) | Cross-skill reuse + cohesive authoring work | `research-framer`, `research-reviewer-narrative`, PM1-PM11 (used by both /plan-review and /research Research-Review) |
| **B. Skill-internal prompts** (`shield/skills/<skill>/prompts/<name>.md`) | Single-skill graded dim work | The 9 PRD-Review PM dim prompts (only `/prd-review` uses them) |

Pattern B is what `/research` already does (general-purpose Agent with stream-specific prompts loaded from skill helpers). Pattern A is what `/prd-review` currently does. v0 uses both.

### Decision 4 — Granularity is "one subagent per coherent concept"

Not atomic-per-check (too granular), not per-multi-mode-persona (too coarse). One subagent per rubric dim (for graded work) OR per cohesive output (for authoring work).

### Decision 5 — TDD discipline mandatory (per CLAUDE.md)

For each new prompt/subagent:
- **RED:** Per-dim baseline finding count from `shield/evals/baselines/prd-review-pm.json` (already captured)
- **GREEN:** Dispatch the new prompt against the relevant fixture; verify finding count meets or exceeds baseline
- **REFACTOR:** Tighten prompt if any baseline gap not caught
- **COMMIT:** Per-cycle commit

### Decision 6 — Merge gate

Total PM finding count across the 4 PRD-Review test fixtures must equal or exceed **62** (baseline). No fixture may regress more than 10%. Stretch goal: 81 (1.3×).

## File map (what gets created in v0)

```
NEW global subagents (Pattern A, cross-skill / authoring):
  shield/agents/research-framer.md
  shield/agents/research-reviewer-narrative.md
  shield/agents/user-impact-clarity.md           ← PM1
  shield/agents/problem-solution-fit.md          ← PM2
  shield/agents/scope-discipline-of-plan.md      ← PM3 (distinct from PRD dim 2)
  shield/agents/prioritization-rationale.md      ← PM4
  shield/agents/stakeholder-communicability.md   ← PM5
  shield/agents/market-competitive-awareness.md  ← PM6
  shield/agents/adoption-rollout-risk.md         ← PM7
  shield/agents/success-metrics-defined.md       ← PM8
  shield/agents/reversibility-exit-cost.md       ← PM9
  shield/agents/business-value-alignment.md      ← PM10
  shield/agents/framing-coverage-honored.md      ← PM11 (Research-Review only)

NEW skill-internal prompts (Pattern B, PRD-Review-specific):
  shield/skills/general/prd-review/prompts/problem-clarity.md            ← PRD dim 1
  shield/skills/general/prd-review/prompts/scope-discipline.md           ← PRD dim 2
  shield/skills/general/prd-review/prompts/measurable-success.md         ← PRD dim 3
  shield/skills/general/prd-review/prompts/raci-and-approvals.md         ← PRD dim 7
  shield/skills/general/prd-review/prompts/legal-privacy-compliance.md   ← PRD dim 8
  shield/skills/general/prd-review/prompts/gtm-customer-comms.md         ← PRD dim 9
  shield/skills/general/prd-review/prompts/support-cx-impact.md          ← PRD dim 10
  shield/skills/general/prd-review/prompts/why-now-cost-of-inaction.md   ← PRD dim 11
  shield/skills/general/prd-review/prompts/risks-and-assumptions.md      ← PRD dim 12

MODIFIED skill files:
  shield/skills/general/prd-review/dimensions.md   (REPLACES personas.md; dispatch registry)
  shield/skills/general/prd-review/SKILL.md        (mixed dispatch: 9 prompts + 4 legacy personas)
  shield/skills/general/prd-review/scoring.md      (accepts both per-persona and per-dim envelopes)
  shield/skills/general/plan-review/dimensions.md  (NEW; PM1-PM10 + legacy architect/agile-coach)
  shield/skills/general/plan-review/SKILL.md       (mixed dispatch)
  shield/skills/general/plan-review/personas.md    (update PM references; keep legacy)
  shield/skills/general/research/SKILL.md          (Phase 2 framing + review use new subagents)

DELETED:
  shield/agents/product-manager.md                              (work redistributed)
  shield/skills/general/prd-review/personas.md                  (replaced by dimensions.md)
```

## How to use `/shield implement` here

Inside the devcontainer (after reopening):

```bash
# Set up Claude Code authentication (one-time per devcontainer)
claude /login

# Verify plan.json is visible
ls docs/shield/pm-restructure-v0-20260521/plan.json

# Start implementation
claude /shield implement EPIC-1-S1
```

`/shield implement` will:
1. Read `plan.json` for EPIC-1-S1's tasks and acceptance criteria
2. Walk RED-GREEN-REFACTOR per acceptance criterion
3. Commit per AC
4. Move to next story when current story's ACs are all green
5. Run merge gate (EPIC-1-S11) after EPIC-1 stories complete

## Things `/shield implement` should know

- **Per-dim baselines from `prd-review-pm.json`** are the RED measurements. Compare GREEN results against them for each fixture.
- **Existing rubric criteria** live in `shield/skills/general/prd-review/rubric.md`. The new prompts should ATTACH the criteria to the focused work (not just reference rubric.md as a helper).
- **Output JSON shape** for graded subagents must match the dim-block schema (see existing personas.md returned-JSON spec).
- **Lean/standard PRD distinctions** matter for dims 9, 10 (lean = "informational", standard = graded).
- **N/A exceptions** for internal-tool fixture: dim 2 + dim 8-10. The prompts must honor these.
- **Persona tags** in the new global subagent frontmatter: `persona: product-manager`. Used by skill aggregation for summary.md rollup.
- **Dispatch pattern for skill-internal prompts:** the skill orchestrator reads the prompt file at dispatch time and passes it to a `general-purpose` Agent (NOT a named subagent dispatch). This is what `/research` does today.

## Open questions deferred to v1

- Decomposing architect, agile-coach, dx-engineer, finops-analyst personas (they stay as today's persona agents for v0; they're handled via legacy dispatch in updated dimensions.md)
- Decomposing dim 5 (NFR) and dim 6 (rollout) sub-checks (architect's work, deferred)
- Code-review skill decomposition (backend/k8s/security/sre/cloud-architect)
- WAR pillar decomposition (cloud-architect's 6 pillars)
- Plan-Review fixtures (no fixtures exist; v0 uses qualitative manual verification only)

## Reference

- Baseline: `shield/evals/baselines/prd-review-pm.json`
- Test fixtures: `shield/skills/general/prd-review/test-fixtures/`
- Existing PM agent (pre-v0): `shield/agents/product-manager.md` — work distributes from here into new subagents
- Existing rubric: `shield/skills/general/prd-review/rubric.md` — criteria source
