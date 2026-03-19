---
name: review-security
description: Run security-focused review with the security reviewer agent
---

# Security Review

Run a targeted security review using the Shield security reviewer agent.

## Behavior

1. Detect the review context:
   - If Terraform files are present → dispatch `shield:security-reviewer` in **infra-code** mode
   - If reviewing a plan document → dispatch in **plan** mode
2. Also invoke `shield:terraform:security-audit` skill if terraform domain is active
3. Present findings sorted by severity
4. Ask user which fixes to apply

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name. If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available, otherwise the current git branch name.

Write findings to the config-driven feature directory:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/
├── summary.md          (security-focused)
├── changes.md
└── detailed/security.md
```

5. Write detailed findings, summary, and applied changes to the paths above
6. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
