# Plan Review — Shield Backlog (`backlog-20260527`)

**Date:** 2026-05-29 · **Run:** 1 · **Source PRD:** prd.md (type: lean) · **Plan:** plan.md + trd.md + plan.json (schema 1.5)
**Reviewers:** dx-engineer, agile-coach, backend-engineer, sre, security-engineer, product-manager (PM1–PM10)

> **✅ Resolution (applied 2026-05-29):** the user chose "Apply P0+P1 to the plan." All **3 P0** and **8 P1** findings have been folded into the canonical artifacts (plan.json, trd.md, the 3 LLD drafts) and `shield/schemas/shield.schema.json` (additive `backlog` object). Re-validation: `validate_plan.py` ✅, `validate_trd.py` ✅ (milestone-drift clean), kill-switch `.shield.json` validates ✅, all 3 LLD drafts structurally ✅. The plan is now clear for `/implement`. See `plan.json` `metadata.plan_review_2026_05_29.{p0_applied,p1_applied}` for the per-finding trace. The findings below are retained as the review record.

## Verdict: **Ready — composite 3.49 (B+)** ⚠️ *(3 P0 + 8 P1 since applied — see Resolution above)*

The re-plan is a clear improvement on the prior run (3.14 → 3.49): the deferred TRD landed, schema is 1.5, and the prior P0 (gate-0d duplication) + the SRE/Security P1 set are verifiably folded in. **However**, the backend reviewer — checking the design against the *live* Shield schemas rather than only against itself — surfaced **3 P0 contract defects** that each break a core path at implementation time. The weighted composite lands in "Ready" range, but the P0s gate `/implement`. All three are localized contract-pinning fixes, not design rework.

## Scorecard

| Persona | Weight | Grade | Numeric |
|---|---|---|---|
| DX Engineer | 1.0 | A− | 3.7 |
| Backend Engineer | 1.0 | B− | 2.7 |
| Security Engineer | 1.0 | A− | 3.7 |
| Agile Coach | 0.7 | A− | 3.7 |
| SRE / Operations | 0.7 | A− | 3.7 |
| Product Manager (PM1–PM10 avg) | 0.7 | A | 3.6 |
| **Composite** | | **B+** | **3.49 → Ready** |

PM dim grades: PM1 A · PM2 A · PM3 A · PM4 B · PM5 B · PM6 B · PM7 A · PM8 A · PM9 A · PM10 B → avg 3.6.

## Deterministic gates (run before dispatch)

| Gate | Result |
|---|---|
| 0a schema (`validate_plan.py`) | ✅ exit 0 |
| 0b TRD sections (`validate_trd.py`) | ✅ exit 0 (incl. milestone-drift) |
| 0c stale anchors | ✅ none |
| 0d PRD↔TRD duplication (§2/§5) | ✅ 6-char / 3-char overlap (≤80) — prior P0 resolved |
| 0e impl-manual (§7 fence >20 lines) | ⚠️ §7 ASCII diagram is 27 lines, but §8 has 5 populated alternatives → escape satisfied (not P0) |
| 0f touches_lld_drift | ✅ |
| 0g lld_components_integrity | ✅ |
| 0h undocumented_lld | n/a — no canonical `docs/lld/` (all net-new) |
| 0i lld_draft_review (3 drafts) | ✅ all 14 always-on + 8 forced subsections present, no vague TBDs |

## P0 — Blockers (fix before `/implement`)

All three independently verified against live schemas (`shield/schemas/{shield,plan}.schema.json`, `docs/shield/manifest.json`).

1. **Reconciler/suggester contracts don't match the real `manifest.json`/`plan.json` shapes** *(backend P0-1)*. `manifest.json` is `{schema_version, features:[{name, artifacts:{…plan_json: bool…}, reviews, updated}]}` — a list keyed by `name`, with a boolean `plan_json` flag and **no stored plan path**. `reconcile(entry, *, manifest, plans)` (lld-reconciler §5) never defines `plans` and never says the path must be *derived*. **Fix:** pin the real shapes; define `plans: dict[slug→plan]` populated by reading `docs/shield/<feature>/plan.json` for each feature with `artifacts.plan_json == true`; add a fixture from the actual manifest schema. *(Also covers DX P1 manifest read-contract.)*
2. **Existing-epic matching keys off a positional slot, not an identity** *(backend P0-2)*. Epic ids are `EPIC-N` slugs assigned by `/plan` (`EPIC-2` = different epics in different plans, verified). After any re-`/plan`, an existing-epic entry stamped `EPIC-2` matches the wrong epic or rots. **Fix:** match existing epics by normalized `name` too (same predicate as proposed-new); treat `EPIC-N` only as a within-one-plan disambiguator; add a "epic reordered across a re-plan" eval.
3. **Kill switch `backlog.auto_reconcile` is unshippable under the current `.shield.json` schema** *(backend P0-3)*. `shield.schema.json` has `additionalProperties: false` and no `backlog` key; adding the flag fails validation, and no story includes the schema change. **Fix:** add a task+AC (EPIC-3-S3, version-bump in EPIC-4-S2) extending `shield.schema.json` with an optional `backlog` object (`{auto_reconcile: bool, default true}`) + config example. Without it the documented first-line rollback (TRD §14) cannot ship.

