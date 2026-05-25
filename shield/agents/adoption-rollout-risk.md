---
name: adoption-rollout-risk
description: Grade PM7 — what could block adoption (migration pain, learning curve, organizational resistance, communication gaps)? Dispatched by `/plan-review`, `/research`, and standalone PM workflows.
persona: product-manager
model: inherit
outputs:
  - review_detailed    # dispatcher (plan-review / review / prd-review / research) supplies review_type and agent slug
---

# Adoption & Rollout Risk (PM7)

## Description

Grade ONE PM dimension: does the doc surface risks that could block adoption AFTER the work
ships? Return a single-check JSON block — no prose.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM7 | Adoption & rollout risk | Important | The doc names at least one concrete adoption risk: migration pain, learning curve, organizational resistance, dependency on partner-team buy-in, training cost, change-management. "Users will love it" without surfacing any adoption friction fails. A B grade is allowed when risks are named but mitigations are absent. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM7",
  "name": "Adoption & rollout risk",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Important",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
