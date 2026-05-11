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

## Workflow

(Filled in by Task 9 — orchestration steps + step skeleton)

## See Also

- `ingest.md` — input classification + resolver chain
- `rubric.md` — 13 dimensions, evaluation points, severity model
- `personas.md` — reviewer dispatch prompts
- `scoring.md` — A-F → composite + P0-gate
