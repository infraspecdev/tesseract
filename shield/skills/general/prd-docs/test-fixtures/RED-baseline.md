# RED Baseline — prd-docs skill absent

> **Evaluation date:** 2026-05-11
> **Method:** Simulated persona evaluation — what a generic LLM session does WITHOUT the prd-docs skill loaded.

---

## Scenario 1: Author from scratch — `/prd "Add gift-card support"`

### What a generic LLM produces (baseline)

Without the prd-docs skill, a generic "write me a PRD" prompt to Claude produces:
- Inconsistent structure — may use 5 sections (Problem, Solution, Requirements, Success, Risks) or no standard scaffold at all
- No Section numbering or 17-section problem-first ordering
- Success metrics are typically vague ("increase revenue") with no numeric threshold or counter-metric
- No prd.meta.json output — the artifact concept does not exist
- No prd.html output — only markdown is produced
- No story-coverage scaffolding — stories are written ad hoc without persona × goal coverage analysis
- No lean vs. standard type selection — just one generic format
- Output goes to wherever the user asks (no `{output_dir}/{feature}/prd/{N}-{slug}/` path enforcement)

### Gaps vs. expected
| Gap | Severity |
|---|---|
| No 17-section problem-first scaffold | P0 — users get random structure |
| No prd.meta.json | P0 — downstream /plan and /prd-review can't read metadata |
| No prd.html | P1 — no rendered artifact |
| No story-coverage scaffolding between Sections 4 and 6 | P1 — poor dim 4 grades downstream |
| No type selection (standard vs. lean) | P1 — every PRD is the same length regardless of feature complexity |
| No path enforcement | P1 — artifacts go to random locations |
| No custom-template merging | P2 — teams with custom templates can't use Shield |

---

## Scenario 2: With research transcript — `/prd "Add gift-card support"` (transcript present)

### What a generic LLM produces (baseline)

Without the prd-docs skill, there is no mechanism to detect a prior `/research` transcript in `{output_dir}/{feature}/research/`. The LLM would:
- Not look for any research transcript in the feature folder
- Not pre-populate Sections 2, 3, or 10 from research
- Not add `<!-- pre-populated from research -->` markers
- Produce the same generic structure as Scenario 1; research is simply ignored

### Gaps vs. expected
| Gap | Severity |
|---|---|
| No research transcript detection | P1 — users must re-enter all context already captured by /research |
| No pre-population of Problem, Personas, Dependencies | P1 — doubles authoring time; risks drift between research and PRD |
| No `linked_research` field in meta | P2 — bidirectional linkage broken |

---

## Scenario 3: Lean upgrade — `/prd` in feature folder with prior lean PRD

### What a generic LLM produces (baseline)

Without the prd-docs skill, there is no detection of a prior lean PRD in the feature folder. The LLM would:
- Not glob `{output_dir}/{feature}/prd/*/prd.meta.json`
- Not detect `type: "lean"` in any prior meta file
- Not offer the multi-select upgrade flow
- Not create a new run folder `prd/{N+1}-{slug}/`
- Not copy existing lean content forward
- Simply start a new PRD from scratch, overwriting context from the lean PRD

### Gaps vs. expected
| Gap | Severity |
|---|---|
| No prior lean PRD detection | P0 — users lose their lean PRD content in the upgrade flow |
| No multi-select of standard sections to add | P1 — users must identify missing sections themselves |
| No new run folder + copy-forward | P1 — no versioning of upgrade; original lean PRD not preserved |

---

## RED Summary

| Scenario | Issues caught | Issues missed | Severity accuracy |
|---|---|---|---|
| New from scratch | 0 / 7 skill-required behaviors | All 7 gaps | N/A — baseline produces wrong structure entirely |
| With research transcript | 0 / 3 skill-required behaviors | All 3 gaps | N/A |
| Lean upgrade | 0 / 3 skill-required behaviors | All 3 gaps | N/A |

**Conclusion:** Without the prd-docs skill, all three authoring scenarios produce structurally incorrect output with missing artifacts (prd.meta.json, prd.html), no type selection, no research pre-population, no lean upgrade detection, and no story-coverage scaffolding. GREEN test will verify the skill closes all these gaps.
