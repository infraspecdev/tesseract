---
name: plan-docs
description: Use when creating infrastructure planning documents — architecture/ADR docs and detailed execution plans with stories that sync to ClickUp. Triggers on mentions of phase planning, ADR creation, detailed plan, story breakdown, or infrastructure planning documents.
---

# Plan Docs

Create two-document planning artifacts for infrastructure phases: an **architecture/ADR** doc and a **detailed execution plan** with stories that become project management cards.

## Output Format

Default: **HTML**. User can request **Markdown** instead. Ask if not specified.

## When to Use

- Creating a new infrastructure phase or project milestone
- Breaking down a large initiative into executable stories
- Writing an ADR with a paired execution plan
- User mentions "phase plan", "detailed plan", "architecture doc", "story breakdown"

## Document Types

### 1. Architecture / ADR

The "why and how" — explains the problem, current state, proposed solution, and key decisions.

**Structure:**
1. **Nav bar** — links to overview, detailed plan, adjacent phases
2. **Phase heading** with timeline, month, dependencies
3. **Problem** — 1-2 paragraphs on what's broken or missing
4. **Context** — existing infrastructure table (Resource | Details | Status: Exists/To create), current state tables
5. **Solution** — approach paragraph, ASCII diagram in `<pre>`, "what changes" table, "what does NOT change" list
6. **Key insights** — in `<blockquote>` blocks (always blue `#1a73e8`, never phase-colored)
7. **Inter-service / integration impacts** — how this affects other systems
8. **Deliverables** — bullet list of concrete outputs
9. **Rollback strategy** — how to undo if things go wrong

### 2. Detailed Execution Plan

The "what to do" — stories that become ClickUp cards via sprint-planner sync.

**Structure:**
1. **Nav bar** — links to overview, architecture doc
2. **Phase heading** with week range and one-line summary
3. **EPIC metadata block** — ClickUp EPIC link (or `to create` badge), status, assignee, timeline
4. **Infrastructure section** — resource inventory table (Resource | ID/Value | Status)
5. **Stories summary table** — index, linked story name, ClickUp badge, status badge, assignee
6. **Story sections** — each story as a card-ready block (see Story Format below)
7. **Phase success criteria** — overall acceptance criteria in `.success-criteria` block

## Story Format

Each story MUST contain all sections needed to become a complete ClickUp card:

```
┌─ Story N: [descriptive name] ─────────────────────────┐
│  [ClickUp badge]  [Status badge]  [Week, Day range]   │
│                                                        │
│  Description paragraph (2-3 sentences, NO user story   │
│  format — just describe what needs to happen and why)  │
│                                                        │
│  Tasks (checklist)                                     │
│  - [ ] Concrete action with resource IDs where known   │
│  - [ ] Another action — specific enough to execute     │
│                                                        │
│  Existing Infrastructure (when relevant)               │
│  Resource | ID | Status: Exists / To create            │
│                                                        │
│  Acceptance Criteria (checklist)                       │
│  - [ ] Verifiable outcome (testable, not vague)        │
│  - [ ] Another verifiable outcome                      │
└────────────────────────────────────────────────────────┘
```

**Critical rules:**
- Story names: `Story 1: Name`, `Story 2: Name` — sequential numbers, NOT phase-prefixed
- Story divs: `id="story-N"` for anchor links from summary table
- Summary table story names: `<a href="#story-N">Name</a>` — clickable links
- Description: direct prose, NOT "As a... I want... so that..."
- Tasks: specific enough to execute without asking questions — include resource IDs, CIDR blocks, config values
- Acceptance criteria: testable commands or verifiable states, not "it works"
- No story points column in summary table
- No week grouping headers — stories listed flat, ordered by execution sequence
- Unset fields use `—` (em dash), not blank

## Badge System

| Badge Class | When to Use | Text |
|---|---|---|
| `badge-clickup` | Story linked to ClickUp | ClickUp task ID (as `<a>` link) |
| `badge-to-create` | No ClickUp card yet | `to create` |
| `badge-done` | Work completed | `done` |
| `badge-in-dev` | Actively being worked | `in dev` |
| `badge-ready` | Ready for development | `ready for dev` |

New stories always start with `badge-to-create` for ClickUp and `badge-ready` for status.

## EPIC Metadata Block

```html
<div class="epic-meta">
  <table>
    <tr><td>EPIC</td><td><span class="badge badge-to-create">to create</span> [EPIC] Project | Phase N: Name</td></tr>
    <tr><td>Status</td><td>&mdash;</td></tr>
    <tr><td>Assignee</td><td>&mdash;</td></tr>
    <tr><td>Timeline</td><td>Week N</td></tr>
  </table>
</div>
```

