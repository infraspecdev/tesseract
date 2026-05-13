---
name: prd-review
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Run multi-persona PRD review against a 13-dimension rubric. Produces scored summary with severity-tiered gaps and an enhanced PRD with suggested fixes.
---

# /prd-review

Dispatch parallel reviewer agents against a PRD and produce a scored gap analysis.

## Usage

```
/prd-review                              # prompts for a source
/prd-review <path>                       # local file path
/prd-review <url>                        # any URL (Notion, Confluence, Google Docs, public web)
/prd-review --paste                      # read pasted content from prompt
/prd-review --feature <name> <source>    # explicit feature folder name
```

## What it does

1. **Classifies** the input as local file / URL / paste
2. **Resolves URLs** via runtime MCP discovery (Notion MCP if present for `notion.so/*`, Atlassian MCP for `*.atlassian.net/wiki/*`, etc.) with WebFetch fallback and universal paste fallback
3. **Snapshots** the source to `source-prd.md` (immutable)
4. **Detects PRD type** (lean vs standard) and confirms with user
5. **Dispatches 5 reviewer agents** in parallel: PM (`shield:product-manager-reviewer`), Agile-coach (`shield:agile-coach-reviewer`), Tech-lead (`shield:architecture-reviewer`), DX (`shield:dx-engineer-reviewer`), Cost (`shield:cost-reviewer`)
6. **Aggregates** grades into a composite verdict (A-F per dimension → per-persona → weighted composite); applies P0-gate
7. **Writes 5 output artifacts** to `{output_dir}/{feature}/prd-review/{N}-{slug}/`:
   - `summary.md` — scored gap analysis
   - `source-prd.md` — verbatim source snapshot
   - `enhanced-prd.md` — P0/P1 inline annotations + P2 comments
   - `review-comments.json` — canonical machine-readable gap export
   - `detailed/<persona>.md` × 5 — per-reviewer detailed reports
8. **Updates** `manifest.json` and `index.html` dashboard
9. **Offers apply options** — use enhanced as canonical PRD / convert back to original format / skip

## Reference

Full behavior in `shield/skills/general/prd-review/SKILL.md`.

## See also

- `/plan` — generate a technical plan from a PRD
- `/plan-review` — review a generated plan
- `/research` — gather product + tech context before authoring
