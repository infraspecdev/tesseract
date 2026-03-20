---
name: plan-review
description: Use when a plan, architecture doc, or execution plan exists and needs expert review before implementation. Triggers on /plan-review, review my plan, document review.
---

# Plan Review

Dispatch parallel expert reviewer agents against a plan document to produce a scored analysis with prioritized recommendations and an enhanced plan.

## Output Path — MANDATORY

All review output goes into the feature's plan-review directory:

```
{output_dir}/{feature}/plan-review/{N}-{slug}/
├── summary.md                        ← scored analysis (main output)
├── enhanced-plan.md                  ← enhanced plan with feedback applied
└── detailed/
    └── <agent-name>.md               ← one file per dispatched agent
```

Where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`), `{feature}` is the feature folder name (`{feature-name}-YYYYMMDD`), `{N}` is a sequential number, and `{slug}` is a short kebab-case descriptor. **Do NOT** use any other path or directory structure. The Write tool creates directories automatically.

## When to Use

- User asks to review a plan, architecture doc, or execution plan
- After plan-docs skill generates a plan
- User mentions "plan review", "review my plan", "review this document"
- User invokes `/plan-review`

## When NOT to Use

- **Code review** — use `/review` instead (dispatches agents in infra-code/app-code mode)
- **Single-page design docs** without stories or infrastructure — overkill
- **Non-plan documents** (READMEs, changelogs, runbooks) — wrong tool

## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Load plan document | always | Yes |
| 2 | Select reviewer personas | always | Yes |
| 3 | Dispatch selected agents in parallel | always | Yes |
| 4 | Parse grades + calculate scores | always | Yes |
| 5 | Generate enhanced plan | always | Yes |
| 6 | Write summary + detailed findings | always | Yes |
| 7 | Update manifest | always | Yes |

## Plan Input

The skill reads plan data from (in priority order):
1. **Named plan sidecar** (`{output_dir}/{feature}/plan.json`) — if name provided or only one feature exists. If multiple features exist and no name given, list them and ask.
2. **Plan docs** in `{output_dir}/{feature}/` — architecture docs, research findings (glob for `{output_dir}/{feature}/plan/` and `{output_dir}/{feature}/research/`)
3. **HTML plan document** — if only HTML exists, parse it for story content
4. **Markdown plan document** — path provided by user or auto-detected
5. **User-provided path** — explicit path argument

**Always start by checking for plan sidecar in `{output_dir}/*/plan.json` and docs in `{output_dir}/{feature}/`.** If no plans exist, ask the user for the plan location or check the project root.

## Persona Selection

See `personas.md` for the full catalog, weights, and dynamic selection flowchart.

## Dispatch

Read each selected agent's markdown file from `agents/` and `scoring.md`, then launch all agents in parallel using the Agent tool. See `templates.md` for the dispatch prompt structure.

Use `subagent_type` matching the agent name (e.g., `shield:architecture-reviewer`) when available, otherwise `general-purpose`.

After all agents return, write each agent's full raw output to `plan-review/{N}-{slug}/detailed/<agent-name>.md` with a header and back-link:

```markdown
# <Agent Name> — Detailed Findings

> Back to [summary](../summary.md)

<full agent output>
```

## Collection & Scoring

After all agents return:

1. **Parse grades** — extract grade per evaluation point from each agent's output
2. **Per-persona grade** — average numeric grades (A=4, B=3, C=2, D=1, F=0), round using ranges in `scoring.md`
3. **Composite score** — weighted average using persona weights, convert to verdict per `scoring.md` thresholds
4. **Classify recommendations** — P0/P1/P2 per severity rules in `scoring.md`

## Output

Write to `{output_dir}/{feature}/plan-review/{N}-{slug}/`:
- `summary.md` — scored evaluation with consolidated recommendations
- `enhanced-plan.md` — enhanced version of original plan with feedback applied
- `detailed/<agent-name>.md` — full output from each dispatched agent

The summary should include a "Detailed Agent Findings" section linking to each detailed file.

After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

See `templates.md` for output formats and enhanced plan rules.

## User Review Gate

**Do NOT proceed until the user explicitly confirms.**

After writing output files, present the user with three options:
1. **Apply as-is** — replace original plan with enhanced `plan-review/{N}-{slug}/enhanced-plan.md`
2. **Apply with edits** — user modifies `plan-review/{N}-{slug}/enhanced-plan.md` first, re-read before applying
3. **Skip** — keep original plan unchanged

The user may also edit `plan-review/{N}-{slug}/summary.md`, ask for changes to specific recommendations, or reject recommendations. Wait for explicit confirmation before overwriting anything.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dispatching all 7 agents for a simple app plan with no infra | Follow trigger keyword matching — skip Cloud Architect and Cost/FinOps if no infra keywords |
| Grading infra points F on a non-infrastructure plan | Only activated personas grade — don't penalize for out-of-scope concerns |
| Applying enhanced plan without user review | Always wait for Step 5 confirmation — never auto-apply |
| Repeating scoring logic instead of referencing scoring.md | All grade math lives in `scoring.md` — reference it, don't inline it |
| Generating plan.md in different format than original | HTML in → HTML out, markdown in → markdown out |
| Softening grades because the user is under time pressure | Grade what the plan SAYS — missing info is F regardless of deadline |
| Giving partial credit for implied or assumed information | Grade only what is explicitly documented — "they probably meant X" is not in the plan |
