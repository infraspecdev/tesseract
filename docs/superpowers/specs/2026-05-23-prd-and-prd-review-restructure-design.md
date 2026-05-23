# PRD + PRD-Review Restructure — Design

**Date:** 2026-05-23
**Owner:** ashwini.manoj@aspora.com
**Status:** Drafted; awaiting user review before plan generation
**Scope:** `shield/skills/general/prd-docs/`, `shield/skills/general/prd-review/`, `shield/commands/prd.md`, `shield/commands/prd-review.md`, evals, and a new repo-scoped project skill at `.claude/skills/script-llm-contract/`

---

## 1. Problem we're solving

Today `/prd` walks the user through a 20-section scaffold to author a new PRD, and `/prd-review` dispatches reviewer agents against an existing PRD to produce a scored gap analysis + annotated `enhanced-prd.md`. Three concerns:

1. **`/prd-review` output shape diverges from `/prd`.** `/prd` writes `prd.md` + `prd.html` + `prd.meta.json` in the feature folder. `/prd-review` writes `summary.md` + `enhanced-prd.md` (with inline `<!-- [from: persona] -->` annotations) in a separate review folder. Downstream consumers (`/plan`) read from the feature folder and don't benefit from review fixes unless the user manually copies the enhanced PRD across.
2. **PRDs leak implementation detail.** The scaffold includes sections (§5 Architecture & flows, §9 Functional requirements, §10 NFRs) that invite implementation framing — Redis choices, p99 targets, per-resource costs. Product framing (what the user sees / experiences) gets lost.
3. **LLM-driven steps that should be deterministic.** Counter resolution, manifest updates, sparse-section detection, reviewer aggregation, and finalize plumbing are LLM-orchestrated today. This costs replay determinism and complicates testing.

## 2. Goals

- `/prd` and `/prd-review` produce the **same output shape**: `{feature}/prd.md` + `{feature}/outputs/prd.html` + `{feature}/prd.meta.json`. `/prd-review`'s scored analysis stays as an audit-trail side-artifact under `reviews/prd/{date}/`, but is no longer the primary deliverable.
- The scaffold is **product-focused**. Sections that lean implementation are reframed so the walk prompt steers the user toward user-visible behavior. Implementation-detail leakage is graded as a reviewer anti-pattern.
- Deterministic steps become **scripts** that the LLM invokes and reacts to per a documented exit-code contract.
- The script-LLM contract is captured as a **repo-scoped project skill** so future plugin work in tesseract benefits from the same discipline.

## 3. Non-goals

- Changing `/research`, `/plan`, `/plan-review`, or `/implement`. Cost / NFR concepts that previously lived in the PRD's implementation-leaning sections may migrate to `/plan-review`'s dim list, but that migration is out of scope here; this design notes the relocation but doesn't change `/plan-review`.
- Batch migration of existing legacy PRDs in user feature folders. Migration is lazy — a legacy PRD is upgraded only when the user runs `/prd` or `/prd-review` against it.
- Touching the marketplace / plugin distribution layer. Shield's `marketplace.json` version will be bumped per repo convention, but no structural changes there.

## 4. Architecture: consolidated skill + two entry paths

### 4.1 Directory layout

Collapse `prd-docs/` and `prd-review/` into a single skill directory `shield/skills/general/prd/`. All assets that today are duplicated across the two skills become a single source of truth.

```
shield/skills/general/prd/
├── SKILL.md              one orchestrator with two entry paths
├── templates.md          THE scaffold (used by both /prd and /prd-review)
├── rubric.md             THE rubric (used by /prd-review dispatch)
├── dimensions.md         dim registry (used by /prd-review dispatch)
├── dim-section-map.yaml  NEW: dim → § mapping (machine-readable;
│                              read by scripts AND referenced by prompts)
├── prompts/*.md          12 PM-dim reviewer prompts (incl. cost)
├── scoring.md            shared scoring logic (consumed by aggregate-review.sh)
├── ingest.md             used by both entry paths via prd-ingest.sh
├── meta-schema.md        prd.meta.json schema
├── type-detection.md     lean vs standard
└── test-fixtures/        shared fixtures
```

`shield/skills/general/prd-docs/` and `shield/skills/general/prd-review/` are removed in the same change. The two slash commands `/prd` and `/prd-review` still exist; they both reference the consolidated skill.

