# Plan Review: /plan TRD refactor

**Date:** 2026-05-25
**Plan:** `docs/shield/plan-trd-refactor-20260524/plan.json` (+ plan.md, plan-architecture.md)
**Reviewers:** DX Engineer, Agile Coach, Architect, Backend Engineer, SRE
**Composite Score:** **B / Ready** (with P0 fixes recommended before implementation)
**Composite numeric:** 2.77 (weighted: Architect+DX+Backend = 1.0; Agile+SRE = 0.7)

## Verdict

The plan is structurally **ready** — sprint-ready stories, testable ACs, milestone DAG is clean, schema design is well-reasoned, reversibility is documented. But three reviewers (SRE, Backend Engineer, Architect) surfaced **6 P0 recommendations** that should be addressed before implementation starts. The most consequential: the adapter work in **EPIC-4-S3** is materially larger than the plan implies (only 1 of 4 PM-tool adapters exists today as a `uv` package), and the eval is wired for one-shot PR-body capture rather than recurring CI gating.

## Score Summary

| Persona | Grade | Weight | Numeric | Key Finding |
|---|---|---|---|---|
| Agile Coach | **A-** | 0.7 | 4 | Sprint-ready: 12/13 points A/A-, milestone DAG clean, all ACs testable |
| DX Engineer | **B+** | 1.0 | 3 | Handoff/specification gaps: section_id heuristic, adapter paths, CI vs PR-body |
| Architect | **B** | 1.0 | 3 | Edge-case completeness: stale "13-section" refs, off-by-N negatives, no stale-anchor detection |
| SRE | **C** | 0.7 | 2 | Runtime safety net missing: no recurring CI gate, no rollback trigger, no provenance stamp |
| Backend Engineer | **C+** | 1.0 | 2 | Adapter contract missing, idempotency undefined, 3 of 4 adapters don't exist as packages |

## P0 Recommendations (block implementation start)

These appear with **convergent support across multiple reviewers** — addressing them is the highest-leverage pre-implementation work.

| # | Recommendation | Origin | Affected story |
|---|---|---|---|
| **P0-1** | **Fix 14 vs 13 inconsistency across all artifacts.** `plan-architecture.md` lines 25, 37, 75 still say "13-section". EPIC-3-S3 AC says "all 13 negatives" but EPIC-3-S2 enumerates 16 negatives (14 missing-section + 1 drift + 1 vague-TBD). Pick a number and propagate everywhere. | Architect P1 + Backend P0 | EPIC-3-S2, EPIC-3-S3; plan-architecture.md prose |
| **P0-2** | **Split EPIC-4-S3 or add adapter-scaffolding story.** Only `shield/adapters/clickup/` exists as a `uv` package today; Jira/Confluence/Notion don't exist. Either split EPIC-4-S3 by adapter (S3a/b/c/d) or add an EPIC-4-S0 that scaffolds `pyproject.toml`, MCP-server skeleton, tests/, and a shared `shield/adapters/_common/design_refs.py` for the `DesignRef` dataclass and `forward_design_refs` protocol. | Backend P0 (verified by repo inspection) | EPIC-4-S3 |
| **P0-3** | **Specify the adapter interface contract.** Lock the function signature across all four adapters before implementation: `forward_design_refs(task_id: str, refs: list[DesignRef]) -> ForwardResult` with `ForwardResult{created, skipped, errors}`. Each `DesignRef` produces a deterministic idempotency key (`sha256(story_id + anchor_url)[:32]`) used as `globalId` for Jira/Confluence remote-links. | Backend P0 | EPIC-4-S3; new schema doc in `sidecar-schema.md` |
| **P0-4** | **Add idempotency test fixture to EPIC-4-S3.** Add an AC: "Running `/pm-sync` twice in succession on the same plan produces the same remote state — no duplicate remote-links, no duplicate ClickUp custom-field writes, no duplicate Notion property writes." Primary regression guard for the most likely incident shape. | Backend P0 + Architect P2 (`trd_sha`) | EPIC-4-S3, EPIC-2-S2 |
| **P0-5** | **Wire eval into recurring CI, not just one-shot PR body.** EPIC-3-S3 says "Wire eval into CI" but the tasks only describe manual PR-body capture. Add a `.github/workflows/` step that runs `uv run shield/evals/run.py plan-trd` on every PR touching `shield/skills/general/plan-docs/**` or `shield/schema/**`. Without this, the next `plan-docs/SKILL.md` edit silently breaks the 14-section contract. | SRE P0 + DX P1 | EPIC-3-S3 |
| **P0-6** | **Define mixed-domain failure mode in EPIC-1-S2.** "Mixed → annotate per section" is a single line with no worked example, no eval fixture, no AC. Realistic monorepos (Tesseract itself: `pyproject.toml` + `*.tf`) will hit this on day 1. Add: (a) a `positive-mixed/` fixture under `shield/evals/plan-trd/fixtures/`, (b) explicit guidance for what "annotate per section" emits, (c) a detection rule (presence of both infra and backend markers). | SRE P0 + DX P1 + Architect P1 (3 reviewers) | EPIC-1-S2, EPIC-3-S1 |

