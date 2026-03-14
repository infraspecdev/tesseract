# Plan Review Templates

## Dispatch Prompt

For each selected agent, use this prompt structure with the Agent tool:

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

Use `subagent_type` matching the agent name (e.g., `shield:architecture-reviewer`) when available, otherwise use `general-purpose`.

## analysis.md Format

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

## Enhanced plan.md Rules

- Preserve the original plan's structure and format exactly
- Enhance each story with: fuller context, expanded requirements, detailed implementation steps (with how-to guidance), stronger acceptance criteria
- Track all improvements with inline attribution: `<!-- [from: Security Engineer] -->`
- Leave already-complete sections unchanged — don't rewrite what's already good
- Incorporate all P0 and P1 recommendations directly into the relevant sections
- P2 recommendations: add as comments/suggestions, not direct changes
- If the original plan is HTML, the enhanced plan is HTML. If markdown, keep markdown.

## User Report Format

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
> Review the analysis and enhanced plan. You can edit either file before proceeding.
>
> When you're ready, let me know:
> 1. **Apply as-is** — replace the original plan with the enhanced `plan.md`
> 2. **Apply with your edits** — I'll use your modified `plan.md` as the source
> 3. **Skip** — keep the original plan unchanged
