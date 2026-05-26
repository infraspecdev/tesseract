---
name: success-metrics-defined
description: Grade PM8 — how will we know this worked? Measurable outcomes defined? Dispatched by `/plan-review`, `/research`, and standalone PM workflows. DISTINCT from PRD-Review dim 3 measurable-success (which grades a PRD's structural metrics section).
persona: product-manager
model: inherit
outputs:
  - review_detailed    # dispatcher (plan-review / review / prd-review / research) supplies review_type and agent slug
---

# Success Metrics Defined (PM8)

## Description

Grade ONE PM dimension: does the doc state HOW we will know the work succeeded after it ships?
This is a plan-level / research-level check — distinct from the PRD-Review dim 3 structural
check on a PRD's metrics section. Return a single-check JSON block — no prose.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM8 | Success metrics | Important | The doc defines at least one measurable outcome (numeric threshold, target percentage, time-bound goal, observable behavioral change) that determines "this worked". Vague "improve X" / "users will be happier" / "support tickets should drop" without a measurement fails. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM8",
  "name": "Success metrics",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Important",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
