# Plan Sidecar JSON Schema

> For the purpose of each Shield artifact and how they relate, see [`shield/docs/artifacts.md`](../../../docs/artifacts.md).

The schema versions in lock-step with `/plan` itself. Current version: **1.6**.

```jsonc
{
  "version": "1.6",
  "project": "<project name from .shield.json>",
  "name": "<kebab-case-plan-name>",
  "phase": "<phase name>",
  "last_aligned_with": null,
  "lld_components": [
    { "name": "user-service", "type": "backend", "fork_blob_sha": null },
    { "name": "vpc-module", "type": "infra", "fork_blob_sha": "abc123def456abc123def456abc123def456abcd" }
  ],
  "milestones": [
    {
      "id": "M1",
      "name": "<short user-language name>",
      "outcome": "<what ships, in user language>",
      "exit_criteria": [
        "<testable fact 1>",
        "<testable fact 2>"
      ],
      "depends_on": [],
      "touches_lld": ["user-service", "vpc-module"],
      "diagram": "flowchart LR\n  A[client] --> B[user-service]\n  B --> C[(db)]"
    }
  ],
  "epics": [
    {
      "id": "EPIC-1",
      "name": "<epic name>",
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "<story name>",
          "status": "ready",
          "assignee": null,
          "priority": "high",
          "week": null,
          "milestone_id": "M1",
          "description": "<2-3 sentences describing what needs to happen>",
          "tasks": [
            "Concrete action 1",
            "Concrete action 2"
          ],
          "acceptance_criteria": [
            "Verifiable outcome 1 (testable, not vague)",
            "Verifiable outcome 2"
          ],
          "design_refs": [
            {
              "doc": "trd",
              "component": null,
              "section_id": "high-level-design",
              "anchor_url": "trd.md#high-level-design",
              "label": "§7 High-Level Design"
            },
            {
              "doc": "lld",
              "component": "user-service",
              "section_id": "api-contracts",
              "anchor_url": "lld-user-service.md#api-contracts",
              "label": "§5 API contracts"
            }
          ],
          "pm_id": null,
          "pm_url": null
        }
      ],
      "pm_id": null,
      "pm_url": null
    }
  ],
  "metadata": {
    "created_at": "<YYYY-MM-DD>",
    "domains": ["<from .shield.json>"],
    "reviewer_grades": {}
  }
}
```

## Rules

- `version` is `"1.6"`. Older sidecars (`"1.5"`, `"1.4"`, `"1.3"`, `"1.2"`, `"1.1"`, `"1.0"`, or missing `version`) remain valid back-compat — see "Back-compat" below. The 1.6 bump makes `milestones[].diagram` (a Mermaid string) required: `validate_plan.py` fails `milestone_no_diagram` / `milestone_ascii_diagram` at 1.6+; older sidecars are grandfathered. The 1.5 bump adds `lld_components[]` at the root and `milestones[].touches_lld[]`; it also tightens `design_refs[]` so `component` is required when `doc=="lld"` (was nullable in 1.4). The 1.4 bump added `pm_id` / `pm_url` to each epic; the 1.3 bump added the top-level `last_aligned_with` field.
- Every epic MUST have at least 1 story.
- Every story MUST have at least 1 acceptance criterion.
- Every story SHOULD have at least 1 `design_refs[]` entry pointing at a TRD section. LLD refs may be TODO placeholders until `/lld <component>` lands.
- Acceptance criteria must be testable — not "it works" but "VPC has DNS support enabled".
- Tasks must be specific enough to execute without questions.
- Status starts as `"ready"` for new stories.
- `pm_id` and `pm_url` start as `null` — populated by `/pm-sync`.

**`epics[].pm_id` / `pm_url` (1.4+)** — ClickUp/Jira/Notion task ID + URL for the epic itself. `null` until first `/pm-sync`. Symmetric with `stories[].pm_id` / `pm_url`. First sync creates the epic task; subsequent syncs read this field to skip already-synced epics.
- Plan name must be kebab-case (`^[a-z0-9-]+$`).
- Each plan lives at `{output_dir}/{feature}/plan.json`.
- Story IDs must be unique across all plans in a project.

### Milestones

