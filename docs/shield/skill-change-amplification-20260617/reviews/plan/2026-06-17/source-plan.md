<!-- sidecar: ./plan.json -->

# Detailed Plan — Reduce skill change amplification

**Project:** Shield · **Phase:** Skills maintainability refactor · **Source:** [ADR 0002](../../adr/0002-reduce-skill-change-amplification.md) · [TRD](./trd.md)

Give each fact one home so a representative change touches ~1 file instead of 6–40. Six milestones, gated on a one-skill prototype, each shipping eval coverage.

## Milestones

| ID | Milestone | Depends on |
|---|---|---|
| M1 | Pattern proven on one skill | — |
| M2 | Paths and script root have one home | M1 |
| M3 | Rubric and agent roster are data | M1 |
| M4 | Steps stated once per skill | M1 |
| M5 | Skills grouped by kind | M2, M3, M4 |
| M6 | Brand and namespace are a profile | M5 |

## Stories

| ID | Story | Milestone | Priority | Status |
|---|---|---|---|---|
| EPIC-1-S1 | Prototype the single-home pattern on one orchestrator | M1 | high | ready |
| EPIC-1-S2 | Add the single-home guard eval (RED) | M1 | high | ready |
| EPIC-2-S1 | Route all path nouns through the registry | M2 | high | ready |
| EPIC-2-S2 | Normalize the scripts root to $CLAUDE_PLUGIN_ROOT | M2 | high | ready |
| EPIC-3-S1 | Promote rubric dimensions and agent roster to schema | M3 | high | ready |
| EPIC-3-S2 | Convert plan-review and prd-review to iterate the roster | M3 | medium | ready |
| EPIC-4-S1 | Make the Step-Skeleton table the single home for steps | M4 | medium | ready |
| EPIC-5-S1 | Split general/ into orchestrators, lib, and contracts | M5 | medium | ready |
| EPIC-6-S1 | Move product name and namespace into a profile | M6 | medium | ready |
| EPIC-6-S2 | Add the re-skin smoke test | M6 | low | ready |

---

## EPIC-1 — Establish the single-home pattern and guardrails

