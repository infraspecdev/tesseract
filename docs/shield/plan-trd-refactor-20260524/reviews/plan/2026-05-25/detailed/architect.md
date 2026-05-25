# Architect — Detailed Findings

> Back to [summary](../summary.md)

## Architect Review (Grade: B)

| # | Evaluation Point | Grade | Notes |
|---|-----------------|-------|-------|
| CA1 | Artifact/component topology | A | The artifact graph is well-formed: `research.md` → `trd.md` (14 sections w/ stable kebab anchors) → `plan.json` (stories with `design_refs[]` pointing at TRD anchors) → `/pm-sync` adapters → PM tools. Anchor scheme (`{#section-id}`) is explicitly defined as the join key. EPIC-1-S1 publishes the slug allow-list as a machine-readable sidecar under `shield/schema/` so eval/review/generator all import from the same source — single source of truth. |
| CA2 | Schema/template growth | B | Schema evolution path is explicit: 1.1 → 1.2 (`design_refs[]`) → 1.3 (`last_aligned_with`), each additive. Gap: the plan does not specify what happens when the 14-section list itself needs to evolve. A `template_version` field on TRD frontmatter would close this. |
| CA3 | Backward compatibility | A | Backward compatibility is rigorously asserted across every schema change. Adapters without link affordance log and continue gracefully. Old `plan-architecture.md` files explicitly preserved. |
| CA4 | Cross-tool / cross-domain reach | B | Multi-tool reach well covered. Multi-domain reach is headline (one TRD, two domains). Gap: "Mixed → annotate per section" is a single sentence with no worked example or fixture. A monorepo with both `*.tf` and `pyproject.toml` is realistic and the plan punts. No mixed-domain positive fixture in EPIC-3-S1. |
| CA5 | Contract/interface design across components | A | Contract surfaces are tight: `design_refs[]` shape fully defined; section anchors use explicit `{#section-id}` kebab-case; slug allow-list machine-readable; LLD placeholder shape precisely specified. Forward-looking contract that lets `/lld` resolve TODOs later without schema change. |
| CA6 | Blast radius / failure-mode isolation | B | Several failure modes explicitly handled and isolated (re-run safety, PM-sync degraded mode, eval gates cutover, undead-doc drift countered). Gaps: (a) stale `design_refs[].anchor_url` when section renamed/deleted between runs — `/plan-review` has no detection; (b) `last_aligned_with` race when working tree is dirty; (c) eval fixture set falling out of sync with live slug allow-list. |
| CA7 | Mechanism choice for each concern | B | Mostly well-reasoned (markdown anchors, eval-as-enforcement, additive schema growth, substring-overlap for duplication detection). Concerns: (a) EPIC-4-S2 "> 80 characters" magic number undefended; (b) EPIC-5-S2 ">20 lines" same; (c) `last_aligned_with` records commit SHA but doesn't capture whether the TRD itself has changed since that SHA — a `trd_sha` content hash would catch post-commit edits. |
| CA8 | Positive ↔ negative fixture parity & template ↔ eval ↔ review consistency | B | Parity mostly enforced. 14 missing-section negatives derived from positive by removing one — right pattern. Slug allow-list imported by generator + eval + review. Gaps: (a) no round-trip integration eval (`/plan` output → `/plan-review` says no Criticals); (b) no positive fixture for mixed-domain or LLD-TODO placeholder shape; (c) **EPIC-3-S3 AC says "13 negatives" — actual count is 14 missing-section + 1 drift + 1 vague-TBD = 16. Off-by-N inconsistency between AC text and fixture inventory in EPIC-3-S2**. |

**Key Finding:** The plan has unusually rigorous artifact-topology design but leaks credibility through small inconsistencies — `plan-architecture.md` still says "13-section" at lines 25, 37, 75; EPIC-3-S3 says "13 negatives" when EPIC-3-S2 enumerates 16; the mixed-domain path is asserted ("Mixed → annotate per section") without a worked example or fixture. Headline architectural choices are sound; gaps are in edge-case completeness.

### Recommendations

| Priority | Point | Recommendation |
|----------|-------|---------------|
| P1 | CA8 | Fix the negative-fixture count inconsistency. `plan.md` EPIC-3-S3 AC says "all 13 negatives fail" but EPIC-3-S2 enumerates 16. Pick a number and propagate. |
| P1 | CA8 | Fix the stale "13-section" references in `plan-architecture.md` (lines 25, 37, 75). Reconcile to 14 everywhere. |
| P1 | CA4 | Add a worked example and at least one eval fixture for the mixed-domain case: (a) `positive-mixed/` fixture, (b) explicit guidance in plan-docs/SKILL.md, (c) detection rule for mixed (both infra and backend markers). |
| P1 | CA6 | Specify stale-anchor detection. Add an AC to EPIC-4-S1: "/plan-review reports any `design_refs[].anchor_url` whose `#section-id` is not present in the linked trd.md as a Critical finding." |
| P2 | CA7 | Defend or parameterize the magic numbers (>80 char overlap, >20 line code block). |
| P2 | CA7 | Consider adding `trd_sha` (content hash) alongside `last_aligned_with` (commit SHA) in EPIC-5-S1. |
| P2 | CA2 | Add a TRD `template_version` field so legitimate template evolution doesn't trigger the drift-by-addition negative. |
| P2 | CA8 | Add a round-trip integration eval: `/plan` output → `/plan-review` asserts no Critical findings. |
