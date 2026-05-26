# PRD Milestones + Plan Sprint Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add agent-proposed, user-refined milestones to the PRD as a high-level roadmap, and wire them into `/plan` as first-class sidecar structure so reviewers can verify story-to-milestone coverage.

**Architecture:** A new `shield:milestone-coverage` skill (sibling to `shield:story-coverage`) dispatches `shield:product-manager-reviewer` and `shield:agile-coach-reviewer` in parallel, merges proposals, surfaces conflicts, and presents an editable scaffold to the user. `/prd` invokes it once stories (or goals, for lean) exist; `/plan` invokes it as a fallback when the PRD has no milestones. `plan-review` extends the agile-coach agent's check list with milestone coverage / DAG / testable-exit-criteria checks. No PRD write-back from `/plan` — the sidecar is the live source after planning.

**Tech Stack:** Markdown-defined Claude Code skills, JSON sidecar schema, shell helpers (`render-markdown.sh`), `uv run` for Python helpers. RED-GREEN testing via subagent runs per CLAUDE.md.

**Spec:** `docs/superpowers/specs/2026-05-13-prd-milestones-design.md` (commit `f2ea1bf`).

**Conventions:**
- All paths below are relative to repo root (`/Users/apple/projects/infraspecdev/tesseract/`).
- All commits go on branch `worktree-prd-milestones-spec` in the worktree at `.claude/worktrees/prd-milestones-spec/`.
- RED-GREEN testing is mandatory for any skill edit (CLAUDE.md). Each skill-edit task includes a baseline subagent run BEFORE the edit and a verification run AFTER.

---

## File map (decomposition)

| File | Responsibility | Tasks |
|---|---|---|
| `shield/skills/general/milestone-coverage/SKILL.md` | **NEW**: milestone proposal skill. Defines input contract (personas/goals/stories), dispatches PM + agile-coach in parallel, merges proposals, surfaces conflicts. | Task 4 |
| `shield/skills/general/milestone-coverage/templates.md` | **NEW**: prompt templates passed to PM + agile-coach agents; merge-rules cheat sheet; output JSON shape. | Task 4 |
| `shield/skills/general/prd-docs/templates.md` | Add Milestones table to standard scaffold §13 (reshape) and lean scaffold (new §6, renumber). | Task 1 |
| `shield/skills/general/prd-docs/SKILL.md` | Invoke `milestone-coverage` at the right step for standard (after §6) and lean (after §5). | Task 5 |
| `shield/skills/general/prd-docs/meta-schema.md` | Bump `rubric_version`. Document scaffold-version semantics. | Task 6 |
| `shield/skills/general/plan-docs/sidecar-schema.md` | Add `milestones[]` and `milestone_id` field, document back-compat rule. | Task 2 |
| `shield/skills/general/plan-docs/SKILL.md` | New Step 1b (milestone resolution); revised story-generation order (milestone-by-milestone). | Task 7 |
| `shield/skills/general/plan-docs/templates.md` | `plan.html` grouped-by-milestone rendering with status rollup. | Task 8 |
| `shield/skills/general/plan-review/scoring.md` (or agent files under `agents/`) | Extend agile-coach checks: coverage, DAG, milestone_id validity, testable exit criteria. | Task 9 |
| `shield/skills/general/summarize/SKILL.md` | Plan-summary template mentions milestones when present. | Task 10 |
| `shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md` | **NEW**: fixture used by RED-GREEN. | Task 3 |
| `shield/skills/general/prd-docs/test-fixtures/with-milestones-lean.md` | **NEW**: fixture used by RED-GREEN. | Task 3 |
| `shield/skills/general/prd-docs/test-fixtures/without-milestones.md` | **NEW**: back-compat fixture (no milestones present). | Task 3 |
| `shield/skills/general/plan-docs/test-fixtures/plan-with-milestones.json` | **NEW**: positive sidecar fixture. | Task 3 |
| `shield/skills/general/plan-docs/test-fixtures/plan-cycle.json` | **NEW**: negative sidecar fixture (depends_on cycle). | Task 3 |
| `shield/skills/general/plan-docs/test-fixtures/plan-dangling-milestone-id.json` | **NEW**: negative sidecar fixture (story → missing milestone). | Task 3 |
| `.claude-plugin/marketplace.json` | Bump `shield` plugin version. | Task 11 |

---

## Task 1: Add milestone fields to PRD templates (standard + lean)

**Files:**
- Modify: `shield/skills/general/prd-docs/templates.md`

**Rationale:** Templates are the source of truth for the PRD scaffold. Update these first so other tasks have something concrete to invoke / fixture against.

- [ ] **Step 1: Read current templates.md to locate the standard §13 block and the lean variant block**

Run: `grep -n "## 13. Rollout plan\|## Lean variant" shield/skills/general/prd-docs/templates.md`
Expected: Two line numbers — one for standard §13, one for the lean variant header.

- [ ] **Step 2: Replace standard §13 with the milestone-first reshape**

