<!-- sidecar: ../../../plan.json -->
<!-- enhanced by /plan-review on 2026-06-17 — review enhancements marked [R] -->

# Detailed Plan — Reduce skill change amplification (enhanced)

**Project:** Shield · **Phase:** Skills maintainability refactor · **Source:** [ADR 0002](../../../../adr/0002-reduce-skill-change-amplification.md) · [TRD](../../../trd.md)

> **[R] Executive summary (PM5):** Today, changing one fact in Shield's skills means hand-editing it everywhere it was copied — up to 40 files for a single path, and 203 places to rename the plugin. This refactor gives each fact one home so the same change takes minutes in one file, and a CI guard stops the copies from creeping back. Payoff: faster, safer maintenance and a path to white-labeling Shield. **[R] Business linkage (PM10):** the profile layer (M6) is what makes a re-skin/white-label deployment possible — track it as a capability, not just a smoke test.

Give each fact one home so a representative change touches ~1 file instead of 6–40. Six milestones, gated on a one-skill prototype, each shipping eval coverage.

> **[R] Adoption risk (PM7):** maintainers must learn the engine/contract/profile boundary and the verbs-inline / nouns-external rule, and may keep restating facts out of habit. Mitigation: a short convention note in CONTRIBUTING/CLAUDE.md plus `check_single_home.py` as the mechanical teaching backstop (it fails the PR and names the rule).

## [R] Tooling & CI substrate (DX7/DX12)

Concrete execution context assumed by every story (state once, here):
- **Runner:** `uv` (per CLAUDE.md — no system pip). Evals run via the existing `shield/evals/` harness.
- **Eval registration:** a new eval is added under `shield/evals/<area>/` following the existing fixture+expected pattern; "registered in CI" = picked up by the eval runner invoked in the repo's CI workflow.
- **CI hook:** `check_single_home.py` runs as a CI step that fails the build on non-zero exit. *(Name the exact workflow file + job during EPIC-1-S2.)*
- **`$CLAUDE_PLUGIN_ROOT`:** harness-provided at skill-load/run time; never hardcode the repo path. Scripts read it from the environment.

## [R] Resolution mechanism (CA7/CA9 — to confirm in TRD §7 during M1)

The keystone assumption is **how `{output_dir}` / `{ns}` / `{registry-name}` get substituted**. Intended mechanism to validate in M1: references are resolved **at skill-load/run time** by reading `.shield.json`/profile + the `schema/` contracts — not by a build step. M1's job is to confirm this works in a dispatched subagent; document the confirmed mechanism in §7 so the rest of the migration builds on a stated design, not a discovered one.

## Milestones

| ID | Milestone | Depends on |
|---|---|---|
| M1 | Pattern proven on one skill | — |
| M2 | Paths and script root have one home | M1 |
| M3 | Rubric and agent roster are data | M1 |
| M4 | Steps stated once per skill | M1 |
| M5 | Skills grouped by kind | M2, M3, M4 |
| M6 | Brand and namespace are a profile | M5 |

## Stories (with review enhancements)

### EPIC-1-S1 — Prototype the single-home pattern on the `review` orchestrator
Convert the **`review`** orchestrator end-to-end (path nouns via registry name, roster-driven dispatch, verbs inline). Prove load-time resolution before fan-out. *(Q3 resolved to `review` — exercises both path and roster resolution.)*

### EPIC-1-S2 — Add the single-home guard eval (RED)
Author `scripts/check_single_home.py` + register the eval; capture the RED baseline.
**[R]** Add a task: name the CI workflow file + job the guard hooks into, and how the eval is invoked there.

### EPIC-2-S1 — Route all path nouns through the registry
**[R] Split (AC1):** consider two stories — (a) remove the 29 inline `docs/shield` literals from prose; (b) refactor the path-consuming scripts to read `output-paths.yaml`. (b) is the riskier code change and is separately estimable.
**[R] Enumerate (DX3):** name the scripts to refactor — `validate_plan.py`, `render_trd_section.py`, `migrate_outputs.py`, `backlog_store.py`, plus any other that hardcodes an artifact filename (derive the full list from the ADR's measured 40-file set).

### EPIC-2-S2 — Normalize the scripts root to `$CLAUDE_PLUGIN_ROOT`
Rewrite the 39 bare `shield/scripts/` references → `$CLAUDE_PLUGIN_ROOT/scripts/`.
**[R] (DX3):** the 39 references span 15 files — list them in the story so the implementer doesn't re-derive the inventory.

### EPIC-3-S1 — Promote rubric dimensions and agent roster to schema
Create `schema/rubric.yaml` + `schema/agents.yaml`.
**[R] (DX10):** include a one-line YAML field example for each (`rubric.yaml`: `dim → {weight, severity}`; `agents.yaml`: `slug → [owned dimensions]`).

### EPIC-3-S2 — Convert plan-review and prd-review to iterate the roster
**[R] (AC6):** name the verification command — the existing `plan-review`/`prd-review` evals (cite the exact runner invocation) must produce an identical dimension + dispatch set.

### EPIC-4-S1 — Make the Step-Skeleton table the single home for steps
Collapse table/body duplication across orchestrators; add the step-duplication check to the guard.

### EPIC-5-S1 — Split general/ into orchestrators, lib, and contracts
**[R] Quantify (AC9/DX3):** measure and cite the cross-reference surface (N references across skills/commands/agents/hooks/scripts) the way other stories cite 29/39/203 — M5 is the highest-churn step; an unmeasured count is the weakest estimation input.
**[R] (AC6):** name the exact "full skill and eval suite" command used to confirm the new layout.

### EPIC-6-S1 — Move product name and namespace into a profile
Replace 203 `shield:` literals + `Shield` name with `{ns}` / `{product_name}`.
**[R] (CA8 / open Q#2):** before kickoff, resolve the profile filename + resolution order, and state in §7/§11 what a "profile" is relative to today's `.shield.json` (superset vs rename vs new layer).
**[R] (DX13):** document a fallback if the harness can't resolve a placeholder at load time, beyond "revert and revisit."

### EPIC-6-S2 — Add the re-skin smoke test
Swap in a throwaway `acme` profile; assert zero `shield`/`Shield` strings in generated artifacts.

## [R] Optional: milestone diagrams (CA9)
Either add a per-milestone Mermaid `diagram` (the engine/contract/profile delta each milestone delivers) to `plan.json` `milestones[]`, or bump the sidecar to 1.6 and let `validate_plan.py` enforce `milestone_no_diagram`. Shipping at 1.5 currently relies on the grandfather clause.

---

*Full per-story tasks and acceptance criteria are unchanged from [plan.md](../../../plan.md); this enhanced copy adds the `[R]`-marked review items. Apply selectively — none are blocking (verdict: Ready).*
