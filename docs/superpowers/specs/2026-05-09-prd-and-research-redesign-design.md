# PRD-and-Research Redesign — Design Doc

**Status:** Draft
**Date:** 2026-05-09
**Author:** ashwinimanoj
**Plugin:** shield

---

## TL;DR

Introduce a product-requirements layer to Shield, sitting between research and technical planning. Two new commands (`/prd`, `/prd-review`) plus an enhancement to the existing `/research` command. All steps optional; each command consumes earlier artifacts as context if present.

**New flow:** `/research` (Q&A + optional external evidence) → `/prd` (or `/prd-review` for existing) → `/plan` → `/plan-review` → `/implement`.

**Shipping order (3 phases):**
1. `/prd-review` — multi-persona scored gap analysis on an ingested PRD. Highest immediate value, lowest competition vs. existing tools.
2. `/prd` — author mode with 17-section problem-first scaffold (mirrors the 13-dimension rubric so every dim has a home; lean variant collapses to 7 sections), custom-template merging via `.shield.json`, lean→standard upgrade flow. Plus an inline story template (happy path, error paths, edge cases, state transitions, cross-functional handoffs, Given/When/Then ACs).
3. `/research` Phase 1 — repo auto-detect + structured product+tech Q&A; existing external evidence-gathering becomes opt-in Phase 2.

**Load-bearing design decisions:**
- **Generic ingest.** No cloud provider baked in. Shield classifies input (local file / URL / paste), and for URLs consults an internal known-host map + runtime MCP discovery. Universal paste fallback. Adding a new tool is data, not code.
- **13-dimension rubric** for `/prd-review` covering problem clarity, scope, metrics, scenario coverage & AC testability, NFRs, rollout, RACI, legal/privacy, GTM, support, why-now, risks & assumptions, cost. (i18n/l10n is absorbed into NFR + ACs rather than a standalone dimension.) Dispatched across five reviewer agents in parallel: PM, **agile-coach** (story/AC quality), tech-lead, DX, cost-reviewer.
- **Three dimension states**: graded (A-F, counted), N/A (excluded with mandatory reasoning), informational (lean-PRD structural exemptions, excluded). Bare N/A grades F.
- **P0-gate on verdict**: composite alone can drown out a fatal gap; any P0 caps the verdict at "Needs Work" regardless of score. Header shows "Needs Work (composite X.X, blocked by N P0s)".
- **Canonical comments export** (`review-comments.json` + auto-generated `review-comments.md`) for converting Shield feedback into GitHub/Notion/Confluence/Jira comments via external converters.
- **Source PRD never overwritten.** `enhanced-prd.md` is always a copy; "Use as Shield's canonical PRD" copies it to `prd/{N}/prd.md`.

**Scoring** aligned with `plan-review/scoring.md` (A-F per evaluation point, weighted-average composite). Persona weights: PM 1.0, agile-coach 1.0, tech-lead 1.0, DX 0.7, cost-reviewer 0.7. P0-gate is a follow-up to also apply to `plan-review`.

**PRD-to-Plan linkage.** `prd.meta.json` records `linked_plans: [...]`; `plan.json` records `source_prd: ...` and `prd_rubric_version_at_planning`. Bidirectional traceability auto-populated when `/plan` runs.

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
2. Provide a Shield-native PRD review command that ingests external PRDs from any source (local file, pasted content, or any URL whose handler is available at runtime), produces a multi-persona scored gap analysis with severity tiers, and outputs an enhanced version with suggested fixes.
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
> then Shield fetches and snapshots the PRD, detects whether it's a lean or standard PRD and confirms with me, dispatches PM / agile-coach / tech-lead / DX / cost reviewer agents in parallel against a 13-dimension rubric, and produces:
> - `summary.md` with composite verdict, persona grades, dimension grades, and severity-tiered gaps (P0/P1/P2)
> - `enhanced-prd.md` with my original PRD plus suggested fixes inline
> - `detailed/<persona>.md` per reviewer with citations to named PM authorities for skeptics

### Story 2 — Authoring a new PRD

**Persona:** PM or tech lead drafting a feature PRD.

> Given a feature topic and an optional `/research` transcript,
> when I run `/prd`,
> then Shield asks me which PRD type (standard vs lean), pulls answers from the transcript and repo where possible, walks me through the 17-section scaffold, and writes:
> - `prd.md` (source of truth)
> - `prd.html` (rendered)
> - `prd.meta.json` (type, status, owner, last-updated, sections-present map)

