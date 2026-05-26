---
name: why-now-cost-of-inaction
---

# Why Now & Cost of Inaction — PRD Dim 11

## Description

Grade the PRD's Why-Now and Cost-of-Inaction content against the three dim-11 evaluation
points. Dispatched skill-internal by `/prd-review` to a general-purpose Agent for both
`standard` and `lean` PRDs.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean` (dim 11 is graded in both)

## Checks (with severity)

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 11a | "Why now" articulated (regulatory, market, competitive, internal urgency) | Critical | A concrete triggering event is named: regulatory deadline, customer contract SLA, competitive launch, internal incident, expiring opportunity, or named external pressure. "We should do this" or "it's a priority" fails. |
| 11b | Cost-of-inaction quantified (what happens if we wait) | Important | The PRD quantifies what happens if delivery slips: $ ARR at risk, # of customers affected, eng-hours of continuing toil, churn signal, missed-deadline penalty. Vague "we'd fall behind" fails. |
| 11c | Sequencing rationale (why this before X) | Warning | Explicit reasoning for why this work precedes a named adjacent initiative (compliance dependency, blocker for downstream effort, capacity window). Silence fails. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause

Dim 11 is graded for every PRD type — no N/A path. If the PRD has no urgency framing at all,
grade 11a-11c as F.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 11,
  "name": "Why now & cost-of-inaction",
  "grade": "A|B|C|D|F",
  "evaluation_points": [
    {
      "id": "11a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "11b", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "11c", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

The top-level `grade` averages the three numeric values (A=4..F=0) and rounds per `scoring.md`:
3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
