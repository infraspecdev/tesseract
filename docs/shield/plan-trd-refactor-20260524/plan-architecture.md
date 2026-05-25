# Plan Architecture — `/plan` TRD refactor

**Feature:** `plan-trd-refactor-20260524`
**Source research:** [`research.md`](./research.md) — read this first; it is the authoritative source for design decisions, citations, and rejected alternatives.
**Date:** 2026-05-24

> This document is the **why & how** companion to `plan.json`. For the **what to do** breakdown (epics, stories, ACs), see `plan.json` and the rendered [`plan.md`](./plan.md).
>
> **Note on path layout:** `/plan` today still emits `plan-architecture.md`. This plan run uses today's `/plan` to plan the refactor of `/plan`. After EPIC-1-S2 lands, future plan runs will emit `trd.md` in this slot instead.

## Why this refactor

`/plan` currently emits a stories-first work-breakdown plus a free-form `plan-architecture.md` companion. The current artifact is loose and de-facto ADR-flavored — well-suited to infra work but missing the structural rigor (NFRs, Cross-Cutting Concerns, first-class Milestones) that backend work needs. The refactor introduces a **unified 14-section Technical Requirements Document** (TRD) — grounded in IEEE 1016 + the reference TRD template (synthesized during research) + Google/Uber/Larson/Orosz modern practice — that replaces `plan-architecture.md` for **both backend and infrastructure** work. Domain-aware prompting per section surfaces the right interpretation (e.g., §11 APIs = HTTP contracts for backend, module interfaces + cloud-API surface for infra), and an explicit `n/a — <reason>` escape handles sections that genuinely don't apply (e.g., §4 Product Journey on a pure-state infra change). The strongest property of today's `plan-architecture.md` — Rollback Strategy — is promoted to first-class §14. LLDs are per-component (C4 Container/Component) and authored separately by a future `/lld <component>` command; typically backend-only since infra code is declarative-spec-as-code. This plan run only emits TODO placeholders for LLD references.

Full rationale, alternatives considered, and citations are in `research.md`. This document does not restate them.

## How the implementation breaks down

Three milestones, five epics, sixteen stories (post-review). Sequencing is enforced by milestone `depends_on` in `plan.json`. Plan reflects the 2026-05-25 plan-review feedback (composite B / Ready; 6 P0 + 12 of 15 P1 recommendations folded in).

```
M1 TRD cutover                                  ← P0 (ship together in one PR)
├─ EPIC-1: TRD generation and storage
│   ├─ S1 Author the canonical 14-section TRD template
│   ├─ S2 Update /plan to emit trd.md (unified backend + infra + mixed)
│   ├─ S3 Update existing-feature behavior on re-run
│   └─ S4 Bump plugin version per CLAUDE.md mandate          (new — P1-12)
├─ EPIC-2: Story schema and design traceability
│   ├─ S1 Extend plan.json schema with optional design_refs[]
│   ├─ S2 Populate design_refs[] when /plan has TRD context
│   └─ S3 Add JSON Schema validator for plan.json            (new — P1-7)
└─ EPIC-3: Eval coverage for TRD format
    ├─ S1 Author positive TRD eval fixtures (backend + infra + mixed)
    ├─ S2 Author 16 negative fixtures (14 missing + drift + vague-TBD)
    └─ S3 Wire eval into recurring CI + RED-GREEN paper trail

M2 Review + sync wiring                         ← P1 (follows M1)
└─ EPIC-4: /plan-review and /pm-sync wiring
    ├─ S0 Scaffold Jira / Confluence / Notion adapter packages   (new — P0-2)
    ├─ S1 Add 14-section presence rule + stale-anchor rule
    ├─ S2 Add PRD↔TRD duplication-detection rule
    └─ S3 /pm-sync emits design_refs[] as web links with idempotent upsert

M3 Drift + duplication hardening                ← P2 (follows M2)
└─ EPIC-5: Drift + duplication hardening
    ├─ S1 Add last_aligned_with metadata to plan.json
    └─ S2 Add implementation-manual / pseudo-code lint rule
```

## Key architectural decisions

The TRD section list, anchor strategy, `design_refs[]` shape, de-duplication contract, and failure-mode countermeasures are all locked in `research.md`. The decisions specific to this implementation plan are:

