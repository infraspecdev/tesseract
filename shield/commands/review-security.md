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

Write findings to a timestamped review directory:

```
{project_root}/shield/docs/reviews-YYYYMMDD-HHMMSS/
├── summary/security-review-summary.md
├── summary/security-review-changes.md
└── detailed/security.md
```

5. Write detailed findings, summary, and applied changes to the paths above
