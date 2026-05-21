# PRD Review Scoring

Aligned with `shield/skills/general/plan-review/scoring.md` — same A-F grade scale and weighted-composite formula, with an added P0-gate on the verdict.

## Grade Scale

| Grade | Meaning | Numeric |
|---|---|---|
| A | Fully addressed, no concerns | 4 |
| B | Addressed with minor gaps | 3 |
| C | Partially addressed, notable gaps | 2 |
| D | Barely addressed, significant issues | 1 |
| F | Missing or critically flawed | 0 |

Plus two non-numeric states:
- **N/A** — excluded from composite (reasoning required; bare N/A grades F)
- **Informational** — excluded from composite (lean-PRD structural exemption)

## Envelope shapes accepted

After the pm-restructure-v0 cutover, the orchestrator (`SKILL.md` Step 5) consumes two
envelope shapes from `/prd-review` dispatch and treats them identically downstream:

- **Per-dim envelope (new — skill-internal PM prompts):** a single dim-block at the top level:
  `{ "id": <int>, "name": "...", "grade": "A|B|C|D|F|N/A|informational", "na_reasoning": "...",
  "evaluation_points": [...] }`. The 9 PM prompts in `prompts/` return this shape.
- **Per-persona envelope (legacy — agile-coach, architect, dx-engineer, finops-analyst):**
  `{ "persona": "...", "persona_grade": "A|B|C|D|F", "dimensions": [<dim-block>, ...],
  "anti_patterns": [...] }`. Unwrap `dimensions[]` to obtain dim-blocks.

Both produce the same dim-block list for the scoring math below. `anti_patterns[]` from the
DX persona is routed to `summary.md` separately and is not used in numeric scoring.

## Per-evaluation-point grade

Each evaluation point in `rubric.md` is graded A-F by the owning persona's reviewer agent
(skill-internal prompt for PM dims, legacy persona for the rest).

## Per-dimension grade

Average all evaluation points within the dimension (numeric values), round to nearest letter:

| Average Range | Letter Grade |
|---|---|
| 3.5 – 4.0 | A |
| 2.5 – 3.4 | B |
| 1.5 – 2.4 | C |
| 0.5 – 1.4 | D |
| 0.0 – 0.4 | F |

N/A or informational dimensions are skipped entirely (not included in the persona's average).

## Per-persona grade

Average that persona's owned dimensions' numeric values, round to letter. Same range table as above.

## Composite readiness score

Weighted average of all activated personas' grades.

**Persona weights for `/prd-review`:**

| Persona | Weight | Role |
|---|---|---|
| `shield:product-manager` | 1.0 | Core |
| `shield:agile-coach` | 1.0 | Core |
| `shield:architect` (tech-lead) | 1.0 | Core |
| `shield:dx-engineer` | 0.7 | Supporting |
| `shield:finops-analyst` | 0.7 | Supporting |

**Formula:**

```
composite = sum(persona_numeric_grade × weight) / sum(activated_weights)
```

Only activated personas contribute. Denominator is the sum of weights for personas that actually ran (typically all 5; configurable via `.shield.json` `prd_review_personas`).

## Priority classification

Recommendations are classified by the evaluation point that triggered them:

| Priority | Triggered by | Meaning |
|---|---|---|
| P0 (High) | Grade D or F on a **Critical** severity evaluation point | Blocks downstream `/plan`. Must fix before proceeding. |
| P1 (Medium) | Grade C-D on an **Important** severity eval point | Should fix for PRD quality. |
| P2 (Low) | Grade C on a **Warning** severity eval point, or minor gaps on B-graded points | Nice to have. |

## Verdict logic — composite + P0 gate

The composite score alone can hide a fatal gap (the "averaging problem"): enough strong dimensions can drown out one F on a critical one. P0 presence GATES the verdict.

| Condition | Verdict |
|---|---|
| Composite < 1.5 | **Not Ready** |
| Composite 1.5 – 2.4 | **Needs Work** |
| Composite ≥ 2.5 AND any P0 present | **Needs Work** (composite is informational; P0 floor binds) |
| Composite ≥ 2.5 AND zero P0s | **Ready** |

**Header line in `summary.md`:**
- With P0s: `**Verdict:** Needs Work (composite 3.3, blocked by 4 P0s)`
- Clean: `**Verdict:** Ready (composite 3.4)`

This makes the P0 gate visible — readers immediately see why a high composite isn't enough.

## Composite computation example (standard PRD)

```
PM reviewer        grade B (3.0), weight 1.0
Agile-coach        grade C (2.0), weight 1.0
Tech-lead          grade B (3.0), weight 1.0
DX reviewer        grade A (4.0), weight 0.7
Cost reviewer      grade B (3.0), weight 0.7

composite = (3.0×1.0 + 2.0×1.0 + 3.0×1.0 + 4.0×0.7 + 3.0×0.7) / (1.0 + 1.0 + 1.0 + 0.7 + 0.7)
          = (3.0 + 2.0 + 3.0 + 2.8 + 2.1) / 4.4
          = 12.9 / 4.4
          = 2.93 → B

If 2 P0s exist (e.g., dim 9 GTM=F and dim 7 RACI=F):
  Verdict: Needs Work (composite 2.93, blocked by 2 P0s)
Else:
  Verdict: Ready
```
