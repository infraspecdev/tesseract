---
name: prd
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Author a new PRD with Shield's 20-section problem-first scaffold (or 10-section lean variant). Includes Terminologies (§2, auto-filled from research+body), Architecture & flows (§5, optional Mermaid), per-story Type labels (new/enhancement/existing) in §8, and auto-generated TOC + rendered Mermaid in prd.html. Supports custom team templates, lean→standard upgrade flow.
outputs: [prd, prd_html]
---

# /prd

Author a PRD interactively. Walks the user through the scaffold; invokes `shield:story-coverage` for story scaffolding; writes `prd.md`, `prd.html`, `prd.meta.json`.

## Usage

```
/prd                          # interactive — prompts for everything
/prd <topic>                  # uses topic as seed for Problem / feature name
/prd --feature <name>         # explicit feature folder
```

## Paths

| Registry key | Resolved path |
|---|---|
| `prd` | `{output_dir}/{feature}/prd.md` |
| `prd_html` | `{output_dir}/{feature}/outputs/prd.html` |

`prd.meta.json` is a metadata sidecar written to `{output_dir}/{feature}/prd.meta.json` — it is not a primary deliverable and is not in the registry (similar to `.session-transcript.md` from /research).

## What it does

1. **Reads `.shield.json`** for `prd_template` (custom team template path, optional)
2. **Resolves feature folder** — `--feature` flag or current context
3. **Detects prior lean PRD** in the folder — if present, offers upgrade flow (multi-select of standard sections to add)
4. **Asks for PRD type** — standard (20 sections) or lean (10 sections)
5. **Pre-populates from prior `/research` transcript** if present
6. **Walks Section 1** (Header) — defers Section 2 (Terminologies) for now
7. **Walks Sections 3, 4** (Problem, Personas), **then Section 5** (Architecture & flows — optional Mermaid), **then Section 6** (Goals)
8. **Invokes `shield:story-coverage`** between Sections 6 and 8 — scaffolds expected stories *(standard only — lean skips story-coverage)*
9. **Walks Section 7** (Metrics); for standard, also walks Section 8 (Stories — prompts each story for Type: new | enhancement | existing)
10. **Walks Sections 9..14** (Functional through Assumptions) *(standard only)*
11. **Invokes `shield:milestone-coverage`** between Sections 8 and 15 — scaffolds Milestones into §15 (or §8 for lean)
12. **Walks Section 15** rollout-mechanics, **then Sections 16..20** *(standard only — lean walks §9 Open questions, §10 Out of scope)*
13. **Builds Terminologies (§2)** — copies from research-transcript glossary, proposes terms via LLM scan of drafted body, user confirms
14. **Merges custom template** if configured
15. **Writes** `prd.md`, `prd.html` (rendered via Shield's renderer — includes auto-TOC + Mermaid rendering), `prd.meta.json`

## Output

```
{output_dir}/{feature}/
├── prd.md            ← registry: {prd}      = {feature_dir}/prd.md
├── outputs/prd.html  ← registry: {prd_html} = {feature_outputs}/prd.html
└── prd.meta.json     ← side-artifact (metadata sidecar, not in registry)
```

## Reference

Full behavior in `shield/skills/general/prd-docs/SKILL.md`.

## See also

- `/prd-review` — multi-persona gap review on this PRD
- `/plan` — generate technical breakdown from this PRD
- `/research` — capture product+tech context before authoring
