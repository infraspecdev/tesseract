# Shield Writing-Style Authoring Guide — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> REQUIRED SUB-SKILL when editing any `SKILL.md`: also load `superpowers:writing-skills` (skill-content quality) and `updating-plugin-assets` (this repo's eval-coverage procedure).

**Goal:** Add a canonical `shield:writing-style` skill that the four Shield doc-authoring skills apply while writing, so generated docs are simple, clear, concise, and to the point — and so future doc skills inherit the standard by contract.

**Architecture:** One source-of-truth skill at `shield/skills/general/writing-style/SKILL.md`. The four current doc skills (`prd-docs`, `plan-docs`, `lld-docs`, `research`) gain an explicit self-check step that applies it to author-written prose only (never rendered/marker-wrapped or JSON content). A contract in `CLAUDE.md` + `updating-plugin-assets` makes future doc skills inherit it. One end-to-end eval proves the skill tightens prose.

**Tech Stack:** Markdown skill definitions; Shield end-to-end eval harness (`shield/evals/run-eval.sh`, `claude --print` dispatch); pre-commit hooks.

**Spec:** `docs/superpowers/specs/2026-06-01-shield-writing-style-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `shield/skills/general/writing-style/SKILL.md` | NEW — canonical writing-style guide (4 principles, scope guard, revision pass) |
| `shield/evals/writing-style/01-tighten-prose.md` | NEW — end-to-end eval proving the skill tightens bloated prose |
| `shield/evals/README.md` | Add an Index section for the `writing-style` folder |
| `shield/skills/general/prd-docs/SKILL.md` | Add self-check step before the write step |
| `shield/skills/general/plan-docs/SKILL.md` | Add self-check step before the markdown-write steps |
| `shield/skills/general/lld-docs/SKILL.md` | Add self-check note in the write contract |
| `shield/skills/general/research/SKILL.md` | Add self-check step before the write step |
| `CLAUDE.md` | Add doc-authoring convention bullet |
| `.claude/skills/updating-plugin-assets/SKILL.md` | Add the writing-style contract for future doc skills |
| `.claude-plugin/marketplace.json` | Bump Shield `2.23.0` → `2.24.0` |

**TDD order:** write the eval first (RED — without the skill, a dispatched subagent leaves filler in), then create the skill (GREEN), then wire the four skills + contract, then bump version and re-run the eval.

---

### Task 1: Write the end-to-end eval (RED)

**Files:**
- Create: `shield/evals/writing-style/01-tighten-prose.md`

- [ ] **Step 1: Create the eval file**

Create `shield/evals/writing-style/01-tighten-prose.md` with exactly this content:

````markdown
---
name: 01-tighten-prose
skill_under_test: shield:writing-style
scenario: Bloated PRD prose is tightened — filler cut, facts preserved, output written to a file
---

## Setup
```bash
mkdir -p docs/shield/writing-style-test
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/writing-style-test/draft.md <<'EOF'
# Checkout Latency Problem

