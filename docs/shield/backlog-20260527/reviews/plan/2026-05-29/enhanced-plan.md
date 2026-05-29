<!-- sidecar: ../../../plan.json -->
<!-- enhanced by /plan-review on 2026-05-29 — P0/P1 fixes folded into affected stories -->

# Plan — Shield Backlog (enhanced 2026-05-29)

**Project:** Shield · **Phase:** v1 · **Domain:** backend (Python)
**PRD:** [`prd.md`](../../../prd.md) (PRD-review **Ready**, composite 3.12) · **TRD:** [`trd.md`](../../../trd.md) · **Sidecar:** [`plan.json`](../../../plan.json)
**Plan-review:** Ready, composite 3.49 (B+) — conditional on the 3 P0 fixes below.

> **Changes applied in this enhanced version** (review 2026-05-29):
> - **P0-1 / P0-2 / P0-3** folded into EPIC-3-S2, EPIC-3-S3, EPIC-1-S1, and a new schema task.
> - **P1s** (recovery-OR resolution, lost-update detection, dup-id wording, name==slug, packaging, CI entrypoint, write-side + ordering-seam evals) folded into the affected stories.
> - P2s recorded as inline `[P2]` notes for the implementer to pick up opportunistically.

## Milestones

| ID | Name | Depends on | Touches LLD | Outcome |
|---|---|---|---|---|
| M1 | Capture + store + view | — | `backlog-store` | `backlog.json` + schema/validator; capture (user + skill, atomic, validate-or-refuse, lost-update detection); `/backlog` ordered view with manifest status badges; manual remove. |
| M2 | Feature + epic association + suggestion | M1 | `epic-suggester` | Every entry carries feature + epic; agent suggests via exact-normalized match against the pinned manifest/plan shapes; user accept/replace/create-new. |
| M3 | Promotion + reconciliation | M2 | `reconciler` | Promotion via transient reference; reconciliation engine (single "epic landed" predicate matching existing epics by **name**, never-remove-on-doubt, drift tolerance, removal logging); eager + lazy idempotent triggers + kill switch (incl. `.shield.json` schema change); eval suite + version bump. |

---

## EPIC-1 — Store, schema & capture  _(M1)_

### EPIC-1-S1 · Define backlog.json schema and validator _(high)_
Define `backlog.json` shape + JSON Schema with a top-level `schema_version`, plus a Python validator. Entry: `{id, order:int, kind∈{epic,story,task}, source∈{user,agent}, feature, epic, text}`.

- **Tasks:** author `shield/schema/backlog.schema.json`; `id` = `uuid4` string; document entry shape + migration policy (doc-only until `schema_version` 2) in `shield/skills/general/backlog/SKILL.md`; create `shield/scripts/validate_backlog.py`; ordering = single integer `order`.
  - **[P1-2 — fix]** Uniqueness of `id` across `entries[]` is enforced by **`validate_backlog.py`** (named error `duplicate_entry_id`), **not** by the JSON Schema — draft 2020-12 `uniqueItems` is whole-item equality and cannot express property-level uniqueness. Reword F2 + the AC accordingly.
  - **[P1-3 — fix]** Document the invariant **`manifest features[].name` == feature folder slug** (the reconciliation key) in the SKILL.md, since suggestion + reconciliation both rely on it.
  - **[P2]** State runtime prereqs once (Python ≥3.x via uv; validator uses pydantic + jsonschema).
