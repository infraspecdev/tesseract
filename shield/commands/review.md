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

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name (e.g., `auth-feature-20260319`). If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available from plan context, otherwise use the current git branch name.

Write the review summary using the Write tool to:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/summary.md
```

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. Follow the review workflow:
   - Code correctness review on changed files
   - Domain-specific review skills (terraform, atmos, etc.)
   - Agent reviews (security, cost, architecture, operations)
   - Acceptance criteria verification (if story context from `{output_dir}/{feature}/plan.json`)
2. Findings are merged, deduplicated, sorted by severity
   - Per-agent detailed findings written to `{output_dir}/{feature}/code-review/{N}-{slug}/detailed/<agent>.md`
   - Applied fixes logged to `{output_dir}/{feature}/code-review/{N}-{slug}/changes.md`
3. **Write review summary, detailed findings, and changes log to the paths above**
4. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
5. Present to user with options: apply all, select specific, skip, post to PM
6. Apply selected fixes

## Single-Agent Shortcuts

- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only
- `/review-well-architected` — AWS Well-Architected Framework review
