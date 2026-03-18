---
name: review
description: Run comprehensive code review with domain-specific agents and AC verification
args: "[path or scope]"
---

# Review

Run a comprehensive code review that covers code correctness, domain-specific checks, agent reviews, and acceptance criteria verification.

## Usage

`/review [path or scope]`

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Then write the review summary using the Write tool to:

```
{project_root}/shield/docs/reviews-YYYYMMDD-HHMMSS/summary/code-review-summary.md
```

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`, and `YYYYMMDD-HHMMSS` with the current date and time.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. Follow the review workflow:
   - Code correctness review on changed files
   - Domain-specific review skills (terraform, atmos, etc.)
   - Agent reviews (security, cost, architecture, operations)
   - Acceptance criteria verification (if story context from plans in `{project_root}/shield/docs/plans/`)
2. Findings are merged, deduplicated, sorted by severity
   - Per-agent detailed findings written to `reviews-YYYYMMDD-HHMMSS/detailed/<agent>.md`
   - Applied fixes logged to `reviews-YYYYMMDD-HHMMSS/summary/code-review-changes.md`
3. **Write review summary, detailed findings, and changes log to the paths above**
4. Present to user with options: apply all, select specific, skip, post to PM
5. Apply selected fixes

## Single-Agent Shortcuts

- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only
- `/review-well-architected` — AWS Well-Architected Framework review