It is important to note that, at the end of the day, the checkout flow is
currently experiencing what can only be described as a situation where the
performance is not where we would ideally like it to be. Basically, due to the
fact that the p95 latency is currently sitting at around 800ms, there is a real
and genuine possibility that users may potentially decide to abandon their carts.
We are of the firm belief that we should endeavour to undertake an initiative in
order to facilitate the reduction of the aforementioned p95 latency down to a
target of 200ms. The team responsible for this, which is the Payments team, will
be the ones who are going to be owning this particular piece of work going forward.
EOF
```

## Prompt
> Apply the `shield:writing-style` skill to `docs/shield/writing-style-test/draft.md`. Write the tightened version to `docs/shield/writing-style-test/tightened.md`. Preserve every fact (numbers, team names, targets) exactly; only improve the writing.

## Success criteria

### Structural (deterministic, bidirectional must-find)
- docs/shield/writing-style-test/tightened\.md
- 800ms
- 200ms
- [Pp]ayments

### Qualitative (LLM-judged)
- The tightened version removes throat-clearing/filler present in the original (e.g. "It is important to note", "at the end of the day", "due to the fact that", "aforementioned").
- The tightened version is materially shorter than the original while preserving all factual content (the 800ms→200ms p95 target and Payments ownership).
- The tightened version uses plain language and active voice rather than the original's hedged, passive phrasing.

## Pass threshold
4 of 4 structural + 2 of 3 qualitative.
````

- [ ] **Step 2: Run the eval to confirm RED (skill does not yet exist)**

Run: `./shield/evals/run-eval.sh writing-style/01-tighten-prose`
Expected: `RESULT: FAIL` (or a notably weak qualitative pass). The dispatched subagent cannot load `shield:writing-style` (not created until Task 2), so filler-removal is inconsistent. Capture this output — it is the RED baseline for the commit body.

- [ ] **Step 3: Record the RED baseline**

Save the RED output to a scratch note (not committed) for the commit/PR body. One sentence: "RED: without shield:writing-style, the subagent leaves throat-clearing filler and passive phrasing in tightened.md (qualitative <2/3)."

- [ ] **Step 4: Commit the eval**

```bash
git add shield/evals/writing-style/01-tighten-prose.md
git commit -m "test(shield): RED eval for writing-style prose tightening"
```

---

### Task 2: Create the canonical writing-style skill (GREEN)

**Files:**
- Create: `shield/skills/general/writing-style/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `shield/skills/general/writing-style/SKILL.md` with exactly this content:

````markdown
---
name: writing-style
description: Use when authoring or revising any Shield doc — research, PRD, TRD/plan, LLD — to make author-written prose simple, clear, concise, and to the point. Applies to prose only; never rewrites rendered/marker-wrapped sections or JSON.
---

# Writing Style

Make Shield doc prose simple, clear, concise, and to the point. This is the
single source of truth for "what good Shield prose looks like." Doc-authoring
skills apply it to author-written prose before writing the doc out.

## Scope — prose only

Apply to **author-written prose**: problem statements, summaries, narrative
sections, outcomes, descriptions, rationale.

**Never touch:**
- Marker-wrapped or deterministically-rendered regions — e.g. the bytes between
  `<!-- BEGIN rendered:* -->` and `<!-- END rendered:* -->` (TRD §10 from
  `render_trd_section.py`). Rewriting these triggers `validate_trd.py` drift
  errors (`milestone_drift`, `unbounded_markers`).
- JSON sidecars, schema-bound field values, stable anchors, code blocks, and
  literal command/output samples.

If unsure whether a region is rendered, leave it untouched.

## The four principles

### 1. Cut filler & redundancy
Delete throat-clearing, hedging, and restated points. Every sentence earns its place.
- ❌ "It is important to note that, at the end of the day, the system is slow."
- ✅ "The system is slow."
Cut: "it is important to note", "basically", "in order to", "due to the fact that",
"aforementioned", "going forward", "really/genuinely", doubled synonyms.

### 2. Plain language
Short sentences. Active voice. Common words. Define an unavoidable term once.
- ❌ "Latency reduction will be facilitated by the team."
- ✅ "The team will cut latency."

### 3. Structure over prose
Prefer tables and bullets to long paragraphs. Lead with the conclusion (BLUF —
bottom line up front), then support it.
- ❌ A 6-sentence paragraph listing five requirements.
- ✅ A 5-row bullet list, conclusion sentence first.

### 4. Concrete & specific
Name real users, numbers, files, outcomes. Replace vague abstractions.
- ❌ "Improve performance."
- ✅ "Cut checkout p95 latency from 800ms to 200ms."

## Revision pass

Before writing the doc, run each prose block through this checklist:

