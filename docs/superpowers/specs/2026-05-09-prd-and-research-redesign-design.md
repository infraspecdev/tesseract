# PRD-and-Research Redesign — Design Doc

**Status:** Draft
**Date:** 2026-05-09
**Author:** ashwinimanoj
**Plugin:** shield

---

## TL;DR

Introduce a product-requirements layer to Shield, sitting between research and technical planning. Two new commands (`/prd`, `/prd-review`) plus an enhancement to the existing `/research` command to capture problem-space and tech-context Q&A before its existing external evidence-gathering. Each command is independently usable; downstream commands consume earlier artifacts as context if present.

Shipping order: `/prd-review` first (highest immediate value, lowest competition), then `/prd` (author mode), then `/research` Phase 1 (Q&A + repo auto-detect).

## Problem

Shield's current pre-implementation flow is `/research → /plan → /plan-review → /implement`. `/plan` produces a technical breakdown (epics, stories, tasks, acceptance criteria) — not a product requirements document. Teams that already have PRDs cannot ingest them; teams that don't have PRDs have no Shield-native way to write one. Both groups skip directly to technical planning, which:

- Loses product context (problem framing, success metrics, scope boundaries)
- Lets implementation drift from what users actually need
- Makes downstream stories untestable against product intent
- Misses gaps that a PM would catch (no Out-of-Scope, no leading metrics, no rollout plan)

`/research` today is solution-space (PM framing → 3 parallel agents fetching official docs / industry voices / community sources → sourced findings.md). It does not capture problem-space or tech-context Q&A. So even teams using `/research` start downstream planning without a structured product+tech context document.

## Goals & non-goals

### Goals

1. Provide a Shield-native PRD authoring command with a defensible default scaffold and support for custom team templates.
2. Provide a Shield-native PRD review command that ingests external PRDs (file, paste, Notion, URL), produces a multi-persona scored gap analysis with severity tiers, and outputs an enhanced version with suggested fixes.
3. Extend `/research` so its first phase is structured Q&A (product + tech) with repo auto-detect; preserve existing external evidence-gathering as an opt-in Phase 2.
4. Keep all new steps optional and skippable. Downstream commands consume earlier artifacts if present.
5. Match existing Shield conventions: feature-folder layout, manifest + index.html dashboard, plan-review scoring rubric, multi-persona dispatch.

### Non-goals

- Replace `/plan`. The technical breakdown stays in `/plan`. PRDs capture *what + why + how-much*; `/plan` captures *how + which-files + what-tests*.
- Replace `/research`'s existing external evidence-gathering. That capability is preserved as Phase 2.
- Build a discovery command separate from `/research`. Earlier exploration that proposed `/discovery` was rejected as a naming/concept overlap with `/research`; both are now phases of one command.
- Enforce a workflow. Every step is skippable. Users can run any command without prior steps.

## Success metrics

| Metric | Type | Target |
|---|---|---|
| Adoption — `/prd-review` runs / week per active project | Leading (usage) | 1+ within 30 days of release |
| Adoption — `/prd` runs / week per active project | Leading (usage) | 1+ within 60 days of release |
| Quality — average composite verdict on `/prd-review` output | Lagging (impact) | Trends toward "Ready" over time as teams iterate |
| Friction — % of `/research` Phase 1 questions auto-answered from repo+context | Operational | ≥ 40% (i.e., users answer < 60% of theoretical max) |
| Counter-metric — feature folders with PRD but no `/plan` follow-up | Leading | Should NOT exceed 20% (would indicate PRDs that go nowhere) |

## User stories & scenarios

### Story 1 — Reviewing an external PRD

**Persona:** Engineering lead at a team with PMs who write PRDs in Notion.

> Given a Notion PRD URL,
> when I run `/prd-review <url>`,
> then Shield fetches and snapshots the PRD, detects whether it's a lean or standard PRD and confirms with me, dispatches PM / tech-lead / DX reviewer agents in parallel against a 12-dimension rubric, and produces:
> - `summary.md` with composite verdict, persona grades, dimension grades, and severity-tiered gaps (P0/P1/P2)
> - `enhanced-prd.md` with my original PRD plus suggested fixes inline
> - `detailed/<persona>.md` per reviewer with citations to named PM authorities for skeptics

