---
description: "Run a CI/CD workflow audit of the repository's GitHub Actions (versions, permissions, concurrency, path filters)"
disable-model-invocation: true
---

# CI/CD Review

Run a GitHub Actions workflow audit for the current repository.

## Process

1. Invoke the `infra-review:github-actions-reviewer` skill
2. Read all workflows in `.github/workflows/`
3. Read related config files (release config, versions.tf, tflint config)
4. Evaluate against the full checklist (version consistency, plugin alignment, permissions, concurrency, path filters, reusable workflows, action pinning, secrets handling)
5. Write analysis and plan to `claude/infra-review/cicd-review.md` in the repository root

Present the grade and key findings to the user.