> When I previously wrote a lean PRD and scope has grown,
> and I run `/prd` again,
> then Shield offers a multi-select prompt with all 5 missing standard sections pre-checked (uncheck to skip any), plus "Start fresh" and "Cancel". Picking add-sections creates a new run folder, carries forward existing content, and walks me through filling each newly-added section.

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

  Scenario: Review a URL (runtime resolver detection)
    Given any HTTP(S) URL
    When I run /prd-review <url>
    Then Shield classifies the input as a URL
    And matches the URL host pattern against its internal known-host map
    And looks for a matching MCP among those available in the current session at runtime
    And if found, uses that MCP to fetch the page
    Or if the URL has no internal map entry, or no matching MCP is available, falls through to WebFetch
    Or if .shield.json has a custom prd_ingest_resolvers entry matching the URL, uses the named MCP
    And content is converted to markdown and snapshotted to source-prd.md
    And review proceeds as for a local file

  Scenario: Ingest handler failure → paste fallback
    Given a URL whose resolver (matched MCP or WebFetch) is unavailable, unauthenticated, or returns an error
    When I run /prd-review <url>
    Then Shield reports the specific error ("Notion MCP not authenticated", "URL returned 403", "Atlassian MCP not present", etc.)
    And offers a paste fallback in the same turn
    And the user can drop the content into the prompt; Shield proceeds as for pasted content

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
    And dimensions 5 (NFR), 6 (Rollout), 9 (GTM), 10 (Support), 13 (Cost) are informational (not graded)
    And dimensions 1, 2, 3, 4, 7, 8, 11, 12 are graded
    And the composite verdict is computed over the 8 graded dimensions only
    And informational gaps appear under "## Informational" in summary.md with severity="informational" in review-comments.json

  Scenario: Reviewer marks a dimension N/A (with reasoning)
    Given the feature genuinely doesn't trigger a dimension (e.g., an internal cron job with no user surface for GTM, no support flow, and no cost budget yet)
    When the reviewer evaluates that dimension
    Then it is graded "N/A" with a one-line reasoning, e.g., "N/A — no user-facing surface"
    And it appears under "## Not applicable (excluded from score)" in summary.md
    And it is tagged severity="n/a" in review-comments.json with the reasoning in the comment field
    And it is excluded from the composite (numerator and denominator)

  Scenario: PRD author declares N/A; reviewer evaluates the claim
    Given the PRD contains "N/A — <reasoning>" under a dimension's section
    When /prd-review processes that section
    Then if the reasoning is plausible, the reviewer confirms N/A
    Or if the reasoning is implausible (e.g., GTM declared N/A for a customer-facing pricing change), the reviewer overrides and grades the dimension normally
    And the override is noted in the reviewer's detailed report

  Scenario: Bare N/A without reasoning is treated as F
    Given a PRD contains "N/A" with no reasoning under a dimension's section
    When /prd-review processes that section
    Then the dimension is graded F (not excluded)
    And the comment notes "N/A claimed without reasoning — please add one-line justification"

  Scenario: P0 floor on the verdict (averaging-problem guard)
    Given the composite score computes to >= 2.5
    And one or more dimensions are graded F on a Critical evaluation point (producing P0s)
    When the verdict is determined
    Then the verdict is "Needs Work" (NOT "Ready") regardless of composite
    And summary.md header reads "Needs Work (composite <X.X>, blocked by <N> P0s)"
    And the composite score is still shown for tracking improvement over time
```

### `/prd`

```gherkin
Feature: PRD authoring

  Scenario: New PRD, no prior context
    When I run /prd <topic>
    Then Shield asks for the PRD type (standard | lean)
    And walks the user through the 17-section scaffold (or 7-section lean variant)
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

  Scenario: Add sections to a lean PRD
    Given a lean PRD exists in the feature folder
    When I run /prd again
    Then Shield presents a multi-select prompt of all standard sections missing from the lean PRD (all pre-checked by default)
    And user can uncheck sections to skip, or pick "Start fresh" or "Cancel"
    And the selected sections are added; a focused Q&A pass runs for each newly-added section only
    And the new PRD is written to a new run folder (prd/{N+1}/), carrying forward existing content
    And the original lean run folder is preserved at prd/{N}/
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
| Reproducibility | All ingest sources (local file, paste, any URL) snapshot to `source-prd.md` so re-runs are deterministic given the same source. |
| Privacy | No content from the user's repo or PRDs leaves Shield's process. External evidence-gathering (existing `/research` Phase 2) is unchanged in privacy posture. |
| Accessibility | Generated HTML uses the same conventions as existing `/plan` output (semantic headings, max-width 900-960px, blue accent). |
| Error handling | Resolver failure (MCP unavailable, auth required, network error), unreachable URLs, malformed source PRDs: Shield reports the specific error and offers a paste fallback. Never produces a partial or silent review. |
| Telemetry / events | Manifest entries for new artifacts (PRD, PRD review, research transcript) appear in `index.html` dashboard with type, verdict (where applicable), date. |

## Dependencies & assumptions

### Dependencies

