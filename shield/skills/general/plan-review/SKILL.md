---
name: plan-review
description: Use when a plan, architecture doc, or execution plan exists and needs expert review before implementation. Triggers on /plan-review, review my plan, document review.
---

# Plan Review

Dispatch parallel expert reviewer agents against a plan document to produce a scored analysis with prioritized recommendations and an enhanced plan.

## Output Path — MANDATORY

Write the analysis using the Write tool to **exactly** this path:

```
shield/docs/analysis-YYYYMMDD-HHMMSS.md
```

Replace `YYYYMMDD-HHMMSS` with the current date and time. **Do NOT** use any other path, filename, or directory. No `latest/`, no topic-based names, no custom filenames. The Write tool creates `shield/docs/` automatically.

## When to Use

- User asks to review a plan, architecture doc, or execution plan
- After plan-docs skill generates a plan
- User mentions "plan review", "review my plan", "review this document"
- User invokes `/plan-review`

## When NOT to Use

- **Code review** — use `/review` instead (dispatches agents in infra-code/app-code mode)
- **Single-page design docs** without stories or infrastructure — overkill
- **Non-plan documents** (READMEs, changelogs, runbooks) — wrong tool

## Plan Input

The skill reads plan data from (in priority order):
1. **Named plan sidecar** (`shield/docs/plans/<name>.json`) — if name provided or only one plan exists. If multiple plans exist and no name given, list them and ask.
2. **Plan docs** in `shield/docs/` — architecture docs, research findings (glob for `shield/docs/architecture-*.html`, `shield/docs/research-*.md`)
3. **HTML plan document** — if only HTML exists, parse it for story content
4. **Markdown plan document** — path provided by user or auto-detected
5. **User-provided path** — explicit path argument

**Always start by checking for plans in `shield/docs/plans/` and docs in `shield/docs/`.** If no plans exist, ask the user for the plan location or check the project root.

## Persona Selection

See `personas.md` for the full catalog, weights, and dynamic selection flowchart.

## Dispatch

Read each selected agent's markdown file from `agents/` and `scoring.md`, then launch all agents in parallel using the Agent tool. See `templates.md` for the dispatch prompt structure.

Use `subagent_type` matching the agent name (e.g., `shield:architecture-reviewer`) when available, otherwise `general-purpose`.

## Collection & Scoring

After all agents return:

1. **Parse grades** — extract grade per evaluation point from each agent's output
2. **Per-persona grade** — average numeric grades (A=4, B=3, C=2, D=1, F=0), round using ranges in `scoring.md`
3. **Composite score** — weighted average using persona weights, convert to verdict per `scoring.md` thresholds
4. **Classify recommendations** — P0/P1/P2 per severity rules in `scoring.md`

## Output

Write to `shield/docs/`:
- `shield/docs/analysis-YYYYMMDD-HHMMSS.md` — scored evaluation with consolidated recommendations
- `shield/docs/plan-enhanced-YYYYMMDD-HHMMSS.md` — enhanced version of original plan with feedback applied

See `templates.md` for output formats and enhanced plan rules.

## User Review Gate

**Do NOT proceed until the user explicitly confirms.**

After writing output files, present the user with three options:
1. **Apply as-is** — replace original plan with enhanced `plan-enhanced-YYYYMMDD-HHMMSS.md`
2. **Apply with edits** — user modifies `plan-enhanced-YYYYMMDD-HHMMSS.md` first, re-read before applying
3. **Skip** — keep original plan unchanged

The user may also edit `analysis-YYYYMMDD-HHMMSS.md`, ask for changes to specific recommendations, or reject recommendations. Wait for explicit confirmation before overwriting anything.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dispatching all 5 agents for a simple app plan with no infra | Follow trigger keyword matching — skip Cloud Architect and Cost/FinOps if no infra keywords |
| Grading infra points F on a non-infrastructure plan | Only activated personas grade — don't penalize for out-of-scope concerns |
| Applying enhanced plan without user review | Always wait for Step 5 confirmation — never auto-apply |
| Repeating scoring logic instead of referencing scoring.md | All grade math lives in `scoring.md` — reference it, don't inline it |
| Generating plan.md in different format than original | HTML in → HTML out, markdown in → markdown out |
| Softening grades because the user is under time pressure | Grade what the plan SAYS — missing info is F regardless of deadline |
| Giving partial credit for implied or assumed information | Grade only what is explicitly documented — "they probably meant X" is not in the plan |
