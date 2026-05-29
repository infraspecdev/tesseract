# Shield — Changelog

## 2.23.0 — 2026-05-29 — TRD rendering & generation fixes

### Fixed
- **TRD §10 milestone ordering**: milestones now render in dependency-topological
  then numeric order (M1, M2, … M16) instead of lexical order (M1, M10, M11, …).
- **Broken relative links in rendered HTML**: body links (plan.json, PRD, plan.md,
  images) rendered into `outputs/` are now rewritten by the md→out directory delta
  so they resolve correctly.

### Added
- **TRD §10 milestone→LLD links**: each milestone renders a "Detailed design:" line
  linking its `touches_lld[]` components to their `lld-<component>.md` drafts, plus
  an optional per-milestone `description`.
- **TRD §7 Mermaid diagrams**: `/plan` guidance now requires Mermaid (topology +
  sequence + boundary) instead of ASCII art.
- **TRD §13 LLD references** derived from `lld_components[]` with the draft→promote
  lifecycle note.

## 2.22.0 — 2026-05-29 — `/backlog` capture / view / promote / reconcile

### Added

- **`/backlog` command** — single global idea-capture sidecar at
  `docs/shield/backlog.json`. Each entry pairs an idea with a **feature**
  (the reconciliation key) and an **epic** (the removal gate); either may
  be proposed-new at capture. Subcommands: `view`, `add`, `remove`,
  `promote`, `sweep`. Promotion forwards the entry id as a **transient
  runtime arg** (`--backlog-ref`) — never stamped into `plan.json` (F6).
- **`shield-backlog` package** — importable module at
  `shield/backlog/shield_backlog/` with public API: `capture`,
  `read_backlog`, `remove`, `eager_prune`, `lazy_sweep`,
  `kill_switch_enabled`, `BacklogInvalid`. Skills can capture mid-task
  with `from shield_backlog import capture`.
- **LOCKED capture() signature** (TRD §11, plan-review 2026-05-27):
  `capture(text, *, kind='task', feature, epic, source) -> str` returning
  a uuid4. `source` is keyword-only and required.
- **Atomic write + compare-before-replace** — every write is full-doc →
  unique `.tmp` → `fsync` → `os.replace()`. A snapshot of `(schema_version,
  entry_count)` taken at read time is re-validated against the on-disk
  state just before the replace; a concurrent change raises
  `BacklogInvalid(lost_update)` (TRD §6 N1, plan-review 2026-05-29 P1).
- **Single reconciliation engine** — `reconcile(entry, *, manifest, plans)`
  in `shield_backlog.reconciler`. Match key is normalized-exact epic NAME
  for BOTH existing and proposed-new entries (plan-review P0-2); positional
  `EPIC-N` id is never a cross-plan key. Verdicts: `REMOVE` /
  `STAY_AMBIGUOUS` / `STAY_NO_MATCH` / `STAY_DOUBT`. Cross-feature epic
  name collisions and unrecognized manifest/plan shapes both result in
  `STAY_*` — never on doubt do we remove, never an exception.
- **Three removal triggers**: manual (`/backlog remove <id>`), eager prune
  (end of a promoted `/plan` or `/implement` run), and lazy sweep
  (`/backlog view` or `/backlog sweep`). Eager and lazy share the same
  engine and are idempotent.
- **Recovery log** — `.shield/backlog-removed.log` is appended **before**
  the destructive remove (ordering seam) for both eager and lazy paths.
  Manual removes do not log; recoverability there is bounded by
  `git revert` of committed state. The pre-remove entry is recoverable by
  replaying the log line through `capture()`.
- **Kill switch** — `.shield.json → backlog.auto_reconcile = false`
  disables eager prune and lazy sweep; manual `remove` continues to work.
  An additive `backlog` object in `shield/schemas/shield.schema.json`
  makes the flag schema-valid (plan-review 2026-05-29 P0-3).
