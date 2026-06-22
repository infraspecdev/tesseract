<!-- sidecar: ./plan.json -->

# Detailed Plan — Reduce skill change amplification

**Project:** Shield · **Phase:** Skills maintainability refactor · **Source:** [ADR 0002](../../adr/0002-reduce-skill-change-amplification.md) · [TRD](./trd.md)

> **In plain terms:** changing one fact in Shield's skills today means hand-editing it everywhere it was copied (up to 40 files for one path, 203 places to rename the plugin). This refactor gives each fact one home so the same change takes minutes in one file, with a CI guard that stops the copies creeping back. It also unlocks white-labeling Shield (M6).

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
| EPIC-1-S1 | Prototype the single-home pattern on the `review` orchestrator | M1 | high | ready |
| EPIC-1-S2 | Add the single-home guard eval (RED) | M1 | high | ready |
| EPIC-2-S1 | Remove inline docs/shield literals from prose | M2 | high | ready |
| EPIC-2-S2 | Refactor path-consuming scripts to read output-paths.yaml | M2 | high | ready |
| EPIC-2-S3 | Normalize the scripts root to $CLAUDE_PLUGIN_ROOT | M2 | high | ready |
| EPIC-3-S1 | Promote rubric dimensions and agent roster to schema | M3 | high | ready |
| EPIC-3-S2 | Convert plan-review and prd-review to iterate the roster | M3 | medium | ready |
| EPIC-4-S1 | Make the Step-Skeleton table the single home for steps | M4 | medium | ready |
| EPIC-5-S1 | Split general/ into orchestrators, lib, and contracts | M5 | medium | ready |
| EPIC-6-S1 | Move product name and namespace into a profile | M6 | medium | ready |
| EPIC-6-S2 | Add the re-skin smoke test | M6 | low | ready |

---

## EPIC-1 — Establish the single-home pattern and guardrails

