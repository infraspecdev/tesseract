---
name: review-cost
description: Run cost optimization review with the cost reviewer agent
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, agent=finops-analyst
  - review_summary_html
  - review_detailed_html
---

# Cost Review

Run a targeted cost review using the Shield cost reviewer agent.

## Paths

Writes registry-tracked paths under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}` (review_type=code, agent=finops-analyst). See `shield/schema/output-paths.yaml`. Resolve `{date}{_counter}` per the counter rule in `/review`. `changes.md` is a side-artifact (applied-fixes log, not in registry).

## Behavior

1. Detect the review context:
   - If Terraform files → dispatch `shield:finops-analyst` in **infra-code** mode
   - If plan document → dispatch in **plan** mode
2. Also invoke `shield:terraform:cost-review` skill if terraform domain is active
3. Present findings with estimated cost impact
4. Show environment-specific recommendations (dev/staging/prod)

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name; if none exists yet, derive from current branch or story context + `-YYYYMMDD`). Resolve `{date}{_counter}` per the counter rule in `/review` (today's ISO date; empty `_counter` for first same-day run, `_2`/`_3`/... otherwise).

Write findings under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}/`:

```
{review_dir}/
├── summary.md              ← {review_summary}
├── changes.md              ← applied-fixes log (side-artifact)
└── detailed/
    └── finops-analyst.md   ← {review_detailed} (agent=finops-analyst)
```

Numbered run subfolders (`code-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

5. Write `{review_summary}`, `{review_detailed}` (agent=finops-analyst), and the side-artifact changes log to the paths above
6. Render `{review_summary_html}` and `{review_detailed_html}` under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/`
7. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
8. Ask user which fixes to apply