1. **Direct cutover, no feature flag.** EPIC-1-S2 swaps `plan-architecture.md` for `trd.md` in `/plan`'s output set. No `.shield.json` toggle.
2. **One TRD, two domains.** Same 14-section template applies to backend and infra work. `/plan`'s SKILL.md carries domain-aware prompting per section (backend interpretation + infra interpretation), and the eval accepts `n/a — <reason>` as an escape for sections that genuinely don't apply (e.g., §4 Product Journey on a pure-state infra change).
3. **§14 Rollback Strategy is a first-class section** — preserves the strongest property of today's `plan-architecture.md`.
4. **Old feature folders are left untouched.** EPIC-1-S3 explicitly guards against deleting existing `plan-architecture.md` files. Git history is the archive.
5. **M1 ships as a single PR.** Generator, schema, and eval land together. The eval cannot ship before the generator (no fixture to validate); the generator should not ship without the eval (regression risk on first re-run). Land them atomically.
6. **`design_refs[]` is additive and zero-risk.** Bumps sidecar schema 1.1 → 1.2. Adapters that don't understand the field ignore it; no `/pm-sync` schema break (EPIC-4-S3 is the additive forward-link wiring).
7. **LLD references are TODO placeholders in v1.** `design_refs[]` entries with `doc: "lld"` carry `anchor_url: null` and `label: "TODO: link when /lld <component> lands"`. When `/lld` ships in a later epic, those placeholders get resolved. LLDs are typically backend-only.
8. **Eval is the structural enforcement mechanism.** Per CLAUDE.md eval-coverage mandate, M1 ships with **two** positive fixtures (one backend, one infra), one missing-section negative per required section, one drift-by-addition negative, and one "vague-prose-instead-of-`n/a`" negative. RED → GREEN paper trail captured in the PR body (EPIC-3-S3).

## Deliverables (per milestone)

### M1 — TRD cutover (one PR)
- `shield/commands/plan.md` — emits `trd.md` not `plan-architecture.md`
- `shield/skills/general/plan-docs/SKILL.md` — 14-section TRD template + generation prompt with **domain-aware section guidance** (backend interpretation + infra interpretation per section)
- `shield/skills/general/plan-docs/sidecar-schema.md` — schema bumped to 1.2 with `design_refs[]` documented
- `shield/schema/output-paths.yaml` — `plan_arch_md`/`plan_arch_html` replaced by `plan_trd_md`/`plan_trd_html`
- `shield/evals/plan-trd.yaml` — 2 positives (backend + infra) + 14 missing-section negatives + 1 drift-by-addition negative + 1 vague-prose-instead-of-`n/a` negative
- `shield/evals/plan-trd/fixtures/positive-backend/` — full 14-section TRD fixture for a backend feature
- `shield/evals/plan-trd/fixtures/positive-infra/` — full 14-section TRD fixture for an infra change (with `n/a — <reason>` on at least one section)
- `shield/evals/plan-trd/fixtures/missing-*/` — 14 missing-section negative fixtures
- `shield/evals/plan-trd/fixtures/extra-section/` — drift-by-addition negative fixture
- `shield/evals/plan-trd/fixtures/vague-tbd/` — section with "TBD" instead of `n/a — <reason>`; eval must fail

### M2 — Review + sync wiring (one PR)
- `shield/skills/general/plan-review/SKILL.md` — 14-section presence rule + stale-anchor rule + duplication-detection rule
- `shield/commands/pm-sync.md` — describes `design_refs[]` forwarding
- `shield/adapters/<each>/...` — Confluence, Jira, ClickUp, Notion adapters forward `design_refs[]` as web links
- `shield/evals/plan-review-trd.yaml` — fixtures exercising both new review rules
- Per-adapter eval fixtures

### M3 — Drift + duplication hardening (one PR)
- `shield/skills/general/plan-docs/sidecar-schema.md` — schema bumped to 1.3 with `last_aligned_with`
- `shield/skills/general/implement/SKILL.md` (or equivalent) — updates `last_aligned_with` on story close
- `shield/skills/general/plan-review/SKILL.md` — implementation-manual lint rule
- Eval fixtures for both new rules

## Rollback strategy

The refactor is a direct cutover; reversibility cost is low.

- **Forward:** Three PRs (M1, M2, M3), sequenced by `depends_on`.
- **Reversal:** Revert `plan-docs/SKILL.md` to the pre-refactor template + restore `plan-architecture.md` generation. Existing `trd.md` files in feature folders remain readable. `design_refs[]` is optional everywhere, so removing it is a no-op for downstream adapters. `last_aligned_with` is also optional and reverting drops it without breaking older sidecars.
- **No migration:** Pre-refactor feature folders keep their `plan-architecture.md` — no rewrite, no script.

## Out of scope

The following are deferred and tracked in `plan.json` `metadata.out_of_scope`:
- `/lld <component>` command (template locked, command is a separate epic).
- Adapter auto-creation of Confluence/Notion design-doc pages.
- Structured ClickUp/Notion relationships beyond URL fields.
- Migration tool for existing `plan-architecture.md`.

## What to do next

- `/plan-review docs/shield/plan-trd-refactor-20260524/plan.json` — multi-agent review against the rubric.
- `/pm-sync docs/shield/plan-trd-refactor-20260524/plan.json --tool clickup` (or jira, notion) — sync stories to your PM tool.
- `/implement` — TDD-driven implementation, starting with EPIC-3-S1 (positive eval fixture) to anchor the RED → GREEN trail.
