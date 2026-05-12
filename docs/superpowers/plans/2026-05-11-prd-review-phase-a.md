# PRD-Review Phase A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Phase A of the PRD-and-Research redesign — the `/prd-review` command — including the new `prd-review` and `story-coverage` skills, an extended `agile-coach-reviewer` agent, and full RED-GREEN validation against PRD fixtures.

**Architecture:** Markdown-driven Shield skill following the existing `plan-review` pattern. `/prd-review` orchestrates: (1) classify input (local/URL/paste), (2) resolve via internal known-host map + runtime MCP discovery → snapshot to `source-prd.md`, (3) detect lean vs standard PRD type + confirm with user, (4) dispatch 5 reviewer agents in parallel (PM, agile-coach with AC1-AC12 incl. story coverage, tech-lead, DX, cost), (5) aggregate grades with A-F → per-persona → weighted composite, (6) apply P0-gate to verdict, (7) write 5 output artifacts (`summary.md`, `source-prd.md`, `enhanced-prd.md`, `review-comments.json`, `detailed/<persona>.md`). The new `story-coverage` skill is consumed by the agile-coach reviewer for dim 4 eval points 4f/4g and (in Phase B) by `/prd`.

**Tech Stack:** All markdown content (skills/commands/agents). No new Python code. Existing Shield agent dispatch infrastructure reused. RED-GREEN validation via Claude Code Agent tool against fixture PRDs.

---

## Spec reference

This plan implements **Phase A** of `docs/superpowers/specs/2026-05-09-prd-and-research-redesign-design.md`. The PRD at `docs/superpowers/specs/2026-05-11-prd-and-research-redesign-prd.md` is the product contract. Read both first; this plan assumes their terminology.

## Scope of this plan (Phase A only)

**In scope:**
- New skill: `shield/skills/general/prd-review/` (5 files: SKILL.md, personas.md, rubric.md, ingest.md, scoring.md)
- New skill: `shield/skills/general/story-coverage/` (2 files: SKILL.md, archetypes.md)
- New command: `shield/commands/prd-review.md`
- Agent update: `shield/agents/agile-coach-reviewer.md` adds AC11 (persona-goal coverage) and AC12 (archetypal flow coverage), referencing the story-coverage skill
- Test fixtures: 4 PRDs at `shield/skills/general/prd-review/test-fixtures/` (lean-with-gaps, standard-with-gaps, well-formed-standard, internal-tool)
- RED-GREEN validation against fixtures
- Marketplace version bump (shield 2.11.0 → 2.12.0)

**Out of scope (per spec):**
- Phase B: `/prd` author command (consumes `story-coverage` skill but command itself is Phase B)
- Phase C: `/research` Phase 1 enhancement
- Converters that post `review-comments.json` to GitHub PR review / Notion API / Confluence
- DOCX ingestion (paste fallback only)
- Multi-language PRDs
- Re-review diff feature

**Dependencies:**
- Existing agents: `shield:product-manager-reviewer`, `shield:architecture-reviewer`, `shield:dx-engineer-reviewer`, `shield:cost-reviewer`, `shield:agile-coach-reviewer` (extended in this plan)
- Existing scoring infrastructure: `shield/skills/general/plan-review/scoring.md` (A-F grade scale, weighted-composite formula)
- Notion MCP server (already installed in plugin context)
- WebFetch tool (built-in)

---

## File structure

**New files:**

```
shield/
├── commands/
│   └── prd-review.md                       (~80 lines — command definition)
├── skills/general/
│   ├── prd-review/
│   │   ├── SKILL.md                        (~200 lines — orchestration workflow)
│   │   ├── personas.md                     (~250 lines — 5 reviewer dispatch prompts)
│   │   ├── rubric.md                       (~300 lines — 13 dimensions + eval points + severity)
│   │   ├── ingest.md                       (~150 lines — classification + dispatch + fallbacks)
│   │   ├── scoring.md                      (~80 lines — A-F, composite, P0-gate)
│   │   └── test-fixtures/
│   │       ├── lean-with-gaps.md           (~80 lines — lean PRD missing required content)
│   │       ├── standard-with-gaps.md       (~250 lines — standard PRD with 5+ P0-class issues)
│   │       ├── well-formed-standard.md     (~350 lines — strong PRD, should grade Ready)
│   │       └── internal-tool.md            (~120 lines — features for N/A handling)
│   └── story-coverage/
│       ├── SKILL.md                        (~120 lines — derive expected stories)
│       └── archetypes.md                   (~250 lines — flow patterns per domain)
```

**Modified files:**

```
shield/agents/agile-coach-reviewer.md       (~+30 lines — add AC11, AC12, reference skill)
.claude-plugin/marketplace.json             (~1 line — version 2.11.0 → 2.12.0)
```

---

## Task 1: Skill directory scaffolding + SKILL.md skeletons

**Files:**
- Create: `shield/skills/general/prd-review/SKILL.md` (skeleton)
- Create: `shield/skills/general/story-coverage/SKILL.md` (skeleton)
- Create: `shield/skills/general/prd-review/test-fixtures/` (empty dir)

**Why this task first:** Skills must be discoverable by Shield before any further skill content matters. SKILL.md is the entry point Claude Code loads when the skill is referenced.

- [ ] **Step 1.1: Create the prd-review SKILL.md skeleton**

Path: `shield/skills/general/prd-review/SKILL.md`

```markdown
---
name: prd-review
description: Use when a PRD exists (file, paste, URL) and needs gap analysis. Dispatches PM, agile-coach, tech-lead, DX, cost reviewer agents in parallel against a 13-dimension rubric; produces scored summary with severity-tiered gaps and P0-gated verdict. Triggers on /prd-review, review my PRD, PRD gap analysis.
---

# PRD Review

Dispatch parallel expert reviewer agents against a PRD to produce a scored analysis with prioritized gaps, severity tiers, and an enhanced PRD with suggested fixes.

## Output Path — MANDATORY

All review output goes into the feature's prd-review directory:

```
{output_dir}/{feature}/prd-review/{N}-{slug}/
├── summary.md                              ← scored analysis (main output)
├── source-prd.md                           ← verbatim snapshot of original source
├── enhanced-prd.md                         ← P0/P1 inline + P2 comments
├── review-comments.json                    ← canonical structured per-section gaps
└── detailed/
    ├── pm-reviewer.md
    ├── agile-coach-reviewer.md
    ├── tech-lead-reviewer.md
    ├── dx-reviewer.md
    └── cost-reviewer.md
```

Where `{output_dir}` comes from `.shield.json` `output_dir` field (default `docs/shield`), `{feature}` is the feature folder (`{feature-name}-YYYYMMDD`), `{N}` is sequential, `{slug}` is a kebab-case descriptor. **Do NOT** use any other path. The Write tool creates directories automatically.

## When to Use

- User invokes `/prd-review` with a PRD source (file path, URL, or paste)
- User asks "review my PRD" / "what's wrong with this PRD" / "PRD gap analysis"

## When NOT to Use

- **Plan review** (technical breakdown / stories) — use `/plan-review` instead
- **Research review** — use the research workflow's PM-review mode
- **Code review** — use `/review`

## Workflow

(Filled in by Task 9 — orchestration steps + step skeleton)

## See Also

- `ingest.md` — input classification + resolver chain
- `rubric.md` — 13 dimensions, evaluation points, severity model
- `personas.md` — reviewer dispatch prompts
- `scoring.md` — A-F → composite + P0-gate
```

- [ ] **Step 1.2: Create the story-coverage SKILL.md skeleton**

Path: `shield/skills/general/story-coverage/SKILL.md`

```markdown
---
name: story-coverage
description: Use when checking that a PRD's user stories cover all persona-goal combinations and archetypal flows for its feature domain. Consumed by agile-coach reviewer (dim 4 eval points 4f/4g) and /prd author flow. Derives expected stories from personas + goals + domain hints.
---

# Story Coverage

Derive expected user stories from personas + goals + feature domain. Cross-reference NFR/GTM/rollout sections for orphan references.

## When to Use

- `shield:agile-coach-reviewer` calls this skill while grading dim 4 eval points 4f and 4g of a PRD
- `/prd` command (Phase B) calls this skill between PRD Sections 4 (Goals) and 6 (Stories) to scaffold expected stories

## Input contract

The caller provides:
- `personas`: list of {id, name, description, goals}
- `goals`: list of {id, description}
- `feature_domain`: best-effort domain hint (e.g., "auth", "payment", "content", "internal-tool", "infrastructure")
- `existing_sections`: optional — content of NFR / GTM / Rollout / Risks sections (for orphan-reference detection)

## Output contract

Return a list of expected stories with structured metadata:

```json
{
  "expected_stories": [
    {
      "rationale": "persona-goal" | "archetype" | "orphan-reference",
      "persona_id": "P1",
      "goal_id": "G1",
      "archetype": "password-reset",
      "story_title": "Anika resets her password",
      "story_template": { ... },
      "severity": "P0" | "P1" | "P2"
    }
  ]
}
```

## Derivation rules

(Filled in by Task 3)

## See Also

- `archetypes.md` — library of flow patterns per domain
```

