# Plan Review — Shield Backlog

**Date:** 2026-05-27
**Plan:** `docs/shield/backlog-20260527/` (plan.md + trd.md + plan.json)
**Source PRD:** prd.md (type: lean) · prior PRD-review: `reviews/prd/2026-05-27_2` (Ready, 3.12)
**Reviewers:** DX Engineer, Agile Coach, Backend Engineer, Security Engineer, SRE, Product Manager (PM1–PM10)
**Composite Score:** **B (3.14) — Ready** · **1 P0** (deterministic gate) · 12 P1 · 13 P2

> **Verdict: Ready, pending one P0 doc-fix.** The plan is well-structured, MVP-disciplined, and
> error-handling-first; the milestone DAG is acyclic and fully covered; the reconciliation
> read-contract was *verified accurate* against the live `manifest.json`/`plan-sidecar.schema.json`.
> The single P0 is a cheap one-line paraphrase (TRD §2 restates PRD §3 verbatim). The 12 P1s
> cluster around four real gaps the implementers should close first: the **skill write-helper
> signature is still open**, **atomicity is conflated with isolation** (lost-update path), the
> **match heuristic is undefined**, and several **load-bearing guarantees lack tests / shipped
> toggles** (F6 no-stamping, validate-or-refuse, the §14 kill switch, removal audit logging).

## Score Summary

| Persona | Weight | Grade | Key Finding |
|---------|:--:|:--:|-------------|
| DX Engineer | 1.0 | B (3.4) | Clear & sound, but 3 `design_refs` point at non-existent LLDs and the capture-helper signature is deferred |
| Agile Coach | 0.7 | B (3.36) | Sprint-ready with an acyclic, fully-covered DAG; only EPIC-2-S2's match heuristic is not estimable |
| Backend Engineer | 1.0 | B (3.33) | Read-contract verified accurate; held back by open helper signature + atomicity≠isolation |
| Security Engineer | 1.0 | B (3.05) | Sound for local single-actor tooling; N1 race + F6 no-stamping asserted but untested |
| SRE | 0.7 | B (3.0) | Failure-mode analysis & staged rollout are A-grade; day-2 instrumentation is thin |
| Product Manager | 0.7 | **A (3.7)** | Strong on impact/scope/prioritization/reversibility; PM10 business-value baseline unvalidated (C) |

**Composite** = (3·1.0 + 3·0.7 + 3·1.0 + 3·1.0 + 3·0.7 + 4·0.7) / 5.1 = **3.14 → B — Ready**

## Deterministic TRD Gates (run before persona dispatch)

| Gate | Rule | Result |
|---|---|---|
| 0a | Schema validation (`validate_plan.py`) | ✅ PASS (exit 0) |
| 0b | TRD 14-section presence (`validate_trd.py`) | ✅ PASS (exit 0) |
| 0c | Stale-anchor on `design_refs[]` | ✅ PASS — all `trd.md#…` anchors live; `lld` refs have null anchors (intentional TODO) |
| 0d | PRD↔TRD duplication (>80-char overlap) | ❌ **FAIL → P0** — TRD §2 restates PRD §3 with a **92-char** verbatim overlap |
| 0e | Implementation-manual (§7 fence >20 lines) | ✅ PASS — §7 is a 13-line ASCII diagram, not code |

## Consolidated Recommendations

### P0 — Must Fix (blocks sprint planning)

1. **[Gate 0d] Paraphrase TRD §2 so it no longer restates PRD §3 verbatim.** The opening sentence shares a 92-char run (`" — during /research, while writing a PRD, mid-/plan, and especially during /implement "`) with PRD §3, exceeding the 80-char duplication threshold. Rewrite TRD §2 to *summarize* the problem in technical-framing terms and link to PRD §3 rather than repeating it. (One-line fix; mechanical.)

### P1 — Should Fix (plan quality)

