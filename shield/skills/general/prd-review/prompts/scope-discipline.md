---
name: scope-discipline
---

# Scope Discipline — PRD Dim 2

## Description

Grade the PRD's Non-Goals / Out-of-Scope content against the three dim-2 evaluation points.
Apply the N/A exception clause for single-purpose internal engineering tools where scope is
entirely bounded by the problem statement. Dispatched skill-internal by `/prd-review` to a
general-purpose Agent for both `standard` and `lean` PRDs.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean` (dim 2 is graded in both)

## Checks (with severity)

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 2a | Explicit "Out of Scope" / "Non-Goals" / "No-gos" section present | Critical | A dedicated section by that name (or equivalent) exists and lists ≥1 item. A "Goals" section alone does not satisfy 2a. |
| 2b | Each out-of-scope item has one-line rationale explaining WHY excluded now | Critical | Every item under 2a's section is accompanied by a one-line reason (deferred, different threat model, separate epic, deadline pressure, etc.). A bare list satisfies 2a but fails 2b. |
| 2c | Scope creep risks acknowledged | Warning | Explicit callout naming a likely scope-creep request and the decision authority for accepting it. Absent risks-section coverage of scope creep fails. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause — N/A for single-purpose internal tools

If the PRD is a single-purpose internal engineering tool (cron job, backfill script, infra-only
change, dependency upgrade) where the problem statement entirely bounds the scope and there is
nothing meaningful to de-scope, grade the dim as `N/A` with a non-empty `na_reasoning` field
quoting or paraphrasing the bounding constraint. Do NOT flag 2a/2b absence as a gap in that case.
Bare N/A (no reasoning) is not allowed — it grades F per `rubric.md`.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 2,
  "name": "Scope boundaries",
  "grade": "A|B|C|D|F|N/A",
  "na_reasoning": "<required if grade is N/A; otherwise omit or null>",
  "evaluation_points": [
    {
      "id": "2a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "2b", "grade": "...", "severity": "Critical", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "2c", "grade": "...", "severity": "Warning",  "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

When grade is N/A, omit `evaluation_points` (or return an empty array). Otherwise the top-level
`grade` averages the three numeric values (A=4..F=0) and rounds per `scoring.md`:
3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