### Story 2 — Authoring a new PRD

**Persona:** PM or tech lead drafting a feature PRD.

> Given a feature topic and an optional `/research` transcript,
> when I run `/prd`,
> then Shield asks me which PRD type (standard vs lean), pulls answers from the transcript and repo where possible, walks me through the 12-section scaffold, and writes:
> - `prd.md` (source of truth)
> - `prd.html` (rendered)
> - `prd.meta.json` (type, status, owner, last-updated, sections-present map)

> When I previously wrote a lean PRD and scope has grown,
> and I run `/prd` again,
> then Shield offers: upgrade to standard / add specific sections / start fresh / cancel. Picking upgrade or add-sections creates a new run folder, carries forward existing content, and walks me through filling new sections.

### Story 3 — Authoring a PRD with a custom team template

**Persona:** Org with an established Confluence/Notion PRD format.

> Given my team's PRD template at `./docs/templates/our-prd.md` (referenced in `.shield.json`),
> when I run `/prd`,
> then Shield uses my template as the structure, parses its `##` headings, identifies any required sections it lacks (Problem, Goals & non-goals, Success metrics, Out of scope, Open questions), appends those with `<!-- Shield: added required section -->` markers, reports the additions, and proceeds with authoring.

### Story 4 — Researching with repo context

**Persona:** Engineer working in an existing codebase.

> Given an existing codebase with package manifests, deployment configs, CLAUDE.md, and prior Shield artifacts,
> when I run `/research <topic>`,
> then Shield silently scans the repo to detect tech stack, integrations, deployment pattern, compliance markers, and recent activity, surfaces the detected context for me to confirm or correct, asks only the Q&A questions not already covered, and produces a transcript organized by product topics (Problem, Users, Evidence, Alternatives, Success criteria, Why now) and tech topics (Existing systems, Constraints, Integration points, Risks, Open questions).
> Shield then surfaces open questions and offers Phase 2 (existing 3-agent external evidence-gathering) on those specific questions only.

## Functional requirements

### `/prd-review`

```gherkin
Feature: PRD review

  Scenario: Review a local file
    Given a markdown file at <path>
    When I run /prd-review <path>
    Then the file is snapshotted to source-prd.md
    And type is detected (lean | standard) and confirmed with the user
    And PM, tech-lead, and DX reviewer agents run in parallel
    And summary.md, enhanced-prd.md, and detailed/<persona>.md are written

  Scenario: Review a Notion URL
    Given a Notion page URL
    When I run /prd-review <url>
    Then the Notion MCP server is used to fetch the page content
    And content is converted to markdown and snapshotted
    And review proceeds as for a local file

  Scenario: Review a generic URL
    Given any HTTP(S) URL
    When I run /prd-review <url>
    Then WebFetch retrieves the content
    And it is converted to markdown and snapshotted
    And review proceeds as for a local file

  Scenario: Review pasted content
    Given the user has pasted PRD content into the prompt
    When I run /prd-review (no source argument)
    Then the pasted content is captured and snapshotted to source-prd.md
    And review proceeds as for a local file

  Scenario: No source argument
    When I run /prd-review with no argument and no pasted content
    Then Shield prompts the user for a source

  Scenario: Lean PRD review
    Given a source PRD that has only Problem, Goals, Metrics, Open Questions
    When I run /prd-review
    Then Shield detects it as lean, confirms with the user
    And dimensions 5, 6, 9, 10, 11 are weighted as informational, not blocking
    And the rubric output reflects the lean variant
```

### `/prd`

