# Shield `/pm-sync` Sidecar Refactor — Design

**Status:** Draft for review
**Date:** 2026-05-26
**Owner:** ashwinimanoj
**Tracking:** EPIC-4-S3 (partial — sidecar-driven sync scope only; `design_refs[]` forwarding deferred)

## 1. Problem

`/pm-sync` cannot ingest the current `plan.json` sidecar. The ClickUp adapter's `pm_sync` MCP tool routes through `get_parser(config.plan_docs.format)`, which only supports `"html"` and `"markdown"`. Three independent symptoms confirm the dead path:

1. The default `plan_docs.format` falls back to `"json"`, which raises `ValueError("Unknown plan doc format: 'json'. Supported: html, markdown")` at the parser factory.
2. The markdown parser is a `NotImplementedError` stub.
3. The HTML parser expects `<div class="story" id="story-N">` markup; `/plan`'s rendered HTML produces `id="epic-X-sY-..."` heading anchors with zero `div.story` elements.

Consequence: no one with a current `/plan`-produced sidecar can run `/pm-sync` end-to-end. The skill's documented "read plan.json" contract has no implementation behind it.

Partial scaffolding already exists for the follow-on work (`shield/adapters/_common/shield_adapters_common/design_refs.py`, `shield/adapters/clickup/server/tools/forward_design_refs.py`, idempotency tests), but it has no caller — the orchestration step that would invoke it requires sidecar-driven sync to exist first.

## 2. Goals

- `/pm-sync` reads `plan.json` directly as the source of truth for milestones, epics, and stories.
- First sync creates epic tasks in the configured ClickUp "epics" list and story tasks in the "backlog" list, linked via the existing `Epic <> Story` relationship custom field.
- Subsequent syncs are idempotent: epics + stories with `pm_id` set are recognised as existing and skipped (or updated only for drift).
- All PM tool linkage state (`pm_id`, `pm_url`) lives in `plan.json`. `pm.json` is configuration only.
- Parser code lives in a top-level `shield/parsers/` package importable from anywhere in Shield.
- ClickUp adapter's existing 8 tests stay green throughout the refactor.

## 3. Non-Goals

- Forwarding `design_refs[]` to PM tools as web links. The forwarder exists; wiring it into the orchestration path waits for EPIC-2-S1 (schema 1.2 with `design_refs[]`) + EPIC-2-S2 (populator).
- Jira / Confluence / Notion implementations of the sidecar sync interface. Their scaffolding lands in EPIC-4-S0.
- A reusable `shield/skills/general/test-coverage/` skill. Factoring deferred to a follow-up PR (skill-last sequencing).
- Auto-rebuild of `manifest.json` via post-write hook. Out of scope for sync work.
- An `index.html` "PM sync status" column. Additive future enhancement.

## 4. Architecture

### 4.1 New top-level package: `shield/parsers/`

A uv package, sibling to `shield/adapters/`, importable as `shield_parsers`:

```
shield/parsers/
├── pyproject.toml                       # package: shield_parsers
├── shield_parsers/
│   ├── __init__.py                      # re-exports: load_plan, save_plan, Plan, Epic, Story, ...
│   └── sidecar.py                       # plan.json reader/writer + typed dataclasses
└── tests/
    ├── conftest.py
    └── test_sidecar.py
```

`shield_parsers.sidecar` owns the canonical mapping from `plan.json` on disk to typed Python objects (`Plan`, `Milestone`, `Epic`, `Story`, `DesignRef`) and back. It uses `shield/schema/plan-sidecar.schema.json` for validation. Consumers: ClickUp adapter, future Jira/Confluence/Notion adapters, `validate_plan.py`, `/plan-review`'s TRD section checks.

Dependency direction: `shield/adapters/clickup/` depends on `shield/parsers/`. `shield/parsers/` depends on nothing inside Shield except the JSON Schema file. No circular deps.

### 4.2 ClickUp adapter changes

