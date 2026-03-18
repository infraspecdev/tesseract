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

Write findings to a timestamped review directory:

```
{project_root}/shield/docs/reviews-YYYYMMDD-HHMMSS/
├── summary/cost-review-summary.md
├── summary/cost-review-changes.md
└── detailed/cost.md
```

5. Write detailed findings, summary, and applied changes to the paths above
6. Ask user which fixes to apply
