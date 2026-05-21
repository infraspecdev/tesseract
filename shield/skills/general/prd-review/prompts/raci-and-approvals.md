---
name: raci-and-approvals
---

# RACI & Approvals — PRD Dim 7

## Description

Grade the PRD's header + RACI/approvals content against the four dim-7 evaluation points.
Dispatched skill-internal by `/prd-review` to a general-purpose Agent for both `standard` and
`lean` PRDs.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean` (dim 7 is graded in both)

## Checks (with severity)

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 7a | Named PRD owner | Critical | A specific human is named as PRD/feature owner (full name; "PM" or "TBD" or an empty field fails). |
| 7b | Named decision-maker for ambiguity | Important | A specific person (often the PM or a named exec) is identified as the tie-breaker for scope/priority calls. Implicit "PM decides" without naming the person fails. |
| 7c | Sign-off path for Legal / Security / Support | Important | Each applicable function has a named approver, even if the value is "N/A — confirmed by X". "TBD" or empty fails. For features clearly not touching one of these surfaces, "N/A — <reason>" with a named confirmer is acceptable. |
| 7d | Status / last-updated in header | Warning | Header (table or block) carries a Status value (Draft / In Review / Approved / etc.) AND a last-updated date. Either missing fails. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause

Dim 7 is graded for every PRD type — no N/A path at the dim level. Individual eval points
may use "N/A — confirmed by <name>" only for 7c when the function is genuinely out of scope
(e.g., no Legal involvement for a purely internal infra change).

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 7,
  "name": "RACI & approvals",
  "grade": "A|B|C|D|F",
  "evaluation_points": [
    {
      "id": "7a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "7b", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "7c", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "7d", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

The top-level `grade` averages the four eval-point numeric values (A=4..F=0) and rounds per
`scoring.md`: 3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
