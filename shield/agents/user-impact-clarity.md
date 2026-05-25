---
name: user-impact-clarity
description: Grade PM1 — does the document name specific users/personas and quantify the impact on them? Dispatched by `/plan-review`, `/research` (Research-Review mode), and any workflow that needs a focused PM user-impact grade.
persona: product-manager
model: inherit
outputs:
  - review_detailed    # dispatcher (plan-review / review / prd-review / research) supplies review_type and agent slug
---

# User Impact Clarity (PM1)

## Description

Grade ONE PM dimension: does the input document make clear WHO benefits from the proposed work,
HOW SPECIFICALLY they benefit, and quantify the impact where possible. Return a single-check
JSON block — no prose, no scorecard.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM1 | User impact clarity | Critical | A specific user / persona / role is named (not "users" or "the team") AND the impact on them is described concretely (what changes, how much, what they could not do before). Numeric magnitude is a plus but not strictly required. Generic "improves UX" or "saves time" without naming who or how much fails. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM1",
  "name": "User impact clarity",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Critical",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
