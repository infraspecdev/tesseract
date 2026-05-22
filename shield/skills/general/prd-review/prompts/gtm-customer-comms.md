---
name: gtm-customer-comms
---

# GTM / Customer Comms — PRD Dim 9

## Description

Grade the PRD's Go-To-Market and customer-communications content against the four dim-9
evaluation points. Dispatched skill-internal by `/prd-review` to a general-purpose Agent.
Dim 9 is graded for `standard` PRDs and treated as `informational` for `lean` PRDs per the
rubric's lean-mode exemption.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean`

## Lean-mode exemption (handle FIRST)

If `prd_type == "lean"`, return immediately with grade `informational` and an empty
`evaluation_points` array — do NOT grade. Lean PRDs are structurally exempt from dim 9 per
`rubric.md`'s "Dimension states by PRD type" table.

## Checks (with severity) — standard PRDs only

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 9a | Pricing / packaging implications addressed | Important | The PRD names the tier/SKU the feature lives in, any price change, and the GTM decision about packaging (bundled, add-on, no change). Silence fails. |
| 9b | In-app messaging / release notes plan | Important | A concrete plan for in-app announcement and release notes is documented (owner, draft cadence, channel). "We'll write release notes" fails. |
| 9c | CS / sales enablement (who tells customers) | Warning | CS and/or Sales enablement is documented: runbook link, named enablement owner, training/one-pager artifact. Silence fails. |
| 9d | Beta / early-access plan (if applicable) | Warning | A beta cohort is named (design partners, internal cohort), with an explicit feedback loop and graduation criterion. Internal-only features may grade `N/A` with reasoning. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause — N/A for internal-only features (standard PRDs)

For features explicitly internal-only (no customer-facing surface), grade the dim as `N/A`
with a non-empty `na_reasoning` field quoting the bounding evidence. Bare N/A is not allowed.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 9,
  "name": "GTM / customer-comms",
  "grade": "A|B|C|D|F|N/A|informational",
  "na_reasoning": "<required if grade is N/A; otherwise omit or null>",
  "evaluation_points": [
    {
      "id": "9a",
      "grade": "A|B|C|D|F",
      "severity": "Important",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "9b", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "9c", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "9d", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

When grade is `informational` or `N/A`, omit `evaluation_points` (or return an empty array).
Otherwise the top-level `grade` averages the four numeric values (A=4..F=0) and rounds per
`scoring.md`: 3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
