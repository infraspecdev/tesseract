---
name: implement-feature
description: Use when implementing a feature or story, especially with acceptance criteria to verify. Triggers on /implement, build, create feature, add functionality.
---

# Implement Feature

**Plan sidecar:** `{output_dir}/*/plan.json` (searches all feature plans, updates story status in place)

Structured feature implementation workflow with test-driven development, acceptance criteria confirmation, and continuous lightweight review.

## Input

The user provides one or more of:
- A story ID (e.g., `EPIC-1-S1`) — looked up in the plan sidecar JSON
- A feature description
- A project management card URL or ID
- Context about constraints or approach

## When to Use

- User says "implement", "add", "build", or "create" a feature
- User references a story ID from the plan sidecar
- User provides a project management card URL/ID
- Multi-step implementation that benefits from planning before coding

**When NOT to use:**
- Bug fixes — use systematic-debugging instead
- Single-line changes or trivial edits
- Pure research or exploration tasks

## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 0 | Devcontainer gate (skip if not in repo with `.devcontainer/`) | always | Yes |
| 1 | Load story from plan.json | skip if no plan context | No |
| 2 | Confirm acceptance criteria | always | Yes |
| 3 | Write failing test | always (TDD) | Yes |
| 4 | Implement to pass test | always | Yes |
| 5 | Per-step review | always | Yes |
| 6 | Commit + update AC status in plan.json | always | Yes |
| 7 | Repeat 3-6 for next AC | loop until all AC done | Yes |
| 8 | Update story status in plan.json | always | Yes |

## Phase 0: Devcontainer Gate

Before any other work, run the pre-flight gate to ensure `/implement` runs in the right place:

```bash
SHIELD_REPO=. python3 shield/scripts/devcontainer_gate.py
```

Behavior:
- Inside a devcontainer (`SHIELD_IN_DEVCONTAINER=true`): proceeds silently.
- Outside, but no `.devcontainer/` in the repo: proceeds silently (no devcontainer set up).
- Outside, with `.devcontainer/` present:
  - If `.shield.json` `devcontainer.required = true`: refuses to start; prints reopen instructions; exits.
  - If `false`: proceeds.
  - If `ask` (default): prompts `[y/n/always/never]`. `y`/`always` refuses + instructs reopen; `n`/`never` proceeds.
- Exit code 1 means refuse — `/implement` must not continue.

This is the same logic implemented in `shield/scripts/devcontainer_gate.py` (covered by `test_devcontainer_gate.py`).

**Per-AC tracking:** Step 6 updates each AC's status in `plan.json` immediately after commit — not just at the end (step 8). This means `plan.json` is the per-AC source of truth. On resume, the skill reads `plan.json` to determine which ACs are already done, then continues the loop from the next incomplete AC. `steps.json` tracks coarse workflow position; `plan.json` tracks per-AC completion.

## Workflow

```
1. Load context (sidecar, PM card, or user description)
2. Confirm acceptance criteria with user
3. Plan implementation steps
4. Get user approval
5. TDD: write failing tests, implement, per-step review
6. Final verification against acceptance criteria
```

## Phase 1: Load Context

### From plan sidecar (preferred)

If plan sidecars exist in `{output_dir}/*/plan.json`:
1. Read all plan files found
2. Search for the story by ID across all plans
3. Extract: name, description, tasks, acceptance criteria
4. Show the story details to the user

If no plans found in `{output_dir}/*/plan.json`, check for legacy `shield/docs/plans/<name>.json` and suggest migration.

### From project management card

If a PM card URL/ID is provided and a PM tool is configured:
1. Call `pm_get_capabilities` to verify the adapter is available
2. Fetch the card details
3. Extract: title, description, acceptance criteria, subtasks

### From user description

If no sidecar or PM card, gather requirements by asking:
- What should this feature do?
- What inputs/outputs?
- How do we know it's done?

## Phase 2: Confirm Acceptance Criteria

**ALWAYS confirm acceptance criteria before starting implementation.**

Present the criteria to the user:

```
Story: EPIC-1-S1 — IPAM Pool Hierarchy

Acceptance Criteria:
  1. Regional pools allocate /20 CIDRs
  2. No CIDR overlap across regions
  3. Rollback without data loss

Confirm before starting implementation:
  [a] Proceed as-is
  [b] Edit criteria (add/remove/modify)
  [c] Skip — implement without formal criteria
```

