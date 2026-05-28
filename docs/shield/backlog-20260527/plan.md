# Plan — Shield Backlog

**Project:** Shield · **Phase:** v1 · **Domain:** backend (Python)
**PRD:** [`./prd.md`](./prd.md) (reviewed **Ready**, composite 3.1) · **TRD:** [`./trd.md`](./trd.md) · **Sidecar:** `./plan.json`

<!-- [from: PM5] Add a 2–3 sentence plain-language executive summary atop trd.md and plan.md before the schema-/pipeline-heavy detail, for non-technical readers who hit these artifacts first. -->

A project-level Shield backlog: capture (user/agent) → user-driven promotion → reconciliation. Entries are removed when their work commits — eagerly at the end of a promoted `/plan` or `/implement` run, lazily on the `/backlog` view sweep, or manually. Matching is by feature (`manifest.json` index) + epic (`plan.json` gate); no ids are stamped.

> **Review note (P0 — gate 0d):** Before this plan ships, paraphrase TRD §2 so it no longer
> restates PRD §3 verbatim (current 92-char overlap exceeds the 80-char duplication threshold).
> Summarize the problem in technical-framing terms and link to PRD §3 instead of repeating it.
> <!-- [from: Deterministic gate 0d] -->

## Milestones

| ID | Name | Depends on | Outcome |
|---|---|---|---|
| M1 | Capture + store + view | — | `backlog.json` + schema/validator; capture (user + skill, atomic); `/backlog` ordered view with manifest status badges; manual remove. |
| M2 | Feature + epic association + suggestion | M1 | Every entry carries feature + epic (existing or proposed-new); agent suggests from manifest/plan; user accept/replace/create-new. |
| M3 | Promotion + reconciliation | M2 | Promotion via transient reference; reconciliation engine (match key, never-remove-on-doubt, drift tolerance); eager + lazy idempotent triggers; eval suite + version bump. |

---

## EPIC-1 — Store, schema & capture  _(M1)_

### EPIC-1-S1 · Define backlog.json schema and validator _(high)_
Define `backlog.json` shape + JSON Schema with a top-level `schema_version`, plus a Python validator. Entry: `{id, order:int, kind∈{epic,story,task}, source∈{user,agent}, feature, epic, text}`. `schema_version` is set now so future shape changes migrate read-old/write-new.
- **Tasks:** author `shield/schema/backlog.schema.json`; document entry shape + migration policy in `shield/skills/general/backlog/SKILL.md`; create `shield/scripts/validate_backlog.py`; ordering = single integer `order`.
  - <!-- [from: Backend P1-a] --> **Specify the `id` contract:** type (string), generation strategy (uuid4 / monotonic / slug — pick one and document it), and a schema-level **uniqueness** constraint across `entries[]`. Remove/promote/prune all key off `id`.
- **AC:** schema rejects unknown `kind` (named error); `validate_backlog.py` exits 0/non-zero correctly; `schema_version` + migration policy present; enums constrained.
  - <!-- [from: Backend P1-a] --> **+ AC:** schema rejects an `entries[]` array containing duplicate `id` values, naming the error.
  - <!-- [from: Backend P2-c] --> Either add a no-op `migrate(doc) -> doc` seam with a unit test, **or** reword the migration AC to "migration *policy* documented (doc-only until schema_version 2)" so it isn't mistaken for working code.
- **Design:** §11 APIs Involved · LLD `backlog-store` (TODO) <!-- [from: Agile P2] land or stub /lld backlog-store before sprint so this design_ref resolves -->

