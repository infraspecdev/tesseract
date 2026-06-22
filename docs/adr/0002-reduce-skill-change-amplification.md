# ADR 0002 — Reduce change amplification in skills: one home per fact, references everywhere else

**Status:** Proposed
**Date:** 2026-06-17
**Authors:** @ashwinimanoj
**Plugin:** shield
**Supersedes:** —
**Related:**
- `shield/schema/output-paths.yaml` (existing path registry — the precedent this ADR generalizes)
- `docs/adr/0001-introduce-prd-layer.md`
- `CLAUDE.md` → "Eval coverage — MANDATORY for plugin updates"

---

## TL;DR

The problem with Shield's skills isn't that they're "too specific" — it's **change amplification**: a single conceptual change forces edits across many scattered places that must all agree. Measured today:

| Modify one… | Files touched | Cause |
|---|---|---|
| Output path (`plan.json`) | **40** | registry + inline prose literals + command frontmatter + scripts hardcoding the literal + hook context |
| PM rubric dimension | **6** | agent def + `dimensions.md` + `scoring.md` weights + 3 orchestrator prose lists |
| Plugin name / namespace | **203 `shield:` literals across 34 files** | namespace prefix hardcoded into every agent dispatch |
| Doc section | **12** | sections restated in prose *and* in `trd-sections.yaml` |
| Orchestrator step | **2× per file** | each step lives in a Step-Skeleton table *and* is re-described in the body |

Root cause: **the same fact has many homes.** A path, a dimension, an agent slug, a step is *restated* in every skill that uses it instead of *referenced* from one source.

Decision: enforce one principle — **every fact has exactly one home; everything else points to it by name.** Skills reference `{registry-name}`, iterate a roster, and import from a schema, rather than restating literals. This is what `output-paths.yaml` already does for paths; we finish it for dimensions, agents, sections, steps, and the brand/namespace. Result: a representative change touches ~1 home instead of dozens, and re-skinning into a non-Shield product falls out for free.

---

## Context — what change amplification looks like here

"Change amplification" (Ousterhout): a good design minimizes the number of places that must change for one modification, *and* the number of those places that must stay in agreement. Shield's skills score badly on both because the same fact is **restated, not referenced**.

### Three duplication patterns drive all of it

**1. Cross-skill restatement of a literal.**
A path or name is typed verbatim into every skill that uses it. `plan.json` appears in 40 files; the literal string `docs/shield` appears inline 29 times *next to* the registry that was supposed to replace it. Change the fact → hunt down every copy.

**2. Internal restatement within a skill.**
Every orchestrator (`research`, `review`, `plan-review`, `prd-review`, `plan-docs`, `prd-docs`, `implement-feature`) carries a **Step-Skeleton table** *and* a body that re-describes each step in prose. Add or reorder a step → edit it twice in the same file, kept in sync by hand.

**3. Prose restating what a schema already holds.**
TRD/PRD section structure lives in `schema/trd-sections.yaml`, `lld-sections-*.yaml`, and the validator/renderer scripts — *and* is listed again in `plan-docs`, `prd-docs`, `plan-review`, `prd-review`, `lld-docs` prose. The 14-/20-section facts have ~12 homes.

### The namespace is the worst case

The agent-namespace prefix `shield:` is hardcoded into every dispatch — **203 literals across 34 files** (skills + commands + agent defs). Renaming the plugin, or adding/renaming a reviewer agent, ripples through all of them. This is pure restatement: the prefix is one fact written 203 times.

### What already does it right (the precedent to extend)

We have working single-source examples in every category — they're just applied inconsistently:

- **Paths** → `schema/output-paths.yaml` ("Plugin-owned contract. Consumers should NOT edit"). Skills reference `{research}`, `{review_summary}` by name. *But scripts still hardcode the literals instead of importing from it, and 29 inline `docs/shield` strings remain.*
- **Doc shapes** → `schema/trd-sections.yaml`, `lld-sections-*.yaml`. *But prose re-lists the sections.*
- **Dimensions** → `plan-review/dimensions.md` registry. *But orchestrator prose re-types the dimension list inline.*
- **Per-project values** → `.shield.json` already carries `output_dir` and `prd_review_personas`.