## P1 Recommendations (should land in implementation milestone)

| # | Recommendation | Origin |
|---|---|---|
| P1-1 | **Define `section_id` heuristic in EPIC-2-S2.** The phrase "story title keyword → TRD section anchor" is a hint, not an algorithm. Specify: "lowercase fuzzy match story.name tokens against TRD section anchor slugs; fall back to §7 high-level-design if no token overlaps." | DX P1 |
| P1-2 | **Define `design_refs[]` merge semantics in EPIC-2-S2.** "Preserved or updated in place" is ambiguous. Specify: "match by `(doc, section_id, component)` tuple; replace `label` if changed, never duplicate keys." | DX P1 |
| P1-3 | **Name adapter file paths in EPIC-4-S3.** Replace "the relevant adapter logic (Python under shield/adapters/)" with explicit per-tool file paths and the function/class to extend in each. | DX P1 + Agile P2 |
| P1-4 | **Rename or rescope EPIC-3-S3.** Story title says "CI" but tasks describe manual PR-body capture. Either add a workflow YAML task (with file path) or retitle to "Eval execution + RED-GREEN paper trail". | DX P1 |
| P1-5 | **Reconcile domain-detection source.** `plan.json` EPIC-1-S2 description says "detects the dominant domain from .shield.json + repo markers"; `plan.md` says only "repo markers". Pick one and document the config key if `.shield.json` is in. | DX P1 |
| P1-6 | **Add stale-anchor detection to /plan-review.** When a story's `design_refs[].anchor_url` points at a `#section-id` no longer present in the live `trd.md`, `/plan-review` should report it as a Critical finding. Otherwise sidecar→doc drift goes undetected. | Architect P1 |
| P1-7 | **Add JSON Schema validator story.** Two version bumps (1.1→1.2→1.3) in one PR series without a machine-readable validator is the drift inflection. Add `shield/scripts/validate_plan.py` using `pydantic` or `jsonschema`. Invoked by `/plan-review` and the eval runner. | Backend P1 |
| P1-8 | **Specify observability shape for adapter forwarding.** Each `design_refs[]` forward emits one `action_log` entry with `action='forward_design_ref'`, fields `{story_id, adapter, anchor_url, outcome, idempotency_key}`. Failures emit `forward_design_ref_failed` with `{error_class, http_status}`. | Backend P1 |
| P1-9 | **Add deprecation overlap for `output-paths.yaml`.** Keep `plan_arch_md` / `plan_arch_html` keys with `deprecated: true` rather than removing in M1. Remove in M3 or follow-up PR to protect external consumers of the contract. | Backend P1 |
| P1-10 | **Add provenance stamp on emitted TRDs.** Top-of-file comment: `<!-- generated by /plan vX.Y.Z on YYYY-MM-DD -->`. Pairs with `last_aligned_with` for full drift accountability. | SRE P1 |
| P1-11 | **Add rollback-trigger statement.** Plan-architecture.md §Rollback should name observable signals that trigger a revert: e.g., (a) eval fails on positive fixtures after merge, (b) >N user-reported broken `/plan` runs within 48h, (c) downstream `/pm-sync` adapter errors trace back to schema 1.2. | SRE P1 |
| P1-12 | **Add version-bump task per CLAUDE.md mandate.** Bump `.claude-plugin/marketplace.json` and `pyproject.toml` per the "When updating any plugin, bump its version in both...in the same commit" rule. Currently absent from every story. | SRE P1 + DX P2 |
| P1-13 | **Add tool-and-access requirements subsection.** Which Confluence/Jira/ClickUp/Notion test tenants (or mock client expectations), where credentials live (`.shield.json`? env vars?), which Python deps the eval pulls. | DX P1 |
| P1-14 | **Specify atomic write for `/plan` output.** If `/plan` cannot write `trd.md` (disk error, partial write, missing template), it must not leave a corrupted file behind — write atomically (temp file + rename) or fail loudly with the partial file removed. | SRE P1 |
| P1-15 | **Specify forward-compat policy in `sidecar-schema.md`.** How does `/plan-review` handle `version: "1.4"` from a future Shield? Reject, warn, or accept-with-ignored-fields? | Backend P1 |

