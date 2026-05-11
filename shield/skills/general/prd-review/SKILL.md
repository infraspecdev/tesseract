---
name: prd-review
description: Use when a PRD exists (file, paste, URL) and needs gap analysis. Dispatches PM, agile-coach, tech-lead, DX, cost reviewer agents in parallel against a 13-dimension rubric; produces scored summary with severity-tiered gaps and P0-gated verdict. Triggers on /prd-review, review my PRD, PRD gap analysis.
---

# PRD Review

Dispatch parallel expert reviewer agents against a PRD to produce a scored analysis with prioritized gaps, severity tiers, and an enhanced PRD with suggested fixes.

## Output Path — MANDATORY

All review output goes into the feature's prd-review directory:

```
{output_dir}/{feature}/prd-review/{N}-{slug}/
├── summary.md                              ← scored analysis (main output)
├── source-prd.md                           ← verbatim snapshot of original source
├── enhanced-prd.md                         ← P0/P1 inline + P2 comments
├── review-comments.json                    ← canonical structured per-section gaps
└── detailed/
    ├── pm-reviewer.md
    ├── agile-coach-reviewer.md
    ├── tech-lead-reviewer.md
    ├── dx-reviewer.md
    └── cost-reviewer.md
```

Where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`), `{feature}` is the feature folder (`{feature-name}-YYYYMMDD`), `{N}` is sequential, `{slug}` is a kebab-case descriptor. **Do NOT** use any other path. The Write tool creates directories automatically.

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
| 5 | Dispatch 5 reviewer agents in parallel — see `personas.md` | always | Yes |
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
- Snapshot result to `{output_dir}/{feature}/prd-review/{N}-{slug}/source-prd.md`

The slug is derived from the feature name + a short descriptor (e.g., `1-add-oauth-login`).

### 3. Type detection + confirmation

Follow `ingest.md` Step 4. Confirm with user. Note: PRD-type override is per-invocation, not configured.

### 4. Persona dispatch (parallel)

Read `personas.md` for the 5 dispatch prompts. Substitute the per-persona variables and dispatch with the `Agent` tool, `subagent_type` set per the persona's agent ID.

**Critical:** dispatch all 5 in a single response (parallel). Aggregating after waits.

### 5. Aggregate

Parse each persona's returned JSON. Apply `scoring.md`:
- Per-dimension grades (already in persona JSON)
- Per-persona grades (already in persona JSON)
- Composite weighted average
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
| `detailed/agile-coach-reviewer.md` | Agile-coach persona's full report |
| `detailed/tech-lead-reviewer.md` | Tech-lead persona's full report |
| `detailed/dx-reviewer.md` | DX persona's anti-pattern findings + clarity notes |
| `detailed/cost-reviewer.md` | Cost persona's full report |

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
1. **Use enhanced as canonical PRD** — copy enhanced-prd.md to prd/{N}-{slug}/prd.md so downstream Shield commands consume the fixed version
2. **Convert back to original format** — produce enhanced-prd.<ext> in source's format (HTML / Notion-flavored markdown)
3. **Skip** — keep enhanced-prd.md in the review folder; do nothing else
```

User picks; Shield executes.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Dispatching reviewer agents sequentially | Dispatch all 5 in a single response (parallel) |
| Writing review output to the wrong path | Must be `{output_dir}/{feature}/prd-review/{N}-{slug}/` — never `shield/` or `.shield/` |
| Overwriting source-prd.md after dispatch | Source snapshot is immutable; only enhanced-prd.md gets annotated |
| Skipping P0-gate when verdict has P0 + high composite | Verdict is Needs Work regardless of composite if any P0 exists |
| Producing enhanced-prd.md without inline attribution | Every P0/P1 inline edit MUST have `<!-- [from: <Persona>] -->` attribution |
| Auto-generating review-comments.md | Don't — JSON is canonical, markdown view is summary.md (per spec's drop-review-comments-md decision) |

## See Also

- `ingest.md` — input classification + resolver chain
- `rubric.md` — 13 dimensions, evaluation points, severity model
- `personas.md` — reviewer dispatch prompts
- `scoring.md` — A-F → composite + P0-gate