If the user edits criteria:
1. Update the plan sidecar JSON with the new criteria
2. Re-render the HTML plan document from the updated sidecar
3. Optionally sync changes to the PM card

**Do NOT skip this step.** The confirmed criteria are what `/review` will verify against.

## Phase 3: Plan Implementation Steps

Explore the codebase to understand existing patterns, then create a plan:

1. Files to create or modify
2. Steps in execution order
3. Test strategy for each step
4. Which steps can run in parallel

If superpowers is available, delegate to `superpowers:writing-plans` for the plan structure.

## Phase 4: Get User Approval

Show the plan summary. **NEVER proceed without explicit approval.**

## Phase 5: TDD Implementation

For each step:

### 5a. Write failing test
Write a test that captures the expected behavior. Run it — confirm it FAILS.

### 5b. Implement
Write the minimal code to make the test pass.

### 5c. Per-step lightweight review
After each step passes its test:
- Check for obvious issues (logic bugs, style, missing edge cases)
- For the changed file's domain, consult the relevant skill(s):
  - `*.tf` / `*.tfvars` → `shield/skills/terraform/*/SKILL.md`
  - `*.java` / `*.kt` / `*.py` / `*.ts` / `*.js` / `*.go` → `shield/skills/backend/*/SKILL.md`
  - `*.yaml` (K8s manifests) → `shield/skills/kubernetes/*/SKILL.md`
  - `.github/workflows/*.yml` → `shield/skills/github-actions/*/SKILL.md`
- Use the LLM's judgment to pick which skills are applicable to the file. Skip skills that don't apply (e.g., spring-security on a controller file).
- This is NOT a full agent review — keep it focused on what changed in this step. Don't run a comprehensive multi-skill audit; that happens at /review.
- If the file's domain has no matching skill, fall back to general code-quality judgment.

### 5d. Commit
Commit the step immediately:
```bash
git add <specific files>
git commit -m "feat(<feature-name>): step N — <description>"
```

### 5e. Update sidecar status
If implementing from a sidecar story, update the story status:
- When starting: `"status": "in-progress"`
- When complete: `"status": "in-review"`
Re-render HTML after status change.

### 5f. Update last_aligned_with on story close
When a story transitions to `"status": "done"` (or, in the in-review path, when
its acceptance criteria are all met and the PR merges), update the plan-level
`last_aligned_with` field to the current `HEAD` commit SHA:

```bash
last_aligned_with=$(git rev-parse HEAD)
# write into {plan_json}.last_aligned_with
```

This satisfies the schema 1.3 drift-accountability contract — `/plan-review`
and `/pm-sync` surface the value so reviewers can compare plan and code as of
the same commit. The field stays `null` until the first close.

### 5h. Promote feature-folder LLD drafts to canonical (milestone close)

After step 5f (`last_aligned_with` update), check whether the just-closed
story was the **last** open story in its milestone. If yes, walk the
milestone's `touches_lld[]` and promote each draft from
`docs/shield/{feature}/lld-{name}.md` to `docs/lld/{name}.md`.

This step has six sub-steps, executed in order per component:

1. **Look up registry entry.** Read `lld_components[]` for the entry where
   `name == <component>`. Extract `type` and `fork_blob_sha`.

