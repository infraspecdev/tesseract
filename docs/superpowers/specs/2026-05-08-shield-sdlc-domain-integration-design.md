# Shield — SDLC Domain Integration Design

**Status:** Draft
**Date:** 2026-05-08
**Marketplace:** Tesseract
**Plugin:** Shield
**Target:** Plan 3 (closes the backend domain plan series after Plans 1, 2, 4)

## Context

Plans 1, 2, and 4 ship a complete backend review domain: 13 skills (7 agnostic + 6 Spring/JVM), the `backend-reviewer` agent, the `/review-backend` command, and SAST adapter integration. These cover **review-time** review and **post-hoc** quality checks well.

What's missing: the same backend skills should also inform **generation-time** SDLC commands — `/plan` and `/implement` — so backend principles shape *what gets planned* and *what gets written*, not just what gets caught after the fact. And the existing `/plan-review` command never registered the `backend-reviewer` (and `kubernetes-reviewer`) agents in its persona auto-detect catalog, so backend plans don't get specialized review.

Plan 3 closes these gaps. It's deliberately small — three markdown edits and a contract-validation step — but conceptually it's the "closing step" that ties the backend domain into shield's full SDLC pipeline.

## Goals

- `/plan` becomes domain-aware: detects markers, loads matching `shield/skills/<domain>/*/SKILL.md` as **context** when generating stories and acceptance criteria
- `/plan-review` auto-selects `backend-reviewer` and `kubernetes-reviewer` when plan content matches their trigger keywords
- `/implement-feature` Phase 5c per-step lightweight review consults relevant skills based on the changed file's domain
- The `/plan` fix is **generic** — works for backend, terraform, kubernetes, atmos, and future domains uniformly. No domain-specific code paths.
- Pre-existing gap: `kubernetes-reviewer` was added to the agents catalog in Plan 1 but never registered in `personas.md`. Plan 3 fixes this incidentally.

## Non-goals

- **Agent consultation during `/plan`.** Considered and rejected — too much complexity (5-7× LLM cost per `/plan` invocation, new "consult mode" semantics, parallel dispatch + aggregation) for marginal quality gain. Skills-as-context is the simpler v1.
- **Heavy AC templates per skill area.** Considered and rejected — bloats the command file, risks template staleness, reduces LLM judgment.
- **Programmatic auto-detect for `/plan`.** Domain detection happens within the LLM reading the command's instructions, not as a deterministic pre-processing step. Could move later if this proves unreliable.
- **Per-project weight overrides for plan-review reviewers.** The current weight scheme (1.0 / 0.7) is undocumented and arbitrary, but a rethink (with rationale + `.shield.json sast.weights` config) is out of scope for Plan 3. Backend and kubernetes reviewers ship at weight 1.0; broader weight redesign deferred.
- **Skill caching during Phase 5c.** If per-step domain checks slow TDD, add caching later. Not urgent.
- **Cross-domain monorepo orchestration.** When `/plan` detects multiple domains, the LLM reads skills from both — reasonable behavior, but not explicitly designed for plans spanning domains.

## Pipeline integration

Each SDLC phase uses skills with a different mechanism:

```
              SDLC PHASE             MECHANISM           SKILLS USED
              ──────────             ─────────           ──────────
/plan       → generation phase     → Claude reads        → as CONTEXT
                                     command + skills

/plan-review → review phase        → dispatches reviewer → applied as CHECKS
                                     agents (parallel)     by each agent

/implement   → generation phase    → Claude writes code  → as CONTEXT
              → per-step (5c)      → direct skill        → as quick CHECKS
                                     invocation

/review      → review phase        → dispatches reviewer → applied as CHECKS
                                     agents (parallel)
```

**The same SKILL.md body serves two roles:** Claude reads it during generation (context informing what to write) AND a reviewer agent reads it during review (rubric for what to check). The body doesn't change; the verb changes (`inform` vs `evaluate`).

