---
name: github-actions-reviewer
description: Use when reviewing, auditing, or improving GitHub Actions workflows in a repository — checks for version drift, permission issues, missing concurrency controls, path filter gaps, and cross-workflow inconsistencies
---

# GitHub Actions Reviewer

## Overview

Structured review of GitHub Actions workflows for consistency, security, and operational best practices.

**Core principle:** Workflows in the same repo form a system. Review them as a group, not individually — inconsistencies between workflows cause the hardest-to-debug CI failures.

## When to Use

- Reviewing CI/CD workflows in any repository
- Auditing workflow permissions and security posture
- Checking for version drift across workflows
- After adding a new workflow to verify consistency with existing ones
- Periodic hygiene check on GitHub Actions setup
- Re-grading after improvements (creates fresh analysis and plan)

## When NOT to Use

- Debugging a single workflow run failure (use GitHub's run logs instead)
- Writing new workflows from scratch (this skill reviews existing ones)
- Non-GitHub CI systems (Jenkins, GitLab CI, CircleCI)
- Reviewing application code that happens to be triggered by workflows

## Workflow

Read All Workflows + Config -> Evaluate Against Checklist -> Write analysis.md -> Write plan.md -> Ask User to Confirm -> (proceed: Execute / stop: Done / edit: revise plan.md)

## Critical Rules

1. **ALWAYS write analysis.md and plan.md** — Even on re-reviews or when no issues found. Never skip file output.
2. **ALWAYS ask user before executing** — Never auto-proceed to implementation.
3. **Show the user what was written** — Summarize key findings after writing files.

## Steps

### 1. Read All Workflows and Config

Read every file in `.github/workflows/` plus related config: release tooling configs (`release-please-config.json`, `.releaserc.json`, etc.), `versions.tf`, `.tflint.hcl`, `package.json`.

### 2. Evaluate Against Checklist

Run through the 8-point checklist covering version consistency, plugin/config alignment, permissions, concurrency control, path filters, reusable patterns, action pinning, and secrets handling. See **checklist.md** for detailed criteria, examples, and red flags.

### 3. Write analysis.md

Write findings, checklist results, and a letter grade (A-F) to `claude/github-actions-review/analysis.md` in the target repo. See **templates.md** for the full template.

### 4. Write plan.md

Write actionable implementation steps (or confirm no changes needed) to `claude/github-actions-review/plan.md`. See **templates.md** for the full template.

### 5. Ask User to Confirm

Present: "I've written the analysis (Grade: X) and plan (Y steps). Would you like me to proceed, stop here, or wait while you edit plan.md?"

### 6. Execute Step by Step

For each plan step: announce it, execute, show what changed, update verification checkboxes in plan.md, and confirm before moving to the next step. Stop and ask for input if anything fails.

## Common Mistakes

| Mistake | Why It Fails | Do Instead |
|---------|-------------|------------|
| Reviewing workflows individually | Misses cross-workflow inconsistencies (version drift, permission gaps) | Always read all workflows before evaluating any |
| Skipping file output on re-review | User loses the updated analysis and grade | Always write fresh analysis.md and plan.md |
| Auto-executing the plan | User hasn't reviewed or approved changes | Always ask for confirmation first |
| Ignoring release tooling config | Plugin mismatches between preview and release workflows go undetected | Read `.releaserc.json`, `release-please-config.json`, etc. |
| Checking only permissions at workflow level | Job-level permissions override workflow-level | Check both levels |

## Supporting Files

- **checklist.md** — Full 8-point review checklist with tables, YAML examples, and red flags
- **templates.md** — Output templates for analysis.md and plan.md
