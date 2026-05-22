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
| 2b | Out-of-scope items each have one-line rationale explaining WHY excluded now | Critical |
| 2c | Scope creep risks acknowledged | Warning |

**N/A exception:** For single-purpose internal engineering tools (e.g., a cron job, a backfill script) where the scope is entirely bounded by the problem statement and there is nothing to de-scope, grade dim 2 N/A with reasoning rather than flagging absence of a Non-goals section as a gap.

**Grading note:** A "Non-goals" or "Out of Scope" section that lists items WITHOUT per-item rationale satisfies 2a (section present) but fails 2b (rationale absent). With 2b now Critical, missing rationale escalates to P0.

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
| 9b | In-app messaging / release notes plan | Critical |
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
