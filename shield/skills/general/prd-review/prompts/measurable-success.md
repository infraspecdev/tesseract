---
name: measurable-success
---

# Measurable Success — PRD Dim 3

## Description

Grade the PRD's Success Metrics content against the four dim-3 evaluation points. Dispatched
skill-internal by `/prd-review` to a general-purpose Agent for both `standard` and `lean` PRDs.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean` (dim 3 is graded in both)

## Checks (with severity)

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 3a | Metrics have numeric thresholds (not "improve X") | Critical | Every named metric carries a concrete number, percentage, threshold, or time-bound target. Vague "improve X", "reduce Y", "fewer tickets" fails. |
| 3b | Both leading AND lagging metrics present | Critical | ≥1 leading indicator (click, open, signup, attempt, in-flight count) AND ≥1 lagging indicator (retention, revenue, NPS, ticket volume after 30d). A single mid-funnel KPI does not satisfy both. |
| 3c | Counter-metric defined (prevents gaming) | Important | An explicit metric guarding against degradation of an adjacent surface (e.g., share-rate AND no-rise in spam reports; signup-conversion AND no-drop in 30d retention). |
| 3d | Dashboard plan or "what we'll track on Monday" specified | Warning | Names the dashboard, tool, owner, or cadence for monitoring (Datadog board, weekly review, named dashboard URL, daily standup metric). Vague "we'll track this" fails. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause

Dim 3 is graded for every PRD type — no N/A path. If the PRD has no metrics section, grade
3a-3d as F.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 3,
  "name": "Measurable success",
  "grade": "A|B|C|D|F",
  "evaluation_points": [
    {
      "id": "3a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "3b", "grade": "...", "severity": "Critical",  "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "3c", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "3d", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

The top-level `grade` averages the four eval-point numeric values (A=4..F=0) and rounds per
`scoring.md`: 3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
