---
name: legal-privacy-compliance
---

# Legal / Privacy / Compliance — PRD Dim 8

## Description

Grade the PRD's Legal / Privacy / Compliance content against the four dim-8 evaluation points.
Dispatched skill-internal by `/prd-review` to a general-purpose Agent for both `standard` and
`lean` PRDs.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean` (dim 8 is graded in both)

## Checks (with severity)

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 8a | Data classification specified (PII / payment / public / etc.) | Critical | The PRD explicitly classifies the new or touched data (PII, payment, regulated, public, internal). "Data is sensitive" without taxonomy fails. |
| 8b | PII handling (collection, storage, retention) | Critical | Specifies how PII is collected, where it is stored, encryption posture, and a retention duration. Missing any of (storage, retention) fails. |
| 8c | Regulated-industry sign-off path (if applicable) | Important | When the feature touches HIPAA / PCI / SOC2 / GDPR / CCPA territory, a named approver and the sign-off path are documented. If clearly not applicable, an explicit "N/A — confirmed by <name>" satisfies. |
| 8d | Compliance-driven flows documented (user-initiated deletion per GDPR Art. 17, data subject access, etc.) | Important | Names the compliance-driven user flows (right-to-erasure, data export, consent capture/withdrawal) and how they're implemented. Silence fails. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause — N/A for features that touch no user data

If the PRD describes an internal-only feature with explicitly no PII / no user content / no
regulated data (e.g., a cron job purging server-side opaque session tokens), grade the dim as
`N/A` with a non-empty `na_reasoning` field quoting the bounding evidence. Bare N/A is not
allowed — it grades F per `rubric.md`.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 8,
  "name": "Legal / privacy / compliance",
  "grade": "A|B|C|D|F|N/A",
  "na_reasoning": "<required if grade is N/A; otherwise omit or null>",
  "evaluation_points": [
    {
      "id": "8a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "8b", "grade": "...", "severity": "Critical",  "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "8c", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "8d", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

When grade is N/A, omit `evaluation_points` (or return an empty array). Otherwise the top-level
`grade` averages the four numeric values (A=4..F=0) and rounds per `scoring.md`:
3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
