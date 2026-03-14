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