### 4.2 Two entry paths share one finalize step

```
/prd          ──┐                                 ┌──> {feature}/prd.md
                │                                 │    {feature}/outputs/prd.html
                ├──> walkSection() (only used     │    {feature}/prd.meta.json
                │       by /prd for low-          ├──> manifest.json
/prd-review   ──┘       confidence sections)     │    index.html
                                                 │
                ╰──> generatePRD()  ──> finalize()
```

`finalize()` is implemented as a single shell script (`finalize-prd.sh`) that all entry paths converge on. It owns the invariant: `prd.md` and `prd.html` move atomically — neither is written without the other being regenerated.

### 4.3 Why this isolates well

- **One walk-section subroutine** lives in `prd/SKILL.md` and is reused only by `/prd`'s low-confidence walk. `/prd-review` skips it — corrections happen in a one-shot generation, and the user reviews the whole document at the end.
- **One ingest pipeline** (`prd-ingest.sh`) is invoked by `/prd` step 3, `/prd-review` step 1, and `/prd-review` step 5b.
- **One finalize function** ensures `prd.md` and `prd.html` move together. Same function deletes the temp regardless of entry path.

## 5. The scaffold (single source of truth in `prd/templates.md`)

20 sections, standard variant. **One structural change vs today**: drop standalone §5 Architecture; add §3 Current context with four subsections. Current-architecture sketch (Mermaid OK) moves into §3's "What exists today" subsection as background — never as new-system design.

| # | Section | Change | Walk-prompt framing |
|---|---|---|---|
| 1 | Header | unchanged | owner, status, links, sign-off contact |
| 2 | Terminologies | **rule change**: populated LAST, from PRD body only. Placeholder until then. | Body-grounded only. Research glossary is a candidate source; terms not referenced in §3..§20 are dropped — including from research. See §5.1. |
| 3 | **Current context** (new) | replaces standalone Problem (was §3) | 4 subsections: **What exists today** (incl. current-arch Mermaid as context only) / **The problem we're facing** / **What we're proposing to change** / **Why now** |
| 4 | Personas | renumber | unchanged |
| 5 | Goals & non-goals | renumber | unchanged |
| 6 | Success metrics | renumber | unchanged |
| 7 | User stories & scenarios | renumber | Type field per story (new/enhancement/existing) stays |
| 8 | Product behavior & user-visible rules | renumber (was §9 FRs) — **reframed** | "Describe rules from the user's POV. No 'must use X library'. Yes: 'when third-party rate-limits us, user sees a retry banner; backend is expected to queue requests for up to 5min.'" |
| 9 | UX-impacting constraints | renumber (was §10 NFRs) — **reframed** | "Latency the user *feels*, error states the user *sees*, third-party degradation behavior, accessibility, privacy/legal that touches UX. NOT: p99 targets, infra SKUs, internal monitoring choices." |
| 10 | RBAC & permissions matrix | renumber | who-can-do-what at product level; enforcement mechanics out |
| 11 | External dependencies (UX-impacting only) | renumber — **reframed** | "External systems the user feels. E.g., 'Stripe — if down, users see X banner'. Drops 'internal-cache-service' plumbing." |
| 12 | Risks & mitigations | renumber | unchanged |
| 13 | Assumptions | renumber | unchanged |
| 14 | Rollout plan | renumber | milestones + rollout mechanics |
| 15 | **Cost estimate** | renumber — **reframed high-level only** | Lump estimates: "Infrastructure ~$X/mo (with HA)", "Vendor APIs ~$Y/mo", "Internal effort: ~N engineer-weeks". **No per-resource breakdowns.** Walk prompt explicitly forbids "Aurora us-east-1 multi-AZ" or "NAT gateway $Z" entries. |
| 16 | GTM & customer-comms | renumber | unchanged |
| 17 | Support / CX impact | renumber | unchanged |
| 18 | Open questions | renumber | unchanged |
| 19 | Out of scope | renumber | unchanged |
| 20 | Sign-offs | renumber (today bundled into §1 / final block) — now its own section | unchanged |

