---
name: review
description: Use when code changes need review for security, cost, architecture, or acceptance criteria verification. Triggers on /review, after implementation, pre-merge.
---

# Review Orchestrator

## Output Path — MANDATORY

All review output goes into a timestamped directory:

```
shield/docs/reviews-YYYYMMDD-HHMMSS/
├── summary/
│   ├── code-review-summary.md      ← consolidated findings (main output)
│   └── code-review-changes.md      ← fixes applied (written after step 9)
└── detailed/
    └── <agent-name>.md              ← one file per dispatched agent
```

Replace `YYYYMMDD-HHMMSS` with the current date and time. **Do NOT** use any other path or directory structure. The Write tool creates directories automatically.

## When to Use

- After implementing a feature or story step
- When explicitly invoked via `/review`
- As the final review at the end of an implementation pipeline

## When NOT to Use

- For plan review — use `plan-review` skill instead
- For a single specific reviewer — use `/review-security`, `/review-cost`, etc.

## Review Process

### 1. Load Prior Context

Before reviewing, check for artifacts from prior phases (all optional — proceed without if missing):
- **Plan sidecars** — `shield/docs/plans/*.json` for stories and acceptance criteria (reads all active plans)
- **Research** — most recent `shield/docs/research-*.md` for domain context
- **Git changes** — `git log --oneline` and `git diff` to see what changed during implementation

### 2. Determine Context and Scope

Identify the review context to determine depth:

| Context | Scope | Depth |
|---------|-------|-------|
| Per-step (during implementation) | Changed files for current story only | Code correctness + domain skill. No full agent suite. |
| Explicit `/review` | All files in scope | Full: code correctness + domain skills + all selected agents + AC verification |
| Final review | All files in scope | Full: everything + AC for all stories |

### 3. Code Correctness Review

For all contexts, review the changed/staged files for:
- Logic bugs and error handling gaps
- Style consistency with surrounding code
- Test coverage — are new code paths tested?
- Edge cases and boundary conditions

### 4. Domain-Specific Review

Read `.shield.json` to get active domains. For each active domain, check if a domain-specific review skill exists:

- `terraform` → invoke `shield:terraform:review`
- `atmos` → invoke `shield:atmos:review`
- `github-actions` → invoke `shield:github-actions:review`

Domain skills run in parallel. Their findings are collected and merged.

### 5. External Plugin Skills

Check `.shield.json` for `external_skills` configured for the active domain's `review` phase. Invoke each configured external skill and merge findings.

### 6. Agent Reviews (explicit/final only)

Select reviewer agents based on:
- **Auto-select:** detect file types and content keywords → pick relevant reviewers
- **`always_include`:** from `.shield.json` `reviewers` section — always dispatched
- **`never_include`:** from `.shield.json` `reviewers` section — always skipped
- **Minimum 3 agents** for full review

Dispatch selected agents in parallel using the appropriate mode:
- For Terraform/HCL files → `infra-code` mode
- For plan documents → `plan` mode
- For application code → `app-code` mode (when available)

### 7. Save Detailed Findings

For each agent that returned results, write its full raw output to:

```
reviews-YYYYMMDD-HHMMSS/detailed/<agent-name>.md
```

Where `<agent-name>` matches the agent (e.g., `security.md`, `cost.md`, `architecture.md`, `operations.md`, `well-architected.md`).

Each detailed file should include a header and back-link:

```markdown
# <Agent Name> — Detailed Findings

> Back to [code-review-summary](../summary/code-review-summary.md)

<full agent output>
```

If an agent fails or times out, omit its detailed file — do not write a placeholder.

### 8. Acceptance Criteria Verification (explicit/final only)

If an active story context exists (from plan sidecars in `shield/docs/plans/`):
1. Read acceptance criteria from the named plan JSON files
2. Check each criterion against the implementation
3. Look for evidence in code, tests, and config
4. Produce an AC report table: criterion | status (met/not met/not verified) | evidence

### 9. Merge and Present Findings

1. Collect all findings from code review, domain skills, agents, and AC verification
2. Deduplicate — if multiple sources flag the same issue, keep the most detailed finding
3. Sort by severity (critical → important → warning)
4. Present summary table to user
5. Ask user which fixes to apply: all / select specific / skip
6. For findings flagged `NEEDS_DISCUSSION`, present options before applying
7. Optionally post findings to PM card (ask user)
8. In the summary file, add a "Detailed Agent Findings" section linking to each agent's file:
   ```markdown
   ## Detailed Agent Findings
   - [Security](../detailed/security.md)
   - [Cost](../detailed/cost.md)
   - [Architecture](../detailed/architecture.md)
   ...
   ```

### 10. Apply Fixes and Update Summary

1. Apply selected fixes
2. Write review summary to `shield/docs/reviews-YYYYMMDD-HHMMSS/summary/code-review-summary.md` (exact path from Output Path section above)
3. Write `summary/code-review-changes.md` documenting applied fixes:
   ```markdown
   # Code Review Changes

   > Review: [code-review-summary.md](code-review-summary.md)

   | # | Finding | File | Change Description |
   |---|---------|------|--------------------|
   | 1 | <finding from summary> | <file:line> | <what was changed> |
   ```
4. If any fixes were applied, re-render the plan HTML from sidecar

## Output Format

## Output Structure

```
reviews-YYYYMMDD-HHMMSS/
├── summary/code-review-summary.md    ← table below
├── summary/code-review-changes.md    ← applied fixes log
└── detailed/<agent>.md               ← full per-agent output
```

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

### Detailed Agent Findings

- [Security](../detailed/security.md)
- [Cost](../detailed/cost.md)
- [Architecture](../detailed/architecture.md)
- [Operations](../detailed/operations.md)
- [Well-Architected](../detailed/well-architected.md)
