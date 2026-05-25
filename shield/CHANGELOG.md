# Shield — Changelog

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
