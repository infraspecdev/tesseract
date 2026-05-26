---
name: plan-docs
description: Use when breaking down a project phase into stories with acceptance criteria, creating ADRs, or planning infrastructure work. Triggers on /plan, story breakdown, detailed plan, architecture doc.
---

# Plan Docs

**You MUST produce all five artifacts. No exceptions.**

## Output Paths — MANDATORY

Write each artifact using the Write tool to **exactly** these paths:

| Registry key | Resolved path | Purpose |
|---|---|---|
| `plan_json` | `{output_dir}/{feature}/plan.json` | Machine-readable sidecar (source of truth for stories/tasks/ACs, PM-sync target) |
| `plan_arch_md` | `{output_dir}/{feature}/plan-architecture.md` | Canonical architecture markdown — the "why and how" |
| `plan_md` | `{output_dir}/{feature}/plan.md` | Canonical detailed-plan markdown — the "what to do" (narrative view of plan.json) |
| `plan_arch_html` | `{output_dir}/{feature}/outputs/plan-architecture.html` | Rendered architecture HTML (rendered from `{plan_arch_md}`) |
| `plan_html` | `{output_dir}/{feature}/outputs/plan.html` | Rendered detailed plan HTML (rendered from `{plan_md}`) |

The global dashboard `{output_dir}/index.html` is updated as a side effect of every run (cross-feature artifact, not a per-run deliverable).

Where:
- `{output_dir}` — read from `.shield.json` `output_dir` field (default: `docs/shield`)
- `{feature}` — `{feature-name}-YYYYMMDD`, derived from plan name in kebab-case (e.g., `input-validation-20260319`)

Numbered run subfolders (`plan/{N}-{slug}/`) are gone — each plan is a single canonical pair of markdown sources at feature root, with rendered HTML under `outputs/`. Re-running `/plan` on the same feature updates the same files (the plan.json sidecar is the source of truth and is updated in place).

**Do NOT** use any other path, filename, or directory. The Write tool creates directories automatically. After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

## Critical: Sidecar First, Markdown Second, HTML Last

**Always generate the sidecar JSON first, then the markdown sources, then render HTML.** The sidecar (`{plan_json}`) is the structured source of truth for stories/tasks/ACs (used by PM-sync and tooling). The markdown files (`{plan_md}`, `{plan_arch_md}`) are the human-readable narrative deliverables — `plan.md` is a markdown render of plan.json's stories with prose context, and `plan-architecture.md` is the hand-authored "why and how" document. The HTML files are rendered from the markdown via `scripts/render-markdown.sh` (the same helper `/prd` uses), so they share the strict CommonMark guarantees.

When anything changes (AC edits, status updates, PM sync), the sidecar is updated, the markdown is regenerated from the sidecar (plus preserved architecture prose), and the HTML is re-rendered.

## Plan Sidecar JSON

The sidecar MUST be written to `{plan_json}` = `{output_dir}/{feature}/plan.json`. See `sidecar-schema.md` for the full JSON schema and rules.

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

## Markdown Sources (canonical)

After the sidecar is created, generate the two markdown source files. These are the canonical, human-readable deliverables. HTML is rendered from them.

### 1. `{plan_arch_md}` — Architecture / ADR

The "why and how" — explains the problem, current state, proposed solution, and key decisions.

**Structure:**
1. Phase heading with timeline
2. Problem — what's broken or missing
3. Context — existing infrastructure, current state
4. Solution — approach, diagrams, "what changes" table
5. Key decisions and trade-offs
6. Deliverables
7. Rollback strategy

### 2. `{plan_md}` — Detailed Execution Plan

The "what to do" — stories rendered as markdown from the sidecar plus narrative context.

**Structure:**
1. Phase heading with summary
2. Epic metadata (name, status, timeline)
3. Stories summary table with status
4. Story sections — each rendered from the sidecar data (description, tasks, ACs)
5. A sidecar back-reference line at the top: `<!-- sidecar: ./plan.json -->`

## HTML Render

After the markdown sources are written, render both into `{output_dir}/{feature}/outputs/` using `render-markdown.sh` (the same helper `/prd` uses — strict CommonMark + plugins):