```gherkin
Feature: PRD authoring

  Scenario: New PRD, no prior context
    When I run /prd <topic>
    Then Shield asks for the PRD type (standard | lean)
    And walks the user through the 12-section scaffold (or 7-section lean variant)
    And writes prd.md, prd.html, prd.meta.json to a new run folder

  Scenario: New PRD with prior research
    Given a /research transcript exists in the feature folder
    When I run /prd
    Then Shield reads the transcript and pre-populates Problem, Users, Constraints, Existing systems
    And only asks for sections not derivable from the transcript

  Scenario: Custom template via .shield.json
    Given .shield.json has prd_template: "./docs/templates/our-prd.md"
    When I run /prd
    Then Shield loads the custom template
    And parses its ## headings
    And appends any missing required sections (Problem, Goals & non-goals, Success metrics, Out of scope, Open questions)
    And reports "Augmented your template with: <list>"
    And proceeds with authoring against the merged template

  Scenario: Lean PRD footer
    Given the user picked lean type
    When the PRD is written
    Then prd.md ends with a footer listing the standard sections that are intentionally omitted
    And prd.meta.json records type=lean and sections_missing=[...]

  Scenario: Upgrade lean to standard
    Given a lean PRD exists in the feature folder
    When I run /prd again
    Then Shield offers: upgrade to standard / add specific sections / start fresh / cancel
    And picking upgrade carries forward existing content into a new run folder
    And walks the user through filling the missing sections
    And the original lean run folder is preserved
```

### `/research` (extended)

```gherkin
Feature: Research with Q&A and external evidence

  Scenario: Phase 1 starts with repo scan
    When I run /research <topic>
    Then Shield scans package manifests, deployment configs, CLAUDE.md, docs/, prior artifacts, git log
    And surfaces detected tech stack, integrations, compliance markers, deployment pattern
    And asks the user to confirm or correct

  Scenario: Q&A with skip rules
    Given Shield has invocation context, repo scan, and prior /research transcript
    When the Q&A walk runs
    Then questions answered by any of these are auto-filled and shown as "✓ <topic>: <answer>"
    And only unanswered or partially-answered questions are asked

  Scenario: Skip is always valid
    When the user replies "skip" or "I don't know" to any question
    Then Shield records [unanswered] for that field
    And surfaces it as an Open Question in the transcript

  Scenario: Depth modes
    Given .shield.json sets research_depth (lean | standard | deep)
    When /research runs
    Then the question set matches the depth mode
    Or, if no setting, Shield auto-suggests a depth based on topic signals (small scope → lean, compliance/migration → deep) and lets the user override

  Scenario: Phase 2 trigger
    Given Phase 1 surfaced open questions
    When Phase 1 completes
    Then Shield offers: run external evidence-gathering on these / no / pick specific
    And only the chosen questions are passed to the existing 3-agent flow
    And findings are written to findings.md alongside transcript.md
```

## Non-functional requirements

| NFR | Requirement |
|---|---|
| Performance | `/prd-review` of a 5-page PRD must complete in ≤ 3 minutes (3 parallel agents). `/prd` Q&A walk is human-paced; no SLA on total wall time. `/research` repo scan must complete in ≤ 30 seconds for a typical repo. |
| Reproducibility | All ingest sources (file, paste, Notion, URL) snapshot to `source-prd.md` so re-runs are deterministic given the same source. |
| Privacy | No content from the user's repo or PRDs leaves Shield's process. External evidence-gathering (existing `/research` Phase 2) is unchanged in privacy posture. |
| Accessibility | Generated HTML uses the same conventions as existing `/plan` output (semantic headings, max-width 900-960px, blue accent). |
| Error handling | Notion fetch failure, URL fetch failure, malformed source PRDs: Shield reports the error and prompts for a different source. Never produces a partial or silent review. |
| Telemetry / events | Manifest entries for new artifacts (PRD, PRD review, research transcript) appear in `index.html` dashboard with type, verdict (where applicable), date. |

## Dependencies & assumptions

### Dependencies

