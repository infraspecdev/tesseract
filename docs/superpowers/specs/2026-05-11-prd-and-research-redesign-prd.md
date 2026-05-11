# PRD — PRD-and-Research Redesign

> **Dogfood note:** This PRD is authored using the 17-section problem-first scaffold defined in the companion design spec. It's the methodology applied to itself. Where this PRD duplicates the spec, that's intentional — the spec is the implementation contract; the PRD is the product contract.

---

## 1. Header

| Field | Value |
|---|---|
| Owner | @ashwinimanoj |
| Status | Draft |
| PRD type | Standard |
| Date created | 2026-05-11 |
| Last updated | 2026-05-11 |
| Linked design spec | [2026-05-09-prd-and-research-redesign-design.md](./2026-05-09-prd-and-research-redesign-design.md) |
| Linked research | `/Users/apple/research/prd/docs/shield/prd-skill-20260508/` |
| Decision-maker | @ashwinimanoj |
| Sign-off contacts | Eng lead (TBD), Maintainer of Shield (TBD) |
| Linked plans | _(auto-populated by `/plan` when it runs)_ |

---

## 2. Problem & context

Shield's pre-implementation flow today is `/research → /plan → /plan-review → /implement`. There is no product-requirements layer. `/plan` produces a technical breakdown (epics, stories, tasks, acceptance criteria); teams that don't write PRDs jump directly to technical planning, losing product framing, success metrics, and scope boundaries. Teams that *do* write PRDs (often in Notion, Confluence, Google Docs) have no Shield-native way to ingest them, and Shield can't review them for quality or completeness.

**Why now.** Shield's plan-review machinery, multi-persona dispatch, and scoring infrastructure are mature. The piece that gates real product-quality output — a structured PRD layer — is the weakest part of the Shield workflow. Without this, Phases B (the `/prd` author) and C (`/research` Q&A enhancement) are blocked from delivering full value: they're meant to feed into a PRD discipline that doesn't yet exist. The opportunity cost of waiting is that engineering work continues to ship with weak or no product framing.

---

## 3. Target users / personas

| ID | Persona | Goals | Frictions today |
|---|---|---|---|
| **P1** | **Tech lead at a team with PMs who write PRDs in Notion/Confluence** *(primary — Phase A wedge)* | Ingest the team's PRD into a defensible review that catches gaps before engineering commits to a plan | No multi-persona scored review tool exists; one-off ChatGPT prompts vary by user; Notion AI is generic and unsourced |
| **P2** | **PM or eng lead drafting a new PRD** *(Phase B target)* | Author a complete PRD without forgetting load-bearing sections; align with team's existing template if there is one | Empty-doc paralysis; team templates drift; "what sections should this have?" is solved differently every time |
| **P3** | **Engineer running `/research` before scoping a feature** *(Phase C target)* | Capture product + tech context up-front so the plan that follows is grounded | `/research` today is solution-space only; Q&A and repo auto-detect would close the gap |

The Phase A primary target is **P1** — engineering leads ingesting external PRDs. Their current alternative (no tool that does multi-persona scored gap analysis) is the weakest in the market, so adoption pull is highest there.

---

## 4. Goals & non-goals

### Goals

1. Provide a Shield-native PRD review command that ingests external PRDs from any source (local file, paste, URL with runtime MCP discovery) and produces a multi-persona scored gap analysis with severity tiers and an enhanced version with suggested fixes.
2. Provide a Shield-native PRD authoring command with a defensible default scaffold (17-section problem-first) and support for custom team templates with required-section merging.
3. Extend `/research` so its first phase is structured Q&A with repo auto-detect; preserve the existing external evidence-gathering as opt-in Phase 2.
4. Keep all new steps optional and skippable. Downstream commands consume earlier artifacts as context if present.
5. Match existing Shield conventions: feature-folder layout, manifest + index.html dashboard, A-F scoring rubric, multi-persona dispatch, P0-gate verdict.

### Non-goals