### EPIC-1-S1 — Prototype the single-home pattern on the `review` orchestrator
**Milestone:** M1 · **Priority:** high · **Status:** ready
**Design:** [§7 High-Level Design](./trd.md#high-level-design), [§10 Milestones](./trd.md#milestones)

Convert the `review` orchestrator end-to-end to the single-home pattern: path nouns via registry name, dispatch driven by a roster, and verbs (script names) left inline. Prove the harness resolves the references at skill-load time (per §7's resolution mechanism) before rolling the pattern out. `review` was chosen because it exercises both path-noun resolution and roster-driven dispatch.

**Tasks**
- Inventory the `review` orchestrator's inline path literals, hand-typed lists, and step duplication.
- Replace inline `docs/shield` literals with registry names resolved from `output-paths.yaml` + `.shield.json` `output_dir`.
- Drive its reviewer/agent dispatch from a roster reference instead of a hand-typed list.
- Run the orchestrator in a dispatched subagent and confirm every reference resolves at load time with no dangling placeholder.

**Acceptance criteria**
- The `review` orchestrator contains zero inline `docs/shield` literals (grep returns nothing).
- Its dispatch list is sourced from a roster reference, not re-typed inline.
- A GREEN subagent run produces correct artifacts with all references resolved (no literal `{output_dir}` or `{ns}` left in output).

### EPIC-1-S2 — Add the single-home guard eval (RED)
**Milestone:** M1 · **Priority:** high · **Status:** ready
**Design:** [§5 Functional Requirements](./trd.md#functional-requirements), [§9 Cross-Cutting Concerns](./trd.md#cross-cutting-concerns)

Author `scripts/check_single_home.py` plus an eval that fails when any fact appears outside its home. It starts RED against today's tree and turns GREEN class-by-class as later stages land. CI substrate per §9: a new `.github/workflows/eval-skills-single-home.yml` invokes it and fails on non-zero exit.

**Tasks**
- Implement `check_single_home.py` covering: inline `docs/shield`, bare `shield/scripts/`, hand-typed dimension lists, literal `shield:` outside the profile, and steps restated in both table and body.
- Add the CI workflow (`.github/workflows/eval-skills-single-home.yml`, mirroring `eval-plan-trd.yml`) so a non-zero exit fails the build.
- Capture the current RED baseline (counts per violation class) as the regression starting point.

**Acceptance criteria**
- `check_single_home.py` exits non-zero on the current tree and prints a per-class violation count.
- The eval runs in CI via the new workflow and fails today (documented RED baseline).
- Each violation class can be queried independently so stages can flip them GREEN one at a time.

---

## EPIC-2 — Centralize path and script-root facts

### EPIC-2-S1 — Remove inline docs/shield literals from prose
**Milestone:** M2 · **Priority:** high · **Status:** ready
**Design:** [§5 Functional Requirements](./trd.md#functional-requirements), [§11 APIs Involved](./trd.md#apis-involved)

Delete the 29 inline `docs/shield` literals from skill and command prose, replacing each with the matching registry name + `{output_dir}` resolution. Pure prose sweep — the lower-risk half of the original story, separable from the script refactor (S2).

**Tasks**
- Replace every inline `docs/shield` literal in `skills/` and `commands/` with the matching registry name + `{output_dir}` resolution.
- Extend `check_single_home.py` to fail on any inline `docs/shield` literal in prose.

**Acceptance criteria**
- grep for `docs/shield` in `skills/` and `commands/` prose returns zero hits.
- `check_single_home.py`'s inline-path check passes.

### EPIC-2-S2 — Refactor path-consuming scripts to read output-paths.yaml
**Milestone:** M2 · **Priority:** high · **Status:** ready
**Design:** [§5 Functional Requirements](./trd.md#functional-requirements), [§11 APIs Involved](./trd.md#apis-involved)

Make the path-consuming Python scripts import filenames from `output-paths.yaml` instead of hardcoding them. This is the riskier code change (the scripts have their own tests) and the lever that collapses the 40-file `plan.json` blast radius. Scripts to refactor (from the measured set): `validate_plan.py`, `validate_trd.py`, `render_trd_section.py`, `migrate_outputs.py`, `backlog_store.py`, `run_step_5h.py`, `lld_blob_sha.py` — plus any other under `shield/scripts/` embedding an artifact filename literal.

**Tasks**
- Add a small path-resolver helper (or extend the existing one) that loads `output-paths.yaml` as the single source.
- Replace hardcoded `plan.json` / `research.md` / `trd.md` / `manifest.json` filename literals in each listed script with resolver calls.
- Add a blast-radius regression asserting a path rename in `output-paths.yaml` touches ≤3 files.
- Re-run each refactored script's existing test to confirm no behavior change.

**Acceptance criteria**
- No path-consuming script contains a hardcoded `plan.json` / `research.md` / `trd.md` filename literal; all resolve from `output-paths.yaml`.
- The blast-radius regression for a path rename passes at the ≤3-file ceiling.
- Every refactored script's existing test suite passes unchanged.

### EPIC-2-S3 — Normalize the scripts root to $CLAUDE_PLUGIN_ROOT
**Milestone:** M2 · **Priority:** high · **Status:** ready
**Design:** [§6 Non-Functional Requirements](./trd.md#non-functional-requirements)

Rewrite the 39 bare `shield/scripts/` references (across 15 files: `manifest-schema.md`, `mermaid-authoring.md`, `prd-docs/templates.md`, `lld-docs/SKILL.md`, `backlog/SKILL.md`, `implement-feature/SKILL.md`, `plan-docs/{sidecar-schema,trd-template,SKILL}.md`, `plan-review/{SKILL,scoring,dimensions}.md`, `devcontainer/SKILL.md`, `commands/init-devcontainer.md`, `commands/backlog.md`) to `$CLAUDE_PLUGIN_ROOT/scripts/`. The bare form is both restatement and a portability bug that only resolves when cwd is the repo root.

**Tasks**
- Rewrite each bare `shield/scripts/` reference in the 15 listed files to `$CLAUDE_PLUGIN_ROOT/scripts/<name>`.
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
- Consolidate `dimensions.md` and the `scoring.md` WEIGHTS table into `schema/rubric.yaml` (shape: `dim_id → {name, weight, severity}`).
- Build `schema/agents.yaml` mapping each reviewer agent slug to the dimensions it owns (shape: `slug → {owns: [dim_id…], weight}`).
- Add a one-line field example to each YAML file header so consumers see the shape inline.
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
- Re-run the evals (`uv run shield/evals/run.py plan-review-trd`, and `shield/evals/run-prd-review-merge-gate.sh`) to confirm identical grading behavior.

**Acceptance criteria**
- No hand-typed dimension or agent list remains in `plan-review` or `prd-review` prose (`check_single_home.py` passes).
- The named eval commands produce the same dimensions and dispatch set as before the change.
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

Move the 15 `general/` skills into three locked kind-based groups — **orchestrators/** (command-backed), **lib/** (reusable utilities), **contracts/** (doc-shape skills) — and update every cross-reference (~27 files reference `general/` today across skills, commands, agents, hooks, and scripts) so the dependency direction (orchestrators → lib, never the reverse) is visible. Highest-churn milestone; land it as one atomic commit (§14).

**Tasks**
- Assign each `general/` skill to orchestrators, lib, or contracts (names locked).
- Move the skill directories and update all ~27 cross-references (Skill invocations, command docs, hook context, script paths) to the new locations.
- Run the full eval suite (`shield/evals/run-evals.sh`) against the new layout.

**Acceptance criteria**
- `general/` no longer exists; every skill lives under orchestrators/, lib/, or contracts/.
- Zero dangling references to a moved skill remain (grep for `general/` across `skills/`, `commands/`, `agents/`, `hooks/`, `scripts/` returns zero hits).
- `shield/evals/run-evals.sh` passes against the new layout.

---

## EPIC-6 — Profile-ize brand and namespace

### EPIC-6-S1 — Move product name and namespace into a profile
**Milestone:** M6 · **Priority:** medium · **Status:** ready
**Design:** [§7 High-Level Design](./trd.md#high-level-design), [§3 Objective & Scope](./trd.md#objective-scope), [§11 APIs Involved](./trd.md#apis-involved)

Replace the 203 `shield:` namespace literals and the embedded `Shield` product name with `{ns}` and `{product_name}` placeholders resolved from the profile. **Decision (locked):** the profile is `.shield.json` generalized in place — add `product_name` + `ns` to the existing file; resolution order unchanged (cwd → parents). It is a superset of today's config, not a new file.

**Tasks**
- Add `product_name` + `ns` fields to `.shield.json` (resolution order unchanged); document the two new fields.
- Replace `shield:` dispatch prefixes with `{ns}` and `Shield` product-name strings with `{product_name}` in engine prose.
- Confirm load-time resolution of `{ns}`/`{product_name}` per the §7 resolution mechanism.
- Document the fallback: an unresolved placeholder fails fast with a named `missing_profile_field` error rather than emitting the literal placeholder.

**Acceptance criteria**
- No literal `shield:` prefix or hardcoded `Shield` product name remains in engine prose (`check_single_home.py` passes).
- `.shield.json` carries `product_name` + `ns`; renaming `ns` there changes exactly one home (blast-radius regression passes).
- An unresolved placeholder produces a named fail-fast error, not a literal `{ns}` in output.
- `shield/evals/run-evals.sh` passes with the default Shield profile.

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
- The eval is registered in CI and runs on PRs.
