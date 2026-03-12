---
name: plan-review
description: Run a multi-persona review on a plan document — dispatches expert reviewers in parallel and produces a scored analysis with prioritized recommendations
disable-model-invocation: true
---

# /plan-review

Run a multi-persona plan review. This command dispatches 3-5 expert reviewer agents in parallel to evaluate a plan document, then produces a scored analysis and enhanced plan.

## Usage

```
/plan-review [path-to-plan]
```

If no path is provided, auto-detect the most recently generated plan document in the working directory.

## Process

1. **Locate the plan** — use the provided path or auto-detect recent plan files (`*plan*.html`, `*plan*.md`)
2. **Read the plan** — load the full document content
3. **Invoke the plan-review skill** — the skill handles persona selection, parallel dispatch, scoring, and output generation
4. **Write output** — results go to `review/<YYYY-MM-DD>-<topic-slug>/analysis.md` and `plan.md`

## Reviewers

| Reviewer | Focus | Weight |
|----------|-------|--------|
| Cloud Architect | Infrastructure, scalability, HA, operational readiness | 1.0 |
| Security Engineer | Security, threat modeling, testability, validation | 1.0 |
| DX Engineer | Plan clarity, actionability, software architecture | 1.0 |
| Cost/FinOps | Cost awareness, right-sizing, environment tiering | 0.7 |
| Agile Coach | Sprint-readiness, story quality, dependencies | 0.7 |

Not all reviewers run every time — the skill dynamically selects 3-5 based on plan content.

## Output

- `review/<date>-<slug>/analysis.md` — scored evaluation with per-persona grades, consolidated recommendations (P0/P1/P2)
- `review/<date>-<slug>/plan.md` — enhanced plan with review feedback applied
