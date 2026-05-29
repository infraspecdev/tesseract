<!-- sidecar: ./plan.json -->

# Plan — Shield Backlog

**Project:** Shield · **Phase:** v1 · **Domain:** backend (Python)
**PRD:** [`./prd.md`](./prd.md) (reviewed **Ready**, composite 3.12) · **TRD:** [`./trd.md`](./trd.md) · **Sidecar:** `./plan.json`

A project-level Shield backlog: capture (user/agent) → user-driven promotion → reconciliation. Entries are removed when their work commits — eagerly at the end of a promoted `/plan` or `/implement` run, lazily on the `/backlog` view sweep, or manually. Matching is by feature (`manifest.json` index) + epic (`plan.json` gate); no ids are stamped. This re-plan folds the 2026-05-27 plan-review findings (P0 gate-0d, the P1/P2 set) into the stories and adds the previously-deferred 14-section TRD plus three component LLD drafts.

## Milestones

| ID | Name | Depends on | Touches LLD | Outcome |
|---|---|---|---|---|
| M1 | Capture + store + view | — | `backlog-store` | `backlog.json` + schema/validator; capture (user + skill, atomic, validate-or-refuse); `/backlog` ordered view with manifest status badges; manual remove. |
| M2 | Feature + epic association + suggestion | M1 | `epic-suggester` | Every entry carries feature + epic (existing or proposed-new); agent suggests via exact-normalized match; user accept/replace/create-new. |
| M3 | Promotion + reconciliation | M2 | `reconciler` | Promotion via transient reference; reconciliation engine (single "epic landed" predicate matching by epic **name**, never-remove-on-doubt, drift tolerance, removal logging); eager + lazy idempotent triggers + kill switch (incl. `shield.schema.json` `backlog` key); eval suite + version bump. |

LLD drafts emitted by this plan (feature-folder, net-new): [`lld-backlog-store.md`](./lld-backlog-store.md), [`lld-epic-suggester.md`](./lld-epic-suggester.md), [`lld-reconciler.md`](./lld-reconciler.md).

---

## EPIC-1 — Store, schema & capture  _(M1)_

### EPIC-1-S1 · Define backlog.json schema and validator _(high)_
Define `backlog.json` shape + JSON Schema with a top-level `schema_version`, plus a Python validator. Entry: `{id, order:int, kind∈{epic,story,task}, source∈{user,agent}, feature, epic, text}`. `schema_version` is set now so future shape changes migrate read-old/write-new.

