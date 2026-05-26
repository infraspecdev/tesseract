---
name: problem-clarity
---

# Problem Clarity — PRD Dim 1

## Description

Grade the PRD's Problem Statement, Users/Personas, and Why-Now sections against the four
dim-1 evaluation points. Return a per-check grade, severity, verbatim `evidence_quote`,
`gap`, and `suggestion`. Aggregate to a dim-level letter grade. Dispatched skill-internal
by `/prd-review` to a general-purpose Agent for both `standard` and `lean` PRDs.

## Inputs

- `prd_path` — absolute path to the source-prd.md snapshot
- `prd_type` — `standard` or `lean` (dim 1 is graded in both)

## Checks (with severity)

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 1a | Named user / persona present (not "users") | Critical | Problem Statement or Users section names ≥1 specific persona with role/title (e.g., "Anya Patel, Head of Growth"). Generic "our users", "customers", "admins" fails. |
| 1b | Baseline data (current state, numbers) | Important | ≥1 concrete number describing today's state (% adoption, # incidents, $ at risk, hours lost, ticket volume). Vague "many users" / "frequently" fails. |
| 1c | "Why now" articulated (urgency, opportunity cost) | Warning | Explicit why-now rationale: regulatory deadline, competitive pressure, internal incident, expiring opportunity, contract SLA. Absence or "we should do this" fails. |
| 1d | First-person user evidence or quotes | Warning | ≥1 verbatim user quote OR a directly cited research artifact (interview transcript, NPS verbatim, ticket text, survey free-response). Aggregate references like "customers filed tickets" or "X% of users do Y" count toward 1b, not 1d. PM-authored persona "current pain" summaries do not count. |

Grade each check A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).
Severity is fixed per the rubric — do not infer it from the grade.

## Exception clause

Bare N/A is not allowed for dim 1 — every PRD (standard or lean, including internal tools)
must have a problem statement. If the PRD has no problem content at all, grade 1a-1d as F.

## Output shape (JSON only — no prose, no markdown)

```json
{
  "id": 1,
  "name": "Problem clarity",
  "grade": "A|B|C|D|F",
  "evaluation_points": [
    {
      "id": "1a",
      "grade": "A|B|C|D|F",
      "severity": "Critical",
      "evidence_quote": "<verbatim line from the PRD; empty string only if the section is absent>",
      "gap": "<one sentence, or null if grade A>",
      "suggestion": "<one sentence, or null if grade A>"
    },
    { "id": "1b", "grade": "...", "severity": "Important", "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "1c", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." },
    { "id": "1d", "grade": "...", "severity": "Warning",   "evidence_quote": "...", "gap": "...", "suggestion": "..." }
  ]
}
```

The top-level `grade` averages the four eval-point numeric values (A=4, B=3, C=2, D=1, F=0)
and rounds per `scoring.md`: 3.5-4.0 → A, 2.5-3.4 → B, 1.5-2.4 → C, 0.5-1.4 → D, 0.0-0.4 → F.
`evidence_quote` MUST be a verbatim substring of the PRD; do not paraphrase.
