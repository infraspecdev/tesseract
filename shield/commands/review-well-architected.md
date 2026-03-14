---
name: review-well-architected
description: Run AWS Well-Architected Framework review across all 6 pillars
---

# Well-Architected Review

Run a holistic infrastructure review using the AWS Well-Architected Framework.

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
6. Ask user which fixes to apply
