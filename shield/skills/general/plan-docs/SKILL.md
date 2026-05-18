---
name: plan-docs
description: Use when breaking down a project phase into stories with acceptance criteria, creating ADRs, or planning infrastructure work. Triggers on /plan, story breakdown, detailed plan, architecture doc.
---

# Plan Docs

**You MUST produce all four artifacts. No exceptions.**

## Output Paths — MANDATORY

Write each artifact using the Write tool to **exactly** these paths:

1. `{output_dir}/{feature-name}-YYYYMMDD/plan.json` — machine-readable plan sidecar at feature root (updated in place)
2. `{output_dir}/{feature-name}-YYYYMMDD/plan/{N}-{slug}/architecture.html` — the "why and how"
3. `{output_dir}/{feature-name}-YYYYMMDD/plan/{N}-{slug}/plan.html` — the "what to do", rendered from the sidecar
4. `{output_dir}/index.html` — dashboard linking to all features (create or update)

Where:
- `{output_dir}` — read from `.shield.json` `output_dir` field (default: `docs/shield`)
- `{feature-name}` — derived from plan name in kebab-case (e.g., `input-validation`, `auth-feature`). If user provides a name explicitly, use it.
- `{N}` — run number (count existing folders in `{feature}/plan/` + 1)
- `{slug}` — plan name

**Do NOT** use any other path, filename, or directory. The Write tool creates directories automatically. After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

## Critical: Sidecar First

**Always generate the sidecar JSON first, then render HTML from it.** The sidecar (`{output_dir}/{feature}/plan.json`) is the source of truth — the HTML is a rendered view. When anything changes (AC edits, status updates, PM sync), the sidecar is updated and HTML is re-rendered.

## Plan Sidecar JSON

The sidecar MUST be written to `{output_dir}/{feature}/plan.json`. See `sidecar-schema.md` for the full JSON schema and rules.

## When to Use

- Creating a new project phase or milestone
- Breaking down a large initiative into executable stories
- Writing an architecture decision record with a paired execution plan
- User mentions "phase plan", "detailed plan", "architecture doc", "story breakdown"
- Invoked by the `/plan` command

## When NOT to Use

- Pure research without implementation stories — use `/research` instead
- Reviewing an existing plan — use `/plan-review` instead
- Single task that doesn't need stories — just implement directly

## HTML Documents

After the sidecar is created, generate HTML documents that render from it.

### 1. Architecture / ADR

The "why and how" — explains the problem, current state, proposed solution, and key decisions.

**Structure:**
1. Phase heading with timeline
2. Problem — what's broken or missing
3. Context — existing infrastructure, current state
4. Solution — approach, diagrams, "what changes" table
5. Key decisions and trade-offs
6. Deliverables
7. Rollback strategy

### 2. Detailed Execution Plan

The "what to do" — stories rendered from the sidecar.

**Structure:**
1. Phase heading with summary
2. Epic metadata (name, status, timeline)
3. Stories summary table with status
4. Story sections — each rendered from the sidecar data

The HTML MUST include a meta tag referencing the sidecar:
```html
<meta name="sidecar" content="../plan.json">
```

### Story Format in HTML

Each story renders from the sidecar JSON:

```
┌─ Story N: [name from sidecar] ──────────────────────┐
│  [Status badge]  [Week range]                         │
│                                                       │
│  Description (from sidecar.description)              │
│                                                       │
│  Tasks (from sidecar.tasks)                          │
│  - [ ] Task 1                                        │
│  - [ ] Task 2                                        │
│                                                       │
│  Acceptance Criteria (from sidecar.acceptance_criteria)│
│  - [ ] Criterion 1                                   │
│  - [ ] Criterion 2                                   │
└───────────────────────────────────────────────────────┘
```

## CSS & HTML Templates

See `templates.md` in this skill directory for CSS and HTML scaffolding. Key rules:
- h1/blockquote accent: `#1a73e8` (blue)
- `max-width: 900px` for architecture, `960px` for detailed plan

## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Gather requirements | skip if spec/topic provided | No |
| 1a | Detect prior PRD in feature folder | skip if no PRD exists | No |
| 2 | Check for prior research / gather context | skip if no research exists | No |
| 2a | Milestone resolution — extract from PRD §15/§8 or invoke `shield:milestone-coverage` as fallback; user refines | always | Yes |
| 3 | Generate plan.json sidecar | always | Yes |
| 4 | Generate architecture HTML | always | Yes |
| 5 | Generate plan HTML | always | Yes |
| 6 | Update manifest + index.html | always | Yes |

## Workflow

1. **Load prior research** — check if any research exists in `{output_dir}/{feature}/research/`. If so, read the latest run's `findings.md` and use the research findings to inform the plan. If not, proceed without it.
1a. **Detect prior PRD in feature folder** — Glob `{output_dir}/{feature}/prd/*/prd.md` to find any prior PRDs. If multiple exist, pick the most recent (highest `{N}`). If found:
   - Read the PRD content
   - Read its `prd.meta.json` for type, sections_present, status
   - Treat the PRD as authoritative context for: Problem, Users, Goals, Stories, NFRs, Risks
   - Append the plan's run folder path to `prd.meta.json.linked_plans` (auto-updates the bidirectional linkage)
   - Record `source_prd` (relative path to prd.md) and `prd_rubric_version_at_planning` (read from prd.meta.json.rubric_version) into the plan.json sidecar
2. **Gather context** — ask about: problem being solved, existing infrastructure, proposed approach, dependencies, timeline

### 2a. Milestone resolution

Before generating stories, resolve milestones:

- **If a PRD was detected (Step 1a) and it contains milestones** (Section 15 standard, Section 8 lean): extract them. Present to the user for confirmation. Allow edits (rename, add exit criteria, change depends_on). Copy approved milestones into the sidecar `milestones[]`.

- **If a PRD was detected but has no milestones** (or an empty Milestones table — back-compat case for PRDs authored against rubric_version 1.0): invoke `shield:milestone-coverage` with:
   - `personas`: from PRD Section 4
   - `goals`: from PRD Section 6
   - `stories`: from PRD Section 8 (if present; empty for lean)
   - `feature_domain`: inferred or read from PRD type-detection metadata

   Present merged proposal + `open_conflicts` to the user (same flow as `/prd` §7a). User refines. Sidecar-only — do NOT write back to the PRD.

- **If no PRD exists:** invoke `shield:milestone-coverage` with whatever inputs were gathered during requirements (Step 2). Sidecar-only.

- **If the user explicitly opts out of milestones:** sidecar stores `milestones: []`. All subsequent stories will have `milestone_id: null`. This is the back-compat single-implicit-milestone case (see `sidecar-schema.md`).

3. **Read `.shield.json`** — get project name and active domains
4. **Generate sidecar JSON first (milestone-by-milestone)** — write `{output_dir}/{feature}/plan.json`:
   - For each milestone in `milestones[]` (resolved in §2a), generate the epics and stories needed to satisfy that milestone's exit criteria. Each story is born with `milestone_id` set to the milestone's `id`.
   - When `milestones: []` (opt-out case), generate stories flat with `milestone_id: null` on each — the back-compat path.
   - Acceptance criteria per story remain the same testable standard; exit criteria on the milestone are the higher-level rollup.
5. **Verify sidecar quality** — every story has tasks and testable acceptance criteria
6. **Generate architecture doc** (HTML) — the "thinking" document
7. **Generate detailed plan** (HTML) — renders stories from the sidecar, includes `<meta>` sidecar reference
8. **Invoke `shield:summarize`** — produce a plan summary for the run directory
9. **Offer next steps:**
   - `/plan-review` — multi-agent review of the plan
   - `/pm-sync` — sync stories to project management tool

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing only a markdown plan | You MUST produce all 3 artifacts: sidecar JSON + architecture.html + plan.html |
| Skipping HTML because "it's simpler" | HTML is required. Markdown is not a substitute. |
| Generating HTML without sidecar | Always write sidecar JSON first |
| Vague acceptance criteria | Testable: specific commands, measurable states |
| Missing acceptance criteria on stories | Every story MUST have at least 1 criterion |
| Empty tasks list | Every story needs concrete, actionable tasks |
| Not reading .shield.json | Project name and domains come from the marker |
| Writing to `shield/plan.json` (old path) | Write to `{output_dir}/{feature}/plan.json` — plan sidecar at feature root |