- **`backlog.schema.json` 1.0** — top-level `schema_version` + `entries[]`
  with `{id (uuid4), order (int), kind (epic|story|task),
  source (user|agent), feature, epic, text}`. Uniqueness of `id` is
  enforced by `validate_backlog.py` (named error `duplicate_entry_id`),
  not by the schema (draft 2020-12 `uniqueItems` cannot express
  property-level uniqueness; plan-review 2026-05-29 P1-2).
- **Pipeline status badges** — `/backlog view` shows per-entry
  `research / prd / plan` flags read live from `manifest.json` artifact
  flags. Canonical badge string pinned in the backlog SKILL.md: `research ✓
  prd ✓  plan –`. A feature absent from manifest renders `not started`.
- **Eval coverage (mandatory per CLAUDE.md)** —
  `shield/evals/run-backlog.py` runs 17 end-to-end cases (capture,
  view+badges, manual remove, eager prune, idempotency, kill switch,
  lazy sweep, name-match-key, re-/plan epic reorder, cross-feature
  collision, malformed-shape, compare-before-replace, write-side refusal,
  F6 no-stamping, ordering-seam recovery rehearsal, validator
  duplicate-id). Gate wired in `.github/workflows/eval-backlog.yml` with
  a path-filter glob over backlog assets.
- **Recovery procedure documented** in `shield/skills/general/backlog/SKILL.md`:
  flip the kill switch, locate the F9 log line, replay the recovery log
  record.
- **Audit cadence** documented (monthly), with concrete numeric revisit
  triggers lifted from PRD §7: scope review if <70% of entries reach a
  terminal state within 30 days OR >20% sit untouched >60 days.

### Changed

- `shield/schemas/shield.schema.json` — added optional `backlog` object
  with `auto_reconcile: bool` (default `true`). The schema's top-level
  `additionalProperties: false` previously rejected the flag.

## 2.21.0 — 2026-05-28 — `/lld` command + Path B drafting + step 5h promotion + plan-sidecar 1.5 + LLD plan-review rules

### Added

- **`/lld <component>` command (Path A)** — generate or update a
  component-scoped Low-Level Design at `docs/lld/<component>.md`. Two
  templates (backend pinned to PR #43, infra adapted to declarative IaC),
  selected automatically per repo markers or via `--type` flag. Bare
  `/lld` lists undocumented components.
- **TRD-driven LLD authoring (Path B)** — `/plan` now derives an
  `lld_components[]` registry from stories' `design_refs[]` (where
  `doc=="lld"`), computes a persisted `milestones[].touches_lld[]` rollup
  per milestone, and emits feature-folder drafts at
  `docs/shield/{feature}/lld-{component}.md` via the new `lld-docs` skill.
- **`/implement` step 5h — milestone-close promotion** — when the last
  story of a milestone closes, /implement walks `touches_lld[]`, performs
  a fork-drift concurrency check (with auto-heal re-merge), appends §14
  Changelog rows tying back to story IDs, atomic-renames each draft to
  `docs/lld/{component}.md`, and back-fills `design_refs[].anchor_url`
  via a token-overlap heuristic with `[exact-match] | [heuristic] | [fallback]`
  match-type labels.
- **`plan-sidecar.schema.json` 1.5** — adds the `lld_components[]` registry
  (`{name, type, fork_blob_sha}`) at the root and the persisted
  `milestones[].touches_lld[]` field. Tightens `design_refs[]` so
  `component` is required when `doc=="lld"`. Older sidecars (1.0–1.4)
  remain valid for read.
