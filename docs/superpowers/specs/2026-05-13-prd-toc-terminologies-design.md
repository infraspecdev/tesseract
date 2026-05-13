# PRD scaffolds: Table of Contents + Terminologies section

**Date:** 2026-05-13
**Owner:** @ashwinimanoj
**Status:** Draft
**Scope:** shield plugin — PRD authoring (`/prd`), PRD scaffolds, HTML renderer

## Problem

Shield's PRD scaffolds (standard 18-section, lean 7-section) lack two affordances readers of long PRDs expect:

1. **No navigation aid** — the rendered `prd.html` is a flat scroll. Reviewers can't jump to a section without scanning, and there's no spatial cue for how long the document is.
2. **No glossary** — PRDs introduce domain terms (acronyms, internal product names, role names) without a single place to define them. Reviewers either guess from context or scroll back to find the first usage.

Both gaps hurt review velocity. The fix is small and self-contained: add an auto-generated Table of Contents to the HTML output and a Terminologies section to the markdown scaffold.

## Goals

1. Every PRD authored via `/prd` after this change has a Terminologies section as Section 2 (right after Header) in both the standard and lean scaffolds.
2. Every `prd.html` rendered after this change displays a Table of Contents block linking to every h2 (and nested h3) heading, sourced automatically from the markdown — no manual TOC maintenance.
3. The Terminologies section is auto-populated when possible: pulled from any prior `/research` transcript's glossary, then enriched at the end of the walk by a Claude pass that scans the drafted PRD body for domain terms. The user confirms / edits the final table before the artifacts are written.

## Non-goals

- **No retroactive backfill** of existing `prd.md` files in this or customer repos. Existing PRDs stay as-is. Re-running `/prd` in a folder with an existing PRD creates a new `{N+1}-{slug}/` run using the new scaffold (this matches existing behavior).
- **No re-render of existing `prd.html`** files. The TOC only appears in HTML rendered after this change lands.
- **No new skill** for Terminologies authoring or term extraction — the behavior lives inside the existing `prd-docs` skill.
- **No TOC inside `prd.md`.** Markdown stays clean; TOC is HTML-only and produced at render time.
- **No sticky-sidebar / collapsible TOC.** The TOC is a static block under the meta-banner. (Future enhancement if reviewers ask.)

## Design

### Markdown scaffold changes

**Standard** grows from 18 → 19 sections. **Lean** grows from 7 → 8. Everything past the new Section 2 shifts by +1.

```
Standard                            Lean
─────────                           ─────
1. Header                           1. Header
2. Terminologies     ← NEW          2. Terminologies   ← NEW
3. Problem & context (was 2)        3. Problem & context (was 2)
4. Target users / personas (was 3)  4. Target users / personas (was 3)
5. Goals & non-goals (was 4)        5. Goals & non-goals (was 4)
6. Success metrics (was 5)          6. Success metrics (was 5)
7. User stories & scenarios (was 6) 7. Open questions (was 6)
8. Functional requirements (was 7)  8. Out of scope (was 7)
9. Non-functional requirements (was 8)
10. RBAC & permissions matrix (was 9)
11. Dependencies (was 10)
12. Risks & mitigations (was 11)
13. Assumptions (was 12)
14. Rollout plan (was 13)
15. Cost & resource impact (was 14)
16. GTM & customer-comms (was 15)
17. Support / CX impact (was 16)
18. Open questions (was 17)
19. Out of scope / Non-goals (was 18)
```

**Terminologies section template** (identical in standard and lean):

```markdown
## 2. Terminologies
| Term | Definition |
|---|---|
| <term> | <one-line definition; link to deeper doc if needed> |
```

### Walk order (in `prd-docs` SKILL.md)

```
1. Walk Header (Section 1)
2. Defer Terminologies (Section 2) — write empty placeholder, fill at end
3. Pre-populate Problem (3), Personas (4), Dependencies (11) from research transcript if present
4. Walk Sections 3, 4, 5
5. Invoke shield:story-coverage between Sections 5 and 7 (was 4 and 6)
6. Walk Section 6 (Success metrics)
7. Walk Section 7 (User stories, scaffolded by step 5) and 8..19 in order
8. NEW STEP — terminologies-build:
   a. If research transcript has a Glossary / Terminology / Terms section,
      copy rows into the Terminologies table.
   b. Scan the drafted PRD body (Sections 3..19) for domain terms,
      acronyms, product / role names. Propose 5–15 rows with one-line
      definitions. Merge with (a), deduplicating by term.
   c. Present to user as an editable table. User can add, remove, edit,
      or accept all. Default: accept all.
   d. Substitute the final table into Section 2.
9. Write prd.md, prd.html, prd.meta.json (unchanged)
```

For lean PRDs, step 5 is skipped (no story-coverage); step 8 still runs.