- **Ingest is fully generic** — `/prd-review` classifies input as one of: local path, HTTP(S) URL, or paste content. No provider is baked in as "default." For URLs, Shield consults an **internal known-host map** (URL pattern → MCP-name pattern) and resolves at runtime by checking which MCPs are present in the session. If a matching MCP exists, it's used. If not, Shield falls through to WebFetch (for public URLs), then to paste fallback (universal). Authentication is each MCP's own concern (its `authenticate` / `complete_authentication` flow), not Shield's. Read tool handles local files natively (md, txt, pdf). Teams with non-mainstream tools can add custom resolver entries to `.shield.json` (`prd_ingest_resolvers`); the default list is empty. See *Architecture summary → Ingest dispatch* for the full model.
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
   - Multi-persona dispatch (PM, agile-coach, tech-lead, DX, cost reviewer) reusing existing scoring infra
   - Ingest pipeline: local file / paste / any URL (resolved at runtime) → markdown → snapshot
   - Type detection (lean / standard) with user confirmation
   - 13-dimension rubric with severity-tiered output
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

All design-phase open questions have been resolved and folded into the relevant sections of this spec. The resolutions:

| # | Question | Decision | Details in |
|---|---|---|---|
| 1 | `enhanced-prd.md` shape | Mirror `plan-review` convention: P0/P1 inline with `<!-- [from: <Persona>] -->` attribution, P2 as comments. Never overwrites source. Optional `enhanced-prd.<ext>` conversion back to source format. New `review-comments.json` + auto-generated `review-comments.md` for tool-export. | Architecture summary → Enhanced PRD output and comments export |
| 2 | Lean rubric — graded vs informational | Lean: dims 1-4, 7, 8, 12 graded (7); dims 5, 6, 9, 10, 11 informational (5). Standard: all 12 graded. Informational entries surfaced but excluded from composite. | Architecture summary → Lean rubric — graded vs informational |
| 3 | Repo-scan output in `transcript.md` | `## Detected Context` section at top, subsectioned (Stack, Integrations, Compliance, Deployment, Recent activity). Each entry tagged `(detected) / (confirmed) / (corrected by user) / (manual)` with source citation. | Architecture summary → Repo-scan and transcript format |
| 4 | `/prd` upgrade flow shape | Single multi-select prompt (all missing sections pre-checked) + Start-fresh + Cancel. Selected sections added to a new run folder; original preserved. | Functional requirements → `/prd` Scenario: Add sections to a lean PRD |
| 5 | Resolver authentication | Shield doesn't bake in providers as "defaults." For URLs, Shield consults an internal known-host map and resolves at runtime to whichever MCP is available. Auth is each MCP's own concern. On any resolver failure (MCP missing, auth required, network error), Shield offers a universal paste fallback. Local files use Read directly. | Dependencies & assumptions · Architecture summary → Ingest dispatch |

Implementation-phase open questions (if any surface) will be tracked in each phase's implementation plan, not here.

## Out of scope

- **`/discovery` as a separate command.** Explicitly rejected after exploration; merged into `/research` Phase 1.
- **Discovery review (gap analysis on a discovery transcript).** Discovery is exploratory; gaps are not a meaningful concept for it.
- **A `/prd` command argument for type or template path.** Type is asked interactively; template path lives in `.shield.json`.
- **Replacing or modifying `/plan`'s output.** `/plan` continues to consume `prd.md` as context if present, but its sidecar/architecture/plan HTML are unchanged.
- **Replacing the existing `/research` external evidence-gathering.** It is preserved as Phase 2.
- **Per-persona feature flags.** All five personas (PM, agile-coach, tech-lead, DX, cost) run together; users who want a single-persona review can invoke the underlying agent directly.
- **Project-management sync for PRDs.** `/pm-sync` continues to operate on plan stories; PRDs are documents, not work items.
- **Version-controlled PRD diffs across runs.** Git already provides this; Shield does not need a custom diff tool.

## Known limitations

Accepted limitations of what's being built. These are real, but addressing them isn't worth blocking Phase A on. Documented so users know what to expect.

- **Massive PRDs (>50 pages / >50K characters).** Ingestion sends the full content to reviewer agents. Beyond ~50 pages, latency degrades and quality may suffer. Workaround: split into multiple PRDs (per epic).
- **Embedded images / diagrams.** When ingesting from Notion / Confluence / Google Docs / etc., MCPs typically convert pages to markdown and lose image fidelity. Images surface as `[image: alt-text]` placeholders. Visual content is not reviewable in Phase A.
- **Sensitive / confidential content.** PRD content flows through the LLM. Teams with strict data-handling requirements may not be able to use URL ingestion. Workarounds: paste fallback (still goes through LLM), or wait for Phase D `prd_review_offline_only: true` (future).
- **Multi-language PRDs.** Rubric and reviewer agents assume English. Non-English PRDs are not formally supported in Phase A — reviews may proceed but quality is not guaranteed.
- **DOCX / non-markdown formats.** Read tool natively handles markdown, txt, pdf. DOCX requires paste fallback (user converts to markdown).

## Future enhancements

Items deliberately deferred but tracked for later phases.