- **`/plan-review` rules** — four new rules: `touches_lld_drift` (High),
  `lld_components_integrity` (High; covers missing-registry-entry, type-enum,
  duplicate-name, and `lld_fork_drift_uncaught`), `undocumented_lld`
  (Medium; canonical exists but anchor_url null), `lld_draft_review`
  (High/Medium/Review depending on what's missing).
- **Eval coverage** — `shield/evals/lld-docs.yaml` ships 3 positive
  fixtures (backend LLD, infra LLD, 1.5 plan.json), 6 Path B fixtures
  (happy/fork-drift-clean/fork-drift-conflict/backfill-exact/backfill-fallback/
  just-in-time), and 19 negative fixtures covering every named error.
  `.github/workflows/eval-lld.yml` runs the suite on every relevant PR.

### Changed

- `shield/skills/general/plan-docs/SKILL.md` — `/plan` flow includes the
  new Path B emission step (derive registry, compute rollup, draft per
  registry entry, capture fork_blob_sha).
- `shield/skills/general/implement-feature/SKILL.md` — adds step 5h
  (milestone-close promotion) after step 5f (last_aligned_with update).
- `shield/skills/general/plan-review/SKILL.md` — new rule entries 0f–0i
  for the LLD surface.
- `shield/schema/output-paths.yaml` — registers `lld_draft_md` and
  `lld_canonical_md`.

### Back-compat

- 1.4 sidecars without `lld_components[]` validate as 1.5 (missing arrays
  default to empty).
- 1.4 sidecars with `design_refs[].doc=="lld"` and `component==null` are
  caught by `/plan-review`'s `lld_components_integrity` rule (High); fix
  the affected refs before upgrading.
- Path A (`/lld <component>`) works against repos with no plan.json at
  all — reverse-doc use case is supported without setup.

### Spec

- Brainstorming spec: [`docs/superpowers/specs/2026-05-28-lld-command-design.md`](../docs/superpowers/specs/2026-05-28-lld-command-design.md).
- Implementation plans:
  - M1 — Foundation: [`docs/superpowers/plans/2026-05-28-lld-command-m1-foundation.md`](../docs/superpowers/plans/2026-05-28-lld-command-m1-foundation.md)
  - M2 — TRD-driven authoring + promotion: [`docs/superpowers/plans/2026-05-28-lld-command-m2-trd-driven.md`](../docs/superpowers/plans/2026-05-28-lld-command-m2-trd-driven.md)
  - M3 — Review wiring + cutover: [`docs/superpowers/plans/2026-05-28-lld-command-m3-review-and-cutover.md`](../docs/superpowers/plans/2026-05-28-lld-command-m3-review-and-cutover.md)

## 2.20.0 — 2026-05-25 — `/plan` TRD cutover + `/plan-review` TRD gates + `/pm-sync` design_refs forwarding + drift accountability

### Breaking

- `/plan` now emits a 14-section Technical Requirements Document at
  `{output_dir}/{feature}/trd.md` (rendered HTML at `outputs/trd.html`)
  **instead of** the legacy `plan-architecture.md`. The slug allow-list
  (`shield/schema/trd-sections.yaml`) is the source of truth.
- `plan.json` sidecar schema bumps **1.1 → 1.3** in this release:
  - **1.2** adds an optional `design_refs[]` array on each story (TRD/LLD/PRD
    pointers; LLD refs are `TODO` placeholders pending the `/lld` command).
  - **1.3** adds a top-level `last_aligned_with` field (40-char git SHA or
    `null`) for drift accountability.

### Backward-compatible

- Older `plan-architecture.md` files in existing feature folders are **never
  modified or deleted** by `/plan`. The cutover is forward-only; old folders
  remain readable.
- Schema 1.0 / 1.1 / 1.2 sidecars continue to validate. Forward-compat policy:
  `/plan-review` warns but does not reject sidecars with `version` newer than
  the current supported one; unknown top-level keys round-trip; unknown enum
  values still fail validation.
- Registry keys `plan_arch_md` / `plan_arch_html` remain declared in
  `shield/schema/output-paths.yaml` with `deprecated: true` for a transition
  window.

### Added — `/plan` TRD emission (M1)

- 14-section TRD template at
  `shield/skills/general/plan-docs/trd-template.md` with per-section
  backend/infra authoring guidance and worked `n/a — <reason>` examples.
- `shield/schema/trd-sections.yaml` — machine-readable slug allow-list (14
  entries) consumed by the validator and `/plan-review`.
- `shield/schema/plan-sidecar.schema.json` — JSON Schema draft 2020-12 for
  plan.json sidecars at version 1.3.
- `shield/scripts/validate_plan.py` — jsonschema-based validator invoked by
  `/plan-review` (first check) and the eval runner.
- `shield/scripts/validate_trd.py` — TRD format validator (presence, anchors,
  ordering, `n/a — <reason>` escape, vague-content detection, drift-by-addition).
- `shield/evals/run.py` + `shield/evals/plan-trd.yaml` + 19 fixtures
  (3 positive — backend / infra / mixed — and 16 negative — 14
  missing-section + 1 drift + 1 vague-TBD).
- `.github/workflows/eval-plan-trd.yml` — recurring CI gate that runs the
  eval on every PR touching the template, the schema, the validators, or the
  eval fixtures themselves.

### Added — `/plan-review` TRD gates (M2)

- Deterministic gates 0a–0e run **before** persona dispatch (see
  `shield/skills/general/plan-review/SKILL.md`):
  - **0a Schema validation** — `validate_plan.py` runs as the first check;
    rubric grading and TRD gates only run on schema-valid sidecars.
  - **0b TRD section presence** — `validate_trd.py` against `trd.md`; missing /
    vague / drift sections become Critical findings.
  - **0c Stale-anchor rule** — every `design_refs[]` with `doc: trd` is checked
    against the live TRD anchor set; stale refs surface as Critical findings.
  - **0d PRD↔TRD duplication** — TRD §2 and §5 are compared to the linked PRD
    for verbatim overlap longer than 80 characters.
  - **0e Implementation-manual rule** — TRD §7 code blocks > 20 lines without
    a populated §8 Alternatives Considered trigger the anti-pattern finding.
- Eval suite `shield/evals/plan-review-trd.yaml` with 5 fixtures
  (clean / stale-anchor / duplication / duplication-paraphrased / implementation-manual);
  5/5 cases pass and run in the same CI workflow.

### Added — `/pm-sync` design_refs forwarding (M2)

- All four PM adapters (ClickUp, Jira, Confluence, Notion) ship a uniform
  `forward_design_refs(task_id, refs) -> ForwardResult` from
  `shield_adapters_common` (under `shield/adapters/_common/`). Each adapter
  forwards every story's `design_refs[]` as web links on the synced task with
  a deterministic idempotency key `sha256(story_id + anchor_url)[:32]`:
  - Jira: `globalId` on `remote_issue_link`.
  - Confluence: `name` on `remote_link`.
  - ClickUp: companion text custom field `Shield Design Link Keys` for dedup.
  - Notion: rich-text property `Shield Link Keys` for dedup.
- Per-adapter idempotency test (`test_idempotency.py` / `test_forward_design_refs.py`)
  asserts running `/pm-sync` twice on the same plan produces zero duplicates.
- Structured observability: one `action_log` entry per ref
  (`action='forward_design_ref'`) with
  `{story_id, adapter, anchor_url, outcome, idempotency_key}`. Failures emit
  `action='forward_design_ref_failed'` with
  `{error_class, http_status, idempotency_key}`.

### Added — drift accountability (M3)

- Sidecar schema 1.3 introduces the top-level `last_aligned_with` field
  (40-char git SHA, or `null` until the first `/implement` close).
- `/implement` step 5f writes `last_aligned_with = HEAD` whenever a story
  closes; `/plan-review` and `/pm-sync` surface the value as an "Aligned with"
  line so reviewers can compare plan and code as of the same commit.

### Plugin versioning

- `.claude-plugin/marketplace.json` shield 2.19.0 → **2.20.0** (single bump
  for the full M1 + M2 + M3 cutover).
- `shield/adapters/clickup/pyproject.toml` 2.0.0 → **2.1.0** for the
  `design_refs[]` forwarding work.
- New adapter packages: `shield-adapters-common@0.1.0`,
  `shield-jira-adapter@0.1.0`, `shield-confluence-adapter@0.1.0`,
  `shield-notion-adapter@0.1.0`.
