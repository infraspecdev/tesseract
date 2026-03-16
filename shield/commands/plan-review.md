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

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Then write the analysis using the Write tool to:

```
{project_root}/shield/docs/analysis-YYYYMMDD-HHMMSS.md
```

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`, and `YYYYMMDD-HHMMSS` with the current date and time.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. If a path is provided, use that plan file
2. If no path, list plans in `{project_root}/shield/docs/plans/*.json`:
   - If exactly one plan exists, use it
   - If multiple plans exist, present a list and ask which to review
   - Accept plan name as shorthand: `/plan-review auth-feature`
   Also check for docs in `{project_root}/shield/docs/`
3. Follow the plan-review workflow:
   - Read the plan and extract keywords
   - Select reviewers (auto-detect + config overrides)
   - Dispatch selected agents in parallel
   - Parse grades, calculate scores
   - Classify recommendations (P0/P1/P2)
   - **Write analysis to the path above**
4. Present results with options: apply as-is, apply with edits, skip
5. Offer next steps: `/pm-sync`, `/implement`