In `shield/skills/general/prd-docs/templates.md`, replace the existing `## 13. Rollout plan` block (the one inside the standard scaffold's fenced code block) with:

```markdown
## 13. Rollout plan

### Milestones
| ID | Name | Outcome | Exit criteria | Depends on |
|---|---|---|---|---|
| M1 | <short user-language name> | <what ships, in user language> | <testable list — what facts must be true to declare done> | — |
| M2 | … | … | … | M1 |

### Rollout mechanics
- Flag plan: <feature flag>
- Canary: <staged rollout slices>
- Kill-switch: <criteria>
- Abort thresholds: <specific metric values>
- Data migration: <plan if touching existing data>
- Backward compatibility: <commitments>
```

Preserve everything outside §13 unchanged.

- [ ] **Step 3: Update the lean variant to add new §6 Milestones and renumber**

In the same file, locate the `## Lean variant (7 sections)` block. Replace the lean scaffold's fenced markdown to renumber from 7 → 8 sections:

```markdown
# <Feature name>

## 1. Header
(Same Header table as standard)

## 2. Problem & context
What's broken, who hurts, baseline data, why now.

## 3. Target users / personas
| ID | Persona | Goals | Frictions today |

## 4. Goals & non-goals
### Goals
### Non-goals

## 5. Success metrics
| Metric | Type | Target | Counter |

## 6. Milestones
| ID | Name | Outcome | Exit criteria | Depends on |
|---|---|---|---|---|
| M1 | <name> | <outcome> | <testable list> | — |

## 7. Open questions

## 8. Out of scope / Non-goals

---

> **This is a lean PRD.** It intentionally omits the following standard sections:
> - Section 6 — User stories & scenarios
> - Section 7 — Functional requirements
> - Section 8 — Non-functional requirements
> - Section 9 — RBAC & permissions matrix
> - Section 10 — Dependencies
> - Section 11 — Risks & mitigations
> - Section 12 — Assumptions
> - Section 13 — Rollout plan (rollout mechanics; lean keeps only the Milestones half)
> - Section 14 — Cost & resource impact
> - Section 15 — GTM & customer-comms
> - Section 16 — Support / CX impact
>
> If scope grows or stakeholders need more detail, run `/prd` again — Shield
> will offer to add specific sections or upgrade to `standard`.
```

- [ ] **Step 4: Verify the file parses and renders by running the existing render helper against a fixture**

This template is consumed at PRD-author time, not rendered standalone. Smoke test by reading the file end-to-end to confirm structural integrity:

Run: `grep -c "^## " shield/skills/general/prd-docs/templates.md`
Expected: ≥3 (standard scaffold, lean variant, story template; plus HTML render template sections).

Run: `awk '/^```markdown/{c++} END{print c}' shield/skills/general/prd-docs/templates.md`
Expected: ≥2 (one fenced block per scaffold variant, plus the story template block).

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/prd-docs/templates.md
git commit -m "feat(shield): add milestones table to PRD standard §13 and lean §6"
```

---

## Task 2: Add milestones[] + milestone_id to plan sidecar schema

**Files:**
- Modify: `shield/skills/general/plan-docs/sidecar-schema.md`

**Rationale:** The schema doc is what every consumer (plan-docs, plan-review, plan.html template, pm-sync) reads. Update before any flow logic depends on the new fields.

- [ ] **Step 1: Read the current schema to confirm existing shape**

Run: `cat shield/skills/general/plan-docs/sidecar-schema.md`
Expected: ~56-line file with the JSON template + Rules section.

- [ ] **Step 2: Replace the schema example to add `milestones[]` and per-story `milestone_id`**

Replace the entire JSON fenced block in `shield/skills/general/plan-docs/sidecar-schema.md` with:

```jsonc
{
  "version": "1.1",
  "project": "<project name from .shield.json>",
  "name": "<kebab-case-plan-name>",
  "phase": "<phase name>",
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

- [ ] **Step 3: Update the Rules section to cover new fields + back-compat**

Replace the `## Rules` section in the same file with:

```markdown
## Rules

- `version` is now `"1.1"` (was `"1.0"` pre-milestones). Older sidecars (`"1.0"` or missing `version`) are treated as back-compat — see below.
- Every epic MUST have at least 1 story.
- Every story MUST have at least 1 acceptance criterion.
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

### Back-compat (single implicit milestone)

A sidecar with `milestones: []` and every story's `milestone_id: null` is treated as a **single implicit milestone covering all stories**. `plan-review` does not flag this — it is the back-compat path for plans authored before this schema version or for explicit user opt-out.
```

- [ ] **Step 4: Verify schema doc parses and has both shapes documented**

Run: `grep -n "milestones\|milestone_id" shield/skills/general/plan-docs/sidecar-schema.md`
Expected: ≥6 hits (in JSON example + Rules subsections).

Run: `grep -n "Back-compat\|implicit milestone" shield/skills/general/plan-docs/sidecar-schema.md`
Expected: at least one match for each (back-compat clause documented).

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/plan-docs/sidecar-schema.md
git commit -m "feat(shield): add milestones[] and per-story milestone_id to plan.json schema"
```

---

## Task 3: Add test fixtures for RED-GREEN

**Files:**
- Create: `shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md`
- Create: `shield/skills/general/prd-docs/test-fixtures/with-milestones-lean.md`
- Create: `shield/skills/general/prd-docs/test-fixtures/without-milestones.md`
- Create: `shield/skills/general/plan-docs/test-fixtures/plan-with-milestones.json`
- Create: `shield/skills/general/plan-docs/test-fixtures/plan-cycle.json`
- Create: `shield/skills/general/plan-docs/test-fixtures/plan-dangling-milestone-id.json`

**Rationale:** Fixtures unblock RED-GREEN testing for Tasks 4–9. Created before the skill / flow edits so each subsequent task can run baseline (RED) immediately.

- [ ] **Step 1: Verify the fixture directories exist (they do for prd-docs; create for plan-docs)**

Run: `ls shield/skills/general/prd-docs/test-fixtures/ && ls shield/skills/general/plan-docs/test-fixtures/ 2>&1`
Expected: prd-docs/test-fixtures lists existing files; plan-docs/test-fixtures does not exist yet → output includes "No such file or directory" for the second path.

Run: `mkdir -p shield/skills/general/plan-docs/test-fixtures && ls -d shield/skills/general/plan-docs/test-fixtures/`
Expected: directory exists.

- [ ] **Step 2: Create the standard PRD fixture with well-formed milestones**

Create `shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md` with the full standard scaffold filled out for a fake "User authentication" feature. The §13 Milestones table should contain:

```markdown
### Milestones
| ID | Name | Outcome | Exit criteria | Depends on |
|---|---|---|---|---|
| M1 | Login core | Users can log in with email + password | Login endpoint returns 200 + session token on valid credentials; 401 on invalid; rate limiting (10/min) active; failed-login telemetry emitted | — |
| M2 | Password recovery | Users can reset a forgotten password without contacting support | Recovery email delivered within 60s; reset link single-use and 15-min TTL; password-reset telemetry emitted | M1 |

### Rollout mechanics
- Flag plan: `auth_v2` LaunchDarkly flag
- Canary: 1% → 10% → 50% → 100% over 2 weeks
- Kill-switch: revert flag to 0%
- Abort thresholds: login error rate > 2% sustained 5 min
- Data migration: backfill user_credentials table from legacy `users.password_hash`
- Backward compatibility: legacy `/auth/login` route 301s to `/v2/auth/login` for 90 days
```

Fill the rest of §1–17 with minimal-but-realistic content (single persona, 2–3 stories, basic NFRs). The fixture should be ~150 lines.

- [ ] **Step 3: Create the lean PRD fixture with well-formed milestones**

Create `shield/skills/general/prd-docs/test-fixtures/with-milestones-lean.md` using the new 8-section lean scaffold. Section 6 (Milestones) should contain the same 2-row table as above (Login core, Password recovery) but without rollout mechanics. ~50 lines.

- [ ] **Step 4: Create the back-compat fixture (PRD without milestones)**

Create `shield/skills/general/prd-docs/test-fixtures/without-milestones.md` — a standard-scaffold PRD with §13 containing the OLD shape (just rollout mechanics, no Milestones table). Used to verify the `/plan` fallback path (Task 7). ~120 lines.

- [ ] **Step 5: Create the positive sidecar fixture**

Create `shield/skills/general/plan-docs/test-fixtures/plan-with-milestones.json` matching the new schema in Task 2: `version: "1.1"`, 2 milestones (M1, M2 with M2 depends on M1), 1 epic with 4 stories — 2 mapped to M1, 2 mapped to M2.

- [ ] **Step 6: Create the cycle negative fixture**

Create `shield/skills/general/plan-docs/test-fixtures/plan-cycle.json` — same as above but with `M1.depends_on: ["M2"]` AND `M2.depends_on: ["M1"]`. Used by plan-review (Task 9) to verify cycle detection.

- [ ] **Step 7: Create the dangling-milestone-id negative fixture**

Create `shield/skills/general/plan-docs/test-fixtures/plan-dangling-milestone-id.json` — `milestones[]` contains only `M1`, but one of the stories references `milestone_id: "M2"`. Used by plan-review (Task 9) to verify dangling-reference detection.

- [ ] **Step 8: Verify all six fixtures exist and parse**

Run: `ls shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md shield/skills/general/prd-docs/test-fixtures/with-milestones-lean.md shield/skills/general/prd-docs/test-fixtures/without-milestones.md shield/skills/general/plan-docs/test-fixtures/plan-with-milestones.json shield/skills/general/plan-docs/test-fixtures/plan-cycle.json shield/skills/general/plan-docs/test-fixtures/plan-dangling-milestone-id.json`
Expected: all six paths printed (no "No such file or directory").

Run: `for f in shield/skills/general/plan-docs/test-fixtures/*.json; do python3 -c "import json; json.load(open('$f'))" && echo "OK: $f"; done`
Expected: three `OK:` lines.

- [ ] **Step 9: Commit**

```bash
git add shield/skills/general/prd-docs/test-fixtures/ shield/skills/general/plan-docs/test-fixtures/
git commit -m "test(shield): add RED-GREEN fixtures for PRD/plan milestones"
```

---

## Task 4: Create shield:milestone-coverage skill

**Files:**
- Create: `shield/skills/general/milestone-coverage/SKILL.md`
- Create: `shield/skills/general/milestone-coverage/templates.md`

**Rationale:** The new shared skill is the heart of the design. It's invoked from both `/prd` and `/plan`, so it ships before either flow change consumes it.

- [ ] **Step 1: RED — verify baseline (no milestone-coverage skill exists)**

Run: `ls shield/skills/general/milestone-coverage/ 2>&1`
Expected: "No such file or directory" — confirms the skill is new.

Dispatch a subagent with the Task tool, subagent_type `general-purpose`, prompt:
> "Read `shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md` and the existing skill `shield/skills/general/prd-docs/SKILL.md`. Imagine you are running `/prd` on a new feature with these personas, goals, and stories: [paste stories from the fixture]. Without using any skill named `shield:milestone-coverage`, propose milestones for this feature. Return JSON with `id`, `name`, `outcome`, `exit_criteria`, `depends_on` per milestone."

Expected baseline (RED): subagent produces *some* milestone proposal but no dual-agent (PM + agile-coach) split, no conflict surfacing, no merge rules. The output will look ad hoc and miss the per-agent rationale that the skill is supposed to provide. Capture this output to `/tmp/red-task4.json` for comparison.

- [ ] **Step 2: Create `shield/skills/general/milestone-coverage/SKILL.md`**

Write the file with this content:

```markdown
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
```

- [ ] **Step 3: Create `shield/skills/general/milestone-coverage/templates.md`**

Write the file with the two agent prompts + merge rules. Structure:

```markdown
# Milestone Coverage — Templates

## Agent prompts

### Product Manager prompt

Pass to `shield:product-manager-reviewer` with subagent_type `shield:product-manager-reviewer`:

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

Pass to `shield:agile-coach-reviewer` with subagent_type `shield:agile-coach-reviewer`:

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
- `source_agents`: `["product-manager-reviewer", "agile-coach-reviewer"]`.
- `conflicts`: list of fields where the two agents disagreed (e.g., `["depends_on"]`).

### 3. Unmatched milestones

- PM-only milestone → keep, `source_agents: ["product-manager-reviewer"]`.
- Agile-coach-only milestone → keep, `source_agents: ["agile-coach-reviewer"]`. Note for the user: this often signals a technical milestone (e.g., infrastructure hardening) that doesn't map to a user-visible outcome.

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
```

- [ ] **Step 4: GREEN — verify the skill exists and is referenced correctly**

Run: `ls shield/skills/general/milestone-coverage/`
Expected: `SKILL.md  templates.md`

Run: `grep -n "milestone-coverage" shield/skills/general/milestone-coverage/SKILL.md | head -3`
Expected: at least one match for the skill name.

Dispatch a subagent (general-purpose) with prompt:
> "Read `shield/skills/general/milestone-coverage/SKILL.md` and `shield/skills/general/milestone-coverage/templates.md`. Walk through how you would invoke this skill given personas P1, P2 and goals G1, G2, G3 and 5 stories from `shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md`. Describe: (a) which two agents you dispatch, (b) what each agent gets as input, (c) how you merge their proposals, (d) what you surface as `open_conflicts`. Be specific."

Expected (GREEN): subagent correctly identifies the dual-dispatch pattern (PM + agile-coach in parallel), describes the per-agent prompt inputs, names the merge rules (intersection for depends_on, union for exit_criteria, name matching), and gives a concrete `open_conflicts` example. Compare against `/tmp/red-task4.json` — the GREEN output should be structured, dual-source, and conflict-aware in a way the RED was not.

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/milestone-coverage/
git commit -m "feat(shield): add milestone-coverage skill — PM + agile-coach merged proposals"
```

---

## Task 5: Wire milestone-coverage into /prd flow

**Files:**
- Modify: `shield/skills/general/prd-docs/SKILL.md`

**Rationale:** Now that `milestone-coverage` exists, `/prd` invokes it at the right step for both scaffolds.

- [ ] **Step 1: RED — baseline a `/prd` run on a feature without the wiring**

Dispatch a subagent (general-purpose) with prompt:
> "Read `shield/skills/general/prd-docs/SKILL.md` and `shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md`. Imagine you are running `/prd` for a new feature with the personas, goals, and stories from this fixture. Walk through the workflow step-by-step. Specifically: does the workflow include a step where milestones are proposed by agents before §13 is filled? Quote the exact step text if so; say 'no such step' if not."

Expected RED: subagent reports "no such step" — Section 13 walk is purely user-driven in the current SKILL.md.

- [ ] **Step 2: Read current SKILL.md to find the Section 13 walk + Story-coverage invocation**

Run: `grep -n "Section 6\|Walk Sections\|story-coverage\|Section 13" shield/skills/general/prd-docs/SKILL.md`
Expected: line numbers for the existing step skeleton + workflow section.

- [ ] **Step 3: Add the milestone-coverage invocation step to the Step Skeleton table**

In `shield/skills/general/prd-docs/SKILL.md`, locate the Step Skeleton table (around lines 33–47 in the current file). Add a new row between the current Step 7 (story-coverage invocation) and Step 8 (walk remaining sections):

| 7a | Invoke `shield:milestone-coverage` skill once stories are filled (standard) or after Section 5 metrics (lean); user refines proposal | always; lean uses goals+personas only as input | conditional |

Renumber subsequent steps accordingly (Step 8 → 8, Step 9 → 9, etc. — keep current numbering and only insert 7a to avoid renumbering everywhere).

- [ ] **Step 4: Add Workflow §7a — Milestone scaffolding**

In the Workflow section of the same file, add a new subsection between the current §7 (Story coverage scaffolding) and §8 (Walk remaining sections):

```markdown
### 7a. Milestone scaffolding (both scaffolds)

After Section 6 (standard, once stories are filled) or after Section 5 (lean, once metrics are filled), invoke `shield:milestone-coverage` with:

- `personas`: from Section 3
- `goals`: from Section 4
- `stories`: from Section 6 (standard only — pass empty for lean)
- `feature_domain`: same inference as story-coverage
- `success_metrics`: from Section 5 (optional)

The skill returns `milestones[]` plus `open_conflicts[]`. Present them to the user:

```
Milestone proposal — refine before approving:

  [x] M1 — Login core (PM + agile-coach agreed)
       Outcome: Users can log in with email + password
       Exit: Login endpoint returns 200 + session token...
       Depends on: —

  [x] M2 — Password recovery (PM + agile-coach disagreed on depends_on — see below)
       Outcome: Users can reset a forgotten password without contacting support
       Exit: Recovery email delivered within 60s; reset link single-use, 15-min TTL
       Depends on: M1
       ⚠ Conflict: PM proposed `depends_on: []`. Agile-coach proposed `depends_on: [M1]`.
         Agile-coach reason: "Recovery needs the session middleware shipped in M1."
         Decision needed: keep [M1] / clear / edit.

Pick which to keep (defaults to all suggested), edit fields per row, or add your own.
```

Selected and edited milestones are written into:
- **Standard:** §13 Milestones table (then walk §13 rollout-mechanics fields next as today).
- **Lean:** §6 Milestones table (then proceed to §7 Open questions).

If the user declines (empty selection), leave the Milestones table empty. `/plan` will re-run `shield:milestone-coverage` as a fallback if needed.
```

- [ ] **Step 5: Update Step 8 (Walk remaining sections) to acknowledge §13 is partially scaffolded for standard**

In the existing §8 description, change:

> Walk Sections 5, then Section 6 (filling in content for the scaffolded stories), then 7-17 in order.

to:

> Walk Sections 5, then Section 6 (filling in content for the scaffolded stories), then 7-12 in order. Section 13's Milestones table is already populated by §7a above — walk only the rollout-mechanics fields beneath it. Then walk 14-17.

For lean, change:

> For lean PRDs, only walk the lean scaffold's sections 5 (Success metrics), 6 (Open questions), 7 (Out of scope)

to:

> For lean PRDs, walk the lean scaffold's sections 5 (Success metrics), then §6 Milestones is already populated by §7a above (skip ahead), then walk 7 (Open questions), 8 (Out of scope).

- [ ] **Step 6: GREEN — verify a fresh subagent reads the updated flow correctly**

Dispatch a subagent (general-purpose) with the same prompt as Step 1. Expected GREEN: subagent now reports "yes, there is a step — §7a Milestone scaffolding — that invokes `shield:milestone-coverage` after Section 6 (standard) or after Section 5 (lean). The user refines before milestones are written to §13 or §6 respectively." Compare against the RED baseline — the GREEN output should explicitly cite §7a.

- [ ] **Step 7: Commit**

```bash
git add shield/skills/general/prd-docs/SKILL.md
git commit -m "feat(shield): /prd invokes milestone-coverage after stories (std) or metrics (lean)"
```

---

## Task 6: Bump prd.meta.json rubric_version

**Files:**
- Modify: `shield/skills/general/prd-docs/meta-schema.md`

**Rationale:** `prd-review` reads `rubric_version` to know which scaffold version a PRD was authored against. Bumping it lets reviewers branch behavior in the future without breaking back-compat.

- [ ] **Step 1: Read current meta-schema to find the version field**

Run: `grep -n "rubric_version\|version" shield/skills/general/prd-docs/meta-schema.md`
Expected: at least one match showing the current `rubric_version` value (e.g., `"1.0"`).

- [ ] **Step 2: Bump `rubric_version` from current to next (e.g., `"1.0"` → `"1.1"`)**

Edit `shield/skills/general/prd-docs/meta-schema.md`. Locate the JSON example and any text describing the version. Change the value from its current string to the next minor (e.g., `"1.0"` → `"1.1"`). If a different version scheme is in use, increment the minor component.

Also add a short note documenting what the bump means:

> `rubric_version: "1.1"` adds the §13 Milestones table (standard) and §6 Milestones section (lean). `prd-review` reading a `1.0` PRD MUST NOT expect milestones; reading a `1.1` PRD MAY expect them. The version bump is scaffold-version awareness only — it does NOT introduce a new scored rubric *dimension* (that is a deferred follow-up; see `docs/superpowers/specs/2026-05-13-prd-milestones-design.md` §8).

- [ ] **Step 3: Verify the bump**

Run: `grep -n "rubric_version" shield/skills/general/prd-docs/meta-schema.md`
Expected: shows the new version string (e.g., `"1.1"`) in at least one place.

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/prd-docs/meta-schema.md
git commit -m "feat(shield): bump prd.meta.json rubric_version for milestone-aware scaffold"
```

---

## Task 7: Wire milestone resolution into /plan flow

**Files:**
- Modify: `shield/skills/general/plan-docs/SKILL.md`

**Rationale:** `/plan` now reads PRD milestones (if present), or invokes `milestone-coverage` as a fallback, and generates stories milestone-by-milestone.

- [ ] **Step 1: RED — baseline a `/plan` run against the without-milestones fixture**

Dispatch a subagent (general-purpose):
> "Read `shield/skills/general/plan-docs/SKILL.md` and `shield/skills/general/prd-docs/test-fixtures/without-milestones.md`. Imagine you are running `/plan` against this PRD. Walk through the workflow. Specifically: when the PRD has no milestones, does the workflow prompt the user to define them, or does it skip ahead to generating stories? Quote the exact step text."

Expected RED: subagent reports the current behavior — no milestone resolution step exists; stories are generated flat.

- [ ] **Step 2: Read current SKILL.md Workflow section to find Step 1a (PRD detection)**

Run: `grep -n "Step 1a\|PRD detection\|Detect prior PRD\|source_prd" shield/skills/general/plan-docs/SKILL.md`
Expected: a handful of line numbers covering the existing PRD-detection step.

- [ ] **Step 3: Add new Step 1b (milestone resolution) to the Step Skeleton table**

In `shield/skills/general/plan-docs/SKILL.md`, locate the Step Skeleton table and add a new row between Step 2 (Check for prior research) and Step 3 (Generate plan.json sidecar):

| 2a | Milestone resolution — extract from PRD §13/§6 or invoke `shield:milestone-coverage` as fallback; user refines | always | Yes |

- [ ] **Step 4: Add Workflow §2a — Milestone resolution**

In the Workflow section, add a subsection between §2 (Gather context) and §3 (Read .shield.json) — note the existing numbering is sloppy (two §3s); position it logically before the sidecar is generated:

```markdown
### 2a. Milestone resolution

Before generating stories, resolve milestones:

1. **If a PRD was detected (Step 1a) and it contains milestones** (Section 13 standard, Section 6 lean): extract them. Present to the user for confirmation. Allow edits (rename, add exit criteria, change depends_on). Copy approved milestones into the sidecar `milestones[]`.

2. **If a PRD was detected but has no milestones** (or an empty Milestones table — back-compat case for PRDs authored against rubric_version 1.0): invoke `shield:milestone-coverage` with:
   - `personas`: from PRD Section 3
   - `goals`: from PRD Section 4
   - `stories`: from PRD Section 6 (if present; empty for lean)
   - `feature_domain`: inferred or read from PRD type-detection metadata

   Present merged proposal + `open_conflicts` to the user (same flow as `/prd` §7a). User refines. Sidecar-only — do NOT write back to the PRD.

3. **If no PRD exists:** invoke `shield:milestone-coverage` with whatever inputs were gathered during requirements (Step 2). Sidecar-only.

4. **If the user explicitly opts out of milestones:** sidecar stores `milestones: []`. All subsequent stories will have `milestone_id: null`. This is the back-compat single-implicit-milestone case (see `sidecar-schema.md`).
```

- [ ] **Step 5: Revise story-generation order in Workflow §3 (sidecar generation)**

Locate the workflow line that says (paraphrased): "Generate sidecar JSON first — write `{output_dir}/{feature}/plan.json` with epics, stories, tasks, and acceptance criteria"

Replace with:

```markdown
3. **Generate sidecar JSON first (milestone-by-milestone)** — write `{output_dir}/{feature}/plan.json`:
   - For each milestone in `milestones[]` (resolved in §2a), generate the epics and stories needed to satisfy that milestone's exit criteria. Each story is born with `milestone_id` set to the milestone's `id`.
   - When `milestones: []` (opt-out case), generate stories flat with `milestone_id: null` on each — the back-compat path.
   - Acceptance criteria per story remain the same testable standard; exit criteria on the milestone are the higher-level rollup.
```

- [ ] **Step 6: GREEN — verify the new flow against the without-milestones fixture**

Dispatch a subagent with the same prompt as Step 1. Expected GREEN: subagent now reports the new §2a step, names `shield:milestone-coverage` as the fallback invocation, and notes that stories are generated milestone-by-milestone with `milestone_id` set per story.

- [ ] **Step 7: Commit**

```bash
git add shield/skills/general/plan-docs/SKILL.md
git commit -m "feat(shield): /plan resolves milestones first, then generates stories per milestone"
```

---

## Task 8: Update plan.html template to group by milestone

**Files:**
- Modify: `shield/skills/general/plan-docs/templates.md`

**Rationale:** Users see `plan.html` — grouping stories under milestone headers with status rollups is the primary surface for the new structure.

- [ ] **Step 1: Read current templates.md to find the plan.html section template**

Run: `grep -n "plan.html\|Stories summary\|Story Format\|Epic metadata" shield/skills/general/plan-docs/templates.md`
Expected: line numbers for the existing detailed-plan template.

- [ ] **Step 2: Add a "Milestones" section to the plan.html template before "Stories"**

In `shield/skills/general/plan-docs/templates.md`, after the "Epic metadata" subsection and before "Stories summary table", insert a new subsection. The HTML structure renders the sidecar's `milestones[]` as a series of collapsible blocks, each containing the stories with that `milestone_id`. Include a status rollup line per milestone (e.g., `M1 — 3/5 stories ready`).

Concretely, add this block to the plan.html template specification:

```markdown
### Milestones section (rendered from `sidecar.milestones[]`)

Render this block immediately after the Epic metadata and before the flat Stories summary table. When `sidecar.milestones` is empty (back-compat), skip this entire block and fall through to the flat stories list as today.

```html
<section class="milestones">
  <h2>Milestones</h2>
  {{#each sidecar.milestones}}
  <div class="milestone" id="milestone-{{id}}">
    <h3>
      {{id}} — {{name}}
      <span class="rollup">
        {{count_stories_in_status this 'ready'}}/{{count_stories this}} ready
      </span>
    </h3>
    <p class="outcome"><strong>Outcome:</strong> {{outcome}}</p>
    <div class="exit-criteria">
      <strong>Exit criteria:</strong>
      <ul>
        {{#each exit_criteria}}<li>{{this}}</li>{{/each}}
      </ul>
    </div>
    {{#if depends_on.length}}
    <p class="depends-on"><strong>Depends on:</strong> {{join depends_on ", "}}</p>
    {{/if}}
    <div class="stories-in-milestone">
      <h4>Stories</h4>
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Week</th><th>Status</th></tr></thead>
        <tbody>
          {{#each (stories_for_milestone this.id sidecar.epics)}}
          <tr>
            <td>{{id}}</td>
            <td>{{name}}</td>
            <td>{{week}}</td>
            <td>{{status}}</td>
          </tr>
          {{/each}}
        </tbody>
      </table>
    </div>
  </div>
  {{/each}}
</section>
```

Stories inside each milestone block are ordered by `week` ascending (sprint cadence emerges from `week` grouping — e.g., week 1–2 = Sprint 1).

Add CSS to the existing stylesheet for `.milestones`, `.milestone`, `.rollup` (small muted text right-aligned in the h3), and `.exit-criteria`. Style consistent with existing tables.
```

(If the existing templates.md uses raw HTML rather than Handlebars-like syntax, adapt the pseudo-template to match the existing rendering approach — the spec says "the renderer is markdown-it-py via render-markdown.sh"; for HTML scaffolding, the generator writes HTML directly. The block above is illustrative — the executing engineer should match the existing template style.)

- [ ] **Step 3: Verify the template addition**

Run: `grep -n "milestones\|milestone-{{id}}\|rollup" shield/skills/general/plan-docs/templates.md`
Expected: ≥3 matches in the new block.

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/plan-docs/templates.md
git commit -m "feat(shield): plan.html groups stories by milestone with status rollup"
```

---

## Task 9: Extend agile-coach checks in plan-review

**Files:**
- Modify: one of `shield/skills/general/plan-review/scoring.md` OR `shield/skills/general/plan-review/personas.md` OR an agent file under `shield/agents/` (locate the existing agile-coach check definitions first)

**Rationale:** The four new checks (milestone coverage, milestone_id validity, testable exit criteria, DAG) land on the existing `shield:agile-coach-reviewer` agent — already always dispatched for plans with stories.

- [ ] **Step 1: Locate where agile-coach evaluation points are defined**

Run: `grep -rn "agile-coach\|sprint-readiness\|dependency ordering" shield/skills/general/plan-review/ shield/agents/ 2>/dev/null | head -20`
Expected: matches in `scoring.md`, `personas.md`, or an `agents/` markdown file. Use the location of existing eval points (e.g., "dim 4 eval points 4f/4g" mentioned in story-coverage SKILL.md) as the model.

- [ ] **Step 2: RED — baseline plan-review against the cycle fixture**

Dispatch a subagent with subagent_type `shield:agile-coach-reviewer`:
> "Review the plan in `shield/skills/general/plan-docs/test-fixtures/plan-cycle.json`. Evaluate sprint-readiness, dependency ordering, sizing, and AC testability. Score per your usual rubric and list any issues."

Expected RED: agile-coach grades stories on AC and dependencies, but does NOT catch the `depends_on` cycle between M1 and M2 (because milestone-level checks don't exist yet). Capture output to `/tmp/red-task9.json`.

Repeat with the dangling-milestone-id fixture (`plan-dangling-milestone-id.json`). Expected RED: agile-coach does not flag the dangling reference.

- [ ] **Step 3: Add four new eval points to the agile-coach scoring location**

Once Step 1 has located the file, append four new evaluation points to agile-coach's check list. Each follows the existing eval-point format. Suggested content:

```markdown
### Milestone coverage (4h — NEW)

For every milestone in `sidecar.milestones[]`, verify ≥1 story has `milestone_id` equal to that milestone's `id`. A milestone with zero covering stories is **P0** ("milestone M1 'Login core' has no covering stories — plan is incomplete").

### Milestone reference integrity (4i — NEW)

For every story, verify `milestone_id` is either `null` or matches an `id` in `sidecar.milestones[]`. A dangling reference (story → milestone M5, but `milestones[]` has only M1, M2) is **P0** ("story EPIC-1-S3 references milestone M5 which does not exist").

### Milestone exit criteria testability (4j — NEW)

For every milestone, verify each `exit_criteria` item is a testable fact (same standard you apply to story AC). Vague items like "login works" or "users are happy" are **P1**. Specific items like "endpoint returns 200 + session token on valid credentials" pass.

### Milestone DAG integrity (4k — NEW)

Build a directed graph from `milestones[].depends_on`. Detect cycles via DFS. A cycle (e.g., M1 depends_on M2; M2 depends_on M1) is **P0** ("milestone dependency cycle: M1 → M2 → M1").

### Back-compat handling

When `sidecar.milestones` is empty AND every story's `milestone_id` is `null`, skip all four new checks (single-implicit-milestone case). This is NOT a quality issue — it is the explicit back-compat path.
```

The exact severity values (P0/P1) should match the severity conventions used by other eval points in the same file.

- [ ] **Step 4: GREEN — re-run agile-coach against the negative fixtures**

Dispatch the same subagent with the same prompt as Step 2 against `plan-cycle.json`.
Expected GREEN: agile-coach now flags the M1↔M2 cycle as P0 under "Milestone DAG integrity".

Repeat against `plan-dangling-milestone-id.json`.
Expected GREEN: agile-coach now flags the dangling `milestone_id` reference as P0 under "Milestone reference integrity".

Run a third subagent against `plan-with-milestones.json` (positive case).
Expected GREEN: no milestone-related issues raised; the four new checks pass cleanly.

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/plan-review/  # or the agents/ path depending on where the eval points live
git commit -m "feat(shield): agile-coach gains milestone coverage / DAG / id-validity / exit-criteria checks"
```

---

## Task 10: Update summarize plan-summary template

**Files:**
- Modify: `shield/skills/general/summarize/SKILL.md`

**Rationale:** The plan summary surfaces high-level structure; it should mention milestones when present.

- [ ] **Step 1: Read current summarize SKILL.md to find the plan-summary template**

Run: `grep -n "plan\|milestone\|summary\|epic" shield/skills/general/summarize/SKILL.md`
Expected: locate the section that handles plan summaries (vs research summaries, PRD summaries, etc.).

- [ ] **Step 2: Add a Milestones bullet to the plan summary template**

In the plan-summary section of the file, add a bulleted line that surfaces milestones when present in the sidecar. Conditional rendering: if `sidecar.milestones` has ≥1 entry, render:

```markdown
- **Milestones (N):** M1 Login core; M2 Password recovery (depends on M1); …
```

If `sidecar.milestones` is empty, omit the line.

- [ ] **Step 3: Verify the edit**

Run: `grep -n "Milestones\|milestone" shield/skills/general/summarize/SKILL.md`
Expected: at least one match in the plan-summary template area.

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/summarize/SKILL.md
git commit -m "feat(shield): summarize plan output mentions milestones when present"
```

---

## Task 11: Bump shield plugin version

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Rationale:** Per CLAUDE.md, plugin version lives ONLY in `marketplace.json` for relative-path plugins. Bump on every plugin change.

- [ ] **Step 1: Read current shield version**

Run: `grep -n '"version"' .claude-plugin/marketplace.json | head -3`
Expected: shows current `"version": "2.14.0"` (or whatever the latest is) for the shield entry.

- [ ] **Step 2: Bump shield version (minor)**

Edit `.claude-plugin/marketplace.json`. In the shield plugin block, change `"version": "2.14.0"` to `"version": "2.15.0"`.

- [ ] **Step 3: Verify**

Run: `grep -A1 '"name": "shield"' .claude-plugin/marketplace.json | head -5`
Expected: shows the new version.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump version to 2.15.0 for milestones feature"
```

---

## Task 12: Final integration smoke test

**Files:**
- No edits — verification only.

**Rationale:** End-to-end RED-GREEN against the full feature: run `/prd` against a fixture, then `/plan` against the resulting PRD, and confirm milestones flow all the way through.

- [ ] **Step 1: Smoke test `/prd` standard flow**

Dispatch a subagent (general-purpose) with prompt:
> "Read the updated skills in `shield/skills/general/`. Walk through a `/prd` invocation for a new feature with personas P1 'Anika', goals G1 'reset password', G2 'log in', and a feature domain of 'auth'. Stories: S1 happy-path login, S2 password reset, S3 account lockout. At the milestone-scaffolding step (§7a), describe (a) which agents are dispatched, (b) what input they receive, (c) what the merged proposal looks like, (d) how `open_conflicts` would surface to the user."

Expected: the subagent demonstrates the full flow including dual-agent dispatch and conflict surfacing. Capture the response.

- [ ] **Step 2: Smoke test `/plan` flow against a PRD with milestones**

Dispatch a subagent (general-purpose) with prompt:
> "Read the updated `shield/skills/general/plan-docs/SKILL.md`. Walk through a `/plan` invocation against `shield/skills/general/prd-docs/test-fixtures/with-milestones-standard.md`. Describe the milestone-resolution step (§2a), how stories are generated (milestone-by-milestone), and what the resulting sidecar JSON skeleton looks like (key fields only — milestones[], one epic, two stories per milestone with milestone_id set)."

Expected: the subagent describes extracting milestones from §13, presenting for confirmation, then generating stories milestone-by-milestone with each story's `milestone_id` correctly populated.

- [ ] **Step 3: Smoke test `/plan` flow against a PRD without milestones**

Dispatch a subagent (general-purpose) with prompt:
> "Read the updated `shield/skills/general/plan-docs/SKILL.md`. Walk through a `/plan` invocation against `shield/skills/general/prd-docs/test-fixtures/without-milestones.md`. The PRD has no milestones. Describe what happens at §2a, which skill is invoked, and confirm that no write-back to the PRD occurs."

Expected: subagent invokes `shield:milestone-coverage` as fallback, user refines, milestones land in sidecar only, PRD remains untouched.

- [ ] **Step 4: Commit the plan completion marker (no code change — just a tag commit)**

If all three smoke tests pass with the expected GREEN behavior, no commit needed at this step. If any smoke test reveals a gap, file it as a follow-up issue and either fix it (REFACTOR step per CLAUDE.md) or document it as a known limitation in the spec's §8.

```bash
# If a REFACTOR pass is needed, fix the underlying skill/template and recommit.
# Otherwise, this task is verification-only.
git log --oneline -12
# Expected: 11 commits (one per task) on the worktree branch.
```

---

## Self-review

After all tasks complete, run:

```bash
git log --oneline worktree-prd-milestones-spec ^main
```

Expected: ~11 commits, each scoped to one task. Confirm:

1. **Spec coverage:** every section of `docs/superpowers/specs/2026-05-13-prd-milestones-design.md` has at least one task implementing it.
   - §4.1 PRD shape → Task 1
   - §4.2 Sidecar schema → Task 2
   - §4.3 Milestone authoring (new skill) → Task 4
   - §4.4 PRD authoring flow → Task 5
   - §4.5 /plan flow changes → Task 7, Task 8
   - §4.6 plan-review checks → Task 9
   - §4.7 Auxiliary changes → Task 6, Task 10, Task 11
   - §5 Edge cases → covered by fixtures (Task 3) and back-compat clauses in Task 2 (sidecar) + Task 9 (plan-review)
   - §6 Testing plan → all skill-edit tasks include RED-GREEN steps; Task 12 is the integration smoke test

2. **No placeholders:** scan all commits for `TBD`, `TODO`, `FIXME`. Should be zero.

```bash
git diff main..worktree-prd-milestones-spec | grep -i "TBD\|TODO\|FIXME" || echo "clean"
```

Expected: `clean`.

3. **Type consistency:** `milestone-coverage` returns `milestones[]` matching the sidecar schema (Task 2 + Task 4). `/prd` writes the same field names into §13 (Task 1 + Task 5). `/plan` reads §13 into sidecar with the same shape (Task 7). plan-review (Task 9) and summarize (Task 10) read the same fields.

---

## Execution Handoff

After this plan is approved:

**Plan complete and saved to `docs/superpowers/plans/2026-05-13-prd-milestones.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Each task dispatched to a fresh subagent. I review between tasks. Fast iteration.

**2. Inline Execution** — Tasks executed in this session via `superpowers:executing-plans`. Batch with checkpoints.

**Which approach?**
