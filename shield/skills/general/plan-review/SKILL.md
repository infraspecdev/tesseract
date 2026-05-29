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
| 0f | `touches_lld_drift` — persisted `milestones[i].touches_lld[]` ≠ rollup of `design_refs[].component` per milestone | when plan.json is schema 1.5+ | Yes — High |
| 0g | `lld_components_integrity` — every `design_refs[].component` (where doc==lld) must appear in `lld_components[]`; type must be in enum; no duplicate names; fork_blob_sha matches canonical when set | when plan.json is schema 1.5+ | Yes — High (missing/dup/type) · Medium (fork drift) |
| 0h | `undocumented_lld` — `docs/lld/<c>.md` exists on disk but a story's `design_refs[].anchor_url` for that component is null | when canonical LLDs exist | Yes — Medium |
| 0i | `lld_draft_review` — apply the LLD structural rubric (missing always-on, missing forced subsection, vague TBDs in always-on, PoD lifted but vague) to every `docs/shield/{feature}/lld-*.md` draft | when feature-folder LLD drafts exist | Yes — High/Medium/Review depending on issue |
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

### 0f. `touches_lld_drift` rule

Wraps `shield/scripts/validate_plan.py`'s `_check_touches_lld_drift` output
(introduced in M1 plan, Task 4). For every milestone in the plan:

```python
persisted = set(milestone["touches_lld"])
rollup = {ref.component for story in milestone.stories
                       for ref in story.design_refs
                       if ref.doc == "lld"}
if persisted != rollup:
    flag as `touches_lld_drift`
```

**Why it matters:** The persisted field exists so PM-sync, reviewers, and
humans can read it without recomputing. Drift means the persisted value is
lying — the source-of-truth `design_refs[]` and the convenience `touches_lld[]`
have diverged.

**Severity:** High. The plan.json is internally inconsistent.

**Suggested fix output:**

```
For milestone <M>:
  persisted touches_lld: [list]
  rollup from design_refs[]: [list]
  To fix: update plan.json milestones[<M>].touches_lld = [rollup].
```

**Fixture reference:** `shield/evals/lld-docs/fixtures/neg-touches-lld-drift/plan.json`.

### 0g. `lld_components_integrity` rule

Wraps `shield/scripts/validate_plan.py`'s `_check_lld_component_missing`
output, plus inline checks for `type` enum, duplicate names, and
`fork_blob_sha` drift against the live canonical.

**Four sub-checks:**

1. **Missing registry entry.** For every `design_refs[].component` (where
   `doc == "lld"`), confirm it appears in `lld_components[].name`.
2. **Type enum.** Every `lld_components[].type` is in `{"backend", "infra"}`.
   Other values fail.
3. **Duplicate names.** `lld_components[].name` values are unique. Duplicates
   mean the registry contradicts itself.
4. **Fork drift uncaught.** For every `lld_components[]` entry where
   `fork_blob_sha` is non-null AND `docs/lld/<name>.md` exists,
   verify `git hash-object docs/lld/<name>.md == fork_blob_sha`.
   Mismatch → finding `lld_fork_drift_uncaught` (Medium). Suggested fix:
   re-run /plan to refresh fork_blob_sha — /implement's step 5h will
   then auto-heal at milestone close.

**Severity:** High for sub-checks 1–3 (registry breaks promotion); Medium for
sub-check 4 (drift caught later by step 5h, but better surfaced now).

**Suggested fix output (per sub-check):**

```
Missing registry entry for component 'user-service':
  Referenced by: EPIC-1-S1, EPIC-1-S2
  To fix: add to lld_components[]: { "name": "user-service", "type": "<inferred-or-asked>", "fork_blob_sha": null }
```

```
Invalid type for component 'foo': 'lambda'
  Valid values: backend, infra
  To fix: update lld_components[<index>].type.
```

```
Duplicate component name in lld_components[]: 'foo' (entries at indices 0 and 2)
  To fix: drop one entry (the duplicate); confirm fork_blob_sha matches across both before dropping.
```