**Lean variant (`templates.md` → §lean):** 8 sections — Header, Current context, Personas, Goals & non-goals, Success metrics, User stories, Milestones, Out of scope. Lean folds Sign-offs into Header.

**Mermaid:** still supported by the renderer; lives in §3 Current context (current-state diagram, optional). No dedicated §5.

### 5.1 §2 Terminologies protocol — body-grounded, populated last

§2 is the **last** section to be populated in both entry paths. Until it's filled, it carries a placeholder block:

```markdown
## 2. Terminologies

<!-- Populated last from PRD body content. See §5.1 of the design. -->
| Term | Definition |
|---|---|
```

**Protocol (runs after §3..§20 are drafted and accepted):**

1. **Extract candidates** from two sources:
   - **Source A — research transcript glossary** (if `/research` transcript present at `{feature}/.session-transcript.md`): parse `## Glossary` / `## Terminology` / `## Terms` rows. Each row becomes a candidate `{term, definition, source: "research"}`.
   - **Source B — LLM body scan** of §3..§20: propose 5–15 candidates that are ALL-CAPS acronyms used 2+ times, capitalized multi-word phrases used as named concepts, domain nouns in §4 Personas / §9 UX-impacting constraints / §11 Dependencies without prior definition, or internal product / service names referenced in §11/§14/§16.
2. **Filter by body-occurrence (script).** `count-term-in-body.sh <term> <prd.md>` returns occurrence count in §3..§20 (excluding §2 itself). Candidates with **0 occurrences are dropped** — including Source A candidates. The rule that today says "ALL research-glossary rows MUST appear" is reversed: research is a source pool, not a mandatory copy.
3. **Deduplicate** by lowercased term. On conflict, **Source A's definition wins** (research is authoritative for terms it defines).
4. **Present filtered list to user.** Offer accept-all / edit / add / remove. Default: accept all.
5. **Substitute** into §2, replacing the placeholder block.

**Rationale:** the Common Mistakes rule today says "Dropping Source A research-glossary terms is an error" — that rule is removed. The opposite is now correct: **a §2 entry whose term doesn't appear in the PRD body is the error**. If a research-glossary term is genuinely important to the PRD, the body should reference it (and the user can add the reference during the walk / review). If the term isn't referenced, it doesn't belong in §2.

## 6. Entry path: `/prd` (author from scratch)

```
1. Determine feature folder context.
2. Ask: "Where's your context coming from?"
   options (multi-select): Notion URL · Jira issue/epic · Confluence ·
     Linear · local file path · paste · "none, I'll provide inline"
3. For each source, invoke prd-ingest.sh and react per the script-LLM
   contract. On error code 3 (resource unavailable), try the script's
   suggested fallback; on code 4 (needs human input), surface to user.
4. Ask: "Want to run /research now too? (Recommended if context is light
   or the problem is new.)" — yes → invoke /research; no → skip.
5. One-shot generate full draft prd.md from:
     - ingested context (step 3)
     - /research transcript (step 4, if present)
     - templates.md scaffold (with §2 left as the placeholder block
       per §5.1 — generation MUST NOT fill §2 here)
   Write to {feature}/.prd-draft.md (hidden temp). Generation MUST emit
   a sidecar {feature}/.prd-draft.confidence.json with per-section
   confidence: high | medium | low for §3..§20 only (§2 is N/A).
6. Run filter-low-confidence.sh → list of §-IDs to walk.
7. walkSection(§N) for each low-confidence §. UX: show draft content,
   accept/edit/skip.
8. Run the §2 Terminologies protocol from §5.1 (extract candidates,
   filter by body-occurrence via count-term-in-body.sh, user confirms,
   substitute into §2). This is ALWAYS the last fill step.
9. Present full draft. Ask: "Manually review, then confirm to finalize."
10. On confirm → finalize-prd.sh --entry prd --feature X --draft {feature}/.prd-draft.md
    On reject → keep .prd-draft.md; exit (user can re-run to resume).
```

## 7. Entry path: `/prd-review` (refine existing PRD)

