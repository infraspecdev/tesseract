---
name: review-k8s
description: Run Kubernetes manifest review for security, cost, and operational readiness
args: "[path]"
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, agent=k8s-security | k8s-cost | k8s-operations
  - review_summary_html
  - review_detailed_html
---

# Kubernetes Review

Run a comprehensive review of Kubernetes manifests covering security, cost optimization, and operational readiness.

## Usage

`/review-k8s [path]`

## Paths

Writes registry-tracked paths under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}` (review_type=code, agents=k8s-security / k8s-cost / k8s-operations — one `{review_detailed}` per skill). See `shield/schema/output-paths.yaml` and the counter-resolution rule in `/review`. `changes.md` is a side-artifact.

## Behavior

1. Detect K8s manifest files at the given path (or current working directory):
   - Look for YAML files containing `apiVersion:` and `kind:` with K8s resource types
   - If no K8s manifests found, inform the user and exit
   - If `kustomization.yaml` found, also invoke `shield:kubernetes:kustomize-review`
2. Invoke the following skills in parallel:
   - `shield:kubernetes:security-audit`
   - `shield:kubernetes:cost-review`
   - `shield:kubernetes:operational-review`
3. Dispatch `shield:platform-engineer` agent in all three modes (security, cost, operational) in parallel
4. If deprecated APIs found by any skill, recommend running `/review-k8s-deprecation`
5. Aggregate findings, deduplicate, sort by severity
6. Present unified findings to the user

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name; if none exists yet, derive from current branch or story context + `-YYYYMMDD`). Resolve `{date}{_counter}` per the counter rule in `/review`.

Write findings under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}/`:

```
{review_dir}/
├── summary.md              ← {review_summary}
├── changes.md              ← applied-fixes log (side-artifact)
└── detailed/
    ├── k8s-security.md     ← {review_detailed} (agent=k8s-security)
    ├── k8s-cost.md         ← {review_detailed} (agent=k8s-cost)
    └── k8s-operations.md   ← {review_detailed} (agent=k8s-operations)
```

Numbered run subfolders (`code-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

After writing, also render `{review_summary_html}` and one `{review_detailed_html}` per agent under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/`. Then update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`.

## Single-Agent Shortcuts

- `/review-k8s-security` — security audit only (invoke `shield:kubernetes:security-audit` + `shield:platform-engineer` in security mode)
- `/review-k8s-cost` — cost review only (invoke `shield:kubernetes:cost-review` + `shield:platform-engineer` in cost mode)
- `/review-k8s-ops` — operational review only (invoke `shield:kubernetes:operational-review` + `shield:platform-engineer` in operational mode)
- `/review-k8s-deprecation` — deprecation check only (invoke `shield:kubernetes:deprecation-check-and-upgrade`)