When ClickUp EPIC exists, replace the `to create` badge with a linked badge:
```html
<a href="https://app.clickup.com/t/{id}" class="badge badge-clickup">{id}</a>
```

## CSS & HTML Templates

See `templates.md` in this skill directory for the full CSS and HTML scaffolding for both document types. Use those templates exactly — do not invent new styles or change colors.

**Key style rules:**
- h1/blockquote accent: always `#1a73e8` (blue) — never use phase-specific colors for these
- Phase color only used in `.phase-color` CSS class for inline accents
- `max-width: 900px` for architecture, `960px` for detailed plan

## Markdown Alternative

When user requests markdown output:

**Architecture doc** — standard markdown with:
- `> **Key Insight:**` for blockquotes
- Pipe tables for resource inventories
- Fenced code blocks for ASCII diagrams

**Detailed plan** — markdown with:
- `[CU:{id}]` inline markers for ClickUp IDs (parseable by sprint-planner)
- `### Story N: Name` headers
- `- [ ]` checklists for tasks and acceptance criteria
- `> **EPIC:** ...` block for EPIC metadata

## Sprint Planner Integration

Documents generated by this skill are directly parseable by the `clickup-sprint-planner` plugin. The HTML structure matches the sprint-planner's `story_extraction` selectors:

| Selector | What It Matches |
|---|---|
| `div.story[id^='story-']` | Story section containers |
| `Story \d+: (.+)` | Story name from `<h3>` |
| `a.badge-clickup` | ClickUp task ID links |
| `.badge:not(.badge-clickup):not(.badge-to-create)` | Status badges |

**After generating documents**, register the new phase in `sprint-planner.json`:

```json
{
  "id": "P7",
  "name": "Observability Stack",
  "plan_doc": "07-observability-stack/detailed-plan.html",
  "epic_id": "..."
}
```

Then run `/sprint-sync P7` to create ClickUp cards from the stories. The sync tool will parse story names, descriptions, tasks, and acceptance criteria from the HTML and create cards with the full content.

## Workflow

1. **Gather context** — ask about: problem being solved, existing infrastructure, proposed approach, dependencies on other phases, timeline
2. **Generate architecture doc first** — the "thinking" document. Get user feedback.
3. **Generate detailed plan second** — break the solution into stories. Each story = one reviewable unit of work.
4. **Verify story quality** — every story must have enough detail to hand to an engineer who wasn't in the planning conversation
5. **Offer sprint-planner sync** — ask the user: *"Want me to add this phase to sprint-planner config and sync stories to ClickUp?"* If yes:
   - Find `sprint-planner.json` in the project (check `clickup-sprint-planner/examples/` or project root)
   - Add a new entry to `plan_docs.epics` with the phase ID, name, plan doc path, and `epic_id` (ask user for EPIC ID, or set to empty string if EPIC doesn't exist yet)
   - Invoke `/sprint-sync {phase_id}` to create ClickUp cards from the stories
   - Show the sync diff and confirm before creating cards
6. **Offer sprint planning** — after cards are created, ask: *"Want to assign stories and plan the sprint?"* If yes:
   - Invoke `/sprint-plan` to assign stories to team members, set priorities, and push updates to ClickUp
7. **Offer plan review** — after generating the detailed plan (or at any point if the user has an existing plan), ask: *"Want me to run a multi-persona review on this plan? I'll dispatch expert reviewers to score it and produce an enhanced version."* If yes:
   - Invoke `/plan-review <path-to-plan>` to dispatch 3-5 reviewer agents in parallel
   - Results go to `review/<date>-<slug>/analysis.md` (scored evaluation) and `plan.md` (enhanced plan)

## Common Mistakes

| Mistake | Fix |
|---|---|
| User story format ("As a...") | Direct description: "Create X to enable Y" |
| Vague acceptance criteria ("networking works") | Testable: "curl ifconfig.me returns 65.2.46.44" |
| Missing infrastructure section | Always include resource IDs and exists/to-create status |
| Phase-colored blockquotes | Blockquotes always use blue (#1a73e8) |
| Story names prefixed with phase ID | Use `Story 1:`, `Story 2:` — not `P1a-S1:` |
| Summary table without anchor links | Every story name links to `#story-N` |
| Invented CSS classes or colors | Use templates.md exactly |