- **Notion MCP server** — already installed in the Shield plugin context. Used by `/prd-review` for Notion URL ingestion.
- **WebFetch tool** — used for generic URL ingestion in `/prd-review` and could be reused inside `/research` Phase 2 (no change to existing behavior).
- **Existing `shield:product-manager-reviewer` agent** — used in PM reviewer dispatch for `/prd-review`.
- **Existing scoring infrastructure** in `shield/skills/general/plan-review/scoring.md` — reused with the same A-F grade scale and weighted-composite formula. PM weight = 1.0 for PRD reviews (vs 0.7 in plan reviews) since PRDs are product docs.

### Assumptions

- Shield users either have or will write PRDs; the value proposition of `/prd-review` is strong even for users who will never use `/prd` (they bring an existing PRD in from another tool).
- Repo auto-detect heuristics (`package.json`, `pom.xml`, etc.) cover ≥ 80% of Shield user projects. Edge cases proceed with manual Q&A.
- Teams with custom PRD templates will configure `prd_template` in `.shield.json`; custom-template merging logic preserves their additions and only appends missing required sections.

## Rollout plan

### Phasing

Three phases, each independently shippable with its own marketplace version bump. Per CLAUDE.md: bump `shield` version in `.claude-plugin/marketplace.json` only.

1. **Phase A — `/prd-review`** (highest immediate value, lowest competition)
   - New skill: `shield/skills/general/prd-review/`
   - New command: `shield/commands/prd-review.md`
   - Multi-persona dispatch (PM, tech-lead, DX) reusing existing scoring infra
   - Ingest pipeline: file / paste / Notion / URL → markdown → snapshot
   - Type detection (lean / standard) with user confirmation
   - 12-dimension rubric with severity-tiered output
   - **Kill-switch:** ship behind a feature flag in `.shield.json`? No — Shield commands are inherently opt-in (user chooses to invoke). Rollback = revert the commit and bump the version back.

2. **Phase B — `/prd`** (after Phase A is in user hands)
   - New skill: `shield/skills/general/prd-docs/`
   - New command: `shield/commands/prd.md`
   - 12-section problem-first scaffold + lean variant
   - PRD-type asked at generation time (no config)
   - Custom-template merging
   - Lean → standard upgrade flow
   - HTML rendering reusing existing plan-docs CSS / blue accent
   - **Kill-switch:** same as Phase A — revert commit if necessary.

3. **Phase C — `/research` Phase 1 enhancement** (after Phases A and B)
   - Update `shield/skills/general/research/SKILL.md` to describe two-phase flow
   - New supporting docs: `repo-scan.md`, `qa-topics.md` in the research skill folder
   - Update `shield/commands/research.md` to reflect two-phase behavior
   - Phase 2 (existing external evidence-gathering) preserved unchanged
   - **Kill-switch:** Phase 1 is additive; if it produces noisy or wrong Q&A, the user can still skip questions or use the existing Phase 2 only. Hard rollback = revert the commit.

### Per-phase abort criteria

Abort and revert if:
- Multi-persona dispatch latency exceeds 5 minutes for typical PRDs
- Repo auto-detect surfaces > 30% false-positive rate (wrong stack, wrong integrations)
- Custom-template merging clobbers user content (any test failure here is a P0)

### Migration

No migration needed. Existing feature folders are unchanged; new subfolders (`prd/`, `prd-review/`) are added when first used. `manifest.json` schema accepts new entries without breaking old ones.

## Open questions

| # | Question | Owner | Notes |
|---|---|---|---|
| 1 | Should `/prd-review` enhanced-prd.md make inline edits or use comments? | Phase A implementation | Inline edits = cleaner; comments = preserves original. Suggest comments-first, evaluate. |
| 2 | Lean rubric — exactly which dimensions are "informational" vs "warning"? | Phase A implementation | Draft: dims 5, 6, 9, 10, 11 informational for lean. Validate against real lean PRDs. |
| 3 | Repo-scan output format inside `transcript.md` | Phase C implementation | Suggest a "Detected Context" header section before the Q&A sections. |
| 4 | Should `/prd` upgrade flow let user select sections to add, or force all-or-nothing? | Phase B implementation | Design says "add specific sections" — keep it. Validate UX before shipping. |
| 5 | Where does Notion MCP authentication live? | Phase A implementation | Existing Notion MCP setup in `~/.claude/plugins/cache/...` should suffice; document the dependency. |