- **Tasks:** author `shield/schema/backlog.schema.json`; specify the `id` contract (`uuid4` string; uniqueness across `entries[]` enforced by the **validator**, not the JSON Schema — P1-2 — since draft 2020-12 can't express property-level array uniqueness); document entry shape, migration policy, and the **`manifest features[].name` == folder-slug** invariant (P1-3) in `shield/skills/general/backlog/SKILL.md`; create `shield/scripts/validate_backlog.py`; ordering = single integer `order`; migration is doc-only until `schema_version` 2.
- **AC:** schema rejects unknown `kind` (named error); **the validator** rejects duplicate `id` values (`duplicate_entry_id`); `validate_backlog.py` exits 0/non-zero correctly; `schema_version` + migration policy + name==slug invariant documented; enums constrained; `id` is a `uuid4` string.
- **Design:** [§11 APIs Involved](./trd.md#apis-involved) · LLD [`backlog-store` §4 Data model](./lld-backlog-store.md#data-model)

### EPIC-1-S2 · Capture entrypoint (user + skill) with atomic write _(high)_
Capture usable by the user (`/backlog add`) and any skill (documented `capture()` write helper). Atomic temp-then-rename + validate-or-refuse so concurrent capture vs reconciliation can't corrupt the file. *Resolves PRD-review P1 (capture interface); closes TRD §12 Q3.*

- **Tasks:** `/backlog add` (assigns next `order` + `uuid4` id); **LOCKED** write-helper signature `capture(text: str, *, kind: str = "task", feature: str | None = None, epic: str | None = None, source: str) -> str` in `shield/scripts/backlog_store.py`, raising `BacklogInvalid` (pinned TRD §11); **LOCKED** single-writer (no lock) → full doc → `.tmp` → `os.replace()` (TRD §6 N1); **+ compare-before-replace** (P1-1/security): refuse `os.replace()` if the on-disk store changed since read → loud `BacklogInvalid`, no lost entry; **package `backlog_store`** with a `pyproject.toml` (P1-4 — skills import `capture()`); validate-or-refuse on read **and** write.
- **AC:** user + skill capture both work; interface documented + pinned in TRD §11; mid-write kill leaves no corruption; **a concurrent on-disk change between read and replace is refused with `BacklogInvalid` (no lost entry)**; next `order`/`uuid4` id/default `kind` assigned; malformed/partial `backlog.json` on read is **refused with `BacklogInvalid`**, never silently read or truncated.
- **Design:** [§5 Functional Requirements](./trd.md#functional-requirements) · LLD [`backlog-store` §5 API contracts](./lld-backlog-store.md#api-contracts)

### EPIC-1-S3 · /backlog view — ordered list _(high)_
`/backlog` command + skill rendering entries sorted by `order` with feature + epic + source.

- **Tasks:** author `shield/commands/backlog.md` + `backlog/SKILL.md`; render sorted by `order`; define the per-entry render-line format once in the SKILL.md (canonical badge string lives in EPIC-2-S1) so every view path renders identically; document a local-dev/dry-run loop; empty-backlog message.
- **AC:** ascending-`order` list with feature/epic/source; clean empty message; command registered; render-line format documented once and reused.
- **Design:** [§4 Product Journey](./trd.md#product-journey)

### EPIC-1-S4 · Manual remove from /backlog _(medium)_
`/backlog remove <id>` — plain delete for ideas decided against / entries no run will clear.

- **Tasks:** `remove <id>` via atomic helper; confirm-before-delete; clear error on absent id; document the recoverability boundary (git revert covers only committed entries; uncommitted manual remove is unrecoverable by design — N4).
- **AC:** deletes + persists atomically; absent id = clear no-op error; no history retained; uncommitted-entry recoverability caveat documented.
- **Design:** [§5 Functional Requirements](./trd.md#functional-requirements) · LLD [`backlog-store` §5 API contracts](./lld-backlog-store.md#api-contracts)

---

## EPIC-2 — Association & pipeline status

### EPIC-2-S1 · Per-entry pipeline status from manifest.json _(high, M1)_
`/backlog` view shows each entry's feature pipeline status (research/prd/plan) read live from `manifest.json` — so "prd done, not yet planned" is visible without removal.

- **Tasks:** read manifest; render status badges per entry; pin the canonical badge string `research ✓  prd ✓  plan –` in the SKILL.md; `not started` when feature absent; compute at view time (no stored status).
- **AC:** badges derived from manifest using the pinned string; prd-but-no-plan shows `prd ✓ plan –` and stays; absent feature → `not started`.
- **Design:** [§7 High-Level Design](./trd.md#high-level-design)

### EPIC-2-S2 · Feature + epic association + agent suggestion _(high, M2)_
Associate every entry with a feature (reconciliation key) + epic (removal gate), either proposed-new; agent suggests feature (manifest) + epic (plan.json); user accept/replace/create-new.

- **Tasks:** prompt/accept feature + epic (allow proposed-new); **LOCKED** match key = exact normalized (`casefold()` + collapsed whitespace); **UPDATED (P0-2): both existing and proposed-new epics match by exact normalized NAME** (epic id `EPIC-N` is a positional within-plan slot, not a cross-plan key), no fuzzy ranking (TRD §5 F7/F8); suggestion typed against the real shapes (P0-1): `suggest_feature` reads `manifest.features[].name`, `suggest_epic` reads `plans[feature].epics[]` (plans = `dict[slug→plan]`, path derived); never block capture; a tie (≥2 matches) surfaces all and auto-picks none.
- **AC:** every entry has feature + epic; ≥1 feature + ≥1 epic candidate proposed when matches exist; `auth` fixture surfaces `auth` top candidate + 2-way tie auto-picks neither; **a suggested feature value resolves to an existing `docs/shield/<value>/` path**; capture succeeds with proposed-new when none.
- **Design:** [§5 Functional Requirements](./trd.md#functional-requirements) · LLD [`epic-suggester` §5 API contracts](./lld-epic-suggester.md#api-contracts)

---

## EPIC-3 — Promotion & reconciliation  _(M3)_

### EPIC-3-S1 · User-driven promotion with transient reference _(high)_
`/backlog promote <id>` launches the user-chosen step (`/research`/`/prd`/`/plan`/`/implement`) and passes the entry id as a transient runtime reference — never stamped into `plan.json`.

- **Tasks:** `promote <id>` affordance; forward id as transient reference; document non-persistence; shippable work routes through `/plan`, direct `/implement` for rare planless one-offs.
- **AC:** promotion starts the chosen step + forwards the reference; reference not persisted to plan.json/stories (F6); tool never auto-routes.
- **Design:** [§4 Product Journey](./trd.md#product-journey)

> **Intra-epic dependency:** EPIC-3-S3 (triggers) consumes both EPIC-3-S1 (transient reference) and EPIC-3-S2 (engine) and must land after them.

### EPIC-3-S2 · Reconciliation engine (match key + never-remove-on-doubt) _(high)_
Locate feature in `manifest.json`; if it has a `plan.json`, apply the single **"epic landed" predicate** (TRD §5 F8): remove iff an epic with the matching **normalized-exact name** is **present in `plan.json.epics[]`** — story `status` is never consulted. Ambiguity/no-match → entry stays. Unknown manifest/plan shapes → doubt (stays), never crash.

- **Tasks:** `shield/scripts/reconcile_backlog.py` with `reconcile(entry, *, manifest: dict, plans: dict[str,dict]) -> RemovalDecision` (pure fn; manifest = list-keyed `features[]`, `plans` = `{slug→plan}` with path **derived** — P0-1); **UPDATED (P0-2)** match key = epic by casefold+collapsed-ws exact **name** for both existing and proposed-new (never by positional `EPIC-N` id; a re-planned reorder must still resolve); tie/no-match → stays; story status never consulted; never-remove-on-doubt; drift tolerance with logged warning; define `RemovalDecision` + **log every removal** `{entry id, feature, epic, match-kind (name), triggering run, gating plan.json path}`.
- **AC:** removed only when an epic with normalized-exact **name** is present in `plan.json.epics[]` (story status not consulted), prd-only not; **a re-planned epic reorder (same name, new `EPIC-N`) still resolves**; epic-name collision across two features → ambiguous → entry stays; malformed/old shapes → entry stays (logged), no exception; every removal emits the structured log line.
- **Design:** [§7 High-Level Design](./trd.md#high-level-design) · LLD [`reconciler` §6 Sequence flows](./lld-reconciler.md#sequence-flows)

### EPIC-3-S3 · Eager + lazy removal triggers (idempotent) + kill switch _(high)_
Eager prune at end of promoted `/plan`/`/implement` (via the transient reference); lazy sweep on `/backlog` view. Both idempotent; both call the one reconciliation engine. Ships the kill switch and closes the uncommitted-state recovery gap. *Lands after EPIC-3-S1 + EPIC-3-S2.*

- **Tasks:** eager prune hook at end of `/plan` + `/implement`; lazy sweep on view; idempotent remove-if-present + shared engine; **kill switch** `.shield.json` `backlog.auto_reconcile` (default true) disabling eager + lazy (§14 rollback fallback) — **requires an additive `backlog` object in `shield/schemas/shield.schema.json`** (P0-3; current schema is `additionalProperties:false`); **RESOLVED (P1-1)** the single recovery mechanism is append-to-`.shield/backlog-removed.log` **before** the destructive prune (commit-before-prune is a non-goal); no-op prune writes no log/recovery record; **instrument the N2 ~1s budget** with a debug-gated latency line (WARN > 1s).
- **AC:** promotion removes referenced entry at end of run (eager); sweep removes plan-committed entries (lazy); second pass is a no-op (idempotent); shared engine; `backlog.auto_reconcile=false` (now schema-valid) disables both, leaving manual-remove; **end-of-run prune appends to `.shield/backlog-removed.log` before remove; replay restores the entry**; debug latency line reports view+sweep wall time + WARN above 1s.
- **Design:** [§7 High-Level Design](./trd.md#high-level-design) · LLD [`reconciler` §8 Concurrency & state](./lld-reconciler.md#concurrency-and-state)

---

## EPIC-4 — Eval coverage & release  _(M3)_

### EPIC-4-S1 · Executable evals for the backlog lifecycle (RED→GREEN) _(high)_
Per CLAUDE.md eval mandate: cover capture (user + skill), view + status, manual remove, eager prune, lazy sweep, match-key, never-remove-on-doubt, concurrency (no lost entry), no-stamping (F6), recovery-rehearsal.

- **Tasks:** fixtures **from the real artifact schemas** (P0-1: list-keyed `manifest.features[]`, boolean `plan_json` flag) covering prd-only-stays, plan-committed-removed, ambiguous-stays (epic-name collision across features), malformed-stays, **re-planned-epic-reorder-still-resolves** (same name, new `EPIC-N` — P0-2); evals incl. duplicate-id rejection; **concurrency/lost-update eval** (P1-1: a concurrent on-disk change between read and `os.replace()` is refused with `BacklogInvalid` — no corruption, no lost entry); **write-side eval** (P1-b: `capture()` producing a schema-invalid doc refuses, byte-unchanged); **no-stamping eval (F6)**; **recovery-rehearsal eval** (P1-c: crash at the ordering seam — after log-append, before remove — still recoverable via replay); name a **concrete CI entrypoint** (the actual workflow file + runner) + path-filter glob (`shield/{schema,scripts,skills/general/backlog}/**`, `shield/commands/backlog.md`).
- **AC:** suite under `shield/evals/` covers all listed behaviors (incl. re-plan reorder, lost-update detection, write-side refusal, ordering-seam recovery); fixtures use real manifest/plan shapes; self-contained (no API/LLM); PR body has RED + GREEN; the named CI workflow runs on the backlog-asset glob.
- **Design:** [§10 Milestones](./trd.md#milestones)

### EPIC-4-S2 · Version bump + command/skill docs _(medium)_
Bump the Shield plugin version (marketplace.json + pyproject where touched) in the same commit as asset changes; finalize `/backlog` + backlog SKILL.md docs.

- **Tasks:** bump `marketplace.json`; bump `backlog_store` `pyproject.toml` (**unconditional** — P1-4, it's a packaged module); commit the `shield/schemas/shield.schema.json` `backlog` change (P0-3) in the same commit; finalize command/skill docs (capture, three triggers, kill switch, **name** match key, manual remove, badges, **wrong-removal recovery procedure**); document a **fixed monthly** `/backlog` audit with the concrete PRD §7 revisit triggers (<70% terminal in 30d, or >20% untouched >60d); add explicit DoD lines ("PR reviewed and merged", "marketplace version published"); CHANGELOG.
- **AC:** version bumped in `marketplace.json` + `backlog_store` `pyproject.toml` and the `shield.schema.json` change committed, all in one commit; command + SKILL document capture/view/promote/remove + 3 triggers + kill switch + recovery procedure + fixed monthly audit with numeric triggers; explicit DoD lines present; CHANGELOG mentions the feature.
- **Design:** [§13 References](./trd.md#references)

---

## Validate the bet from v1 data  _(P1 — PM10, decided 2026-05-27)_

No pre-build baseline gate. The load-bearing assumption (PRD §10: lost future-work volume is high enough to justify the tool) is **accepted for v1** and validated *after* M1 ships, from `backlog.json`'s own add/remove git history over the first 30 days (the §7 success metric). If that data shows the backlog isn't earning its keep, revisit scope before investing further in M2/M3.

## Carried forward from PRD-review (Ready, run _2)
- Capture-from-skill interface defined → **EPIC-1-S2** / TRD §11 (closed — F3 signature locked).
- `backlog.json` `schema_version` + migration → **EPIC-1-S1** / TRD §9.
- Reconciliation read-contract drift tolerance → **EPIC-3-S2** / TRD §6 N3.
- Eager-prune + lazy-sweep idempotency → **EPIC-3-S3** / TRD §5 F9.

## Next steps
- `/plan-review` — re-run multi-agent review on the refreshed plan + new TRD.
- `/pm-sync` — sync epics + stories to ClickUp.
- `/implement` — begin TDD implementation at M1 / EPIC-1-S1.
