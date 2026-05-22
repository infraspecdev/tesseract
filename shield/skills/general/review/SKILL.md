---
name: review
description: Use when code changes need review for security, cost, architecture, or acceptance criteria verification. Triggers on /review, after implementation, pre-merge.
---

# Review Orchestrator

## Output Path — MANDATORY

All review output goes into a per-run, date-keyed folder under the feature's `reviews/code/` directory:

```
{output_dir}/{feature}/reviews/code/{date}{_counter}/   ← {review_dir}
├── summary.md                       ← {review_summary}  (consolidated findings, main output)
├── changes.md                       ← applied-fixes log (side-artifact, written after step 9)
└── detailed/
    └── <agent>.md                   ← {review_detailed} (one per dispatched agent)

{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/  ← {review_outputs_dir}
├── summary.html                     ← {review_summary_html}
└── detailed/
    └── <agent>.html                 ← {review_detailed_html} (one per agent)
```

Where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`), `{feature}` is the feature folder name (`{feature-name}-YYYYMMDD`), `{date}` is today's ISO date (`YYYY-MM-DD`), and `{_counter}` is empty for the first run of the day or `_2`, `_3`, ... on same-day collisions. Numbered-run subfolders (`code-review/{N}-{slug}/`) are gone. Reviews never overwrite prior runs.

**Resolving the counter:** before writing, list `{output_dir}/{feature}/reviews/code/` for entries matching today's date. If `{date}/` does not exist, use `_counter=""`. Otherwise, find the highest `{date}_<N>/` and use `_counter="_<N+1>"`. **Do NOT** use any other path or directory structure. The Write tool creates directories automatically.

## When to Use

- After implementing a feature or story step
- When explicitly invoked via `/review`
- As the final review at the end of an implementation pipeline

## When NOT to Use

- For plan review — use `plan-review` skill instead
- For a single specific reviewer — use `/review-security`, `/review-cost`, etc.

## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Load prior context (plan, research) | skip if none exists | No |
| 2 | Code correctness review | always | Yes |
| 3 | Domain-specific review | skip if no active domains | No |
| 4 | Dispatch agent reviewers | explicit/final review only | No |
| 5 | AC verification | skip if no plan.json | No |
| 6 | Merge + present findings | always | Yes |
| 7 | Apply selected fixes | always | Yes |
| 8 | Write summary + update manifest | always | Yes |

## Review Process

### 1. Load Prior Context

Before reviewing, check for artifacts from prior phases (all optional — proceed without if missing):
- **Plan sidecar** — `{plan_json}` = `{output_dir}/{feature}/plan.json` for stories and acceptance criteria
- **Research** — `{research}` = `{output_dir}/{feature}/research.md` for domain context
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
- `kubernetes` → invoke `shield:kubernetes:review` (security-audit + cost-review + operational-review). Also dispatch `shield:platform-engineer` agent. Only if K8s manifests detected (YAML files with K8s `apiVersion`/`kind` fields, `Chart.yaml`, or `kustomization.yaml`).

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
{review_dir}/detailed/<agent>.md         (i.e. {review_detailed} with agent=<dispatched-subagent-slug>)
```

Where `<agent>` matches the dispatched subagent's slug (e.g., `security-engineer.md`, `finops-analyst.md`, `architect.md`, `platform-engineer.md`, `cloud-architect.md`).

Each detailed file should include a header and back-link:

```markdown
# <Agent Name> — Detailed Findings

> Back to [summary](../summary.md)

<full agent output>
```

If an agent fails or times out, omit its detailed file — do not write a placeholder.

### 8. Acceptance Criteria Verification (explicit/final only)

If an active story context exists (from the plan sidecar `{plan_json}` = `{output_dir}/{feature}/plan.json`):
1. Read acceptance criteria from the plan JSON
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
   - [Security](detailed/security.md)
   - [Cost](detailed/cost.md)
   - [Architecture](detailed/architecture.md)
   ...
   ```

### 10. Apply Fixes and Update Summary

1. Apply selected fixes
2. Write review summary to `{review_summary}` = `{review_dir}/summary.md` (exact path from Output Path section above)
3. Render `{review_summary_html}` and each `{review_detailed_html}` under `{review_outputs_dir}` via `render-markdown.sh`
4. After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`
5. Write `changes.md` in `{review_dir}` documenting applied fixes (side-artifact, not in registry):
   ```markdown
   # Code Review Changes

   > Review: [summary.md](summary.md)

   | # | Finding | File | Change Description |
   |---|---------|------|--------------------|
   | 1 | <finding from summary> | <file:line> | <what was changed> |
   ```
6. If any fixes were applied, re-render `{plan_html}` from the updated `{plan_md}` (via `/plan` rendering flow)

## Output Format

## Output Structure

```
{review_dir}/
├── summary.md                        ← {review_summary} (table below)
├── changes.md                        ← applied-fixes log (side-artifact)
└── detailed/<agent>.md               ← {review_detailed} (full per-agent output)
```

### Review Summary

| # | Severity | Source | Location | Finding | Recommendation |
|---|----------|--------|----------|---------|---------------|
| 1 | Critical | security-engineer | main.tf:42 | Wildcard IAM policy | Scope to specific ARNs |
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

- [Security](detailed/security.md)
- [Cost](detailed/cost.md)
- [Architecture](detailed/architecture.md)
- [Operations](detailed/operations.md)
- [Well-Architected](detailed/well-architected.md)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Running full agent suite for a per-step review during implementation | Per-step reviews only need code correctness + domain skills — save the full agent suite for explicit `/review` |
| Dispatching all agents without checking `.shield.json` reviewers config | Respect `always_include` and `never_include` from the project config before auto-selecting |
| Applying fixes without user confirmation | Always present findings and ask which to apply — never auto-fix, especially for `NEEDS_DISCUSSION` items |
| Writing detailed agent findings to summary.md instead of separate files | Each agent gets its own file in `detailed/<agent>.md` — summary.md only has the merged table |
| Skipping AC verification because no plan sidecar exists | If there's no `plan.json`, skip AC verification silently — don't error or ask the user to create one |
| Not deduplicating findings from multiple sources | If security-engineer and terraform/security-audit flag the same issue, keep the most detailed one |