```
1. prd-ingest.sh on source PRD (file/URL/paste).
   Output → {output_dir}/{feature}/reviews/prd/{date}{_counter}/source-prd.md
   (counter resolved by next-review-dir.sh).
2. detect-prd-type.sh source-prd.md → "lean" | "standard". LLM confirms
   with user.
3. PHASE A — Dispatch 13 reviewer invocations in parallel (unchanged
   pattern; dim 13 Cost stays, rubric narrowed — see §9).
4. aggregate-review.sh on dispatch outputs →
     reviews/prd/{date}/summary.md
     reviews/prd/{date}/review-comments.json
     reviews/prd/{date}/detailed/<persona>.md × 5
5. sparse-sections.sh on review-comments.json → §-IDs with Critical D/F.
6. IF sparse sections exist:
   Ask: "Sections X, Y, Z look sparse based on the review. Want to
         gather more context before I apply corrections?"
   yes →
     6a. Ask for source(s) (same prompt as /prd step 2).
     6b. For each, invoke prd-ingest.sh; react per contract.
     6c. Ask: "Run /research too?" — yes → invoke; no → skip.
   no → step 7.
7. PHASE B — Generate corrected PRD in one LLM pass from:
     - source-prd.md
     - review-comments.json (grouped by § via map-gaps-to-sections.sh)
     - additional context from step 6 (if any)
     - templates.md scaffold (new 20-section structure; §2 LEFT as
       placeholder per §5.1 — generation MUST NOT fill §2 here)
   Write to reviews/prd/{date}/corrected-prd.md.
8. Run the §2 Terminologies protocol from §5.1 against the corrected
   PRD body (extract candidates, filter by body-occurrence, user
   confirms, substitute into §2). Last fill step before review.
9. Present corrected PRD. Ask: "Manually review, then confirm to
   finalize into {feature}/prd.md."
10. On accept → finalize-prd.sh --entry prd-review --feature X
                                  --draft <reviews/prd/{date}/corrected-prd.md>
                                  --review-dir <reviews/prd/{date}/>
   On reject → keep corrected-prd.md in review folder; exit.
```

Legacy PRDs (containing standalone §5 Architecture) are handled by the corrected-PRD LLM pass: §5 content is folded into §3's "What exists today" automatically; the user reviews the result before finalize.

## 8. The shared finalize step

`finalize-prd.sh --feature X --draft <path> --entry prd|prd-review [--review-dir <path>]`

```
Steps (atomic; exit non-zero on any failure, leaving temp in place):
  a. Pre-flight: uv installed? draft exists? feature dir writable?
     Each failure → distinct exit code per the script-LLM contract.
  b. cp <draft> {feature}/prd.md (overwrite if exists).
  c. Render {feature}/outputs/prd.html via render-markdown.sh.
     Invariant: this step MUST NOT be skipped when prd.md changes.
  d. Update {feature}/prd.meta.json (jq-based):
        - last_updated = today
        - source_command = "prd" | "prd-review"
        - review_link    = <review-dir> | null (only set when --entry prd-review)
  e. Delete the temp:
        --entry prd        → rm {feature}/.prd-draft.md
                              rm {feature}/.prd-draft.confidence.json
        --entry prd-review → rm <review-dir>/corrected-prd.md
     Side-artifacts in <review-dir> (summary.md, detailed/, source-prd.md,
     review-comments.json) are NOT deleted; they remain as audit trail.
  f. update-manifest.sh --feature X --event prd-updated
       → append manifest.json entry, regenerate index.html.
```

## 9. Reviewer rubric narrowing

Two narrowings to `rubric.md`. The 13-dim dispatch count is unchanged; only rubric content shifts.

### 9.1 Dim 5 NFR coverage — narrow to UX-impacting

Today asks for p99, capacity, scale. Replace eval points with:

| ID | Eval point | Severity |
|---|---|---|
| 5a | Privacy / data-handling visible to user | Critical |
| 5b | Error & degradation user-facing behavior | Critical |
| 5c | Accessibility | Important |
| 5d | Third-party-failure UX | Important |

Implementation-detail asks (Redis, p99 latency targets, scale numbers) move to `/plan-review` dim list. **This PR doesn't change `/plan-review`** — it only relocates the rubric concepts and leaves a TODO for `/plan-review` to absorb them. The new evals here verify that dim 5 no longer asks for `p99` / `scale` in PRD reviews.

### 9.2 Dim 13 Cost & resource impact — narrow to lump estimates

