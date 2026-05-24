# Shield Output Structure — Per-Asset Cutover (Phase 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut over every command, skill, and agent that writes files to declare its outputs via the central path registry (built in the foundations plan). After this plan lands, every emit-path in the codebase is a named registry reference, not a literal template duplicated across assets.

**Architecture:** Per-asset edits follow a single pattern: add an `outputs:` block to the asset's frontmatter listing the registry path names it emits, replace literal `{output_dir}/...` templates in the body with `{registry_name}` references (a `## Paths` section at the top of each body acts as a human-readable expansion), and add an eval that exercises the new behavior on a temp `output_dir`. The four command families ship as four independent PRs (Sections A–D). Reviewer subagents (Section E) share a single declaration shape since they all write to `review_detailed`.

**Tech Stack:** Markdown frontmatter (YAML), Python evals (`uv run --with pyyaml --with pytest pytest`), shield's existing eval harness in `shield/evals/`.

**Scope:** Phase 3 of design spec (`docs/superpowers/specs/2026-05-22-shield-output-structure-design.md`). Requires the foundations plan (`2026-05-22-shield-output-structure-foundations.md`) to be complete — i.e. `shield/schema/output-paths.yaml` and `shield/scripts/lint_output_paths.py` exist.

**Prerequisites:**
- Foundations plan merged.
- `uv run --with pyyaml shield/scripts/lint_output_paths.py --root .` exits 0 on current `main`.
- `legacy_*` registry entries still in place (will be removed in the Phase 5 cleanup plan).

**Out of scope:**
- Running `migrate_outputs.py --apply` on the live `docs/shield/` tree (Phase 4 plan).
- Removing `legacy_*` entries (Phase 5 plan).
- Editing files outside `shield/commands/`, `shield/skills/`, `shield/agents/`.

---

## Reference task (read first)

Sections A–E reuse this exact pattern per asset. Read it once here; section tasks call it by reference.

### Per-asset cutover pattern

**Files** (per asset):
- Modify: `shield/<dir>/<asset>.md` — the asset itself
- Create: `shield/evals/output-paths/<asset>-outputs.eval.md` — eval that verifies declared paths are written

- [ ] **Step 1: RED — write the failing eval**

Create `shield/evals/output-paths/<asset>-outputs.eval.md`. The eval invokes the asset against a sandboxed `output_dir = $TMPDIR/shield-eval-<n>`.

After running the command, the eval captures the full set of files written under `$output_dir` (e.g. via `find $output_dir -type f`). It then asserts:
  - Every declared output path is present.
  - No file is present that is not declared (the runner implicitly exempts derived globals and side-artifacts: `manifest.json`, `index.html`, anything under `outputs/`, and `changes.md`).

A command that silently writes to an undeclared path fails its eval. This is the load-bearing check against future registry drift — lint catches declaration errors, but only the eval catches the "command wrote files it didn't tell anyone about" case.

Run: `bash shield/evals/run-eval.sh shield/evals/output-paths/<asset>-outputs.eval.md`
Expected: FAIL — the asset still writes to legacy paths.

- [ ] **Step 2: Add the `outputs:` block to the asset's frontmatter**

Open `shield/<dir>/<asset>.md`. In the YAML frontmatter (top of file, between `---` lines), add or extend the `outputs:` key with the registry path names this asset writes (see family sections below for the exact list per asset). Example:

```yaml
---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories, plus a JSON sidecar for project management sync
outputs:
  - plan_json
  - plan_md
  - plan_arch_md
  - plan_html
  - plan_arch_html
---
```

- [ ] **Step 3: Insert a `## Paths` reference section at the top of the body**

Right after the frontmatter, before the existing body content, add:

```markdown
## Paths

This command writes the following registry-tracked paths (see `shield/schema/output-paths.yaml`):

- `{plan_json}` → `{output_dir}/{feature}/plan.json`
- `{plan_md}` → `{output_dir}/{feature}/plan.md`
- `{plan_arch_md}` → `{output_dir}/{feature}/plan-architecture.md`
- `{plan_html}` → `{output_dir}/{feature}/outputs/plan.html`
- `{plan_arch_html}` → `{output_dir}/{feature}/outputs/plan-architecture.html`
```

