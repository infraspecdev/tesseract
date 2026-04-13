---
name: review-k8s
description: Run Kubernetes manifest review for security, cost, and operational readiness
args: "[path]"
---

# Kubernetes Review

Run a comprehensive review of Kubernetes manifests covering security, cost optimization, and operational readiness.

## Usage

`/review-k8s [path]`

## Behavior

1. Detect K8s manifest files at the given path (or current working directory):
   - Look for YAML files containing `apiVersion:` and `kind:` with K8s resource types
   - If no K8s manifests found, inform the user and exit
   - If `kustomization.yaml` found, also invoke `shield:kubernetes:kustomize-review`
2. Invoke the following skills in parallel:
   - `shield:kubernetes:security-audit`
   - `shield:kubernetes:cost-review`
   - `shield:kubernetes:operational-review`
3. Dispatch `shield:kubernetes-reviewer` agent in all three modes (security, cost, operational) in parallel
4. If deprecated APIs found by any skill, recommend running `/review-k8s-deprecation`
5. Aggregate findings, deduplicate, sort by severity
6. Present unified findings to the user

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name. If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available, otherwise the current git branch name.

Write findings to the config-driven feature directory:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/
├── summary.md          (unified K8s review)
├── changes.md
└── detailed/
    ├── k8s-security.md
    ├── k8s-cost.md
    └── k8s-operations.md
```

After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`.

## Single-Agent Shortcuts

- `/review-k8s-security` — security audit only (invoke `shield:kubernetes:security-audit` + `shield:kubernetes-reviewer` in security mode)
- `/review-k8s-cost` — cost review only (invoke `shield:kubernetes:cost-review` + `shield:kubernetes-reviewer` in cost mode)
- `/review-k8s-ops` — operational review only (invoke `shield:kubernetes:operational-review` + `shield:kubernetes-reviewer` in operational mode)
- `/review-k8s-deprecation` — deprecation check only (invoke `shield:kubernetes:deprecation-check-and-upgrade`)
