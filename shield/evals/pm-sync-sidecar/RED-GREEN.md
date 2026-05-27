# pm-sync-sidecar eval — RED → GREEN paper trail

Covers the `/pm-sync` sidecar refactor's schema-1.4 surface. Design spec:
`docs/superpowers/specs/2026-05-26-shield-pm-sync-sidecar-refactor-design.md`.

## RED (pre schema bump)

Under schema 1.3, the `epic` def had no `pm_id`/`pm_url` properties. A synced
plan that wrote `pm_id`/`pm_url` onto an epic still validated — but only because
`additionalProperties: true` let the fields through *untyped and unvalidated*.
Nothing asserted they were string-or-null, and `validate_plan.py`'s
`CURRENT_VERSION = (1, 3)` meant a `version: "1.4"` sidecar tripped a
`forward_compat` WARN on every run.

## GREEN (schema 1.4 + validator current)

Schema 1.4 explicitly types epic `pm_id`/`pm_url` as `["string", "null"]`, and
`validate_plan.py` now sets `CURRENT_VERSION = (1, 4)`, so 1.4 sidecars validate
cleanly with no forward-compat warning. The three cases exercise: an unsynced
plan (null pm ids), a synced plan (populated epic + story pm ids — the new
field with a real value), and a negative where an epic omits `stories`:

```
$ uv run shield/evals/run.py pm-sync-sidecar
=== eval suite: pm-sync-sidecar (3 cases) ===
  PASS v14-unsynced-null-pm-ids
  PASS v14-synced-populated-pm-ids
  PASS invalid-epic-missing-stories   # schema_violation, exit 1
=== 3/3 cases passed ===
```

## Backfill write-path (pm_backfill_ids)

The `pm_backfill_ids` write-back tool has no eval.yaml case: the deterministic
eval runner only validates static fixtures (validate_plan/validate_trd), not MCP
tool orchestration. Its write path is regression-covered by unit tests in
`shield/adapters/clickup/tests/test_backfill.py`.

## Milestone tags (shield:ms:<id>)

`pm_bulk_create` tags created story tasks with `shield:ms:<milestone_id>` (e.g.
`shield:ms:m1`) when the story carries a `milestone_id`. This has no deterministic
eval case for the same reason as backfill — the runner validates static plan.json
fixtures, it does not execute `pm_bulk_create` to inspect the emitted ClickUp
create payload. The tag-injection behavior (set / missing / null) is
regression-covered by unit tests in
`shield/adapters/clickup/tests/test_bulk_create.py`. The suite fixtures already
carry `milestone_id: "M1"` on their stories, so the schema surface that feeds the
tag (a valid `milestone_id` referencing a declared milestone) is exercised by the
existing `v14-unsynced` / `v14-synced` cases.
