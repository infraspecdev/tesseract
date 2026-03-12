# clickup-sprint-planner Skills Evaluation (writing-skills checklist)

**Date:** 2026-03-12
**Evaluator:** writing-skills superpowers skill
**Skills evaluated:** 1

## Summary

| Skill | Words | Description CSO | Structure | Token Efficiency | Verdict |
|-------|-------|----------------|-----------|-----------------|---------|
| sprint-planning | 1248 | PASS | PARTIAL | FAIL (2.5x over) | Needs extraction |

---

## sprint-planning (1248 words)

### Frontmatter

- Name: `sprint-planning` — letters and hyphens only. PASS
- Description: `Use when the user asks about sprint planning, syncing plan docs to ClickUp, managing stories/tasks in bulk, or checking sprint status.` — starts with "Use when", includes specific triggers, no workflow summary. PASS

### CSO

- Keywords: sprint, sync, stories, ClickUp, bulk, epic, tasks, planning. PASS
- Naming: `sprint-planning` — gerund, descriptive. PASS
- Third person description. PASS

### Structure

- Overview: MISSING — jumps straight to tool table. Should have 1-2 sentence overview with core principle
- When to Use: MISSING — description covers triggers but the body lacks a "When to Use" section
- When NOT to Use: MISSING
- Tool reference table: PASS — clear quick reference for available tools
- Rules section (7 rules): PASS — clear, numbered, actionable
- Workflows (3): PASS — creating, updating, status check
- Card Content Requirements: PASS — detailed with example
- Common Mistakes: MISSING
- Flowchart: MISSING — workflows are shown as numbered lists, but the "sync before mutating" decision is non-obvious and would benefit from a flowchart

### Token Efficiency: FAIL

- 1248 words — 2.5x over the 500-word target
- **Card Content Requirements section**: ~350 words with full example card. This is heavy reference — extract to `card-format.md`
- **Card Ordering section**: ~200 words of reference. Extract to `card-format.md` or keep with card content
- **Custom Fields section**: ~100 words of reference. Extract
- **Workflow examples**: ~250 words. These are the skill's core value — keep inline but compress

### Specific Issues

**1. Missing Overview**
The skill opens with a tool table but never states its core principle. Add:
```
## Overview
Orchestrate ClickUp sprint operations through the sprint-planner MCP server — sync plan documents, create story cards in bulk, and track sprint progress.

**Core principle:** Always sync before mutating. Show the user the diff, get confirmation, then execute.
```

**2. Missing When to Use / When NOT to Use**
Should explicitly state:
- When to Use: sprint planning, syncing stories, bulk ClickUp operations
- When NOT to Use: individual task updates (use ClickUp UI), non-ClickUp project management, creating plan documents (use plan-docs skill instead)

**3. Example card is excellent but too large for SKILL.md**
The 20-line example card in "Card Content Requirements" is great reference but inflates the SKILL.md. Extract to `card-format.md` with the full example, required sections, optional sections, and ordering rules.

**4. No Common Mistakes section**
Obvious mistakes to document:
- Creating tasks one-by-one instead of bulk
- Not syncing before creating (duplicating existing tasks)
- Cards with one-line descriptions (mentioned in rules but not in a mistakes table)
- Hardcoding ClickUp IDs instead of reading from config
- Setting orderindex without gaps (can't insert later)

**5. Custom Fields section is low-value in SKILL.md**
"Not Yet Automated" fields are reference — move to a supporting file or append to `card-format.md`.

---

## Priority Recommendations

### P0 — Must Fix
1. **Extract card content/ordering/custom fields to `card-format.md`** — reduces SKILL.md by ~650 words (target: under 500)
2. **Add Overview section** with core principle

### P1 — Should Fix
3. **Add When to Use / When NOT to Use sections**
4. **Add Common Mistakes table** (5 mistakes identified above)
5. **Run Iron Law baseline test** — dispatch agent without skill to manage ClickUp tasks, document failures

### P2 — Nice to Have
6. **Add flowchart** for the sync-before-mutate decision flow
7. **Compress workflow examples** — the 3 workflows use similar patterns, could be more concise
