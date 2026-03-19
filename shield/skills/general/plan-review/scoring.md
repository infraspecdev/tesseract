# Plan Review Scoring Rubric

## Grade Scale

| Grade | Meaning | Numeric |
|-------|---------|---------|
| A | Fully addressed, no concerns | 4 |
| B | Addressed with minor gaps | 3 |
| C | Partially addressed, notable gaps | 2 |
| D | Barely addressed, significant issues | 1 |
| F | Missing or critically flawed | 0 |

## Per-Persona Grade

Average all evaluation point grades for a persona, then round to the nearest letter:

| Average Range | Letter Grade |
|---------------|-------------|
| 3.5 - 4.0 | A |
| 2.5 - 3.4 | B |
| 1.5 - 2.4 | C |
| 0.5 - 1.4 | D |
| 0.0 - 0.4 | F |

## Composite Readiness Score

Weighted average of all activated persona grades.

**Persona Weights:**

| Persona | Weight | Role |
|---------|--------|------|
| Cloud Architect | 1.0 | Core |
| Security Engineer | 1.0 | Core |
| DX Engineer | 1.0 | Core |
| Cost/FinOps | 0.7 | Supporting |
| Agile Coach | 0.7 | Supporting |
| Operations | 0.7 | Supporting |
| Product Manager | 0.7 | Supporting |

**Formula:**

```
composite = sum(persona_numeric_grade * weight) / sum(activated_weights)
```

Only activated personas contribute to the composite. The denominator is the sum of weights for personas that actually ran — not all 7.

## Verdict Thresholds

| Composite Range | Verdict |
|----------------|---------|
| A - B (>= 2.5) | Ready |
| B - C (1.5 - 2.4) | Needs Work |
| D - F (< 1.5) | Not Ready |

## Priority Classification

Recommendations are classified by the grade and severity of the evaluation point that triggered them:

| Priority | Criteria | Meaning |
|----------|----------|---------|
| P0 (High) | Grade D or F on a **Critical** severity evaluation point | Blocks sprint planning. Must fix before proceeding. |
| P1 (Medium) | Grade C-D on an **Important** severity point | Should fix for plan quality. |
| P2 (Low) | Grade C on a **Warning** severity point, or minor gaps on B-graded points | Nice to have. |
