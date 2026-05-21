---
name: risks-and-assumptions
---

# Risks & Assumptions — PRD Dim 12

## Description

Grade the PRD's Risks and Assumptions content against the three dim-12 evaluation points.
Dispatched skill-internal by `/prd-review` to a general-purpose Agent for both `standard` and
`lean` PRDs.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean` (dim 12 is graded in both)

## Checks (with severity)

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 12a | Risks enumerated WITH mitigations and owners | Critical | Each risk in the risks section has BOTH a mitigation (concrete action / safeguard) AND a named owner. A risks table without mitigation columns or with empty mitigation cells fails. Risks listed in prose without owners fails. |
| 12b | Validated vs unvalidated assumptions distinguished | Important | The PRD explicitly distinguishes assumptions that are validated (with evidence) from those that are unvalidated. A column, label, or callout that separates the two satisfies. Implicit / unmarked fails. |
| 12c | Counter-arguments / dissenting views noted (if any exist) | Warning | At least one dissenting view, alternative approach considered, or stakeholder objection is documented. A "Decision log" or "Alternatives considered" section satisfies. Silence fails. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause

Dim 12 is graded for every PRD type — no N/A path. A PRD with literally no risks listed grades
12a F, 12b F, 12c F.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 12,
  "name": "Risks & assumptions",
  "grade": "A|B|C|D|F",
  "evaluation_points": [
    {
      "id": "12a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "12b", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "12c", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

The top-level `grade` averages the three numeric values (A=4..F=0) and rounds per `scoring.md`:
3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