| Check | Action |
|---|---|
| Filler phrase present? | Delete it. |
| Sentence > ~25 words or passive? | Split / make active. |
| Paragraph lists 3+ parallel items? | Convert to a table or bullets. |
| Vague claim ("fast", "better", "improve")? | Replace with a number/name/file. |
| Point already made above? | Cut the repeat. |
| Conclusion buried at the end? | Move it to the front (BLUF). |

Preserve all facts — numbers, names, targets, file paths — exactly. Tighten the
writing, never the meaning.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Rewriting a `<!-- BEGIN rendered:* -->` block | Leave rendered/marker-wrapped content untouched |
| Editing JSON sidecar values for "clarity" | Sidecars are structured data, not prose |
| Dropping a fact while cutting words | Tighten phrasing, keep every number/name |
| Over-compressing into cryptic shorthand | Concise ≠ terse-to-the-point-of-unclear |

## See Also
- `shield:summarize` — sibling skill for condensing existing long content
- `prd-review` `problem-clarity` / `stakeholder-communicability` — downstream clarity checks
````

- [ ] **Step 2: Verify frontmatter and structure**

Run: `head -4 shield/skills/general/writing-style/SKILL.md`
Expected: a `---` frontmatter block with `name: writing-style` and a `description:` line beginning "Use when authoring or revising any Shield doc".

- [ ] **Step 3: Run the eval to confirm GREEN**

Run: `./shield/evals/run-eval.sh writing-style/01-tighten-prose`
Expected: `RESULT: PASS` — `4 of 4 structural` and at least `2 of 3 qualitative`. The subagent now loads `shield:writing-style`, cuts the filler, keeps `800ms`/`200ms`/`Payments`, and writes `tightened.md`.

- [ ] **Step 4: If the eval fails, fix the skill and re-run**

If structural fails: confirm the prompt's output path matches the assertion (`tightened.md`) and facts are preserved. If qualitative fails: sharpen the principle wording / examples in the skill. Re-run Step 3 until PASS. Do not proceed until GREEN.

- [ ] **Step 5: Commit the skill**

```bash
git add shield/skills/general/writing-style/SKILL.md
git commit -m "feat(shield): add writing-style authoring guide (GREEN)"
```

---

### Task 3: Wire prd-docs

**Files:**
- Modify: `shield/skills/general/prd-docs/SKILL.md` (Step Skeleton table, before row "15 | Write `prd.md`...")

- [ ] **Step 1: Add a self-check row to the Step Skeleton**

In `shield/skills/general/prd-docs/SKILL.md`, find this line (row 54 area):

```
| 15 | Write `prd.md`, `prd.html`, `prd.meta.json` | always | Yes |
```

Insert a new row immediately BEFORE it:

```
| 14b | Apply `shield:writing-style` to all author-written prose (NOT rendered/marker-wrapped sections or the §2 Terminologies table values) before writing | always | Yes |
```

- [ ] **Step 2: Verify the edit**

Run: `grep -n "shield:writing-style" shield/skills/general/prd-docs/SKILL.md`
Expected: one match on the new row, positioned before the "Write `prd.md`" row.

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/prd-docs/SKILL.md
git commit -m "feat(shield): apply writing-style in prd-docs"
```

---

### Task 4: Wire plan-docs

**Files:**
- Modify: `shield/skills/general/plan-docs/SKILL.md` (Step Skeleton table, around rows 163-165)

- [ ] **Step 1: Add a self-check row to the Step Skeleton**

In `shield/skills/general/plan-docs/SKILL.md`, find this line:

```
| 4 | Generate `{plan_trd_md}` per the 14-section TRD template (atomic write, provenance stamp) | always | Yes |
```

Insert a new row immediately BEFORE it:

```
| 3b | Apply `shield:writing-style` to author-written TRD/plan prose (preamble/narrative sections only — NEVER the marker-wrapped rendered regions like §10 Milestones, and never `{plan_json}` values) | always | Yes |
```

- [ ] **Step 2: Verify the edit**

Run: `grep -n "shield:writing-style" shield/skills/general/plan-docs/SKILL.md`
Expected: one match, positioned before the "Generate `{plan_trd_md}`" row.

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/plan-docs/SKILL.md
git commit -m "feat(shield): apply writing-style in plan-docs (prose only, not rendered §10)"
```

