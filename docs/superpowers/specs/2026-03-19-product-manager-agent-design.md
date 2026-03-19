# Product Manager Agent — Design Spec

**Status:** Proposed
**Date:** 2026-03-19
**Context:** Shield's research skill produces technically thorough output but lacks a product lens — no consideration of user impact, prioritization, scope discipline, or stakeholder communicability. A standalone PM agent fills this gap across research, plan review, and ad-hoc workflows.

## Decision

Add a **Technical Product Manager agent** to Shield with a thin orchestration skill, following the same patterns as the existing 7 reviewer agents. The agent operates in 4 modes and is available to any Shield workflow.

## Architecture

### Two New Files

| File | Role |
|------|------|
| `shield/agents/product-manager.md` | Agent definition — persona, 4 modes, evaluation checklists, output format |
| `shield/skills/general/pm-analysis/SKILL.md` | Thin orchestrator — dispatches the agent with the right mode and context |

### Two Skill Updates

| File | Change |
|------|--------|
| `shield/skills/general/research/SKILL.md` | Add PM framing (before research) and PM review (after synthesis) |
| `shield/skills/general/plan-review/SKILL.md` | Add PM agent to reviewer dispatch list |

## Agent Definition

### Persona

**Technical Product Manager** who bridges engineering and product. Has shipped products at scale, run roadmap prioritization exercises, shaped MVPs from ambiguous requirements, and communicated technical trade-offs to non-technical stakeholders. Thinks in terms of user value, business outcomes, and scope discipline — not just technical elegance.

### Weight

0.7 (Supporting persona — same as agile-coach-reviewer and cost-reviewer)

### Trigger Keywords

user impact, business value, prioritization, MVP, scope, stakeholder, roadmap, market, competitive, adoption, ROI

### Modes

The agent operates in one of four modes. The dispatching skill specifies the mode.

| Mode | When Dispatched | Focus |
|------|----------------|-------|
| Research Framing | Before research agents run | Frame the right questions — stakeholders, decisions needed, success criteria, what matters most |
| Research Review | After research synthesis | Product lens on findings — user impact, prioritization, scope, stakeholder summary |
| Plan Review | During plan-review skill | Evaluates whether the plan delivers the right thing — user value, scope discipline, stakeholder clarity |
| Standalone | Direct dispatch from any workflow | Full PM analysis on any input — research, RFC, proposal, etc. |

## Evaluation Checklists

### Research Framing Checklist (PF1-PF6)

Used in research-framing mode only. Focus is on asking the right questions, not evaluating answers.

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| PF1 | Stakeholder identification | Who cares about this decision and why | Critical |
| PF2 | Decision clarity | What specific decision(s) need to be made | Critical |
| PF3 | Success criteria | What would a good outcome look like, measurably | Important |
| PF4 | Question prioritization | Which questions matter most — ranked, not a flat list | Important |
| PF5 | Scope boundaries | What's explicitly out of scope for this research | Important |
| PF6 | Timeline & urgency | When is the decision needed, what constraints does that impose on depth vs. speed | Important |

### PM Evaluation Points (PM1-PM10)

Used in research-review, plan-review, and standalone modes.

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| PM1 | User impact clarity | Who benefits, how specifically, quantified where possible | Critical |
| PM2 | Problem-solution fit | Does the proposed approach actually solve the stated problem, or is it a solution looking for a problem | Critical |
| PM3 | Scope discipline | Is this an MVP or a kitchen sink? What can be cut without losing core value | Important |
| PM4 | Prioritization rationale | Effort vs. impact considered, dependencies mapped, sequencing justified | Important |
| PM5 | Stakeholder communicability | Can a non-technical stakeholder understand what's being built and why | Important |
| PM6 | Market/competitive awareness | How does this position relative to alternatives (buy vs build, existing tools) | Warning |
| PM7 | Adoption & rollout risk | What could block adoption — migration pain, learning curve, organizational resistance | Important |
| PM8 | Success metrics | How will we know this worked? Measurable outcomes defined | Important |
| PM9 | Reversibility & exit cost | What happens if this is the wrong bet — how hard is it to change course | Warning |
| PM10 | Business value alignment | Does this serve actual business goals or is it engineering-driven scope creep | Critical |

## Output Format

### Research Framing Mode

Structured output that directly shapes the research agent prompts:

```markdown
## PM Research Framing

### Stakeholders
[Who cares about this decision and their perspective]

### Decision(s) to Make
[Specific, crisp decision statements]

### Success Criteria
[Measurable outcomes that define a good result]

### Prioritized Research Questions
1. [Most important question — why it matters]
2. [Second question — why it matters]
3. ...

### Scope Boundaries
- In scope: [...]
- Out of scope: [...]

### Timeline & Constraints
[When the decision is needed, what that means for research depth]
```

### Research Review, Plan Review, and Standalone Modes

Hybrid format — narrative sections followed by a summary scorecard.

```markdown
## Product Manager Review

### User Impact Analysis
[Who benefits, how much, what's the risk of not doing it]

### Scope Recommendation
[What's essential vs. nice-to-have, MVP definition, what to cut]

### Prioritization Framework
[Effort vs. impact, dependencies, what to build first and why]

### Stakeholder Summary
[Non-technical framing of the decision and recommendation — suitable for sharing with leadership or cross-functional partners]

### Scorecard

| # | Evaluation Point | Grade | Notes |
|---|-----------------|-------|-------|
| PM1 | User impact clarity | _ | ... |
| PM2 | Problem-solution fit | _ | ... |
| PM3 | Scope discipline | _ | ... |
| PM4 | Prioritization rationale | _ | ... |
| PM5 | Stakeholder communicability | _ | ... |
| PM6 | Market/competitive awareness | _ | ... |
| PM7 | Adoption & rollout risk | _ | ... |
| PM8 | Success metrics | _ | ... |
| PM9 | Reversibility & exit cost | _ | ... |
| PM10 | Business value alignment | _ | ... |

**Key Finding:** [One sentence summary of the most important observation]

#### Recommendations

| Priority | Point | Recommendation |
|----------|-------|---------------|
| P0/P1/P2 | PM# | What to fix and why |
```

## Skill Definition

### `shield/skills/general/pm-analysis/SKILL.md`

Thin orchestrator that:

1. Determines mode from context (research-framing, research-review, plan-review, or standalone)
2. Gathers input material (raw topic, research doc, plan doc, or caller-provided input)
3. Dispatches the PM agent with the mode and input
4. Returns the output

**When to use:** Any workflow that needs a product lens.

**When NOT to use:** Pure infrastructure/code reviews with no product decisions. Quick factual lookups.

## Research Skill Integration

Updated research workflow (changes in **bold**):

1. Clarify topic (existing — skip if user provided context)
2. **PM framing — dispatch PM agent in research-framing mode**
3. Research with 3 parallel agents — **prompts shaped by PM framing output (prioritized questions, scope boundaries, stakeholder context)**
4. Synthesize findings (existing)
5. **PM review — dispatch PM agent in research-review mode**
6. Write final document — **includes PM review output as a section**

## Plan Review Integration

The PM agent is added to the reviewer dispatch list alongside the existing agents. Dispatched in plan-review mode. Output goes alongside other reviewer outputs (e.g., `detailed/product-manager.md` in the review directory).

## What This Does NOT Cover

- Output directory configuration — deferred to `feat/config-driven-output-dir` branch
- Changes to the implement-feature or review skills — PM agent is available but not wired in; can be added later
- PM agent as a required reviewer — it's supporting (weight 0.7), not blocking