### EPIC-1-S2 · Capture entrypoint (user + skill) with atomic write _(high)_
Capture usable by the user (`/backlog add`) and any skill (documented write helper). Atomic temp-then-rename + validate-or-refuse so concurrent capture vs reconciliation can't corrupt the file. *Resolves PRD-review P1 (capture interface).*
- **Tasks:** `/backlog add` (assigns next `order`); skill-callable write helper (text, kind, feature?, epic?, source); atomic write; validate-or-refuse.
  - <!-- [from: Backend P1-b, DX P1 — LOCKED 2026-05-27] --> **Write-helper signature (locked):** `capture(text: str, *, kind: str = "task", feature: str | None = None, epic: str | None = None, source: str) -> str` in `shield/scripts/backlog_store.py`, raising `BacklogInvalid` on a malformed/partial store. Pinned in TRD §11; closes TRD §12 Q3. Every capturing skill builds against this.
  - <!-- [from: Backend P1-c, Security P1 — LOCKED 2026-05-27] --> **Concurrency (locked): single-writer assumption.** Shield is single-actor (N5), so v1 assumes one writer — no lock. Build full doc → `.tmp` → `os.replace()`; reads validate-or-refuse. Documented at TRD §6 N1, guarded by the interleaved capture/prune eval in EPIC-4-S1 (asserts no lost entry). Revisit with a lockfile only if Shield becomes multi-actor.
- **AC:** user + skill capture both work; interface documented; mid-write kill leaves no corruption; next `order`/default `kind` assigned.
  - <!-- [from: Security P1] --> **+ AC:** a malformed/partial `backlog.json` on read is **refused with a named error** (validate-or-refuse refusal path), never silently read or truncated.
- **Design:** §5 Functional Requirements · LLD `backlog-store` (TODO)

### EPIC-1-S3 · /backlog view — ordered list _(high)_
`/backlog` command + skill rendering entries sorted by `order` with feature + epic + source.
- **Tasks:** author `shield/commands/backlog.md` + `backlog/SKILL.md`; render sorted; empty-backlog message.
- **AC:** ascending-`order` list with feature/epic/source; clean empty message; command registered.
- **Design:** §4 Product Journey
<!-- [from: DX P2] Specify the badge render format once (EPIC-2-S1 shows 'research ✓ prd ✓ plan –' only as an example) and document a local-dev/dry-run loop in backlog SKILL.md. -->

### EPIC-1-S4 · Manual remove from /backlog _(medium)_
`/backlog remove <id>` — plain delete for ideas decided against / entries no run will clear.
- **Tasks:** `remove <id>` via atomic helper; confirm-before-delete; clear error on absent id.
- **AC:** deletes + persists atomically; absent id = clear no-op error; no history retained.
  - <!-- [from: Security P2/SE3] --> Note (doc): `git revert` recoverability (N4) covers only entries that reached a commit; a manual remove of an *uncommitted* entry is unrecoverable by design.
- **Design:** §5 Functional Requirements

---

## EPIC-2 — Association & pipeline status

### EPIC-2-S1 · Per-entry pipeline status from manifest.json _(high, M1)_
`/backlog` view shows each entry's feature pipeline status (research/prd/plan) read live from `manifest.json` — so "prd done, not yet planned" is visible without removal.
- **Tasks:** read manifest; render status badges per entry; `not started` when feature absent; compute at view time (no stored status).
- **AC:** badges derived from manifest; prd-but-no-plan shows `prd ✓ plan –` and stays; absent feature → `not started`.
- **Design:** §7 High-Level Design

### EPIC-2-S2 · Feature + epic association + agent suggestion _(high, M2)_
Associate every entry with a feature (reconciliation key) + epic (removal gate), either proposed-new; agent suggests feature (manifest) + epic (plan.json); user accept/replace/create-new.
- **Tasks:** prompt/accept feature + epic (allow proposed-new); suggest by scanning manifest + candidate plan.json; never block capture.
  - <!-- [from: DX P1, Agile P1, Backend P2-b — LOCKED 2026-05-27] --> **Match key (locked): exact normalized match, no ranking.** Normalize names with `casefold()` + collapsed whitespace; existing epic → by id, proposed-new → exact normalized name. A tie (≥2 matches) or no match → entry stays (never auto-pick). No fuzzy/token-overlap ranking in v1; suggestion surfaces exact-normalized candidates only. Specified in TRD §5 F7.
- **AC:** every entry has feature + epic; ≥1 feature + ≥1 epic candidate proposed when matches exist; capture succeeds with proposed-new when none.
  - <!-- [from: Agile P1] --> **+ measurable AC:** given a fixture manifest with feature `auth`, capturing text mentioning "auth" surfaces `auth` as the top candidate; a 2-way name tie surfaces both and auto-picks neither.
