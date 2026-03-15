---
name: plan-docs
description: |
  Shield's planning skill — generates plan documents AND a JSON sidecar file.
  The sidecar is the machine-readable source of truth for stories, acceptance
  criteria, and status. It is required by /pm-sync, /implement (AC confirmation),
  and /review (AC verification). Use this skill instead of external planning
  plugins when the Shield pipeline is active.
  Triggers on: phase planning, ADR creation, detailed plan, story breakdown,
  infrastructure planning documents, /plan command.
---

# Plan Docs

Create planning artifacts for a project phase:
1. **Plan sidecar JSON** (`plan-sidecar.json`) — machine-readable source of truth
2. **Architecture/ADR document** (HTML) — the "why and how"
3. **Detailed execution plan** (HTML) — the "what to do", rendered from the sidecar

## Critical: Sidecar First

**Always generate the sidecar JSON first, then render HTML from it.** The sidecar is the source of truth — the HTML is a rendered view. When anything changes (AC edits, status updates, PM sync), the sidecar is updated and HTML is re-rendered.

## Plan Sidecar JSON

The sidecar MUST be written to the Shield run directory (`docs/tesseract/<run>/plan-sidecar.json`). The session-start hook injects the current run path — use it. It MUST conform to this structure:

```json
{
  "version": "1.0",
  "project": "<project name from .tesseract.json>",
  "phase": "<phase name>",
  "epics": [
    {
      "id": "EPIC-1",
      "name": "<epic name>",
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "<story name>",
          "status": "ready",
          "assignee": null,
          "priority": "high",
          "week": null,
          "description": "<2-3 sentences describing what needs to happen>",
          "tasks": [
            "Concrete action 1",
            "Concrete action 2"
          ],
          "acceptance_criteria": [
            "Verifiable outcome 1 (testable, not vague)",
            "Verifiable outcome 2"
          ],
          "pm_id": null,
          "pm_url": null
        }
      ]
    }
  ],
  "metadata": {
    "created_at": "<YYYY-MM-DD>",
    "domains": ["<from .tesseract.json>"],
    "reviewer_grades": {}
  }
}
```

**Sidecar rules:**
- Every epic MUST have at least 1 story
- Every story MUST have at least 1 acceptance criterion
- Acceptance criteria must be testable — not "it works" but "VPC has DNS support enabled"
- Tasks must be specific enough to execute without questions
- Status starts as `"ready"` for new stories
- `pm_id` and `pm_url` start as `null` — populated by `/pm-sync`

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
<meta name="sidecar" content="./plan-sidecar.json">
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

1. **Gather context** — ask about: problem being solved, existing infrastructure, proposed approach, dependencies, timeline
2. **Read `.tesseract.json`** — get project name and active domains
3. **Generate sidecar JSON first** — write `plan-sidecar.json` with epics, stories, tasks, and acceptance criteria
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
| Generating HTML without sidecar | Always write sidecar JSON first |
| Vague acceptance criteria | Testable: specific commands, measurable states |
| Missing acceptance criteria on stories | Every story MUST have at least 1 criterion |
| Empty tasks list | Every story needs concrete, actionable tasks |
| Not reading .tesseract.json | Project name and domains come from the marker |