- **PRD-author N/A declaration UX.** Phase A treats author-declared N/A as overridable by the reviewer; later phases could surface N/A claims as a structured field with reasoning prompts in `/prd`.
- **Re-review diff** (compare current `/prd-review` against prior run): "new gaps", "still-open gaps", "resolved gaps." Adds a learning loop. Phase B or C.
- **Sample / starter PRDs** shipped in `templates.md` so users see what good looks like, not just structural skeletons.
- **PRD status lifecycle** beyond `draft`: `in-review`, `approved`, `in-implementation`, `shipped`, `retired`. Recorded in `prd.meta.json`.
- **Configurable Shield attribution.** Some teams want clean output, no `<!-- [from: ...] -->` markers — `.shield.json` flag.
- **Index.html dashboard treatment** for PRDs: latest PRD per feature, status badge, link to most recent review, verdict trend.
- **Plan-review adopts the same P0-gate** verdict rule (tracked in the spec under Scoring's follow-up note).
- **Context federation** beyond repo scan: pull related runbooks (Confluence), tickets (Jira/Linear), dashboards (Datadog), design (Figma) via MCPs declared in `.shield.json` `context_sources`. Discussed but deferred.
- **`prd_review_offline_only`** mode for teams that can't send PRDs through external LLMs — refuses URL/Notion ingestion and requires local-LLM or refuses entirely.
- **Converters** that post `review-comments.json` back to GitHub PR review / Notion comments / Confluence inline comments / Jira via tool-specific helper scripts.
- **Multi-file PRD sources.** Some teams (like the bill-payments review case) split a PRD across `architecture.html` + `plan.html`. Phase A reviews one source; future enhancement: accept multiple files as one logical PRD.

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
│       ├── source-prd.md            ← verbatim snapshot of original source
│       ├── enhanced-prd.md          ← P0/P1 inline + P2 comments; never overwrites source
│       ├── enhanced-prd.<ext>       ← (optional) conversion back to source's original format
│       ├── review-comments.json     ← canonical structured per-section gap comments
│       ├── review-comments.md       ← auto-generated human view of the JSON
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
│   ├── personas.md               ← PM, agile-coach, tech-lead, DX, cost reviewer dispatch prompts
│   ├── rubric.md                 ← 13 dimensions, evaluation points per dimension (incl. 4a-4e scenario coverage; threat model; RBAC matrix under NFR; i18n under NFR; data migration; risks+mitigations; cost components), severity, citations
│   ├── ingest.md                 ← classification (local/URL/paste) + resolver chain + known-host map
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
  "prd_review_personas": ["pm", "agile-coach", "tech-lead", "dx", "cost"],
  "prd_ingest_resolvers": [
    { "pattern": "company-wiki.internal/*", "mcp": "internal-wiki-fetch" }
  ],
  "research_depth": "standard"
}
```

Defaults if absent:
- `prd_template` → built-in 17-section scaffold (problem-first; mirrors the 13-dimension rubric)
- `prd_required_sections` → as listed above
- `prd_review_personas` → all five
- `prd_ingest_resolvers` → `[]` (empty; Shield's internal known-host map handles mainstream tools at runtime)
- `research_depth` → `standard`

### Default PRD scaffold (problem-first, 17 sections — every rubric dimension has a home)

The standard scaffold now mirrors the 13-dimension rubric so authors aren't missing sections that reviewers will grade against. Lean PRDs collapse this dramatically (see Lean variant below).

```
# <Feature name>

## 1. Header                                    ← dim 7 (owner, decision-maker, sign-offs)
Owner · Status · PRD type · Date created · Last updated · Linked discovery/research
Decision-maker · Sign-off contacts (Legal, Security, Support)
Linked plans: <auto-populated by /plan>

## 2. Problem & context                         ← dim 1 + dim 11 (why now)
What's broken, who hurts, baseline data, why now (cost-of-inaction)

## 3. Target users / personas                   ← dim 1
Named segments with size/scale; primary vs secondary

## 4. Goals & non-goals                         ← dim 2
What success looks like; what we're explicitly NOT trying to do

## 5. Success metrics                           ← dim 3
Leading + lagging + threshold + dashboard plan + counter-metric

## 6. User stories & scenarios                  ← dim 4 (story-level)
Per persona. See story template below.

## 7. Functional requirements                   ← dim 4 (AC)
Given/When/Then per story; prioritized

## 8. Non-functional requirements               ← dim 5
Performance, security, accessibility, privacy, threat model / abuse cases,
telemetry / event schemas, RBAC / permissions matrix, i18n / l10n
(RTL, encoding, formats, translation pipeline)

## 9. Dependencies                              ← dim 5
Internal services, third parties, integration contracts

## 10. Risks & mitigations                      ← dim 12 (split from Assumptions)
Each risk: description · likelihood · impact · mitigation · owner

## 11. Assumptions                              ← dim 12
Validated vs unvalidated; what we're betting on