**Deleted** (sidecar-only sync — Section 5 of the brainstorm rationale):

```
shield/adapters/clickup/server/parsers/         # whole directory
├── base.py                                     # PlanParser ABC, get_parser factory
├── html_parser.py                              # CSS-selector HTML extractor
└── markdown_parser.py                          # NotImplementedError stub
```

**Modified:**

| File | Change |
|---|---|
| `server/config.py` | Drop `PlanDocsConfig.format`, `.base_path`, `.epics[].plan_doc`; drop `StoryExtractionConfig` and `HtmlExtractionConfig`. |
| `server/tools/sync.py` | Rewrite. Source stories from `plan.json` via `shield_parsers.sidecar`, not `get_parser`. Rename tool to `pm_sync_sidecar`. |
| `server/tools/bulk_create.py` | Accept typed `Epic` / `Story` lists; permit creating epics in `lists.epics.id` and stories in `lists.backlog.id` in the same tool. |
| `pm.json` shape | Drop `epics[]` and `plan_docs` blocks; keep `space`, `folder`, `lists`, `relationship_field`, `naming`. |

### 4.3 Schema change: `plan.json` 1.3 → 1.4

`shield/schema/plan-sidecar.schema.json`: add `pm_id` and `pm_url` (both nullable, optional) to the `Epic` object, mirroring what `Story` already has. `shield/skills/general/plan-docs/sidecar-schema.md` bumps the version reference and adds the two fields to the Epic example.

**Migration policy:**

- `shield_parsers.sidecar.load_plan()` reads any version ≥ 1.0 silently. Missing `pm_id`/`pm_url` defaults to `null` on both Epic and Story.
- `shield_parsers.sidecar.save_plan()` always writes `version: "1.4"`.
- Unknown top-level and per-object keys round-trip (forward-compat for fields added in future minor versions).
- A plan at `version: "2.0"` or higher raises `SchemaVersionTooNew` — no silent upgrade across major versions.
- Constants exported: `CURRENT_SCHEMA_VERSION = "1.4"`, `MIN_SUPPORTED_VERSION = "1.0"`.

## 5. Sync pipeline orchestration

End-to-end `/pm-sync` flow, sidecar-driven, `plan.json` owns all PM state.

### 5.1 Trigger surface (skill: `shield/skills/pm-sync/SKILL.md`)

1. User invokes `/pm-sync`.
2. Skill reads `.shield.json` → `output_dir` (default `docs/shield`).
3. Skill globs `{output_dir}/*/plan.json`:
   - 0 plans → error + offer `/plan`
   - 1 plan → use it
   - 2+ plans → AskUserQuestion picker
4. Skill loads the chosen plan via `shield_parsers.sidecar.load_plan(path)` — surfaces named schema errors if invalid.
5. Skill calls `pm_get_capabilities()` and verifies `pm_sync_sidecar` is advertised.

### 5.2 Read step — new MCP tool `pm_sync_sidecar(feature, epic=None)`

Pure read, no mutations. Returns a diff structure:

```python
{
    "epics": [
        {
            "id": "EPIC-1",
            "name": "TRD generation and storage",
            "pm_id": None,
            "diff": "to_create",          # to_create | match | to_update | to_link | orphan
            "candidate": None,             # populated for to_link with fuzzy_ratio
        },
        ...
    ],
    "stories": [
        {
            "id": "EPIC-1-S1",
            "epic_id": "EPIC-1",
            "name": "Author the canonical 14-section TRD template...",
            "pm_id": None,
            "diff": "to_create",
            "candidate": None,
        },
        ...
    ],
    "summary": {
        "epics":   {"match": 0, "to_create": 5,  "to_update": 0, "to_link": 0, "orphan": 0},
        "stories": {"match": 0, "to_create": 16, "to_update": 0, "to_link": 0, "orphan": 0}
    },
    "orphans_in_clickup": []
}
```