1. **[Backend, DX] Lock the skill write-helper signature in EPIC-1-S1/S2 ACs.** This is the carried-forward PRD-review P1, but TRD §12 Q3 still punts the signature to "/lld or implementation." Pin name, module path, params, return, and raise-on-invalid behavior now (e.g. `capture(text, *, kind="task", feature=None, epic=None, source) -> entry_id` in `shield/scripts/backlog_store.py`) — downstream skills cannot be built/tested against an undefined shape.
2. **[Backend, Security] Name the concurrency strategy — atomicity ≠ isolation.** N1 defends "capture racing reconciliation," but temp-then-rename alone does not prevent lost updates (two read-modify-writes → last-writer-wins drops an entry). Either document the single-writer assumption *where N1 describes the threat* (N5 already says "single actor") or add a lock / re-read-and-merge / `O_EXCL`. Add an interleaved-capture eval.
3. **[DX, Agile, Backend] Define the feature/epic match + suggestion heuristic.** Replace "best match" / "names expected stable" (EPIC-2-S2, EPIC-3-S2) with a concrete rule: normalization (case/whitespace), tie-break/ambiguity → entry stays, and epic-rename behavior. Add a measurable AC and resolve PRD §9's open "discovery cost" question (or land `/lld epic-suggester`).
4. **[Security] Add an eval asserting promotion leaves `plan.json` byte-unchanged (F6 no-stamping).** F6 is the load-bearing trust boundary; it has an AC but is absent from EPIC-4-S1's listed eval coverage.
5. **[Security] Add an AC that a malformed/partial `backlog.json` on read is *refused* with a named error.** "Validate-or-refuse on read" (F2/N1) currently has no AC proving the refusal path (only crash-atomicity is tested).
6. **[SRE] Ship the "disable eager prune" kill switch as a story/task.** §14 names it as the rollback action but no story delivers the toggle — add a `.shield.json` flag (e.g. `backlog.auto_reconcile`) disabling eager prune and lazy sweep independently. Today the documented mitigation is unactionable.
7. **[SRE] Log successful removals with rationale.** Only the never-remove-on-doubt path logs (N3). Eager prune / lazy sweep should log `{entry id, feature, epic, match-kind, triggering run, gating plan.json}` to a defined destination — otherwise a confident-but-wrong removal leaves a git diff with no reasoning.
8. **[SRE] Close the uncommitted-state recovery gap.** Eager prune fires at end-of-`/plan`/`/implement`, possibly before `backlog.json` is committed — at which point `git revert` (N4) cannot recover the entry. Commit before the destructive prune, or write pruned entries to a transient `.shield/backlog-removed.log`.
9. **[SRE] Instrument the N2 ~1s budget.** "Revisit if breached" (Q1 epic-index) is unfalsifiable without timing — add a debug-gated latency line to `/backlog` view so the breach signal isn't "a human notices slowness."
10. **[PM10] Ground the business-value claim with a rough baseline.** The whole justification rests on an explicitly unvalidated assumption that lost future-work volume is high enough to justify the tool. Count lost/re-derived items over a recent week (git history / chat) before committing all four milestones.
11. **[Backend] Specify the `id` contract.** `id` is required but its type, generation strategy, and uniqueness are undefined, yet remove/promote/prune all key off it. Add type + generation (uuid4/monotonic/slug) + a uniqueness constraint in EPIC-1-S1, plus an AC: "schema rejects duplicate `id`."
12. **[Backend] State the "epic landed" gate as one precise predicate.** F7 ("epic's work appears"), EPIC-3-S2 AC ("epic's stories appear"), and the schema (`stories[] minItems:1`) say it three ways. Pin it: "epic with matching id/name is present in `plan.json.epics[]`; story `status` is **not** consulted."

### P2 — Nice to Have

1. **[DX]** Name the CI entrypoint + path-filter glob in EPIC-4-S1 ("wire into CI" is not actionable as written).
2. **[DX]** Add an explicit intra-epic story-dependency note for EPIC-3 (S1+S2 must land before S3).
3. **[DX]** Specify the badge render format once (EPIC-2-S1 shows it only as an example) and add a local-dev/dry-run loop to the backlog SKILL.md.
4. **[Agile]** Add code-review + "marketplace version published" steps to the implied Definition of Done (EPIC-4-S2).
5. **[Agile]** Land or stub `/lld backlog-store`, `/lld epic-suggester`, `/lld reconciler` so the unresolved TODO `design_refs` resolve before sprint start.
6. **[Backend]** Add a no-op `migrate(doc)->doc` seam + test, or explicitly scope the schema_version AC as doc-only-until-v2 (it currently overstates "migration policy present" as working code).
7. **[Security]** Add a `--dry-run` reconciliation canary so a maintainer validates against their real backlog before trusting auto-removal.
8. **[Security]** Add a fixture for epic-name collision across two different features (PRD §10 risk / §14 trigger) asserting the entry stays.
9. **[Security]** Define the security purpose of the `source ∈ {user, agent}` field (provenance/audit-only vs. trust signal) and address agent-injected entries flowing into `/plan`.
10. **[Security]** Note in N4/EPIC-1-S4 that git-revert recoverability only covers committed entries — a manual remove of an uncommitted entry is unrecoverable by design.
11. **[SRE]** Give the manual `/backlog` audit a concrete cadence and "what reading triggers action."
12. **[SRE]** Add a recovery-rehearsal eval (assert `git revert` / restore brings a wrongly-pruned entry back).
13. **[PM5]** Add a 2–3 sentence plain-language executive summary atop `trd.md` and `plan.md` before the schema-/pipeline-heavy detail.

## Detailed Agent Findings

| Agent | Grade | Detailed Report |
|-------|:--:|----------------|
| DX Engineer | B | [detailed/dx-engineer.md](detailed/dx-engineer.md) |
| Agile Coach | B | [detailed/agile-coach.md](detailed/agile-coach.md) |
| Backend Engineer | B | [detailed/backend-engineer.md](detailed/backend-engineer.md) |
| Security Engineer | B | [detailed/security-engineer.md](detailed/security-engineer.md) |
| SRE | B | [detailed/sre.md](detailed/sre.md) |
| Product Manager (PM1–PM10) | A | [detailed/product-manager.md](detailed/product-manager.md) |
