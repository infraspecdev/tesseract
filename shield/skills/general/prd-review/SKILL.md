---
name: prd-review
description: Use when a PRD exists (file, paste, URL) and needs gap analysis. Dispatches PM, agile-coach, tech-lead, DX, cost reviewer agents in parallel against a 13-dimension rubric; produces scored summary with severity-tiered gaps and P0-gated verdict. Triggers on /prd-review, review my PRD, PRD gap analysis.
---

# PRD Review

Dispatch parallel expert reviewer agents against a PRD to produce a scored analysis with prioritized gaps, severity tiers, and an enhanced PRD with suggested fixes.

## Output Path — MANDATORY

All review output goes into a per-run, date-keyed folder under the feature's `reviews/prd/` directory:

```
{output_dir}/{feature}/reviews/prd/{date}{_counter}/        ← {review_dir}
├── summary.md                              ← {review_summary}    (main output)
├── source-prd.md                           ← verbatim source snapshot (side-artifact)
├── enhanced-prd.md                         ← {review_enhanced}   (P0/P1 inline + P2 comments)
├── review-comments.json                    ← canonical structured per-section gaps (side-artifact)
└── detailed/
    ├── pm-reviewer.md                      ← {review_detailed} (agent=pm-reviewer)
    ├── agile-coach.md                      ← {review_detailed} (agent=agile-coach)
    ├── tech-lead-reviewer.md               ← {review_detailed} (agent=tech-lead-reviewer)
    ├── dx-reviewer.md                      ← {review_detailed} (agent=dx-reviewer)
    └── finops-analyst.md                   ← {review_detailed} (agent=finops-analyst)

{output_dir}/{feature}/outputs/reviews/prd/{date}{_counter}/  ← {review_outputs_dir}
├── summary.html                            ← {review_summary_html}
└── enhanced-prd.html                       ← {review_enhanced_html}
```

Where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`), `{feature}` is the feature folder (`{feature-name}-YYYYMMDD`), `{date}` is today's ISO date (`YYYY-MM-DD`), and `{_counter}` is empty for the first run of the day or `_2`, `_3`, ... on same-day collisions. Numbered-run subfolders (`prd-review/{N}-{slug}/`) are gone. Reviews never overwrite prior runs.

**Resolving the counter:** before writing, list `{output_dir}/{feature}/reviews/prd/` for entries matching today's date. If `{date}/` does not exist, use `_counter=""`. Otherwise, find the highest `{date}_<N>/` and use `_counter="_<N+1>"`. **Do NOT** use any other path. The Write tool creates directories automatically.

## When to Use

- User invokes `/prd-review` with a PRD source (file path, URL, or paste)
- User asks "review my PRD" / "what's wrong with this PRD" / "PRD gap analysis"

## When NOT to Use

- **Plan review** (technical breakdown / stories) — use `/plan-review` instead
- **Research review** — use the research workflow's PM-review mode
- **Code review** — use `/review`

## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Condition | Mandatory |
|---|---|---|---|
| 1 | Classify input (local/URL/paste) — see `ingest.md` Step 1 | always | Yes |
| 2 | Resolve via resolver chain — see `ingest.md` Step 2 | URL only | URL only |
| 3 | Snapshot to source-prd.md — see `ingest.md` Step 3 | always | Yes |
| 4 | Detect PRD type, confirm with user — see `ingest.md` Step 4 | always | Yes |
| 5 | Dispatch the 14 entries from `dimensions.md` in parallel (9 skill-internal PM prompts + 4 legacy persona dispatches) | always | Yes |
| 6 | Aggregate grades + compute composite + apply P0-gate — see `scoring.md` | always | Yes |
| 7 | Generate enhanced-prd.md with inline annotations | always | Yes |
| 8 | Write summary.md, review-comments.json, detailed/<persona>.md | always | Yes |
| 9 | Update manifest.json, regenerate index.html dashboard | always | Yes |
| 10 | Offer apply options (use as canonical / convert back / skip) | always | Yes |

## Workflow

### 1. Read context

- Read `.shield.json` for: `output_dir` (default `docs/shield`), `prd_review_personas` (default all 5), `prd_ingest_resolvers` (default `[]`)
- Determine feature folder context: `--feature <name>` flag, or `--name`, or fall back to a prompt asking the user

### 2. Ingest

Follow `ingest.md` Steps 1-3:
- Classify input (local path / URL / paste)
- Route through resolver chain if URL
- Snapshot result to `{review_dir}/source-prd.md` (where `{review_dir}` = `{output_dir}/{feature}/reviews/prd/{date}{_counter}` resolved per the Output Path section above)

### 3. Type detection + confirmation

Follow `ingest.md` Step 4. Confirm with user. Note: PRD-type override is per-invocation, not configured.

### 4. Dispatch (parallel — mixed pattern)

Read `dimensions.md` for the 14-entry dispatch registry. Two dispatch patterns coexist:

- **Skill-internal prompts (rows 1, 2, 3, 7, 8, 9, 10, 11, 12 — all PM dims):** read the prompt
  file at `prompts/<name>.md`, then dispatch a `general-purpose` Agent with that prompt content +
  `prd_path` and `prd_type` inputs. The agent returns one dim-block JSON.
- **Legacy persona dispatches (rows 4, 5+6, 13, anti-patterns):** dispatch the named subagent via
  `subagent_type: <agent-id>` (e.g. `shield:agile-coach`, `shield:architect`, `shield:finops-analyst`,
  `shield:dx-engineer`) with the per-persona prompt skeleton kept inline below. `shield:architect`
  is dispatched ONCE and grades both dim 5 and dim 6 in its returned envelope.

**Critical:** dispatch all 13 unique invocations in a single response (parallel). Aggregating
after waits.

Legacy-persona dispatch prompt skeleton (substitute per row):

```
You are reviewing a PRD in PRD-Review mode. Mode: Standalone.

