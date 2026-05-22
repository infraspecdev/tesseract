---
name: plan-review
description: Run multi-agent plan review with scored analysis
args: "[path to plan file]"
outputs:
  - review_summary    # review_type=plan
  - review_enhanced   # review_type=plan
  - review_detailed   # review_type=plan, multiple agents
  - review_summary_html
  - review_enhanced_html
  - review_detailed_html
---

# Plan Review

Run a multi-persona plan review on a plan document.

## Usage

`/plan-review [path]`

## Paths

This command writes the following registry-tracked paths (see `shield/schema/output-paths.yaml`). All resolve under `{review_dir}` = `{output_dir}/{feature}/reviews/plan/{date}{_counter}`:

| Registry key | Resolved path |
|---|---|
| `review_summary` | `{review_dir}/summary.md` |
| `review_enhanced` | `{review_dir}/enhanced-plan.md` |
| `review_detailed` (per agent) | `{review_dir}/detailed/{agent}.md` |
| `review_summary_html` | `{output_dir}/{feature}/outputs/reviews/plan/{date}{_counter}/summary.html` |
| `review_enhanced_html` | `{output_dir}/{feature}/outputs/reviews/plan/{date}{_counter}/enhanced-plan.html` |
| `review_detailed_html` | `{output_dir}/{feature}/outputs/reviews/plan/{date}{_counter}/detailed/{agent}.html` |

Each reviewer subagent dispatched by this command writes its own `{review_detailed}` entry (with `agent` set to that subagent's slug); the subagents declare `review_detailed` in their own `outputs:`.

### Resolving the counter

Before writing, list `{output_dir}/{feature}/reviews/plan/` for entries matching today's ISO date. If `{date}/` does not exist, use `_counter=""`. Otherwise, find the highest `{date}_<N>/` (with `<N>` starting at 2 for the second same-day run) and use `_counter="_<N+1>"`. Reviews never overwrite prior runs.

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name, e.g. `auth-feature-20260319`). Resolve `{date}` and `{_counter}` per the section above.

Write artifacts using the Write tool under `{review_dir}` = `{output_dir}/{feature}/reviews/plan/{date}{_counter}/`:

```
{review_dir}/
├── summary.md              ← {review_summary}
├── enhanced-plan.md        ← {review_enhanced}
└── detailed/
    └── <agent>.md          ← {review_detailed} (one per dispatched reviewer)
```

Numbered run subfolders (`plan-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

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
   - **Write `{review_summary}`, per-agent `{review_detailed}`, and `{review_enhanced}` under `{review_dir}` per the paths above**
4. Render HTML — produce `{review_summary_html}`, `{review_enhanced_html}`, and one `{review_detailed_html}` per agent under `{output_dir}/{feature}/outputs/reviews/plan/{date}{_counter}/`
5. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
6. Present results with options: apply as-is, apply with edits, skip
7. Offer next steps: `/pm-sync`, `/implement`