- Replace `/plan`. The technical breakdown stays in `/plan`; PRDs capture *what + why + how-much*, `/plan` captures *how + which-files + what-tests*.
- Replace `/research`'s existing external evidence-gathering. That capability is preserved as Phase 2.
- Build a separate `/discovery` command. Explicitly rejected during design; merged into `/research` Phase 1.
- Enforce a workflow. Every step is skippable; users can run any command without prior steps.

---

## 5. Success metrics

| Metric | Type | Target | Counter |
|---|---|---|---|
| `/prd-review` runs / week per active project | Leading (adoption) | ≥ 1 within 30 days of release | — |
| `/prd` runs / week per active project | Leading (adoption) | ≥ 1 within 60 days of release | — |
| Average composite verdict on repeat-reviewed PRDs | Lagging (quality) | Trends from Needs Work → Ready over the 2nd or 3rd review pass on the same feature | PRD-author N/A claims must not exceed 30% (gaming check) |
| % of `/research` Phase 1 questions auto-answered from context + repo scan | Operational | ≥ 40% | — |
| Counter — feature folders with a PRD but no `/plan` follow-up | Leading | ≤ 20% over 90 days (avoids PRDs that go nowhere) | — |

**Dashboard plan.** Surfaced via `manifest.json` aggregation; the existing `index.html` dashboard learns a "PRD" status column per feature folder with the latest verdict.

---

## 6. User stories & scenarios

### Story P1-S1: Tech lead reviews an external PRD

- **Persona:** P1 — Tech lead
- **Goal:** Run a multi-persona review on a PRD living in Notion to identify load-bearing gaps before the team commits to a `/plan`.
- **Happy path:**
  1. Lead runs `/prd-review https://notion.so/<page>`
  2. Shield classifies as URL → consults known-host map → looks for `*notion*` MCP at runtime
  3. Notion MCP fetches page, content snapshotted to `source-prd.md`
  4. Shield asks: "This looks like a standard PRD. Confirm?"
  5. Lead confirms; 5 reviewer agents dispatched in parallel (PM, agile-coach, tech-lead, DX, cost)
  6. Reviewers grade dimensions A-F; verdict computed with P0-gate
  7. Outputs written: `summary.md`, `source-prd.md`, `enhanced-prd.md`, `review-comments.json`, `review-comments.md`, `detailed/{persona}.md`
  8. Lead is offered: use enhanced version as canonical / convert back to original format / skip
- **Error / timeout / abandon paths:**
  - Notion MCP unauthenticated → Shield reports error, offers paste fallback in same turn
  - URL returns 403 → Shield reports, offers paste fallback
  - All 5 reviewers fail → Shield reports which failed; user can re-run or accept partial output