**PRD source:** {source-prd.md path}
**PRD type:** {standard | lean — confirmed by user}
**Your assigned dimensions:** {list from dimensions.md row}

**Rubric:** Read `shield/skills/general/prd-review/rubric.md` for evaluation points per
dimension, severity model, and grade scale. Read `shield/skills/general/prd-review/scoring.md`
for the A-F → composite logic.

**Your job:**
1. Read the PRD at the path above.
2. For each of YOUR assigned dimensions, grade each evaluation point A-F (or N/A with
   reasoning, or informational for lean dims).
3. Aggregate to a per-dimension grade.
4. Identify gaps — for each non-A grade, write a one-sentence gap description.
5. For each gap, suggest a fix (one or two sentences) suitable for `enhanced-prd.md`
   annotation.

**Output format:** Return JSON in the per-persona envelope:

{
  "persona": "<your agent id>",
  "persona_grade": "A|B|C|D|F",
  "dimensions": [
    { "id": <int>, "name": "...", "grade": "A|B|C|D|F|N/A|informational", "na_reasoning": "...",
      "evaluation_points": [ {"id": "Na", "grade": "...", "severity": "...", "gap": "...", "suggestion": "..."} ] }
  ],
  "anti_patterns": [ {"name": "...", "evidence_line": 42, "evidence_quote": "..."} ]  // DX only
}
```

Special instructions per legacy persona (unchanged from the deprecated `personas.md`):

- **Agile-coach (dim 4):** apply AC1-AC12 framework including persona-goal coverage (consume
  `shield:story-coverage` skill) and archetypal-flow coverage.
- **Tech-lead / architect (dims 5, 6):** treat 5b/5e as Critical for any feature with user data,
  Important for purely internal infra. Grade dim 5 and dim 6 in one dispatch.
- **DX (anti-patterns):** primary output is the `anti_patterns` array; no numeric dim.
- **Cost / finops-analyst (dim 13):** N/A allowed for clearly internal-only features (e.g.,
  internal-tool fixture) with reasoning.

### 5. Aggregate

Collect dim-blocks from all 13 dispatch results. Two envelope shapes coexist:

- **Per-dim envelope (skill-internal prompts):** the returned JSON IS the dim-block — use directly.
- **Per-persona envelope (legacy personas):** unwrap the `dimensions[]` array; each element is a
  dim-block. Also capture `anti_patterns[]` from the DX dispatch.

Group dim-blocks by their owning persona (per `dimensions.md`'s "Owning persona" column).
Then apply `scoring.md`:
- Per-dimension grade (already in each dim-block)
- Per-persona grade (compute by averaging the persona's dim-blocks numerically; for `product-manager`,
  this means averaging the 9 PM dim-blocks since the omnibus persona-grade is no longer emitted)
- Composite weighted average across activated personas
- Detect P0s (any Critical eval point graded D or F)
- Apply P0-gate to verdict

### 6. Generate enhanced-prd.md

For each gap-with-suggestion in the aggregated JSON:
- P0 or P1: insert inline in the relevant section of source-prd.md content; wrap with `<!-- [from: <Persona>] -->` attribution
- P2: insert as a comment block adjacent to the relevant section, prefixed `<!-- Suggestion (<Persona>): ... -->`
- Informational: insert as comment with `<!-- [informational] -->` tag

Preserve source-prd.md's exact structure; only ADD content, never replace.

Write the result to `enhanced-prd.md`.

### 7. Write output artifacts

| File | Content |
|---|---|
| `summary.md` | Scored analysis (template in `templates.md` if you create one, or follow the shape in the spec's Architecture summary) |
| `source-prd.md` | (already written by Step 2) |
| `enhanced-prd.md` | (Step 6 output) |
| `review-comments.json` | Aggregated JSON conforming to the schema in spec's "Enhanced PRD output and comments export" section |
| `detailed/pm-reviewer.md` | PM persona's full report (markdown rendering of their JSON, kept for skeptics) |
| `detailed/agile-coach.md` | Agile-coach persona's full report |
| `detailed/tech-lead-reviewer.md` | Tech-lead persona's full report |
| `detailed/dx-reviewer.md` | DX persona's anti-pattern findings + clarity notes |
| `detailed/finops-analyst.md` | Cost persona's full report |

### 7b. Render review HTML

Render `summary.md` and `enhanced-prd.md` into `{review_outputs_dir}` via the shared shell, then refresh the manifest-derived page assets:

```bash
"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    {review_dir}/summary.md \
  --shell "$CLAUDE_PLUGIN_ROOT/templates/shell.html" \
  --out   {review_outputs_dir}/summary.html \
  --assets-root "{output_dir}" \
  --title "Review — {feature}"

