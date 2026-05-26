# PRD Milestones + Plan Sprint Alignment — Design Spec

**Date:** 2026-05-13
**Author:** @ashwinimanoj
**Status:** Draft (pending review)

## 1. Problem

The PRD scaffold today documents *what* a feature is (problem, users, goals, stories, NFRs) but stops short of *how it ships in pieces*. Section 13 "Rollout plan" covers flag/canary/abort mechanics but offers no roadmap-level phasing.

The `/plan` step jumps straight from PRD to flat epics/stories with no milestone grouping. Stories get a `week` field but no higher-level structure groups them into shippable outcomes.

Result: product and engineering have no shared roadmap artifact. Reviewers cannot verify that the plan covers the product's intended phasing because that phasing was never named.

## 2. Goals

- PRDs surface a high-level **roadmap of milestones** — ordered, named outcomes with exit criteria.
- **Milestones are agent-proposed, user-refined.** A new `shield:milestone-coverage` skill dispatches `shield:product-manager-reviewer` and `shield:agile-coach-reviewer` in parallel, merges their proposals, and presents an editable scaffold to the user. User has the final say.
- The `/plan` sidecar treats milestones as first-class structure: stories link to milestones; reviewers can validate coverage.
- Timing stays out of the PRD. Concrete timing emerges at `/plan` via existing story-level `week` assignments and sprint grouping.
- Backward compatibility: existing PRDs and plans without milestones continue to work.

## 3. Non-goals

- Sprint-level capacity / velocity modeling (PM-tool territory).
- Auto-rescheduling milestones when stories slip (manual decision).
- A `prd-review` rubric dimension scoring milestone quality (follow-up).
- `/pm-sync` mapping milestones to PM-tool releases or epics (follow-up).

## 4. Design

### 4.1 PRD shape

**Milestone fields (both scaffolds):**

| Field | Description |
|---|---|
| ID | `M1`, `M2`, … (sequential within the PRD) |
| Name | Short, user-language ("Login core", "Password recovery") |
| Outcome | What ships at the end of this milestone, in user language |
| Exit criteria | Testable conditions for "this milestone is done" (list) |
| Depends on | Other milestone IDs that must ship first (list; empty = none) |

**No timing field.** Timing lives in `/plan` via story-level `week` and sprint grouping (see §4.5).

**Standard scaffold — Section 13 reshape.** Section 13 ("Rollout plan") is reshaped: milestones lead, existing rollout mechanics follow as global fields applying across milestones.

```markdown
## 13. Rollout plan

### Milestones
| ID | Name | Outcome | Exit criteria | Depends on |
|---|---|---|---|---|
| M1 | <name> | <user-language outcome> | <testable list> | — |
| M2 | …    | …                       | …               | M1 |

### Rollout mechanics
- Flag plan: <…>
- Canary: <…>
- Kill-switch / abort thresholds: <…>
- Data migration: <…>
- Backward compatibility: <…>
```

**Lean scaffold — grows from 7 to 8 sections.** New Section 6 "Milestones" inserts between Success metrics (5) and Open questions (now 7). No rollout-mechanics block in lean.

New lean numbering: 1 Header, 2 Problem, 3 Personas, 4 Goals, 5 Success metrics, **6 Milestones**, 7 Open questions, 8 Out of scope.

### 4.2 Sidecar schema (plan.json)

Two additions:

```jsonc
{
  // …existing fields…
  "milestones": [
    {
      "id": "M1",
      "name": "Login core",
      "outcome": "Users can log in with email + password",
      "exit_criteria": [
        "Login endpoint returns session token on valid credentials",
        "Rate limiting active on login endpoint"
      ],
      "depends_on": []
    }
  ],
  "epics": [{
    "stories": [{
      // …existing fields…
      "milestone_id": "M1"   // nullable for back-compat
    }]
  }]
}
```

**Back-compat:** A sidecar with `milestones: []` and every story's `milestone_id: null` is the "single implicit milestone" case. plan-review treats it as one milestone covering all stories — not a blocker, not flagged.

`sidecar-schema.md` is updated to document the new fields and the back-compat rule.

### 4.3 Milestone authoring — agent-led, user-refined

Milestones are **proposed by agents, refined by the user**. They are never silently written without user approval.

**New shared skill: `shield:milestone-coverage`** (sibling to existing `shield:story-coverage`).