**Fixture references:**
- `shield/evals/lld-docs/fixtures/neg-component-not-in-registry/plan.json`
- `shield/evals/lld-docs/fixtures/neg-invalid-type/plan.json`
- `shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught/`

### 0h. `undocumented_lld` rule

Detects the gap state where an LLD has landed at the canonical path but
the plan.json still has TODO placeholders for it.

**Check:**

```python
for epic in plan.epics:
    for story in epic.stories:
        for ref in story.design_refs:
            if ref.doc == "lld" and ref.anchor_url is None:
                canonical = Path(f"docs/lld/{ref.component}.md")
                if canonical.exists():
                    slug, match_type = select_anchor(story.name, slugs_for(ref.component))
                    finding(story.id, ref.component, slug, match_type)
```

**Why it matters:** Before /implement's step 5h has run, design_refs[] entries
may legitimately carry `anchor_url: null` (the LLD doesn't exist yet). After
the LLD lands, those entries should be back-filled. If they're still null
post-promotion, either /implement skipped the back-fill (bug) or a human
edited plan.json afterward (drift). Either way, the LLD layer's value is
diminished — stories don't know which section they implement.

**Severity:** Medium. Doesn't block /implement runs but degrades traceability.

**Suggested fix output:**

```
Story EPIC-1-S1 has a TODO LLD ref for component 'user-service', but
docs/lld/user-service.md exists.

Suggested back-fill:
  anchor_url: lld-user-service.md#data-model
  label: §4 Data model
  match type: [heuristic]

To apply: update plan.json epics[].stories[].design_refs[].
```

**Fixture reference:** `shield/evals/lld-docs/fixtures/neg-undocumented-lld/`.

### 0i. `lld_draft_review` rule

Mirrors the TRD-review rubric pattern (rule 0b), applied to LLD drafts in the
feature folder.

**Procedure for each `docs/shield/{feature}/lld-*.md`:**

1. Parse the provenance comment to determine template type
   (look for `<!-- generated by /lld v… -->`; the filename `lld-<name>.md`
   gives the component; the matching `lld_components[]` entry gives the
   `type`).
2. Load the slug allow-list from `shield/schema/lld-sections-<type>.yaml`.
3. **Always-on presence check:** for every section where `promote_on_demand: false`,
   verify the heading + anchor are present in the draft. If absent → finding.
4. **Forced-subsection check:** for §12, verify every entry in
   `forced_subsections[]` has its sub-anchor present. If absent → finding.
5. **`n/a — <reason>` escape check:** any section may declare `n/a — <reason>`
   in place of populated content. Vague placeholders
   (`TBD`, `TODO`, `to be determined`, `to do`, `[fill in]`) in always-on
   sections → finding.
6. **PoD lifted-but-vague check:** for promote-on-demand sections rendered as
   `<details open>` (lifted), verify content is non-vague. A lifted PoD
   section with only `TBD` or `n/a` is a finding.

**Severities:**
- Missing always-on section → **High**.
- Missing §12 forced subsection → **Medium**.
- Vague TBD in always-on → **Review** (informational; human decides).
- PoD lifted but vague → **Review**.

**Suggested fix output:**

```
Draft docs/shield/{feature}/lld-foo.md:
  - Missing always-on section: §3 module-layout (severity: High)
  - Missing forced subsection: §12.4 latency-breakdown (severity: Medium)
  - Vague TBD in §1 overview (severity: Review)

To fix:
  - Add the missing sections per shield/schema/lld-sections-backend.yaml.
  - Replace `TBD` with concrete content or `n/a — <reason>`.
```

**Fixture references:**
- `shield/evals/lld-docs/fixtures/neg-missing-section-1/lld.md` through `…-8`
- `shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-1/lld.md` through `…-4`
- `shield/evals/lld-docs/fixtures/neg-vague-tbd/lld.md`
- `shield/evals/lld-docs/fixtures/neg-pod-lifted-vague/lld.md`

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
