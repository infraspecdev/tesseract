---
name: review-helm
description: Run Helm chart review for structure, best practices, and K8s security/operational issues in templates
args: "[path]"
---

# Helm Chart Review

Run a comprehensive review of a Helm chart covering chart structure, template best practices, and K8s security/operational issues in rendered templates.

## Usage

`/review-helm [path]`

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

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name. If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available, otherwise the current git branch name.

Write findings to the config-driven feature directory:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/
├── summary.md          (unified Helm review)
├── changes.md
└── detailed/
    ├── helm-structure.md
    ├── k8s-security.md
    └── k8s-operations.md
```

After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`.
