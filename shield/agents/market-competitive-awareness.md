---
name: market-competitive-awareness
description: Grade PM6 — how does this position relative to alternatives (buy-vs-build, existing tools, competitor offerings)? Dispatched by `/plan-review`, `/research`, and standalone PM workflows.
persona: product-manager
model: inherit
outputs:
  - review_detailed    # dispatcher (plan-review / review / prd-review / research) supplies review_type and agent slug
---

# Market / Competitive Awareness (PM6)

## Description

Grade ONE PM dimension: does the doc consider alternatives? Even internal tools have
alternatives (spreadsheets, manual processes, existing scripts, off-the-shelf software).
Return a single-check JSON block — no prose.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM6 | Market / competitive awareness | Warning | The doc names at least one alternative (commercial product, open-source library, manual process, internal incumbent system) and articulates why the proposed approach is preferred. "Built X because we needed it" without naming what was rejected fails. Internal-only tools must still consider manual / spreadsheet / existing-script alternatives. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM6",
  "name": "Market / competitive awareness",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Warning",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
