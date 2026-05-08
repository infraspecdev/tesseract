# Shield SDLC Domain Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the backend domain plan series by adding generation-time skill awareness to `/plan` and `/implement`, and by registering `backend-reviewer` + `kubernetes-reviewer` in `/plan-review`'s persona auto-detect catalog.

**Architecture:** Three small markdown edits in existing shield files. The same `SKILL.md` body serves two roles depending on which command loads it: as **context** during generation phases (`/plan`, `/implement`) and as **checks** during review phases (`/plan-review`, `/review`). Plan 3 is the smallest of the four backend-domain plans — no new files, no Python, just instruction edits that change LLM behavior in three commands.

**Tech Stack:** Markdown only.

---

## Spec reference

This plan implements `docs/superpowers/specs/2026-05-08-shield-sdlc-domain-integration-design.md`. Read the spec first; this plan assumes its terminology (skills-as-context vs skills-as-checks, generation phases vs review phases).

## Scope of this plan (Plan 3)

**In scope:**
- `shield/commands/plan.md`: insert a generic domain-detection step
- `shield/skills/general/plan-review/personas.md`: add `backend-reviewer` and `kubernetes-reviewer` rows (both at weight 1.0)
- `shield/skills/general/implement-feature/SKILL.md` Phase 5c: extend hook to consult domain skills based on changed file type
- End-of-plan contract validation (subagent dispatch — same pattern as Plan 4 Task 9)
- Bump shield from `2.12.0` to `2.13.0` in `.claude-plugin/marketplace.json`

**Out of scope** (per the spec; see "Out of scope" section there for full list):
- Weight scheme rethink (keep 1.0/0.7 as-is; both new reviewers at 1.0)
- Programmatic auto-detect for `/plan` (LLM-instruction-driven for v1)
- Agent consultation mode for `/plan` (skills-as-context only)
- Phase 5c skill caching
- Per-project plan-review weight overrides

---

## File structure

**No new files.** Plan 3 only modifies existing files.

**Modified files:**

| File | Change |
|---|---|
| `shield/commands/plan.md` | Insert new "Domain detection" step (Step 8); renumber existing 8-14 → 9-15 |
| `shield/skills/general/plan-review/personas.md` | Add 2 rows to the agent weight table |
| `shield/skills/general/implement-feature/SKILL.md` | Replace Phase 5c body |
| `.claude-plugin/marketplace.json` | Bump shield: `2.12.0` → `2.13.0` |

---

## Conventions

- **All file paths absolute** from repo root: `/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/`.
- **Commits per task** unless a step says otherwise. Conventional Commits (`feat(shield):`, `chore(shield):`).
- **No automated tests for the markdown edits.** Verification = manual smoke tests + a contract-validation subagent dispatch at end of plan. Manual smoke tests are documented in each task's "Verification" section but not automated — LLM-behavior changes aren't unit-testable.

---

### Task 1: `/plan` domain-detection step

**Files:**
- Modify: `shield/commands/plan.md`

- [ ] **Step 1: Read the current file**

Read `shield/commands/plan.md` (53 lines). Locate the "## Behavior" section and confirm the existing numbered steps:

