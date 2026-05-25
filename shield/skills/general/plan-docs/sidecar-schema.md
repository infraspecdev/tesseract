# Plan Sidecar JSON Schema

The schema versions in lock-step with `/plan` itself. Current version: **1.3**.

```jsonc
{
  "version": "1.3",
  "project": "<project name from .shield.json>",
  "name": "<kebab-case-plan-name>",
  "phase": "<phase name>",
  "last_aligned_with": null,
  "milestones": [
    {
      "id": "M1",
      "name": "<short user-language name>",
      "outcome": "<what ships, in user language>",
      "exit_criteria": [
        "<testable fact 1>",
        "<testable fact 2>"
      ],
      "depends_on": []
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
              "component": null,
              "section_id": null,
              "anchor_url": null,
              "label": "TODO: link when /lld <component> lands"
            }
          ],
          "pm_id": null,
          "pm_url": null
        }
      ]
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

- `version` is `"1.3"`. Older sidecars (`"1.2"`, `"1.1"`, `"1.0"`, or missing `version`) remain valid back-compat — see "Back-compat" below. The 1.3 bump adds the top-level `last_aligned_with` field (see "`last_aligned_with`" below).
- Every epic MUST have at least 1 story.
- Every story MUST have at least 1 acceptance criterion.
- Every story SHOULD have at least 1 `design_refs[]` entry pointing at a TRD section. LLD refs may be TODO placeholders until `/lld <component>` lands.
- Acceptance criteria must be testable — not "it works" but "VPC has DNS support enabled".
- Tasks must be specific enough to execute without questions.
- Status starts as `"ready"` for new stories.
- `pm_id` and `pm_url` start as `null` — populated by `/pm-sync`.
- Plan name must be kebab-case (`^[a-z0-9-]+$`).
- Each plan lives at `{output_dir}/{feature}/plan.json`.
- Story IDs must be unique across all plans in a project.

### Milestones

- `milestones[]` is the roadmap. Each milestone has `id` (`M1`, `M2`, …), `name`, `outcome`, `exit_criteria` (≥1 testable item), and `depends_on` (array of milestone IDs; empty = no prerequisites).
- Every milestone in `milestones[]` MUST have at least one covering story (any story whose `milestone_id` equals this milestone's `id`).
- Exit criteria follow the same testable standard as story acceptance criteria.
- `depends_on` forms a DAG — cycles are rejected by `plan-review`.

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
| `component` | `string \| null` | no | LLD scoping — the named sub-component (e.g. `payment-orchestrator`). `null` for TRD/PRD refs (which are feature-scoped) and for LLD placeholders. |
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
