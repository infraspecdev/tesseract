# prd.meta.json Schema

Lightweight metadata sidecar accompanying every `prd.md`. Records type, status, owner, last-updated, rubric-version, and the bidirectional linkage to plans.

## Schema (v1.0)

```json
{
  "schema_version": "1.0",
  "type": "standard | lean",
  "status": "Draft | In Review | Approved | In Implementation | Shipped | Retired",
  "owner": "@<handle>",
  "decision_maker": "@<handle>",
  "sign_off_contacts": {
    "legal": "@<handle> | null",
    "security": "@<handle> | null",
    "support": "@<handle> | null"
  },
  "date_created": "YYYY-MM-DD",
  "last_updated": "YYYY-MM-DD",
  "rubric_version": "1.2",
  "sections_present": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
  "sections_missing_from_standard": [],
  "linked_research": "research/1-some-slug/findings.md | null",
  "linked_design_spec": "<path or null>",
  "linked_plans": ["plan/1-foundation-slug/", "plan/2-rollout-slug/"]
}
```

## Field rules

- **`schema_version`**: bumped if schema changes (e.g., new field added). Current = "1.0".
- **`type`**: "standard" if all 20 sections present; "lean" if only the 10 lean sections are present. See `type-detection.md`.
- **`status`**: lifecycle stages. Default "Draft" on first write. Updated by user externally (Shield doesn't manage transitions in Phase B; future enhancement).
- **`sections_missing_from_standard`**: populated only for lean PRDs; lists which standard sections are deliberately omitted. Empty for standard.
- **`linked_plans`**: auto-appended by `/plan` when it runs against a feature folder containing a PRD. Each entry is a relative path to the plan run folder (`plan/{N}-{slug}/`).
- **`rubric_version`**: records which version of the PRD-review rubric was relevant at PRD authoring time. Read from `shield/skills/general/prd-review/rubric.md` header (add a version comment there in Phase A if missing).

  `rubric_version: "1.1"` adds the §13 Milestones table (standard) and §6 Milestones section (lean). `prd-review` reading a `1.0` PRD MUST NOT expect milestones; reading a `1.1` PRD MAY expect them. The version bump is scaffold-version awareness only — it does NOT introduce a new scored rubric *dimension* (that is a deferred follow-up; see `docs/superpowers/specs/2026-05-13-prd-milestones-design.md` §8).

  `rubric_version: "1.2"` adds Terminologies (§2), Architecture & flows (§5), and the Type field on §8 stories. `prd-review` reading a `1.0` or `1.1` PRD MUST NOT expect these; reading a `1.2` PRD MAY expect them. As with 1.1, the version bump is scaffold-version awareness only — it does NOT introduce a new scored rubric *dimension*.

## Read/Write contracts

- **Created by:** `/prd` command (Phase B) on first run; updates `last_updated` on subsequent runs in the same feature folder
- **Read by:** `/prd-review` (consumes `type`, `sections_present`, `sections_missing_from_standard` for rubric selection), `/plan` (consumes `linked_plans` to know what's already planned), `/plan-review` (consumes `sections_present` to inform plan-vs-PRD alignment review — future)
- **Appended by:** `/plan` on each run, adds an entry to `linked_plans`

## Schema evolution

When dim 14 was added in the spec, no schema change was needed (the schema stayed at v1.0). The schema only changes if a new field is added or an existing field's shape changes. Adding a new field is non-breaking; consumers ignore unknown fields. Removing or changing a field requires a `schema_version` bump.