Matching logic:
- By `pm_id` when non-null on plan.json side and the task exists in ClickUp → `match` (or `to_update` if names drifted).
- Fuzzy name match ≥ 0.8 → `match`; backfill `pm_id` on the next save.
- Fuzzy match 0.6–0.8 → `to_link`; ambiguous, surfaces in the user's confirmation table.
- No match → `to_create`.

### 5.3 Present step (skill)

Skill renders the diff as two side-by-side tables (epics + stories) and asks: apply all / pick which / cancel.

### 5.4 Write step (skill calls existing MCP tools)

**Epic-first, two phases:**

```
Phase 1 — Epics
  For each epic with diff=to_create:
    pm_bulk_create(list_id=lists.epics.id, stories=[{name: "EPIC-1: TRD generation...", ...}])
    Backfill epic.pm_id and epic.pm_url in the in-memory Plan object
  For each epic with diff=to_update:
    pm_bulk_update(updates=[{task_id: epic.pm_id, name: <updated>}])
  For each epic with diff=to_link:
    pm_link_story_to_epic(...) — confirm with user first

Phase 2 — Stories
  Every epic now has a pm_id (existing or just-backfilled).
  For each story with diff=to_create:
    pm_bulk_create(
      list_id=lists.backlog.id,
      stories=[{
        name: "[SHIELD] EPIC-1-S1: Author the canonical...",      # from naming.story_format
        description: <markdown body>,
        epic_id: <epic.pm_id>,
        orderindex: <sequence * 1000>
      }],
      set_relationships=true                                       # links via Epic <> Story field
    )
    Backfill story.pm_id and story.pm_url
  For each story with diff=to_update:
    pm_bulk_update(...)
```

### 5.5 Persist step (skill)

1. Save plan.json — atomic write via `shield_parsers.sidecar.save_plan(path, plan)` (temp file + `os.replace`). Schema version bumps to `"1.4"` if it was older. Unknown keys round-tripped.
2. Re-render `plan.md` from updated plan.json (existing `/plan` rendering helper).
3. Touch `manifest.json` — only the feature's `updated` timestamp changes; no schema change.

### 5.6 Failure semantics

- HTTP failure mid-bulk-create → successful creates already have IDs in the ClickUp response. The skill writes back **only the successful IDs** and leaves failed stories with `pm_id: null`. Next `/pm-sync` retries them. No half-state in plan.json.
- User Ctrl-C between phases → plan.json may already be partially backfilled. Idempotent re-run: stories with `pm_id` set are skipped (`match`), stories without are retried (`to_create`).
- Action-log entries (`bulk_create_epic`, `bulk_create_story`, `link_epic`) emitted for every mutation — observability and audit trail.

### 5.7 Orphans

`orphans_in_clickup` in the diff = ClickUp tasks that don't correspond to any plan.json story. Surfaced in the user's table, but **never auto-deleted**. User chooses to delete in the ClickUp UI or open a separate cleanup PR.

## 6. Test-first ordering + no-regression strategy

Strangler refactor with green checkpoints at every phase. Existing 8 ClickUp tests stay green throughout.

**Phase A — Build `shield/parsers/` in isolation (RED → GREEN)**

1. Scaffold `shield/parsers/pyproject.toml`, empty `shield_parsers/sidecar.py`, `tests/test_sidecar.py`.
2. Write failing tests first, one behavior at a time:
   - `test_load_plan_v14_minimal` — parse a minimal valid plan.json into typed `Plan`.
   - `test_load_plan_v11_upgrades_to_v14_on_save` — read v1.1, save back as v1.4 with `pm_id: null` defaults.
   - `test_load_plan_rejects_invalid_schema` — JSON Schema validation surfaces named error.
   - `test_load_plan_rejects_too_new_version` — `version: "2.0"` raises `SchemaVersionTooNew`.
   - `test_round_trip_preserves_unknown_keys` — load → save preserves fields we don't model.
   - `test_write_plan_atomic` — temp-file + rename, never leaves partial files on disk.