## 12. Rollout plan                             ← dim 6
Flag plan, canary, kill-switch, abort thresholds, rollback criteria,
data migration plan, backward compatibility commitments

## 13. Cost & resource impact                   ← dim 13 [NEW]
Build cost (eng-time estimate), run cost at projected scale
(compute, storage, bandwidth, $$/month), cost counter-metric

## 14. GTM & customer-comms                     ← dim 9 [NEW]
Pricing / packaging implications, in-app messaging plan,
release notes, CS enablement, sales/marketing collateral

## 15. Support / CX impact                      ← dim 10 [NEW]
Day-1 ticket owner, runbook, escalation path, sales enablement

## 16. Open questions
Tracked, owned, dated

## 17. Out of scope / Non-goals                 ← dim 2
Named items with one-line rationale
```

#### User story template (used inside Section 6)

```markdown
### Story <ID>: <name>
- **Persona:** <named persona>
- **Goal:** <user-language goal>
- **Happy path:** <numbered steps>
- **Error / timeout / abandon paths:** <branches>
- **Edge cases:** <enumeration — boundary conditions, concurrent state, partial failures>
- **State transitions:** <if applicable; diagram or table for non-trivial lifecycles>
- **Cross-functional handoffs:** <who/when downstream teams (CS, Finance, Legal) get pulled in>
- **Acceptance criteria (Given/When/Then):**
  - Given <pre> When <action> Then <outcome>
  - <repeat for each AC>
```

### Lean variant (7 sections)

Header, Problem & context, Users, Goals & non-goals, Success metrics, Open questions, Out of scope. Sections 6-15 of the standard scaffold (stories, FRs, NFRs, dependencies, risks, rollout, cost, GTM, support) are intentionally omitted.

Lean PRDs include a footer listing the standard sections they intentionally omit and pointing to the upgrade flow.

### PRD-to-Plan bidirectional linkage

`prd.meta.json` records which plans were generated from this PRD; `plan.json` records which PRD it implements. Both are auto-populated when `/plan` runs against a feature folder containing a PRD.

```json
// prd.meta.json
{
  "type": "standard",
  "status": "approved",
  "owner": "...",
  "last_updated": "...",
  "rubric_version": "1.0",
  "linked_plans": ["plan/1-foo-foundation/", "plan/2-foo-cutover/"]
}

// plan.json
{
  "source_prd": "prd/2-foo-v2/prd.md",
  "prd_rubric_version_at_planning": "1.0",
  ...
}
```

The `prd_rubric_version_at_planning` is recorded so re-runs can detect rubric drift (e.g., dim 13 was added later — older PRDs reviewed before that don't auto-fail on it).

### Ingest dispatch

Shield doesn't enumerate cloud providers. It runs three steps:

**1. Classify the input.**

| Class | Detection | Handler |
|---|---|---|
| Local file | Path doesn't match `^https?://` (starts with `/`, `./`, or a relative path) | Read tool — supports md, txt, pdf natively |
| HTTP(S) URL | Matches `^https?://` | Resolver chain (step 2) |
| Paste | No source argument; content from the prompt | Direct from prompt |

**2. For URLs, resolve at runtime.**

Shield consults an internal known-host map (URL pattern → MCP-name pattern), then checks which MCPs are actually present in the session.

| URL pattern | Looks for MCP matching | If not present |
|---|---|---|
| `notion.so/*` | `*notion*` | WebFetch → paste |
| `*.atlassian.net/wiki/*` | `*atlassian*` or `*confluence*` | WebFetch → paste |
| `docs.google.com/document/*` | `*google*drive*` or `*google*docs*` | WebFetch → paste |
| `github.com/*/blob/*` | (no MCP needed — uses `gh` CLI directly) | WebFetch |
| anything else | (no map entry) | WebFetch → paste |

This map is **internal Shield knowledge** — not user-facing config. The user never sees it. They give Shield a URL; Shield figures out whether any present MCP can handle it, and if not, falls through.

**3. Fall through universally.**

- WebFetch handles any public HTTP(S) URL (no auth required)
- Paste handles anything Shield can't reach — works for any document regardless of where it lives

**Custom resolvers (extension point, rarely needed).** Teams using non-mainstream tools (Coda, Quip, Box, internal wikis, custom MCPs) can add explicit rows to `.shield.json` `prd_ingest_resolvers`. The list is empty by default; Shield's internal map covers the mainstream cases. Custom entries are checked before WebFetch fallback:

```json
{
  "prd_ingest_resolvers": [
    { "pattern": "company-wiki.internal/*", "mcp": "internal-wiki-fetch" }
  ]
}
```

**Failure flow** (uniform): handler fails → Shield reports the specific error → offers paste fallback in the same turn → user pastes content → review proceeds.