- **AC:** schema rejects unknown `kind`/`source` (named error); **the validator** rejects duplicate `id` (`duplicate_entry_id`); `validate_backlog.py` exits 0/non-zero correctly; `schema_version` + migration policy present; `id` is a `uuid4` string.
- **Design:** [TRD §11 APIs Involved](../../../trd.md#apis-involved) · LLD [`backlog-store` §4 Data model](../../../lld-backlog-store.md#data-model)

### EPIC-1-S2 · Capture entrypoint (user + skill) with atomic write + lost-update detection _(high)_
Capture usable by the user (`/backlog add`) and any skill (documented `capture()` helper). Atomic temp-then-rename + validate-or-refuse.

- **Tasks:** `/backlog add` (assigns next `order` + `uuid4` id); **LOCKED** signature `capture(text, *, kind="task", feature=None, epic=None, source) -> str` in `shield/scripts/backlog_store.py`, raising `BacklogInvalid`; **LOCKED** single-writer (no lock) → full doc → `.tmp` → `os.replace()`.
  - **[P1-1 — fix]** Add **compare-before-replace**: `capture()`/`remove()` capture the on-disk `schema_version`+entry-count (or mtime/hash) at read time and refuse the `os.replace()` if the file changed underneath, raising `BacklogInvalid`. Converts a silent lost-update (the real N1/N5 threat) into a loud refusal **without a lockfile**.
  - **[P1-4 — fix]** Package `backlog_store` as an importable module with a `pyproject.toml` (F3 requires skills to import `capture()`); document the import path. Makes the EPIC-4-S2 version bump unconditional.
  - **[P2]** `os.fsync()` the temp fd before `os.replace()`; use a unique `.tmp` suffix (pid/uuid). Consider `read() -> BacklogDoc` (pydantic) over raw dict.
- **AC:** user + skill capture both work; interface documented + pinned in TRD §11; mid-write kill leaves no corruption; **a concurrent on-disk change between read and replace is refused with `BacklogInvalid` (no lost entry)**; malformed/partial read refused with `BacklogInvalid`.
- **Design:** [TRD §5 Functional Requirements](../../../trd.md#functional-requirements) · LLD [`backlog-store` §5 API contracts](../../../lld-backlog-store.md#api-contracts)

### EPIC-1-S3 · /backlog view — ordered list _(high)_
`/backlog` command + skill rendering entries sorted by `order` with feature + epic + source.
- **Tasks:** author `shield/commands/backlog.md` + `backlog/SKILL.md`; render sorted; define render-line format once; document a **provably non-destructive** local-dev/dry-run loop; empty-backlog message.
  - **[P2 — security]** Dry-run/fixture mode MUST force the lazy sweep off (the sweep runs on every real view) so testing a fixture can't mutate the project store.
- **AC:** ascending-`order` list with feature/epic/source; clean empty message; command registered; dry-run mode runs no sweep against the project store.
- **Design:** [TRD §4 Product Journey](../../../trd.md#product-journey)

### EPIC-1-S4 · Manual remove from /backlog _(medium)_
`/backlog remove <id>` — plain delete.
- **Tasks:** `remove <id>` via atomic helper; confirm-before-delete; clear error on absent id; document the recoverability boundary (uncommitted manual remove is unrecoverable by design — N4).
- **AC:** deletes + persists atomically; absent id = clear no-op error; no history retained.
- **Design:** [TRD §5 Functional Requirements](../../../trd.md#functional-requirements) · LLD [`backlog-store` §5 API contracts](../../../lld-backlog-store.md#api-contracts)

---

## EPIC-2 — Association & pipeline status  _(EPIC-2 deliberately straddles M1/M2 — see note)_

> **[P2 — agile]** EPIC-2-S1 (status badges) ships with the M1 view; EPIC-2-S2 (association + suggestion) is the M2 deliverable. This straddle is intentional, not a numbering slip.

### EPIC-2-S1 · Per-entry pipeline status from manifest.json _(high, M1)_
- **Tasks:** read manifest; render status badges; pin badge string `research ✓  prd ✓  plan –`; `not started` when feature absent; compute at view time.
  - **[P0-1 — fix]** Read against the **pinned manifest contract** (see TRD §11 addition): `manifest.json` = `{schema_version, features:[{name, artifacts:{research,prd,plan_json,...}}]}` — a list keyed by `name`, `plan_json` is a boolean flag, **no plan path stored**.
- **AC:** badges derived from the pinned manifest shape; prd-but-no-plan shows `prd ✓ plan –` and stays; absent feature → `not started`.
- **Design:** [TRD §7 High-Level Design](../../../trd.md#high-level-design)

### EPIC-2-S2 · Feature + epic association + agent suggestion _(high, M2)_
- **Tasks:** prompt/accept feature + epic (allow proposed-new); **LOCKED** exact-normalized match (`casefold()` + collapsed ws); suggest by scanning manifest + candidate plan.json; never block capture; tie → surface all, auto-pick none.
  - **[P0-1 — fix]** `suggest_feature(text, *, manifest)` and `suggest_epic(text, *, feature, plans)` are typed against the real shapes: `manifest.features[].name`; `plans` is `dict[feature-slug → parsed plan.json]`, the path derived as `docs/shield/<slug>/plan.json` for features with `artifacts.plan_json == true`.
  - **[P1-3 — fix]** `suggest_feature` returns `features[].name`, which **is** the folder slug (invariant pinned in EPIC-1-S1).
- **AC:** every entry has feature + epic; ≥1 feature + ≥1 epic candidate when matches exist; `auth` fixture surfaces `auth` top candidate + 2-way tie auto-picks neither; **a suggested feature value resolves to an existing `docs/shield/<value>/` path**; capture succeeds proposed-new when none.
- **Design:** [TRD §5 Functional Requirements](../../../trd.md#functional-requirements) · LLD [`epic-suggester` §5 API contracts](../../../lld-epic-suggester.md#api-contracts)

---

## EPIC-3 — Promotion & reconciliation  _(M3)_

### EPIC-3-S1 · User-driven promotion with transient reference _(high)_
`/backlog promote <id>` launches the user-chosen step and passes the entry id as a transient runtime reference — never stamped into `plan.json` (F6).
- **AC:** promotion starts the chosen step + forwards the reference; reference not persisted (F6); tool never auto-routes.
- **Design:** [TRD §4 Product Journey](../../../trd.md#product-journey)

> **Intra-epic dependency:** EPIC-3-S3 consumes EPIC-3-S1 + EPIC-3-S2 and lands after both.

### EPIC-3-S2 · Reconciliation engine (match key + never-remove-on-doubt) _(high)_
Locate feature in `manifest.json`; if it has a `plan.json`, apply the single **"epic landed" predicate** (F8).
- **Tasks:** `shield/scripts/reconcile_backlog.py`; never-remove-on-doubt; drift tolerance with logged warning; log every removal `{entry id, feature, epic, match-kind, triggering run, gating plan.json path}`.
  - **[P0-2 — fix]** Match key: **existing epic by normalized `name`** (NOT by `EPIC-N` id — ids are positional slots reassigned on every re-`/plan`, so id-matching breaks across re-plans). Proposed-new also by normalized name. `EPIC-N` is only a within-one-plan disambiguator. Story status never consulted.
  - **[P0-1 — fix]** `reconcile(entry, *, manifest: dict, plans: dict[str,dict]) -> RemovalDecision` — `manifest` is the parsed `{schema_version, features:[...]}`; `plans` maps feature-slug → parsed plan.json (path derived, not stored). Define the `RemovalDecision` dataclass carrying the F9 log fields **[P2]**.
- **AC:** removed only when an epic with **normalized-exact name** is present in `plan.json.epics[]` (story status not consulted); prd-only not removed; epic-name collision across two features → ambiguous → stays; **an epic reordered across a re-plan still resolves correctly**; malformed/old shapes → stays (logged), no exception; every removal emits the structured log line.
- **Design:** [TRD §7 High-Level Design](../../../trd.md#high-level-design) · LLD [`reconciler` §6 Sequence flows](../../../lld-reconciler.md#sequence-flows)

### EPIC-3-S3 · Eager + lazy removal triggers (idempotent) + kill switch _(high)_
Eager prune at end of promoted `/plan`/`/implement`; lazy sweep on view. Both idempotent; both call the one engine. Lands after S1 + S2.
- **Tasks:** eager prune hook; lazy sweep; idempotent remove-if-present + shared engine; debug-gated latency line.
  - **[P0-3 — fix]** Extend `shield/schemas/shield.schema.json` with an optional `backlog` object (`{auto_reconcile: bool, default true}`) + a config example — the current schema has `additionalProperties: false`, so the kill switch fails validation without this. (Reflected in the EPIC-4-S2 version bump.)
  - **[P1-1 (agile/sre) — fix]** Resolve the N4 recovery OR: **v1 default = `.shield/backlog-removed.log`** (append the entry *before* the destructive remove); commit-before-prune is an explicit non-goal. Update TRD §6 N4 + §14 step 2 to name the single mechanism.
  - **[P2 — sre]** Drop "independently" (one coupled boolean); surface "N entries removed since last view (see backlog-removed.log)" on view; define the removed-log lifecycle (gitignored, append-only, manual rotation); specify "no-op prune emits no log line"; state the N2 WARN threshold (">1s").
- **AC:** eager prune removes the referenced entry at end of run; lazy sweep removes plan-committed entries; second pass is a no-op (idempotent); shared engine; **`backlog.auto_reconcile=false` (now schema-valid) disables both**; **an end-of-run prune appends to `.shield/backlog-removed.log` before the remove; replaying the log restores the entry**; debug latency line reports view+sweep wall time.
- **Design:** [TRD §7 High-Level Design](../../../trd.md#high-level-design) · LLD [`reconciler` §8 Concurrency & state](../../../lld-reconciler.md#concurrency-and-state)

---

## EPIC-4 — Eval coverage & release  _(M3)_

### EPIC-4-S1 · Executable evals for the backlog lifecycle (RED→GREEN) _(high)_
- **Tasks:** fixtures (prd-only-stays, plan-committed-removed, ambiguous-stays via epic-name collision, malformed-stays, **re-planned-epic-reorder-still-resolves**, **manifest-from-real-schema**); evals for each behavior incl. duplicate-id rejection.
  - **[P1-1 — fix]** Concurrency eval asserts **detection**: a concurrent on-disk change between read and replace is refused (`BacklogInvalid`), no lost entry — not a race the design forbids.
  - **[P1 (security P1-b) — fix]** Write-side eval: `capture()` producing a schema-invalid doc raises `BacklogInvalid` and leaves backlog.json byte-unchanged (no `.tmp` promoted).
  - **[P1 (security P1-c) — fix]** Recovery-rehearsal eval asserts recoverability across a crash at the ordering seam (after log-append/before remove).
  - no-stamping eval (F6): plan.json + story records byte-unchanged after promotion.
  - **[P1 / DX P1 — fix]** Name the concrete CI entrypoint (the actual workflow file + runner under `shield/evals/` or `.github/workflows/`), not a task; path-filter glob `shield/{schema,scripts,skills/general/backlog}/**`, `shield/commands/backlog.md`.
- **AC:** suite covers all listed behaviors (incl. compare-before-replace detection, write-side refusal, ordering-seam recovery, re-plan epic-reorder); self-contained (no API/LLM); PR body has RED + GREEN; named CI runner runs on the glob.
- **Design:** [TRD §10 Milestones](../../../trd.md#milestones)

### EPIC-4-S2 · Version bump + command/skill docs _(medium)_
- **Tasks:** bump `marketplace.json` + `backlog_store` `pyproject.toml` (now **unconditional** per P1-4); finalize command/skill docs (capture, three triggers, kill switch, match key, manual remove, badges, **wrong-removal recovery procedure**); commit the `shield.schema.json` `backlog` change (P0-3); document a **fixed** audit interval + numeric trigger (PRD §7 thresholds); explicit DoD lines; CHANGELOG.
  - **[P2 — PM]** Add a plain-language stakeholder/executive summary to the PRD (PM5); make the buy-vs-build case vs ClickUp/Jira explicit (PM6); add coarse effort/impact per milestone (PM4); quantify the v1-audit target (PM10).
- **AC:** version bumped in same commit (incl. schema change); SKILL.md documents capture/view/promote/remove + 3 triggers + kill switch + audit cadence + recovery procedure; explicit DoD lines present; CHANGELOG mentions the feature.
- **Design:** [TRD §13 References](../../../trd.md#references)

---

## Carried forward + validate-the-bet
- The prior PRD-review carry-forwards (capture interface, schema_version, drift tolerance, idempotency) remain folded (EPIC-1-S1/S2, EPIC-3-S2/S3).
- PM10 decision unchanged: ship M1, validate the bet from `backlog.json`'s 30-day git history before investing in M2/M3.

## Next steps
- Fold the 3 P0s (+ the P1s) in one editing pass on TRD §11/§5, the reconciler/epic-suggester LLDs, EPIC-3-S2/S3, EPIC-1-S1/S2, EPIC-4-S1/S2. No story restructuring needed.
- Re-run `/plan-review` to confirm the P0s clear, then `/pm-sync` and `/implement` from M1.