3. Implement minimum to pass each. Refactor.
4. **Checkpoint:** `uv run --directory shield/parsers pytest` green. ClickUp adapter untouched; its 8 tests still green.

**Phase B — Migrate ClickUp `sync.py` to consume `shield_parsers` (RED → GREEN)**

5. Add new failing tests in `shield/adapters/clickup/tests/test_sync_sidecar.py`:
   - `test_sync_emits_epics_and_stories_from_plan_json` — given a plan.json fixture + mocked ClickUp (respx), sync produces expected create operations.
   - `test_sync_skips_already_synced_stories` — stories with non-null `pm_id` are skipped.
   - `test_sync_creates_missing_epics_before_stories` — epic-create then story-create ordering, story links to just-created epic's pm_id.
   - `test_sync_idempotent_second_run` — re-run against same plan.json produces 0 creates.
   - `test_sync_partial_failure_writes_only_successful_ids` — story 2 fails mid-batch; plan.json saves with pm_id set on story 1 only.
6. Rewrite `sync.py` to import from `shield_parsers.sidecar` instead of `server.parsers`. Rename the registered MCP tool from `pm_sync` to `pm_sync_sidecar` (changes the `@mcp.tool()` registration). Make the new tests pass.
7. **Checkpoint:** `uv run --directory shield/adapters/clickup pytest` green for all 8 baseline tests + 5 new tests. Old `server/parsers/` directory still on disk but unimported.

**Phase C — Delete the old parser path (REFACTOR)**

8. Delete `shield/adapters/clickup/server/parsers/` (all three files).
9. Delete `PlanDocsConfig.format`, `.base_path`, `.epics[].plan_doc`, `StoryExtractionConfig`, `HtmlExtractionConfig` from `config.py`. Update `pm.json` JSON Schema (`shield/schemas/pm.schema.json`).
10. **Checkpoint:** `uv run --directory shield/adapters/clickup pytest` green. `grep -r "from server.parsers" shield/` returns nothing.

**Phase D — Eval coverage**

11. Add `shield/evals/pm-sync-sidecar/eval.yaml` with one positive fixture (sync produces expected ClickUp ops) and one negative (malformed plan.json rejected with named error).
12. RED→GREEN paper trail recorded in PR body: pre-change agent run (failure) + post-change agent run (success).

## 7. Coverage tooling (inline; skill factoring deferred)

Add `pytest-cov` as a dev dep to each Python package touched:

```toml
[dependency-groups]
dev = ["pytest>=8", "pytest-cov>=5", "respx>=0.21"]
```

Per-package thresholds enforced on **patch lines only** (added/modified lines in this PR), not absolute coverage:

| Package | Threshold | Rationale |
|---|---|---|
| `shield/parsers/` (new) | 95% line + branch | Pure logic, easy to cover. |
| `shield/adapters/clickup/server/tools/` (modified) | 85% line | Some HTTP error paths hard to exercise without live ClickUp; `respx` covers the rest. |
| `shield/adapters/_common/` | 95% | Already at this level; preserve. |
| Other clickup adapter files | No regression | Existing 8 tests are the baseline. |

Local invocation:

```bash
uv run --directory shield/parsers          pytest --cov=shield_parsers --cov-report=term-missing --cov-report=xml
uv run --directory shield/adapters/clickup pytest --cov=server          --cov-report=term-missing --cov-report=xml
```

`shield/scripts/coverage_gate.py` is a standalone script invoked as `uv run --with coverage shield/scripts/coverage_gate.py --xml <path> --threshold <pct> --base-ref <main-sha>` (no install step required). It parses `coverage.xml`, diffs against the base ref to identify patch lines, applies the threshold, and prints uncovered patch lines with file:line references. Wired into a CI step for PRs touching the affected paths. Reusable factoring into a `shield/skills/general/test-coverage/` skill comes in a follow-up PR.

## 8. Migration & backwards compatibility