The pattern is proven. The failure is that "reference" keeps degrading back into "restate."

---

## Decision — one home per fact

**Rule:** each fact (a path, a dimension + its weight, an agent + the dims it owns, a doc section, a step, the product name, the namespace prefix) lives in exactly one source. Skill prose, command frontmatter, and scripts all **reference it by name** — they never re-type the literal.

The test for any edit: *"To change this fact, how many files do I touch?"* The target is **one** (the home) plus references that don't need editing because they point rather than copy.

### Where each fact's single home lives

| Fact | One home | Consumers reference by… |
|---|---|---|
| Output paths | `schema/output-paths.yaml` (already) | `{registry-name}`; **scripts import it too** (stop hardcoding) |
| Doc section scaffolds | `schema/*-sections.yaml` (already) | prose iterates / links the schema, never re-lists |
| Rubric dimensions + weights | `schema/rubric.yaml` (promote `dimensions.md` + `scoring.md` WEIGHTS) | orchestrator iterates the registry |
| Reviewer-agent roster | `schema/agents.yaml` (slug → dims owned) | orchestrator dispatches "every agent owning an active dim" |
| Orchestrator steps | the Step-Skeleton table | body keys off step IDs; **no second prose copy of the step list** |
| Product name (`Shield`) | a profile | `{product_name}` placeholder |
| Agent namespace (`shield:`) | a profile | `{ns}` prefix, resolved once |

### Two structural fixes that kill the worst amplification

**Collapse the Step-Skeleton duplication.** The table is the spec. The body addresses steps by ID and adds only the detail the table can't hold — it does not restate the step list. One step, one home.

**Make the registry the source for scripts, not just prose.** `validate_plan.py`, `render_trd_section.py`, etc. should read paths/sections from `output-paths.yaml` / `*-sections.yaml` rather than embedding the literal. That alone drops the `plan.json` blast radius from 40 toward a handful.

### Folder split (secondary, supports the above)

`general/` is a junk drawer (15 skills, 61→465 lines, no shared property). Split by kind so the dependency direction is visible and each kind has a place to grow:

```
skills/
  orchestrators/   research, plan-docs, prd-docs, review, plan-review, prd-review, implement-feature, pm-analysis
  lib/             writing-style, summarize, execute-steps, story-coverage, milestone-coverage
  contracts/       prd-docs, plan-docs, lld-docs, backlog  (author-procedure + pointer to schema home)
```

(Names illustrative; settled in the migration plan.)

---

## Scope guardrail — don't trade amplification for indirection

Every externalized fact is a file-hop the model must follow and less inline context at the point of use. Give a fact its own home **only if** it is (a) restated in ≥2 places today, or (b) something a maintainer changes as a unit. A fact used in exactly one skill stays inline — moving it out adds indirection without removing duplication. We are removing *restatement*, not dissolving Shield's opinions into config soup. The 20-section scaffold and PM1–PM11 rubric stay exactly as opinionated — they just stop being copied.

### Verbs stay inline; nouns get a home

The line between "stays in the skill" and "gets externalized" is **verb vs. noun**:

- **Verb — stays in the skill.** *Which script to run* (`validate_plan.py`, `render_trd_section.py`) is part of the procedure. The skill is the right and only home for it. We deliberately do **not** build a script-name registry: you rename a script rarely (a code refactor), but you change a path/dimension/agent often (content work). A name-lookup indirection would tax the common path to save effort on the rare one — the over-rotation trap. Script names stay inline even though a few (`write_shield_assets.py`) appear in ~6 skills.
- **Noun — gets a home.** *The data the script reads or writes* (paths) lives in the registry.

For path nouns specifically, "external" must hold in **three places** or the literal just moves:

```
uv run "$CLAUDE_PLUGIN_ROOT/scripts/render_trd_section.py" milestones {plan_json}
        └──────────── verb: stays in skill ────────────┘            └ noun: registry name ┘
```

1. **Skill prose** — reference `{plan_json}`, never a literal path.
2. **The invocation args** — pass the registry name, not a literal.
3. **The script's own code** — `validate_plan.py` reads the path from `output-paths.yaml` instead of hardcoding `plan.json`. *This is the lever that collapses the 40-file blast radius — the skills are mostly fixed already; the scripts each re-embed the literal.*

### Script root: always `$CLAUDE_PLUGIN_ROOT/scripts/`

The script *location* is a noun with one home: the `$CLAUDE_PLUGIN_ROOT` env var the harness sets. Today this is violated — **39 bare `shield/scripts/...` literals across 15 files** vs only 18 correct `$CLAUDE_PLUGIN_ROOT/scripts/...` usages. The bare form is both restatement *and* a portability bug: it only resolves when the working directory is the repo root, so it breaks for an installed plugin. Every script call must use `$CLAUDE_PLUGIN_ROOT/scripts/<name>`; the single-home guard (below) fails on any bare `shield/scripts/`.

---

## Consequences

**Positive**
- A representative change (add a dimension, rename an artifact, add an agent, reorder a step) touches ~1 home instead of 6–40.
- Sync bugs disappear: prose and schema can't drift when prose doesn't hold a copy.
- Skills get shorter and easier for the model to follow.
- Re-skinning into a non-Shield product becomes a profile + contract edit, not a 203-site prose rewrite — a free byproduct of the namespace/name having one home.

**Negative / risks**
- More runtime file-hops; bounded by the guardrail.
- Migration spans ~15 skills, agent defs, commands, and several scripts (the namespace and paths live in all of them). Must be staged.
- Risk that the harness can't resolve a profile/registry reference at skill-load time. **Validate the resolution mechanism on one skill before rollout.**

---

## Migration plan (staged; each stage ships eval coverage per CLAUDE.md)

1. **Prototype on one orchestrator** (`review` or `research`): collapse its Step-Skeleton duplication, drive its dispatch from a roster, resolve `{product_name}`/`{ns}`. Prove load-time resolution works. Gate the rollout on this.
2. **Path literals → single home**: delete the 29 inline `docs/shield` strings; make scripts import from `output-paths.yaml`; rewrite the 39 bare `shield/scripts/...` references to `$CLAUDE_PLUGIN_ROOT/scripts/...`.
3. **Dimensions + roster → `schema/rubric.yaml`, `schema/agents.yaml`**: convert `plan-review`/`prd-review` to iterate instead of listing.
4. **Step-skeleton collapse** across the remaining orchestrators.
5. **Split `general/`**; update cross-references.
6. **Namespace/name → profile**: replace the 203 `shield:` literals and `Shield` strings with placeholders resolved from one home.

### Eval coverage (definition of done)

- **Single-home guard (RED→GREEN):** an eval that fails if a fact appears outside its home — inline `docs/shield`, a bare `shield/scripts/` path, a hand-typed dimension list, a literal `shield:` outside the profile, a step restated in both table and body. RED today; GREEN after each stage.
- **Blast-radius regression:** for each scenario in the TL;DR table, assert the touch-count after migration is at or below a committed ceiling (e.g. path change ≤ 3 files), so future edits can't reintroduce restatement.

---

## Alternatives considered

- **Leave it as-is.** Rejected: the amplification is measured and already causes drift (29 inline literals that the registry was meant to retire).
- **Generate skills from one big template.** Rejected: hides the engine behind a build step and is harder to read/debug than named references in plain prose.
- **One mega-config file.** Rejected: collapses distinct contracts (paths, sections, rubric, agents, profile) into a new junk drawer one layer down. Keep one home *per kind of fact*, not one file for all of them.