"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    {review_dir}/enhanced-prd.md \
  --shell "$CLAUDE_PLUGIN_ROOT/templates/shell.html" \
  --out   {review_outputs_dir}/enhanced-prd.html \
  --assets-root "{output_dir}" \
  --title "Review — {feature}"

uv run "$CLAUDE_PLUGIN_ROOT/scripts/write_shield_assets.py" --output-dir "{output_dir}"
```

Do NOT write per-skill `*.shell.html` files — the shared shell at `$CLAUDE_PLUGIN_ROOT/templates/shell.html` owns DOCTYPE/head/nav/footer.

### 8. Update manifest + dashboard

- Append a new entry to `{output_dir}/manifest.json`
- Regenerate `{output_dir}/index.html` to show the new review with verdict badge

### 9. Offer apply options

Emit to user (template):

```
PRD Review complete.

Verdict: <Ready | Needs Work (composite X.X, blocked by N P0s) | Not Ready>

Files written:
- summary.md       — scored analysis
- enhanced-prd.md  — your PRD with suggested fixes applied
- review-comments.json — machine-readable for converters
- detailed/<persona>.md — per-reviewer findings

What next?
1. **Use enhanced as canonical PRD** — copy `{review_enhanced}` to `{prd}` (i.e. `{output_dir}/{feature}/prd.md`) so downstream Shield commands consume the fixed version
2. **Convert back to original format** — produce `enhanced-prd.<ext>` in source's format (HTML / Notion-flavored markdown)
3. **Skip** — keep `{review_enhanced}` in `{review_dir}`; do nothing else
```

User picks; Shield executes.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Dispatching reviewer agents sequentially | Dispatch all 13 unique invocations in a single response (parallel) |
| Writing review output to the wrong path | Must be `{review_dir}` = `{output_dir}/{feature}/reviews/prd/{date}{_counter}/` — never the legacy `prd-review/{N}-{slug}/`, never `shield/` or `.shield/` |
| Overwriting source-prd.md after dispatch | Source snapshot is immutable; only enhanced-prd.md gets annotated |
| Skipping P0-gate when verdict has P0 + high composite | Verdict is Needs Work regardless of composite if any P0 exists |
| Producing enhanced-prd.md without inline attribution | Every P0/P1 inline edit MUST have `<!-- [from: <Persona>] -->` attribution |
| Auto-generating review-comments.md | Don't — JSON is canonical, markdown view is summary.md (per spec's drop-review-comments-md decision) |

## See Also

- `ingest.md` — input classification + resolver chain
- `rubric.md` — 13 dimensions, evaluation points, severity model
- `dimensions.md` — 14-entry dispatch registry (replaces the old persona-keyed table)
- `prompts/*.md` — 9 skill-internal PM dim prompts (Pattern B)
- `scoring.md` — A-F → composite + P0-gate (accepts both envelope shapes)
