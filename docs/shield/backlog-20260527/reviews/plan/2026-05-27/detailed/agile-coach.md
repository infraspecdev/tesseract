# Agile Coach — Detailed Findings

> Back to [summary](../summary.md)

### Agile Coach Review (Grade: B)

| # | Evaluation Point | Grade | Notes |
|---|-----------------|-------|-------|
| AC1 | Story sizing | A | Ten stories, each a coherent single-sprint unit. Schema+validator, capture, view, remove, status badges, association+suggestion, promotion, reconciliation engine, triggers, evals, release each scoped to days not weeks. None trivial, none multi-week. EPIC-3-S2 (reconciliation engine) is the heaviest but still one focused unit. |
| AC2 | Story independence | B | Good parallelism within M1 (S1 schema unblocks S2/S3/S4; S3 view and S4 remove can proceed in parallel once helper exists). EPIC-3-S3 hard-depends on EPIC-3-S2 (shared engine) and EPIC-3-S1 (transient reference) — correctly sequenced but tightly coupled; that coupling is inherent, not a defect. |
| AC3 | Dependency ordering | A | Milestone chain M1→M2→M3 is explicit and acyclic. Blockers are stated: EPIC-3-S3 "share the reconciliation engine" depends on EPIC-3-S2; promotion (S1) precedes eager prune (S3); EPIC-2-S1 view-badges build on EPIC-1-S3 view (called out: "Pipeline status badges are added in EPIC-2-S1"). No circular deps. |
| AC4 | Context completeness | A | Every story's `description` states why it exists, not just what. E.g. EPIC-1-S2 ties to a corruption-race rationale and explicitly "resolves the PRD-review P1 'capture interface undefined'"; EPIC-2-S1 explains the goal ("show 'prd done, not yet planned' without being removed"). Carried-forward PRD-review items mapped to stories. |
| AC5 | Requirements clarity | B | Mostly specific and measurable: named validator errors (`unknown_kind_enum`, `missing_required_field`, `schema_version_too_new`), explicit field list, atomic temp-then-rename. Weaker spot: EPIC-2-S2 "propose the best match" leaves the matching algorithm undefined (no string-distance/heuristic spec) — deferred to a TODO LLD `epic-suggester`. AC6/AC7 partly compensate but the "best match" criterion is not measurable. |
| AC6 | Implementation step quality | B | Steps say what and mostly how (e.g. "write backlog.json.tmp then rename; on failure remove .tmp", "pydantic + jsonschema, run via uv"). Verification is largely pushed into the AC rather than into the steps themselves; e.g. EPIC-3-S2 steps describe behavior but no in-step verification checkpoint. Solid but not exemplary. |
| AC7 | Acceptance criteria testability | B | Most AC are pass/fail verifiable by a third party (exit 0/non-zero with named error; "killing capture mid-write leaves no corrupted backlog.json"; "second pass is a no-op"). Two soft spots: EPIC-2-S2 "proposes ≥1 feature and ≥1 epic candidate when matches exist" — the "best match" quality isn't asserted; EPIC-3-S3 "before the next /backlog view" is a sequencing claim that's awkward to test deterministically. No vague "performance is good"-style criteria. |
| AC8 | Sprint-readiness | B | M1 and M3 stories are pullable as-is. EPIC-2-S2 carries an open design question (suggestion match algorithm, TODO `/lld epic-suggester`) and PRD §9 flags "Feature/epic discovery cost" as still-open — a dev would need a planning conversation on the matching heuristic before estimating S2 confidently. Everything else is ready. |
| AC9 | Estimation feasibility | B | Eight of ten stories are confidently estimable. EPIC-2-S2 (undefined match heuristic) and EPIC-3-S2 (match-key + drift-tolerance edge space) carry estimation uncertainty until the LLDs land. All LLD design_refs are unresolved `TODO` links — fine for a plan, but they're the exact detail an estimator wants. |
| AC10 | Definition of Done alignment | B | Strong on tests (dedicated EPIC-4-S1 eval story with RED→GREEN, CI wiring, self-contained no-LLM fixtures) and docs (EPIC-4-S2: command + SKILL + CHANGELOG) and release (version bump per CLAUDE.md). Not stated anywhere: code review and deploy/ship-to-staging steps in the DoD. For a plugin-asset repo "staging" maps loosely to the marketplace bump, but review is unmentioned. |
| AC13 | Milestone coverage | A | All three milestones have covering stories. M1: EPIC-1-S1/S2/S3/S4 + EPIC-2-S1 (5). M2: EPIC-2-S2 (1). M3: EPIC-3-S1/S2/S3 + EPIC-4-S1/S2 (5). No empty milestone. |
| AC14 | Milestone reference integrity | A | Every story `milestone_id` is M1, M2, or M3 — all present in `milestones[]`. No null, no dangling reference. `milestones[]` non-empty. |
| AC15 | Milestone exit criteria testability | B | Most exit criteria are testable facts (validator exits 0/non-zero with named error; atomic temp-then-rename; "a prd-only feature is NOT removed"; "second pass is idempotent"). M2's "proposes ≥1 candidate ... using a documented match" leans on an undocumented match (mirrors the EPIC-2-S2 AC5/AC8 gap). M1's "renders ... a research/prd/plan status read from manifest.json" is verifiable. Overall testable with one soft item. |
| AC16 | Milestone DAG integrity | A | Graph: M1→(M2), M2→(M3). Linear, acyclic, fully connected. No cycle, no dangling depends_on (M1 deps [], M2 deps [M1], M3 deps [M2]). |