---

### Task 5: Wire lld-docs

**Files:**
- Modify: `shield/skills/general/lld-docs/SKILL.md` (`## Atomic write contract` section, ~line 44)

- [ ] **Step 1: Read the write-contract section to find the insertion point**

Run: `sed -n '44,54p' shield/skills/general/lld-docs/SKILL.md`
Expected: the `## Atomic write contract` heading and its body lines.

- [ ] **Step 2: Append a writing-style line to the Atomic write contract**

Add this line as the last bullet/sentence of the `## Atomic write contract` section (immediately before the next `##` heading):

```
- Before the write, apply `shield:writing-style` to author-written prose sections (overview, rationale, narrative). Do NOT alter the provenance stamp, the §14 Changelog rows, header metadata, code blocks, or `n/a — <reason>` escapes.
```

- [ ] **Step 3: Verify the edit**

Run: `grep -n "shield:writing-style" shield/skills/general/lld-docs/SKILL.md`
Expected: one match inside the Atomic write contract section.

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/lld-docs/SKILL.md
git commit -m "feat(shield): apply writing-style in lld-docs"
```

---

### Task 6: Wire research

**Files:**
- Modify: `shield/skills/general/research/SKILL.md` (Step Skeleton table, before row 54 "9 | Write `{research}`...")

- [ ] **Step 1: Add a self-check row to the Step Skeleton**

In `shield/skills/general/research/SKILL.md`, find this line (row 54 area):

```
| 9 | Write `{research}` (findings) + `.session-transcript.md` (side-artifact) | Both | always | Yes |
```

Insert a new row immediately BEFORE it (match the existing column count — Step | Action | Phase | When | Mandatory):

```
| 8b | Apply `shield:writing-style` to the synthesized findings prose (NOT citation blocks, quoted source text, or the raw transcript) | Both | always | Yes |
```

- [ ] **Step 2: Verify the edit**

Run: `grep -n "shield:writing-style" shield/skills/general/research/SKILL.md`
Expected: one match, positioned before the "Write `{research}`" row.

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/research/SKILL.md
git commit -m "feat(shield): apply writing-style in research"
```

---

### Task 7: Add the contract so future doc skills inherit it

**Files:**
- Modify: `CLAUDE.md` (`## Key Conventions`, after the MCP servers bullet at line 41)
- Modify: `.claude/skills/updating-plugin-assets/SKILL.md` (after `## When NOT to use`, ~line 37)

- [ ] **Step 1: Add the convention bullet to CLAUDE.md**

In `CLAUDE.md`, find this line:

```
- **MCP servers** are configured in `.mcp.json` at the plugin root.
```

Insert immediately AFTER it:

```
- **Doc-authoring skills** (any skill that writes a doc to `docs/shield/`) MUST apply the `shield:writing-style` skill to their author-written prose before writing — see `shield/skills/general/writing-style/SKILL.md`. This keeps generated docs simple, clear, and concise. It applies to prose only, never to rendered/marker-wrapped sections or JSON sidecars.
```

- [ ] **Step 2: Add the contract section to updating-plugin-assets**

In `.claude/skills/updating-plugin-assets/SKILL.md`, find the end of the `## When NOT to use` section — this line:

```
For these, state "no eval-shaped surface" in the PR body and proceed.
```

Insert immediately AFTER it (a new section):

```

## Doc-authoring skills — writing-style contract

If the asset you are adding or editing is a **doc-authoring skill** (it writes a
doc to `docs/shield/` — e.g. `prd-docs`, `plan-docs`, `lld-docs`, `research`, or
any future equivalent), it MUST include an explicit step that applies
`shield:writing-style` to its author-written prose before writing. Prose only —
never rendered/marker-wrapped sections or JSON sidecars. This is part of the
definition of done for such skills, alongside eval coverage.
```

