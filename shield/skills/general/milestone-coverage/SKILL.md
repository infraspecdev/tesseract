---
name: milestone-coverage
description: Use when scaffolding milestones for a PRD or for a plan when no PRD milestones exist. Dispatches product-manager-reviewer and agile-coach-reviewer in parallel, merges proposals, surfaces conflicts. Consumed by /prd (after stories for standard, after goals for lean) and /plan (as fallback when PRD has no milestones).
---

# Milestone Coverage

Propose a milestone scaffold for a feature by dispatching `shield:product-manager-reviewer` and `shield:agile-coach-reviewer` in parallel and merging their outputs into a single user-editable proposal.

## When to Use

- `/prd` invokes this after Section 6 (User stories) is filled in the standard scaffold, or after Section 5 (Success metrics) in the lean scaffold, to scaffold the Milestones table.
- `/plan` invokes this as a fallback when the linked PRD has no milestones (or no PRD exists), to populate the sidecar `milestones[]`.

## Input contract

The caller provides:
- `personas`: list of {id, name, goals[]} (always required)
- `goals`: list of {id, description} (always required)
- `stories`: list of story objects from PRD §6 (required for standard; absent for lean — skill falls back to coarser proposals from goals+personas)
- `feature_domain`: best-effort domain hint (same set as `shield:story-coverage`)
- `success_metrics`: optional; used by PM agent to anchor outcomes to metrics

## Output contract

Return a single merged milestone proposal:

```json
{
  "milestones": [
    {
      "id": "M1",
      "name": "Login core",
      "outcome": "Users can log in with email + password",
      "exit_criteria": [
        "Login endpoint returns 200 + session token on valid credentials",
        "Rate limiting active on login endpoint"
      ],
      "depends_on": [],
      "source_agents": ["product-manager-reviewer", "agile-coach-reviewer"],
      "conflicts": []
    }
  ],
  "open_conflicts": [
    {
      "field": "depends_on",
      "milestone_id": "M2",
      "pm_proposal": [],
      "agile_coach_proposal": ["M1"],
      "explanation_pm": "PM sees recovery as independent of login UI changes",
      "explanation_agile_coach": "Recovery needs the session middleware shipped in M1"
    }
  ]
}
```

`open_conflicts` is what the caller surfaces to the user for resolution. `conflicts` per-milestone is set to `[]` when both agents agreed.

## Step Skeleton

| Step | Action | Mandatory |
|---|---|---|
| 1 | Validate input — personas + goals required; stories required for standard mode | Yes |
| 2 | Dispatch `shield:product-manager-reviewer` and `shield:agile-coach-reviewer` in parallel with the prompts in `templates.md` | Yes |
| 3 | Parse each agent's milestone proposal (validate JSON shape) | Yes |
| 4 | Merge proposals using the rules in `templates.md` → Merge rules section | Yes |
| 5 | Return merged proposal + `open_conflicts` | Yes |

## Merge rules summary

See `templates.md` → Merge rules for the full ruleset. Summary:
- **Same milestone name (or strong semantic overlap):** merge into one row. Take union of exit criteria, intersection of depends_on (with conflict raised on disagreement).
- **PM-only milestone:** keep, mark `source_agents: ["product-manager-reviewer"]`.
- **Agile-coach-only milestone:** keep, mark `source_agents: ["agile-coach-reviewer"]`. Common for purely-technical milestones (e.g., "Auth module hardening").
- **Field conflict (depends_on, exit_criteria):** record under `open_conflicts` rather than silently picking one.

## Lean fallback

When `stories` is not provided (lean PRD), pass empty stories list to both agents. The agents propose milestones from goals+personas only. Output is structurally identical, just coarser. The caller should warn the user: "Lean PRD detected — milestones proposed from goals only; refine before approving."

## Caller behavior

The caller (`/prd` or `/plan`) MUST:
1. Present the merged `milestones[]` to the user with multi-select + editable fields (accept, edit per row, drop, add new).
2. Surface every entry in `open_conflicts` to the user. The user resolves each conflict by choosing one side, merging, or rewriting.
3. NEVER write the proposal to the destination (PRD section or sidecar) without explicit user approval.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Calling without `personas` or `goals` | These are mandatory inputs; skill returns an error if either is missing |
| Silently picking one agent's view on a conflict | All conflicts MUST be surfaced to the user via `open_conflicts` |
| Skipping the user-approval gate | Caller MUST gate on user approval before any write |
| Treating lean output as standard quality | Warn the user when stories are absent — proposal is coarser |

## See Also

- `templates.md` — agent prompts + merge rules
- `shield:story-coverage` — sibling skill, invoked before this one in `/prd` standard flow
- `shield:product-manager-reviewer` agent
- `shield:agile-coach-reviewer` agent
