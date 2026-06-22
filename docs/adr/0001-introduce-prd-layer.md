# ADR 0001 — Introduce a PRD layer between Research and Planning

**Status:** Accepted (shipped across PRs #35, #38, #41, #42 — Phase A `/prd-review`, Phase B `/prd`, milestones, scaffold expansion)
**Date:** 2026-05-18
**Authors:** @ashwinimanoj
**Plugin:** shield
**Supersedes:** —
**Related specs:**
- `docs/superpowers/specs/2026-05-09-prd-and-research-redesign-design.md` (design)
- `docs/superpowers/specs/2026-05-11-prd-and-research-redesign-prd.md` (PRD-for-PRD, dogfooded)
- `docs/superpowers/specs/2026-05-13-prd-milestones-design.md`
- `docs/superpowers/specs/2026-05-13-prd-toc-terminologies-design.md`

---

## TL;DR

Shield's pre-implementation flow went `/research → /plan → /plan-review → /implement` with no product-requirements layer. Teams jumped from problem-space research (or nothing) straight to technical breakdown, losing product framing, success metrics, and scope boundaries. We added a PRD layer — two commands (`/prd`, `/prd-review`) plus an enhancement to `/research` — that sits between research and planning. All steps are optional and skippable; downstream commands consume earlier artifacts if present.

---

## Context — what we had before

### The old workflow

```
/research  →  /plan  →  /plan-review  →  /implement
```

- **`/research`** was solution-space only: a PM-framed prompt fanned out to 3 parallel agents fetching official docs, industry voices, and community sources, producing a sourced `findings.md`. It did not capture problem-space or tech-context Q&A.
- **`/plan`** produced a technical breakdown — epics, stories, tasks, acceptance criteria — not a product requirements document. Its job was *how + which-files + what-tests*, not *what + why + how-much*.
- **`/plan-review`** scored the plan with multi-persona dispatch (PM, architecture, security, DX, cost, agile-coach, ops, well-architected) on a documented A-F rubric.

### The gap

The flow worked end-to-end but had a structural hole between research and planning:

1. **No place to capture product intent.** Teams that don't write PRDs jumped straight from research (or nothing) to technical planning. Result: implementation drifted from what users needed; downstream stories were untestable against product intent; reviewers couldn't catch gaps a PM would catch (no Out-of-Scope, no leading metrics, no rollout plan).
2. **No way to ingest external PRDs.** Teams that *do* write PRDs — usually in Notion, Confluence, or Google Docs — had no Shield-native way to bring them in. Their PRD lived outside the Shield artifact graph, so plans couldn't reference it and reviewers couldn't grade against it.
3. **`/research` was missing the front half.** It went straight to external evidence-gathering without first capturing problem-space, users, constraints, or existing tech context from the repo. Even teams using `/research` started downstream planning without a structured product + tech context document.

### Why now

Shield's plan-review machinery, multi-persona dispatch, and A-F scoring infrastructure were mature by early 2026. The piece gating real product-quality output — a structured PRD layer — was the weakest part of the workflow. Without it, the existing strengths (parallel reviewer agents, weighted-composite scoring, severity-tiered gaps) could not be applied to product framing at all. Opportunity cost: engineering work continued to ship with weak or no product framing.

---

## Decision — what we built and why

### The new workflow

```
/research  →  /prd   →  /plan  →  /plan-review  →  /implement
              /prd-review (for existing external PRDs)
```

Each step remains optional. Downstream commands consume earlier artifacts if present (e.g., `/plan` reads `prd.md` and records `source_prd` in `plan.json`).

### Load-bearing decisions

#### D1. Two PRD commands, not one

We split authoring and review:

- **`/prd`** — authors a new PRD using a 17-section problem-first scaffold (lean variant collapses to 7 sections). Walks the user section by section, pre-populating from `/research` transcripts and repo scans where possible.
- **`/prd-review`** — ingests an external PRD from any source (local file, paste, or URL) and produces a multi-persona scored gap analysis on a 13-dimension rubric.

**Why two commands:** the two use cases have different mental models. Authoring is a writing flow; review is a critique flow. One command would have meant a confusing entry point with a "are you writing or reviewing?" prompt. Two commands also let us ship them in separate phases (Phase A: review; Phase B: author), getting review value out the door faster.

#### D2. Ship `/prd-review` first (Phase A)

Adoption pull was strongest for engineering leads ingesting PRDs their PMs had already written. The market alternatives (one-off ChatGPT prompts, Notion AI) were weak — neither did multi-persona scored gap analysis with citations. `/prd` (authoring) competed against more entrenched habits (existing team templates in Confluence/Notion), so we shipped review first to establish a wedge.

#### D3. 17-section problem-first scaffold, mirroring the 13-dimension rubric

Every rubric dimension reviewers grade against has a home section in the default scaffold. Authors aren't surprised at review time by sections they didn't know were expected. Sections are ordered problem-first: Header → Problem → Personas → Goals → Metrics → Stories → FRs → NFRs → Dependencies → Risks → Assumptions → Rollout → Cost → GTM → Support → Open questions → Out of scope.

**Lean variant** collapses to 7 sections (Header, Problem, Users, Goals, Metrics, Open questions, Out of scope). Lean PRDs include a footer listing the standard sections they intentionally omit, plus a multi-select upgrade flow.

Subsequent expansions (PRs #41, #42) added the milestones table, TOC, Terminologies section, Architecture & flows section with Mermaid diagrams, and story types — all derived from real-world reviews surfacing gaps in the original scaffold.

#### D4. Generic ingest — no provider baked in

`/prd-review` accepts a local path, paste content, or any URL. For URLs, Shield consults an internal known-host map (URL pattern → MCP-name pattern) and resolves at runtime to whichever MCP is present in the session. If no MCP matches, falls through to WebFetch, then to paste fallback. Authentication is each MCP's own concern.

**Why generic:** baking in a default provider (e.g., always Notion) would have created a maintenance burden every time a team used Confluence, Google Docs, or an internal wiki. The universal paste fallback means Shield never hard-fails on a document it can't reach. Adding support for a new cloud is data, not code.

#### D5. Reuse plan-review's scoring infrastructure with one new rule

The A-F per-evaluation-point scale, weighted-composite formula, and severity tiers (P0/P1/P2) all come from `shield/skills/general/plan-review/scoring.md`. We added one new rule:

- **P0 gate on verdict.** Composite alone can drown out a fatal gap (the averaging problem). If any P0 is open, the verdict cannot be "Ready" regardless of composite. Header reads: *"Needs Work (composite 3.3, blocked by 4 P0s)"*.

This is a follow-up candidate for `/plan-review` itself, tracked separately.

#### D6. Three dimension states — graded, N/A, informational

- **Graded** (A-F) — default; counted toward composite.
- **N/A** — dimension genuinely doesn't apply (e.g., GTM for an internal cron); requires one-line reasoning; excluded from composite. Bare N/A without reasoning grades F.
- **Informational** — lean-PRD structural exemption (dims 5, 6, 9, 10, 13 are informational for lean); surfaced but excluded from composite.

**Why three states:** a binary graded/skip model lets authors game the rubric by skipping inconvenient dimensions. Forcing reasoning and letting reviewers override implausible N/A claims keeps the rubric honest while accommodating genuine non-applicability.

#### D7. Source PRD never overwritten

`enhanced-prd.md` is always a copy with P0/P1 fixes inline (attributed by persona via `<!-- [from: <Persona>] -->`) and P2 as adjacent comments. The original `source-prd.md` snapshot is preserved verbatim so re-runs are deterministic.

#### D8. Canonical comments export (`review-comments.json`)

Machine-readable per-section gap comments, intended for external converters that post back into GitHub PR review, Notion page comments, Confluence inline comments, or Jira. Human-readable views live in `summary.md` (scannable triage) and `detailed/<persona>.md` (per-persona prose). We rejected a parallel `review-comments.md` because it invites sync drift when humans edit the wrong copy.

#### D9. Bidirectional PRD ↔ Plan linkage

`prd.meta.json` records `linked_plans: [...]`; `plan.json` records `source_prd: ...` and `prd_rubric_version_at_planning`. Auto-populated when `/plan` runs against a feature folder containing a PRD. `prd_rubric_version_at_planning` lets re-runs detect rubric drift (e.g., dim 13 was added later — older PRDs reviewed before that don't auto-fail on it).

#### D10. All steps optional and skippable

No workflow enforcement. Users can run any command without prior steps. Downstream commands gracefully consume earlier artifacts if present, and proceed without them if not.

#### D11. `/research` keeps its solution-space agents as Phase 2

Rather than replacing the existing 3-agent external evidence-gathering, we added a Phase 1 (structured Q&A + repo auto-detect) in front of it. Phase 2 becomes opt-in on the open questions that Phase 1 surfaces.

**Why preserve:** Phase 2 is the strongest part of `/research` today. Replacing it would have lost a working capability for a hypothetical improvement.

---

## Alternatives considered

### A1. Single `/prd` command with `--review` flag

**Rejected.** Conflated two different mental models (writing vs critiquing) and forced a confusing entry-point prompt. Two commands ship and iterate independently.

### A2. Extend `/plan` to include product framing

**Rejected.** `/plan` is the technical breakdown. Stuffing product framing in would have either bloated the plan output or watered down the product framing. The two artifacts have different audiences (engineering vs. product + engineering) and different review rubrics.

### A3. Build a separate `/discovery` command

**Rejected during design.** Earlier exploration proposed `/discovery` as a third command (problem-space exploration distinct from research). It overlapped with `/research` in name and concept. Folded into `/research` Phase 1 instead. Discovery review (gap analysis on a discovery transcript) was also rejected — discovery is exploratory; gaps aren't a meaningful concept for it.

### A4. Bake Notion in as the default URL resolver

**Rejected.** Would have created lock-in to one provider and a maintenance tax for every team that uses Confluence, Google Docs, or an internal wiki. Generic ingest with runtime MCP discovery handles all mainstream cases without code changes.

### A5. Provider-specific feature flags (e.g., `prd_review_notion_only`)

**Rejected.** Generic ingest with paste fallback makes per-provider toggles unnecessary. The universal paste fallback is the kill-switch.

### A6. Replace `/research`'s external agents instead of extending them

**Rejected.** Phase 2 is the working part of `/research` today. Replacing it would have regressed a capability for a hypothetical improvement. Phase 1 + Phase 2 in sequence is additive.

### A7. Single-flat-rubric (no graded/N/A/informational distinction)

**Rejected.** A binary graded/skip model lets authors game the rubric by skipping inconvenient dimensions, and forces the composite to either over-penalize legitimately-N/A dimensions or under-penalize gaming. Three states with mandatory reasoning + reviewer override keep the rubric honest.

---

## Consequences

### Positive

- **Product framing has a home.** Teams that don't write PRDs now have a Shield-native authoring scaffold; teams that do have a Shield-native review path.
- **Bidirectional traceability.** PRD → Plan linkage is auto-populated and survives rubric drift.
- **Reusable scoring.** The PRD-review scoring uses the same A-F + weighted-composite + severity model as plan-review, so users only learn the model once.
- **Generic ingest.** Adding support for a new tool is data, not code.
- **Phase A wedge.** `/prd-review` ships value to the largest segment (teams with external PRDs) first, with low competition from existing tools.

### Negative / trade-offs

- **Two more commands to maintain.** `/prd` and `/prd-review` add surface area to Shield. Mitigated by reusing existing skill/agent/scoring infrastructure.
- **Rubric drift risk.** Re-reviewed PRDs may grade differently as the rubric evolves. Mitigated by `rubric_version` in `review-comments.json` so old reviews stay interpretable.
- **LLM cost.** `/prd-review` dispatches 5 parallel reviewer agents (~50-150k tokens per review). Documented as ~$0.30-$1.50 per review at standard Claude Opus 4.7 rates. Users absorb their own LLM costs.
- **Adoption is a habit problem, not a tooling problem.** Engineers may not run `/prd-review` even when valuable. Adoption tracked from launch; if < 1 run/week at 30 days, we dig into friction.
- **English-only.** Rubric and reviewer agents assume English. Multi-language PRDs are not formally supported.
- **Massive PRDs (>50 pages).** Latency degrades and quality may suffer. Workaround: split into multiple PRDs per epic.

### Follow-ups tracked separately

- **P0-gate on `/plan-review` verdict.** The same rule should apply to plan reviews — a plan with Security = F shouldn't be "Ready" regardless of composite. Tracked in design spec under Scoring's follow-up note.
- **Converters that post `review-comments.json` to external tools.** GitHub PR review, Notion API, Confluence inline comments, Jira. Out of Phase A scope.
- **Re-review diff** (compare current `/prd-review` against prior run): "new gaps", "still-open gaps", "resolved gaps." Adds a learning loop.
- **PRD status lifecycle** beyond `draft`: `in-review`, `approved`, `in-implementation`, `shipped`, `retired`.
- **Context federation** beyond repo scan: pull related runbooks (Confluence), tickets (Jira/Linear), dashboards (Datadog), design (Figma) via MCPs declared in `.shield.json` `context_sources`.
- **Multi-file PRD sources.** Phase A reviews one source; the bill-payments case (architecture + plan as two files) is a future enhancement.

---

## References

- Design spec: `docs/superpowers/specs/2026-05-09-prd-and-research-redesign-design.md`
- PRD-for-PRD (dogfooded): `docs/superpowers/specs/2026-05-11-prd-and-research-redesign-prd.md`
- PRD milestones spec: `docs/superpowers/specs/2026-05-13-prd-milestones-design.md`
- PRD TOC + Terminologies spec: `docs/superpowers/specs/2026-05-13-prd-toc-terminologies-design.md`
- Phase A implementation plan: `docs/superpowers/plans/2026-05-11-prd-review-phase-a.md`
- Phase B implementation plan: `docs/superpowers/plans/2026-05-11-prd-phase-b.md`
- Shipped skills: `shield/skills/general/prd-docs/`, `shield/skills/general/prd-review/`, `shield/skills/general/story-coverage/`
- Shipped commands: `shield/commands/prd.md`, `shield/commands/prd-review.md`
- Scoring infrastructure (reused): `shield/skills/general/plan-review/scoring.md`