**Plan 3 affects only the generation and pre-existing review-registration gaps.** Plans 1, 2, and 4 already covered the review side via `backend-reviewer`, `/review-backend`, `/review`, and SAST adapters.

## Component changes

### `shield/commands/plan.md` — domain-detection step

Insert a new step in the "Behavior" section between the existing "Check for prior research" (current step 7) and "Generate plan.json" (current step 8). The new step:

```markdown
8. **Domain detection.** Walk the project root for stack/domain markers:
   - `pom.xml` / `build.gradle*` → backend (Java/Kotlin)
   - `pyproject.toml` / `requirements.txt` → backend (Python)
   - `package.json` → backend (Node/TS)
   - `go.mod` → backend (Go)
   - `*.tf` / `terraform.tfvars` → terraform
   - `Chart.yaml` / `values.yaml` → kubernetes
   - `kustomization.yaml` → kubernetes
   - `*.yaml` with `kind:` and `apiVersion:` → kubernetes
   - `atmos.yaml` → atmos

   For each domain detected, read all `SKILL.md` files under `shield/skills/<domain>/` as **context** when generating stories and ACs. Skills inform what the plan should cover (API design conventions, test strategy, deployment safety, etc.) but are NOT applied as gating checks — that happens at /plan-review and /review.

   If no domain markers are found, generate a generic plan; the LLM uses its general knowledge.
```

(Existing steps 8–14 renumber to 9–15.)

The pattern is generic — it works for any domain that has skills under `shield/skills/<domain>/`. Future domains plug in by existing in that directory.

### `shield/skills/general/plan-review/personas.md` — register agents

Add two rows to the agent weight table:

```markdown
| `shield:kubernetes-reviewer` | 1.0 | K8s manifests, Helm/Kustomize, RBAC, security, cost, operational readiness |
| `shield:backend-reviewer` | 1.0 | Backend application code (Java/Kotlin/Python/Node/Go), API design, database, testing, framework patterns |
```

Both at weight 1.0 — when triggered, they're authoritative voices for their domain. Auto-detection then works because both agents already declare `## Trigger Keywords` in `shield/agents/{kubernetes,backend}-reviewer.md`. The plan-review skill's existing logic (count trigger keyword matches per agent → include if 2+) picks them up automatically.

The `kubernetes-reviewer` registration fixes a pre-existing Plan 1 gap (the agent shipped but was never added to the persona catalog).

### `shield/skills/general/implement-feature/SKILL.md` Phase 5c — extend the hook

Replace the current Phase 5c text (lines 138-142):

```markdown
### 5c. Per-step lightweight review
After each step passes its test:
- Check for obvious issues (logic bugs, style, missing edge cases)
- If the active domain has a review skill (e.g., `terraform/review`), run domain-specific checks on the changed files
- This is NOT a full agent review — just quick correctness checks
```

With:

```markdown
### 5c. Per-step lightweight review
After each step passes its test:
- Check for obvious issues (logic bugs, style, missing edge cases)
- For the changed file's domain, consult the relevant skill(s):
  - `*.tf` / `*.tfvars` → `shield/skills/terraform/*/SKILL.md`
  - `*.java` / `*.kt` / `*.py` / `*.ts` / `*.js` / `*.go` → `shield/skills/backend/*/SKILL.md`
  - `*.yaml` (K8s manifests) → `shield/skills/kubernetes/*/SKILL.md`
  - `.github/workflows/*.yml` → `shield/skills/github-actions/*/SKILL.md`
- Use the LLM's judgment to pick which skills are applicable to the file. Skip skills that don't apply (e.g., spring-security on a controller file).
- This is NOT a full agent review — keep it focused on what changed in this step. Don't run a comprehensive multi-skill audit; that happens at /review.
- If the file's domain has no matching skill, fall back to general code-quality judgment.
```

Removed the hard cap on number of skills; trusts LLM judgment to select what's applicable. Soft guidance ("lightweight," "focused on what changed") preserves the original intent.

## Test strategy