- [ ] **Step 1.3: Create the test-fixtures directory**

```bash
mkdir -p shield/skills/general/prd-review/test-fixtures
```

- [ ] **Step 1.4: Commit**

```bash
git add shield/skills/general/prd-review/SKILL.md shield/skills/general/story-coverage/SKILL.md shield/skills/general/prd-review/test-fixtures/
git commit -m "feat(shield): scaffold prd-review + story-coverage skill skeletons"
```

---

## Task 2: Test fixtures — 4 PRDs with intentional gaps

**Files:**
- Create: `shield/skills/general/prd-review/test-fixtures/lean-with-gaps.md`
- Create: `shield/skills/general/prd-review/test-fixtures/standard-with-gaps.md`
- Create: `shield/skills/general/prd-review/test-fixtures/well-formed-standard.md`
- Create: `shield/skills/general/prd-review/test-fixtures/internal-tool.md`

**Why this task before skill content:** Fixtures define what "correct" review output looks like. The skill files are graded against whether subagents catch the planted issues.

For each fixture, document inline what gaps the reviewer SHOULD catch. This is the "expected behavior" specification.

- [ ] **Step 2.1: Create `lean-with-gaps.md`** — lean PRD missing problem clarity + counter-metric

```markdown
# Add password reset to web auth

## Header
Owner · Status: Draft

## Problem
Users keep getting locked out and complain.

## Goals
- Reduce support tickets about locked accounts

## Success metrics
- Fewer tickets

## Open questions
- Should we use magic link or token email?

## Out of scope
- Mobile app password reset
```

**Expected reviewer output (used in Task 12 GREEN verification):**
- Dim 1 (Problem clarity): C/D — vague problem, no baseline ("how many tickets?"), no named user
- Dim 3 (Measurable success): D/F — "fewer tickets" has no threshold, no leading indicator, no counter-metric
- Dim 4 (Scenario coverage & AC): F — no user stories at all (eval point 4f flags missing persona-goal stories via story-coverage skill: "auth → password-reset flow has archetypal stories: request, email/SMS receipt, set new password, confirmation; none present")
- Dim 5 (NFR): N/A for lean — surfaced as informational
- Dim 7 (RACI): D — no owner besides "Owner" header field empty
- Verdict: Needs Work (composite < 2.0, blocked by P0s on dims 4 and 3)

- [ ] **Step 2.2: Create `standard-with-gaps.md`** — standard PRD with 5+ P0-class issues

(Full content provided in Task 2.5 — write a substantial standard PRD with deliberate weaknesses: solution-first ordering, vague language ("intuitive UX"), single metric without counter, no kill-switch criteria, no GTM section, no Day-1 support owner. ~250 lines.)

**Expected reviewer output:**
- Dim 1 (Problem clarity): C — problem present but no baseline numbers
- Dim 2 (Scope): F — no Out of Scope section
- Dim 3 (Measurable success): D — single metric, no counter, "intuitive UX" is unmeasurable
- Dim 4 (Scenario coverage & AC): C — happy paths only, no error/timeout paths in stories (4a fail); ACs are prose, no Given/When/Then (4e fail); state transitions not documented (4c fail). 4f surfaces missing stories: "account recovery, edge case for concurrent sessions"
- Dim 6 (Rollout): D — flag plan mentioned but no kill-switch criteria
- Dim 9 (GTM): F — section entirely absent
- Dim 10 (Support): F — section entirely absent
- Anti-patterns flagged: "vague language" ("intuitive UX", "simple flow"); "single metric without counter"
- Verdict: Needs Work (composite ~1.6, blocked by 4+ P0s)

- [ ] **Step 2.3: Create `well-formed-standard.md`** — strong PRD, should grade Ready

(Full content in Task 2.5 — substantial standard PRD with all 17 sections covered, named owner, real metrics with thresholds, Given/When/Then ACs across multiple stories incl. error paths, explicit kill-switch, GTM + Support sections, named risks with mitigations. ~350 lines.)

**Expected reviewer output:**
- All dims grade A or B
- Verdict: Ready (composite ≥ 3.0)
- No P0s
- May flag 2-3 P2s (minor polish items)

- [ ] **Step 2.4: Create `internal-tool.md`** — features for N/A handling

(Content in Task 2.5 — internal cron job / pipeline. Has Problem, Users (internal team only), Goals, Success metrics, Stories, NFRs, but legitimately N/A on GTM, Support, i18n. ~120 lines.)

**Expected reviewer output:**
- Dim 8 (Legal/privacy): N/A — no user data
- Dim 9 (GTM): N/A — internal-only feature
- Dim 10 (Support): N/A — no external surface
- Dim 5 eval point i18n: N/A — internal English-only tool
- All graded dims A/B
- Verdict: Ready (composite over GRADED dimensions only)

- [ ] **Step 2.5: Write the full contents of fixtures 2.2-2.4**

Write each fixture file with substantial realistic content (250-350 lines each). The fixtures are reused throughout Tasks 12 and 13 RED-GREEN testing; they must be rich enough that reviewers can produce meaningful grading. Use prior PRD examples from the user's research at `/Users/apple/research/prd/docs/shield/prd-skill-20260508/` as style reference.

For each fixture, include a trailing comment block:

```markdown
<!--
EXPECTED REVIEW OUTCOMES (used by RED-GREEN tests, do not delete):
  P0 expected on dims: <list>
  P1 expected on dims: <list>
  N/A expected on dims: <list>
  Composite expected: <range>
  Verdict expected: <Ready|Needs Work|Not Ready>
-->
```

This comment is parsed by the GREEN test harness in Task 13 to verify reviewer agents catch what they should.

- [ ] **Step 2.6: Commit fixtures**

```bash
git add shield/skills/general/prd-review/test-fixtures/
git commit -m "test(shield): add 4 PRD test fixtures for prd-review RED-GREEN validation"
```

---

## Task 3: Story-coverage skill — SKILL.md derivation rules

**Files:**
- Modify: `shield/skills/general/story-coverage/SKILL.md`

**Goal of this task:** Fill in the `## Derivation rules` section of `SKILL.md` with concrete logic the agile-coach reviewer and `/prd` command will follow.

- [ ] **Step 3.1: Append the derivation-rules section**

Append to `shield/skills/general/story-coverage/SKILL.md`:

```markdown
## Derivation rules

### Rule 1 — Persona × Goal cross-product

For each `(persona, goal)` pair, derive at minimum:
- **Happy path story** — the persona achieves the goal successfully
- **One named error/recovery path** — what happens when the happy path fails (timeout, partial failure, user abandons)

If 0 stories address a `(persona, goal)` pair → flag P0 ("persona P's goal G has no story").
If exactly 1 story (happy path only) → flag P1 ("persona P's goal G has happy path but no error/recovery").

### Rule 2 — Archetype match

Look up the feature domain in `archetypes.md`. If the domain matches one of: `auth`, `payment`, `content`, `lifecycle`, `multi-region`, `billing`, `observability`, retrieve its archetypal flow list.

For each archetypal flow that's NOT covered by an existing story → flag P1 or P2 based on the archetype's marked severity in archetypes.md.

Example: domain=auth has archetypes `signup`, `login`, `password-reset`, `account-deletion`. If the PRD has signup but no password-reset story, return:
```json
{
  "rationale": "archetype",
  "archetype": "password-reset",
  "story_title": "User resets forgotten password",
  "severity": "P1"
}
```

### Rule 3 — Orphan-reference detection

Parse `existing_sections` (NFR / GTM / Rollout / Risks). For each mention of an action verb that implies a flow (e.g., "rollback", "deactivate", "delete", "migrate"), check whether a story exists addressing that flow.

Example: NFR section says "supports user-initiated account deletion per GDPR Article 17"; no story covers account deletion → return `{ rationale: "orphan-reference", severity: "P0", source_section: "NFR", source_quote: "supports user-initiated account deletion..." }`.

### Domain detection

If the caller didn't pass `feature_domain`, infer from PRD title + Problem section + Personas:
- keywords like "login", "auth", "password", "session" → auth
- "payment", "checkout", "billing", "subscription" → payment / billing
- "post", "article", "comment", "media" → content
- "cron", "pipeline", "internal tool", "back-office" → internal-tool / infrastructure
- No clear match → return empty domain; skip Rule 2

### Output format

Return JSON with one entry per expected-but-missing story:

```json
{
  "expected_stories": [
    {
      "rationale": "persona-goal | archetype | orphan-reference",
      "persona_id": "P1",
      "goal_id": "G1",
      "archetype": "password-reset",
      "story_title": "User resets forgotten password",
      "severity": "P0 | P1 | P2",
      "story_template": {
        "persona": "P1",
        "goal": "Reset forgotten password without contacting support",
        "happy_path": ["..."],
        "error_paths": ["..."],
        "edge_cases": ["..."],
        "state_transitions": "...",
        "cross_functional_handoffs": "...",
        "acceptance_criteria": [{"given": "...", "when": "...", "then": "..."}]
      }
    }
  ]
}
```
```