- `milestones[]` is the roadmap. Each milestone has `id` (`M1`, `M2`, …), `name`, `outcome`, `exit_criteria` (≥1 testable item), and `depends_on` (array of milestone IDs; empty = no prerequisites). Each milestone MAY also carry an optional `description` (2–3 sentences of context beyond `outcome`); it is additive and back-compat (sidecars without it render with no Description line).
- Every milestone in `milestones[]` MUST have at least one covering story (any story whose `milestone_id` equals this milestone's `id`).
- Exit criteria follow the same testable standard as story acceptance criteria.
- `depends_on` forms a DAG — cycles are rejected by `plan-review`.

#### `touches_lld[]` (1.5+)

Persisted rollup of `lld_components[].name` values referenced by this milestone's stories' `design_refs[]`. Deterministically derived:

```
touches_lld[M] = unique(component for ref in
                        stories[milestone_id==M].design_refs[]
                        where ref.doc == "lld")
```

`/plan-review` (M3 plan) enforces the drift gate: persisted value ≠ rollup → finding. Persisting lets PM-sync, reviewers, and humans read the field without recomputing. Schema 1.4 sidecars without `touches_lld` are treated as empty.

### Story → Milestone linkage

- Each story has a `milestone_id` field. It is either a valid `id` from `milestones[]` or `null`.
- `null` is permitted only when `milestones[]` is empty (back-compat case below) OR when the story is intentionally scoped outside any milestone.
- When `milestones[]` is non-empty AND a story has `milestone_id: null`, `plan-review` surfaces the uncovered story as a warning (not a failure) — null is permitted but flagged.

### `design_refs[]` field

Each story's `design_refs[]` array lists pointers to the design documents the story
implements. Empty array (`[]`) is legal but discouraged — `/plan-review` warns on
stories with no design refs once a TRD is present in the feature folder.

**Field shape (each entry):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `doc` | enum (`trd`, `lld`, `prd`) | yes | Which document the ref points at. Unknown values fail validation. |
| `component` | `string \| null` | **required when `doc=="lld"` (1.5+)** | LLD scoping — the named sub-component (e.g. `user-service`). `null` permitted for TRD/PRD refs. Must match an entry in `lld_components[].name`. |
| `section_id` | `string \| null` | no | Canonical kebab-case slug of the target section. For `doc=trd`, MUST come from the TRD slug allow-list (`shield/schema/trd-sections.yaml`). `null` for placeholder entries pending `/lld`. |
| `anchor_url` | `string \| null` | no | Stable anchor URL relative to the feature folder (e.g. `trd.md#high-level-design`). The anchor token survives heading rename because emitters write explicit `{#section-id}` anchors. `null` for placeholder entries. |
| `label` | `string` | yes | Human-readable label rendered in `/plan-review` and `/pm-sync` outputs. |

**Section-ID selection heuristic (used by `/plan` when emitting refs):**

1. Lowercase the story's name; tokenize on whitespace and punctuation.
2. For each TRD section in `shield/schema/trd-sections.yaml`, score the slug by token-overlap count with the story tokens (Jaccard similarity over the two token sets).
3. Pick the highest-scoring slug.
4. Tie-break by section order (lower section number wins).
5. If no token overlaps any slug, fall back to `high-level-design`.

**Re-run merge semantics (used by `/plan` on subsequent invocations):**

- Existing `design_refs[]` entries are matched against newly-computed entries by the tuple `(doc, section_id, component)`.
- If a stored entry's `(doc, section_id, component)` matches a new entry, `label` and `anchor_url` are updated in place; no duplicate is created.
- If a stored entry no longer matches any TRD section (anchor was deleted), the entry is preserved but tagged `stale: true` for `/plan-review` to surface.
- New entries are appended.

**Inline JSON example (one TRD ref + one LLD placeholder):**

```jsonc
"design_refs": [
  {
    "doc": "trd",
    "component": null,
    "section_id": "apis-involved",
    "anchor_url": "trd.md#apis-involved",
    "label": "§11 APIs Involved"
  },
  {
    "doc": "lld",
    "component": "payment-orchestrator",
    "section_id": null,
    "anchor_url": null,
    "label": "TODO: link when /lld payment-orchestrator lands"
  }
]
```

### `lld_components[]` (1.5+)

Registry of LLD components referenced by any story's `design_refs[]`. Stated once per component, then referenced by name from `design_refs[]` and `milestones[].touches_lld[]`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string (kebab-case) | yes | Matches the filename `docs/lld/<name>.md`. |
| `type` | enum (`backend`, `infra`) | yes | Selects the LLD template variant. |
| `fork_blob_sha` | string (40 hex) \| null | no, default null | `git hash-object docs/lld/<name>.md` at the time `/plan` drafted the feature-folder copy. `null` means the canonical didn't exist at draft time (net-new component). Used by `/implement` at milestone-close for the concurrency check. |

Example:

```json
"lld_components": [
  { "name": "user-service", "type": "backend", "fork_blob_sha": null },
  { "name": "vpc-module", "type": "infra", "fork_blob_sha": "abc123…" }
]
```

### `last_aligned_with`

Top-level field. Stores the git commit SHA of the most recent `/implement` run
that closed (moved to `status: done`) a story in this plan. Pairs with the TRD
provenance stamp to give drift accountability: the plan and the code can be
compared as of the same commit.

- Type: `string | null`. A 40-character lowercase hex sha when set; `null` until
  the first story closes.
- `/implement` writes the field on every story close (status flip to `done`).
- `/plan-review` and `/pm-sync` surface the value as an "Aligned with" line in
  their summaries (e.g., `Aligned with: abc1234… (2026-05-25)`).
- The field is opaque to validators — schema 1.3 enforces shape, not freshness;
  the undead-doc detection that would flag *stale* `last_aligned_with` is a
  separate rule that lives in `/plan-review` (out of scope for this schema bump).

### Back-compat

A sidecar with `version: "1.0"` / `"1.1"` / `"1.2"` or no `version` field is read
as a back-compat sidecar. `design_refs[]` is optional in 1.0/1.1 — missing fields
default to `[]`. `last_aligned_with` is optional in 1.0/1.1/1.2 — missing field
is treated as `null`. A 1.3 sidecar with no `design_refs[]` on any story still
validates; the validator emits a `WARN` (not `FAIL`) when a TRD is present in
the feature folder and a story has zero refs.

A 1.0/1.1 sidecar with `milestones: []` and every story's `milestone_id: null` is
treated as a single implicit milestone covering all stories — see "Single implicit
milestone" below.

**1.4 → 1.5:** A 1.4 sidecar without `lld_components[]` or `touches_lld[]` validates as 1.5; missing arrays default to empty. A 1.4 sidecar with a `design_refs[]` entry where `doc=="lld"` and `component==null` becomes invalid under 1.5 — those entries must be updated before 1.5 validation passes. `/plan-review` will surface this as a finding (see M3 plan).

**1.5 → 1.6:** A 1.5 sidecar without `milestones[].diagram` validates as 1.5 (grandfathered — the diagram gate only fires at `version >= 1.6`). To author at 1.6, every milestone MUST carry a `diagram` (a Mermaid string, not ASCII box-art); `validate_plan.py` fails `milestone_no_diagram:<id>` / `milestone_ascii_diagram:<id>` otherwise, and `render_trd_section.py` renders the diagram under each milestone in TRD §10.

### Forward-compat policy

When `/plan-review` or the validator encounters a sidecar with `version` greater than
the current supported version:

- The validator emits a `WARN` and proceeds with best-effort validation. It does
  NOT reject the document. Unknown top-level keys are preserved on round-trip
  (write-back never strips them).
- Unknown values for closed enums (e.g., `doc` in a `design_refs[]` entry, where
  the closed set is `{trd, lld, prd}`) DO fail validation. Add new doc types via
  schema bump, not silent acceptance.
- Unknown story-level keys are preserved on round-trip; `/plan-review` ignores them.

The rationale: a Shield client one version ahead can safely write to a repo
managed by an older client; the older client preserves the additions without
losing data. Enum drift, by contrast, is a versioning bug — strict rejection
catches it early.

### Single implicit milestone (back-compat)

A sidecar with `milestones: []` and every story's `milestone_id: null` is treated as a **single implicit milestone covering all stories**. `plan-review` does not flag this — it is the back-compat path for plans authored before this schema version or for explicit user opt-out.

If `milestones[]` is empty but any story has a non-null `milestone_id`, the sidecar is invalid — `plan-review` flags the dangling reference (see the milestone_id validity check).

## Rollup invariants (1.5+)

The 1.5 schema introduces two persisted-but-derived fields. Tools that read
or write plan.json must respect the following invariants:

### `milestones[].touches_lld[]` ≡ rollup of `design_refs[]` per milestone

For every milestone `M` in the plan:

```
persisted_touches_lld(M) == sorted(unique({
  ref.component
  for story in stories[milestone_id == M.id]
  for ref in story.design_refs
  if ref.doc == "lld"
}))
```

When this invariant breaks (a human edits `touches_lld` without updating
`design_refs`, or vice versa), `/plan-review` surfaces a `touches_lld_drift`
finding (severity: High).

### `lld_components[].name` is the union of all `design_refs[].component`

For every story's `design_refs[]`:

```
for ref in design_refs:
  if ref.doc == "lld":
    assert ref.component in {c.name for c in lld_components}
```

When this invariant breaks, `/plan-review` surfaces an `lld_component_missing`
finding (severity: High).

### `fork_blob_sha` evolution

`lld_components[].fork_blob_sha` is set by `/plan` when drafting a
feature-folder LLD (only for enhancement components — net-new components
keep `fork_blob_sha = null`). Updated by `/implement` after a successful
auto-heal merge at milestone close. Never edited by humans.

## Validator

The machine-readable counterpart of this schema lives at
`shield/schema/plan-sidecar.schema.json` (JSON Schema draft 2020-12). The Python
validator `shield/scripts/validate_plan.py` loads both this document and the JSON
Schema and runs them in concert:

```bash
uv run --with pydantic --with jsonschema shield/scripts/validate_plan.py path/to/plan.json
```

Exit code 0 means the sidecar is valid. A non-zero exit code carries a named
error (printed to stderr) — `unknown_doc_enum`, `missing_acceptance_criteria`,
`milestone_id_unknown`, etc. The eval runner and `/plan-review` invoke the
validator as the first check; rubric grading and TRD-section checks run only on
schema-valid sidecars.
