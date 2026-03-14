---
name: review
description: Run comprehensive code review with domain-specific agents and AC verification
args: "[path or scope]"
---

# Review

Run a comprehensive code review that covers code correctness, domain-specific checks, agent reviews, and acceptance criteria verification.

## Usage

`/review [path or scope]`

## Arguments

- `path` (optional) — specific file or directory to review
- If omitted, reviews all changed files (git diff against main)

## Behavior

1. Invoke the `shield:general:review` skill
2. The skill determines context and runs the appropriate depth:
   - Code correctness review on changed files
   - Domain-specific review skills (terraform, atmos, etc.)
   - Agent reviews (security, cost, architecture, operations — selected by auto-detect + config)
   - Acceptance criteria verification (if story context exists)
3. Findings are merged, deduplicated, sorted by severity
4. Present to user with options:
   - Apply all fixes
   - Select specific fixes
   - Skip (review only)
   - Post findings to PM card
5. Apply selected fixes
6. Invoke `shield:general:summarize` to produce a review summary
7. If fixes were applied, offer to re-run review to verify

## Single-Agent Shortcuts

For targeted reviews, use:
- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only
- `/review-well-architected` — AWS Well-Architected Framework review