- [ ] **Step 3.2: Commit**

```bash
git add shield/skills/general/story-coverage/SKILL.md
git commit -m "feat(shield): story-coverage skill derivation rules (persona-goal + archetype + orphan-reference)"
```

---

## Task 4: Story-coverage skill — archetypes library

**Files:**
- Create: `shield/skills/general/story-coverage/archetypes.md`

**Goal:** Library of common flow patterns per domain. Used by Rule 2 in SKILL.md.

- [ ] **Step 4.1: Write archetypes.md**

Path: `shield/skills/general/story-coverage/archetypes.md`

```markdown
# Story Coverage — Archetypes Library

Common flow patterns per feature domain. Used by `story-coverage` skill Rule 2 to identify archetypal flows missing from a PRD.

Each archetype: name, description, severity if missing, typical persona, typical state transitions.

## Domain: auth

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| signup | New user creates account | P0 | None → Unverified → Verified |
| login | Returning user authenticates | P0 | Logged out → Logging in → Logged in |
| logout | User ends session | P1 | Logged in → Logged out |
| password-reset | User recovers forgotten password | P1 | None → Reset requested → Reset link clicked → New password set |
| email-change | User updates email | P2 | Email confirmed → Email change requested → Email reconfirmed |
| mfa-enrollment | User adds MFA | P2 | MFA off → MFA setup pending → MFA on |
| account-deletion | User deletes account (GDPR / compliance) | P0 | Active → Deletion requested → Soft-deleted → Hard-deleted |
| account-recovery | Recover deleted/disabled account | P2 | Disabled → Recovery requested → Active |

## Domain: payment

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| charge-happy | Customer pays successfully | P0 | Created → Authorized → Captured → Settled |
| charge-decline | Card declined | P0 | Created → Authorized failed |
| charge-partial-success | Some line items succeed, others fail | P1 | Created → Partial settlement |
| refund-full | Customer requests full refund | P1 | Settled → Refund requested → Refunded |
| refund-partial | Customer refunded for some line items | P2 | Settled → Partial refund |
| dispute / chargeback | Bank-initiated dispute | P1 | Settled → Disputed → Won / Lost |
| recurring-renewal | Subscription auto-renews | P1 (if recurring) | Active → Renewal attempting → Active OR Past due |
| recurring-failure | Renewal fails | P1 (if recurring) | Active → Renewal failed → Past due → Cancelled |

## Domain: content

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| create | User creates content | P0 | None → Draft → Published |
| read / view | User views content | P0 (depends — implied if create exists) | — |
| update / edit | User edits existing | P1 | Published → Draft → Published (v2) |
| delete | User deletes | P1 | Published → Deleted (soft) → Hard-deleted |
| share | User shares with others | P2 | Published → Shared (with permission set) |
| search | User finds content | P2 | — |
| archive / unarchive | User archives | P2 | Published → Archived → Published |

## Domain: lifecycle (user account / subscription / feature flag rollout)

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| activation | Newly created → fully active | P1 | Pending → Activating → Active |
| dormancy | User stops engaging | P2 | Active → Dormant |
| churn | User cancels | P1 | Active → Cancelling → Cancelled |
| win-back | Re-engage churned user | P2 | Cancelled → Win-back offered → Active |

## Domain: multi-region / residency

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| region-pinned-write | User write goes to pinned region | P0 (if regulatory) | — |
| cross-region-read | User reads from non-home region | P1 | — |
| residency-conflict | User crosses borders | P1 | — |
| data-purge | Compliance-driven data deletion | P0 (if regulatory) | Resident → Purge scheduled → Purged |

## Domain: billing (separate from payment — invoice + revenue ops)

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| invoice-issued | Customer is billed | P0 | None → Issued |
| invoice-paid | Customer pays invoice | P0 | Issued → Paid |
| invoice-overdue | Customer misses payment | P1 | Issued → Overdue → (Past due actions) |
| credit-issued | Customer receives credit | P2 | None → Credited |

## Domain: observability / ops (internal tooling features)

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| metric-emitted | Feature emits a measured event | P1 | — |
| alert-fired | Threshold breached | P1 | OK → Alerting → Acknowledged → Resolved |
| runbook-followed | On-call resolves alert | P2 | Alerting → Investigating → Resolved |
| capacity-scaling | System scales under load | P2 | At capacity → Scaling up → Scaled |

## Domain: internal-tool

No archetypal flows — internal tools have feature-specific flows. Rule 2 returns empty for this domain. Rule 1 (persona-goal cross-product) and Rule 3 (orphan-reference) still apply.

## How to extend

To add a new domain or archetype:
1. Add the domain section above with archetype rows
2. Update the `feature_domain` inference list in `SKILL.md` if a new keyword should map
3. No code changes needed — this is reference data
```

- [ ] **Step 4.2: Commit**

```bash
git add shield/skills/general/story-coverage/archetypes.md
git commit -m "feat(shield): story-coverage archetypes library (7 domains)"
```

---

## Task 5: prd-review skill — rubric.md (13 dimensions)

**Files:**
- Create: `shield/skills/general/prd-review/rubric.md`

**Goal:** The authoritative rubric document the reviewer agents consult. Specifies the 13 dimensions, their evaluation points, severity, and citations to PM/eng authorities (referenced once here, not in every output).

- [ ] **Step 5.1: Write rubric.md header + dimension structure**

Path: `shield/skills/general/prd-review/rubric.md`