| ID | Eval point | Severity |
|---|---|---|
| 13a | Infrastructure cost estimated as a lump (no per-resource SKU) | Important |
| 13b | Vendor / API cost estimated | Important |
| 13c | Internal effort estimated (engineer-weeks or similar) | Warning |

Reviewer FAILS the PRD if §15 has per-resource breakdowns. Phrases that auto-fail: "Aurora us-east-1 multi-AZ", "NAT gateway $X", "EC2 m5.xlarge × N". The reviewer's `gap` cites the offending line.

### 9.3 New anti-pattern: implementation-detail-bleed

Added to the DX engineer dispatch (cross-cutting, like other anti-patterns):

```
implementation-detail-bleed
  Flag any section that describes HOW (library / SKU / p99 / internal-
  service name) instead of WHAT the user experiences. Exception: §3
  Current context's "What exists today" subsection MAY describe current
  architecture as background — explicitly allowed.
```

## 10. The dim-section map

Lives at `shield/skills/general/prd/dim-section-map.yaml`. Single source of truth for both scripts (`map-gaps-to-sections.sh`) and the corrected-PRD generation prompt.

```yaml
dim_section_map:
  1:  [3]            # Problem clarity            → §3 Current context
  2:  [5, 19]        # Scope boundaries           → §5 Goals & non-goals, §19 Out of scope
  3:  [6]            # Measurable success         → §6 Success metrics
  4:  [7]            # Scenario coverage & AC     → §7 User stories
  5:  [9, 10, 11]    # NFR coverage (UX only)     → §9 UX constraints, §10 RBAC, §11 Deps
  6:  [14]           # Rollout & ops              → §14 Rollout plan
  7:  [1, 20]        # RACI & approvals           → §1 Header, §20 Sign-offs
  8:  [9, 12]        # Legal/privacy/compliance   → §9 UX constraints (privacy-side), §12 Risks
  9:  [16]           # GTM / customer-comms       → §16 GTM
  10: [17]           # Support / CX impact        → §17 Support
  11: [3]            # Why now & cost-of-inaction → §3 Current context
  12: [12, 13, 18]   # Risks & assumptions        → §12, §13, §18
  13: [15]           # Cost & resource impact     → §15 Cost estimate (high-level)
  # anti-patterns: cross-cutting, no specific §
```

## 11. Scripts — the deterministic skeleton

All scripts live at `shield/scripts/prd/`. Python via `uv run --with <deps>` per the repo's `uv`-only convention.

| Script | Purpose | Inputs | Outputs |
|---|---|---|---|
| `prd-ingest.sh` | Classify source + run resolver chain | `<source>`, optional `--resolver <name>` | normalized markdown on stdout (JSON envelope per contract) |
| `detect-prd-type.sh` | lean vs standard | `<prd.md>` | `"lean"` or `"standard"` |
| `next-review-dir.sh` | Resolve `{date}{_counter}` for same-day collisions | `<feature>` | absolute path |
| `sparse-sections.sh` | Find §s with Critical D/F | `<review-comments.json>`, `<dim-section-map.yaml>` | `{"section_ids":[3,9,15]}` |
| `map-gaps-to-sections.sh` | Group gaps by § for the generation prompt | `<review-comments.json>`, `<dim-section-map.yaml>` | `{"§3":[gap-ids],"§9":[gap-ids],…}` |
| `aggregate-review.sh` | Composite + P0-gate from dim-block JSON | `<dispatch-output-dir>` | `review-comments.json`, grade table |
| `filter-low-confidence.sh` | List low-confidence §s | `<draft.confidence.json>` | `{"section_ids":[3,9]}` |
| `update-manifest.sh` | Append + regenerate index.html | `--feature X --event <type> [--payload <json>]` | exit 0 on success |
| `finalize-prd.sh` | Atomic copy + render + cleanup + meta update + manifest | see §8 | exit 0 on success |
| `extract-glossary-candidates.sh` | Parse research transcript glossary into candidate rows (no copy into PRD yet) | `<transcript>` | `{"candidates":[{"term":"...","definition":"...","source":"research"}]}` |
| `count-term-in-body.sh` | Count term occurrences in PRD body (§3..§20, excluding §2) | `<term>`, `<prd.md>` | `{"term":"...","count":N}` |

