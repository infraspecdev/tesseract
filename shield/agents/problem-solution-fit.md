---
name: problem-solution-fit
description: Grade PM2 — does the proposed approach actually solve the stated problem, or is it a solution looking for a problem? Dispatched by `/plan-review`, `/research`, and standalone PM workflows.
persona: product-manager
model: inherit
outputs:
  - review_detailed    # dispatcher (plan-review / review / prd-review / research) supplies review_type and agent slug
---

# Problem-Solution Fit (PM2)

## Description

Grade ONE PM dimension: traceability from the stated problem to the proposed solution.
Return a single-check JSON block — no prose.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM2 | Problem-solution fit | Critical | The proposed approach is traceable to the stated problem: the problem statement and the solution share at least one explicit causal connection (e.g., "users wait 10s; solution caches result"). A solution that introduces capabilities unrelated to the problem (or where the problem section is missing) fails. Watch for solution-first ordering as a red flag. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM2",
  "name": "Problem-solution fit",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Critical",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
