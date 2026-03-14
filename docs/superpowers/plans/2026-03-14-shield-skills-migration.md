# Shield Skills Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move all existing skills from 3 plugins into the Shield domain-based directory structure, add the review orchestrator and summarize skills, and create the pm-sync skill.

**Architecture:** Skills are organized by domain (`general/`, `terraform/`, `atmos/`, `github-actions/`) with each domain containing phase-specific skills. The `general/` directory holds domain-agnostic orchestrators. Each skill is copied from its source with path updates and minor description changes.

**Tech Stack:** Markdown skill definitions with supporting files

---

## Chunk 1: General Skills (from dev-workflow)

### Task 1: Move research skill

**Files:**
- Copy: `dev-workflow/skills/research/SKILL.md` → `shield/skills/general/research/SKILL.md`

- [ ] **Step 1: Copy the skill**

Read the full content of `/Users/ashwinimanoj/projects/tesseract/dev-workflow/skills/research/SKILL.md` and create it at `shield/skills/general/research/SKILL.md`. Update the frontmatter `name` to `general:research` (so it's clear it's in the general domain). Keep all content intact.

- [ ] **Step 2: Remove .gitkeep from skills/general/**

- [ ] **Step 3: Commit**

```
feat: add general research skill
```

### Task 2: Move plan-docs skill

**Files:**
- Copy: `dev-workflow/skills/plan-docs/SKILL.md` → `shield/skills/general/plan-docs/SKILL.md`
- Copy: `dev-workflow/skills/plan-docs/templates.md` → `shield/skills/general/plan-docs/templates.md`

- [ ] **Step 1: Copy SKILL.md and supporting files**

Read and copy both files. Update the `name` in frontmatter. Keep all content intact — this skill generates the HTML plan docs and will need updates in a future plan to also generate the JSON sidecar, but for now copy as-is.

- [ ] **Step 2: Commit**

```
feat: add general plan-docs skill
```

### Task 3: Move plan-review skill

**Files:**
- Copy: `dev-workflow/skills/plan-review/SKILL.md` → `shield/skills/general/plan-review/SKILL.md`
- Copy: `dev-workflow/skills/plan-review/scoring.md` → `shield/skills/general/plan-review/scoring.md`
- Copy: `dev-workflow/skills/plan-review/templates.md` → `shield/skills/general/plan-review/templates.md`

- [ ] **Step 1: Copy SKILL.md and supporting files**

Read and copy all files. Update the `name` in frontmatter. The skill references agent names — update any references from `dev-workflow:cloud-architect-reviewer` to `shield:architecture-reviewer`, `dev-workflow:security-engineer-reviewer` to `shield:security-reviewer`, etc. Update the persona catalog to match the new 7-agent names.

- [ ] **Step 2: Commit**

```
feat: add general plan-review skill
```

### Task 4: Move implement-feature skill

**Files:**
- Copy: `dev-workflow/skills/implement-feature/SKILL.md` → `shield/skills/general/implement-feature/SKILL.md`

- [ ] **Step 1: Copy the skill**

Read and copy. Update the `name` in frontmatter. Keep content intact.

- [ ] **Step 2: Commit**

```
feat: add general implement-feature skill
```

### Task 5: Create review orchestrator skill

**Files:**
- Create: `shield/skills/general/review/SKILL.md`

- [ ] **Step 1: Create the review orchestrator**

This is a NEW skill — the main `/review` orchestrator that coordinates all review activity.

```markdown
---
name: review
description: |
  Comprehensive code review orchestrator. Detects domains from .tesseract.json and
  changed files, dispatches domain-specific review skills and reviewer agents,
  verifies acceptance criteria, merges findings, and presents to user.
  Use when running code review during or after implementation.
autoInvoke: false
---

# Review Orchestrator

## When to Use

- After implementing a feature or story step
- When explicitly invoked via `/review`
- As the final review at the end of an implementation pipeline
- When triggered by the pre-commit hook (lightweight mode)

## When NOT to Use

- For plan review — use `plan-review` skill instead
- For a single specific reviewer — use `/review-security`, `/review-cost`, etc.

## Review Process

### 1. Determine Context and Scope

Identify the review context to determine depth:

| Context | Scope | Depth |
|---------|-------|-------|
| Per-step (during implementation) | Changed files for current story only | Code correctness + domain skill. No full agent suite. |
| Explicit `/review` | All files in scope | Full: code correctness + domain skills + all selected agents + AC verification |
| Final review | All files in scope | Full: everything + AC for all stories |
| Pre-commit hook | Staged files only | Checks at/above configured threshold severity only |

### 2. Code Correctness Review

For all contexts, review the changed/staged files for:
- Logic bugs and error handling gaps
- Style consistency with surrounding code
- Test coverage — are new code paths tested?
- Edge cases and boundary conditions

### 3. Domain-Specific Review

Read `.tesseract.json` to get active domains. For each active domain, check if a domain-specific review skill exists:

- `terraform` → invoke `shield:terraform:review`
- `atmos` → invoke `shield:atmos:review`
- `github-actions` → invoke `shield:github-actions:review`

Domain skills run in parallel. Their findings are collected and merged.

### 4. External Plugin Skills

Check `.tesseract.json` for `external_skills` configured for the active domain's `review` phase. Invoke each configured external skill and merge findings.

### 5. Agent Reviews (explicit/final only)

Select reviewer agents based on:
- **Auto-select:** detect file types and content keywords → pick relevant reviewers
- **`always_include`:** from `~/.tesseract/config.json` — always dispatched
- **`never_include`:** from config — always skipped
- **Minimum 3 agents** for full review

Dispatch selected agents in parallel using the appropriate mode:
- For Terraform/HCL files → `infra-code` mode
- For plan documents → `plan` mode
- For application code → `app-code` mode (when available)

### 6. Acceptance Criteria Verification (explicit/final only)

If an active story context exists (from the plan sidecar):
1. Read acceptance criteria from the sidecar JSON
2. Check each criterion against the implementation
3. Look for evidence in code, tests, and config
4. Produce an AC report table: criterion | status (met/not met/not verified) | evidence

### 7. Merge and Present Findings

1. Collect all findings from code review, domain skills, agents, and AC verification
2. Deduplicate — if multiple sources flag the same issue, keep the most detailed finding
3. Sort by severity (critical → important → warning)
4. Present summary table to user
5. Ask user which fixes to apply: all / select specific / skip
6. For findings flagged `NEEDS_DISCUSSION`, present options before applying
7. Optionally post findings to PM card (ask user)

### 8. Apply Fixes and Update Summary

1. Apply selected fixes
2. Write review summary to run directory
3. If any fixes were applied, re-render the plan HTML from sidecar

## Output Format

### Review Summary

| # | Severity | Source | Location | Finding | Recommendation |
|---|----------|--------|----------|---------|---------------|
| 1 | Critical | security-reviewer | main.tf:42 | Wildcard IAM policy | Scope to specific ARNs |
| 2 | Important | terraform/review | variables.tf:15 | Missing validation block | Add CIDR validation |
| ... | ... | ... | ... | ... | ... |

### Acceptance Criteria Report (if applicable)

| Criteria | Status | Evidence |
|----------|--------|----------|
| Regional pools allocate /20 CIDRs | Met | main.tf:42 — netmask_length = 20 |
| No CIDR overlap | Not verified | No test found |

### Actions

Which fixes would you like to apply?
- [a] Apply all
- [s] Select specific fixes
- [n] Skip — review only
- [p] Post findings to PM card
```

- [ ] **Step 2: Commit**

```
feat: add review orchestrator skill

Comprehensive review skill that coordinates code correctness checks,
domain-specific review skills, agent dispatch, acceptance criteria
verification, and finding presentation with user-driven fix selection.
```

### Task 6: Create summarize skill

**Files:**
- Create: `shield/skills/general/summarize/SKILL.md`

- [ ] **Step 1: Create the summarize skill**

```markdown
---
name: summarize
description: |
  Phase summary generator. Called by orchestrators at the end of each pipeline phase.
  Produces concise bullet-point summaries written to the run directory.
autoInvoke: false
---

# Phase Summarize

## When to Use

Called automatically by each phase's orchestrator at the end of execution. Not invoked directly by users.

## Input

The orchestrator passes:
- `phase_name`: The pipeline phase that just completed (research, plan, plan-review, sync, implement-step-N, review-step-N, final-review)
- `phase_output`: Structured data about what was done
- `project_name`: From `.tesseract.json`
- `run_id`: The current run identifier (date-topic)

## Process

1. Format the phase output as concise bullet points (5-10 bullets max)
2. Include: what was done, key decisions made, findings if any, next phase
3. Write to `~/.tesseract/projects/<project>/runs/<run_id>/<phase_name>-summary.md`
4. Return the summary text to the orchestrator for display

## Summary Format

```markdown
# <Phase Name> Summary

**Run:** <run_id>
**Date:** <timestamp>

## What was done
- Bullet 1
- Bullet 2
- ...

## Key decisions
- Decision 1 (if any)

## Findings
- Finding 1 (if any review findings)

## Next
- What the next phase will do
```

## Rules

- Keep summaries concise — 5-10 bullets per section max
- Include only information relevant to the next phase or audit trail
- Do not repeat full review findings — reference the review summary file
- Always include the "Next" section so the user knows what's coming
```

- [ ] **Step 2: Commit**

```
feat: add phase summarize skill
```

## Chunk 2: Terraform Skills (from infra-review)

### Task 7: Move terraform review skills

**Files:**
- Copy: `infra-review/skills/terraform-cost-review/` → `shield/skills/terraform/cost-review/`
- Copy: `infra-review/skills/terraform-security-audit/` → `shield/skills/terraform/security-audit/`
- Copy: `infra-review/skills/terraform-plan-analyzer/` → `shield/skills/terraform/plan-analysis/`
- Copy: `infra-review/skills/terraform-test-coverage/` → `shield/skills/terraform/test-coverage/`

- [ ] **Step 1: Copy all 4 terraform skills with supporting files**

For each skill:
1. Read the SKILL.md and all supporting files from the source
2. Create in the new location under `shield/skills/terraform/`
3. Update `name` in frontmatter to use `terraform:<phase>` format
4. Keep all content intact

Supporting files per skill:
- `terraform-cost-review`: `pricing-reference.md`, `report-template.md`
- `terraform-security-audit`: `audit-dimensions.md`, `templates.md`
- `terraform-plan-analyzer`: `reference-tables.md`, `templates.md`
- `terraform-test-coverage`: `templates.md`, `test-patterns.md`

- [ ] **Step 2: Remove .gitkeep from skills/terraform/**

- [ ] **Step 3: Commit (one per skill)**

```
feat: add terraform cost-review skill
feat: add terraform security-audit skill
feat: add terraform plan-analysis skill
feat: add terraform test-coverage skill
```

## Chunk 3: Atmos and GitHub Actions Skills

### Task 8: Move atmos skills

**Files:**
- Copy: `infra-review/skills/atmos-component-hygiene/` → `shield/skills/atmos/hygiene/`
- Copy: `infra-review/skills/atmos-repo-review/` → `shield/skills/atmos/repo-review/`

- [ ] **Step 1: Copy both atmos skills with supporting files**

Supporting files:
- `atmos-component-hygiene`: `check-tables.md`
- `atmos-repo-review`: `red-flags-reference.md`, `scoring-rubric.md`, `templates.md`

Update `name` in frontmatter. Keep all content intact.

- [ ] **Step 2: Remove .gitkeep from skills/atmos/**

- [ ] **Step 3: Commit (one per skill)**

```
feat: add atmos hygiene review skill
feat: add atmos repo-review skill
```

### Task 9: Move github-actions skill

**Files:**
- Copy: `infra-review/skills/github-actions-reviewer/` → `shield/skills/github-actions/review/`

- [ ] **Step 1: Copy the skill with supporting files**

Supporting files: `checklist.md`, `templates.md`

Update `name` in frontmatter. Keep all content intact.

- [ ] **Step 2: Remove .gitkeep from skills/github-actions/**

- [ ] **Step 3: Commit**

```
feat: add github-actions review skill
```

## Chunk 4: PM Sync Skill

### Task 10: Create pm-sync skill

**Files:**
- Create: `shield/skills/pm-sync/SKILL.md`
- Source: `clickup-sprint-planner/skills/sprint-planning/SKILL.md` (adapt for abstract PM interface)

- [ ] **Step 1: Read the source skill**

Read `/Users/ashwinimanoj/projects/tesseract/clickup-sprint-planner/skills/sprint-planning/SKILL.md` and its supporting file `card-format.md`.

- [ ] **Step 2: Create the pm-sync skill**

Adapt the sprint-planning skill to use abstract PM operations instead of ClickUp-specific tools. The skill should:
- Reference `pm_sync`, `pm_bulk_create`, `pm_bulk_update`, `pm_get_status` etc. instead of `sprint_sync`, `sprint_bulk_create` etc.
- Read the plan sidecar JSON instead of parsing HTML
- Keep the same workflow rules (sync before mutating, confirm before changes, present results as tables)
- Note that the actual PM adapter is configured in `~/.tesseract/projects/<project>/pm.json`
- Keep the card format reference (copy card-format.md as supporting file)

- [ ] **Step 3: Commit**

```
feat: add pm-sync skill

Adapted from clickup-sprint-planner sprint-planning skill.
Uses abstract pm_* operations instead of ClickUp-specific tools.
Reads plan sidecar JSON for story data.
```