```bash
cd "{output_dir}/{feature}"
mkdir -p outputs

# Architecture
"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    plan-architecture.md \
  --shell plan-architecture.shell.html \
  --out   outputs/plan-architecture.html

# Detailed plan
"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    plan.md \
  --shell plan.shell.html \
  --out   outputs/plan.html
```

Each rendered HTML file MUST include a meta tag in its shell template that references the sidecar:
```html
<meta name="sidecar" content="../plan.json">
```

Delete the `.shell.html` files once the helper succeeds.

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
| 3 | Generate `{plan_json}` sidecar | always | Yes |
| 4 | Generate `{plan_arch_md}` (architecture markdown) | always | Yes |
| 5 | Generate `{plan_md}` (detailed plan markdown) | always | Yes |
| 6 | Render `{plan_arch_html}` and `{plan_html}` via render-markdown.sh | always | Yes |
| 7 | Update manifest + index.html | always | Yes |

## Workflow

1. **Load prior research** — read `{output_dir}/{feature}/research.md` (i.e. `{research}`) if it exists, and use the research findings to inform the plan. Falls back to `.session-transcript.md` only if `research.md` is absent. If neither exists, proceed without it.
1a. **Detect prior PRD in feature folder** — read `{output_dir}/{feature}/prd.md` (i.e. `{prd}`). If it exists:
   - Read the PRD content
   - Read its `prd.meta.json` for type, sections_present, status
   - Treat the PRD as authoritative context for: Problem, Users, Goals, Stories, NFRs, Risks
   - Append this plan's `{plan_md}` path to `prd.meta.json.linked_plans` (auto-updates the bidirectional linkage)
   - Record `source_prd` (relative path to prd.md) and `prd_rubric_version_at_planning` (read from prd.meta.json.rubric_version) into the `{plan_json}` sidecar
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
4. **Generate sidecar JSON first (milestone-by-milestone)** — write `{plan_json}`:
   - For each milestone in `milestones[]` (resolved in §2a), generate the epics and stories needed to satisfy that milestone's exit criteria. Each story is born with `milestone_id` set to the milestone's `id`.
   - When `milestones: []` (opt-out case), generate stories flat with `milestone_id: null` on each — the back-compat path.
   - Acceptance criteria per story remain the same testable standard; exit criteria on the milestone are the higher-level rollup.
5. **Verify sidecar quality** — every story has tasks and testable acceptance criteria
6. **Generate `{plan_arch_md}`** (architecture markdown) — the "thinking" document, hand-authored from gathered context + PRD + research
7. **Generate `{plan_md}`** (detailed plan markdown) — renders stories from the sidecar as markdown sections; includes a `<!-- sidecar: ./plan.json -->` reference at top
8. **Render HTML** — invoke `render-markdown.sh` per the "HTML Render" section above to produce `{plan_arch_html}` and `{plan_html}` under `{output_dir}/{feature}/outputs/`
9. **Invoke `shield:summarize`** — produce a plan summary
10. **Offer next steps:**
   - `/plan-review` — multi-agent review of the plan
   - `/pm-sync` — sync stories to project management tool

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing only the markdown without HTML render | You MUST produce all 5 artifacts: `{plan_json}` + `{plan_md}` + `{plan_arch_md}` + `{plan_html}` + `{plan_arch_html}` |
| Skipping HTML because "it's simpler" | HTML is required. Render from the markdown via `render-markdown.sh`. Hand-rendered HTML or pandoc/python-markdown output is NOT acceptable (same rules as `/prd`) |
| Generating markdown or HTML without the sidecar | Always write `{plan_json}` first; markdown is derived from it, HTML is derived from markdown |
| Writing under a numbered run folder (`plan/{N}-{slug}/`) | Numbered run subfolders are gone — write the markdown sources flat at `{output_dir}/{feature}/` and render HTML under `{output_dir}/{feature}/outputs/` |
| Vague acceptance criteria | Testable: specific commands, measurable states |
| Missing acceptance criteria on stories | Every story MUST have at least 1 criterion |
| Empty tasks list | Every story needs concrete, actionable tasks |
| Not reading .shield.json | Project name and domains come from the marker |
| Writing to `shield/plan.json` (old path) | Write to `{plan_json}` = `{output_dir}/{feature}/plan.json` — plan sidecar at feature root |
