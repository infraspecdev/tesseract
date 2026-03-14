---
name: plan-review
description: Run multi-agent plan review with scored analysis
args: "[path to plan file]"
---

# Plan Review

Run the Shield multi-persona plan review on a plan document.

## Usage

`/plan-review [path]`

## Behavior

1. If a path is provided, use that plan file
2. If no path, auto-detect recent plan files in the working directory
3. Invoke the `shield:general:plan-review` skill
4. The skill:
   - Reads the plan and extracts keywords
   - Selects reviewers (auto-detect + config overrides from `~/.tesseract/config.json`)
   - Dispatches selected agents in parallel (plan review mode)
   - Parses grades, calculates scores
   - Classifies recommendations (P0/P1/P2)
   - Writes analysis and enhanced plan to `review/` directory
5. Present results with three options:
   - Apply recommendations as-is
   - Apply with edits
   - Skip
6. Invoke `shield:general:summarize` to produce a plan-review summary
7. Offer next steps: `/pm-sync`, `/implement`
