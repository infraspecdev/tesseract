# Milestone Coverage — Templates

## Agent prompts

### Product Manager prompt

Pass to `shield:product-manager` with subagent_type `shield:product-manager`:

> You are reviewing a feature for milestone-grouping from a product/user-outcome perspective.
>
> **Personas:** {personas-json}
> **Goals:** {goals-json}
> **Stories:** {stories-json or "[empty — lean PRD; propose from goals only]"}
> **Success metrics:** {success-metrics-json or "[none]"}
>
> Propose 2–5 milestones grouping these stories (or, in lean mode, decomposing these goals) by **coherent user-facing outcome**. Each milestone should ship a benefit a user can describe in one sentence. Optimize for outcome cohesion — do NOT optimize for technical sequencing (that is the agile coach's job).
>
> Output a JSON object matching this shape:
> ```json
> { "milestones": [ { "id": "M1", "name": "...", "outcome": "...", "exit_criteria": ["..."], "depends_on": [], "covered_story_ids": ["S1","S2"] } ] }
> ```
>
> Rules:
> - Exit criteria must be testable (not "it works"; instead "endpoint returns 200 + session token on valid credentials").
> - `depends_on` should reflect *product* prerequisites only ("recovery is meaningless without login shipping first"), not technical dependencies.
> - `covered_story_ids` must reference story IDs from the input.

### Agile Coach prompt

Pass to `shield:agile-coach` with subagent_type `shield:agile-coach`:

> You are reviewing a feature for milestone-grouping from a sprint-readiness / dependency / sizing perspective.
>
> **Personas:** {personas-json}
> **Goals:** {goals-json}
> **Stories:** {stories-json or "[empty — lean PRD; propose from goals only]"}
>
> Propose 2–5 milestones grouping these stories (or, in lean mode, decomposing these goals) by **technical sequencing, sizing, and testable exit criteria**. Optimize for: (a) each milestone is sprint-sized (roughly 1–3 sprints of work), (b) `depends_on` reflects real technical prerequisites, (c) exit criteria are verifiable facts a reviewer can check.
>
> Output a JSON object matching this shape:
> ```json
> { "milestones": [ { "id": "M1", "name": "...", "outcome": "...", "exit_criteria": ["..."], "depends_on": [], "covered_story_ids": ["S1","S2"] } ] }
> ```
>
> Rules:
> - Exit criteria must be testable (same standard you apply to story AC).
> - `depends_on` should reflect *technical* prerequisites only (shared modules, data migrations, infra).
> - Flag any milestone you think exceeds 3 sprints of work by adding `"sizing_concern": "<reason>"`.

## Merge rules

After both agents return, merge their proposals:

### 1. Name matching

Two milestones match if:
- Names are identical (case-insensitive), OR
- Outcomes share ≥60% of words (stopwords filtered), OR
- They cover an overlapping set of `covered_story_ids` (intersection / union ≥ 0.5)

When matched, merge into one row.

### 2. Field merge (matched milestones)

- `id`: assign sequentially in final output (M1, M2, …), regardless of input IDs.
- `name`: prefer the PM agent's name (user-facing language wins for naming).
- `outcome`: prefer the PM agent's outcome.
- `exit_criteria`: **union** of both lists. Deduplicate by semantic similarity (drop near-duplicates).
- `depends_on`: **intersection** of both lists. If the two lists differ, record the disagreement in `open_conflicts` (see §3 below) AND set the merged `depends_on` to the intersection (conservative — fewer dependencies).
- `covered_story_ids`: union.
- `source_agents`: `["product-manager", "agile-coach"]`.
- `conflicts`: list of fields where the two agents disagreed (e.g., `["depends_on"]`).

### 3. Unmatched milestones

- PM-only milestone → keep, `source_agents: ["product-manager"]`.
- Agile-coach-only milestone → keep, `source_agents: ["agile-coach"]`. Note for the user: this often signals a technical milestone (e.g., infrastructure hardening) that doesn't map to a user-visible outcome.

### 4. Open conflicts

For every disagreement (depends_on diff, sizing concerns, missing match), add an entry to top-level `open_conflicts`:

```json
{
  "field": "<field name or 'unmatched'>",
  "milestone_id": "M2",
  "pm_proposal": "<PM view>",
  "agile_coach_proposal": "<agile-coach view>",
  "explanation_pm": "<one sentence>",
  "explanation_agile_coach": "<one sentence>"
}
```

The caller surfaces each conflict to the user for resolution.
