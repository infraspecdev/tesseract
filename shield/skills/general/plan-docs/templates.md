# Plan Docs — HTML Templates

## Overview / Index Template

This page is written to `{output_dir}/index.html` (registry: `global_index_html`) and regenerated each time `{manifest}` is updated. It links to all features and their artifacts. See `manifest-schema.md` for the full link layout per feature (post-cutover flat paths under `{feature}/` and `{feature}/outputs/`).

> The HTML shell is now shared — see `shield/templates/shell.html` and `shield/templates/shield.css`. Skills render via `render-markdown.sh --shell $CLAUDE_PLUGIN_ROOT/templates/shell.html`. Do not inline HTML/CSS here.

The dashboard at `{output_dir}/index.html` is produced by `shield/templates/index.html` + `shield-dashboard.js`, which iterates `window.SHIELD_MANIFEST.features[]` client-side and emits one row per feature with links conditional on `artifacts.<key>` and `reviews.<type>.count > 0`. Refresh by running `uv run "$CLAUDE_PLUGIN_ROOT/scripts/write_shield_assets.py" --output-dir "{output_dir}"` after `manifest.json` updates.

## Architecture / ADR Template

> The HTML shell is now shared — see `shield/templates/shell.html` and `shield/templates/shield.css`. Skills render via `render-markdown.sh --shell $CLAUDE_PLUGIN_ROOT/templates/shell.html`. Do not inline HTML/CSS here.

The TRD (formerly `plan-architecture.md`) is authored as markdown per `trd-template.md` and rendered into the shared shell — see plan-docs/SKILL.md "HTML Render" for the exact invocation.

## Detailed Execution Plan Template

> The HTML shell is now shared — see `shield/templates/shell.html` and `shield/templates/shield.css`. Skills render via `render-markdown.sh --shell $CLAUDE_PLUGIN_ROOT/templates/shell.html`. Do not inline HTML/CSS here.

The detailed plan is authored as markdown (see the "Markdown Detailed Plan Template" below) and rendered into the shared shell. Story / milestone / epic blocks become markdown sections in `plan.md`; styling for cards, badges, and milestone rails lives in `shield/templates/shield.css`. See plan-docs/SKILL.md "HTML Render" for the exact invocation.

## Markdown Detailed Plan Template

```markdown
# Phase {N}: {Name} — Detailed Plan

**Week {X}** | {one-line summary}

> **EPIC:** `to create` — [EPIC] {Project} | Phase {N}: {Name}
> **Status:** —
> **Assignee:** —
> **Timeline:** Week {X}

## Infrastructure

| Resource | ID / Value | Status |
|---|---|---|
| {resource} | `{id}` {details} | Exists |
| {resource} | {description} | **To create** |

---

## Stories

| # | Story | ClickUp | Status | Assignee |
|---|---|---|---|---|
| 1 | [{Story name}](#story-1-story-name) | `to create` | ready for dev | — |

---

### Story 1: {Descriptive name}

`to create` · `ready for dev` · Week {X}, Day {Y}

{2-3 sentences describing what needs to happen and why.}

#### Tasks
- [ ] {Concrete action with resource IDs}
- [ ] {Another specific action}

#### Existing Infrastructure
| Resource | ID | Notes |
|---|---|---|
| {resource} | `{id}` | Exists |

#### Acceptance Criteria
- [ ] {Verifiable outcome}
- [ ] {Another verifiable outcome}

[CU:] <!-- ClickUp ID populated after sync -->

---

## Phase Success Criteria
- [ ] {Overall acceptance criterion}
```

## Markdown Architecture / ADR Template

```markdown
# Phase {N}: {Name}

**Timeline:** Week {X} ({duration}) | **Month {M}** | **Depends on:** {deps}

### Problem

{1-2 paragraphs on what's broken or missing}

### Context

**Existing Infrastructure:**

| Resource | Details | Status |
|---|---|---|
| {resource} | `{id}` {description} | Exists |
| {resource} | {description} | **To create** |

> **Key Insight:** {important context that affects the approach}

### Solution

**Approach:** {1-2 paragraphs describing the solution}

```
{ASCII architecture diagram}
```

**What changes:**

| Component | Action |
|---|---|
| {component} | {what happens} |

**What does NOT change:**
- {thing that stays the same}

### Deliverables
- {concrete output}

### Rollback Strategy

{How to undo if needed}
```
