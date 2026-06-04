# Plan Review Templates

## Dispatch Prompt

Dispatch each selected reviewer via the `Agent` tool with `subagent_type` set to the agent's
slug (e.g. `shield:architect`, `shield:security-engineer`, or one of the PM1-PM10 dim subagents
— see `dimensions.md`). The subagent loads its OWN persona definition; do **not** inline the
agent markdown into the prompt. Pass only the plan path and the rubric pointer:

```
You are reviewing a plan document in plan-review mode.

<plan-path>
{path to the plan document — e.g. docs/shield/{feature}/plan.md or the source-plan.md snapshot}
</plan-path>

Grade against your persona's evaluation points using the rubric at
`shield/skills/general/plan-review/scoring.md`. Produce output in the exact format
specified in your persona's Output Format section.

Important:
- Grade based on what the plan SAYS, not what you assume
- Missing information defaults to F, not "N/A"
- Be specific in notes — quote the plan or cite what's missing
- Recommendations must be actionable — not "improve this" but "add X to section Y"
```

Fall back to `subagent_type: general-purpose` only if the named subagent is unavailable; in
that case inline the agent's markdown file as a `<persona>` block.

## plan-review-summary.md Format

```markdown
# Plan Review: <Plan Title>

**Date:** <YYYY-MM-DD>
**Plan:** <path to reviewed plan>
**Reviewers:** <list of activated personas>
**Composite Score:** <letter grade> — <verdict>

## Deterministic Gates

Results of gates 0a–0i (run before persona dispatch). List each as PASS or the named
Critical/High/Medium finding. A failed gate is a P0 regardless of persona grades.

| Gate | Check | Result |
|------|-------|--------|
| 0a | plan.json schema (validate_plan.py) | PASS |
| 0b | TRD 14-section presence (validate_trd.py) | PASS |
| 0c | Stale design_refs[] anchors | PASS |
| 0d | PRD↔TRD duplication | PASS |
| 0e | Implementation-manual (TRD §7) | PASS |
| 0f–0i | touches_lld / registry / undocumented / LLD-draft | PASS |

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

## Detailed Agent Findings

| Agent | Detailed Report |
|-------|----------------|
| <Persona Name> | [detailed/<agent>.md](../detailed/<agent>.md) |
```

## plan-enhanced.md Rules

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
> Files written (under `{review_dir}` = `{output_dir}/{feature}/reviews/plan/{date}{_counter}/`):
> - `summary.md` — full scored analysis
> - `enhanced-plan.md` — enhanced plan with recommendations applied
> - `detailed/<agent>.md` — per-agent detailed findings
>
> Review the analysis and enhanced plan. You can edit either file before proceeding.
>
> When you're ready, let me know:
> 1. **Apply as-is** — replace the original plan with the enhanced `enhanced-plan.md`
> 2. **Apply with your edits** — I'll use your modified `enhanced-plan.md` as the source
> 3. **Skip** — keep the original plan unchanged
