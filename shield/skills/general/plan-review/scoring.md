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

**Persona Weights:** the canonical table lives in `shield/scripts/compute_plan_verdict.py`
(`WEIGHTS`). It is the single source of truth — `dimensions.md` and this file reference it
rather than restating values. For human reference, the current weights are:

| Persona (subagent slug) | Weight | Role |
|---------|--------|------|
| `architect` | 1.0 | Core |
| `security-engineer` | 1.0 | Core |
| `dx-engineer` | 1.0 | Core |
| `platform-engineer` | 1.0 | Core |
| `backend-engineer` | 1.0 | Core |
| `finops-analyst` | 0.7 | Supporting |
| `agile-coach` | 0.7 | Supporting |
| `sre` | 0.7 | Supporting |
| `product-manager` | 0.7 | Supporting (applied to the grade rolled up from PM1-PM10) |

**Formula:**

```
composite = sum(persona_numeric_grade * weight) / sum(activated_weights)
```

Only activated personas contribute to the composite. The denominator is the sum of weights
for personas that actually ran — not all nine.

## Verdict — composite + P0-gate

**Do not compute the verdict by hand.** Feed the aggregated persona grades and the classified
findings to `shield/scripts/compute_plan_verdict.py`; it returns the composite, the P0 count,
and the verdict string. The SKILL.md scoring step invokes it.

The composite alone can hide a fatal gap (the "averaging problem"): enough strong personas can
drown out one F on a Critical dimension — and plan-review makes this worse by first averaging
the ten PM dims into one grade, then weighting that aggregate at only 0.7. **P0 presence GATES
the verdict.**

| Condition | Verdict |
|----------------|---------|
| Composite < 1.5 | **Not Ready** |
| Composite 1.5 – 2.4 | **Needs Work** |
| Composite ≥ 2.5 AND any P0 present | **Needs Work** (composite is informational; the P0 floor binds) |
| Composite ≥ 2.5 AND zero P0s | **Ready** |

**Verdict line in `summary.md`** (verbatim from the script):
- With P0s: `Needs Work (composite 3.61, blocked by 1 P0)`
- Clean: `Ready (composite 3.61)`

This is aligned with `/prd-review`'s P0-gate (`prd-review/scoring.md`) — same averaging-problem
guard, same gate semantics.

## Priority Classification

Recommendations are classified by the grade and severity of the evaluation point that triggered them:

| Priority | Criteria | Meaning |
|----------|----------|---------|
| P0 (High) | Grade D or F on a **Critical** severity evaluation point | Blocks sprint planning. Must fix before proceeding. |
| P1 (Medium) | Grade C-D on an **Important** severity point | Should fix for plan quality. |
| P2 (Low) | Grade C on a **Warning** severity point, or minor gaps on B-graded points | Nice to have. |