### EPIC-1-S1 — Prototype the single-home pattern on one orchestrator
**Milestone:** M1 · **Priority:** high · **Status:** ready
**Design:** [§7 High-Level Design](./trd.md#high-level-design), [§10 Milestones](./trd.md#milestones)

Convert one orchestrator (`review` or `research`) end-to-end to the single-home pattern: path nouns via registry name, dispatch driven by a roster, and verbs (script names) left inline. Prove the harness resolves the references at skill-load time before rolling the pattern out.

**Tasks**
- Pick `review` or `research` as the prototype and inventory its inline path literals, hand-typed lists, and step duplication.
- Replace inline `docs/shield` literals with registry names resolved from `output-paths.yaml` + `.shield.json` `output_dir`.
- Drive its reviewer/agent dispatch from a roster reference instead of a hand-typed list.
- Run the orchestrator in a dispatched subagent and confirm every reference resolves at load time with no dangling placeholder.

**Acceptance criteria**
- The prototype orchestrator contains zero inline `docs/shield` literals (grep returns nothing).
- Its dispatch list is sourced from a roster reference, not re-typed inline.
- A GREEN subagent run produces correct artifacts with all references resolved (no literal `{output_dir}` or `{ns}` left in output).

### EPIC-1-S2 — Add the single-home guard eval (RED)
**Milestone:** M1 · **Priority:** high · **Status:** ready
**Design:** [§5 Functional Requirements](./trd.md#functional-requirements), [§9 Cross-Cutting Concerns](./trd.md#cross-cutting-concerns)

Author `scripts/check_single_home.py` plus an eval that fails when any fact appears outside its home. It starts RED against today's tree and turns GREEN class-by-class as later stages land.

**Tasks**
- Implement `check_single_home.py` covering: inline `docs/shield`, bare `shield/scripts/`, hand-typed dimension lists, literal `shield:` outside the profile, and steps restated in both table and body.
- Wire it into the eval suite so a non-zero exit fails CI.
- Capture the current RED baseline (counts per violation class) as the regression starting point.

**Acceptance criteria**
- `check_single_home.py` exits non-zero on the current tree and prints a per-class violation count.
- The eval is registered in `evals/` and fails today (documented RED baseline).
- Each violation class can be queried independently so stages can flip them GREEN one at a time.

---

## EPIC-2 — Centralize path and script-root facts

### EPIC-2-S1 — Route all path nouns through the registry
**Milestone:** M2 · **Priority:** high · **Status:** ready
**Design:** [§5 Functional Requirements](./trd.md#functional-requirements), [§11 APIs Involved](./trd.md#apis-involved)

Delete the 29 inline `docs/shield` literals from skill and command prose, and make the path-consuming Python scripts read filenames from `output-paths.yaml` instead of hardcoding them. This is the lever that collapses the 40-file `plan.json` blast radius.

**Tasks**
- Replace every inline `docs/shield` literal in `skills/` and `commands/` with the matching registry name + `{output_dir}` resolution.
- Refactor `validate_plan.py`, `render_trd_section.py`, and other path-consuming scripts to import paths from `output-paths.yaml`.
- Add a blast-radius regression asserting a path change touches ≤3 files.

**Acceptance criteria**
- grep for `docs/shield` in `skills/` and `commands/` prose returns zero hits.
- Scripts no longer contain hardcoded `plan.json` / `research.md` / `trd.md` filename literals; they resolve from the registry.
- The blast-radius regression for a path rename passes at the ≤3-file ceiling.

### EPIC-2-S2 — Normalize the scripts root to $CLAUDE_PLUGIN_ROOT
**Milestone:** M2 · **Priority:** high · **Status:** ready
**Design:** [§6 Non-Functional Requirements](./trd.md#non-functional-requirements)

Rewrite the 39 bare `shield/scripts/` references across 15 files to `$CLAUDE_PLUGIN_ROOT/scripts/`. The bare form is both restatement and a portability bug that only resolves when cwd is the repo root.

**Tasks**
- Find every bare `shield/scripts/` reference in `skills/` and `commands/`.
- Rewrite each to `$CLAUDE_PLUGIN_ROOT/scripts/<name>`.
- Extend `check_single_home.py` to fail on any bare `shield/scripts/` path.

**Acceptance criteria**
- grep for bare `shield/scripts/` in `skills/` and `commands/` returns zero hits.
- All script invocations use `$CLAUDE_PLUGIN_ROOT/scripts/`.
- `check_single_home.py`'s script-root check passes.

---

## EPIC-3 — Externalize rubric and agent roster

### EPIC-3-S1 — Promote rubric dimensions and agent roster to schema
**Milestone:** M3 · **Priority:** high · **Status:** ready
**Design:** [§7 High-Level Design](./trd.md#high-level-design), [§5 Functional Requirements](./trd.md#functional-requirements)

Move the PM rubric dimensions + weights into `schema/rubric.yaml` and the reviewer-agent roster (slug → owned dimensions) into `schema/agents.yaml`, giving each fact one home.

**Tasks**
- Consolidate `dimensions.md` and the `scoring.md` WEIGHTS table into `schema/rubric.yaml`.
- Build `schema/agents.yaml` mapping each reviewer agent slug to the dimensions it owns.
- Document both as plugin-owned contracts (consumers reference, do not re-list).

**Acceptance criteria**
- `schema/rubric.yaml` lists every PM dimension with its weight, with no duplicate source remaining.
- `schema/agents.yaml` maps every reviewer agent to its owned dimensions.
- Adding one dimension requires editing ≤2 files (blast-radius regression passes).

### EPIC-3-S2 — Convert plan-review and prd-review to iterate the roster
**Milestone:** M3 · **Priority:** medium · **Status:** ready
**Design:** [§7 High-Level Design](./trd.md#high-level-design)

Rewrite `plan-review` and `prd-review` so dispatch iterates `schema/agents.yaml` and grading iterates `schema/rubric.yaml`, removing the hand-typed dimension and agent lists from their prose.

**Tasks**
- Replace the inline dimension list in `plan-review`/`prd-review` with iteration over `schema/rubric.yaml`.
- Replace the inline agent dispatch list with iteration over `schema/agents.yaml`.
- Re-run `plan-review` and `prd-review` evals to confirm identical grading behavior.

**Acceptance criteria**
- No hand-typed dimension or agent list remains in `plan-review` or `prd-review` prose (`check_single_home.py` passes).
- `plan-review` and `prd-review` evals produce the same dimensions and dispatch set as before the change.
- Removing a dimension from `schema/rubric.yaml` drops it from both reviews with no prose edit.

---

## EPIC-4 — Collapse step-skeleton duplication

### EPIC-4-S1 — Make the Step-Skeleton table the single home for steps
**Milestone:** M4 · **Priority:** medium · **Status:** ready
**Design:** [§5 Functional Requirements](./trd.md#functional-requirements)

For each remaining orchestrator, treat the Step-Skeleton table as the spec and rewrite the body to address steps by ID, adding only detail the table cannot hold, so the step list is stated exactly once.

**Tasks**
- Audit each orchestrator for body prose that restates the Step-Skeleton table.
- Rewrite bodies to reference step IDs instead of re-listing steps.
- Add the step-duplication check to `check_single_home.py` and turn it GREEN.

**Acceptance criteria**
- No orchestrator body restates the step list held in its Step-Skeleton table.
- `check_single_home.py`'s step-duplication check passes for all orchestrators.
- Reordering a step in a spot-checked orchestrator changes exactly one region of the file.

---

## EPIC-5 — Restructure skills by kind

### EPIC-5-S1 — Split general/ into orchestrators, lib, and contracts
**Milestone:** M5 · **Priority:** medium · **Status:** ready
**Design:** [§7 High-Level Design](./trd.md#high-level-design), [§14 Rollback Strategy](./trd.md#rollback-strategy)

Move the 15 `general/` skills into the three kind-based groups and update every cross-reference so the dependency direction (orchestrators → lib, never the reverse) is visible.

**Tasks**
- Define the final group names and assign each `general/` skill to orchestrators, lib, or contracts.
- Move the skill directories and update Skill invocations, command docs, hook context, and script paths to the new locations.
- Run the full skill and eval suite against the new layout.

**Acceptance criteria**
- `general/` no longer exists; every skill lives under one of the three groups.
- No dangling reference to a moved skill remains in `skills/`, `commands/`, `agents/`, `hooks/`, or `scripts/`.
- The existing skill and eval suites pass against the new layout.

---

## EPIC-6 — Profile-ize brand and namespace

### EPIC-6-S1 — Move product name and namespace into a profile
**Milestone:** M6 · **Priority:** medium · **Status:** ready
**Design:** [§7 High-Level Design](./trd.md#high-level-design), [§3 Objective & Scope](./trd.md#objective-scope)

Replace the 203 `shield:` namespace literals and the embedded `Shield` product name with `{ns}` and `{product_name}` placeholders resolved from a single profile, generalizing `.shield.json` into that profile.

**Tasks**
- Define the profile fields (`product_name`, `ns`, config filename, `output_dir`) and resolution order.
- Replace `shield:` dispatch prefixes with `{ns}` and `Shield` product-name strings with `{product_name}` in engine prose.
- Generalize `.shield.json` into the profile and confirm load-time resolution.

**Acceptance criteria**
- No literal `shield:` prefix or hardcoded `Shield` product name remains in engine prose (`check_single_home.py` passes).
- Renaming the namespace in the profile changes exactly one home (blast-radius regression passes).
- The full eval suite passes with the default Shield profile.

### EPIC-6-S2 — Add the re-skin smoke test
**Milestone:** M6 · **Priority:** low · **Status:** ready
**Design:** [§9 Cross-Cutting Concerns](./trd.md#cross-cutting-concerns)

Add an eval that swaps in a throwaway `acme` profile, runs one orchestrator, and asserts no `shield`/`Shield` strings appear in the generated artifacts, proving the brand layer has exactly one home.

**Tasks**
- Create a throwaway `acme` profile + minimal contract fixtures.
- Run one orchestrator under the `acme` profile in the eval and capture its artifacts.
- Assert zero `shield`/`Shield` strings in the generated output.

**Acceptance criteria**
- The re-skin smoke eval runs an orchestrator under the `acme` profile and passes.
- Generated artifacts under the `acme` profile contain zero `shield`/`Shield` strings.
- The eval is registered in `evals/` and runs in CI.
