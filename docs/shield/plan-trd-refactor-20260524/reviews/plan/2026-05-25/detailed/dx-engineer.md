# DX Engineer — Detailed Findings

> Back to [summary](../summary.md)

## DX Engineer Review (Grade: B+)

| # | Evaluation Point | Grade | Notes |
|---|-----------------|-------|-------|
| DX1 | Plan clarity | A | "Why this refactor" paragraph and milestone table give 30-second comprehension — "unified 14-section TRD replacing free-form plan-architecture.md, covers backend + infra, direct cutover." |
| DX2 | Story actionability | B | Most stories name exact files and concrete deltas. Gaps: EPIC-2-S2 names a "heuristic for picking section_id" but never defines what keyword-matching algorithm to use; EPIC-4-S3 says "the relevant adapter logic (Python under shield/adapters/)" without naming any of the 4 adapter files. |
| DX3 | Implementation step detail | B | Strong specifics in many places (slug allow-list verbatim, domain-detection markers enumerated, thresholds quantified). Weak spots: EPIC-3-S2 doesn't show the YAML schema; EPIC-3-S3 says `uv run shield/evals/run.py plan-trd` "or equivalent existing eval runner" — author should commit to one. |
| DX4 | Ambiguity audit | B | Several soft phrases survived: EPIC-4-S2 "e.g., flag if > 80 characters" (advisory not normative); EPIC-5-S2 "more than N lines" and only later pins N=20; EPIC-1-S2 "Mixed → annotate per section" is undefined; EPIC-2-S2 says entries are "preserved or updated in place" — which is it? |
| DX5 | Context sufficiency | A | Plan links to research.md, plan-architecture.md, and PR #43 sample. A new joiner can chase the references without tribal knowledge. |
| DX6 | Dependency clarity | A | Milestone-level `depends_on` is explicit. M1 ships as a single PR is called out. Eval-before-generator constraint is documented. Minor gap: story-level depends_on is implicit only. |
| DX7 | Tool & access requirements | C | `uv` implied by CLAUDE.md but never restated. EPIC-4-S3 needs Confluence/Jira/ClickUp/Notion credentials with no mention of test accounts, sandbox tenants, or how to mock. No mention of which Python version or new deps the eval runner might need. |
| DX8 | Handoff readiness | B | A developer can start EPIC-1-S1, EPIC-3-S1, EPIC-3-S2 cold. EPIC-4-S3 and EPIC-2-S2 would generate questions. Plan assumes familiarity with `plan-docs/SKILL.md` "generation prompt" current shape. |
| DX9 | Service boundaries | B | Boundaries are clean: `shield/commands/plan.md`, `shield/skills/general/plan-docs/`, `shield/schema/output-paths.yaml`, `shield/adapters/<tool>/`, `shield/evals/`. Gap: slug allow-list location is given as "YAML or JSON sidecar under shield/schema/" with choice left open. |
| DX10 | API & data flow design | B | `design_refs[]` contract is explicit. Schema bump path documented (1.1 → 1.2 → 1.3). Gap: no inline example `design_refs[]` JSON instance; EPIC-2-S2's "preserved or updated in place" merge semantics absent. |
| DX11 | Deployment strategy | B | "Direct cutover, no feature flag" is explicit. "M1 ships as a single PR" specifies atomicity. Old `plan-architecture.md` files preserved. Rollback strategy documented. Gap: no version bump checklist for `.claude-plugin/marketplace.json` and `pyproject.toml` per CLAUDE.md. |
| DX12 | CI/CD integration | C | EPIC-3-S3 names "Wire eval into CI" but tasks only describe manual PR-body capture. No GitHub Action, no workflow file path, no auto-discovery of new evals. Story title says CI but tasks describe manual capture. |
| DX13 | Error handling patterns | B | Several failure modes addressed (adapters without link affordance log + continue, `n/a — <reason>` escape, missing-reason flagged distinct from vague-TBD). Gap: malformed `trd.md` recovery? Unknown `doc` value in `design_refs[]`? Retry/idempotency for `/pm-sync` partial failures? |
| DX14 | Configuration management | C | EPIC-1-S2 description says ".shield.json + repo markers" but plan.md drops the .shield.json mention. No mention of secrets management for 4 adapter credentials. Slug allow-list filename left to implementer. |
| DX15 | Developer onboarding | B | plan-architecture.md is fine onboarding. research.md named authoritative. CLAUDE.md covers conventions. Gap: no local-dev "how do I run /plan and see trd.md emit?" walkthrough; no debugging note for non-deterministic eval failures. |

**Key Finding:** The plan is one of the more actionable specs reviewed — concrete file paths, verbatim slug allow-list, specific thresholds, clear cutover stance — but four soft spots will generate Slack pings during execution: (1) `design_refs[]` section_id heuristic underspecified, (2) EPIC-4-S3 doesn't list 4 adapter file paths, (3) "CI" in EPIC-3-S3 is actually PR-body capture, (4) Mixed-domain "annotate per section" output format undefined.

### Recommendations

| Priority | Point | Recommendation |
|----------|-------|---------------|
| P1 | DX2 | In EPIC-4-S3, replace "the relevant adapter logic (Python under shield/adapters/)" with the four explicit file paths and the function/class to extend in each. |
| P1 | DX4 | In EPIC-2-S2 tasks, define the `section_id` selection heuristic concretely: name the exact keyword-matching algorithm. |
| P1 | DX4 | In EPIC-2-S2 AC #3, replace "existing entries are preserved or updated in place" with a precise merge rule. |
| P1 | DX12 | In EPIC-3-S3, decide whether eval runs in GitHub Actions or only in PR-body capture. If CI is in scope, add a workflow YAML task; if not, retitle. |
| P1 | DX4 | In EPIC-1-S2, define what "Mixed → annotate per section" emits in the TRD prose. |
| P1 | DX7 | Add a "Tool & access requirements" subsection covering test tenants, credential location, Python deps. |
| P1 | DX14 | In EPIC-1-S2, decide and document: does domain detection consult `.shield.json` or only repo markers? The two documents disagree. |
| P2 | DX3 | In EPIC-3-S2/S3, lock the eval runner invocation. |
| P2 | DX9 | In EPIC-1-S1, choose YAML or JSON for the slug allow-list sidecar and commit to a filename. |
| P2 | DX10 | Add an inline example `design_refs[]` JSON instance to EPIC-2-S1 description. |
| P2 | DX11 | Add a task to EPIC-1-S2 (or a separate release story) for version bumps in `.claude-plugin/marketplace.json` and `pyproject.toml`. |
| P2 | DX13 | Add an AC or task covering `/pm-sync` partial-failure behavior when 1 of 4 adapters errors. |
| P2 | DX15 | Add a "local development" note describing how to run `/plan` against a fixture repo. |