```markdown
# PRD Review Rubric

The 13-dimension rubric used by `shield:prd-review` reviewer agents. Each dimension is graded A/B/C/D/F (or N/A or informational); severity is derived from the evaluation point's classification (Critical / Important / Warning).

## Severity mapping

- **Critical eval point graded D or F** → P0 (blocker; gates verdict)
- **Important eval point graded C-D** → P1 (should fix)
- **Warning eval point graded C** → P2 (nice to have)
- **N/A** (with mandatory reasoning) → excluded from composite
- **Informational** (lean PRD structural exemption) → excluded from composite

Bare N/A (no reasoning) → graded F.

## Dimension states by PRD type

| Dim | Standard | Lean |
|---|---|---|
| 1 Problem clarity | Graded | Graded |
| 2 Scope boundaries | Graded | Graded |
| 3 Measurable success | Graded | Graded |
| 4 Scenario coverage & AC | Graded | Graded |
| 5 NFR coverage | Graded | Informational |
| 6 Rollout & ops | Graded | Informational |
| 7 RACI & approvals | Graded | Graded |
| 8 Legal / privacy / compliance | Graded | Graded |
| 9 GTM / customer-comms | Graded | Informational |
| 10 Support / CX impact | Graded | Informational |
| 11 Why now & cost-of-inaction | Graded | Graded |
| 12 Risks & assumptions | Graded | Graded |
| 13 Cost & resource impact | Graded | Informational |

## Dim 1 — Problem clarity (PM)

| ID | Eval point | Severity |
|---|---|---|
| 1a | Named user / persona present (not "users") | Critical |
| 1b | Baseline data (current state, numbers) | Important |
| 1c | "Why now" articulated (urgency, opportunity cost) | Warning |
| 1d | First-person user evidence or quotes (research backing) | Warning |

**Authorities:** Lenny Rachitsky on problem statement primacy; Cagan on discovery-before-spec.

## Dim 2 — Scope boundaries (PM)

| ID | Eval point | Severity |
|---|---|---|
| 2a | Explicit "Out of Scope" / "Non-goals" / "No-gos" section present | Critical |
| 2b | Out-of-scope items have one-line rationale | Important |
| 2c | Scope creep risks acknowledged | Warning |

**Authorities:** Atlassian, Shape Up, Kevin Yien (Square), Plane.so — convergent across all PM template traditions.

## Dim 3 — Measurable success (PM)

| ID | Eval point | Severity |
|---|---|---|
| 3a | Metrics have numeric thresholds (not "improve X") | Critical |
| 3b | Both leading AND lagging metrics present | Critical |
| 3c | Counter-metric defined (prevents gaming) | Important |
| 3d | Dashboard plan or "what we'll track on Monday" specified | Warning |

**Authorities:** Shreyas Doshi on dashboard mockups + usage vs impact metrics; Lenny on problem statement primacy.

## Dim 4 — Scenario coverage & AC testability (Agile-coach)

| ID | Eval point | Severity |
|---|---|---|
| 4a | Each story has happy path AND error/timeout/abandon paths | Critical |
| 4b | Edge cases enumerated per story (boundary conditions, concurrent state, partial failures) | Important |
| 4c | State transitions / lifecycle documented for non-trivial entities | Important |
| 4d | Cross-functional handoffs noted (downstream teams pulled in) | Important |
| 4e | ACs in Given/When/Then format (bullets allowed for lean) | Important |
| 4f | Every persona-goal pair has ≥ 1 story addressing it (consume `story-coverage` skill) | Critical |
| 4g | Archetypal flows for the feature domain are covered (consume `story-coverage` skill) | Important |

Plus the agile-coach's existing AC1-AC10 framework applies; the agile-coach merges them when grading.

**Authorities:** Plane.so, Routine.co on engineer-perceived gaps; Altexsoft on per-story acceptance criteria.

## Dim 5 — NFR coverage (Tech-lead)

| ID | Eval point | Severity |
|---|---|---|
| 5a | Performance budget specified (latency, throughput) | Critical |
| 5b | Security: auth model + threat model / abuse cases | Critical |
| 5c | RBAC / permissions matrix (if multi-role feature) | Important |
| 5d | Accessibility (WCAG level if user-facing) | Important |
| 5e | Privacy (data classification, retention) | Critical |
| 5f | Telemetry / event taxonomy completeness — events named, not just "we'll instrument" | Important |
| 5g | i18n / l10n (system-level: RTL, encoding, formats, translation pipeline — N/A allowed for English-only products) | Warning |

**Authorities:** Routine.co (engineer-trust gaps); Plane.so (engineer-friendly scaffold).

## Dim 6 — Rollout & ops (Tech-lead)

| ID | Eval point | Severity |
|---|---|---|
| 6a | Flag plan (feature flag) specified | Critical |
| 6b | Canary / staged rollout slices defined | Important |
| 6c | Kill-switch criteria (what signals trigger rollback) | Critical |
| 6d | Abort thresholds named (specific metric values) | Important |
| 6e | Data migration plan (if touches existing data) | Critical |
| 6f | Backward compatibility commitments (API consumers, schema readers) | Important |

**Authorities:** Routine.co (rollout slices, kill switches); Plane.so (engineer-friendly rollout).

## Dim 7 — RACI & approvals (PM)

| ID | Eval point | Severity |
|---|---|---|
| 7a | Named PRD owner | Critical |
| 7b | Named decision-maker for ambiguity | Important |
| 7c | Sign-off path for Legal / Security / Support | Important |
| 7d | Status / last-updated in header | Warning |

**Authorities:** Atlassian header convention; Plane.so on staleness.

## Dim 8 — Legal / privacy / compliance (PM)

| ID | Eval point | Severity |
|---|---|---|
| 8a | Data classification specified (PII / payment / public / etc.) | Critical |
| 8b | PII handling (collection, storage, retention) | Critical |
| 8c | Regulated-industry sign-off path (if applicable) | Important |
| 8d | Compliance-driven flows documented (user-initiated deletion per GDPR Art. 17, etc.) | Important |

## Dim 9 — GTM / customer-comms (PM)

| ID | Eval point | Severity |
|---|---|---|
| 9a | Pricing / packaging implications addressed | Important |
| 9b | In-app messaging / release notes plan | Important |
| 9c | CS / sales enablement (who tells customers) | Warning |
| 9d | Beta / early-access plan (if applicable) | Warning |

## Dim 10 — Support / CX impact (PM)

| ID | Eval point | Severity |
|---|---|---|
| 10a | Day-1 ticket owner named | Critical |
| 10b | Runbook or escalation path | Important |
| 10c | Sales enablement (talking points for sales/CS) | Warning |
| 10d | Training plan for support team | Warning |

## Dim 11 — Why now & cost-of-inaction (PM)

| ID | Eval point | Severity |
|---|---|---|
| 11a | "Why now" articulated (regulatory, market, competitive, internal urgency) | Critical |
| 11b | Cost-of-inaction quantified (what happens if we wait) | Important |
| 11c | Sequencing rationale (why this before X) | Warning |

## Dim 12 — Risks & assumptions (PM)

| ID | Eval point | Severity |
|---|---|---|
| 12a | Risks enumerated WITH mitigations and owners | Critical |
| 12b | Validated vs unvalidated assumptions distinguished | Important |
| 12c | Counter-arguments / dissenting views noted (if any exist) | Warning |

## Dim 13 — Cost & resource impact (Cost reviewer)

| ID | Eval point | Severity |
|---|---|---|
| 13a | Build cost estimate (eng-time, dependencies) | Important |
| 13b | Run cost at projected scale (compute, storage, bandwidth, $$/month) | Critical |
| 13c | Cost counter-metric (won't exceed $X/user/month) | Important |
| 13d | Cost-aware design alternatives noted | Warning |

## Anti-patterns (DX reviewer; cross-cutting)

Flagged separately in summary.md, not graded into a dimension:

- **Solution-first ordering** (problem buried below the fold)
- **Vague language** (specific quotes: "simple", "intuitive", "performant")
- **Single metric without counter** (gaming risk)
- **Acceptance criteria as prose only** (no testable conditions)
- **"We'll figure out rollout later"** (rollout missing or hand-waved)
- **No status/owner/last-updated header** (staleness risk)
- **Risks listed without mitigations** (theater)
- **Happy-path-only scenarios** (no error or edge handling)
```

- [ ] **Step 5.2: Commit**

```bash
git add shield/skills/general/prd-review/rubric.md
git commit -m "feat(shield): prd-review 13-dimension rubric with eval points + severity"
```

---

## Task 6: prd-review skill — ingest.md

**Files:**
- Create: `shield/skills/general/prd-review/ingest.md`

**Goal:** Classification (local/URL/paste) + resolver chain with runtime MCP discovery + WebFetch fallback + paste fallback. No baked-in provider defaults.

- [ ] **Step 6.1: Write ingest.md**

Path: `shield/skills/general/prd-review/ingest.md`

```markdown
# PRD Review — Ingest Pipeline

Classify input, route to a resolver, snapshot the resolved content to `source-prd.md`.

## Step 1: Classify the input

| Class | Detection rule | Handler |
|---|---|---|
| **Local file** | First arg matches `^/` or `^\./` or doesn't match `^https?://` AND is a path to an existing file | Read tool |
| **HTTP(S) URL** | First arg matches `^https?://` | Resolver chain (Step 2) |
| **Paste** | No first arg, OR first arg is `--paste`, OR the user pasted content into the prompt | Read from prompt directly |

