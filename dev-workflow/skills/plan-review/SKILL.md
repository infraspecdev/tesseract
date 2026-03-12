---
name: plan-review
description: Multi-persona plan review — dispatches parallel reviewer agents to evaluate plan documents, producing scored analysis and enhanced plan. Triggers on mentions of plan review, document review, review my plan, or after plan-docs generation.
---

# Plan Review

Dispatch parallel expert reviewer agents against a plan document to produce a scored analysis with prioritized recommendations and an enhanced plan.

## When to Use

- User asks to review a plan document
- After plan-docs skill generates a plan
- User mentions "plan review", "review my plan", "review this document"
- User invokes `/plan-review`

## Input

Accept the plan document path as an argument, or auto-detect:

1. **Explicit path** — user provides a file path or the `/plan-review` command passes one
2. **Auto-detect** — look for the most recently generated plan in the working directory:
   - Check for files matching `*plan*.html`, `*plan*.md` in the current directory and subdirectories
   - Prefer files modified in the last hour
   - If multiple candidates, ask the user which to review

Read the full plan document content before proceeding.

## Persona Catalog

Five reviewer agents are available, each with a specialized checklist:

| Agent | File | Weight | Focus |
|-------|------|--------|-------|
| Cloud Architect | `agents/cloud-architect-reviewer.md` | 1.0 | Infrastructure topology, scalability, HA, operational readiness |
| Security Engineer | `agents/security-engineer-reviewer.md` | 1.0 | Security posture, threat modeling, testability, validation |
| DX Engineer | `agents/dx-engineer-reviewer.md` | 1.0 | Plan clarity, actionability, software architecture |
| Cost/FinOps | `agents/cost-finops-reviewer.md` | 0.7 | Cost awareness, right-sizing, environment tiering |
| Agile Coach | `agents/agile-coach-reviewer.md` | 0.7 | Sprint-readiness, story quality, dependency ordering |

## Dynamic Persona Selection

Select which reviewers to dispatch based on plan content:

### Step 1: Extract themes

Read the plan document and identify keywords and themes present in the content.

### Step 2: Match against triggers

Each agent file contains a "Trigger Keywords" section. Count how many trigger keywords appear in the plan content for each agent.

### Step 3: Select agents

- **Always include** DX Engineer and Agile Coach when the plan contains stories (these two are non-negotiable for plans with actionable work items)
- **Include** any agent with 2+ trigger keyword matches
- **Minimum 3** agents must be selected — if fewer than 3 match on triggers, add the next-closest agents by trigger count
- **All 5 may run** if the plan touches infrastructure, security, cost, stories, and architecture

### Step 4: Announce selection

Tell the user which reviewers were selected and why:

> **Dispatching 4 reviewers:** Cloud Architect (infrastructure + monitoring keywords), Security Engineer (auth + encryption keywords), DX Engineer (stories detected), Agile Coach (stories detected). Skipping Cost/FinOps (no cost-related content detected).

## Dispatch

For each selected agent, launch a parallel agent using the Agent tool:

1. Read the agent's markdown file from the `agents/` directory to get its full persona, checklist, and output format
2. Dispatch each agent in parallel with this prompt structure:

```
You are reviewing a plan document as a specialized reviewer.

<persona>
{full content of the agent's markdown file}
</persona>

<plan>
{full content of the plan document}
</plan>

<scoring-rubric>
{full content of scoring.md}
</scoring-rubric>

Review the plan according to your persona's evaluation points. Grade each point A-F using the scoring rubric. Produce your output in the exact format specified in your persona's Output Format section.

Important:
- Grade based on what the plan SAYS, not what you assume
- Missing information defaults to F, not "N/A"
- Be specific in notes — quote the plan or cite what's missing
- Recommendations must be actionable — not "improve this" but "add X to section Y"
```

3. Use `subagent_type` matching the agent name (e.g., `dev-workflow:cloud-architect-reviewer`) when available, otherwise use `general-purpose`

## Collection & Scoring

After all agents return their reviews:

### Step 1: Parse grades

Extract the grade for each evaluation point from each agent's output table.

### Step 2: Calculate per-persona grade

For each persona, average the numeric grades of all evaluation points using the mapping from `scoring.md`:
- A=4, B=3, C=2, D=1, F=0
- Round to nearest letter grade using the ranges in scoring.md

### Step 3: Calculate composite readiness score

Weighted average using persona weights:

```
composite = sum(persona_numeric_grade * weight) / sum(activated_weights)
```

Convert to letter grade and verdict using scoring.md thresholds.

### Step 4: Classify recommendations

Collect all recommendations from all personas and classify by priority:
- **P0 (High):** Grade D or F on a Critical severity evaluation point
- **P1 (Medium):** Grade C-D on an Important severity point
- **P2 (Low):** Grade C on a Warning severity point, or minor gaps on B-graded points

## Output Generation

### Step 1: Create output folder

```
review/<YYYY-MM-DD>-<topic-slug>/
```

Where `<topic-slug>` is a kebab-case summary of the plan topic (e.g., `observability-stack`, `auth-migration`).

### Step 2: Write analysis.md

```markdown
# Plan Review: <Plan Title>

**Date:** <YYYY-MM-DD>
**Plan:** <path to reviewed plan>
**Reviewers:** <list of activated personas>
**Composite Score:** <letter grade> — <verdict>

## Score Summary

| Persona | Grade | Key Finding |
|---------|-------|-------------|
| Cloud Architect | B | Missing multi-AZ failover details |
| Security Engineer | A | Comprehensive threat model |
| ... | ... | ... |

## Detailed Evaluation

### <Persona Name> (Grade: X)

| # | Evaluation Point | Grade | Notes |
|---|-----------------|-------|-------|
| CA1 | Service topology | A | Correct VPC hierarchy |
| CA2 | Scalability | C | No auto-scaling plan |

#### Recommendations
| Priority | Point | Recommendation |
|----------|-------|---------------|
| P0 | CA2 | Add auto-scaling strategy for compute tier |
| P1 | CA5 | Document cross-region failover path |

(repeat for each persona)

## Consolidated Recommendations

### P0 — Must Fix
1. [CA2] Add auto-scaling strategy...

### P1 — Should Fix
1. [SE9] Improve acceptance criteria...

### P2 — Nice to Have
1. [DX4] Define acronyms used in plan...
```

### Step 3: Write plan.md (enhanced plan)

Generate an improved version of the original plan that incorporates review feedback:

**Rules:**
- Preserve the original plan's structure and format exactly
- Enhance each story with: fuller context, expanded requirements, detailed implementation steps (with how-to guidance), stronger acceptance criteria
- Track all improvements with inline attribution: `<!-- [from: Security Engineer] -->`
- Leave already-complete sections unchanged — don't rewrite what's already good
- Incorporate all P0 and P1 recommendations directly into the relevant sections
- P2 recommendations: add as comments/suggestions, not direct changes
- If the original plan is HTML, the enhanced plan is HTML. If markdown, keep markdown.

### Step 4: Report to user

After writing both files, summarize:

> **Plan Review Complete**
>
> **Composite Score: B — Needs Work**
>
> | Persona | Grade |
> |---------|-------|
> | ... | ... |
>
> **P0 issues:** 2 (must fix before sprint planning)
> **P1 issues:** 5 (should fix for quality)
> **P2 issues:** 3 (nice to have)
>
> Files written:
> - `review/<date>-<slug>/analysis.md` — full scored analysis
> - `review/<date>-<slug>/plan.md` — enhanced plan with recommendations applied
>
> Review the analysis and enhanced plan. Want me to apply the P0 fixes to the original plan document?