```
1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning
3. Read `output_dir` from `.shield.json` (default: `docs/shield`)
4. If `--name` not provided, derive from topic in kebab-case
5. Feature folder = `{plan-name}-YYYYMMDD`
6. Determine run number by counting existing folders in `{output_dir}/{feature}/plan/` + 1
7. Check for prior research: glob for `{project_root}/{output_dir}/{feature}/research/*/findings.md` and read the most recent one if it exists
8. **Generate `{feature}/plan.json` first** — ...
```

- [ ] **Step 2: Insert new Step 8 (Domain detection)**

After the existing step 7 (the "Check for prior research" line) and before the existing step 8 (the "Generate `{feature}/plan.json` first" line), INSERT this new content:

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

- [ ] **Step 3: Renumber the existing steps that follow**

The existing steps 8 through 14 must renumber to 9 through 15. Update each:

```
9. **Generate `{feature}/plan.json` first** — the sidecar JSON with epics, stories, tasks, and acceptance criteria. See the `shield:plan-docs` skill for the schema.
10. **Generate architecture HTML** — the "why and how" document
11. **Generate plan HTML** — stories rendered from the sidecar, includes `<meta name="sidecar" content="../plan.json">`
12. **Update `manifest.json`** in `{output_dir}/` and **regenerate `index.html`** — single dashboard linking to all artifacts
13. **You MUST produce all four artifacts and write them to the paths above.** No exceptions.
14. Verify the sidecar JSON contains at least 1 epic with stories, each with acceptance criteria
15. Offer next steps:
    - `/plan-review` — run multi-agent review on the plan
    - `/pm-sync` — sync stories to project management tool
```

- [ ] **Step 4: Verify with git diff**

```bash
git diff shield/commands/plan.md
```

Expected: a single contiguous insertion of the new Step 8, plus 7 number changes (8→9, 9→10, ..., 14→15) on the lines that follow. No other content changes.

- [ ] **Step 5: Commit**

```bash
git add shield/commands/plan.md
git commit -m "feat(shield): /plan loads domain skills as context for plan generation"
```

**Verification (manual, post-execution):** Once Plan 3 is implemented, run `/plan add user authentication` against the `shield/examples/spring-boot-api/` fixture (which has `pom.xml`). The generated plan's ACs should reference REST conventions, validation patterns, password hashing — content the LLM only knows about because it loaded the backend skills as context.

---

### Task 2: `/plan-review` persona registration

**Files:**
- Modify: `shield/skills/general/plan-review/personas.md`

- [ ] **Step 1: Read the current personas.md**

Read `shield/skills/general/plan-review/personas.md`. Locate the agent weight table at the top:

```markdown
| Agent | Weight | Focus |
|-------|--------|-------|
| `shield:architecture-reviewer` | 1.0 | Service topology, scalability, HA, network design |
| `shield:security-reviewer` | 1.0 | Security posture, threat modeling, access control, testability |
| `shield:dx-engineer-reviewer` | 1.0 | Plan clarity, actionability, software architecture |
| `shield:cost-reviewer` | 0.7 | Cost awareness, right-sizing, environment tiering |
| `shield:agile-coach-reviewer` | 0.7 | Sprint-readiness, story quality, dependencies |
| `shield:operations-reviewer` | 0.7 | Monitoring, failure modes, backup, on-call readiness |
| `shield:product-manager-reviewer` | 0.7 | User impact, scope discipline, prioritization, business value |
```

- [ ] **Step 2: Add the two new rows**

After the `shield:product-manager-reviewer` row (the last row in the existing table) and before the next markdown section, INSERT these two rows:

```markdown
| `shield:kubernetes-reviewer` | 1.0 | K8s manifests, Helm/Kustomize, RBAC, security, cost, operational readiness |
| `shield:backend-reviewer` | 1.0 | Backend application code (Java/Kotlin/Python/Node/Go), API design, database, testing, framework patterns |
```

The full table after this edit should have 9 rows (7 existing + 2 new).

- [ ] **Step 3: Verify with git diff**

```bash
git diff shield/skills/general/plan-review/personas.md
```

Expected: exactly 2 new rows added, no other changes.

- [ ] **Step 4: Verify the agents already declare trigger keywords**

The persona auto-detect logic counts trigger keyword matches per agent. Both agents must already have `## Trigger Keywords` sections in their respective files. Verify:

```bash
grep -A2 "## Trigger Keywords" shield/agents/backend-reviewer.md shield/agents/kubernetes-reviewer.md
```

Expected output: each file shows its trigger keywords. If either is missing, STOP — that's a Plan 1/2 bug requiring separate investigation.

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/plan-review/personas.md
git commit -m "feat(shield): register backend-reviewer + kubernetes-reviewer in plan-review personas"
```

**Verification (manual, post-execution):** Run `/plan-review` against a backend-flavored plan. The selection log should announce backend-reviewer was auto-included due to keyword matches. Same for kubernetes-reviewer with a K8s plan.

---

### Task 3: `/implement-feature` Phase 5c hook

**Files:**
- Modify: `shield/skills/general/implement-feature/SKILL.md`

- [ ] **Step 1: Read the current Phase 5c**

Read `shield/skills/general/implement-feature/SKILL.md`. Locate the "### 5c. Per-step lightweight review" section. The current content (lines 138-142):

```markdown
### 5c. Per-step lightweight review
After each step passes its test:
- Check for obvious issues (logic bugs, style, missing edge cases)
- If the active domain has a review skill (e.g., `terraform/review`), run domain-specific checks on the changed files
- This is NOT a full agent review — just quick correctness checks
```

- [ ] **Step 2: Replace Phase 5c with the extended version**

Replace the entire "### 5c. Per-step lightweight review" subsection (the heading line and the bulleted body that follows it, up to but not including "### 5d. Commit") with:

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

- [ ] **Step 3: Verify with git diff**

```bash
git diff shield/skills/general/implement-feature/SKILL.md
```

Expected: the Phase 5c block replaced; no other content changes.

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/implement-feature/SKILL.md
git commit -m "feat(shield): /implement Phase 5c consults domain skills for changed-file area"
```

**Verification (manual, post-execution):** Run `/implement` on a small backend story; verify Phase 5c quick-checks consult relevant backend skills (e.g., editing a controller → spring-web + api-design; editing a service → code-quality + concurrency).

---

### Task 4: End-of-plan contract validation

**Files:**
- (No file changes — validation step)

- [ ] **Step 1: Dispatch a contract-validation subagent**

Use the `Agent` tool with `subagent_type: general-purpose` and `model: opus`. Send this prompt:

```
You are validating shield's SDLC domain integration end-to-end (Plan 3 contract validation).

Working directory: /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/

Read the following files in full:
1. docs/superpowers/specs/2026-05-08-shield-sdlc-domain-integration-design.md (the spec)
2. shield/commands/plan.md (modified by Task 1)
3. shield/skills/general/plan-review/personas.md (modified by Task 2)
4. shield/skills/general/implement-feature/SKILL.md (modified by Task 3)
5. shield/agents/backend-reviewer.md (referenced by Task 2 — trigger keywords)
6. shield/agents/kubernetes-reviewer.md (referenced by Task 2 — trigger keywords)

Verify the following claims:

A. shield/commands/plan.md has a new "Domain detection" step in the Behavior section that:
  - Lists markers for backend (pom.xml/build.gradle*, pyproject.toml/requirements.txt, package.json, go.mod), terraform (*.tf, terraform.tfvars), kubernetes (Chart.yaml, kustomization.yaml, *.yaml with kind:/apiVersion:), and atmos (atmos.yaml)
  - Instructs the LLM to read shield/skills/<domain>/*/SKILL.md as CONTEXT
  - Notes that skills are NOT applied as gating checks (review-time, not generation-time)
  - Has a fallback for "no markers detected"

