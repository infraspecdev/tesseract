---
name: review-security
description: Run security-focused review with the security reviewer agent
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, agent=security-engineer
  - review_summary_html
  - review_detailed_html
---

# Security Review

Run a targeted security review using the Shield security reviewer agent.

## Paths

Writes registry-tracked paths under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}` (review_type=code, agent=security-engineer). See `shield/schema/output-paths.yaml` and the counter-resolution rule in `/review`. `changes.md` is a side-artifact.

## Behavior

1. Detect the review context:
   - If Terraform files are present → dispatch `shield:security-engineer` in **infra-code** mode
   - If reviewing a plan document → dispatch in **plan** mode
2. Also invoke `shield:terraform:security-audit` skill if terraform domain is active
3. Present findings sorted by severity
4. Ask user which fixes to apply

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name; if none exists yet, derive from current branch or story context + `-YYYYMMDD`). Resolve `{date}{_counter}` per the counter rule in `/review` (today's ISO date in `YYYY-MM-DD` format; empty `_counter` for first same-day run, `_2`/`_3`/... otherwise).

Write findings under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}/`:

```
{review_dir}/
├── summary.md                ← {review_summary}
├── changes.md                ← applied-fixes log (side-artifact)
└── detailed/
    └── security-engineer.md  ← {review_detailed} (agent=security-engineer)
```

Numbered run subfolders (`code-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

5. Write `{review_summary}`, `{review_detailed}` (agent=security-engineer), and the side-artifact changes log to the paths above
6. Render `{review_summary_html}` and `{review_detailed_html}` under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/`
7. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