| Surface | Strategy |
|---|---|
| `pm.json` `epics[]` + `plan_docs.*` keys | Loader logs a deprecation warning and ignores them. No schema-validator failure. The minimal Shield-init shape doesn't write them. |
| Existing `plan.json` files at v1.1 (the two in this repo) | Loaded silently. First `/pm-sync` diff = all-to-create; user confirms; pm_id backfilled. Saved as v1.4. |
| Existing ClickUp tasks created out-of-band | Fuzzy-name match at ratio 0.6–0.8 → `to_link`. User confirms; pm_id backfilled into plan.json. |
| Old `pm_sync` MCP tool | Deleted. Cannot succeed against current `/plan` output anyway. `pm_get_capabilities` advertises `pm_sync_sidecar`; stops advertising `pm_sync`. |
| `/shield init` step 7 narrative | Update `shield/commands/init.md` to drop `epics[]` / `plan_docs` references in its scaffolding bullets. |

## 9. Eval coverage (CLAUDE.md mandate)

Two evals land with this PR.

**(1) `shield/evals/pm-sync-sidecar/eval.yaml`** — skill-orchestration eval.

- Fixture: `shield/evals/pm-sync-sidecar/fixtures/plan-v14-minimal.json` — tiny plan.json with 1 epic, 2 stories, schema 1.4.
- Mocked PM adapter: `pm_get_capabilities` returns the new capability set; `pm_sync_sidecar` returns a deterministic diff; `pm_bulk_create` returns deterministic IDs.
- Positive run: agent invokes `/pm-sync`, presents the diff, user confirms, agent makes the expected sequence of MCP calls in epic-first order, writes plan.json back with `pm_id` populated. Assertions check the resulting plan.json matches the expected fixture.
- Negative run (RED): same eval without the new skill content — agent fails to perform the orchestration. Documented in the PR body as the RED baseline.

**(2) `shield/parsers/tests/test_sidecar.py`** — pytest unit tests. Coverage targets per Section 7 (95% line + branch). Structural correctness check; not a CLAUDE.md "eval" but the right form of coverage for the parser code.

**RED→GREEN paper trail** committed to PR body:

```
RED  — pre-change agent run produces: <link to transcript>
GREEN — post-change agent run produces: <link to transcript>
```

## 10. Risks & open questions

- **Risk:** A pre-existing ClickUp task that exactly matches a plan.json story name will be auto-linked at fuzzy ratio 1.0. If the match is coincidental (different intent), the user inherits a wrong link. **Mitigation:** the diff table shows `match` vs `to_link` distinctly; ratio ≥ 0.8 auto-links but is still listed in the confirmation table for the user to override.
- **Risk:** plan.md re-render after every `/pm-sync` may produce noisy diffs in git (`pm_id` references appearing in story headers). **Mitigation:** keep `pm_id` out of the markdown render; only the sidecar carries it.
- **Open:** Should `pm_sync_sidecar` accept `--dry-run` to short-circuit the write phase even after confirmation? Useful in CI for plan validation. **Decision:** ship without it; add later if a use case appears.
- **Open:** Should `coverage_gate.py` live in `shield/scripts/` or `shield/tools/`? Existing scripts live in `shield/scripts/`. **Decision:** `shield/scripts/` for consistency.

## 11. Definition of done

- All four phases (A, B, C, D) green at their checkpoints.
- `grep -r "from server.parsers" shield/` returns nothing.
- `/pm-sync docs/shield/plan-trd-refactor-20260524/plan.json` runs end-to-end against ClickUp, creates 5 epics + 16 stories in the Flow Sprints folder, backfills `pm_id`/`pm_url` in plan.json, re-renders plan.md.
- Re-running `/pm-sync` against the same plan.json produces 0 creates, 0 updates.
- PR body includes the RED→GREEN paper trail for `shield/evals/pm-sync-sidecar/eval.yaml`.
- Plugin version bumped in `.claude-plugin/marketplace.json` and `shield/adapters/clickup/pyproject.toml` per CLAUDE.md.
