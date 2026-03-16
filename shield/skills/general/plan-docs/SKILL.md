---
name: plan-docs
description: Use when breaking down a project phase into stories with acceptance criteria, creating ADRs, or planning infrastructure work. Triggers on /plan, story breakdown, detailed plan, architecture doc.
---

# Plan Docs

**You MUST produce all four artifacts. No exceptions.**

## Output Paths — MANDATORY

Write each artifact using the Write tool to **exactly** these paths:

1. `shield/docs/plans/<name>.json` — machine-readable named plan sidecar (updated in place, no timestamp)
2. `shield/docs/architecture-YYYYMMDD-HHMMSS.html` — the "why and how"
3. `shield/docs/plan-YYYYMMDD-HHMMSS.html` — the "what to do", rendered from the sidecar
4. `shield/docs/index.html` — overview page linking to all artifacts (created or updated)

Where `<name>` is derived from the planning topic in kebab-case (e.g., `input-validation`, `auth-feature`). If the user provides a name explicitly, use it.

Replace `YYYYMMDD-HHMMSS` with the current date and time.

**Do NOT** use any other path, filename, or directory. No `latest/`, no topic-based names, no custom filenames. The Write tool creates `shield/docs/` automatically.

## Critical: Sidecar First

**Always generate the sidecar JSON first, then render HTML from it.** The sidecar (`shield/docs/plans/<name>.json`) is the source of truth — the HTML is a rendered view. When anything changes (AC edits, status updates, PM sync), the sidecar is updated and HTML is re-rendered.

## Plan Sidecar JSON

The sidecar MUST be written to `shield/docs/plans/<name>.json`. See `sidecar-schema.md` for the full JSON schema and rules.

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
<meta name="sidecar" content="./plans/<name>.json">
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

## Workflow

1. **Load prior research** — check if any `shield/docs/research-*.md` files exist. If so, read the most recent one and use the research findings to inform the plan. If not, proceed without it.
2. **Gather context** — ask about: problem being solved, existing infrastructure, proposed approach, dependencies, timeline
3. **Read `.shield.json`** — get project name and active domains
3. **Generate sidecar JSON first** — write `plan.json` with epics, stories, tasks, and acceptance criteria
4. **Verify sidecar quality** — every story has tasks and testable acceptance criteria
5. **Generate architecture doc** (HTML) — the "thinking" document
6. **Generate detailed plan** (HTML) — renders stories from the sidecar, includes `<meta>` sidecar reference
7. **Invoke `shield:summarize`** — produce a plan summary for the run directory
8. **Offer next steps:**
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
| Writing to `shield/plan.json` (old path) | Write to `shield/docs/plans/<name>.json` — named plans, not single file |