## P1 — Should fix for plan quality

1. **Resolve the EPIC-3-S3 N4 recovery OR** *(agile AC7 + sre P1-1)*. AC5 encodes "commit-before-prune **or** removed-log" — not writable as one test, and the §14 runbook can't be precise. Pick one v1 default (**recommend `.shield/backlog-removed.log`** — avoids forcing a possibly-dirty-tree commit on every prune, decouples recovery from git state mid-`/implement`); make the other a non-goal.
2. **Add lost-update detection (compare-before-replace)** *(backend P1-1 + security P1-a)*. The concurrency eval tests a race the single-writer design forbids, and N5, if silently violated, yields a silent lost update. Have `capture()`/`remove()` carry the schema_version+entry-count (or mtime/hash) read at start and refuse `os.replace()` if the file changed underneath — a loud `BacklogInvalid` instead of a lost entry, **no lockfile**. Then the eval tests a real, detectable behavior.
3. **Reword "schema rejects duplicate id" → validator** *(backend P1-2)*. JSON Schema 2020-12 can't express property-level array uniqueness; F2 + EPIC-1-S1 AC must say `validate_backlog.py` enforces it (`duplicate_entry_id`).
4. **Pin the feature `name` == folder-slug invariant** *(backend P1-3)*. `suggest_feature` returns manifest `features[].name`, but the reconciliation key is the folder slug; if they differ, suggestion proposes an unresolvable value. Document the invariant + add a "suggested value resolves to an existing `docs/shield/<value>/`" fixture.
5. **Resolve the packaging model** *(backend P1-4)*. F3 ("every capturing skill builds against this signature") implies an importable module; EPIC-4-S2 hedges. Decide at plan time — package `backlog_store` with a `pyproject.toml` so the version bump is unconditional; document the import path skills use.
6. **Resolve the CI entrypoint to a concrete value** *(dx P1)*. EPIC-4-S1 still phrases the runner as a task; name the actual workflow file + runner so the eval-gate AC is verifiable.
7. **Add a write-side validation eval** *(security P1-b)*. "validate-or-refuse on read/**write**" is asserted but only read-side + crash-mid-write are tested. Add: `capture()` producing a schema-invalid doc raises `BacklogInvalid` and leaves backlog.json byte-unchanged.
8. **Test the recovery ordering seam** *(security P1-c)*. Strengthen the recovery-rehearsal eval to assert recoverability across a crash *between* log-append and remove (and between remove and commit), not just after a clean wrong-removal.

## P2 — Nice to have

- **DX:** fixed audit interval + numeric trigger (not "e.g. monthly"); state runtime prereqs (Python/uv, pydantic+jsonschema) once in SKILL.md; label the 3.12 (PRD-review) vs 3.14 (plan-review) composites inline.
- **Agile:** consider splitting EPIC-3-S3 into S3a (triggers) + S3b (kill switch + recovery + latency); note EPIC-2 deliberately straddles M1/M2; state the N2 WARN threshold (">1s").
- **SRE:** drop "independently" from the kill-switch description (it's one coupled boolean); add a "N entries removed since last view" notice so wrong-removals aren't pull-only; define the removed-log lifecycle (tracked vs gitignored, rotation); require the wrong-removal recovery procedure in SKILL.md; specify no-op-prune logging.
- **Backend:** add `os.fsync()` + a unique `.tmp` suffix; consider `read() -> BacklogDoc` (pydantic) over raw dict; define the `RemovalDecision` dataclass (the F9 log fields).
- **Security:** give `.shield/backlog-removed.log` a schema/parser + tracked-status decision; make dry-run/fixture mode provably non-destructive (force sweep off) + eval it; add a forward note that a future `migrate()` must be validate-or-refuse.
- **PM:** add coarse effort/impact per milestone (PM4); add a plain-language stakeholder/executive summary to the PRD (PM5); make the buy-vs-build case vs ClickUp/Jira explicit (PM6); quantify the operational cost the tool recovers as a falsifiable v1-audit target (PM10).

## Detailed agent findings

- [Backend Engineer](detailed/backend-engineer.md) — B− (the 3 P0s + 4 P1s)
- [DX Engineer](detailed/dx-engineer.md) — A−
- [Security Engineer](detailed/security-engineer.md) — A−
- [Agile Coach](detailed/agile-coach.md) — A−
- [SRE / Operations](detailed/sre.md) — A−
- [Product Manager (PM1–PM10)](detailed/product-manager.md) — A

## Recommendation

The plan is **Ready in substance** — strong scope discipline, testable ACs, an acyclic milestone DAG, clean trust boundaries, and an honest threat model. But do **not** start `/implement` until the **3 P0 contract fixes** land: they are the difference between a plan that reads consistently and one whose reconciler, epic-matching, and kill switch actually work against the real Shield artifacts. The P1s (recovery-mechanism choice, lost-update detection, packaging) are best folded in the same revision pass. Estimated effort: one focused editing pass on the TRD §11/§5, the reconciler/epic-suggester LLDs, EPIC-3-S3, and EPIC-4-S1/S2 — no story restructuring required.