- **Inputs:** stories (PRD Section 6, when present), goals (Section 4), personas (Section 3).
- **Dispatches in parallel:**
  - `shield:product-manager-reviewer` → proposes milestone groupings by user-facing outcome (which stories ship together as a coherent user benefit; outcome statements in user language).
  - `shield:agile-coach-reviewer` → proposes dependency ordering, milestone sizing, and testable exit criteria.
- **Merges** both proposals into a single milestone scaffold (ID, Name, Outcome, Exit criteria, Depends on). When the two agents conflict (e.g., PM groups M1 stories one way, agile-coach disagrees on ordering), the merge keeps both views in the proposal and **surfaces the conflict to the user** for resolution — it does not silently pick one side.
- **Presents the scaffold to the user** with a multi-select / editable view: accept all, edit fields per row, drop, add new. User has the final say. Approved milestones land in their destination (PRD section or sidecar — see §4.4, §4.5).
- **Lean PRD note:** lean lacks Section 6 stories. `milestone-coverage` falls back to **goals + personas only** in that case. The proposal is coarser but still works; user refinement is still the final gate.

This matches the pattern `shield:story-coverage` already establishes (skill proposes, user picks via multi-select before scaffolding lands).

### 4.4 PRD authoring flow (`/prd`)

Workflow updates in `prd-docs/SKILL.md`:

- **Standard scaffold:** after Section 6 (User stories) is filled and before walking Section 13, invoke `shield:milestone-coverage`. User-approved milestones populate Section 13's Milestones table. Then walk the rollout-mechanics fields below the table as today.
- **Lean scaffold:** after Section 4 (Goals) and Section 5 (Success metrics) are filled and before walking Section 6 (the new Milestones section), invoke `shield:milestone-coverage` with the lean fallback (goals + personas only). User-approved milestones populate Section 6.
- **User can skip:** if the user declines to define milestones, both scaffolds allow an empty Milestones table. `/plan` will then run `shield:milestone-coverage` again as the fallback path (§4.5).

### 4.5 /plan flow changes

Workflow updates in `plan-docs/SKILL.md`:

1. **Step 1a (PRD detection, existing):** continues to read the PRD if found.
2. **New Step 1b — Milestone resolution:**
   - **If PRD has milestones in Section 13 (standard) or Section 6 (lean):** present them to the user for confirmation. Allow edits. Copy into sidecar `milestones[]`.
   - **If PRD exists but has no milestones (or empty Milestones table):** invoke `shield:milestone-coverage` with whatever inputs the PRD provides (stories if standard, goals+personas if lean). User refines the proposal. Sidecar-only — **do NOT write back to PRD**. The PRD is treated as an authoring-time snapshot; if the author wants to update it, they re-run `/prd`.
   - **If no PRD at all:** invoke `shield:milestone-coverage` with whatever inputs `/plan` collected during requirements gathering. User refines. Sidecar-only.
   - **If user explicitly opts out of milestones:** sidecar stores `milestones: []` (the back-compat case in §4.2).
3. **Story generation (revised order):** walk milestone-by-milestone. For each milestone, generate the stories that satisfy its exit criteria. Each story is born with a valid `milestone_id` — no separate mapping pass.
4. **plan.html template:** group stories by milestone. Inside each milestone block, render stories in order of their existing `week` value (sprint cadence emerges from `week` grouping — e.g., weeks 1–2 = Sprint 1, weeks 3–4 = Sprint 2). Milestone header shows status rollup (e.g., `M1 — 3/5 stories ready`).

### 4.6 plan-review checks

`plan-review` agents pick up new checks. The `shield:agile-coach-reviewer` agent is the natural owner since milestones land in its scope (sprint-readiness, dependency ordering, AC/exit-criteria testability, story sizing). It is "always dispatched for plans with stories" today, so no new wiring is needed — only its check list grows:

- Every milestone has ≥1 covering story. *(agile-coach: coverage/sizing)*
- Every story's `milestone_id` is either `null` or references an existing milestone in the sidecar. *(agile-coach + structural validator)*
- Exit criteria are testable (not "it works" — same standard as story AC). *(agile-coach)*
- `depends_on` forms a DAG (no cycles). *(agile-coach: dependency ordering)*

Existing checks unchanged.

### 4.7 Auxiliary changes