**Why this is generic:**
- No provider is baked into Shield as "default."
- Adding support for a new cloud almost never requires code changes — if the org has an MCP and the URL is mainstream, Shield matches it at runtime; if the tool is exotic, the user adds a config row.
- Local files work for any format Read can open (md, txt, pdf). Other formats (docx, etc.) → paste fallback.
- The universal paste fallback means Shield never hard-fails on a document it can't reach.

### Repo-scan and transcript format

`/research` Phase 1 emits a `transcript.md` that opens with a `## Detected Context` section before the Q&A topics. Each entry is tagged with a confidence marker and a source citation in italics. Downstream `/prd` and `/plan` consume this section to pre-populate Existing systems, Dependencies, and Constraints.

| Tag | Meaning |
|---|---|
| `(confirmed)` | Shield detected AND user said yes |
| `(detected)` | Shield inferred from repo; user neither confirmed nor corrected |
| `(corrected by user)` | Shield's guess was wrong; this is the correction |
| `(manual)` | User added; Shield did not detect |

Sections inside `## Detected Context`: Stack, Integrations, Compliance markers, Deployment pattern, Recent activity. Each is bullet-list per item, with source citation (`— *from package.json*`, `— *git log*`, etc.).

After Detected Context, the transcript contains `## Product Context`, `## Technical Context`, `## Open Questions`, and (if Phase 2 ran) `## External Findings`. Heading structure is stable so downstream parsing is reliable.

### `/prd-review` rubric (13 dimensions)

| # | Dimension | Owner | Notable evaluation points |
|---|---|---|---|
| 1 | Problem clarity | PM | named user, baseline, why-now |
| 2 | Scope boundaries | PM | explicit Out-of-Scope present |
| 3 | Measurable success | PM | thresholds, leading + lagging, counter-metric, dashboard plan |
| 4 | **Scenario coverage & AC testability** | **Agile-coach** (`shield:agile-coach-reviewer`) | 4a: happy path AND error/timeout paths · 4b: edge cases enumerated · 4c: state transitions / lifecycle documented · 4d: cross-functional handoffs noted · 4e: ACs in Given/When/Then · plus the agile-coach's existing AC1-AC10 evaluation points (context, requirements, sprint-readiness, etc.) |
| 5 | NFR coverage | Tech-lead | perf, accessibility, privacy, security, **threat model / abuse cases**, **telemetry / event taxonomy completeness**, **RBAC / permissions matrix**, **i18n / l10n (system-level: RTL, encoding, formats, translation pipeline)** |
| 6 | Rollout & ops | Tech-lead | flag plan, canary, kill-switch, rollback criteria, **data migration & backward compatibility** |
| 7 | RACI & approvals | PM | named decision-maker, Legal/Security/Support sign-off path |
| 8 | Legal / privacy / compliance | PM | data classification, PII handling, regulated-industry sign-off |
| 9 | GTM / customer-comms | PM | pricing, packaging, in-app messaging, release notes, CS enablement |
| 10 | Support / CX impact | PM | Day-1 ticket owner, runbook, sales enablement |
| 11 | Why now & cost-of-inaction | PM | sequencing rationale, opportunity cost |
| 12 | **Risks & assumptions** | PM | risks enumerated WITH mitigations + owners; validated vs unvalidated assumptions distinguished |
| 13 | **Cost & resource impact** | **Cost reviewer** (`shield:cost-reviewer`) | build cost; run cost at projected scale (compute, storage, bandwidth, $$/month); cost counter-metric |

**Note on dim 11 (former i18n).** i18n/l10n was previously a standalone dimension but is absorbed into dim 5 NFR (system-level concerns: RTL, encoding, formats, translation pipeline) and dim 4 ACs (per-story copy variations). This drops the dimension count from 14 to 13.

Anti-patterns flagged separately: solution-first ordering, vague language, single-metric-no-counter, missing rollout, missing status/owner header, **risks without mitigations**, **happy-path-only scenarios**.

### Dimension states — graded, N/A, informational

Every dimension is in one of three states at review time. Only **graded** dimensions count toward the composite verdict.

| State | When | Effect on composite | Decision driver |
|---|---|---|---|
| **Graded** (A/B/C/D/F) | Dimension applies; reviewer evaluates content | Counted | Default |
| **N/A** | Dimension genuinely doesn't apply to this feature; reasoning required | Excluded | Per-PRD, per-dimension; reviewer judgment (may confirm or override the PRD author's declared N/A) |
| **Informational** | Lean-PRD structural exemption (dims 5, 6, 9, 10, 11) | Excluded | Per-PRD, automatic for lean type |

**N/A rules:**
- Reasoning is mandatory. Bare N/A (no justification) is treated as F.
- If the PRD author declares N/A under a dimension's section, the reviewer evaluates whether the claim is plausible. Implausible declarations are overridden and graded normally; the override is noted in the detailed report.
- If no declaration but the feature obviously doesn't trigger the dimension, the reviewer infers N/A and writes a one-line reason.

