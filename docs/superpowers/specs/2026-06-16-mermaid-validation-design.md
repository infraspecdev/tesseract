# Mermaid diagram quality — design

**Date:** 2026-06-16
**Status:** approved (brainstorm) — pending spec review
**Branch / PR:** `feat/shield-mermaid-validation` (PR #69 — full system ships here, not just the heuristic linter)

## Problem

Shield embeds Mermaid diagrams in generated docs (LLDs, TRDs, PRDs). The
renderer emits each fence verbatim as `<pre class="mermaid">` for client-side
mermaid.js (`render-markdown.py:99`), so an invalid diagram fails **only in the
browser at view time**. Nothing in the author → write → eval → render → CI path
ever parses a diagram.

This shipped: 8 of 17 sequence diagrams in the component LLDs failed real
mermaid parsing (verified with mermaid-cli 10.9.1). Two root causes dominated —
semicolons (mermaid treats `;` as a statement separator) and an actor named
`Create` (a reserved keyword).

PR #69 added a pure-Python heuristic linter for those known traps. This design
extends that work into a complete system.

## Goals

1. **Complete coverage** — catch every syntax error, not three heuristics.
2. **Catch earlier** — validate at authoring time, before the file is written.
3. **Auto-repair** — fix the mechanical breakages without a human.
4. **Prevent at generation** — stop agents producing bad mermaid up front.

## Non-goals

- Render-fidelity checks (layout, overlap, readability). Syntax validity only.
- Validating non-Shield markdown outside `docs/**` and `shield/{skills,templates,agents}/**`.
- A hard Node dependency. When Node is absent, the heuristic fallback runs and
  coverage degrades gracefully (it does not block).

## Architecture

One core validator with a real-parse backend, a deterministic fixer, four
integration points, and a prevention reference.

```
                    ┌─────────────────────────────────────────┐
                    │  validate_mermaid.py  (orchestrator)      │
                    │  • extract ```mermaid blocks from .md     │
                    │  • map errors → document-relative lines   │
                    │  • --fix (deterministic repair)           │
                    └───────────────┬───────────────────────────┘
                       calls per block, picks best available
                  ┌─────────────────┴──────────────────┐
                  ▼                                     ▼
   ┌──────────────────────────┐          ┌────────────────────────────┐
   │ validate_mermaid.mjs      │  (else)  │ heuristic checks (PR #69)   │
   │ Node + mermaid.parse()    │ ───────▶ │ semicolon / reserved /      │
   │ authoritative, no chromium│ fallback │ block-balance               │
   └──────────────────────────┘          └────────────────────────────┘
```

### Goal → mechanism

| Goal | Mechanism |
|---|---|
| Complete coverage | `validate_mermaid.mjs` calls real `mermaid.parse()`. Python heuristic remains the no-Node fallback. |
| Catch earlier | lld-docs (and the mermaid-emitting steps of /plan, /prd) call the validator before the atomic write. |
| Auto-repair | `--fix` repairs known classes and re-parses. At author-time, residual errors return to the agent's repair loop with the parse message. |
| Prevent at generation | `shield/skills/general/mermaid-authoring.md` — loaded by doc-authoring skills when emitting diagrams. |

### Components

1. **`shield/scripts/validate_mermaid.mjs`** — Node backend. Reads one diagram
   on stdin, calls `mermaid.parse()`, exits 0 on success or non-zero with the
   parse error on stderr. No Chromium. mermaid version pinned via a local
   `package.json` (or `npx --package mermaid@<ver>`).

2. **`shield/scripts/validate_mermaid.py`** — orchestrator (upgrade of the PR
   #69 script). Extracts `mermaid` fences with document-relative line offsets;
   for each block calls the Node backend when Node + mermaid are available, else
   the existing heuristic checks; maps backend errors back to document lines.

3. **`--fix` mode** — deterministic repair of known classes: `;` → `—` (or `,`
   inside parentheses/quotes), rename reserved-word actor identifiers
   consistently across a block. Re-validates after repair; only rewrites the
   file if every block then passes, else reports the residual.

4. **Author-time integration** — `lld-docs` SKILL contract gains a
   validate-before-write step: after composing content, validate every mermaid
   block; run `--fix`; if a block still fails, the authoring agent rewrites it
   from the parse error, re-validates, and retries (bounded). A shared helper
   note lets `/plan` and `/prd` reuse the same contract.

5. **`shield/skills/general/mermaid-authoring.md`** — prevention reference (no
   semicolons, reserved-word list, quoting rules, keep labels simple). A sibling
   of `architecture-authoring.md`; referenced by lld-docs, prd-docs, plan-docs,
   and `agents/architect.md`. Kept separate from `architecture-authoring.md`
   because the hygiene rules apply to sequence diagrams too, not just C4.

## Risk / spike

`mermaid.parse()` headless in Node may need a DOM shim (jsdom) and the right
import form. Very likely fine and fast (~10–50 ms/diagram), but **Phase 1 opens
with a ~20-minute spike** proving it on one diagram. If it unexpectedly needs
Chromium, fall back to heuristic-as-primary and reconsider the backend.

## Phasing

Each phase is independently shippable; all land in PR #69. The PR #69 heuristic
becomes the fallback, not throwaway.

### Phase 1 — Real parser + fallback (Goal 1)
- Spike `mermaid.parse()` headless.
- `validate_mermaid.mjs` backend; pin mermaid version.
- Upgrade `validate_mermaid.py`: call backend, fall back to heuristic, map lines.
- Upgrade the pre-commit hook to use the real parser when available.
- Tests: real-parse path catches errors the heuristic misses; fallback path
  still works when Node is stubbed absent.
- **Acceptance:** every broken pre-fix LLD diagram is caught via the real parser;
  all 17 fixed diagrams pass; suite green with and without Node available.

### Phase 2 — Deterministic `--fix` (Goal 3, mechanical)
- `--fix` repair pass + re-validate + safe file rewrite.
- pre-commit autofix mode.
- Tests: `;` and reserved-word fixtures are repaired and then parse clean;
  a non-mechanical error is left untouched and still reported.
- **Acceptance:** running `--fix` on the pre-fix LLDs produces diagrams that
  pass the real parser; unknown errors are not silently mangled.

### Phase 3 — Author-time + prevention (Goals 2, 4, agent repair)
- `mermaid-authoring.md` style guide; wire references into the emitting skills.
- lld-docs validate-before-write + bounded agent repair loop; shared helper for
  /plan and /prd.
- Evals: an lld-docs eval that a diagram with a seeded trap is caught and
  repaired before write; a prevention check that the style guide is referenced.
- **Acceptance:** a seeded bad diagram never reaches disk from `/lld`; the
  authoring skills cite `mermaid-authoring.md`.

## Testing approach

- Unit/eval tests live beside the scripts (`shield/scripts/test_validate_mermaid.py`),
  matching the existing validator convention, run via the existing pytest
  pre-commit hooks.
- RED→GREEN is anchored to the **real** LLD diagrams: the pre-fix versions are
  the RED corpus, the post-fix versions the GREEN corpus.
- Node-backend tests must run with the backend stubbed absent to exercise the
  fallback deterministically in CI without requiring mermaid installed.

## Version / mandate

- Bump shield in `.claude-plugin/marketplace.json` (already `2.27.0 → 2.28.0` on
  the branch; re-confirm at PR close).
- Every changed plugin asset (skills in Phase 3) ships with an eval in the same
  PR, per CLAUDE.md.

## Open questions

None blocking. The Node-backend feasibility is handled by the Phase 1 spike.
