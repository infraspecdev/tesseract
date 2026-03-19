---
name: plan-review
description: Run multi-agent plan review with scored analysis
args: "[path to plan file]"
---

# Plan Review

Run a multi-persona plan review on a plan document.

## Usage

`/plan-review [path]`

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name (e.g., `auth-feature-20260319`). If none exists yet, derive from the plan name or current branch name and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/plan-review/` and add 1.
- **Slug** (`{slug}`): Use the plan name (e.g., `auth-feature`).

Write the analysis using the Write tool to:

```
{project_root}/{output_dir}/{feature}/plan-review/{N}-{slug}/summary.md
```

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. If a path is provided, use that plan file
2. If no path, scan for plans in `{output_dir}/*/plan.json` (each feature folder may contain a `plan.json`):
   - If exactly one plan exists, use it
   - If multiple plans exist, present a list and ask which to review
   - Accept plan name as shorthand: `/plan-review auth-feature`
   Also check for docs in `{output_dir}/{feature}/`
3. Follow the plan-review workflow:
   - Read the plan and extract keywords
   - Select reviewers (auto-detect + config overrides)
   - Dispatch selected agents in parallel
   - Parse grades, calculate scores
   - Classify recommendations (P0/P1/P2)
   - **Write analysis, detailed findings, and enhanced plan to the paths above**
   - Per-agent detailed findings written to `{output_dir}/{feature}/plan-review/{N}-{slug}/detailed/<agent>.md`
   - Enhanced plan written to `{output_dir}/{feature}/plan-review/{N}-{slug}/enhanced-plan.md`
4. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
5. Present results with options: apply as-is, apply with edits, skip
6. Offer next steps: `/pm-sync`, `/implement`