- **Edge cases:**
  - PRD is in lean form (just Problem + Goals + Metrics + Open questions) → Shield detects lean, confirms, applies 8-dim lean rubric
  - PRD is in a custom team format (not Shield's scaffold) → reviewer agents adapt; dim 7 owner-detection may fall back to "header section not found"
  - Source contains embedded images → preserved as `[image: alt-text]` placeholders, not reviewable in Phase A
- **State transitions:** PRD status in `prd.meta.json` may move Draft → In Review (added to lifecycle in a future enhancement)
- **Cross-functional handoffs:** if Legal/Privacy gaps (dim 8) are P0, the suggested next-step note in `summary.md` recommends Legal sign-off before `/plan`
- **Acceptance criteria (Given/When/Then):**
  - Given a Notion URL with Notion MCP present, When `/prd-review <url>` runs, Then `source-prd.md` is created with the page content snapshot AND all 6 output files are produced AND verdict respects the P0-gate
  - Given Notion MCP is absent, When `/prd-review <url>` runs, Then Shield offers paste fallback in the same turn AND continues review on pasted content
  - Given a PRD with GTM dim graded F, When verdict is computed, Then verdict is "Needs Work (composite X.X, blocked by N P0s)" regardless of composite score

### Story P2-S1: PM authors a new PRD using the default scaffold

- **Persona:** P2 — PM or eng lead
- **Goal:** Author a complete PRD using Shield's 17-section problem-first scaffold without forgetting load-bearing sections.
- **Happy path:**
  1. PM runs `/prd <topic>`
  2. Shield asks PRD type (standard | lean); PM picks standard
  3. Shield checks for prior `/research` transcript in feature folder; if present, pre-populates Problem, Users, Constraints
  4. Shield walks remaining sections one at a time, asking for content
  5. PM provides answers; Shield writes `prd.md`, `prd.html`, `prd.meta.json` to new run folder
- **Error / timeout / abandon paths:**
  - PM hits "skip" on a required section → Shield records `[TBD]` and surfaces it as an Open Question
- **Edge cases:**
  - `.shield.json` declares a custom template → Shield merges in any required sections the custom template lacks, reports "Augmented your template with: <list>"
  - PM has a prior lean PRD in the folder → Shield offers multi-select to add sections (defaults to all 10 missing-from-standard checked)
- **Cross-functional handoffs:** if PM names sign-off contacts in Header, downstream `/plan` and `/prd-review` reference them
- **Acceptance criteria (Given/When/Then):**
  - Given `<topic>` only, When `/prd standard <topic>` runs, Then Shield walks the 17-section scaffold AND writes `prd.md`, `prd.html`, `prd.meta.json` to `prd/{N}-{slug}/`
  - Given `.shield.json` `prd_template` is set, When `/prd` runs, Then the custom template is used as the base AND missing required sections are appended with markers AND user is told what was added
  - Given a lean PRD exists in the feature folder, When `/prd` runs again, Then multi-select with missing sections pre-checked is offered AND original lean run is preserved AND new run folder created

### Story P3-S1: Engineer runs research with repo context

- **Persona:** P3 — Engineer
- **Goal:** Capture product + tech context before scoping; reduce friction by skipping questions whose answers are inferable from the repo.
- **Happy path:**
  1. Engineer runs `/research <topic>`
  2. Shield silently scans repo: package manifests → tech stack; CLAUDE.md/SECURITY.md → compliance markers; `.github/workflows/` → deployment pattern; git log → recent activity
  3. Shield surfaces detected context, asks user to confirm/correct
  4. Shield asks remaining Q&A topics not auto-answered
  5. Phase 1 transcript written; Shield offers Phase 2 external evidence-gathering on surfaced open questions
- **Edge cases:**
  - Repo is empty / no manifests → Shield skips auto-detect and proceeds with full Q&A
  - User overrides auto-detected value → recorded as `(corrected by user)` in transcript
- **Acceptance criteria (Given/When/Then):**
  - Given a Node + TypeScript repo, When `/research <topic>` runs, Then `## Detected Context` section appears at top of transcript AND Q&A skips tech-stack and integration questions

---

## 7. Functional requirements

All scenarios in section 6 above are testable Given/When/Then ACs. Additional functional requirements are in the [design spec's Functional Requirements section](./2026-05-09-prd-and-research-redesign-design.md), which is the authoritative source for command-level behavior.

Key invariants:
- Source PRD is never overwritten — `enhanced-prd.md` is always a copy
- Verdict is gated by P0 presence — composite alone cannot produce "Ready"
- All output artifacts (summary, source-prd, enhanced-prd, review-comments.json, review-comments.md, detailed/*) are written atomically per run

---

## 8. Non-functional requirements

| NFR | Requirement |
|---|---|
| **Performance** | `/prd-review` of a 5-page PRD ≤ 3 minutes (5 parallel reviewer agents). `/research` repo scan ≤ 30s. `/prd` is human-paced. |
| **Reliability** | All ingest sources snapshot to `source-prd.md`; re-runs are deterministic given the same source. Resolver failure offers paste fallback in same turn. |
| **Privacy** | No content leaves the user's process beyond what the LLM and configured MCPs receive. URL ingest uses the user's authenticated MCPs only. |
| **Security** | Each MCP handles its own auth. Shield delegates; no Shield-side credential storage. |
| **Accessibility** | Generated HTML matches existing `/plan` accessibility conventions (semantic headings, max-width, blue accent, contrast). |
| **Telemetry / event taxonomy** | Manifest entries record new artifacts (PRD, PRD review, research transcript) with type, verdict, date. |
| **Threat model / abuse cases** | Risk: an author games the rubric with N/A claims to dodge grading → mitigated by N/A reasoning requirement + reviewer override on implausible claims. |
| **RBAC / permissions matrix** | N/A — Shield is a single-user CLI plugin; no multi-user permissions. |
| **i18n / l10n (system-level)** | English-only. Documented limitation; no i18n roadmap in scope. |

---

## 9. Dependencies

- **Notion MCP server** — already installed in the Shield plugin context; required for Notion URL ingestion.
- **WebFetch tool** — built-in; used as catch-all for HTTP(S) URLs.
- **Existing Shield agents** — `product-manager-reviewer`, `agile-coach-reviewer`, `architecture-reviewer`, `dx-engineer-reviewer`, `cost-reviewer`.
- **Existing scoring infrastructure** — `shield/skills/general/plan-review/scoring.md` (same A-F grade scale, weighted-composite formula).
- **`gh` CLI** — for `github.com/*/blob/*.md` URL handling.
- **Optional / extension** — Atlassian (Confluence) MCP, Google Drive MCP for those URL patterns; absence falls back to WebFetch then paste.

---

## 10. Risks & mitigations

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Multi-persona dispatch latency exceeds 3-minute SLA for typical PRDs | M | M | Run with 3 personas (PM, agile-coach, tech-lead) under load; defer DX + cost to A.1 if needed. Per-phase abort criterion is set. | @ashwinimanoj |
| R2 | Repo auto-detect surfaces > 30% false-positive rate (wrong stack, wrong integrations) | M | M | Manual confirmation step is part of the Q&A. User can correct anything. | @ashwinimanoj |
| R3 | Custom-template merging clobbers user content | L | H | Templating writes only at end of file, never mid-section. Test fixtures include user-modified templates. | @ashwinimanoj |
| R4 | Generated rubric over-flags well-formed PRDs (false-positive gaps) | M | M | Iterate the rubric over the first 3-5 real reviews; lower-severity points can be promoted/demoted. PM-author declared N/A escape hatch. | @ashwinimanoj |
| R5 | Adoption-as-habit problem: engineers don't run `/prd-review` even when valuable | M-H | H | Adoption metric tracked from launch; if < 1 run/week at 30 days, dig into friction. Behavior change isn't a tooling problem alone. | @ashwinimanoj |
| R6 | Rubric drift over time creates inconsistent grades on re-reviewed PRDs | M | L-M | `rubric_version` field in `review-comments.json`; re-runs note version change. | @ashwinimanoj |
| R7 | Open-source plugin marketplace: PR review bandwidth limits how fast we iterate | L | M | Build in Aspora-Infraspec fork-style work, PR to upstream when stable. | @ashwinimanoj |

---

## 11. Assumptions

| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | Shield users either have or will write PRDs | Unvalidated | Phase A's wedge weakens; Phase B becomes the primary phase |
| A2 | The 13-dimension rubric captures the gaps that engineering teams actually care about | Unvalidated | Iterate via Future enhancement "rubric evolution" pattern; rubric_version handles drift |
| A3 | Repo auto-detect heuristics cover ≥ 80% of Shield user projects | Plausible — Shield already uses these heuristics in `/plan` domain detection | Edge cases proceed with manual Q&A; not blocking |
| A4 | Teams with custom PRD templates will configure `prd_template` in `.shield.json` | Plausible | Custom-template merging logic preserves their additions; falls back to default if unconfigured |
| A5 | The 5 reviewer agents collectively grade meaningfully different dimensions (low overlap) | Unvalidated | Review actual output for redundancy in first 5 dispatches; demote overlapping personas to supporting weight |

---

## 12. Rollout plan

Three sub-phases, each independently shippable. Per `CLAUDE.md`: bump `shield` version in `.claude-plugin/marketplace.json` only.

1. **Phase A — `/prd-review`** (highest immediate value, lowest competition)
2. **Phase B — `/prd`** (after Phase A is in user hands)
3. **Phase C — `/research` Phase 1 enhancement** (after Phases A and B)

### Per-phase abort criteria

| Criterion | Threshold | Action |
|---|---|---|
| Multi-persona dispatch latency | > 5 min for typical PRDs | Reduce personas to 3 core; defer DX + cost |
| Repo auto-detect false-positive rate | > 30% on sampled repos | Roll back Phase C; manual Q&A only |
| Custom-template merging clobbers user content | Any P0 in fixture tests | Block release; root-cause + fix |

### Migration

No migration needed. Existing feature folders are unchanged; new subfolders (`prd/`, `prd-review/`) are added on first use. `manifest.json` schema accepts new entries without breaking old ones.

### Kill switch

Per-phase rollback = revert the commit and bump the marketplace version back. Shield commands are inherently opt-in (user invokes), so no feature flag is needed.

### Data migration & backward compatibility

- Existing `plan.json` and `plan-review/*` files in user feature folders remain valid; new fields (`source_prd`, `prd_rubric_version_at_planning`) are additive and absent in pre-existing files.
- Rubric evolution (e.g., dim 14 added later) is recorded via `rubric_version` in `review-comments.json` so old reviews stay interpretable.

---

## 13. Cost & resource impact

| Component | Cost dimension | Estimate |
|---|---|---|
| **Build cost** | Engineering time | ~4-6 weeks across 3 phases for a single engineer using Shield's existing skill/agent patterns; ~2-3 weeks for Phase A alone |
| **Run cost — per `/prd-review` invocation** | LLM API tokens | 5 parallel reviewer dispatches × ~10-30k tokens each = 50-150k tokens per review (Claude Opus 4.7 pricing). Roughly $0.30-$1.50 per review at standard rates. |
| **Run cost — per `/prd` invocation** | LLM API tokens | Interactive Q&A walk: ~5-20k tokens. ~$0.05-$0.20 per PRD authored. |
| **Run cost — per `/research` invocation** | LLM API tokens | Phase 1: 2-10k tokens for repo scan + Q&A. Phase 2 (existing): unchanged. |
| **Storage** | Disk per feature folder | < 100KB per `/prd-review` run (markdown + JSON). Negligible. |
| **Maintenance** | Engineering time | Rubric iteration, MCP failures, new resolver additions. Estimate ~1-2 dev-days/quarter steady state. |

**Cost counter-metric:** total monthly LLM spend on `/prd-review` should remain < $X per user per month at typical usage (target TBD based on early adoption).

For an open-source plugin marketplace where users bring their own Claude API key, **Shield-side cost is zero**; users absorb their own LLM costs based on their plan. This is documented in user-facing docs.

---

## 14. GTM & customer-comms

Internal-team feature; no external pricing implications. GTM plan:

| Channel | Action |
|---|---|
| **tesseract repo `CHANGELOG.md` / release notes** | Per-phase release entry naming the new command + one-line value prop |
| **README / Shield docs** | New "PRD authoring + review" section with one-screen quickstart |
| **In-tool nudge** | When `/plan` runs in a feature folder without a PRD, Shield can suggest "run `/prd-review` first if you have an external PRD, or `/prd` to author one" (low-priority enhancement) |
| **Internal demo** | Loom recording: `/prd-review` against a real anonymized PRD; surface verdict + P0 list |
| **Slack / team channel** | Per-phase announcement when shipped; pin to channel for new joiners |
| **Pricing / packaging** | N/A — open-source plugin marketplace |
| **Sales / partnership** | N/A — no external distribution gates |

---

## 15. Support / CX impact

| Concern | Plan |
|---|---|
| **Issue tracking** | GitHub Issues on `infraspecdev/tesseract` |
| **Day-1 ticket owner** | @ashwinimanoj (escalation: Shield maintainers) |
| **Runbook for common failures** | Documented in `shield/skills/general/prd-review/ingest.md` under "Failure flow": handler unavailable → paste fallback; unreachable URL → error message + paste fallback |
| **User documentation** | `SKILL.md` per skill (Shield convention); command-level docs in `shield/commands/prd-review.md` |
| **Internal training / enablement** | One Loom + one-page user guide for the Aspora-Infraspec team |
| **Triage policy** | P0 bugs (Shield refuses to start, wrong output written, missing artifacts): same-day; P1 (degraded rubric grades, MCP integration issues): 1-week; P2 (cosmetic, edge case): next release |

---

## 16. Open questions

| # | Question | Owner | Target resolution |
|---|---|---|---|
| Q1 | Should `/prd-review` enhanced-prd.md make inline edits or use comments? | Phase A implementation | Resolved in spec — `plan-review`-style hybrid (P0/P1 inline with attribution; P2 as comments). |
| Q2 | Will the 5-persona dispatch hold the 3-minute SLA on real PRDs? | Phase A integration testing | First 5 real reviews benchmarked; abort criterion in rollout plan handles regression. |
| Q3 | How does `/prd` discover that an existing prior PRD lives in a non-default location? | Phase B implementation | Convention-based: only checks `prd/` under the feature folder. Custom locations require explicit user action. |
| Q4 | What's the right default behavior if `.shield.json` is missing? | Phase B implementation | Default to built-in scaffold and personas; no error. (Already in spec.) |
| Q5 | Should `/prd-review` produce a re-review diff when run twice on the same PRD? | Future enhancement (not Phase A) | Captured in Future Enhancements section of spec. |

---

## 17. Out of scope / Non-goals

(Same set as the design spec — duplicated here for PRD self-containedness.)

- **`/discovery` as a separate command.** Explicitly rejected after exploration; merged into `/research` Phase 1.
- **Discovery review (gap analysis on a discovery transcript).** Discovery is exploratory; gaps are not a meaningful concept for it.
- **A `/prd` command argument for type or template path.** Type is asked interactively; template path lives in `.shield.json`.
- **Replacing or modifying `/plan`'s output.** `/plan` continues to consume `prd.md` as context if present.
- **Replacing the existing `/research` external evidence-gathering.** Preserved as Phase 2.
- **Per-persona feature flags.** All five personas run together; single-persona invocation is via the underlying agent directly.
- **Project-management sync for PRDs.** `/pm-sync` continues to operate on plan stories; PRDs are documents, not work items.
- **Version-controlled PRD diffs across runs.** Git provides this; Shield doesn't need a custom diff tool.
- **Converters that post `review-comments.json` to external tools** (GitHub PR review, Notion API, Confluence inline comments, Jira). Tracked as future enhancement.
- **Multi-file PRD sources.** Phase A reviews one source; the bill-payments case (architecture + plan as two files) is a future enhancement.

---

## Appendix A — Glossary

| Term | Definition |
|---|---|
| **Composite verdict** | Weighted average of all activated personas' grades, mapped to Ready / Needs Work / Not Ready. P0-gated. |
| **Dimension** | One of the 13 rubric checks (e.g., Problem clarity, Rollout & ops). Each owned by one persona; graded A-F or N/A or informational. |
| **Evaluation point** | A specific A-F-graded sub-check within a dimension (e.g., 4a: "happy path AND error/timeout paths captured"). |
| **P0-gate** | The verdict can never be "Ready" if any P0 exists, regardless of composite. |
| **Persona** | A reviewer agent (PM, agile-coach, tech-lead, DX, cost). Each owns a subset of dimensions and contributes a weighted grade to the composite. |
| **Severity** | P0 (Critical/blocker) · P1 (Important) · P2 (Warning/nice-to-have) · informational (lean structural) · n/a (excluded with reasoning). |
| **Standard vs lean** | Standard PRD = 17-section scaffold; lean = 7-section. Lean has 5 informational dimensions (excluded from composite). |