B. shield/skills/general/plan-review/personas.md has both:
  - shield:backend-reviewer at weight 1.0 with focus mentioning backend code, API design, database, testing
  - shield:kubernetes-reviewer at weight 1.0 with focus mentioning K8s manifests, Helm/Kustomize, RBAC

C. shield/skills/general/implement-feature/SKILL.md Phase 5c hook:
  - Lists 4 domain mappings (Terraform, Backend, Kubernetes, GitHub Actions) with file extensions and skill paths
  - Says "use the LLM's judgment to pick which skills are applicable" — no hard cap on skill count
  - Preserves the "NOT a full agent review" guidance

D. shield/agents/backend-reviewer.md and shield/agents/kubernetes-reviewer.md both have a "## Trigger Keywords" section. (This is a precondition for Task 2's persona registration to actually trigger auto-detection.)

E. The instruction edits are internally consistent:
  - The marker list in /plan Step 8 covers all 4 domains the spec mentions
  - The Phase 5c file extensions match the marker list (no orphan domains)

Report:
- Section-by-section: PASS or list specific contradictions/gaps
- Any issues that would cause the integration to misbehave
- Verdict: PASS / PARTIAL / FAIL

Do NOT modify code or docs. Just report findings.
```

- [ ] **Step 2: Address any issues**

If the validation reports gaps:
- Fix the relevant file(s)
- Re-run Step 1 until verdict is PASS

If verdict is PASS, no commit needed. Skip to Task 5.

If commits are needed:

```bash
git add <changed files>
git commit -m "fix(shield): refine SDLC domain integration based on contract validation"
```

---

### Task 5: Bump shield version

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read the current shield version**

Read `.claude-plugin/marketplace.json`. Confirm shield's `version` is `"2.12.0"` (set by Plan 4).

- [ ] **Step 2: Bump to 2.13.0**

Change shield's `version` from `"2.12.0"` to `"2.13.0"`. Per `CLAUDE.md`, the version lives only in `marketplace.json` — do NOT add a `version` field to `shield/.claude-plugin/plugin.json`.

- [ ] **Step 3: Verify**

```bash
git diff .claude-plugin/marketplace.json
```

Expected: single-line change in shield's version `"2.12.0"` → `"2.13.0"`.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.13.0 — SDLC domain integration (Plan 3)"
```

---

## Self-review checklist (run at end of plan execution)

- [ ] All 5 tasks committed
- [ ] `shield/commands/plan.md` has the new Step 8 with the marker list and skills-as-context guidance; existing steps renumbered to 9-15
- [ ] `shield/skills/general/plan-review/personas.md` shows 9 rows total (7 original + 2 new) with backend-reviewer and kubernetes-reviewer at weight 1.0
- [ ] `shield/skills/general/implement-feature/SKILL.md` Phase 5c block has the new domain mapping
- [ ] Contract validation (Task 4) reports PASS
- [ ] `.claude-plugin/marketplace.json` shows shield at `2.13.0`
- [ ] No file in this plan contains a TBD/TODO marker

## After Plan 3 ships

The backend domain plan series is complete:
- Plan 1: foundation (7 agnostic skills + agent + command + fixture) — merged
- Plan 2: Spring/JVM (6 framework skills + version-extensibility) — pushed
- Plan 4: SAST adapter integration (Semgrep + SonarQube + framework) — pushed
- Plan 3: SDLC integration (this plan) — closes the loop

Plan 5+ candidates from across the series:
- Python framework skills (FastAPI, Django, Flask) following Plan 2's pattern
- Node/TS framework skills following Plan 2's pattern
- Go framework skills
- SpotBugs / gitleaks / CodeQL adapters following Plan 4's pattern
- Spring Boot 2.x rule packs / sibling skills via `EXTENDING-VERSIONS.md`
- Kotlin-specific Semgrep rules and fixture coverage
- `recommended-rules.md` mapping if SAST adoption surfaces a need
- Weight scheme rethink (per-project `.shield.json` `plan_review.weights` config)
- Programmatic `/plan` domain auto-detect (move from LLM-instruction to deterministic pre-processor)
- Agent consultation mode for `/plan` (if skills-as-context yields plans of inadequate depth)
