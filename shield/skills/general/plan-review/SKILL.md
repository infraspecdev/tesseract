---
name: plan-review
description: Use when a plan, architecture doc, or execution plan exists and needs expert review before implementation. Triggers on /plan-review, review my plan, document review.
---

# Plan Review

Dispatch parallel expert reviewer agents against a plan document to produce a scored analysis with prioritized recommendations and an enhanced plan.

## Output Path — MANDATORY

All review output goes into a per-run, date-keyed folder under the feature's `reviews/plan/` directory:

```
{output_dir}/{feature}/reviews/plan/{date}{_counter}/   ← {review_dir}
├── summary.md                        ← {review_summary}  (scored analysis, main output)
├── enhanced-plan.md                  ← {review_enhanced} (enhanced plan with feedback applied)
└── detailed/
    └── <agent>.md                    ← {review_detailed} (one per dispatched agent)

{output_dir}/{feature}/outputs/reviews/plan/{date}{_counter}/  ← {review_outputs_dir}
├── summary.html                      ← {review_summary_html}
├── enhanced-plan.html                ← {review_enhanced_html}
└── detailed/
    └── <agent>.html                  ← {review_detailed_html} (one per agent)
```

Where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`), `{feature}` is the feature folder name (`{feature-name}-YYYYMMDD`), `{date}` is today's ISO date (`YYYY-MM-DD`), and `{_counter}` is empty for the first run of the day or `_2`, `_3`, ... on same-day collisions. Numbered-run subfolders (`plan-review/{N}-{slug}/`) are gone. Reviews never overwrite prior runs.

**Resolving the counter:** before writing, list `{output_dir}/{feature}/reviews/plan/` for entries matching today's date. If `{date}/` does not exist, use `_counter=""`. Otherwise, find the highest `{date}_<N>/` and use `_counter="_<N+1>"`. **Do NOT** use any other path or directory structure. The Write tool creates directories automatically.

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
| 0a | Schema validate {plan_json} (validate_plan.py) — abort on schema failure | always | Yes |
| 0b | TRD section presence (validate_trd.py) — Critical findings on missing/vague/drift | when {plan_trd_md} exists | Yes |
| 0c | Stale-anchor check on design_refs[] — Critical finding per stale entry | when {plan_trd_md} exists | Yes |
| 0d | PRD↔TRD duplication (§2 + §5, 80-char substring threshold) | when both PRD and TRD exist | Yes |
| 0e | Implementation-manual rule (§7 code blocks > 20 lines without §8 rationale) | when {plan_trd_md} exists | Yes |
| 1 | Load plan document | always | Yes |
| 1a | Detect prior PRD in feature folder — read prd.meta.json if present | only if prd.meta.json exists | No |
| 2 | Select reviewer personas | always | Yes |
| 3 | Dispatch selected agents in parallel | always | Yes |
| 4 | Parse grades + calculate scores | always | Yes |
| 5 | Generate enhanced plan | always | Yes |
| 6 | Write summary + detailed findings (gates 0a-0e flow in here as Critical findings) | always | Yes |
| 7 | Update manifest | always | Yes |

### Step 1a: Detect prior PRD

If `{output_dir}/{feature}/prd.meta.json` exists (alongside `{prd}` = `{output_dir}/{feature}/prd.md`), read it. Use its `sections_present` and `type` to inform the plan-vs-PRD alignment check (future enhancement — for now, record it in `{review_summary}` as a "Source PRD" header line, e.g. `Source PRD: prd.md (type: standard, rubric: 1.2)`). This gives reviewers visibility into which PRD version the plan was built from.

## Plan Input

The skill reads plan data from (in priority order):
1. **Named plan sidecar** (`{plan_json}` = `{output_dir}/{feature}/plan.json`) — if name provided or only one feature exists. If multiple features exist and no name given, list them and ask.
2. **Plan markdown sources** at feature root — the canonical TRD `{plan_trd_md}` = `{output_dir}/{feature}/trd.md` (preferred) AND `{plan_md}` = `{output_dir}/{feature}/plan.md`. Legacy `plan-architecture.md` is also accepted when present (back-compat with pre-2.20 plans).
3. **HTML plan document** — `{plan_html}` / `{plan_trd_html}` (or legacy `{plan_arch_html}`) under `{output_dir}/{feature}/outputs/`; if only HTML exists, parse it for story content.
4. **User-provided path** — explicit path argument.

**Always start by checking for the plan sidecar at `{output_dir}/*/plan.json` and the canonical markdown sources at `{output_dir}/{feature}/plan.md`.** If no plans exist, ask the user for the plan location or check the project root.

## TRD-specific rules (run before persona dispatch)

When `{plan_trd_md}` is present, run these deterministic gates **before**
dispatching reviewers. Each gate emits a Critical finding on failure; the
finding flows into the reviewer pass and the enhanced plan.

### 0a. Schema validation (P0 — first gate)

Run `uv run shield/scripts/validate_plan.py {plan_json}` before applying any
rubric. A non-zero exit aborts the review with the named error printed in
the summary (`schema_violation`, `unknown_doc_enum`, `cycle_in_milestones`,
`milestone_id_unknown`, …). The reviewer dispatch only runs on schema-valid
sidecars.

### 0b. TRD section presence (14-section rubric)

Import the slug allow-list from `shield/schema/trd-sections.yaml` (14 entries)
and run `uv run shield/scripts/validate_trd.py {plan_trd_md}`. Each named
error (`missing_section:<slug>`, `missing_anchor:<slug>`, `out_of_order:<slug>`,
`unexpected_section:<text>`, `provenance_missing`) maps to a Critical finding:

- `missing_section:<slug>` → "TRD §N <title> is absent." (Critical)
- `vague_section:<slug>` → "TRD §N <title> contains only TBD/placeholder content." (Critical)
- `na_missing_reason:<slug>` → "TRD §N <title> declares `n/a` without a `— <reason>` suffix." (Critical)
- `unexpected_section:<text>` → "TRD contains an unprompted extra section: `<text>`." (Critical)
- `out_of_order:<slug>` → "TRD §N <title> appears out of canonical order." (Warn)
- `provenance_missing` → "TRD lacks the `<!-- generated by /plan vX.Y.Z on YYYY-MM-DD -->` stamp." (Warn)

Sections containing `n/a — <reason>` PASS the presence rule (they are an
explicit opt-out, not an omission).

### 0c. Stale-anchor rule

For every story in `{plan_json}` with `design_refs[]`, follow each ref's
`anchor_url`. If `anchor_url` starts with `trd.md#` and the slug after `#`
is not present in the live TRD (per the slug allow-list intersected with
actually-emitted anchors), the ref is **stale**. Emit a Critical finding:

> Story `EPIC-1-S1` design_refs[0].anchor_url points at `trd.md#api-create-user`,
> but the live TRD does not contain that anchor. Either restore the anchor
> or update the design_ref.

The validator also surfaces refs that the sidecar itself tagged `stale: true`
(set by the `/plan` re-run merge logic). Both flow into the same finding type.

### 0d. PRD↔TRD duplication

When both `{prd}` = `{output_dir}/{feature}/prd.md` AND `{plan_trd_md}` exist:

1. Extract the body of TRD §2 (Problem Statement) and §5 (Functional Requirements)
   between their `{#section-id}` anchors.
2. Extract the corresponding sections from the PRD (`## Problem` / `## Functional
   Requirements` or their numbered equivalents).
3. For each TRD body, find the longest common substring shared with the PRD body
   (case-insensitive, whitespace-collapsed).
4. If the longest common substring exceeds **80 characters**, emit a Critical
   finding: "TRD §N restates PRD §M verbatim (<N>-char overlap). Paraphrase or
   summarize instead." (Threshold lives in the rule body; do not change without
   bumping the rule version.)

### 0e. Implementation-manual rule (TRD §7)

Walk the TRD §7 High-Level Design body for fenced code blocks. For each
fence longer than **20 lines** of code (excluding the fence markers
themselves), check whether TRD §8 Alternatives Considered carries at least
one non-`n/a` body paragraph. If §8 is empty (or only `n/a — <reason>`), emit
a Critical finding:

> TRD §7 contains a 28-line code block, but §8 Alternatives Considered is
> empty. Move the code to `/lld <component>` or document the alternatives
> rejected in §8.

This catches the "design doc is really an implementation manual" anti-pattern
from `research.md`. Threshold lives in the rule body; do not change without
bumping the rule version.

## Persona Selection

See `personas.md` for the dynamic selection flowchart and trigger keywords.
See `dimensions.md` for the post-restructure dispatch registry (PM1-PM10 dim subagents +
legacy persona dispatches).

## Dispatch

When a persona is selected, dispatch per its row in `dimensions.md`:

- **PM persona selected (Pattern A — decomposed):** dispatch ALL 10 PM dim subagents in
  parallel (`shield:user-impact-clarity`, `shield:problem-solution-fit`,
  `shield:scope-discipline-of-plan`, `shield:prioritization-rationale`,
  `shield:stakeholder-communicability`, `shield:market-competitive-awareness`,
  `shield:adoption-rollout-risk`, `shield:success-metrics-defined`,
  `shield:reversibility-exit-cost`, `shield:business-value-alignment`). Each takes the plan
  doc path as input and returns a single-check JSON object.
- **Legacy persona selected:** dispatch the single named subagent (e.g., `shield:architect`,
  `shield:agile-coach`, `shield:dx-engineer`, `shield:finops-analyst`, `shield:sre`,
  `shield:platform-engineer`, `shield:backend-engineer`, `shield:security-engineer`) with
  the dispatch prompt skeleton from `templates.md`.

Launch all selected dispatches in parallel — that may be 10 PM dim calls + up to 8 legacy
persona calls in a single response. Aggregating sequentially throws away the depth gains.

Use `subagent_type` matching the agent name (e.g., `shield:architect`), or `general-purpose`
as fallback.

After all agents return, write each agent's full raw output to `{review_dir}/detailed/<agent>.md` (i.e. `{review_detailed}` with `agent=<that-subagent-slug>`) with a header and back-link:

```markdown
# <Agent Name> — Detailed Findings

> Back to [summary](../summary.md)

<full agent output>
```

## Collection & Scoring

After all agents return:

1. **Parse grades** — extract grade per evaluation point from each agent's output. PM dim
   subagents return single-check JSON; legacy personas return a multi-check scorecard.
2. **Group PM dim results under the PM persona** — collect all 10 PM single-check returns
   (filter on `persona: product-manager` in each result), then synthesize a PM persona block
   with the 10 dim grades and a computed `persona_grade` (numeric average rounded per
   `scoring.md`). This recreates the pre-restructure PM persona shape that downstream summary
   templates expect.
3. **Per-persona grade** — average numeric grades (A=4, B=3, C=2, D=1, F=0) within each
   persona, round using ranges in `scoring.md`.
4. **Composite score** — weighted average using persona weights from `dimensions.md` (PM
   persona is 0.7, applied to the aggregated PM grade), convert to verdict per `scoring.md`
   thresholds.
5. **Classify recommendations** — P0/P1/P2 per severity rules in `scoring.md`.

## Output

Write to `{review_dir}` = `{output_dir}/{feature}/reviews/plan/{date}{_counter}/`:
- `{review_summary}` (`summary.md`) — scored evaluation with consolidated recommendations
- `{review_enhanced}` (`enhanced-plan.md`) — enhanced version of original plan with feedback applied
- `{review_detailed}` (`detailed/<agent>.md`) — full output from each dispatched agent

The summary should include a "Detailed Agent Findings" section linking to each detailed file.

Render HTML to `{review_outputs_dir}` = `{output_dir}/{feature}/outputs/reviews/plan/{date}{_counter}/` via `render-markdown.sh`:
- `{review_summary_html}` (`summary.html`)
- `{review_enhanced_html}` (`enhanced-plan.html`)
- `{review_detailed_html}` (`detailed/<agent>.html`) — one per dispatched agent

After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

See `templates.md` for output formats and enhanced plan rules.

## User Review Gate

**Do NOT proceed until the user explicitly confirms.**

After writing output files, present the user with three options:
1. **Apply as-is** — replace `{plan_md}` with `{review_enhanced}`
2. **Apply with edits** — user modifies `{review_enhanced}` first, re-read before applying
3. **Skip** — keep `{plan_md}` unchanged

The user may also edit `{review_summary}`, ask for changes to specific recommendations, or reject recommendations. Wait for explicit confirmation before overwriting anything.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dispatching all 7 agents for a simple app plan with no infra | Follow trigger keyword matching — skip Cloud Architect and Cost/FinOps if no infra keywords |
| Grading infra points F on a non-infrastructure plan | Only activated personas grade — don't penalize for out-of-scope concerns |
| Applying enhanced plan without user review | Always wait for Step 5 confirmation — never auto-apply |
| Repeating scoring logic instead of referencing scoring.md | All grade math lives in `scoring.md` — reference it, don't inline it |
| Writing to legacy `plan-review/{N}-{slug}/` path | Reviews land under `{review_dir}` = `{output_dir}/{feature}/reviews/plan/{date}{_counter}/` — date-keyed, no numbered runs |
| Generating enhanced-plan.md in a different format than original | HTML in → HTML out, markdown in → markdown out |
| Softening grades because the user is under time pressure | Grade what the plan SAYS — missing info is F regardless of deadline |
| Giving partial credit for implied or assumed information | Grade only what is explicitly documented — "they probably meant X" is not in the plan |