This plan touches three markdown files (no Python). Test strategy is verification-focused, not unit-test-focused. Validation patterns from Plans 1–2 (RED-GREEN with a fixture + oracle) don't fit because the changes affect LLM behavior (instruction-driven), not code that produces specific findings.

**For `/plan`:**
- Manual smoke test: run `/plan` against a backend project (the spring-boot-api fixture works). Verify the output references skill principles in ACs (e.g., a story for "create user endpoint" has ACs that mention REST conventions, validation, error response shape).
- Negative test: run `/plan` against a non-domain project (just a README, no markers). Verify a generic plan still generates without errors.
- Detect-but-no-skill case: e.g., Go marker present but `shield/skills/backend/go/` doesn't exist. Verify graceful fallback to agnostic backend skills.

**For `/plan-review`:**
- Manual smoke test: run `/plan-review` against a backend-flavored plan (mentions "API," "Spring," "service"). Verify backend-reviewer is auto-selected. Same for kubernetes-reviewer with a k8s plan.
- Negative test: irrelevant plan (UI-only) doesn't auto-select backend-reviewer.

**For `/implement-feature` Phase 5c:**
- Manual smoke test: implement a small backend feature; verify Phase 5c quick-check consults backend skills (not skipped, not running all 13).

**End-of-plan validation:**
- Dispatch a subagent to read all three modified files + this spec, verify cross-consistency:
  - `/plan` instructs generic domain detection with the marker list
  - `/plan-review` lists backend-reviewer and kubernetes-reviewer in `personas.md` at weight 1.0
  - `/implement-feature` Phase 5c references the four domain skill paths
- Mirrors Plan 4's Task 9 contract validation pattern.

## Versioning

Per `CLAUDE.md`:
- Bump shield in `.claude-plugin/marketplace.json` only — no `version` field added to `shield/.claude-plugin/plugin.json`.
- Plan 4 left shield at `2.12.0`. Plan 3 ships next: `2.13.0`.

## v1 deliverable summary

**Modified files:**

| File | Change |
|---|---|
| `shield/commands/plan.md` | Insert domain-detection step (Step 8) with marker list and skills-as-context guidance |
| `shield/skills/general/plan-review/personas.md` | Add 2 rows: `kubernetes-reviewer` (1.0) and `backend-reviewer` (1.0) |
| `shield/skills/general/implement-feature/SKILL.md` | Replace Phase 5c with domain-aware multi-domain skill consultation |
| `.claude-plugin/marketplace.json` | Bump shield from `2.12.0` to `2.13.0` |

**New files:** none.

**Estimated 4-5 tasks** in the implementation plan:
1. `/plan` domain-detection step
2. `/plan-review` persona registration (backend + kubernetes)
3. `/implement-feature` Phase 5c hook extension
4. End-of-plan contract validation (subagent dispatch)
5. Version bump

## Out of scope (deferred to follow-on plans)

- **Weight scheme rethink.** Add documented rationale and per-project configurability via `.shield.json` (e.g., `sast.weights` or `plan_review.weights`). Plan 5+.
- **Programmatic auto-detect for `/plan`.** Move domain detection from LLM-instruction to a deterministic pre-processing step that walks markers and outputs a structured domain list before the LLM generates.
- **Agent consultation mode for `/plan`.** Have reviewer agents weigh in on plan content during generation (not just review). 5-7× cost per `/plan`. Worth considering only if skills-as-context yields plans of inadequate depth.
- **`/plan` output validation.** No automated check that generated plans actually reflect skill principles. Quality is observed manually.
- **Phase 5c skill caching.** If running per-step domain checks slows TDD, cache loaded skill content per session.
- **AC templates per skill area.** Heavy prescriptive templates embedded in `plan.md` for each skill's concerns. Considered and rejected for v1.
- **Cross-domain monorepo orchestration.** Behavior is reasonable when `/plan` detects multiple domains (LLM reads skills from both), but not explicitly designed for plans spanning multiple domains.