**Examples of plausible N/A:**
- Dim 9 (GTM) and 10 (Support): purely internal infrastructure changes
- Dim 8 (Legal/privacy): no user data, no regulated industry
- Dim 13 (Cost): pre-budget proof-of-concept; cost analysis pending
- Dim 5 evaluation point (i18n / l10n): English-only product, no internationalization roadmap

### Lean rubric — graded vs informational

For lean PRDs, 8 of the 13 dimensions are graded; the other 5 are surfaced as **informational** (gaps noted, but they don't drag the composite verdict).

| # | Dimension | Lean treatment | Standard treatment |
|---|---|---|---|
| 1 | Problem clarity | Graded | Graded |
| 2 | Scope boundaries | Graded | Graded |
| 3 | Measurable success | Graded | Graded |
| 4 | Scenario coverage & AC testability | Graded (bullets accepted; happy-path-only and prose-only ACs still flagged) | Graded (Given/When/Then expected; full scenario coverage including edges, state, cross-functional handoffs) |
| 5 | NFR coverage | **Informational** | Graded |
| 6 | Rollout & ops | **Informational** | Graded |
| 7 | RACI & approvals | Graded | Graded |
| 8 | Legal / privacy / compliance | Graded (A if N/A applies) | Graded |
| 9 | GTM / customer-comms | **Informational** | Graded |
| 10 | Support / CX impact | **Informational** | Graded |
| 11 | Why now & cost-of-inaction | Graded | Graded |
| 12 | Risks & assumptions | Graded | Graded |
| 13 | Cost & resource impact | **Informational** | Graded |

**Informational entries:**
- Surfaced in `summary.md` under an `## Informational` section (separate from P0/P1/P2)
- Tagged `severity: "informational"` in `review-comments.json`
- Excluded from the composite formula entirely (denominator is over graded dimensions only)

### Scoring (aligned with `plan-review/scoring.md`)

- **Per evaluation point:** A (4) / B (3) / C (2) / D (1) / F (0)
- **Per dimension:** average of points, rounded to letter — or **N/A** (excluded) or **informational** (excluded)
- **Per persona:** average of that persona's *graded* dimensions, rounded to letter (N/A and informational dimensions are dropped from the persona's average)
- **Composite:** weighted average of activated personas, computed over graded dimensions only (both N/A and informational excluded from numerator and denominator)

Persona weights for `/prd-review`:

| Persona | Agent | Weight | Role | Dimensions owned |
|---|---|---|---|---|
| PM reviewer | `shield:product-manager-reviewer` | 1.0 | Core | 1, 2, 3, 7, 8, 9, 10, 11, 12 |
| Agile-coach reviewer | `shield:agile-coach-reviewer` | 1.0 | Core | 4 (story/AC quality) |
| Tech-lead reviewer | `shield:architecture-reviewer` | 1.0 | Core | 5, 6 |
| DX reviewer | `shield:dx-engineer-reviewer` | 0.7 | Supporting | anti-patterns + clarity (cross-cutting) |
| Cost reviewer | `shield:cost-reviewer` | 0.7 | Supporting | 13 |

Priorities (same model as plan-review): P0 = D/F on Critical · P1 = C/D on Important · P2 = C on Warning.

**Verdict logic — composite + P0 gate.** The composite score alone can hide a fatal gap (the "averaging problem"): enough strong dimensions can drown out one F on a critical one. To prevent that, the verdict is gated by P0 presence — if any P0 is open, the verdict cannot be "Ready" regardless of composite.

| Condition | Verdict |
|---|---|
| Composite < 1.5 | **Not Ready** |
| Composite 1.5 – 2.4 | **Needs Work** |
| Composite ≥ 2.5 AND any P0 present | **Needs Work** (composite is informational; P0 floor is binding) |
| Composite ≥ 2.5 AND zero P0s | **Ready** |

The header line in `summary.md` makes the gate visible: *"Verdict: Needs Work (composite 3.3, blocked by 4 P0s)"* — readers immediately see why a high composite isn't enough. The composite stays in the report for tracking improvement over time.

**Follow-up (out of scope for this branch):** `shield/skills/general/plan-review/scoring.md` should adopt the same P0-gate rule for consistency. A plan-review where Security = F should not be "Ready" regardless of how strong the architecture grade is. Tracked separately.

Citations to named PM authorities (Cagan, Lenny, Shreyas, Plane.so, Routine.co, Atlassian, Shape Up, etc.) appear:
- **Once** in the rubric documentation (`rubric.md`) as the foundation
- **In detailed/<persona>.md files** for skeptics or pushback
- **NOT in summary.md** — the executive view stays scannable

### `summary.md` shape