- **Design:** §5 Functional Requirements · LLD `epic-suggester` (TODO)

---

## EPIC-3 — Promotion & reconciliation  _(M3)_

### EPIC-3-S1 · User-driven promotion with transient reference _(high)_
`/backlog promote <id>` launches the user-chosen step (`/research`/`/prd`/`/plan`/`/implement`) and passes the entry id as a transient runtime reference — never stamped into `plan.json`.
- **Tasks:** `promote <id>` affordance; forward id as transient reference; document non-persistence; shippable work routes through `/plan`, direct `/implement` for rare planless one-offs.
- **AC:** promotion starts the chosen step + forwards the reference; reference not persisted to plan.json/stories; tool never auto-routes.
- **Design:** §4 Product Journey
<!-- [from: DX P2] Add an explicit intra-epic dependency note: EPIC-3-S3 (triggers) consumes both EPIC-3-S1 (transient reference) and EPIC-3-S2 (engine) and must land after them. -->

### EPIC-3-S2 · Reconciliation engine (match key + never-remove-on-doubt) _(high)_
Locate feature in `manifest.json`; if it has a `plan.json`, check the entry's epic. Match: existing epic → by id; proposed-new → by epic name. Ambiguity/no-match → entry stays. Unknown manifest/plan shapes → doubt (stays), never crash.
- **Tasks:** `shield/scripts/reconcile_backlog.py`; match key impl; never-remove-on-doubt; drift tolerance with logged warning.
  - <!-- [from: Backend P2-a] --> **State the "epic landed" gate as one precise predicate** and use it everywhere: "an entry is removed when an epic with the matching id (existing) or normalized name (proposed-new) is **present in `plan.json.epics[]`**; story `status` is **not** consulted." F7, the EPIC-3-S2 AC, and the schema currently word this three ways.
  - <!-- [from: SRE P1/OP1] --> **Log every removal with rationale** to a defined destination/format: `{entry id, feature, epic, match-kind (id|name), triggering run, gating plan.json path}`. Today only the never-remove-on-doubt path logs (N3); a confident-but-wrong removal must not be a silent git diff.
- **AC:** plan-committed epic selected for removal, prd-only not; id/name match per case; malformed/old shapes → entry stays (logged), no exception.
  - <!-- [from: Security P2] --> **+ fixture/AC:** epic-name collision across two different features → ambiguous → entry stays (the one place a wrong removal is plausible; PRD §10 risk / §14 trigger).
- **Design:** §7 High-Level Design · LLD `reconciler` (TODO)

### EPIC-3-S3 · Eager + lazy removal triggers (idempotent) _(high)_
Eager prune at end of promoted `/plan`/`/implement` (via the transient reference); lazy sweep on `/backlog` view. Both idempotent; both call the one reconciliation engine.
- **Tasks:** eager prune hook at end of `/plan` + `/implement`; lazy sweep on view; idempotent remove-if-present; shared engine.
  - <!-- [from: SRE P1/OP7] --> **Ship the kill switch.** Add a `.shield.json` flag (e.g. `backlog.auto_reconcile: false`) that disables eager prune and lazy sweep **independently**, leaving manual-remove only. §14 names this as the rollback fallback but no story currently delivers it — without it the documented mitigation is unactionable.
  - <!-- [from: SRE P1/OP4] --> **Close the uncommitted-state recovery gap.** Eager prune fires at end-of-run, possibly before `backlog.json` is committed, so `git revert` (N4) can't recover. Either commit `backlog.json` before the destructive prune, or append pruned entries to a transient `.shield/backlog-removed.log`.
  - <!-- [from: SRE P1/OP2,OP5] --> **Instrument the N2 ~1s budget.** Add a debug-gated latency line to `/backlog` view so "revisit if breached" (Q1 epic-index) is falsifiable, not "a human notices slowness."
