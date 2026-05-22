---
name: scope-discipline-of-plan
description: Grade PM3 — is this an MVP or a kitchen sink? What can be cut without losing core value? DISTINCT from the PRD-Review dim 2 scope-discipline prompt (which grades a PRD's Non-Goals section). Dispatched by `/plan-review`, `/research`, and standalone PM workflows.
persona: product-manager
model: inherit
outputs:
  - review_detailed    # dispatcher (plan-review / review / prd-review / research) supplies review_type and agent slug
---

# Scope Discipline of Plan (PM3)

## Description

Grade ONE PM dimension: is the proposed plan disciplined (MVP-shaped) or overloaded? Identify
what could be cut without losing core value. This is a PLAN-level scope check — distinct from
the PRD-Review dim 2 prompt that grades a PRD's Non-Goals section structurally. Return a
single-check JSON block — no prose.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM3 | Scope discipline | Important | The plan distinguishes "must have to deliver the stated value" from "could have, deferred", with a defensible MVP cut. Kitchen-sink plans (everything is must-have) fail. Plans without any scope decisions documented fail. A B grade is allowed when the cut is mostly there but one or two items appear scope-creepy. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM3",
  "name": "Scope discipline (plan)",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Important",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
