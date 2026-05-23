---
name: review-well-architected
description: Run AWS Well-Architected Framework review across all 6 pillars
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, agent=cloud-architect
  - review_summary_html
  - review_detailed_html
---

# Well-Architected Review

Run a holistic infrastructure review using the AWS Well-Architected Framework.

## Paths

Writes registry-tracked paths under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}` (review_type=code, agent=cloud-architect). See `shield/schema/output-paths.yaml` and the counter-resolution rule in `/review`. `changes.md` is a side-artifact.

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name; if none exists yet, derive from current branch or story context + `-YYYYMMDD`). Resolve `{date}{_counter}` per the counter rule in `/review` (today's ISO date in `YYYY-MM-DD` format; empty `_counter` for first same-day run, `_2`/`_3`/... otherwise).

Write findings under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}/`:

```
{review_dir}/
├── summary.md              ← {review_summary}
├── changes.md              ← applied-fixes log (side-artifact)
└── detailed/
    └── cloud-architect.md  ← {review_detailed} (agent=cloud-architect)
```

Numbered run subfolders (`code-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

## Behavior

1. Dispatch `shield:cloud-architect` agent in **infra-code** mode
2. The agent evaluates across all 6 pillars:
   - Operational Excellence
   - Security
   - Reliability
   - Performance Efficiency
   - Cost Optimization
   - Sustainability
3. Cross-reference with specialized agents if available
4. Present pillar scores summary table
5. Show overall verdict and top 3 remediation items
6. Write `{review_summary}`, `{review_detailed}` (agent=cloud-architect), and the side-artifact changes log to the paths above
7. Render `{review_summary_html}` and `{review_detailed_html}` under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/`
8. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
9. Ask user which fixes to apply