Scripts that stay as-is: `shield/scripts/render-markdown.sh` (unchanged).

## 12. Script-LLM contract (captured as a project skill)

The contract becomes a repo-scoped project skill at `.claude/skills/script-llm-contract/SKILL.md`.

### 12.1 Triggers (auto-invocation)

- Editing a `SKILL.md` that calls Bash scripts (to ensure exit-code branches + payload handling are wired).
- Designing a new plugin command or skill (to flag deterministic steps for scriptification).
- **Proactive:** when writing any new skill — even if the user hasn't asked — the skill scans the workflow for deterministic steps coded as LLM-only and suggests scripts.

### 12.2 Contract summary

1. **Scripts never prompt.** All inputs come from args or stdin. If a script needs a human decision, it exits with code 4 (`needs-human`) and emits a JSON payload telling the LLM what to ask.
2. **Scripts emit JSON on stdout.** Success or failure, the payload is structured.
3. **Exit codes carry category** (see table below). The LLM branches on `$?`, not on stderr parsing.
4. **Scripts are idempotent and safe to retry** within an error category.

### 12.3 Exit code table

| Code | Category | LLM behavior |
|---|---|---|
| 0 | success | Use stdout payload, continue. |
| 1 | unexpected internal | Surface to user; do NOT retry. |
| 2 | invalid input | Caller bug. LLM re-examines inputs; never auto-retry the same call. |
| 3 | external resource unavailable | Transient. LLM may retry, prompt user, or fall back per `suggested_action`. |
| 4 | needs human input | LLM asks user the question in the payload, then re-invokes with chosen path. |
| 5 | partial success | LLM reviews `partial:` payload; decides re-dispatch / accept / escalate. |

### 12.4 Output envelope

Success:
```json
{"ok": true, "data": {...}}
```

Error:
```json
{
  "ok": false,
  "code": 3,
  "category": "external_resource_unavailable",
  "resource": "notion_mcp",
  "reason": "401 unauthorized",
  "suggested_action": "ask_user_to_run_mcp_connect",
  "fallback": "webfetch_with_paste_prompt"
}
```

`suggested_action` and `fallback` are advisory. The LLM decides.

### 12.5 Skill content includes

- The contract (above).
- A walked example (the `prd-ingest.sh notion://…` flow).
- A "common mistakes" table — scripts that read stdin interactively, scripts that mask errors as success, scripts that retry internally and hide transients from the LLM.
- A checklist for skill authors: for each LLM step in your workflow, ask "is this deterministic?" — if yes, make it a script.

## 13. Evals (mandatory per CLAUDE.md)

### 13.1 `shield/evals/prd/` (replaces `prd-docs/`)

| Eval | What it tests |
|---|---|
| `prd-context-gathering.eval.md` | `/prd` prompts for context source, ingests via `prd-ingest.sh`, surfaces errors per contract |
| `prd-research-opt-in.eval.md` | After ingest, `/prd` offers research and behaves correctly on yes/no |
| `prd-low-confidence-walk.eval.md` | One-shot generation emits confidence sidecar; walk visits only low-confidence § |
| `prd-current-context-section.eval.md` | §3 Current context has all four subsections filled |
| `prd-no-architecture-section.eval.md` | New scaffold has no standalone §5 Architecture (negative check) |
| `prd-cost-high-level.eval.md` | §15 Cost has lump estimates; "Aurora us-east-1", "NAT gateway" are MUST-NOT-FIND |
| `prd-finalize-html-rendered.eval.md` | `finalize-prd.sh` re-renders prd.html whenever prd.md changes |
| `prd-temp-cleanup.eval.md` | After finalize, `.prd-draft.md` + confidence sidecar removed |
| `prd-terminologies-body-grounded.eval.md` | §2 contains ONLY terms that occur in §3..§20 of the same PRD (excluding §2 itself). Specifically: a research-glossary term NOT used in the body is absent from §2. A term used 2+ times in the body but missing from research is present. `count-term-in-body.sh` returns N>0 for every row in §2. |
| `prd-terminologies-placeholder-until-last.eval.md` | During the walk / generation phase, §2 is a placeholder block (not populated). It only fills after §3..§20 are accepted. |

### 13.2 `shield/evals/prd-review/` (updated)

