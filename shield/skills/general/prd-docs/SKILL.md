---
name: prd-docs
description: Use when authoring a new PRD or upgrading a lean PRD to standard. Walks user through 17-section problem-first scaffold (or 7-section lean), pre-populates from prior /research transcript if present, invokes shield:story-coverage between Sections 4 and 6, supports custom team templates via .shield.json. Triggers on /prd, write a PRD, author a PRD.
---

# PRD Docs

Author a new PRD with the Shield 17-section problem-first scaffold (or lean variant), or upgrade an existing lean PRD to standard by adding missing sections.

## Output Path — MANDATORY

```
{output_dir}/{feature}/prd/{N}-{slug}/
├── prd.md
├── prd.html
└── prd.meta.json
```

Where `{output_dir}` comes from `.shield.json`, `{feature}` is the feature folder, `{N}` is sequential. The `prd.meta.json` records type, status, owner, last_updated, rubric_version, and `linked_plans` (auto-populated by `/plan` when it runs).

## When to Use

- User invokes `/prd` to author a new PRD
- User invokes `/prd` in a feature folder containing a lean PRD (triggers upgrade flow)

## When NOT to Use

- **Review an existing PRD** — use `/prd-review` instead
- **Generate a plan from a PRD** — use `/plan` instead
- **Capture pre-PRD context** — use `/research` instead

## Workflow

(Filled in by Task 5 — orchestration workflow + step skeleton)

## See Also

- `templates.md` — 17-section scaffold + lean variant + HTML render templates
- `meta-schema.md` — prd.meta.json schema
- `type-detection.md` — lean vs standard heuristics
- `shield:story-coverage` skill — invoked between Sections 4 and 6 for scaffolding
