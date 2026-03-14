---
name: atmos-repo-review
description: Use when reviewing Atmos infrastructure repositories, evaluating IaC structure, or assessing components/stacks organization for quality and best practices
---

# Atmos Repository Review

## Overview

Structured review of Atmos infrastructure repositories with file-based analysis and implementation planning.

**Core principle:** Analysis and plans are ALWAYS persisted to files, even on re-reviews. Never skip writing files.

## When to Use

- Reviewing an Atmos components or stacks repository
- Evaluating Terraform/OpenTofu infrastructure organization
- Assessing IaC repository for Atmos best practices
- Onboarding to understand existing Atmos setup
- Re-grading after improvements (creates fresh analysis.md and plan.md)

## When NOT to Use

- Reviewing a single Terraform module that is not part of an Atmos repo
- General Terraform code review without Atmos structure concerns
- Reviewing Helm charts, Kubernetes manifests, or non-IaC code
- Quick one-off questions about Atmos configuration syntax
- The user explicitly asks for a non-structured review or casual feedback

## Workflow

```
Explore -> Questions (skip if known) -> Evaluate -> Write analysis.md -> Write plan.md
  -> Ask User: [proceed | stop | edit plan] -> Review Plan -> Execute Step by Step
```

## Critical Rules

1. **ALWAYS write analysis.md** — Even on re-reviews, create fresh analysis
2. **ALWAYS write plan.md** — Even if no P0 issues, document P1/P2 improvements
3. **ALWAYS ask user before executing** — Never auto-proceed to execution
4. **Show the user what was written** — Summarize key findings after writing files

## Workflow Steps

### 1. Explore Repository

Use Glob, Read, and file exploration to understand structure. Check for: `atmos.yaml`, `stacks/`, `components/terraform/`, `catalog/`, CI/CD config, version constraints, provider/backend files, pre-commit hooks, terraform-docs setup, release tooling, and per-component versioning strategy.

Identify repo type: **components-only**, **stacks-only**, or **monorepo**.

### 2. Ask Clarifying Questions

On first review, ask 10-15 questions covering architecture, scale, operations, development, and governance. Skip on re-review if context is known. See [templates.md](./templates.md) for question categories.

### 3. Evaluate Against Criteria

Score 10 dimensions on a 1-5 scale (structure, environments, DRY, naming, layering, security, operability, scalability, CI/CD, blast-radius). See [scoring-rubric.md](./scoring-rubric.md) for full rubric and grading scale (A-F).

### 4-5. Write analysis.md and plan.md

Write both files to `<repo-root>/claude/atmos-repo-review/`. Use templates from [templates.md](./templates.md). Check findings against [red-flags-reference.md](./red-flags-reference.md).

### 6. Ask User to Confirm

Present grade summary and offer three choices: proceed, stop, or wait for edits.

### 7-8. Review Plan and Execute

Re-read plan.md for user edits, clarify ambiguities, then execute step by step. Announce each step, show changes, update verification checkboxes, and stop on failures.

## Common Mistakes

| Mistake | Why It Matters | What to Do Instead |
|---------|---------------|-------------------|
| Skipping file writes on re-review | Loses audit trail; user expects fresh files each time | Always write both analysis.md and plan.md |
| Auto-executing the plan | User may want to edit plan.md first | Always ask and wait for confirmation |
| Scoring without exploring fully | Leads to inaccurate grades and missed issues | Check all directories, CI config, and gitignore before scoring |
| Ignoring repo type distinction | Components-only repos have different expectations than monorepos | Identify repo type in Phase 1 and adjust criteria accordingly |
| Missing provider/backend nuance | Atmos generates override files at deploy time | Consult [red-flags-reference.md](./red-flags-reference.md) for commit rules |

## Supporting Files

- [templates.md](./templates.md) — Output templates, question categories, confirmation prompt
- [scoring-rubric.md](./scoring-rubric.md) — Evaluation dimensions and grading scale
- [red-flags-reference.md](./red-flags-reference.md) — Red flags, provider/backend rules, quick reference