If classification ambiguous (e.g., a relative path that's also a valid URL), prefer local-file classification — explicit URL prefix is required for URL handling.

## Step 2: Resolver chain (URLs only)

Walk the resolvers in order. Stop at the first one that returns content.

### Resolver order

1. **Custom resolvers from `.shield.json`** (`prd_ingest_resolvers` array) — matched first
2. **Internal known-host map** (below) — matched second
3. **WebFetch** — catch-all for any HTTP(S) URL (public pages only)
4. **Paste fallback** — if all above fail, prompt the user to paste content

### Internal known-host map (Shield-side knowledge — not config)

| URL pattern | MCP-name pattern Shield searches for at runtime | If MCP absent |
|---|---|---|
| `notion.so/*` or `*.notion.so/*` | `*notion*` (e.g., `notion-fetch`) | Fall through to WebFetch |
| `*.atlassian.net/wiki/*` | `*atlassian*` or `*confluence*` | Fall through to WebFetch |
| `docs.google.com/document/*` | `*google*drive*` or `*google*docs*` | Fall through to WebFetch |
| `github.com/*/blob/*` (any file) | (no MCP needed) | Use `gh api` via Bash directly |
| anything else (https) | (no map entry) | Fall through to WebFetch |

### Resolution flow per URL

1. Match URL against `prd_ingest_resolvers` config first
2. Match URL against internal known-host map
3. If matched, check whether the corresponding MCP is currently available
   - Available → call MCP, return content as markdown
   - Not available → log specific error ("MCP `*atlassian*` not present"), continue to step 4
4. Try WebFetch on the URL
   - Returns content → convert to markdown if needed, return
   - Returns 4xx/5xx or network error → log, continue to step 5
5. Paste fallback — emit to user: "Couldn't fetch from <URL> (reason: <X>). Paste the PRD content here." Then read pasted content.

## Step 3: Convert to markdown + snapshot

Regardless of source class, normalize output to markdown:
- Local file: if `.md`/`.txt` → as-is; if `.pdf` → use Read tool's PDF handling; if `.docx` → paste fallback (DOCX not natively supported)
- URL response: if `Content-Type: text/html` → strip and convert; if already markdown → as-is
- Paste: as-is

Write the result to `{output_dir}/{feature}/prd-review/{N}-{slug}/source-prd.md`. This snapshot is the canonical input to all reviewer agents.

## Step 4: PRD type detection (lean vs standard)

After snapshot, parse `source-prd.md` for top-level `##` headings:

- If headings ⊆ {Header, Problem, Users, Goals, Metrics, Open Questions, Out of scope} → likely **lean**
- If 8+ standard-scaffold sections present → likely **standard**
- Otherwise → likely **standard** (default; lean is opt-in by structural minimalism)

Surface detection result + confirm:

> "This looks like a **standard** PRD (detected sections: Header, Problem, Users, Goals, Metrics, Stories, FRs, NFRs, Rollout, Risks, Out of scope). Apply standard rubric? (yes / lean / standard)"

User can override.

## Failure flow (uniform across resolvers)

When any resolver fails — MCP unavailable, network error, parse error, auth required:
1. Emit specific error: "Notion MCP not authenticated" / "URL returned 403" / "Atlassian MCP not present in session"
2. Offer paste fallback in the same turn
3. User pastes content → continue normally
4. If user declines, abort with clear message; do NOT produce a partial review

## See Also

- `SKILL.md` Step 1 calls into this file's Step 1
- `rubric.md` — the rubric used downstream of ingest
```

- [ ] **Step 6.2: Commit**

```bash
git add shield/skills/general/prd-review/ingest.md
git commit -m "feat(shield): prd-review ingest pipeline (classify + resolver chain + fallbacks)"
```

---

## Task 7: prd-review skill — scoring.md

**Files:**
- Create: `shield/skills/general/prd-review/scoring.md`

**Goal:** Mirror `plan-review/scoring.md` structure, add P0-gate verdict logic.

- [ ] **Step 7.1: Write scoring.md**

Path: `shield/skills/general/prd-review/scoring.md`

```markdown
# PRD Review Scoring

Aligned with `shield/skills/general/plan-review/scoring.md` — same A-F grade scale and weighted-composite formula, with an added P0-gate on the verdict.

## Grade Scale

| Grade | Meaning | Numeric |
|---|---|---|
| A | Fully addressed, no concerns | 4 |
| B | Addressed with minor gaps | 3 |
| C | Partially addressed, notable gaps | 2 |
| D | Barely addressed, significant issues | 1 |
| F | Missing or critically flawed | 0 |

Plus two non-numeric states:
- **N/A** — excluded from composite (reasoning required; bare N/A grades F)
- **Informational** — excluded from composite (lean-PRD structural exemption)

## Per-evaluation-point grade

Each evaluation point in `rubric.md` is graded A-F by the owning persona's reviewer agent.

## Per-dimension grade

Average all evaluation points within the dimension (numeric values), round to nearest letter:

| Average Range | Letter Grade |
|---|---|
| 3.5 – 4.0 | A |
| 2.5 – 3.4 | B |
| 1.5 – 2.4 | C |
| 0.5 – 1.4 | D |
| 0.0 – 0.4 | F |

N/A or informational dimensions are skipped entirely (not included in the persona's average).

## Per-persona grade

Average that persona's owned dimensions' numeric values, round to letter. Same range table as above.

## Composite readiness score

Weighted average of all activated personas' grades.

**Persona weights for `/prd-review`:**

| Persona | Weight | Role |
|---|---|---|
| `shield:product-manager-reviewer` | 1.0 | Core |
| `shield:agile-coach-reviewer` | 1.0 | Core |
| `shield:architecture-reviewer` (tech-lead) | 1.0 | Core |
| `shield:dx-engineer-reviewer` | 0.7 | Supporting |
| `shield:cost-reviewer` | 0.7 | Supporting |

**Formula:**

```
composite = sum(persona_numeric_grade × weight) / sum(activated_weights)
```

Only activated personas contribute. Denominator is the sum of weights for personas that actually ran (typically all 5; configurable via `.shield.json` `prd_review_personas`).

## Priority classification

Recommendations are classified by the evaluation point that triggered them:

| Priority | Triggered by | Meaning |
|---|---|---|
| P0 (High) | Grade D or F on a **Critical** severity evaluation point | Blocks downstream `/plan`. Must fix before proceeding. |
| P1 (Medium) | Grade C-D on an **Important** severity eval point | Should fix for PRD quality. |
| P2 (Low) | Grade C on a **Warning** severity eval point, or minor gaps on B-graded points | Nice to have. |

## Verdict logic — composite + P0 gate

The composite score alone can hide a fatal gap (the "averaging problem"): enough strong dimensions can drown out one F on a critical one. P0 presence GATES the verdict.

| Condition | Verdict |
|---|---|
| Composite < 1.5 | **Not Ready** |
| Composite 1.5 – 2.4 | **Needs Work** |
| Composite ≥ 2.5 AND any P0 present | **Needs Work** (composite is informational; P0 floor binds) |
| Composite ≥ 2.5 AND zero P0s | **Ready** |

**Header line in `summary.md`:**
- With P0s: `**Verdict:** Needs Work (composite 3.3, blocked by 4 P0s)`
- Clean: `**Verdict:** Ready (composite 3.4)`

This makes the P0 gate visible — readers immediately see why a high composite isn't enough.

## Composite computation example (standard PRD)

```
PM reviewer        grade B (3.0), weight 1.0
Agile-coach        grade C (2.0), weight 1.0
Tech-lead          grade B (3.0), weight 1.0
DX reviewer        grade A (4.0), weight 0.7
Cost reviewer      grade B (3.0), weight 0.7

composite = (3.0×1.0 + 2.0×1.0 + 3.0×1.0 + 4.0×0.7 + 3.0×0.7) / (1.0 + 1.0 + 1.0 + 0.7 + 0.7)
          = (3.0 + 2.0 + 3.0 + 2.8 + 2.1) / 4.4
          = 12.9 / 4.4
          = 2.93 → B

If 2 P0s exist (e.g., dim 9 GTM=F and dim 7 RACI=F):
  Verdict: Needs Work (composite 2.93, blocked by 2 P0s)
Else:
  Verdict: Ready
```
```

- [ ] **Step 7.2: Commit**

```bash
git add shield/skills/general/prd-review/scoring.md
git commit -m "feat(shield): prd-review scoring with A-F + P0-gate verdict"
```

---

## Task 8: prd-review skill — personas.md (5 dispatch prompts)

**Files:**
- Create: `shield/skills/general/prd-review/personas.md`

**Goal:** The 5 reviewer dispatch prompts. Each persona receives PRD content + the rubric (`rubric.md`) + its assigned dimensions; returns graded evaluation points + per-dimension grades.

- [ ] **Step 8.1: Write personas.md**

Path: `shield/skills/general/prd-review/personas.md`

```markdown
# PRD Review Persona Catalog

Five reviewer agents dispatched in parallel against a PRD. Each receives the PRD content + rubric + its assigned dimensions; each returns a graded report.

## Persona dispatch table

| Persona | Agent ID | Weight | Dimensions owned | Mode hint |
|---|---|---|---|---|
| PM reviewer | `shield:product-manager-reviewer` | 1.0 | 1, 2, 3, 7, 8, 9, 10, 11, 12 | Standalone |
| Agile-coach reviewer | `shield:agile-coach-reviewer` | 1.0 | 4 (incl. AC11/AC12 via story-coverage skill) | Standalone |
| Tech-lead reviewer | `shield:architecture-reviewer` | 1.0 | 5, 6 | Standalone |
| DX reviewer | `shield:dx-engineer-reviewer` | 0.7 | Anti-patterns + cross-cutting clarity | Standalone |
| Cost reviewer | `shield:cost-reviewer` | 0.7 | 13 | Standalone |

## Dispatch prompts

Each persona receives a prompt of this shape (substituted per persona):

```
You are reviewing a PRD in PRD-Review mode. Mode: Standalone.

**PRD source:** {source-prd.md path}
**PRD type:** {standard | lean — confirmed by user}
**Your assigned dimensions:** {list from dispatch table}

**Rubric:** Read `shield/skills/general/prd-review/rubric.md` for evaluation points per dimension, severity model, and grade scale. Read `shield/skills/general/prd-review/scoring.md` for the A-F → composite logic.

**Your job:**
1. Read the PRD at the path above.
2. For each of YOUR assigned dimensions, grade each evaluation point A-F (or N/A with reasoning, or informational for lean dims).
3. Aggregate to a per-dimension grade.
4. Aggregate your dimensions to a persona grade.
5. Identify gaps — for each non-A grade, write a one-sentence gap description.
6. For each gap, suggest a fix (one or two sentences) suitable for use in `enhanced-prd.md` annotation.

**Output format:** Return JSON conforming to this shape:

{
  "persona": "<your agent id>",
  "persona_grade": "A|B|C|D|F",
  "dimensions": [
    {
      "id": 1,
      "name": "Problem clarity",
      "grade": "A|B|C|D|F|N/A|informational",
      "na_reasoning": "<if N/A>",
      "evaluation_points": [
        { "id": "1a", "grade": "A|B|C|D|F", "severity": "Critical|Important|Warning", "gap": "<one sentence or null>", "suggestion": "<one sentence or null>" }
      ]
    }
  ],
  "anti_patterns": [ {"name": "...", "evidence_line": 42, "evidence_quote": "..."} ]  // DX reviewer only
}
```

### Special instructions per persona

**PM reviewer:** When grading dim 11 (Why now & cost-of-inaction) and dim 12 (Risks & assumptions), apply your existing PF1-PF11 evaluation framework where relevant.

**Agile-coach reviewer:** When grading dim 4:
- Apply your existing AC1-AC10 evaluation framework to eval points 4a-4e
- Apply NEW AC11 (Persona-goal coverage) and AC12 (Archetypal flow coverage):
  - Invoke the `shield:story-coverage` skill, passing personas + goals + detected feature domain
  - For each `expected_story` the skill returns that has NO matching story in the PRD's Section 6, count as a gap
  - Severity: per the skill's returned `severity` field

**Tech-lead reviewer (architecture-reviewer):** When grading dim 5 NFRs, treat 5b (security + threat model) and 5e (privacy) as Critical for any feature with user data; treat them as Important for purely internal infrastructure features.

**DX reviewer:** Your primary output is the `anti_patterns` array. You don't own a dimension column in the composite; you contribute via flagging cross-cutting issues that show up in `summary.md`'s "Anti-patterns" section.

**Cost reviewer:** When the feature is clearly internal-only (e.g., test fixture `internal-tool.md`), 13a-13d may be N/A; grade with N/A reasoning.

## Aggregation step (orchestrator, not persona)

After all 5 personas return JSON, the orchestrator:
1. Combines dimensions across personas
2. Computes composite per `scoring.md` formula
3. Applies P0-gate
4. Writes to output artifacts (see SKILL.md Step 6)
```

- [ ] **Step 8.2: Commit**

```bash
git add shield/skills/general/prd-review/personas.md
git commit -m "feat(shield): prd-review 5-persona dispatch prompts (PM/agile/tech/DX/cost)"
```

---

## Task 9: prd-review skill — main SKILL.md (orchestration)

**Files:**
- Modify: `shield/skills/general/prd-review/SKILL.md` (replace the `## Workflow` placeholder from Task 1)

**Goal:** Fill in the orchestration workflow that ties ingest → type detection → persona dispatch → aggregation → output artifacts.

- [ ] **Step 9.1: Replace SKILL.md workflow section**

Open `shield/skills/general/prd-review/SKILL.md`. Replace the line `(Filled in by Task 9 — orchestration steps + step skeleton)` with the following content:

```markdown
## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Condition | Mandatory |
|---|---|---|---|
| 1 | Classify input (local/URL/paste) — see `ingest.md` Step 1 | always | Yes |
| 2 | Resolve via resolver chain — see `ingest.md` Step 2 | URL only | URL only |
| 3 | Snapshot to source-prd.md — see `ingest.md` Step 3 | always | Yes |
| 4 | Detect PRD type, confirm with user — see `ingest.md` Step 4 | always | Yes |
| 5 | Dispatch 5 reviewer agents in parallel — see `personas.md` | always | Yes |
| 6 | Aggregate grades + compute composite + apply P0-gate — see `scoring.md` | always | Yes |
| 7 | Generate enhanced-prd.md with inline annotations | always | Yes |
| 8 | Write summary.md, review-comments.json, detailed/<persona>.md | always | Yes |
| 9 | Update manifest.json, regenerate index.html dashboard | always | Yes |
| 10 | Offer apply options (use as canonical / convert back / skip) | always | Yes |

## Workflow

### 1. Read context

- Read `.shield.json` for: `output_dir` (default `docs/shield`), `prd_review_personas` (default all 5), `prd_ingest_resolvers` (default `[]`)
- Determine feature folder context: `--feature <name>` flag, or `--name`, or fall back to a prompt asking the user

### 2. Ingest

Follow `ingest.md` Steps 1-3:
- Classify input (local path / URL / paste)
- Route through resolver chain if URL
- Snapshot result to `{output_dir}/{feature}/prd-review/{N}-{slug}/source-prd.md`

The slug is derived from the feature name + a short descriptor (e.g., `1-add-oauth-login`).

### 3. Type detection + confirmation

Follow `ingest.md` Step 4. Confirm with user. Note: PRD-type override is per-invocation, not configured.

### 4. Persona dispatch (parallel)

Read `personas.md` for the 5 dispatch prompts. Substitute the per-persona variables and dispatch with the `Agent` tool, `subagent_type` set per the persona's agent ID.

**Critical:** dispatch all 5 in a single response (parallel). Aggregating after waits.

### 5. Aggregate

Parse each persona's returned JSON. Apply `scoring.md`:
- Per-dimension grades (already in persona JSON)
- Per-persona grades (already in persona JSON)
- Composite weighted average
- Detect P0s (any Critical eval point graded D or F)
- Apply P0-gate to verdict

### 6. Generate enhanced-prd.md

For each gap-with-suggestion in the aggregated JSON:
- P0 or P1: insert inline in the relevant section of source-prd.md content; wrap with `<!-- [from: <Persona>] -->` attribution
- P2: insert as a comment block adjacent to the relevant section, prefixed `<!-- Suggestion (<Persona>): ... -->`
- Informational: insert as comment with `<!-- [informational] -->` tag

Preserve source-prd.md's exact structure; only ADD content, never replace.

Write the result to `enhanced-prd.md`.

### 7. Write output artifacts

| File | Content |
|---|---|
| `summary.md` | Scored analysis (template in `templates.md` if you create one, or follow the shape in the spec's Architecture summary) |
| `source-prd.md` | (already written by Step 2) |
| `enhanced-prd.md` | (Step 6 output) |
| `review-comments.json` | Aggregated JSON conforming to the schema in spec's "Enhanced PRD output and comments export" section |
| `detailed/pm-reviewer.md` | PM persona's full report (markdown rendering of their JSON, kept for skeptics) |
| `detailed/agile-coach-reviewer.md` | Agile-coach persona's full report |
| `detailed/tech-lead-reviewer.md` | Tech-lead persona's full report |
| `detailed/dx-reviewer.md` | DX persona's anti-pattern findings + clarity notes |
| `detailed/cost-reviewer.md` | Cost persona's full report |

### 8. Update manifest + dashboard

- Append a new entry to `{output_dir}/manifest.json`
- Regenerate `{output_dir}/index.html` to show the new review with verdict badge

### 9. Offer apply options

Emit to user (template):

```
PRD Review complete.

Verdict: <Ready | Needs Work (composite X.X, blocked by N P0s) | Not Ready>

Files written:
- summary.md       — scored analysis
- enhanced-prd.md  — your PRD with suggested fixes applied
- review-comments.json — machine-readable for converters
- detailed/<persona>.md — per-reviewer findings

What next?
1. **Use enhanced as canonical PRD** — copy enhanced-prd.md to prd/{N}-{slug}/prd.md so downstream Shield commands consume the fixed version
2. **Convert back to original format** — produce enhanced-prd.<ext> in source's format (HTML / Notion-flavored markdown)
3. **Skip** — keep enhanced-prd.md in the review folder; do nothing else
```

User picks; Shield executes.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Dispatching reviewer agents sequentially | Dispatch all 5 in a single response (parallel) |
| Writing review output to the wrong path | Must be `{output_dir}/{feature}/prd-review/{N}-{slug}/` — never `shield/` or `.shield/` |
| Overwriting source-prd.md after dispatch | Source snapshot is immutable; only enhanced-prd.md gets annotated |
| Skipping P0-gate when verdict has P0 + high composite | Verdict is Needs Work regardless of composite if any P0 exists |
| Producing enhanced-prd.md without inline attribution | Every P0/P1 inline edit MUST have `<!-- [from: <Persona>] -->` attribution |
| Auto-generating review-comments.md | Don't — JSON is canonical, markdown view is summary.md (per spec's drop-review-comments-md decision) |
```

- [ ] **Step 9.2: Commit**

```bash
git add shield/skills/general/prd-review/SKILL.md
git commit -m "feat(shield): prd-review SKILL.md orchestration workflow + step skeleton"
```

---

## Task 10: Extend agile-coach-reviewer agent

**Files:**
- Modify: `shield/agents/agile-coach-reviewer.md`

**Goal:** Add AC11 (Persona-goal coverage) and AC12 (Archetypal flow coverage) to the existing AC1-AC10 evaluation framework. Reference the `shield:story-coverage` skill.

- [ ] **Step 10.1: Read the current agile-coach-reviewer.md and find the AC1-AC10 table**

```bash
grep -n "AC1\|AC10\|AC11\|## Mode" shield/agents/agile-coach-reviewer.md | head -20
```

Locate the table containing the existing AC1-AC10 evaluation points (likely under a "Plan Review" mode section).

- [ ] **Step 10.2: Add a PRD Review mode + AC11/AC12 rows**

Append a new mode section to the agent file. Following the structure of the existing mode sections, add:

```markdown
## Mode: PRD Review

Dispatched by `shield:prd-review` skill against a PRD (not a plan). Grades dim 4 (Scenario coverage & AC testability) of the PRD-review rubric.

### Evaluation framework (extends AC1-AC10)

Apply the existing AC1-AC10 evaluation points to the PRD's user stories (Section 6). Plus the following PRD-specific additions:

| ID | Check | What to look for | Severity |
|---|---|---|---|
| AC11 | Persona-goal coverage | Every persona-goal pair in the PRD has at least one user story addressing it | Critical |
| AC12 | Archetypal flow coverage | Common flows for the feature's domain are present (auth → signup + login + recover + delete; payment → happy + decline + refund; etc.) | Important |

### How to grade AC11 + AC12

Invoke the `shield:story-coverage` skill with:
- `personas`: extracted from PRD Section 3 (Target users / personas)
- `goals`: extracted from PRD Section 4 (Goals & non-goals)
- `feature_domain`: inferred from PRD title + Problem + personas (see story-coverage SKILL.md "Domain detection")
- `existing_sections`: NFR / GTM / Rollout / Risks sections (for orphan-reference detection)

The skill returns a list of `expected_stories` that SHOULD exist. For each entry where no matching story is found in PRD Section 6:
- Count as a gap for AC11 (if rationale = "persona-goal" or "orphan-reference") or AC12 (if rationale = "archetype")
- Use the entry's `severity` field as the gap's severity

### Output contribution

Your contribution to the `dim 4` grade in the PRD-review composite is the average of AC1-AC10 + AC11 + AC12 grades, mapped via the A-F scale in `scoring.md`.
```

- [ ] **Step 10.3: Commit**

```bash
git add shield/agents/agile-coach-reviewer.md
git commit -m "feat(shield): agile-coach AC11/AC12 for PRD-review feature-level story coverage"
```

---

## Task 11: Command file — `/prd-review`

**Files:**
- Create: `shield/commands/prd-review.md`

**Goal:** The slash command that triggers the skill. Follows the pattern of existing commands like `shield/commands/plan-review.md`.

- [ ] **Step 11.1: Inspect plan-review command for template**

```bash
cat shield/commands/plan-review.md
```

- [ ] **Step 11.2: Write commands/prd-review.md**

Path: `shield/commands/prd-review.md`

```markdown
---
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Run multi-persona PRD review against a 13-dimension rubric. Produces scored summary with severity-tiered gaps and an enhanced PRD with suggested fixes.
---

# /prd-review

Dispatch parallel reviewer agents against a PRD and produce a scored gap analysis.

## Usage

```
/prd-review                              # prompts for a source
/prd-review <path>                       # local file path
/prd-review <url>                        # any URL (Notion, Confluence, Google Docs, public web)
/prd-review --paste                      # read pasted content from prompt
/prd-review --feature <name> <source>    # explicit feature folder name
```

## What it does

1. **Classifies** the input as local file / URL / paste
2. **Resolves URLs** via runtime MCP discovery (Notion MCP if present for `notion.so/*`, Atlassian MCP for `*.atlassian.net/wiki/*`, etc.) with WebFetch fallback and universal paste fallback
3. **Snapshots** the source to `source-prd.md` (immutable)
4. **Detects PRD type** (lean vs standard) and confirms with user
5. **Dispatches 5 reviewer agents** in parallel: PM (`shield:product-manager-reviewer`), Agile-coach (`shield:agile-coach-reviewer`), Tech-lead (`shield:architecture-reviewer`), DX (`shield:dx-engineer-reviewer`), Cost (`shield:cost-reviewer`)
6. **Aggregates** grades into a composite verdict (A-F per dimension → per-persona → weighted composite); applies P0-gate
7. **Writes 5 output artifacts** to `{output_dir}/{feature}/prd-review/{N}-{slug}/`:
   - `summary.md` — scored gap analysis
   - `source-prd.md` — verbatim source snapshot
   - `enhanced-prd.md` — P0/P1 inline annotations + P2 comments
   - `review-comments.json` — canonical machine-readable gap export
   - `detailed/<persona>.md` × 5 — per-reviewer detailed reports
8. **Updates** `manifest.json` and `index.html` dashboard
9. **Offers apply options** — use enhanced as canonical PRD / convert back to original format / skip

## Reference

Full behavior in `shield/skills/general/prd-review/SKILL.md`.

## See also

- `/plan` — generate a technical plan from a PRD
- `/plan-review` — review a generated plan
- `/research` — gather product + tech context before authoring
```

- [ ] **Step 11.3: Commit**

```bash
git add shield/commands/prd-review.md
git commit -m "feat(shield): /prd-review command (Phase A)"
```

---

## Task 12: RED test — baseline without skill

**Goal:** Document baseline reviewer behavior WITHOUT the new skill content. This is the RED side of RED-GREEN — proves the skill adds value.

- [ ] **Step 12.1: Run a baseline review on each fixture WITHOUT the prd-review skill**

For each of the 4 fixture PRDs, dispatch each reviewer agent with a generic prompt (no rubric reference). Use the Agent tool:

For `lean-with-gaps.md`:

```
Agent(
  subagent_type="shield:agile-coach-reviewer",
  prompt="Read the PRD at shield/skills/general/prd-review/test-fixtures/lean-with-gaps.md. Identify any gaps in story coverage, acceptance criteria, or sprint readiness. Return a list of gaps."
)
```

Repeat for the other 3 fixtures and the other 4 reviewer agents (20 dispatches total — can be done in batches of 5 in parallel).

- [ ] **Step 12.2: Document baseline findings**

For each fixture × persona combination, record in `shield/skills/general/prd-review/test-fixtures/RED-baseline.md` (a temporary file, deleted after Task 13):
- What gaps the reviewer caught
- What gaps from the fixture's EXPECTED REVIEW OUTCOMES section were MISSED
- Severity accuracy (did they grade P0 as P0?)

This is the BASELINE the GREEN test in Task 13 must exceed.

- [ ] **Step 12.3: Commit the baseline**

```bash
git add shield/skills/general/prd-review/test-fixtures/RED-baseline.md
git commit -m "test(shield): RED baseline — reviewer behavior without prd-review skill"
```

---

## Task 13: GREEN test — with skill loaded

**Goal:** Re-run the same reviewer agents WITH the new skill content loaded. Verify they catch the gaps documented in each fixture's EXPECTED REVIEW OUTCOMES section.

- [ ] **Step 13.1: Run reviewer agents WITH the prd-review skill content**

For each fixture × persona, dispatch with a prompt that explicitly references the rubric:

```
Agent(
  subagent_type="shield:agile-coach-reviewer",
  prompt="""
  You are reviewing a PRD in PRD-Review mode.
  Read the rubric at shield/skills/general/prd-review/rubric.md.
  Read the dispatch prompt template at shield/skills/general/prd-review/personas.md (your section: Agile-coach reviewer).
  Read the PRD at shield/skills/general/prd-review/test-fixtures/lean-with-gaps.md.
  Apply your AC1-AC10 framework PLUS AC11 (Persona-goal coverage) and AC12 (Archetypal flow coverage), invoking the shield:story-coverage skill at shield/skills/general/story-coverage/.
  Return your dimension 4 grade and gaps as JSON conforming to personas.md output format.
  """
)
```

- [ ] **Step 13.2: Compare against EXPECTED REVIEW OUTCOMES**

For each fixture × persona:
- Parse the agent's JSON output
- Cross-reference against the fixture's trailing `<!-- EXPECTED REVIEW OUTCOMES -->` comment block
- Confirm the agent caught: every P0 in expected, every N/A correctly identified, every dimension graded within ±1 letter of expected

- [ ] **Step 13.3: Iterate on gaps**

If any fixture × persona combination misses an expected gap or grades wildly off:
- Identify which skill file's content is insufficient (rubric.md eval points too vague? personas.md prompt missing instruction?)
- Edit the skill file
- Re-dispatch
- Repeat until all 4 fixtures × 5 personas catch their expected gaps

This is the REFACTOR step of RED-GREEN-REFACTOR. Common gaps:
- Rubric eval point too vague → tighten the "what to look for" column
- Persona prompt doesn't specify mode → add "PRD-Review mode: Standalone" instruction
- Story-coverage rule misses a case → add an example to archetypes.md

- [ ] **Step 13.4: Delete the RED-baseline.md temp file**

```bash
rm shield/skills/general/prd-review/test-fixtures/RED-baseline.md
```

- [ ] **Step 13.5: Commit any skill refinements + cleanup**

```bash
git add shield/skills/general/prd-review/ shield/skills/general/story-coverage/ shield/agents/agile-coach-reviewer.md
git commit -m "test(shield): GREEN — reviewer agents catch all fixture-expected gaps; refinements applied"
```

---

## Task 14: End-to-end integration test

**Goal:** Run the actual `/prd-review` command against the dogfooded PRD (`docs/superpowers/specs/2026-05-11-prd-and-research-redesign-prd.md`). This validates orchestration end-to-end: ingest → type detection → 5-persona parallel dispatch → aggregation → output artifacts → apply options.

- [ ] **Step 14.1: Invoke /prd-review against the dogfooded PRD**

```
/prd-review docs/superpowers/specs/2026-05-11-prd-and-research-redesign-prd.md
```

Expected: Shield classifies as local file → snapshots → detects type=standard → confirms with user → dispatches 5 personas in parallel → aggregates → writes 5 output artifacts → offers apply options.

- [ ] **Step 14.2: Inspect the output artifacts**

Check that all 5 expected files exist at the right path:
- `summary.md` — verdict line follows the "Needs Work (composite X.X, blocked by N P0s)" format if P0s exist
- `source-prd.md` — exact byte-for-byte match with the input file
- `enhanced-prd.md` — has inline `<!-- [from: <Persona>] -->` attribution on each P0/P1 fix
- `review-comments.json` — valid JSON, schema_version "1.0", at least 1 comment per persona that found gaps
- `detailed/<persona>.md` × 5 — each persona's detailed report present

- [ ] **Step 14.3: Verify manifest + index.html updated**

```bash
cat docs/shield/manifest.json | jq '.prd_reviews // []'
ls docs/shield/index.html
```

The new prd-review entry should appear in the manifest; index.html should mention it.

- [ ] **Step 14.4: Verify failure paths**

Run two failure-mode invocations:

```
/prd-review https://notion.so/some-fake-page-id   # tests MCP-then-WebFetch-then-paste fallback
/prd-review --paste                                # tests paste-only flow
```

For each, confirm the failure flow handles cleanly (specific error message, paste fallback offered, no partial output).

- [ ] **Step 14.5: Commit the integration test output as a fixture for future regression checks**

Save the integration-test output (the actual review of the dogfooded PRD) to a permanent fixture:

```bash
mkdir -p shield/skills/general/prd-review/test-fixtures/integration/
cp -r docs/shield/<feature-folder>/prd-review/1-<slug>/ shield/skills/general/prd-review/test-fixtures/integration/dogfood-baseline/
git add shield/skills/general/prd-review/test-fixtures/integration/
git commit -m "test(shield): commit integration-test baseline (dogfood review of the PRD itself)"
```

---

## Task 15: Marketplace version bump + final cleanup

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Goal:** Per CLAUDE.md, bump shield version in `.claude-plugin/marketplace.json` ONLY (not in `plugin.json`).

- [ ] **Step 15.1: Bump shield version**

Edit `.claude-plugin/marketplace.json`:

```diff
- "version": "2.11.0",
+ "version": "2.12.0",
```

Only for the `shield` entry. Other entries (infra-review, clickup-sprint-planner, dev-workflow) are unchanged.

- [ ] **Step 15.2: Commit version bump**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.12.0 — Phase A /prd-review"
```

- [ ] **Step 15.3: Sanity check — list all changes since the spec PRs**

```bash
git log --oneline 33dac04..HEAD
```

Expected: 15 commits covering the 15 tasks above. No surprise files outside `shield/` or `.claude-plugin/marketplace.json`.

- [ ] **Step 15.4: Push to remote**

```bash
git push
```

---

## Post-implementation: Optional polish

The following are out of scope but tracked here for awareness:

- Run `/prd-review` against 2-3 real PRDs from prior Shield user feature folders; capture findings for Phase B/C iteration
- Document any rubric drift discovered during real-world testing as candidates for Phase B refinement
- Update `docs/shield/README.md` (if it exists) to mention the new command
- Notify Shield maintainers via the project's communication channel

---

## Spec → plan coverage check

Spec section / requirement | Implemented in task
---|---
Ingest: local file / paste / URL with runtime MCP discovery | Task 6
13-dimension rubric with eval points | Task 5
5-persona dispatch | Task 8 (personas), Task 9 (orchestration)
A-F scoring + P0-gate verdict | Task 7
Output: source-prd.md (immutable snapshot) | Task 6 Step 3, Task 9 Step 7
Output: summary.md, enhanced-prd.md, review-comments.json, detailed/*.md | Task 9 Step 7
Type detection (lean vs standard) | Task 6 Step 4
N/A handling with reasoning | Task 5 (rubric) + Task 8 (personas)
Three dimension states (graded/N/A/informational) | Task 5 + Task 7
P0-gate on verdict | Task 7
Story-coverage skill (AC11/AC12) | Tasks 3, 4, 10
Apply options (use as canonical / convert back / skip) | Task 9 Step 9
Notion MCP auth fallback | Task 6 (paste fallback flow)
PRD-to-Plan linkage (linked_plans, source_prd) | **Not in this plan** — Phase B / `/plan` consumer side
Lean → standard upgrade flow | **Not in this plan** — Phase B
PRD scaffold (17 sections) | **Not in this plan** — Phase B
`/research` Phase 1 enhancement | **Not in this plan** — Phase C

This plan is Phase A only. Phase B and C are tracked in the spec under "Rollout plan" and will get their own plans when scheduled.
