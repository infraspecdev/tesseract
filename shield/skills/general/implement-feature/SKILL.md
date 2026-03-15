---
name: implement-feature
description: |
  Shield's implementation skill — TDD-based feature implementation with acceptance
  criteria confirmation, per-step lightweight review, and sidecar status updates.
  Reads stories and AC from the plan sidecar JSON when available.
  Triggers on: implement, build, create feature, /implement command.
---

# Implement Feature

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

If a `plan-sidecar.json` exists in the Shield run directory (`docs/tesseract/latest/plan-sidecar.json`) or project root:
1. Read the sidecar
2. Find the story by ID (if story ID provided)
3. Extract: name, description, tasks, acceptance criteria
4. Show the story details to the user

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
- If the active domain has a review skill (e.g., `terraform/review`), run domain-specific checks on the changed files
- This is NOT a full agent review — just quick correctness checks

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
