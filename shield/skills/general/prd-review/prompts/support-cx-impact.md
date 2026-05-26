---
name: support-cx-impact
---

# Support / CX Impact — PRD Dim 10

## Description

Grade the PRD's Support / CX content against the four dim-10 evaluation points. Dispatched
skill-internal by `/prd-review` to a general-purpose Agent. Dim 10 is graded for `standard`
PRDs and treated as `informational` for `lean` PRDs per the rubric's lean-mode exemption.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean`

## Lean-mode exemption (handle FIRST)

If `prd_type == "lean"`, return immediately with grade `informational` and an empty
`evaluation_points` array — do NOT grade. Lean PRDs are structurally exempt from dim 10 per
`rubric.md`'s "Dimension states by PRD type" table.

## Checks (with severity) — standard PRDs only

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 10a | Day-1 ticket owner named | Critical | A named team or queue (and ideally a named human lead) receives day-1 tickets. "Support will handle it" without a named queue or owner fails. |
| 10b | Runbook or escalation path | Important | A linked or described runbook AND a named escalation contact (or rotation) for technical issues. Either alone partially satisfies. |
| 10c | Sales enablement (talking points for sales/CS) | Warning | A talking-points artifact, one-pager, or FAQ is referenced with a named owner. "We'll prepare talking points" fails. |
| 10d | Training plan for support team | Warning | A named training session, recorded walkthrough, or live enablement plan with a date or pre-GA milestone. Silence fails. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause — N/A for internal-only features (standard PRDs)

For features explicitly internal-only (no customer-facing surface, no external support
implications), grade the dim as `N/A` with a non-empty `na_reasoning` field quoting the
bounding evidence. Bare N/A is not allowed.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 10,
  "name": "Support / CX impact",
  "grade": "A|B|C|D|F|N/A|informational",
  "na_reasoning": "<required if grade is N/A; otherwise omit or null>",
  "evaluation_points": [
    {
      "id": "10a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "10b", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "10c", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "10d", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

When grade is `informational` or `N/A`, omit `evaluation_points` (or return an empty array).
Otherwise the top-level `grade` averages the four numeric values (A=4..F=0) and rounds per
`scoring.md`: 3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