- **`prd.meta.json` `rubric_version`** bumps with this change so `prd-review` knows whether a PRD was authored against the milestone-aware scaffold or an older version. The bump is scaffold-version awareness only — it does NOT introduce a new rubric *dimension* (that is the deferred follow-up in §8).
- **`shield:summarize`** plan-summary template mentions milestones when present (small cosmetic template update).
- **`templates.md`** updated for both PRD scaffolds (standard + lean) and for `plan.html`.

### 4.8 What is intentionally NOT changing

- **Section 6 (User stories)** stays as-is. Milestones group stories; they don't replace them.
- **`shield:story-coverage`** skill stays where it is in `/prd` flow (between Sections 4 and 6). It runs before milestones, which is correct — milestones are scaffolded once stories exist.
- **PRD review rubric** — no new dimension scored in this scope (deferred).
- **`/pm-sync`** — no milestone mapping in this scope (deferred).
- **Cross-feature milestone dashboard** — out of scope.

## 5. Edge cases

| Case | Behavior |
|---|---|
| Old PRD without Section 13 milestones | `/plan` prompts user to define; sidecar-only; PRD untouched |
| Old plan.json without `milestones[]` | Treated as back-compat single-implicit-milestone; no migration required |
| User invokes `/plan` with no PRD | Prompt for milestones from scratch; sidecar-only |
| User opts out of milestones | `milestones: []`, all `milestone_id: null`; plan-review treats as single implicit milestone |
| Story references a `milestone_id` that doesn't exist in `milestones[]` | plan-review flags as an error |
| `depends_on` cycle | plan-review flags as an error |
| Lean PRD upgraded to standard | Existing upgrade flow already covers Section 13; new milestone fields walked through during upgrade |
| Lean section renumbering breaks downstream checks | `prd-review` and any consumer that reads lean PRDs MUST address sections by name ("Milestones", "Open questions"), not by number — the lean renumber from 7 to 8 sections is the only practical case where this matters. Audit `prd-review` to confirm name-based addressing before shipping. |

## 6. Testing plan (RED-GREEN per CLAUDE.md)

Skill changes require RED-GREEN testing. Fixtures and runs to add:

**Fixtures:**
- PRD with well-formed milestones (standard scaffold)
- PRD with well-formed milestones (lean scaffold)
- PRD without milestones (back-compat)
- PRD with stories + goals (input for `milestone-coverage` standard path)
- PRD with goals + personas only (input for `milestone-coverage` lean path)
- Plan sidecar with milestones + milestone_id wired through stories
- Plan sidecar with cycle in `depends_on` (negative case)
- Plan sidecar with story referencing missing milestone_id (negative case)

**RED:** Run agents without the skill updates against each fixture. Expected: `milestone-coverage` doesn't exist (so no proposal); plan-review misses milestone structure, doesn't catch cycle, doesn't catch dangling milestone_id.

**GREEN:** Run with skill updates against the same fixtures. Verify:
- `milestone-coverage` dispatches PM + agile-coach, merges proposals, surfaces conflicts, presents user-editable scaffold.
- Lean fallback (goals+personas only) still produces a usable proposal.
- plan-review catches both negative cases.
- Sidecar shape matches §4.2.

**REFACTOR:** Fix any gaps in the skill text and re-test.

## 7. Affected files (preview, not exhaustive)

- `shield/skills/general/milestone-coverage/` (**new skill** — SKILL.md + any prompt/agent-dispatch helpers, modeled on `shield:story-coverage`)
- `shield/skills/general/prd-docs/SKILL.md` (invoke `milestone-coverage` at the right step for standard + lean)
- `shield/skills/general/prd-docs/templates.md`
- `shield/skills/general/prd-docs/meta-schema.md` (rubric_version bump)
- `shield/skills/general/plan-docs/SKILL.md` (invoke `milestone-coverage` as fallback when PRD lacks milestones)
- `shield/skills/general/plan-docs/sidecar-schema.md`
- `shield/skills/general/plan-docs/templates.md` (plan.html grouping)
- `shield/skills/general/plan-review/` (new agile-coach checks)
- `shield/skills/general/prd-docs/test-fixtures/` (new milestone fixtures)
- `shield/skills/general/summarize/` (plan-summary template update)

## 8. Follow-ups (out of scope, tracked here)

- `prd-review` rubric dimension scoring milestone quality.
- `/pm-sync` mapping milestones → PM-tool releases or epics (per-adapter).
- Cross-feature milestone dashboard on `{output_dir}/index.html`.
- Optional: `/prd` re-run flow that pulls milestones back from the sidecar if `/plan` revised them.
