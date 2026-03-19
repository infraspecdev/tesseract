---
name: review-well-architected
description: Run AWS Well-Architected Framework review across all 6 pillars
---

# Well-Architected Review

Run a holistic infrastructure review using the AWS Well-Architected Framework.

## Output Path

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name. If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available, otherwise the current git branch name.

Write findings to the config-driven feature directory:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/
├── summary.md          (well-architected)
├── changes.md
└── detailed/well-architected.md
```

## Behavior

1. Dispatch `shield:well-architected-reviewer` agent in **infra-code** mode
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
6. Write detailed findings, summary, and applied changes to the paths above
7. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
8. Ask user which fixes to apply