### TOC generation (Approach A — server-side in `render-markdown.py`)

The renderer already enables `anchors_plugin` from `mdit-py-plugins` (see `render-markdown.py:40`). Anchor ids are already produced for every heading. The change:

1. **Walk the token stream after parsing.** Collect every `heading_open` token at levels 2–3 along with its rendered text and the anchor id emitted by `anchors_plugin`. Skip level 1 (the document title).
2. **Build TOC HTML.** Top-level `<nav class="toc">` containing a `<ul>` of h2 items; each h2 `<li>` may contain a nested `<ul>` of h3s.
3. **Substitute into the shell.** The shell file (`prd.shell.html`) gets a new `{{TOC}}` placeholder positioned directly below the meta-banner. The script replaces `{{TOC}}` with the built HTML and `{{BODY}}` with the body as today.
4. **Backwards compat.** If the shell does not contain `{{TOC}}`, the renderer silently skips TOC substitution (no error). Non-PRD shells that use this renderer keep working unchanged.

#### Why server-side and not client-side JS

The HTML must be useful when emailed, printed, or opened with JS disabled. Reviewers paste PRDs into PDFs and ticket tools. A JS-driven TOC would render blank in those contexts. Anchors already exist in the rendered HTML, so the work is bounded.

#### CSS for the TOC

Added to the shell template in `templates.md`:

```css
.toc {
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 32px;
  font-size: 0.94rem;
}
.toc-title { font-weight: 600; color: var(--text); margin-bottom: 8px; }
.toc ul { margin: 0; padding-left: 20px; list-style: decimal; }
.toc ul ul { list-style: disc; }
.toc li { margin: 2px 0; }
.toc a { color: var(--accent); text-decoration: none; }
.toc a:hover { text-decoration: underline; }
```

The block's visual:

```
┌─ meta-banner ────────────────────────────────────┐
│ PRD · Feature · Standard · Owner · 2026-05-13    │
└──────────────────────────────────────────────────┘
┌─ Contents ───────────────────────────────────────┐
│ 1. Header                                        │
│ 2. Terminologies                                 │
│ 3. Problem & context                             │
│ 4. Target users / personas                       │
│ 5. Goals & non-goals                             │
│   • Goals                                        │
│   • Non-goals                                    │
│ …                                                │
│ 19. Out of scope / Non-goals                     │
└──────────────────────────────────────────────────┘
[ rendered body starts here ]
```

### Auto-fill behavior for Terminologies (step 8 detail)

**Source A — research transcript glossary (deterministic).** Look in `{output_dir}/{feature}/research/*/transcript.md` (or `findings.md`) for any `## Glossary`, `## Terminology`, or `## Terms` section. If found, parse the table or bullet list and seed those rows into the Terminologies table.

**Source B — LLM scan of drafted PRD body (proposed).** After all other sections are walked, Claude scans Sections 3..19 and proposes terms that meet at least one of:
- ALL-CAPS acronyms used 2+ times (e.g., "SLA", "RBAC")
- Capitalized multi-word phrases used as named concepts (e.g., "Sign-off Contact", "Kill-switch")
- Domain nouns referenced in personas, NFRs, or dependencies without a prior definition
- Internal product or service names referenced in Dependencies / GTM / Rollout sections

Claude proposes one-line definitions, prefers terminology used in the PRD's own prose, and links to source paths from the research transcript when the term originates there.

**Merge.** Source A rows take precedence on conflict (research-sourced definitions are usually more authoritative). Source B rows are appended after deduplicating by term (case-insensitive).

**User confirmation.** Present the merged table to the user with: accept all, edit individual rows, add rows, remove rows. Default action on enter / silence: accept all.

### Files changed