(Adjust the list and resolved literal templates to match what's in `outputs:`.)

This section lets a human or Claude resolve `{plan_md}` etc. by reading the file top-to-bottom; no external lookup needed at runtime.

- [ ] **Step 4: Replace literal path templates in the existing body with `{registry_name}` references**

Skim the asset body for occurrences of `{output_dir}/{feature}/...` and similar literal templates. For each, substitute the registry-name reference:

| Find | Replace with |
|---|---|
| `{output_dir}/{feature}/plan.json` | `` `{plan_json}` `` |
| `{output_dir}/{feature}/plan.md` | `` `{plan_md}` `` |
| `{output_dir}/{feature}/research/{N}-{slug}/findings.md` | `` `{research}` `` (note: numbered run goes away) |
| `{output_dir}/{feature}/plan-review/{N}-{slug}/summary.md` | `` `{review_summary}` `` with review_type=plan |
| `{output_dir}/{feature}/plan-review/{N}-{slug}/detailed/<agent>.md` | `` `{review_detailed}` `` |
| `{output_dir}/{feature}/plan/{N}-{slug}/architecture.html` | `` `{plan_arch_html}` `` |
| `{output_dir}/{feature}/plan/{N}-{slug}/plan.html` | `` `{plan_html}` `` |

(See the registry in `shield/schema/output-paths.yaml` for the full mapping.)

If the body has rendering or PM-sync workflow steps that historically wrote to numbered-run folders, rewrite them to write to the flat path. Numbered runs no longer exist in the new schema.

- [ ] **Step 5: GREEN — run the eval**

Run: `bash shield/evals/run-eval.sh shield/evals/output-paths/<asset>-outputs.eval.md`
Expected: PASS — the asset now writes to declared paths.

- [ ] **Step 6: Run lint**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0 — frontmatter is valid, registry is clean.

- [ ] **Step 7: Commit**

```bash
git add shield/<dir>/<asset>.md shield/evals/output-paths/<asset>-outputs.eval.md
git commit -m "feat(shield): cut over <asset> to path registry"
```

---

## Section A: Discovery family (research, prd, prd-review)

Three commands. Each follows the per-asset pattern above with these specifics:

### Task A1: Cut over `shield/commands/research.md`

**`outputs:`**
```yaml
outputs:
  - research
```

**Body substitutions:** historical research wrote to `{output_dir}/{feature}/research/{N}-{slug}/findings.md` (with a sibling `transcript.md`). The new contract is a single flat `{research}` file at `{output_dir}/{feature}/research.md`. Numbered subfolders are gone; session transcripts (if any) move to `{output_dir}/{feature}/.session-transcript.md` (hidden file at feature root, not declared in `outputs:` because it's a side-artifact, not a deliverable).

Follow the Reference task steps 1–7.

### Task A2: Cut over `shield/commands/prd.md`

**`outputs:`**
```yaml
outputs:
  - prd
  - prd_html
```

**Body substitutions:** historical prd.md wrote both `prd.md` and `prd.html` at feature root. New contract keeps the source `.md` at feature root (`{prd}`) and moves the rendered `.html` into `{feature}/outputs/` (`{prd_html}`). Update any "open in browser" or "share with stakeholders" notes to point at the new `{prd_html}` location.

Follow the Reference task steps 1–7.

### Task A3: Cut over `shield/commands/prd-review.md`

**`outputs:`**
```yaml
outputs:
  - review_summary    # review_type=prd
  - review_enhanced   # review_type=prd
  - review_summary_html
  - review_enhanced_html
```

**Body substitutions:** historical prd-review wrote to `{output_dir}/{feature}/prd-review/{N}-{slug}/`. New contract writes under `{output_dir}/{feature}/reviews/prd/{date}{_counter}/`. The command must compute `{date}` (today, ISO) and `{_counter}` (probe filesystem for existing `{date}*` folders, append `_2`, `_3`, ... as needed).

In the body, add a "Resolving the counter" callout near the start of the workflow:

> Before writing, list `{output_dir}/{feature}/reviews/prd/` for entries matching today's date. If `{date}/` does not exist, use `_counter=""`. Otherwise, find the highest `{date}_N/` and use `_counter="_<N+1>"`. Files are then written under `{review_dir}` resolved with these values.

Reviews never overwrite prior runs — they always create a new dated folder.

Follow the Reference task steps 1–7.

### Task A4: Section A integration check

- [ ] **Step 1: Run all discovery-family evals**

Run: `bash shield/evals/run-eval.sh shield/evals/output-paths/research-outputs.eval.md shield/evals/output-paths/prd-outputs.eval.md shield/evals/output-paths/prd-review-outputs.eval.md`
Expected: all PASS.

- [ ] **Step 2: Lint clean**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0.

- [ ] **Step 3: This is the PR boundary for Section A.** Push the three asset commits + three eval commits as one PR titled `feat(shield): cut over discovery family to path registry`.

---

## Section B: Planning family (plan, plan-review)

### Task B1: Cut over `shield/commands/plan.md`

**`outputs:`**
```yaml
outputs:
  - plan_json
  - plan_md
  - plan_arch_md
  - plan_html
  - plan_arch_html
```

**Body substitutions:** historical plan.md wrote phase-numbered architecture and detailed-plan HTML into `{output_dir}/{feature}/plan/{N}-{slug}/`. New contract is flat: one canonical `{plan_md}`, one `{plan_arch_md}`, one `{plan_json}` sidecar, plus their renders under `{feature_outputs}`. Architecture and detailed plan become separate source files (not a single `plan.md` with embedded sections), per design spec §4.

If the existing body iterates over phases and writes per-phase files, restructure to a single canonical plan with phases as `##` sections inside `{plan_md}`. Remove the per-phase numbered folders entirely.

Follow the Reference task steps 1–7.

### Task B2: Cut over `shield/commands/plan-review.md`

**`outputs:`**
```yaml
outputs:
  - review_summary    # review_type=plan
  - review_enhanced   # review_type=plan
  - review_detailed   # review_type=plan, multiple agents
  - review_summary_html
  - review_enhanced_html
  - review_detailed_html
```

**Body substitutions:** plan-review dispatches multiple reviewer subagents. The command itself writes `{review_summary}` and `{review_enhanced}`. Each subagent writes `{review_detailed}` with its own `{agent}` slug — that part is declared in the subagent's frontmatter (Section E), not in plan-review.md. In plan-review.md, the dispatch table should list which subagent writes which `{agent}` slug, e.g.:

> Subagents dispatched: `shield:backend-engineer`, `shield:security-engineer`, `shield:sre`, ... each writes `{review_detailed}` with `agent=<their slug>`.

Use the same `{_counter}` resolution as Task A3.

Follow the Reference task steps 1–7.

### Task B3: Section B integration check

- [ ] **Step 1: Run planning-family evals**

Run: `bash shield/evals/run-eval.sh shield/evals/output-paths/plan-outputs.eval.md shield/evals/output-paths/plan-review-outputs.eval.md`
Expected: all PASS.

- [ ] **Step 2: Lint clean**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0.

- [ ] **Step 3: PR boundary for Section B.** Title: `feat(shield): cut over planning family to path registry`.

---

## Section C: Code review family

Eight commands: `review`, `review-backend`, `review-cost`, `review-helm`, `review-k8s`, `review-security`, `review-well-architected`, `analyze-plan`.

All eight share the same `outputs:` shape — they emit a code-review run (review_type=code). The per-domain commands (`review-backend`, `review-security`, etc.) dispatch the corresponding `shield:<domain>` subagent which writes a `review_detailed` entry.

### Task C1: Cut over `shield/commands/review.md`

**`outputs:`**
```yaml
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, multiple agents
  - review_summary_html
  - review_detailed_html
```

**Body substitutions:** historical review.md wrote to `{output_dir}/{feature}/code-review/{N}-{slug}/`. New contract is `{output_dir}/{feature}/reviews/code/{date}{_counter}/`. Same counter resolution as prd-review (Task A3). No `enhanced-*` doc for code reviews (source code is outside `docs/shield/`).

Follow the Reference task steps 1–7.

### Task C2: Cut over each domain-specific review command

Apply the per-asset cutover pattern to each of:

- `shield/commands/review-backend.md`
- `shield/commands/review-cost.md`
- `shield/commands/review-helm.md`
- `shield/commands/review-k8s.md`
- `shield/commands/review-security.md`
- `shield/commands/review-well-architected.md`

Each writes:

```yaml
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, agent=<this command's domain>
  - review_summary_html
  - review_detailed_html
```

Each gets its own eval at `shield/evals/output-paths/<command-name>-outputs.eval.md`. Commit each cutover separately.

### Task C3: Cut over `shield/commands/analyze-plan.md`

`analyze-plan` analyzes Terraform plan output (not a Shield plan). Inspect the current command body to identify what files it writes today, then declare those paths in `outputs:`. If it writes a single findings document, expect:

```yaml
outputs:
  - review_summary    # review_type=code (treat Terraform-plan analysis as a code-review variant)
  - review_summary_html
```

If the command writes outside `docs/shield/` (e.g. directly into a Terraform working directory), it does NOT need an `outputs:` block — only paths inside `{output_dir}` are governed by the registry. In that case, add a comment in the frontmatter explaining the omission:

```yaml
# No outputs declared: analyze-plan writes findings into the user's Terraform
# working directory, which is outside the shield output_dir registry scope.
```

### Task C4: Section C integration check

- [ ] **Step 1: Run all review-family evals**

Run: `bash shield/evals/run-evals.sh shield/evals/output-paths/review*.eval.md`
Expected: all PASS.

- [ ] **Step 2: Lint clean**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0.

- [ ] **Step 3: PR boundary for Section C.** Title: `feat(shield): cut over code-review family to path registry`.

---

## Section D: Implementation, PM, config family

Six commands plus two skills. Inspect each before cutover; not every command writes inside `docs/shield/`.

### Task D1: Cut over `shield/commands/implement.md`

`implement` executes a plan task-by-task and updates plan status. It writes:

```yaml
outputs:
  - plan_json    # updated with story status
```

It does NOT write a fresh plan source — it mutates `{plan_json}` in place. The eval verifies that running implement against a fixture `plan_json` updates the story status field correctly without changing any other declared path.

Follow the Reference task steps 1–7.

### Task D2: Cut over `shield/commands/pm-sync.md`

`pm-sync` syncs stories to an external PM tool (ClickUp, Jira). It writes:

```yaml
outputs:
  - plan_json    # updated with PM tool IDs after sync
```

Same pattern as implement: in-place update of `{plan_json}`, no new files.

Follow the Reference task steps 1–7.

### Task D3: Cut over `shield/commands/init.md` and `shield/commands/migrate.md`

`init` creates `.shield.json` and gitignore patterns in the consumer repo. `migrate` runs the migration script and regenerates `manifest.json`. Both write **outside** `{output_dir}` (init writes to repo root; migrate writes `manifest.json`, which is tracked in the registry as `manifest`).

For `init.md`:

```yaml
# No outputs declared: init writes .shield.json and .gitignore at the repo
# root, which are outside the shield output_dir registry scope.
```

Body updates: replace any reference to legacy numbered-run gitignore patterns (e.g. `docs/shield/*/plan/*-*`) with the new flat-layout patterns. The new layout is committed (sources + outputs/), so gitignore should NOT exclude `outputs/` — instead it should exclude transient session files like `.session-transcript.md`.

For `migrate.md`:

```yaml
outputs:
  - manifest
```

Body updates: reference `{manifest}` instead of literal `docs/shield/manifest.json`.

Follow the Reference task steps 1–7 for each.

### Task D4: Cut over `shield/commands/pm-status.md`

Inspect first — if pm-status is read-only (just prints status from `{plan_json}` and the PM tool), no `outputs:` is needed. Add:

```yaml
# No outputs declared: pm-status is read-only.
```

If pm-status writes a status report file, declare its path (likely a new `pm_status_report` registry entry; add to `shield/schema/output-paths.yaml` first, then declare it here).

### Task D5: Cut over `shield/commands/init-devcontainer.md`

`init-devcontainer` writes `.devcontainer/` files in the consumer repo root — outside `{output_dir}`.

```yaml
# No outputs declared: init-devcontainer writes .devcontainer/ at the repo
# root, which is outside the shield output_dir registry scope.
```

Body: no path substitutions needed (writes happen outside the registry's scope).

### Task D6: Cut over `shield/skills/pm-sync/SKILL.md`

The skill helps a command sync to PM tools but typically doesn't directly own a registry path — it operates on `{plan_json}` via the calling command. Add:

```yaml
outputs:
  - plan_json    # mutated in place during sync
```

(Same shape as pm-sync.md command.)

Follow the Reference task steps 1–7.

### Task D7: Cut over `shield/skills/devcontainer/SKILL.md`

Writes `.devcontainer/` outside `{output_dir}`.

```yaml
# No outputs declared: writes .devcontainer/ at the repo root.
```

### Task D8: Section D integration check

- [ ] **Step 1: Run all D-family evals**

Run: `bash shield/evals/run-evals.sh shield/evals/output-paths/implement-outputs.eval.md shield/evals/output-paths/pm-sync-outputs.eval.md shield/evals/output-paths/migrate-outputs.eval.md`
(Skip evals for assets without declared outputs — they have no behavior to test.)
Expected: all PASS.

- [ ] **Step 2: Lint clean**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0.

- [ ] **Step 3: PR boundary for Section D.** Title: `feat(shield): cut over impl/PM/config family to path registry`.

---

## Section E: Reviewer subagents

Twenty-two agents in `shield/agents/`. The PM-dim graders (e.g. `user-impact-clarity.md`, `problem-solution-fit.md`, `scope-discipline-of-plan.md` — see `shield/agents/`) all write a single per-agent detail file when dispatched by a parent reviewer command. The non-grader agents (`research-framer.md`, `research-reviewer-narrative.md`, `agile-coach.md`, `architect.md`, etc.) need case-by-case inspection.

### Task E1: Cut over all reviewer subagents that write `review_detailed`

For each agent whose only output is a detail file:

```yaml
outputs:
  - review_detailed    # the dispatcher (plan-review / review / prd-review) supplies review_type and agent
```

Agents in this category (verify each in `shield/agents/` body):
- `adoption-rollout-risk.md`
- `business-value-alignment.md`
- `market-competitive-awareness.md`
- `prioritization-rationale.md`
- `problem-solution-fit.md`
- `reversibility-exit-cost.md`
- `scope-discipline-of-plan.md`
- `stakeholder-communicability.md`
- `success-metrics-defined.md`
- `user-impact-clarity.md`
- `framing-coverage-honored.md`
- `backend-engineer.md`
- `cloud-architect.md`
- `finops-analyst.md`
- `platform-engineer.md`
- `security-engineer.md`
- `sre.md`
- `agile-coach.md`
- `architect.md`
- `dx-engineer.md`

For each agent, follow the per-asset cutover pattern. The eval can be lighter than for commands — a single test that asserts the agent's body contains the `{review_detailed}` reference and frontmatter declares it.

To keep this section tractable, group the cutover commits by domain (e.g. one commit for all PM-dim graders, one for all engineering reviewers).

### Task E2: Cut over `shield/agents/research-framer.md` and `research-reviewer-narrative.md`

These write outputs in the research workflow. Inspect each agent body for the file paths it currently writes. Likely candidates:

- `research-framer.md`: writes a framing brief — historically under `research/{N}-{slug}/framing.md`. In the new layout, embed framing as a section inside `{research}` (no separate file). Declaration:

```yaml
# No outputs declared: research-framer contributes to the main {research}
# document owned by /research; it does not write its own file.
```

- `research-reviewer-narrative.md`: writes a narrative summary. Similarly, fold into `{research}` or declare a new registry entry (`research_narrative`) if a separate file is preferred. The latter requires adding the entry to `shield/schema/output-paths.yaml` first.

### Task E3: Section E integration check

- [ ] **Step 1: Run lint on the full repo**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0 across all 22 agents.

- [ ] **Step 2: PR boundary for Section E.** Title: `feat(shield): cut over reviewer subagents to path registry`. (Single PR is fine — agent changes are small and mechanical.)

---

## Section F: Final whole-repo verification

### Task F1: Whole-repo lint

- [ ] **Step 1: Lint clean**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0. Message: `Lint clean: registry + N assets` where N matches the count of `.md` files under `shield/commands/`, `shield/skills/`, `shield/agents/`.

- [ ] **Step 2: Count assets with `outputs:` declarations**

Run: `grep -lE "^outputs:" /Users/apple/projects/infraspecdev/tesseract/shield/commands/*.md /Users/apple/projects/infraspecdev/tesseract/shield/skills/*/SKILL.md /Users/apple/projects/infraspecdev/tesseract/shield/agents/*.md | wc -l`
Expected: every asset that writes inside `{output_dir}` has the block. Assets explicitly out of scope have a comment block instead (see D3, D5, D7, E2).

### Task F2: Run all evals

- [ ] **Step 1: Run the full eval suite under shield/evals/output-paths/**

Run: `bash shield/evals/run-evals.sh shield/evals/output-paths/*.eval.md`
Expected: all PASS.

### Task F3: Sanity-check the registry hasn't drifted

- [ ] **Step 1: Check registry name coverage**

Build a set of registry names actually referenced by at least one asset:

Run: `grep -hE "^\s*-\s+[a-z_]+\s*$" /Users/apple/projects/infraspecdev/tesseract/shield/commands/*.md /Users/apple/projects/infraspecdev/tesseract/shield/skills/*/SKILL.md /Users/apple/projects/infraspecdev/tesseract/shield/agents/*.md | sed 's/^\s*-\s*//' | sort -u`

Compare this list against `paths:` in `shield/schema/output-paths.yaml`. Every name in the registry that is NOT referenced by any asset is a candidate "dead declaration" — investigate before keeping it. (Exception: `legacy_*` entries should remain unreferenced until Phase 5.)

- [ ] **Step 2: No commit needed** — this is a verification step.

---

## Definition of Done

- [ ] Every command, skill, and agent that writes to `{output_dir}` has an `outputs:` frontmatter block listing registry path names.
- [ ] Every command, skill, and agent that writes OUTSIDE `{output_dir}` has a comment block in its frontmatter explaining the omission.
- [ ] Literal `{output_dir}/{feature}/...` templates are gone from asset bodies; references use `{registry_name}` form (or are inside a `## Paths` callout that maps them to their resolved literal form).
- [ ] Every cutover has eval coverage at `shield/evals/output-paths/<asset>-outputs.eval.md`.
- [ ] `uv run --with pyyaml shield/scripts/lint_output_paths.py --root .` exits 0.
- [ ] All evals under `shield/evals/output-paths/` pass.
- [ ] Five PRs landed (one per section A–E), each with eval coverage in the same PR per repo CLAUDE.md mandate.

---

## Follow-ups

- **Phase 4 plan** (`2026-05-22-shield-output-structure-live-migration.md`) — run `migrate_outputs.py --apply` against `docs/shield/`.
- **Phase 5 plan** (`2026-05-22-shield-output-structure-legacy-cleanup.md`) — remove `legacy_*` entries from the registry and migration script.