**Key Finding:** A well-structured, sprint-ready backlog with an acyclic milestone DAG and full coverage; the single recurring weakness is the undefined feature/epic suggestion-matching heuristic (EPIC-2-S2 / M2), which is still an open question and undercuts requirements clarity, sprint-readiness, and estimability for that one story.

#### Story-Level Assessment

| Story | Sizing | Has Context | Has Requirements | Has Steps | Has Criteria | Sprint-Ready? |
|-------|--------|-------------|-----------------|-----------|-------------|--------------|
| EPIC-1-S1 · Schema + validator | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-1-S2 · Capture (user+skill) atomic write | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-1-S3 · /backlog ordered view | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-1-S4 · Manual remove | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-2-S1 · Pipeline status from manifest | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-2-S2 · Feature+epic association + suggestion | OK | Yes | Partial (match heuristic undefined) | Partial | Partial ("best match" not asserted) | No |
| EPIC-3-S1 · Promotion (transient reference) | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-3-S2 · Reconciliation engine | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-3-S3 · Eager + lazy triggers (idempotent) | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-4-S1 · Executable evals (RED→GREEN) | OK | Yes | Yes | Yes | Yes | Yes |
| EPIC-4-S2 · Version bump + docs | OK | Yes | Yes | Yes | Yes | Yes |

#### Milestone-Level Assessment

| Milestone | Has Covering Stories | Exit Criteria Testable | Depends-On Valid |
|-----------|---------------------|------------------------|------------------|
| M1 · Capture + store + view | Yes (5: E1-S1..S4, E2-S1) | Yes | Yes (root, deps []) |
| M2 · Feature + epic association + suggestion | Yes (1: E2-S2) | Partial ("documented match" undefined) | Yes (deps M1) |
| M3 · Promotion + reconciliation | Yes (5: E3-S1..S3, E4-S1, E4-S2) | Yes | Yes (deps M2) |

Note on milestone/epic phase alignment: EPIC-2-S1 carries `milestone_id: M1` while sitting in EPIC-2 ("Association & pipeline status"). This is **intentional and correct**, not a conflict — the story implements the manifest status badge, which M1's outcome explicitly includes ("`/backlog` renders the ordered list ... with per-entry pipeline status from manifest.json"). The epic groups by theme; the milestone groups by ship-phase. They legitimately cross here. No remediation needed.

#### Recommendations

| Priority | Point | Recommendation |
|----------|-------|---------------|
| P1 | AC5 / AC7 / AC8 (EPIC-2-S2) | Define the feature/epic suggestion match heuristic before the story enters a sprint — specify the matching method (e.g. case-insensitive substring + token-overlap ranking on feature/epic names) and add a measurable AC such as "given fixture manifest with feature `auth`, capturing text mentioning 'auth' surfaces `auth` as the top candidate." Resolve the PRD §9 open "Feature/epic discovery cost" question or land the TODO `/lld epic-suggester` so S2 is estimable. |
| P2 | AC15 (M2) | Tighten M2's exit criterion "using a documented match" — point it at the resolved heuristic above and restate as a testable fact, mirroring the M3 exit criteria's precision. |
| P2 | AC10 | Add code-review and ship/staging steps to the implied Definition of Done. EPIC-4-S2 covers version bump + docs + CHANGELOG; add "PR reviewed and merged; marketplace version published" as an explicit DoD line so 'done' is unambiguous across the team. |
| P2 | AC9 | The LLD `design_refs` for EPIC-1-S1, EPIC-1-S2, EPIC-2-S2, EPIC-3-S2, EPIC-3-S3 are all unresolved `TODO` links. Land (or stub) `/lld backlog-store`, `/lld epic-suggester`, and `/lld reconciler` before sprint start so estimators have the interface-level detail those stories reference. |

**Overall Persona Grade: B** (point average ≈ 3.36 across 14 evaluation points — six A, eight B — rounds to B). The plan is sprint-ready with strong context, an acyclic and fully-covered milestone DAG, and testable criteria throughout. The one consistent drag is the under-specified suggestion-matching in EPIC-2-S2 / M2, which a single planning clarification (P1) would lift to A-range.
