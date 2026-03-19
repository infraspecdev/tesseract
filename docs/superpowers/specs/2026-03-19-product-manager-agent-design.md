# Product Manager Agent — Design Spec

**Status:** Proposed
**Date:** 2026-03-19
**Context:** Shield's research skill produces technically thorough output but lacks a product lens — no consideration of user impact, prioritization, scope discipline, or stakeholder communicability. A standalone PM agent fills this gap across research, plan review, and ad-hoc workflows.

## Decision

Add a **Technical Product Manager agent** to Shield with a thin orchestration skill, following the same patterns as the existing 7 reviewer agents. The agent operates in 4 modes and is available to any Shield workflow.

> **Note on Research Framing mode:** Unlike the other 7 agents which are purely evaluative (grading existing work), the PM agent's research-framing mode is **prescriptive** — it produces output that shapes future work. This is an intentional departure from the reviewer pattern. The other 3 modes (research-review, plan-review, standalone) are evaluative as usual.

## Architecture

### Two New Files

| File | Role |
|------|------|
| `shield/agents/product-manager-reviewer.md` | Agent definition — persona, 4 modes, evaluation checklists, output format |
| `shield/skills/general/pm-analysis/SKILL.md` | Thin orchestrator — dispatches the agent with the right mode and context |

### Two Skill Updates

| File | Change |
|------|--------|
| `shield/skills/general/research/SKILL.md` | Add PM framing (before research) and PM review (after synthesis) |
| `shield/skills/general/plan-review/SKILL.md` | Add PM agent to reviewer dispatch list |

### Two Plan-Review Supporting File Updates

| File | Change |
|------|--------|
| `shield/skills/general/plan-review/personas.md` | Add PM agent to persona catalog with weight 0.7, trigger keywords, and selection rules |
| `shield/skills/general/plan-review/scoring.md` | Add PM persona to weighted scoring table |

## Agent Definition

### Frontmatter

```yaml
---
name: product-manager-reviewer
description: |
  Multi-mode product manager. Dispatched for research framing (6 checks),
  research review / plan review / standalone (10 checks). Evaluates user impact,
  scope discipline, prioritization, and stakeholder communicability.
model: inherit
---
```

### Persona

You are a **Technical Product Manager** who bridges engineering and product. You've shipped products at scale, run roadmap prioritization exercises, shaped MVPs from ambiguous requirements, and communicated technical trade-offs to non-technical stakeholders. You think in terms of user value, business outcomes, and scope discipline — not just technical elegance. You've seen teams build the wrong thing because nobody asked "who needs this and why?" before diving into architecture.

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

Used in research-framing mode only. Focus is on asking the right questions, not evaluating answers. This mode does **not** produce a graded scorecard — it produces a structured brief that shapes the research agents' prompts.

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

## Review Process

### Research Framing Mode

1. Read the research topic/question provided by the user
2. Identify all stakeholders who will be affected by or care about the decision
3. Distill the topic into specific, answerable decision statements
4. Define measurable success criteria for the research
5. Prioritize research questions by impact — rank, don't just list
6. Draw explicit scope boundaries (in scope vs. out of scope)
7. Assess timeline constraints and calibrate recommended research depth
8. Produce the framing output in the format below

### Research Review, Plan Review, and Standalone Modes

1. Read the full input document (research findings, plan, RFC, or proposal)
2. Identify the target users/stakeholders and how the proposal affects them
3. Evaluate problem-solution fit — does the proposed approach actually address the stated problem?
4. Assess scope — is it disciplined or overloaded?
5. Analyze prioritization and sequencing rationale
6. Frame findings for non-technical stakeholders
7. Check for market/competitive context and adoption risks
8. Evaluate success metrics and reversibility
9. Grade each evaluation point PM1-PM10 using A-F scale
10. Write recommendations for anything graded C or below
11. Produce the output in the format below

## Output Format

### Research Framing Mode

Structured output that directly shapes the research agent prompts. No scorecard — this mode produces a brief, not a graded evaluation.

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
### Product Manager Review (Grade: X)

#### User Impact Analysis
[Who benefits, how much, what's the risk of not doing it]

#### Scope Recommendation
[What's essential vs. nice-to-have, MVP definition, what to cut]

#### Prioritization Framework
[Effort vs. impact, dependencies, what to build first and why]

#### Stakeholder Summary
[Non-technical framing of the decision and recommendation — suitable for sharing with leadership or cross-functional partners]

#### Scorecard

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

### Frontmatter

```yaml
---
name: pm-analysis
description: |
  Dispatch the product manager agent for product-lens analysis. Use when any workflow
  needs user impact, prioritization, scope, or stakeholder framing. Triggers on
  product analysis, PM review, user impact, business value.
---
```

### `shield/skills/general/pm-analysis/SKILL.md`

Thin orchestrator that:

1. Determines mode from context
2. Gathers input material (raw topic, research doc, plan doc, or caller-provided input)
3. Dispatches the PM agent (`shield:product-manager-reviewer`) with the mode and input
4. Returns the output

**Mode selection logic:**

| Context | Mode |
|---------|------|
| Called from research skill before research agents run | `research-framing` |
| Called from research skill after synthesis | `research-review` |
| Called from plan-review skill | `plan-review` |
| Called directly or from any other workflow | `standalone` (default) |

The calling skill passes the mode explicitly. Standalone is the default when no mode is specified.

**When to use:** Any workflow that needs a product lens.

**When NOT to use:** Pure infrastructure/code reviews with no product decisions. Quick factual lookups.

## Research Skill Integration

Updated research workflow (changes in **bold**):

1. Clarify topic (existing — skip if user provided context)
2. **PM framing — dispatch PM agent in research-framing mode with the raw topic as input**
3. Research with 3 parallel agents — **each agent's prompt is prefixed with the PM framing output (stakeholders, prioritized questions, scope boundaries) so they research what matters most**
4. Synthesize findings (existing)
5. **PM review — dispatch PM agent in research-review mode with the synthesized findings as input**
6. Write final document — **PM review output is included as a `## Product Lens` section after `## Summary` and before `## References`**

### Concrete Research Agent Prompt Change

Current agent prompt pattern:
```
Research [topic] from [source type]. Return direct quotes with attribution, source URLs, key data points.
```

Updated pattern:
```
Research [topic] from [source type].

Context from product analysis:
- Stakeholders: [from PM framing]
- Key questions to answer: [from PM framing, prioritized]
- Scope: [from PM framing]
- Timeline: [from PM framing]

Return direct quotes with attribution, source URLs, key data points. Prioritize findings that address the key questions above.
```

## Plan Review Integration

### `personas.md` Update

Add to the persona catalog table:

```
| `shield:product-manager-reviewer` | 0.7 | User impact, scope discipline, prioritization, business value |
```

Add to selection rules:
- **Include** product-manager-reviewer when plan contains user-facing features, product decisions, or scope trade-offs (matched via trigger keywords)

### `scoring.md` Update

Add to the Persona Weights table:

```
| Product Manager | 0.7 | Supporting |
```

The composite formula is unchanged — only activated personas contribute to the weighted average.

### Output Location

PM agent output goes to `detailed/product-manager-reviewer.md` in the review directory, alongside the other agent outputs. The `(Grade: X)` header format ensures the scoring pipeline can parse the PM grade for composite calculation.

## What This Does NOT Cover

- Output directory configuration — deferred to `feat/config-driven-output-dir` branch
- Changes to the implement-feature or review skills — PM agent is available but not wired in; can be added later
- PM agent as a required reviewer — it's supporting (weight 0.7), not blocking
