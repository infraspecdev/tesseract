---
name: story-coverage
description: Use when checking that a PRD's user stories cover all persona-goal combinations and archetypal flows for its feature domain. Consumed by agile-coach reviewer (dim 4 eval points 4f/4g) and /prd author flow. Derives expected stories from personas + goals + domain hints.
---

# Story Coverage

Derive expected user stories from personas + goals + feature domain. Cross-reference NFR/GTM/rollout sections for orphan references.

## When to Use

- `shield:agile-coach-reviewer` calls this skill while grading dim 4 eval points 4f and 4g of a PRD
- `/prd` command (Phase B) calls this skill between PRD Sections 4 (Goals) and 6 (Stories) to scaffold expected stories

## Input contract

The caller provides:
- `personas`: list of {id, name, description, goals}
- `goals`: list of {id, description}
- `feature_domain`: best-effort domain hint (e.g., "auth", "payment", "content", "internal-tool", "infrastructure")
- `existing_sections`: optional — content of NFR / GTM / Rollout / Risks sections (for orphan-reference detection)

## Output contract

Return a list of expected stories with structured metadata:

```json
{
  "expected_stories": [
    {
      "rationale": "persona-goal" | "archetype" | "orphan-reference",
      "persona_id": "P1",
      "goal_id": "G1",
      "archetype": "password-reset",
      "story_title": "Anika resets her password",
      "story_template": { ... },
      "severity": "P0" | "P1" | "P2"
    }
  ]
}
```

## Derivation rules

(Filled in by Task 3)

## See Also

- `archetypes.md` — library of flow patterns per domain
