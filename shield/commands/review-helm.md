---
name: review-helm
description: Run Helm chart review for structure, best practices, and K8s security/operational issues in templates
args: "[path]"
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, agent=helm-structure | k8s-security | k8s-operations
  - review_summary_html
  - review_detailed_html
---

# Helm Chart Review

Run a comprehensive review of a Helm chart covering chart structure, template best practices, and K8s security/operational issues in rendered templates.

## Usage

`/review-helm [path]`

## Paths

Writes registry-tracked paths under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}` (review_type=code, agents=helm-structure / k8s-security / k8s-operations — one `{review_detailed}` per skill). See `shield/schema/output-paths.yaml` and the counter-resolution rule in `/review`. `changes.md` is a side-artifact.

## Behavior

1. Detect Helm chart at the given path (or current working directory):
   - Look for `Chart.yaml` file
   - If not found, inform the user and exit
2. Invoke the following skills:
   - `shield:kubernetes:helm-review` — chart structure and best practices
   - `shield:kubernetes:security-audit` — security issues in templates
   - `shield:kubernetes:operational-review` — operational issues in templates
3. If deprecated K8s API versions found in templates, recommend `deprecation-check-and-upgrade`
4. Aggregate findings, deduplicate, sort by severity
5. Present unified findings to the user

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name; if none exists yet, derive from current branch or story context + `-YYYYMMDD`). Resolve `{date}{_counter}` per the counter rule in `/review`.

Write findings under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}/`:

```
{review_dir}/
├── summary.md              ← {review_summary}
├── changes.md              ← applied-fixes log (side-artifact)
└── detailed/
    ├── helm-structure.md   ← {review_detailed} (agent=helm-structure)
    ├── k8s-security.md     ← {review_detailed} (agent=k8s-security)
    └── k8s-operations.md   ← {review_detailed} (agent=k8s-operations)
```

Numbered run subfolders (`code-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

After writing, also render `{review_summary_html}` and one `{review_detailed_html}` per agent under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/`. Then update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`.