| File | Change |
|---|---|
| `shield/skills/general/prd-docs/templates.md` | Rewrite both scaffolds with new numbering; add Terminologies section template; add `{{TOC}}` placeholder + TOC CSS to the HTML shell template. Update Section-6 → Section-7 reference in the story template note. Update lean's "intentionally omits" list to new numbers. Update doc copy "17-section" → "19-section", "7-section" → "8-section". |
| `shield/skills/general/prd-docs/SKILL.md` | Update walk order (defer Section 2, add step 8 terminologies-build, renumber walk references); update upgrade-flow multi-select to new numbers; update "Sections 1-4" → "1-5"; update story-coverage trigger references "Section 3/4/6" → "Section 4/5/7"; update Common Mistakes references; update See-Also reference counts. Update frontmatter description. |
| `shield/skills/general/prd-docs/meta-schema.md` | Update `sections_present` example `[1..18]` → `[1..19]`; "all 17 sections" → "all 19 sections"; lean 7 → 8. |
| `shield/skills/general/prd-docs/type-detection.md` | Add "Terminologies" to lean section list (now 8 sections); update load-bearing standard-only range — these are sections 7..17 in the new numbering (Stories through Support; Terminologies, Open questions, and Out of scope are in both lean and standard). Update the "12 of 18" threshold proportionally for the 19-section count; the implementer should pick a threshold consistent with the new load-bearing count. |
| `shield/skills/general/prd-docs/test-fixtures/new-from-scratch-expected.md` | Regenerate fixture with new numbering + Terminologies section populated with a couple of sample rows; update expectation comments. |
| `shield/skills/general/prd-docs/test-fixtures/with-research-transcript-expected.md` | Regenerate with new numbering; show Terminologies pre-populated from a transcript glossary section in the fixture. |
| `shield/skills/general/prd-docs/test-fixtures/lean-upgrade-prior-prd.md` | Update note "Sections 6-15" → new range; add Terminologies to expected upgrade. |
| `shield/skills/general/prd-review/personas.md` | "PRD's Section 6" → "PRD's Section 7" (story-coverage gap reference). |
| `shield/commands/prd.md` | Update frontmatter description: "17-section" → "19-section", "7-section" → "8-section"; update walk order summary "Sections 1-4" → "1-5"; update story-coverage trigger reference. |
| `shield/scripts/render-markdown.py` | Implement TOC token-walk; add `{{TOC}}` placeholder substitution; tolerate missing `{{TOC}}` in shell. |
| `shield/scripts/test_render_markdown_toc.py` | NEW — unit test for TOC generation. |
| `.claude-plugin/marketplace.json` | Bump shield plugin version (per CLAUDE.md: version lives ONLY here for relative-path plugins). |

### Testing

Per CLAUDE.md, RED-GREEN testing is mandatory for skill changes:

1. **Renderer unit test** (`test_render_markdown_toc.py`):
   - Fixture: markdown with `## 1. Header`, `## 2. Terminologies`, `## 3. Problem`, `### Sub-heading` and a shell with both `{{TOC}}` and `{{BODY}}` placeholders.
   - Assert: rendered HTML contains `<nav class="toc">`, three top-level `<li>`s with hrefs matching anchor ids, one nested `<ul>` for the h3.
   - Backwards-compat case: shell without `{{TOC}}` renders body without error and produces no TOC HTML.
   - Edge case: markdown with only h1 (no h2/h3) produces an empty `<nav class="toc">` (or no TOC node — implementer's call, asserted in test).

2. **Fixture regeneration**: refresh both `new-from-scratch-expected.md` and `with-research-transcript-expected.md` to the new numbering and include the Terminologies section. The `with-research-transcript-expected.md` fixture should also exercise the research-glossary copy path.

3. **RED-GREEN skill test**:
   - **RED**: dispatch a subagent with the OLD `prd-docs` skill against the prompt "author a PRD for feature X". Document: the agent writes 18 sections, no Terminologies, no TOC in prd.html.
   - **GREEN**: dispatch a subagent with the UPDATED skill loaded against the same prompt. Verify: 19 sections, Terminologies present at position 2 with non-empty rows, prd.html contains `<nav class="toc">` with links to every section.
   - **REFACTOR**: if GREEN reveals that the subagent skips the terminologies-build step or mis-numbers sections, tighten the SKILL.md instructions and re-test.

### Versioning

Per CLAUDE.md, bump the `shield` plugin version in `.claude-plugin/marketplace.json` only. There is no `pyproject.toml` for the `shield` plugin (Python lives only in `clickup-sprint-planner/`), so no second bump is needed.

## Risks

| Risk | Mitigation |
|---|---|
| Renderer change breaks non-PRD callers of `render-markdown.sh` | The `{{TOC}}` placeholder is optional — shells without it render exactly as today. Tested in the renderer unit test. |
| Subagent skips the terminologies-build step | RED-GREEN test catches it; SKILL.md walk order makes the step explicit (numbered) and mandatory. |
| Auto-extracted terms are noisy or off-topic | User confirmation gate before write. Default is "accept all" but user can prune. If feedback shows noise, tighten the extraction criteria in step 8b. |
| Section-number renumbering misses a reference | Inventory in "Files changed" table was built from `grep` across `shield/skills/general/prd-*` and `shield/commands/prd*.md`. The plan step that renumbers each file is bounded to that list. |

## Open questions

None at time of writing. Both design choices flagged during brainstorm (TOC position, Terminologies auto-fill source) are resolved.

## Out of scope

- Stickly-sidebar / collapsible / floating TOC variants
- Inline link from a term's first PRD usage to its Terminologies row
- A separate `terminologies.yaml` per feature folder (shared across PRDs in the same folder)
- Auto-extraction of terms from `/plan` outputs or code references
- Migrating existing `prd.md` / `prd.html` files