## Out of scope

- **`/discovery` as a separate command.** Explicitly rejected after exploration; merged into `/research` Phase 1.
- **Discovery review (gap analysis on a discovery transcript).** Discovery is exploratory; gaps are not a meaningful concept for it.
- **A `/prd` command argument for type or template path.** Type is asked interactively; template path lives in `.shield.json`.
- **Replacing or modifying `/plan`'s output.** `/plan` continues to consume `prd.md` as context if present, but its sidecar/architecture/plan HTML are unchanged.
- **Replacing the existing `/research` external evidence-gathering.** It is preserved as Phase 2.
- **Per-persona feature flags.** All three personas (PM, tech-lead, DX) run together; users who want a single-persona review can invoke the underlying agent directly.
- **Project-management sync for PRDs.** `/pm-sync` continues to operate on plan stories; PRDs are documents, not work items.
- **Version-controlled PRD diffs across runs.** Git already provides this; Shield does not need a custom diff tool.

## Architecture summary

### Folder structure (per feature)

```
{output_dir}/{feature}-YYYYMMDD/
├── manifest.json
├── plan.json                     ← existing, unchanged
├── research/
│   └── {N}-{slug}/
│       ├── transcript.md         ← Phase 1 Q&A + repo scan summary (new)
│       └── findings.md           ← Phase 2 external evidence (existing — only if Phase 2 ran)
├── prd/
│   └── {N}-{slug}/
│       ├── prd.md
│       ├── prd.html
│       └── prd.meta.json
├── prd-review/
│   └── {N}-{slug}/
│       ├── summary.md
│       ├── enhanced-prd.md
│       ├── source-prd.md
│       └── detailed/
│           ├── pm-reviewer.md
│           ├── tech-lead.md
│           └── dx-reviewer.md
├── plan/                         ← existing, unchanged
└── plan-review/                  ← existing, unchanged
```

### Skills layout

```
shield/skills/general/
├── prd-docs/                     ← new (Phase B)
│   ├── SKILL.md
│   ├── templates.md              ← 12-section default + lean variant + HTML render
│   ├── meta-schema.md            ← prd.meta.json schema
│   └── type-detection.md         ← lean vs standard heuristics
├── prd-review/                   ← new (Phase A)
│   ├── SKILL.md
│   ├── personas.md               ← PM, tech-lead, DX dispatch prompts
│   ├── rubric.md                 ← 12 dimensions, evaluation points, severity, citations
│   ├── ingest.md                 ← file/paste/Notion/URL → markdown pipeline
│   └── scoring.md                ← per-dim → per-persona → composite, P0/P1/P2
├── research/                     ← existing — extended (Phase C)
│   ├── SKILL.md                  ← updated: two-phase flow
│   ├── repo-scan.md              ← new — what to detect, how
│   └── qa-topics.md              ← new — product + tech topic catalog with skip rules
├── plan-docs/                    ← existing — minor update to consume prd.md as context
└── plan-review/                  ← existing — minor update to consume prd.meta.json
```

### `.shield.json` additions (all optional, sensibly defaulted)

```json
{
  "prd_template": "./docs/templates/our-prd.md",
  "prd_required_sections": [
    "Problem", "Goals & non-goals", "Success metrics",
    "Out of scope", "Open questions"
  ],
  "prd_review_personas": ["pm", "tech-lead", "dx"],
  "research_depth": "standard"
}
```

Defaults if absent:
- `prd_template` → built-in 12-section scaffold (problem-first)
- `prd_required_sections` → as listed above
- `prd_review_personas` → all three
- `research_depth` → `standard`

### Default PRD scaffold (problem-first, 12 sections)

