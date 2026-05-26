---
name: story-coverage
description: Use when checking that a PRD's user stories cover all persona-goal combinations and archetypal flows for its feature domain. Consumed by agile-coach reviewer (dim 4 eval points 4f/4g) and /prd author flow. Derives expected stories from personas + goals + domain hints.
---

# Story Coverage

Derive expected user stories from personas + goals + feature domain. Cross-reference NFR/GTM/rollout sections for orphan references.

## When to Use

- `shield:agile-coach` calls this skill while grading dim 4 eval points 4f and 4g of a PRD
- `/prd` command (Phase B) calls this skill between PRD Sections 6 (Goals) and 8 (Stories) to scaffold expected stories

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

### Rule 1 — Persona × Goal cross-product

For each `(persona, goal)` pair, derive at minimum:
- **Happy path story** — the persona achieves the goal successfully
- **One named error/recovery path** — what happens when the happy path fails (timeout, partial failure, user abandons)

If 0 stories address a `(persona, goal)` pair → flag P0 ("persona P's goal G has no story").
If exactly 1 story (happy path only) → flag P1 ("persona P's goal G has happy path but no error/recovery").

### Rule 2 — Archetype match

Look up the feature domain in `archetypes.md`. If the domain matches one of: `auth`, `payment`, `content`, `lifecycle`, `multi-region`, `billing`, `observability`, retrieve its archetypal flow list.

For each archetypal flow that's NOT covered by an existing story → flag P1 or P2 based on the archetype's marked severity in archetypes.md.

Example: domain=auth has archetypes `signup`, `login`, `password-reset`, `account-deletion`. If the PRD has signup but no password-reset story, return:
```json
{
  "rationale": "archetype",
  "archetype": "password-reset",
  "story_title": "User resets forgotten password",
  "severity": "P1"
}
```

### Rule 3 — Orphan-reference detection

Parse `existing_sections` (NFR / GTM / Rollout / Risks). For each mention of an action verb that implies a flow (e.g., "rollback", "deactivate", "delete", "migrate"), check whether a story exists addressing that flow.

Example: NFR section says "supports user-initiated account deletion per GDPR Article 17"; no story covers account deletion → return `{ rationale: "orphan-reference", severity: "P0", source_section: "NFR", source_quote: "supports user-initiated account deletion..." }`.

### Domain detection

If the caller didn't pass `feature_domain`, infer from PRD title + Problem section + Personas:
- keywords like "login", "auth", "password", "session" → auth
- "payment", "checkout", "billing", "subscription" → payment / billing
- "post", "article", "comment", "media" → content
- "cron", "pipeline", "internal tool", "back-office" → internal-tool / infrastructure
- No clear match → return empty domain; skip Rule 2

### Output format

Return JSON with one entry per expected-but-missing story:

```json
{
  "expected_stories": [
    {
      "rationale": "persona-goal | archetype | orphan-reference",
      "persona_id": "P1",
      "goal_id": "G1",
      "archetype": "password-reset",
      "story_title": "User resets forgotten password",
      "severity": "P0 | P1 | P2",
      "story_template": {
        "persona": "P1",
        "goal": "Reset forgotten password without contacting support",
        "happy_path": ["..."],
        "error_paths": ["..."],
        "edge_cases": ["..."],
        "state_transitions": "...",
        "cross_functional_handoffs": "...",
        "acceptance_criteria": [{"given": "...", "when": "...", "then": "..."}]
      }
    }
  ]
}
```

**Default story Type.** Scaffolded stories are created with `Type: new` as a placeholder. The user overrides this during `/prd`'s §8 walk — particularly for rewrites of existing services, where some stories will be retyped to `enhancement` or `existing`.

## See Also

- `archetypes.md` — library of flow patterns per domain
