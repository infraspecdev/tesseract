---
name: prd-review
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Run multi-persona PRD review against a 13-dimension rubric. Produces scored summary with severity-tiered gaps and an enhanced PRD with suggested fixes.
outputs:
  - review_summary           # review_type=prd
  - review_enhanced          # review_type=prd
  - review_detailed          # review_type=prd, multiple reviewer personas
  - review_summary_html
  - review_enhanced_html
  - review_detailed_html
  - source_prd               # immutable snapshot of input PRD
  - review_comments_json     # canonical machine-readable gap export
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

## Paths

This command writes the following registry-tracked paths (see `shield/schema/output-paths.yaml`). All resolve under `{review_dir}` = `{output_dir}/{feature}/reviews/prd/{date}{_counter}`:

| Registry key | Resolved path |
|---|---|
| `review_summary` | `{review_dir}/summary.md` |
| `review_enhanced` | `{review_dir}/enhanced-prd.md` |
| `review_detailed` (per persona) | `{review_dir}/detailed/{agent}.md` |
| `review_summary_html` | `{output_dir}/{feature}/outputs/reviews/prd/{date}{_counter}/summary.html` |
| `review_enhanced_html` | `{output_dir}/{feature}/outputs/reviews/prd/{date}{_counter}/enhanced-prd.html` |
| `review_detailed_html` (per persona) | `{output_dir}/{feature}/outputs/reviews/prd/{date}{_counter}/detailed/{agent}.html` |
| `source_prd` | `{review_dir}/source-prd.md` (immutable snapshot of the input PRD) |
| `review_comments_json` | `{review_dir}/review-comments.json` (machine-readable gap export) |

Each dispatched reviewer subagent writes its own `detailed/<persona>.md` — that file is also declared by the reviewer subagent itself (matches `/review` and `/plan-review` convention of orchestrator + subagent both declaring the per-agent output).

### Resolving the counter

Before writing, list `{output_dir}/{feature}/reviews/prd/` for entries matching today's ISO date. If `{date}/` does not exist, use `_counter=""`. Otherwise, find the highest `{date}_<N>/` (with `<N>` starting at 2 for the second same-day run) and use `_counter="_<N+1>"`. Reviews never overwrite prior runs — they always create a new dated folder.

## What it does

1. **Classifies** the input as local file / URL / paste
2. **Resolves URLs** via runtime MCP discovery (Notion MCP if present for `notion.so/*`, Atlassian MCP for `*.atlassian.net/wiki/*`, etc.) with WebFetch fallback and universal paste fallback
3. **Snapshots** the source to `{review_dir}/source-prd.md` (immutable)
4. **Detects PRD type** (lean vs standard) and confirms with user
5. **Dispatches 13 reviewer invocations** in parallel per `dimensions.md`: 9 PM dim prompts via `general-purpose` Agents (`problem-clarity`, `scope-discipline`, `measurable-success`, `raci-and-approvals`, `legal-privacy-compliance`, `gtm-customer-comms`, `support-cx-impact`, `why-now-cost-of-inaction`, `risks-and-assumptions`) + 4 legacy persona dispatches (Agile-coach `shield:agile-coach`, Tech-lead `shield:architect` for dims 5+6, DX `shield:dx-engineer`, Cost `shield:finops-analyst`)
6. **Aggregates** grades into a composite verdict (A-F per dimension → per-persona → weighted composite); applies P0-gate
7. **Writes output artifacts** under `{review_dir}` (with `review_type=prd`):
   - `{review_summary}` = `{review_dir}/summary.md` — scored gap analysis
   - `{review_dir}/source-prd.md` — verbatim source snapshot (side-artifact)
   - `{review_enhanced}` = `{review_dir}/enhanced-prd.md` — P0/P1 inline annotations + P2 comments
   - `{review_dir}/review-comments.json` — canonical machine-readable gap export (side-artifact)
   - `{review_dir}/detailed/<persona>.md` × 5 — per-reviewer detailed reports (each subagent writes `review_detailed`)
8. **Renders** `{review_summary_html}` and `{review_enhanced_html}` under `{output_dir}/{feature}/outputs/reviews/prd/{date}{_counter}/`
9. **Updates** `manifest.json` and `index.html` dashboard
10. **Offers apply options** — use enhanced as canonical PRD (copies to `{prd}`) / convert back to original format / skip

## Reference

Full behavior in `shield/skills/general/prd-review/SKILL.md`.

## See also

- `/plan` — generate a technical plan from a PRD
- `/plan-review` — review a generated plan
- `/research` — gather product + tech context before authoring
