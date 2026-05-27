# PRD Review — Shield Backlog

**Source:** `docs/shield/backlog-20260527/prd.md` (snapshot: `source-prd.md`)
**PRD type:** Lean (confirmed) · **Date:** 2026-05-27 · **Reviewers:** 13 dispatches (9 PM dims + agile-coach + tech-lead + dx-engineer + finops-analyst)

## Verdict: **Needs Work** (composite 2.7, blocked by 1 P0)

Strong, well-scoped lean PRD with an unusually clean conceptual model (manifest = reconciliation key, epic = removal gate, no ids). It's held back by one Critical gap (no risks/assumptions treatment) and a cluster of consistency issues — several introduced by the recent rapid edits (the reconciliation trigger and "automatically" wording).

| Persona | Weight | Grade | Notes |
|---|---|---|---|
| product-manager (dims 1,2,3,7,8,11,12) | 1.0 | **C (2.17)** | dim 1 & 12 drag it down |
| agile-coach (dim 4) | 1.0 | **B (3.0)** | happy-path-only coverage |
| tech-lead (dims 5,6) | 1.0 | **Informational** | lean-exempt (real NFR notes below) |
| dx-engineer (anti-patterns) | 0.7 | **B (3.0)** | found edit-induced contradictions |
| finops-analyst (dim 13) | 0.7 | **N/A** | internal tool, no cost surface |
| **Composite** | | **2.69** | ≥2.5 but P0-gated → Needs Work |

### Per-dimension grades

| Dim | Name | Grade | | Dim | Name | Grade |
|---|---|---|---|---|---|---|
| 1 | Problem clarity | **D** | | 8 | Legal/privacy | N/A |
| 2 | Scope boundaries | B | | 9 | GTM | informational |
| 3 | Measurable success | C | | 10 | Support/CX | informational |
| 4 | Scenario coverage & AC | B | | 11 | Why now | C |
| 5 | NFR coverage | informational | | 12 | Risks & assumptions | **D** |
| 6 | Rollout & ops | informational | | 13 | Cost | informational |
| 7 | RACI & approvals | A | | | | |

---

## P0 — must fix before `/plan` (1)

**P0-1 · Dim 12a · Risks & assumptions (Critical, F).** No risks section: failure modes appear only as §7 counter-metrics, with no mitigations or named owners, and no validated/unvalidated assumptions framing.
→ *Add a short lean risks table — each risk + mitigation + owner — and an assumptions list. The load-bearing unvalidated assumption is the whole no-hooks bet: "agents reliably surface follow-ups conversationally." Mitigations mostly already exist (reconciliation-on-view → graveyard risk; atomic write → corruption).*

## P1 — should fix for quality (8)

- **P1-1 · Dim 1b (Important, F).** Problem stated with zero baseline numbers. → Add one figure, e.g. "~N follow-ups lost across the last M `/implement` runs."
- **P1-2 · Dim 1a (Critical, C).** Personas are role categories, not a named persona. → Name P1 concretely (e.g. "Ashwini, Shield maintainer running `/implement` daily").
- **P1-3 · Dim 3a (Critical, C).** Three of four metrics use vague targets ("Majority", "often enough", "one step"). → Attach numbers + a time horizon (e.g. "≥70% reach a terminal state within 30 days").
- **P1-4 · Dim 3d (Warning, F).** No tracking owner/cadence for the metrics. → Name how it's measured (e.g. periodic `/backlog` audit, or git history of `backlog.json`).
- **P1-5 · Dim 11a/11b (Critical/Important, C).** Why-now describes a standing gap, not a concrete trigger; cost-of-inaction unquantified. → Anchor to a real recent instance of lost follow-up work.
- **P1-6 · Dim 12b (Important, D).** No validated-vs-unvalidated assumptions split. → See P0-1 fix.
- **P1-7 · Dim 4a (Critical, C) + 4b (Important, C).** Flows are happy-path only; edge cases (missing `plan.json`, abandoned capture, concurrent writes to the single global `backlog.json`, two features sharing an epic id) unaddressed. → Add ≥1 error path per core flow; resolve the ordering-collision open question.
- **P1-8 · DX / matching rule (P1).** With ids removed, the PRD never says **how a proposed-new epic name is matched to the eventual real epic in `plan.json`** — this is the central removal-correctness decision and is left implicit. → Specify the match key (string match? user-confirmed at promotion?).

## P2 — nice to have (4)

- **Dim 2b (Critical, B).** Several §10 out-of-scope items are bare; add a one-line why-deferred each.
- **Dim 2c (Warning, F).** No scope-creep guard naming the likely creep ask + decision authority (@ashwinimanoj).
- **Dim 7c (Important, B).** Sign-off N/A names no confirmer → "N/A — internal tooling (confirmed by @ashwinimanoj)".
- **Dim 12c (Warning, B).** Promote resolved §9 open questions into a short decision log.

---

## DX anti-patterns (cross-cutting)

Two of these were introduced by the recent edits — worth fixing before `/plan`:

1. **(P1) M3 vs §9 contradiction.** §8 M3 states "`/backlog` reconciles on view" as settled, but §9 still lists the reconciliation trigger as **Open** ("on view / end of `/plan` / both"). A developer can't implement M3 against an unsettled trigger. → Resolve §9 or soften M3.
2. **(P2) "removed automatically" vs user-triggered.** §6 says entries are "removed **automatically**," but reconciliation runs on `/backlog` view (a user action) — and §6's own non-goal disclaims "automatic surfacing machinery." → Replace "automatically" with "on next `/backlog` view."
3. **(P1) `kind` field undefined but assumed settled.** §6 + M1 commit to "epic/story/task granularity" and M1 says "schema defined," yet §9 leaves the backing `kind` field open. → Decide `kind` before M1.
4. **(P1) Capture-from-skill interface undefined.** M1 requires capture "usable from any Shield skill" but no command/helper/write-contract is specified. → Define the capture entrypoint.
5. **(P1) Reconciliation match key** — see P1-8.
6. **(P1) Unfalsifiable metrics** — see P1-3.

**Clarity strengths (keep):** problem-first ordering; the feature=key / epic=gate distinction is load-bearing and well-defined; non-goals are thorough with rationale; lean exemptions are explicit and correct.

## Tech-lead NFR notes (informational, lean-exempt — but real)

Not gating, but cheap to fold in now since the plan will need them:
- **Atomic write + concurrency** for `backlog.json` (write-temp-then-rename; concurrent capture vs reconcile-rewrite is the primary failure case).
- **Schema versioning** — add `schema_version` so the open §9 shape decisions (ordering, `kind`) can evolve via read-old/write-new.
- **Read-contract drift** — reconciliation should no-op (never remove) if `manifest.json`/`plan.json` are missing or an older shape, not error.
- **Recovery posture** — `backlog.json` is git-tracked, so a bad reconciliation is `git revert`-able; consider a dry-run/confirm before reconcile removals in v1.

---

## Recommended next steps

1. Fix **P0-1** (risks/assumptions) and the two edit-induced contradictions (#1, #2) — all small.
2. Resolve the three M1-gating open questions (`kind`, ordering, reconciliation trigger) or mark them deferred-with-default.
3. Specify the **epic match key** (P1-8) — it's the correctness heart of reconciliation.
4. Re-run `/prd-review` or proceed to `/plan` once P0 is cleared.

*Files: `summary.md` (this), `enhanced-prd.md` (annotated), `review-comments.json`, `detailed/*.md` ×5.*