- [ ] **Step 3: Verify both edits**

Run: `grep -n "writing-style" CLAUDE.md .claude/skills/updating-plugin-assets/SKILL.md`
Expected: one match in `CLAUDE.md` (Key Conventions) and at least one in the updating-plugin-assets contract section.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md .claude/skills/updating-plugin-assets/SKILL.md
git commit -m "docs(shield): contract so future doc skills apply writing-style"
```

---

### Task 8: Eval README index, version bump, final verification

**Files:**
- Modify: `shield/evals/README.md` (add an Index section for `writing-style`)
- Modify: `.claude-plugin/marketplace.json:12` (`2.23.0` → `2.24.0`)

- [ ] **Step 1: Add an Index section to the eval README**

In `shield/evals/README.md`, find the `### Index — prd-docs` table (ends with the `05 | end-to-end-render` row near line 106). Immediately AFTER that table's last row, add:

```

### Index — writing-style

| # | Name | Measures |
|---|---|---|
| 01 | tighten-prose | Cuts filler/passive voice, preserves facts, prose-only scope |
```

- [ ] **Step 2: Bump the Shield version**

In `.claude-plugin/marketplace.json`, change the `shield` plugin version:

```
      "version": "2.23.0",
```
to:
```
      "version": "2.24.0",
```

(Only the `shield` block at line 12 — leave the deprecated plugins untouched. Shield has no plugin-root `pyproject.toml`, so no Python version bump is needed.)

- [ ] **Step 3: Validate marketplace.json is still valid JSON**

Run: `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Re-run the eval to confirm still GREEN**

Run: `./shield/evals/run-eval.sh writing-style/01-tighten-prose`
Expected: `RESULT: PASS` (4/4 structural + ≥2/3 qualitative).

- [ ] **Step 5: Run pre-commit hooks across changed files**

Run: `pre-commit run --all-files`
Expected: all hooks Pass or Skip (notably the `end-to-end eval format check`).

- [ ] **Step 6: Commit**

```bash
git add shield/evals/README.md .claude-plugin/marketplace.json
git commit -m "chore(shield): writing-style eval index + bump shield to 2.24.0"
```

- [ ] **Step 7: Push and open the PR**

```bash
git push
```

PR body MUST include:
- The eval path: `shield/evals/writing-style/01-tighten-prose.md` and the PASS output (Definition of Done item 4).
- The RED baseline sentence captured in Task 1 Step 3.
- Note: version bumped in `.claude-plugin/marketplace.json` only (no `pyproject.toml` for the shield plugin root).

---

## Self-Review

**Spec coverage:**
- Canonical skill → Task 2. ✅
- Scope guard (prose only, not rendered/JSON) → skill body (Task 2) + every wiring step (Tasks 3-6) + contract (Task 7). ✅
- Wire 4 current skills → Tasks 3, 4, 5, 6. ✅
- Contract for future skills (CLAUDE.md + updating-plugin-assets) → Task 7. ✅
- Eval coverage (RED→GREEN) → Tasks 1, 2; README index Task 8. ✅
- Version bump → Task 8. ✅
- Four principles (filler, plain language, structure, concrete) → skill body Task 2. ✅

**Placeholder scan:** No TBD/TODO. Full skill and eval content is inline. All file paths exact.

**Type/name consistency:** Skill name `shield:writing-style` and folder `shield/skills/general/writing-style/` consistent across all tasks. Eval slug `01-tighten-prose` and output file `tightened.md` consistent between Task 1 (eval) and Task 2 (GREEN run). Version `2.24.0` consistent.

**Note for the worker:** The skeleton-row numbers (`14b`, `3b`, `8b`) are labels for ordering, not array indices — insert them as literal new table rows at the indicated position; do not renumber existing rows.