| Eval | What it tests |
|---|---|
| `prd-review-walk-output-shape.eval.md` | Output is structurally identical to `/prd` output (prd.md + prd.html + prd.meta.json) |
| `prd-review-sparse-detection.eval.md` | `sparse-sections.sh` correctly identifies §s with Critical D/F (script unit test) |
| `prd-review-additional-context-flow.eval.md` | When sparse, `/prd-review` asks for additional context and incorporates it |
| `prd-review-dispatch-aggregation.eval.md` | `aggregate-review.sh` deterministically produces composite + P0-gate (script unit test) |
| `prd-review-corrected-cleanup.eval.md` | After finalize: corrected-prd.md deleted; side-artifacts retained |
| `prd-review-rubric-narrowing.eval.md` | Dim 5 fails per-resource SKU mentions; passes UX-only NFRs |
| `prd-review-cost-anti-pattern.eval.md` | DX engineer flags `implementation-detail-bleed` when §15 has per-resource entries |
| `prd-review-legacy-fold.eval.md` | A legacy PRD with standalone §5 Architecture has its content folded into §3 by the corrected-PRD pass |

### 13.3 `shield/evals/script-llm-contract/`

| Eval | What it tests |
|---|---|
| `script-exit-code-contract.eval.md` | Fixture script returns code 3 with JSON payload; LLM follows the documented branch (retry / fallback / prompt) |
| `script-no-prompting.eval.md` | Fixture script that reads stdin interactively fails the contract |
| `proactive-script-suggestion.eval.md` | When editing a SKILL.md with 5 deterministic LLM steps, the skill prompts to scriptify them |

## 14. Migration

| Scenario | Behavior |
|---|---|
| User runs `/prd-review` on a legacy 20-section PRD | Source ingested as-is. Reviewers grade against narrowed rubric (dim 5 UX-only, dim 13 lump-cost). Corrected PRD generated against the new 20-section scaffold; §5 Architecture content folds into §3 "What exists today" automatically. User reviews + finalizes. |
| User runs `/prd` in a feature folder containing a legacy PRD | The existing upgrade flow detects legacy structure → offers: (a) re-run as `/prd-review` (preferred), (b) start fresh, (c) cancel. |
| Untouched legacy PRDs across many feature folders | No batch migration. Each PRD migrates lazily on first `/prd` or `/prd-review` invocation. |

## 15. What gets deleted

- `shield/skills/general/prd-docs/` (directory) — contents moved into `shield/skills/general/prd/`.
- `shield/skills/general/prd-review/` (directory) — contents moved into `shield/skills/general/prd/`.
- References to §5 Architecture & flows throughout `templates.md`, `SKILL.md`, `rubric.md`, `prompts/`, `dimensions.md`.
- `enhanced-prd.md` filename and concept (replaced by `corrected-prd.md`, which is temp-deleted on finalize).
- `enhanced-prd.html` rendering step. Only canonical `{feature}/outputs/prd.html` remains.

## 16. What stays exactly the same

- `shield/agents/` — the 4 legacy persona subagents. Prompts are lightly touched for new section names, but agent shape is unchanged.
- `shield/scripts/render-markdown.sh` — unchanged.
- `manifest.json` + `index.html` dashboard layout — unchanged.
- `/research`, `/plan`, `/plan-review`, `/implement` — untouched in this PR.

## 17. Version bumps

Per repo convention (`CLAUDE.md` §Git Conventions):
- `.claude-plugin/marketplace.json` — bump Shield's version (minor — new feature). NOT in `plugin.json`.
- No `pyproject.toml` bump needed (no Python package version is tied to PRD logic; scripts run via `uv run --with`).

## 18. Open questions

None remaining at design-doc time. All open questions from the brainstorming session have been resolved into concrete choices above. Implementation may surface new ones; those go into the plan, not back into this design.

## 19. Out of scope (deferred)

- `/plan-review` absorbing the implementation-detail NFR concepts (p99, scale, infra SKU) relocated from PRD dim 5. Tracked as a follow-up.
- Cross-plugin propagation of the script-LLM contract — the skill is repo-scoped, but `infra-review` / `clickup-sprint-planner` / `dev-workflow` adoption is opportunistic, not a forced refactor.
- Marketplace-wide changes (none required).