2. **Locate the draft.** `draft_path = docs/shield/{feature}/lld-{name}.md`.
   - If the draft is missing, auto-heal by invoking lld-docs in `draft` mode
     just-in-time; print a loud audit-trail warning (see "Just-in-time
     auto-heal" below).

3. **Concurrency check.** If `docs/lld/{name}.md` exists AND
   `fork_blob_sha` is non-null:
   - Compute `current_sha = blob_sha(docs/lld/{name}.md)` via
     `shield/scripts/lld_blob_sha.py`.
   - If `current_sha != fork_blob_sha`: fork drift detected. Invoke
     lld-docs in `remerge` mode (canonical changed since /plan drafted;
     merge canonical changes into draft). On clean merge, refresh
     `fork_blob_sha = current_sha` in plan.json and proceed. On conflict
     markers in the merged output, **abort** this component's promotion
     and surface a clear remediation message.

4. **Append §14 Changelog row** to the draft:
   ```
   | <milestone_id> | <YYYY-MM-DD> | <milestone.name> | <story_ids touching this component> |
   ```
   Insert at the bottom of the §14 table; preserve all existing rows.

5. **Atomic promote.** `os.replace(draft_path, canonical_path)` (writes via
   `<canonical>.tmp` first, then rename — same atomic contract as lld-docs
   skill's own writes).

6. **Back-fill `design_refs[]` anchors.** Walk all stories in plan.json;
   for each `design_refs[]` entry where `doc == "lld"` AND
   `component == <this component>` AND `anchor_url is null`:
   - Use `shield/scripts/lld_anchor_heuristic.py select_anchor()` with the
     story name and the template's slug allow-list (loaded from
     `shield/schema/lld-sections-<type>.yaml`).
   - Set `anchor_url = "lld-{name}.md#{slug}"`.
   - Update `label = "§{n} {title}"` (look up the slug's number+title from
     the schema).
   - Write the updated plan.json back atomically.

### Just-in-time auto-heal for missing drafts

If step 5h sub-step 2 finds no draft for a component listed in
`touches_lld[]`, just-in-time invoke the lld-docs skill to draft. Print a
loud multi-line warning to the run log AND include it in the run summary:

```
⚠️  DRAFT AUTO-GENERATED AT PROMOTION
    Component: <name>
    The /plan run did not produce docs/shield/{feature}/lld-{name}.md.
    /implement just-in-time-drafted the LLD; the design bypassed human review
    before promotion. Review docs/lld/{name}.md for content quality before
    next /plan-review.
```

Proceed with steps 3 through 6 normally.

### Milestone-close detection

A milestone is closed iff every story whose `milestone_id == <M>` has
`status == "done"`. The just-closed story is the trigger; step 5h runs
when its closure tips the milestone over to all-done.

If multiple stories close in the same /implement session (e.g. batch),
step 5h runs after the LAST one, not after each — the implementation can
short-circuit by checking the milestone state once per session-end.

### Summary output

`/implement` prints one block per promoted LLD:

```
LLD promoted: <component> (<type>)
  Source draft:    docs/shield/{feature}/lld-{component}.md
  Canonical:       docs/lld/{component}.md
  Fork drift:      none | auto-healed | aborted
  Changelog row:   | <M> | <date> | <milestone name> | <story_ids> |
  Anchor backfill: <count> entries updated (<exact-match: X, heuristic: Y, fallback: Z>)
```

### Failure modes

| Failure | Behavior |
|---|---|
| Draft missing AND auto-heal lld-docs invocation fails | Abort this component's promotion; continue with remaining `touches_lld[]` entries; surface as run-end error. |
| Concurrency check produces conflict markers | Abort this component's promotion; print `re-run /plan to refresh fork` and the conflicting section IDs; continue with remaining entries. |
| Atomic rename fails | Abort this component's promotion; the draft and the canonical both remain in their pre-step state (the `.tmp` is cleaned up); surface error. |
| Anchor back-fill: plan.json write-back fails | Roll back the changelog row append (re-read draft from prior state) is NOT attempted — the promotion already happened. Surface "promotion succeeded but design_refs[] back-fill failed; re-run /implement to retry back-fill." |

## Phase 6: Verify Against Acceptance Criteria

After all steps complete:

1. **Run all tests** — every test must pass
2. **Run linters/formatters** — code must be clean
3. **Check each acceptance criterion** against the implementation:

   | Criteria | Status | Evidence |
   |----------|--------|----------|
   | Regional pools allocate /20 CIDRs | Met | main.tf:42 — netmask_length = 20 |
   | No CIDR overlap | Met | tests/overlap.tftest.hcl |

4. **Update sidecar** — mark story as `"in-review"` if all criteria met
5. **Invoke `shield:summarize`** — produce an implementation summary

## Phase 7: Offer Next Steps

- `/review` — run full agent-based code review with AC verification
- `/pm-sync` — update story status in the PM tool

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping AC confirmation | Always confirm before implementing |
| Implementing before tests | Write test first, confirm it fails |
| No per-step review | Check each step before committing |
| Not updating sidecar | Update status and re-render HTML |
| Giant end-of-feature commit | Commit after each step |
| Skipping verification | Check every AC before claiming done |
