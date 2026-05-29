# Backend Engineer — Detailed Findings

> Back to [summary](../summary.md)

**Persona grade: B−.** A well-structured, honestly-bounded plan with excellent error/idempotency/testability discipline, held back from B+/A− by three contract defects that only surface when the design is placed next to the real `manifest.json` / `plan.json` / `shield.schema.json`.

## Evaluation points (A–F)

| # | Point | Grade |
|---|---|---|
| 1 | F8 "epic landed" predicate consistency | B |
| 2 | Single-writer concurrency claim (N1) | B+ |
| 3 | Atomic-write + validate-or-refuse correctness | A− |
| 4 | The id contract | A− |
| 5 | LLD API contracts implementable as specified | C+ |
| 6 | Python packaging via uv | B |
| 7 | Error semantics | A− |
| 8 | Idempotency | A |
| 9 | Testability | A− |

## P0 findings (verified against live schemas)

### P0-1 — `reconcile`/`suggest_*` contracts don't match the real `manifest.json`/`plan.json` shapes
Every cross-document reference treats `manifest` and `plans` as opaque `dict`s, but the live artifacts have a specific shape the contracts contradict. `manifest.json` is `{"schema_version":…, "features":[ {name, artifacts:{research,prd,plan_json,plan_md,plan_arch_md}, reviews, updated} ]}` — a list keyed by `name`, with a **boolean** `plan_json` flag and **no plan path stored**. `reconcile(entry, *, manifest: dict, plans: dict)` (`lld-reconciler.md` §5) never defines `plans` and never says the reconciler must *derive* `docs/shield/<feature>/plan.json`.
**Fix:** pin the real shapes in `lld-reconciler.md` §5 and `lld-epic-suggester.md` §5; define `plans: dict[str, dict]` (feature-slug → parsed plan.json) populated by reading `docs/shield/<feature>/plan.json` for each feature whose `artifacts.plan_json is True`; state the flag is `plan_json` (boolean) and the path is derived. Add an EPIC-4-S1 fixture from the actual manifest schema.

### P0-2 — F8 "match existing-epic by id" matches a positional slot, not a stable identity
Epic ids are positional `EPIC-N` slugs assigned by `/plan`, not durable identifiers. After any re-`/plan`, `EPIC-2` points at a different epic. An existing-epic backlog entry stamped `EPIC-2` will then match the wrong epic (false removal) or fail to match (entry rots). Verified: `plan-trd-refactor-20260524` `EPIC-2 = "Story schema and design traceability"` vs `pm-restructure-v0-20260521` `EPIC-2 = "Global authoring…"`.
**Fix:** match existing epics by normalized `name` too (same predicate as proposed-new); treat `EPIC-N` only as a within-a-single-plan disambiguator. If id-matching is kept, document the re-plan failure mode and add a "epic reordered across a re-plan" eval.

### P0-3 — Kill switch `backlog.auto_reconcile` cannot live in `.shield.json` as the schema stands
`shield/schemas/shield.schema.json` has `additionalProperties: false` and properties `[project, domains, output_dir, reviewers, devcontainer, external_skills]` — no `backlog` key. Adding `backlog.auto_reconcile` to a real `.shield.json` fails validation, and no story includes the schema change.
**Fix:** add a task+AC (EPIC-3-S3, reflected in EPIC-4-S2 version bump) to extend `shield.schema.json` with an optional `backlog` object (`{auto_reconcile: bool, default true}`) + a config example. Without this the documented first-line rollback (TRD §14) is unshippable.

## P1 findings

- **P1-1** — Concurrency eval tests a race the single-writer design says cannot occur. Nothing enforces serialization (no lock). Either the race can't happen (eval vacuous) or it can (read-modify-write is not atomic — `os.replace()` only makes the rename atomic; loser's entry is silently dropped). Resolve: rescope to sequential, OR add a minimal compare-before-replace/merge and test it.
- **P1-2** — F2/EPIC-1-S1 AC says "the schema rejects duplicate id"; JSON Schema (2020-12) cannot express property-level array uniqueness. Reword to "the **validator** (`validate_backlog.py`) rejects duplicate id with `duplicate_entry_id`."
- **P1-3** — Feature "name" (manifest) vs "folder slug" (reconciliation key) conflated. Pin the invariant (`features[].name` == folder slug) and make `suggest_feature` return that field; add a fixture asserting the suggested value resolves to an existing `docs/shield/<value>/` path.
- **P1-4** — Packaging model unresolved. F3 ("every capturing skill builds against this signature") implies an importable module, but EPIC-4-S2 hedges ("if backlog scripts are packaged"). Decide at plan time — recommend packaging with a `pyproject.toml` so the version bump is unconditional; document how a skill calls `capture()`.

## P2 findings

- **P2-1** — Atomic write omits `os.fsync()` before `os.replace()` (power-loss window) and uses a fixed `.tmp` name (stale-temp collision). Add fsync + unique temp suffix.
- **P2-2** — `read() -> dict` forces every caller to re-validate shape; consider returning the pydantic model (`read() -> BacklogDoc`).
- **P2-3** — `RemovalDecision` / `Candidate` payloads referenced but `RemovalDecision`'s fields (the F9 log fields) are undefined. Add a 4-field dataclass in `lld-reconciler.md`.

**Verification sources:** `shield/schemas/plan.schema.json`, `shield/schemas/shield.schema.json`, `docs/shield/manifest.json`.