```markdown
# PRD Review: <feature>

**Reviewed:** <source>  ·  **Type:** standard  ·  **Verdict:** Needs Work (composite 3.3, blocked by 4 P0s)

## Persona grades
| Persona | Grade | Weight |
| PM reviewer         | C (2.1) | 1.0 |
| Agile-coach reviewer| C (2.0) | 1.0 |
| Tech-lead reviewer  | D (1.4) | 1.0 |
| DX reviewer         | B (2.8) | 0.7 |
| Cost reviewer       | B (2.6) | 0.7 |

## Dimension grades
| # | Dimension | Grade | Owner |

## P0 — Blockers
- ...

## P1 — Important
- ...

## P2 — Nice to have
- ...

## Not applicable (excluded from score)
- Dim 8 (Legal / privacy): N/A — internal cron job, no user data
- Dim 9 (GTM / customer-comms): N/A — internal-only feature
- Dim 5 eval point (i18n): N/A — English-only product

## Informational (lean PRDs only — not graded)
- ...

## Anti-patterns
- ...
```

### Enhanced PRD output and comments export

`/prd-review` produces an enhanced copy of the source PRD plus a structured comments export. The source PRD is never overwritten.

**`enhanced-prd.md`** mirrors the `plan-review` convention:

- Original PRD structure preserved exactly
- P0 and P1 recommendations applied **directly inline** with `<!-- [from: <Persona>] -->` attribution (PM Reviewer / Tech-lead Reviewer / DX Reviewer)
- P2 recommendations added as **comments adjacent to the relevant section**, not direct changes
- Informational entries (lean PRDs) added as comments tagged `<!-- [informational] -->`
- Already-good sections left unchanged
- If source was markdown, output is markdown; if HTML, HTML

**`review-comments.json`** is the canonical structured export, intended for converters that post comments back into the team's PM/code-review tools (GitHub PR review, Notion page comments, Confluence inline comments, Jira). Schema:

```json
{
  "schema_version": "1.0",
  "feature": "<feature-name>",
  "review_id": "<YYYYMMDD>-<N>-prd-review",
  "source": {
    "type": "file | paste | url",
    "resolver": "<name of resolver that handled it — e.g., 'notion-fetch', 'webfetch', 'gh-cli'>",
    "uri": "<original location, if applicable>",
    "snapshot": "source-prd.md"
  },
  "prd_type": "standard | lean",
  "verdict": "Ready | Needs Work | Not Ready",
  "composite_score": 1.8,
  "comments": [
    {
      "id": "<persona>-<seq>",
      "section": "<heading name>",
      "section_anchor": "<URL-safe anchor>",
      "line_in_source": 28,
      "severity": "P0 | P1 | P2 | informational | n/a",
      "reviewer": "pm | tech-lead | dx",
      "dimension": "<rubric dimension name>",
      "comment": "<markdown — body of destination comment>",
      "suggested_addition": "<markdown, or null>",
      "suggested_replacement": "<markdown, or null>"
    }
  ]
}
```

**Severity values:** `P0` / `P1` / `P2` (graded gaps), `informational` (lean PRD structural exemptions), `n/a` (per-dimension reviewer-judged exclusions with reasoning in the `comment` field).

**Suggestion fields by severity:**
- P0 / P1 / P2: at least one of `suggested_addition` / `suggested_replacement` is non-null (gap with fix).
- `informational` and `n/a`: both suggestion fields are null (no fix proposed; entry is explanatory).

Addition vs replacement is the converter's signal — addition becomes "consider adding…"; replacement maps to GitHub suggestion blocks or inline replacements.

**`review-comments.md`** is auto-generated from the JSON for human review. Stable headers (`## Section: <name> (line N)`) so a markdown-only reader can navigate it. Regenerated whenever the JSON changes; never edited directly.

**Apply options** (presented after review completes):
1. **Use as Shield's canonical PRD** — copy `enhanced-prd.md` to `prd/{N}/prd.md`. Works for any source type (local file, URL of any cloud tool, paste). Downstream Shield commands consume the enhanced version from here.
2. **Convert back to original format** — produce `enhanced-prd.<ext>` in a format that matches the source's original tool (HTML, tool-specific markdown flavor, etc.) so the team can paste back into their tool. Shield does NOT write to the original source location.
3. **Skip** — keep `enhanced-prd.md` in the review folder; do nothing else.

Converter tools that post to external systems (GitHub, Notion, Confluence) are out of scope for Phase A — they consume `review-comments.json` and are tracked as a future enhancement.

## References

- Existing research that informed this design: `/Users/apple/research/prd/docs/shield/prd-skill-20260508/research/1-prd-best-practices-and-coverage/findings.md`
- Figma's PRD approach (initial reference, superseded by the 17-section scaffold derived from the research): https://coda.io/@yuhki/figmas-approach-to-product-requirement-docs/prd-name-of-project-1
- Existing Shield skills: `shield/skills/general/plan-docs/`, `shield/skills/general/plan-review/`, `shield/skills/general/research/`
- Project conventions: `/Users/apple/projects/infraspecdev/tesseract/CLAUDE.md`
