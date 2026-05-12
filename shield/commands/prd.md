---
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Author a new PRD with Shield's 17-section problem-first scaffold (or 7-section lean variant). Supports custom team templates, lean→standard upgrade flow, and consumes prior /research transcripts as pre-population.
---

# /prd

Author a PRD interactively. Walks the user through the scaffold; invokes `shield:story-coverage` for story scaffolding; writes `prd.md`, `prd.html`, `prd.meta.json`.

## Usage

```
/prd                          # interactive — prompts for everything
/prd <topic>                  # uses topic as seed for Problem / feature name
/prd --feature <name>         # explicit feature folder
```

## What it does

1. **Reads `.shield.json`** for `prd_template` (custom team template path, optional)
2. **Resolves feature folder** — `--feature` flag or current context
3. **Detects prior lean PRD** in the folder — if present, offers upgrade flow (multi-select of standard sections to add)
4. **Asks for PRD type** — standard (17 sections) or lean (7 sections)
5. **Pre-populates from prior `/research` transcript** if present
6. **Walks Sections 1-4** (Header, Problem, Personas, Goals)
7. **Invokes `shield:story-coverage`** between Sections 4 and 6 — scaffolds expected stories (persona × goal + archetypal flows) for user confirmation/skip
8. **Walks remaining sections** (5, 6 content, 7-17 for standard; 5, 16, 17 for lean)
9. **Merges custom template** if configured — appends missing required sections with `<!-- Shield: added required section -->` markers
10. **Writes** `prd.md`, `prd.html` (rendered via Shield's standard CSS), `prd.meta.json` (with linked_plans field — auto-populated by `/plan` later)

## Output

```
{output_dir}/{feature}/prd/{N}-{slug}/
├── prd.md
├── prd.html
└── prd.meta.json
```

## Reference

Full behavior in `shield/skills/general/prd-docs/SKILL.md`.

## See also

- `/prd-review` — multi-persona gap review on this PRD
- `/plan` — generate technical breakdown from this PRD
- `/research` — capture product+tech context before authoring
