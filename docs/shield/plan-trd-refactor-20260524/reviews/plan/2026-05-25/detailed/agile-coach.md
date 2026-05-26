# Agile Coach — Detailed Findings

> Back to [summary](../summary.md)

## Agile Coach Review (Grade: A-)

| # | Evaluation Point | Grade | Notes |
|---|-----------------|-------|-------|
| AC1 | Story sizing | A | 12 stories across 5 epics, each story is a clear, atomic deliverable. None are multi-week; none are trivial sub-tasks. EPIC-3-S2 is the largest (14 negative fixtures) but is appropriately scoped as one cohesive deliverable. |
| AC2 | Story independence | A- | M1 stories can largely run in parallel (EPIC-1-S1, EPIC-2-S1, EPIC-3-S1 are independent docs/schema/fixture tasks). EPIC-1-S2 depends implicitly on EPIC-1-S1's slug allow-list; EPIC-2-S2 depends on EPIC-2-S1; EPIC-3-S2 depends on EPIC-3-S1's positive fixture. These intra-milestone deps could be explicit but are inferable from content. |
| AC3 | Dependency ordering | A | Milestones have an explicit DAG: `M1 → M2 → M3` via `depends_on` in `sidecar.milestones[]`. No cycles. EPIC-3-S3 explicitly orders RED before GREEN. Story sequencing within M1 is logical (template → emit → re-run guard; schema → populate; fixtures → wire). |
| AC4 | Context completeness | A | Every story has a "why" paragraph in `description`. Examples: EPIC-2-S1 explains "preserve back-compat (missing field is ignored)"; EPIC-5-S1 explains "Countermeasure for undead-doc drift"; EPIC-1-S3 explains the deterministic re-run policy and "no migration." |
| AC5 | Requirements clarity | A | Requirements are specific and measurable. Examples: "exactly 14 entries" in slug list (EPIC-1-S1 AC2), "40-char hex sha" (EPIC-5-S1 AC2), "> 80 characters of consecutive verbatim overlap" (EPIC-4-S2 task), ">20-line code block" threshold (EPIC-5-S2). |
| AC6 | Implementation step quality | A- | Tasks cite exact files, exact field names, and exact thresholds. Minor gap: EPIC-4-S3 says "Update the relevant adapter logic" without naming the adapter files for each tool (just the directory). |
| AC7 | Acceptance criteria testability | A | Every AC is testable. Examples: "exit code 0" (EPIC-3-S1), "reports that section by slug as a Critical finding" (EPIC-4-S1), "40-char hex sha" (EPIC-5-S1). No vagueness. |
| AC8 | Sprint-readiness | A | Each story declares `"status": "ready"`. File paths, schemas, thresholds, and named errors are all pre-decided. A developer could pick up any story without a planning meeting. |
| AC9 | Estimation feasibility | A- | Detail is sufficient for confident estimation. EPIC-3-S2 (14 missing-section fixtures + drift + vague-TBD) is the largest unit of work and could be split for tighter sizing. |
| AC10 | Definition of Done alignment | B+ | DoD is implied: code change + eval fixture + RED→GREEN paper trail (CLAUDE.md mandate). No explicit mention of code review, deploy-to-staging, or user-facing CHANGELOG. |
| AC13 | Milestone coverage | A | Every milestone has covering stories: M1 = 8, M2 = 3, M3 = 2. No milestone is empty. |
| AC14 | Milestone reference integrity | A | Every story's `milestone_id` is `M1`, `M2`, or `M3` — all match `sidecar.milestones[].id`. No dangling references. |
| AC15 | Milestone exit criteria testability | A | All exit criteria are testable. |
| AC16 | Milestone DAG integrity | A | DAG is `M1 → M2 → M3`. Linear chain, no cycles. |

**Key Finding:** Sprint-ready plan — every story has crisp file targets, exact thresholds, named errors, and testable ACs; the milestone DAG and reference integrity are clean; the only meaningful gap is that the largest story (EPIC-3-S2) could be split for finer estimation, and DoD's code-review/changelog rituals are implicit.

### Recommendations

| Priority | Point | Recommendation |
|----------|-------|---------------|
| P2 | AC9 | Split EPIC-3-S2 into two stories: (a) "Build negative-fixture generator + 14 missing-section fixtures" and (b) "Author drift-by-addition + vague-TBD fixtures." |
| P2 | AC6 | In EPIC-4-S3, name the adapter file per tool instead of "Update the relevant adapter logic." |
| P2 | AC10 | Add one cross-cutting AC requiring a CHANGELOG entry / migration note documenting the cutover. |
| P2 | AC2 | Make intra-milestone story ordering explicit (e.g., EPIC-1-S2 depends on EPIC-1-S1 slug list; EPIC-3-S2 depends on EPIC-3-S1 positive fixture). |
