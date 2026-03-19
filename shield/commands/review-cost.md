---
name: review-cost
description: Run cost optimization review with the cost reviewer agent
---

# Cost Review

Run a targeted cost review using the Shield cost reviewer agent.

## Behavior

1. Detect the review context:
   - If Terraform files → dispatch `shield:cost-reviewer` in **infra-code** mode
   - If plan document → dispatch in **plan** mode
2. Also invoke `shield:terraform:cost-review` skill if terraform domain is active
3. Present findings with estimated cost impact
4. Show environment-specific recommendations (dev/staging/prod)

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name. If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available, otherwise the current git branch name.

Write findings to the config-driven feature directory:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/
├── summary.md          (cost-focused)
├── changes.md
└── detailed/cost.md
```

5. Write detailed findings, summary, and applied changes to the paths above
6. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
7. Ask user which fixes to apply