```
# <Feature name>

## Header
Owner · Status · PRD type · Last updated · Linked discovery/research

## Problem & context
What's broken, who hurts, baseline data, why now (cost-of-inaction)

## Target users / personas
Named segments with size/scale; primary vs secondary

## Goals & non-goals
What success looks like; what we're explicitly NOT trying to do

## Success metrics
Leading + lagging + threshold + dashboard plan + counter-metric

## User stories & scenarios
Per persona; happy path + edge cases + error states

## Functional requirements
Given/When/Then per story; prioritized

## Non-functional requirements
Performance, security, accessibility, privacy, telemetry

## Dependencies & assumptions
Internal services, third parties, integration contracts, validated assumptions

## Rollout plan
Flag plan, canary, kill-switch, abort thresholds, rollback criteria

## Open questions
Tracked, owned, dated

## Out of scope / Non-goals
Named items with one-line rationale
```

### Lean variant (7 sections)

Header, Problem, Users, Goals, Metrics, Open Questions, Out of scope.

Lean PRDs include a footer listing the standard sections they intentionally omit and pointing to the upgrade flow.

### `/prd-review` rubric (12 dimensions)

| # | Dimension | Owner |
|---|---|---|
| 1 | Problem clarity | PM |
| 2 | Scope boundaries | PM |
| 3 | Measurable success | PM |
| 4 | AC testability | Tech-lead |
| 5 | NFR coverage | Tech-lead |
| 6 | Rollout & ops | Tech-lead |
| 7 | RACI & approvals | PM |
| 8 | Legal / privacy / compliance | PM |
| 9 | GTM / customer-comms | PM |
| 10 | Support / CX impact | PM |
| 11 | i18n / l10n | PM |
| 12 | Why now & cost-of-inaction | PM |

Anti-patterns flagged separately: solution-first ordering, vague language, single-metric-no-counter, missing rollout, missing status/owner header.

### Scoring (aligned with `plan-review/scoring.md`)

- **Per evaluation point:** A (4) / B (3) / C (2) / D (1) / F (0)
- **Per dimension:** average of points, rounded to letter
- **Per persona:** average of dimensions, rounded to letter
- **Composite:** weighted average of activated personas

Persona weights for `/prd-review`:

| Persona | Weight | Role |
|---|---|---|
| PM reviewer | 1.0 | Core |
| Tech-lead reviewer | 1.0 | Core |
| DX reviewer | 0.7 | Supporting |

Verdicts (same as plan-review): ≥ 2.5 Ready · 1.5–2.4 Needs Work · < 1.5 Not Ready.
Priorities (same model): P0 = D/F on Critical · P1 = C/D on Important · P2 = C on Warning.

Citations to named PM authorities (Cagan, Lenny, Shreyas, Plane.so, Routine.co, Atlassian, Shape Up, etc.) appear:
- **Once** in the rubric documentation (`rubric.md`) as the foundation
- **In detailed/<persona>.md files** for skeptics or pushback
- **NOT in summary.md** — the executive view stays scannable

### `summary.md` shape

```markdown
# PRD Review: <feature>

**Reviewed:** <source>  ·  **Type:** standard  ·  **Verdict:** Needs Work (1.8)

## Persona grades
| Persona | Grade | Weight |
| PM reviewer       | C (2.1) | 1.0 |
| Tech-lead reviewer| D (1.4) | 1.0 |
| DX reviewer       | B (2.8) | 0.7 |

## Dimension grades
| # | Dimension | Grade | Owner |

## P0 — Blockers
- ...

## P1 — Important
- ...

## P2 — Nice to have
- ...

## Anti-patterns
- ...
```

## References

- Existing research that informed this design: `/Users/apple/research/prd/docs/shield/prd-skill-20260508/research/1-prd-best-practices-and-coverage/findings.md`
- Figma's PRD approach (initial reference, superseded by the 12-section scaffold from the research): https://coda.io/@yuhki/figmas-approach-to-product-requirement-docs/prd-name-of-project-1
- Existing Shield skills: `shield/skills/general/plan-docs/`, `shield/skills/general/plan-review/`, `shield/skills/general/research/`
- Project conventions: `/Users/apple/projects/infraspecdev/tesseract/CLAUDE.md`