## P2 Recommendations (nice to have)

| # | Recommendation | Origin |
|---|---|---|
| P2-1 | Split EPIC-3-S2 into "negative-fixture generator + 14 missing-section fixtures" and "drift + vague-TBD fixtures" for tighter sizing | Agile P2 |
| P2-2 | Add CHANGELOG entry / migration-note AC for the cutover | Agile P2 |
| P2-3 | Make intra-milestone story `depends_on` explicit in plan.json | Agile P2 |
| P2-4 | Lock the eval runner invocation (drop "or equivalent existing eval runner") | DX P2 |
| P2-5 | Pick YAML or JSON for the slug allow-list sidecar | DX P2 |
| P2-6 | Add inline `design_refs[]` JSON example in EPIC-2-S1 | DX P2 |
| P2-7 | Add AC for `/pm-sync` partial-failure behavior (1 of 4 adapters errors) | DX P2 |
| P2-8 | Add "local development" how-to-run note in plan-architecture.md | DX P2 |
| P2-9 | Defend or parameterize magic numbers (>80 char overlap, >20 line code block) | Architect P2 |
| P2-10 | Add `trd_sha` content hash alongside `last_aligned_with` for true undead-doc detection | Architect P2 |
| P2-11 | Add TRD `template_version` field for legitimate template evolution | Architect P2 |
| P2-12 | Add round-trip integration eval (`/plan` output → `/plan-review` says no Criticals) | Architect P2 |
| P2-13 | Add `--dry-run` mode for `/plan` so users validate locally before committing | SRE P2 |
| P2-14 | Add a one-page troubleshooting block (`plan-troubleshooting.md`) | SRE P2 |
| P2-15 | Add eval fixture for M2 running on pre-M1 `plan-architecture.md`-only folders | SRE P2 |
| P2-16 | Concurrent `/pm-sync` note (single-writer until idempotency-key lands) | Backend P2 |
| P2-17 | Rate-limit handling note per existing adapter posture | Backend P2 |
| P2-18 | Decide fate of this plan's own `plan-architecture.md` post-M1 (rename or freeze) | Backend P2 |

## Cross-reviewer convergence

The strongest signal is **convergent flagging** — recommendations cited by 2+ reviewers:

| Theme | Reviewers | Severity |
|---|---|---|
| Mixed-domain handling (EPIC-1-S2) | DX, SRE, Architect (3) | P0 |
| 14 vs 13 inconsistency | Architect, Backend (2) | P0 |
| EPIC-4-S3 adapter file paths | DX, Agile, Backend (3) | P0 (escalated) |
| CI wiring vs PR-body capture | DX, SRE (2) | P0 |
| Version-bump discipline | DX, SRE (2) | P1 |
| Idempotency / re-run safety | Architect, Backend (2) | P0 |

## Detailed Agent Findings

- [Agile Coach](detailed/agile-coach.md) — A-, sprint-readiness focus
- [DX Engineer](detailed/dx-engineer.md) — B+, handoff/specification gaps
- [Architect](detailed/architect.md) — B, topology + edge-case completeness
- [Backend Engineer](detailed/backend-engineer.md) — C+, adapter contract + repo-grounded findings
- [SRE](detailed/sre.md) — C, runtime safety net

## Next steps

1. Apply the **enhanced plan** ([enhanced-plan.md](enhanced-plan.md)) which carries the P0 fixes and most P1 recommendations
2. After applying, re-run `/plan-review` to confirm composite moves above 3.0 (target: B+/Ready-clean)
3. Then `/pm-sync` to push the updated stories
4. Then `/implement` starting with EPIC-3-S1 (positive eval fixtures) per the RED → GREEN trail