- **AC:** promotion removes referenced entry at end of run (eager); sweep removes plan-committed entries (lazy); second pass is a no-op (idempotent); shared engine.
- **Design:** §7 High-Level Design · LLD `reconciler` (TODO)

---

## EPIC-4 — Eval coverage & release  _(M3)_

### EPIC-4-S1 · Executable evals for the backlog lifecycle (RED→GREEN) _(high)_
Per CLAUDE.md eval mandate: cover capture (user + skill), view + status, manual remove, eager prune, lazy sweep, match-key, never-remove-on-doubt.
- **Tasks:** fixtures (prd-only-stays, plan-committed-removed, ambiguous-stays, malformed-stays); evals for each behavior; wire into CI; capture RED + GREEN in PR.
  - <!-- [from: Backend P1-c, Security P1] --> **+ concurrency eval:** two interleaved captures (and a capture racing a reconciliation write) against the same `backlog.json` assert no corruption **and no lost entry** — the actual N1 threat, distinct from the crash-mid-write test.
  - <!-- [from: Security P1] --> **+ no-stamping eval (F6):** after promotion via `/plan`/`/implement`, assert `plan.json` and story records are **byte-unchanged**. F6 is the load-bearing trust boundary and is currently absent from the eval coverage list.
  - <!-- [from: SRE P2] --> **+ recovery-rehearsal eval:** after a simulated wrong removal, assert `git revert` / file-restore brings the entry back (exercises the N4 recovery path the plan relies on).
  - <!-- [from: DX P2] --> Name the CI entrypoint explicitly (which runner under `shield/evals/`) and the path-filter glob scoping "backlog assets" (e.g. `shield/{schema,scripts,skills/general/backlog}/**`, `shield/commands/backlog.md`).
- **AC:** eval suite under `shield/evals/` covers all behaviors; self-contained (no API/LLM); PR body has RED + GREEN; CI runs on backlog-asset PRs.
- **Design:** §10 Milestones

### EPIC-4-S2 · Version bump + command/skill docs _(medium)_
Bump the Shield plugin version (marketplace.json + pyproject where touched) in the same commit as asset changes; finalize `/backlog` + backlog SKILL.md docs.
- **Tasks:** bump `marketplace.json`; bump touched `pyproject.toml`; finalize command/skill docs (capture, triggers, match key, manual remove, badges); CHANGELOG.
  - <!-- [from: Agile P2] --> Add explicit DoD lines: "PR reviewed and merged" and "marketplace version published" so 'done' is unambiguous.
  - <!-- [from: SRE P2] --> Document the manual `/backlog` audit cadence (e.g. monthly) and which §7 reading triggers action — the single owner needs a concrete on-call procedure, not "periodic."
- **AC:** version bumped in same commit; command + SKILL document capture/view/promote/remove + 3 triggers; CHANGELOG mentions the feature.
- **Design:** §13 References

---

## Validate the bet from v1 data _(P1 — PM10, decided 2026-05-27)_

<!-- [from: PM10 — decided: validate from v1 data, no pre-build gate] -->
No pre-build baseline gate. The load-bearing assumption (PRD §10: lost future-work volume is
high enough to justify the tool) is **accepted for v1** and validated *after* M1 ships, from
`backlog.json`'s own add/remove git history over the first 30 days (the §7 success metric). If
that data shows the backlog isn't earning its keep, revisit scope before investing further in
M2/M3.

---

## Carried forward from PRD-review (Ready, run _2)
- Capture-from-skill interface defined → **EPIC-1-S2** / TRD §11. _(Review note: still open as TRD §12 Q3 — P1 #1 closes it.)_
- `backlog.json` `schema_version` + migration → **EPIC-1-S1** / TRD §9.
- Reconciliation read-contract drift tolerance → **EPIC-3-S2** / TRD §6 N3.
- Eager-prune + lazy-sweep idempotency → **EPIC-3-S3** / TRD §5 F8.

## Next steps
- `/pm-sync` — sync epics + stories to ClickUp.
- `/implement` — begin TDD implementation (start at M1 / EPIC-1-S1 once the P0 doc-fix and the EPIC-1 P1s are folded in).
