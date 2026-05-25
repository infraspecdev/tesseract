# PRD Restructure — Cutover (Plan 2 of 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the scripts from Plan 1 into a consolidated `shield/skills/general/prd/` skill that backs both `/prd` and `/prd-review` with the new product-focused scaffold, and delete the legacy `prd-docs/` + `prd-review/` directories.

**Architecture:** A single `prd/SKILL.md` orchestrator branches on entry path. Both flows converge at `finalize-prd.sh`. New 20-section scaffold in `templates.md` is the source of truth for both authoring (`/prd`) and refining (`/prd-review`). `rubric.md` narrowed for product framing. Three agent prompts updated (DX, architect, finops). Persona weights moved to `persona-weights.yaml` (SSoT). HTML shell in `finalize-prd.sh` extended with TOC, nav header, and sidecar reference. `update-manifest.sh` extended with `index.html` regeneration.

**Tech Stack:** Markdown for skill/template/rubric content; Python via `uv run` for scripts; pytest for unit tests; existing skill conventions for SKILL.md frontmatter and step skeletons.

**Spec source:** `docs/superpowers/specs/2026-05-23-prd-and-prd-review-restructure-design.md` (sections 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 17).

**Plan 1 prerequisite:** `docs/superpowers/plans/2026-05-23-prd-restructure-foundation.md` MUST be merged before this plan starts. Plan 1's 11 scripts + `.claude/skills/script-llm-contract/SKILL.md` + `dim-section-map.yaml` are referenced throughout.

---

## File Structure

**Creates (new):**

```
shield/skills/general/prd/
├── SKILL.md                            consolidated orchestrator (replaces prd-docs/SKILL.md + prd-review/SKILL.md)
├── templates.md                        new 20-section scaffold + lean variant
├── persona-weights.yaml                SSoT for aggregate_review.py (moved out of code)
└── (carried over from legacy)
    ├── rubric.md                       narrowed dims 5 + 13
    ├── dimensions.md                   touched for new § references
    ├── scoring.md                      reads persona-weights.yaml
    ├── prompts/*.md                    light section-name updates
    ├── ingest.md                       carried verbatim
    ├── meta-schema.md                  carried verbatim
    ├── type-detection.md               carried verbatim
    └── dim-section-map.yaml            from Plan 1 — unchanged

shield/evals/prd/
├── prd-context-gathering.eval.md
├── prd-research-opt-in.eval.md
├── prd-low-confidence-walk.eval.md
├── prd-current-context-section.eval.md
├── prd-no-architecture-section.eval.md
├── prd-cost-high-level.eval.md
├── prd-finalize-html-rendered.eval.md
├── prd-temp-cleanup.eval.md
├── prd-terminologies-body-grounded.eval.md
└── prd-terminologies-placeholder-until-last.eval.md

shield/evals/prd-review/
├── prd-review-walk-output-shape.eval.md
├── prd-review-sparse-detection.eval.md
├── prd-review-additional-context-flow.eval.md
├── prd-review-dispatch-aggregation.eval.md
├── prd-review-corrected-cleanup.eval.md
├── prd-review-rubric-narrowing.eval.md
├── prd-review-cost-anti-pattern.eval.md
└── prd-review-legacy-fold.eval.md

.claude/skills/script-llm-contract/evals/
├── script-exit-code-contract.eval.md
├── script-no-prompting.eval.md
└── proactive-script-suggestion.eval.md
```

**Modifies:**
- `shield/commands/prd.md` — rewrite for new entry flow
- `shield/commands/prd-review.md` — rewrite for new entry flow
- `shield/agents/dx-engineer.md` — add `implementation-detail-bleed` anti-pattern
- `shield/agents/architect.md` — narrow dim 5 eval points
- `shield/agents/finops-analyst.md` — narrow dim 13 eval points
- `shield/scripts/prd/aggregate_review.py` — read persona-weights.yaml instead of hardcoded dict
- `shield/scripts/prd/update_manifest.py` + `update-manifest.sh` — regenerate `index.html`
- `shield/scripts/prd/finalize_prd.py` — use full HTML shell (TOC + nav + sidecar-meta)
- `.claude-plugin/marketplace.json` — bump Shield version

**Deletes:**
- `shield/skills/general/prd-docs/` (whole directory)
- `shield/skills/general/prd-review/` (whole directory)
- `shield/evals/prd-docs/` (after fixtures migrated to `shield/evals/prd/`)

---

## Task 1: Carry over unchanging assets into `shield/skills/general/prd/`

Move files that are functionally unchanged (or change only in section-number references) from `prd-docs/` and `prd-review/` into the new `prd/` directory. Old directories stay in place until Task 16's cutover so existing `/prd` and `/prd-review` continue to work during Plan 2 development.

**Files:**
- Copy: `shield/skills/general/prd-docs/meta-schema.md` → `shield/skills/general/prd/meta-schema.md`
- Copy: `shield/skills/general/prd-docs/type-detection.md` → `shield/skills/general/prd/type-detection.md`
- Copy: `shield/skills/general/prd-review/ingest.md` → `shield/skills/general/prd/ingest.md`
- Copy: `shield/skills/general/prd-review/dimensions.md` → `shield/skills/general/prd/dimensions.md`
- Copy: `shield/skills/general/prd-review/scoring.md` → `shield/skills/general/prd/scoring.md`
- Copy: `shield/skills/general/prd-review/prompts/` → `shield/skills/general/prd/prompts/` (entire directory, 9 files)

- [ ] **Step 1: Copy the assets**

```bash
cp shield/skills/general/prd-docs/meta-schema.md     shield/skills/general/prd/meta-schema.md
cp shield/skills/general/prd-docs/type-detection.md  shield/skills/general/prd/type-detection.md
cp shield/skills/general/prd-review/ingest.md        shield/skills/general/prd/ingest.md
cp shield/skills/general/prd-review/dimensions.md    shield/skills/general/prd/dimensions.md
cp shield/skills/general/prd-review/scoring.md       shield/skills/general/prd/scoring.md
cp -r shield/skills/general/prd-review/prompts       shield/skills/general/prd/prompts
ls shield/skills/general/prd/prompts/ | wc -l    # expect: 9
```

- [ ] **Step 2: Verify copies are byte-identical to source**

```bash
diff -r shield/skills/general/prd-review/prompts shield/skills/general/prd/prompts
# Expected: no output (identical).
diff shield/skills/general/prd-docs/meta-schema.md shield/skills/general/prd/meta-schema.md
# Expected: no output.
```

- [ ] **Step 3: Update section-number references in carried files**

Open `shield/skills/general/prd/dimensions.md` and `shield/skills/general/prd/prompts/*.md`. Find any reference to "§5" that means the old standalone Architecture section, and update to point to §3 Current context's "What exists today" subsection. Find any reference to "§10 NFRs" and update to "§9 UX-impacting constraints". Find any reference to "§9 Functional requirements" and update to "§8 Product behavior". Find any reference to "§11 RBAC" and update to "§10". Find any "§12 Dependencies" → "§11". Find any "§13 Risks" → "§12". Find any "§14 Assumptions" → "§13". Find any "§15 Rollout" → "§14". Find any "§16 Cost" → "§15". Find any "§17 GTM" → "§16". Find any "§18 Support" → "§17". Find any "§19 Open questions" → "§18". Find any "§20 Out of scope" → "§19". Add new "§20 Sign-offs".

Use a focused sweep — DO NOT mass-substitute, since some files reference the rubric's dim numbers (dim 5, dim 13) which are unchanged. Only update where the text refers to PRD section numbers.

Run: `grep -nE '§5|§9 Functional|§10 NFR|§11 RBAC|§12 Dep|§13 Risk|§14 Ass|§15 Roll|§16 Cost|§17 GTM|§18 Sup|§19|§20' shield/skills/general/prd/dimensions.md shield/skills/general/prd/prompts/*.md`
Expected output AFTER updates: the only matches should be the new numbering (e.g., `§14 Rollout plan`, `§15 Cost estimate`).

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/prd/
git commit -m "refactor(prd): carry over unchanging assets into consolidated prd/ dir

Copies meta-schema.md + type-detection.md from prd-docs/, and
ingest.md + dimensions.md + scoring.md + prompts/ from prd-review/.
Renumbers § references in dimensions.md and prompts/ for the new
20-section scaffold. Legacy directories remain in place until Task 16."
```

---

## Task 2: Write the new `templates.md` (20-section scaffold + lean variant)

The single source of truth for the new scaffold. Used by `/prd` to generate from scratch and by `/prd-review` to apply corrections.

**Files:**
- Create: `shield/skills/general/prd/templates.md`

- [ ] **Step 1: Write the file header + standard scaffold §1-§5**

Write to `shield/skills/general/prd/templates.md`:

````markdown
# PRD Templates

Two scaffolds: **standard** (20 sections, default) and **lean** (8 sections, for 1-pagers and "stop me if this is wrong" docs).

Both use the same `prd.md` filename. PRD type is recorded in `prd.meta.json` per `meta-schema.md`. Heuristic detection is in `type-detection.md`; `detect-prd-type.sh` (Plan 1) implements the heuristic.

§2 Terminologies is populated LAST in both flows — until then it carries the placeholder block defined in this file. The body-grounding rule (only terms used in §3..§20 appear in §2) is enforced by `count-term-in-body.sh` + `extract-glossary-candidates.sh` from Plan 1.

§5 Architecture (legacy) is GONE. Current-architecture sketches now live inside §3 Current context's "What exists today" subsection — as background only, never as new-system design.

---

## Standard scaffold (20 sections)

```markdown
# {Feature name} — PRD

## 1. Header

- **Owner:** {name}
- **Status:** Draft | In review | Approved | Shipped
- **Last updated:** {YYYY-MM-DD}
- **Sign-off contact:** {name}
- **Linked artifacts:**
  - Research: {feature}/research.md
  - Plan: {feature}/plan.md (when created)
  - Review: {feature}/reviews/prd/{latest}/summary.md (when applicable)

## 2. Terminologies

<!-- Populated last from PRD body content per design spec §5.1.
     Until §3..§20 are accepted, this is a placeholder. Do NOT fill
     manually. -->

| Term | Definition |
|---|---|

## 3. Current context

### What exists today

{What the current system or process looks like. May include a brief
description of current architecture as background, optionally a
Mermaid diagram of the current-state flow. NOT a design — context
only. If there is no current system (greenfield), say so.}

### The problem we're facing

{What's broken / missing / costly about the current state. Include
quantifiable pain where possible: tickets/quarter, hours/week, %
adoption, $ at risk.}

### What we're proposing to change

{One-paragraph summary of the proposed change — at a product level.
"We're moving from X to Y" or "We're adding ability for users to Z."
Do NOT prescribe implementation choices here.}

### Why now

{Urgency or opportunity-cost rationale. Regulatory deadline,
competitive pressure, internal incident, expiring opportunity,
contract SLA. "We should do this" without grounded urgency fails
rubric dim 11.}

## 4. Personas

{Per persona: name + role, what they do today, what they want, their
"jobs to be done". Use research-derived quotes/data where possible.}

## 5. Goals & non-goals

### Goals
- {Outcome-oriented, measurable where possible.}

### Non-goals
- {Things explicitly out of scope to prevent later scope creep.}
```

- [ ] **Step 2: Append §6-§10 + §11-§15 to `templates.md`**

Append the following to `shield/skills/general/prd/templates.md`:

````markdown
## 6. Success metrics

| Metric | Baseline (today) | Target (after launch) | Measurement window |
|---|---|---|---|

Each metric should be measurable from existing telemetry or a small
addition. Avoid vanity metrics; prefer leading + lagging pairs.

## 7. User stories & scenarios

Use the standard story template:

```
### {Story ID} — {Story name}

**Persona:** {from §4}
**Type:** new | enhancement | existing
{If enhancement or existing: name the existing behavior in one line.}

**As a** {persona}, **I want to** {action}, **so that** {outcome}.

**Acceptance criteria**
1. Given {precondition}, when {action}, then {observable outcome}.
2. ...
```

`shield:story-coverage` skill scaffolds expected stories from §4 + §5
before the user fills them.

## 8. Product behavior & user-visible rules

What the product does from the user's POV. Rules that aren't tied to
one specific story (cross-story invariants, negative "shall not"
rules, third-party degradation behavior, data-handling rules visible
to the user).

EXAMPLES of acceptable framing:
- "When a third-party service rate-limits us, the user sees a 'Try
  again in {N}s' banner; the backend is expected to queue requests
  for up to 5 minutes before surfacing a hard error."
- "Once a user submits a refund, no further edits to the order are
  allowed."

NOT acceptable here (those belong in /plan):
- "Use Redis for the queue."
- "p99 latency 50ms."
- "DynamoDB GSI on userId."

## 9. UX-impacting constraints

Constraints the user can feel, see, or be blocked by. Includes
privacy/legal/compliance when those manifest in the UI (consent
prompts, data-residency banners, deletion timelines).

EXAMPLES of acceptable framing:
- Privacy: "Users in the EU see a cookie consent banner before tracking
  loads."
- Error states: "If payment service returns a generic 500, the user
  sees 'Payment is temporarily unavailable; we'll retry your order
  automatically'."
- Accessibility: "All forms reachable by keyboard; screen-reader labels
  on every interactive element."
- Third-party degradation: "If Stripe webhooks are delayed >2min,
  order status shows 'Processing' (not 'Failed')."

NOT acceptable (move to /plan):
- "p99 latency 50ms."
- "Use Redis."
- "RDS multi-AZ in us-east-1."

## 10. RBAC & permissions matrix

| Persona | Can do (product capability) | Cannot do |
|---|---|---|

Capability-level, not enforcement-mechanism level. "Admin can revoke
sessions" is product. "Admin uses /api/admin/sessions/revoke endpoint"
is implementation — out.

## 11. External dependencies (UX-impacting only)

External systems the user feels the dependency on.

| Dependency | UX impact if absent / degraded | Mitigation user sees |
|---|---|---|
| Stripe | Payments fail | "Payments temporarily unavailable" banner |
| Sentry | (none — internal) | DO NOT include — not UX-impacting |

Drop internal-only services (caches, queues, internal microservices)
unless their outage is user-visible.

## 12. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|

## 13. Assumptions

What this PRD takes as given. Each assumption is a future risk if it
proves wrong.

## 14. Rollout plan

### Milestones

| ID | Outcome | Exit criteria | Depends on |
|---|---|---|---|
| M1 | {short outcome} | {observable exit signal} | — |

`shield:milestone-coverage` skill scaffolds milestones from §4 + §5 + §7.

### Rollout mechanics
- {Phased / cohort / dark-launch / feature-flag plan.}
- {Kill-switch criteria.}
- {Migration steps for existing users.}

## 15. Cost estimate

**Lump estimates only.** No per-resource breakdowns. The PRD reviewer
auto-fails entries like "Aurora us-east-1 multi-AZ $X" or "NAT gateway
$Y" — those belong in `/plan`, not here.

| Category | Estimate (monthly, post-launch) | Notes |
|---|---|---|
| Infrastructure | ~${X}/mo (with HA) | one-line rationale |
| Vendor / APIs | ~${Y}/mo | which vendors |
| Internal effort | ~{N} engineer-weeks (one-time) | for delivery |
```

- [ ] **Step 3: Append §16-§20 + lean scaffold to `templates.md`**

Append the following to `shield/skills/general/prd/templates.md`:

````markdown
## 16. GTM & customer-comms

- **Customer-facing messaging:** {announcement, in-app notice, email}
- **Internal comms:** {sales enablement, support enablement, eng-wide announce}
- **Timing:** {pre-launch, launch day, post-launch}

## 17. Support / CX impact

- **Expected ticket volume:** {qualitative or quantitative estimate}
- **Macros / playbooks:** {what changes for the support team}
- **Escalation paths:** {who owns what when something breaks}

## 18. Open questions

Things this PRD doesn't yet answer. Each open question has an owner
and a target resolution date.

## 19. Out of scope

Explicit list of things this PRD is NOT addressing. Future-proofs
against scope creep.

## 20. Sign-offs

| Approver | Role | Status | Date |
|---|---|---|---|
| {name} | Product | | |
| {name} | Engineering | | |
| {name} | Design | | |
| {name} | Legal / Privacy | | |

---

## Lean scaffold (8 sections)

```markdown
# {Feature name} — Lean PRD

## 1. Header

- **Owner:** {name}
- **Status:** Draft | Approved
- **Last updated:** {YYYY-MM-DD}
- **Sign-offs:** {name} (Product), {name} (Eng)

## 2. Terminologies

<!-- Populated last from PRD body. Placeholder until §3..§8 are accepted. -->

| Term | Definition |
|---|---|

## 3. Current context

### What exists today
{...}

### The problem we're facing
{...}

### What we're proposing to change
{...}

### Why now
{...}

## 4. Personas

{Short — one persona, two at most.}

## 5. Goals & non-goals

### Goals
- {...}

### Non-goals
- {...}

## 6. Success metrics

| Metric | Baseline | Target | Window |
|---|---|---|---|

## 7. User stories

{Short — 1-3 stories with AC.}

## 8. Milestones

| ID | Outcome | Exit criteria |
|---|---|---|

## 9. Open questions

## 10. Out of scope
```

The lean variant folds Sign-offs into §1 Header (no standalone §20).
Lean is intentionally 10-numbered (its own count) — not the same numbers
as the standard scaffold.

---

## HTML shell template (consumed by `finalize-prd.sh`)

`finalize-prd.sh --entry prd|prd-review` injects this shell around the
rendered markdown body. Placeholders `{{TOC}}` and `{{BODY}}` are
substituted by `shield/scripts/render-markdown.sh`. `{{NAV_PATH}}` is
substituted by `finalize_prd.py` before render.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PRD — {{FEATURE_NAME}}</title>
  <meta name="sidecar" content="prd.meta.json">
  <style>
    body { font-family: system-ui; max-width: 980px; margin: 0 auto; padding: 0 1rem; line-height: 1.5; }
    nav.shield-nav { background:#f8f9fa;padding:8px 16px;border-bottom:1px solid #dee2e6;font-family:system-ui;font-size:14px;margin: 0 -1rem 1.5rem; }
    nav.shield-nav a { text-decoration:none; }
    .meta-banner { background:#fff8e7;padding:10px 14px;border-radius:6px;margin-bottom:1rem;font-size:14px; }
    code { background:#f4f4f4;padding:.1rem .3rem;border-radius:3px; }
    pre { background:#f4f4f4;padding:.7rem;border-radius:6px;overflow-x:auto; }
    table { border-collapse:collapse;width:100%; }
    th,td { border:1px solid #ddd;padding:.4rem .6rem;text-align:left; }
    .toc { background:#f4f6f8;padding:1rem;border-radius:6px;margin-bottom:1.5rem; }
    .toc ul { margin: 0; padding-left: 1.2rem; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true,theme:'neutral'});</script>
</head>
<body>
<nav class="shield-nav">
  <a href="{{NAV_PATH}}index.html">← All Features</a> |
  <strong>{{FEATURE_NAME}}</strong> |
  <a href="../prd.md">PRD source</a> ·
  <a href="../prd.meta.json">Meta</a>
</nav>
<div class="meta-banner">
  <strong>PRD</strong> — Owner: {{OWNER}} · Status: {{STATUS}} · Last updated: {{LAST_UPDATED}}
</div>
{{TOC}}
{{BODY}}
</body>
</html>
```

Variable substitution rules (done by `finalize_prd.py` BEFORE the
render-markdown call):

| Placeholder | Source | Notes |
|---|---|---|
| `{{FEATURE_NAME}}` | `feature_dir.name` | from --feature-dir arg |
| `{{NAV_PATH}}` | `../../` | feature/outputs/ → docs/shield/ |
| `{{OWNER}}` | `prd.meta.json` `.owner` | fall back to `(unset)` |
| `{{STATUS}}` | `prd.meta.json` `.status` | fall back to `Draft` |
| `{{LAST_UPDATED}}` | `prd.meta.json` `.last_updated` | filled by finalize itself |

`{{TOC}}` and `{{BODY}}` are processed by `render-markdown.sh` — leave
them as-is in the shell.
````

- [ ] **Step 4: Sanity-check the file**

Run: `wc -l shield/skills/general/prd/templates.md && grep -c "^## " shield/skills/general/prd/templates.md`
Expected: file has 300+ lines; ~10 `## ` headings (TOC entries within the spec markdown).

Run: `grep -n "## 5\\. Architecture" shield/skills/general/prd/templates.md`
Expected: NO MATCH. The legacy §5 Architecture section is gone.

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/prd/templates.md
git commit -m "feat(prd): new 20-section scaffold + lean variant + HTML shell

§3 Current context replaces standalone §3 Problem; legacy §5
Architecture is gone (current-arch context goes into §3 'What exists
today'). §8 Product behavior, §9 UX-impacting constraints, §11
External deps, §15 Cost are reframed product-first. §2 Terminologies
has a placeholder block — filled last by the §5.1 body-grounding
protocol. Lean variant carries 10 sections."
```

---

<!-- PLAN2-CHUNK-1-END -->

## Task 3: Narrow `rubric.md` for dim 5 (UX-only NFRs) and dim 13 (lump cost)

**Files:**
- Create: `shield/skills/general/prd/rubric.md` (start from a copy of the legacy `prd-review/rubric.md`, then apply narrowings)

- [ ] **Step 1: Copy legacy rubric as starting point**

```bash
cp shield/skills/general/prd-review/rubric.md shield/skills/general/prd/rubric.md
```

- [ ] **Step 2: Rewrite the dim 5 section**

Open `shield/skills/general/prd/rubric.md`. Find the section for dim 5 (NFR coverage) and replace its evaluation-points table with this:

```markdown
### Dim 5 — UX-impacting constraints

Narrowed from the legacy "NFR coverage". Asks only about constraints
the user feels. Implementation-level NFRs (p99 targets, scale numbers,
infra SKU choices) move to `/plan-review` dim list.

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 5a | Privacy / data-handling visible to user | Critical | PRD names what data is stored, who can see it, and the user-facing controls (deletion, export, consent). Generic "we comply with GDPR" without UX detail fails. |
| 5b | Error & degradation user-facing behavior | Critical | PRD names what the user sees when an external dep degrades or fails (banner, retry copy, fallback path). "Backend handles errors gracefully" without UX detail fails. |
| 5c | Accessibility | Important | PRD names accessibility commitments visible in UI (keyboard nav, screen reader, contrast). Generic "WCAG compliant" without specifics fails. |
| 5d | Third-party-failure UX | Important | PRD names per-external-dep failure UX (e.g., "if Stripe webhooks delayed >2min, status shows 'Processing'"). Reuses Dependencies table from §11. |

**Excluded (now /plan-review territory):** p99 latency targets, scale
numbers, RDS/DynamoDB choices, monitoring tools, internal-cache
strategy, capacity planning. If the PRD describes any of these in
§9, flag as `implementation-detail-bleed` via the DX engineer
dispatch (Task 4).
```

- [ ] **Step 3: Rewrite the dim 13 section**

Find the section for dim 13 (Cost & resource impact) and replace its evaluation-points table with:

```markdown
### Dim 13 — Cost estimate (lump only)

Narrowed to lump estimates. Auto-fail entries that name a specific
resource SKU (e.g., "Aurora us-east-1 multi-AZ $X", "NAT gateway $Y",
"EC2 m5.xlarge × N").

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| 13a | Infrastructure cost estimated as a lump (no per-resource SKU) | Important | One line per high-level category — "Infrastructure ~${X}/mo (with HA)". Auto-fail on phrases like "Aurora", "NAT gateway", "EC2 mN.xlarge", "EBS gp3", or any region-specific SKU. |
| 13b | Vendor / API cost estimated | Important | Names the vendor(s) and a rough monthly figure. |
| 13c | Internal effort estimated | Warning | Rough engineer-weeks for delivery (one-time). |

**Verdict logic:** if 13a evidence contains a per-resource SKU, set
13a grade to F (Critical-severity equivalent) and record the
offending line as `evidence_quote`.
```

- [ ] **Step 4: Update the rubric's section-number references**

Find any references in the rubric to legacy section names and update:
- "§9 Functional requirements" → "§8 Product behavior & user-visible rules"
- "§10 NFRs" → "§9 UX-impacting constraints"
- "§11 RBAC matrix" → "§10 RBAC & permissions matrix"
- "§12 Dependencies" → "§11 External dependencies (UX-impacting only)"
- "§15 Rollout plan" → "§14 Rollout plan"
- "§16 Cost" → "§15 Cost estimate"
- "§17 GTM" → "§16 GTM & customer-comms"
- "§18 Support" → "§17 Support / CX impact"

- [ ] **Step 5: Sanity-check + commit**

Run: `grep -nE "Aurora|NAT gateway|p99" shield/skills/general/prd/rubric.md`
Expected: matches only appear inside the dim 5 "Excluded" line and dim 13 "Auto-fail" line — not as real evaluation points.

```bash
git add shield/skills/general/prd/rubric.md
git commit -m "feat(prd): narrow rubric for dim 5 (UX-only) and dim 13 (lump cost)

Dim 5 replaces legacy NFR coverage with privacy/error/accessibility/
third-party-UX eval points. Implementation-level NFRs (p99, scale,
SKUs) relocated to /plan-review.
Dim 13 narrows to lump-estimate cost; auto-fails per-resource SKU
mentions (Aurora, NAT gateway, EC2 SKUs)."
```

---

## Task 4: Update DX engineer agent — add `implementation-detail-bleed` anti-pattern

**Files:**
- Modify: `shield/agents/dx-engineer.md`

- [ ] **Step 1: Read the current DX agent**

```bash
cat shield/agents/dx-engineer.md | head -80
```

Locate the section that enumerates anti-patterns (today's named patterns: `pm-jargon-bleed`, `unstated-tradeoffs`, etc. — exact names vary).

- [ ] **Step 2: Append the new anti-pattern entry**

Add the following entry to the anti-patterns list in `shield/agents/dx-engineer.md`:

```markdown
### implementation-detail-bleed

Flag any section that describes HOW the feature is built (library
choice / SKU / p99 target / internal service name / queue technology)
instead of WHAT the user experiences.

**Exception:** §3 Current context's "What exists today" subsection MAY
describe current architecture as background. This is the only place
implementation detail is acceptable in a PRD.

**Detection:**
- Mentions of specific cloud SKUs (Aurora, RDS, DynamoDB, EC2 instance
  types, EBS volume types, NAT gateway, ALB, etc.) outside §3.
- p99 / p95 / p99.9 latency numbers outside §3 or the §9 UX-impacting
  constraints framing ("user sees X within Yms" is OK; "p99=50ms"
  alone is not).
- Internal service names (e.g., "queue-service", "auth-internal")
  outside §3.
- Library choice mentions outside §3 ("we'll use Redis", "Stripe SDK
  v8").

**Severity:** Warning (not Critical — these are bleeds, not gating
failures, but they accumulate and signal scope drift toward design).

**Output shape (per anti-pattern entry in the persona envelope):**

```json
{
  "name": "implementation-detail-bleed",
  "evidence_line": 142,
  "evidence_quote": "We'll use Redis for the session cache.",
  "section": "§8 Product behavior"
}
```
```

- [ ] **Step 3: Verify the agent file still parses**

```bash
head -1 shield/agents/dx-engineer.md       # YAML frontmatter intact
grep -c "^### " shield/agents/dx-engineer.md   # Heading count incremented by 1
```

- [ ] **Step 4: Commit**

```bash
git add shield/agents/dx-engineer.md
git commit -m "feat(agents): DX engineer flags implementation-detail-bleed

New anti-pattern in PRD reviews. Flags Aurora/RDS/p99/Redis-style
mentions outside §3 Current context's 'What exists today'. Severity
Warning."
```

---

## Task 5: Update architect + finops-analyst agent prompts for narrowed dims

**Files:**
- Modify: `shield/agents/architect.md`
- Modify: `shield/agents/finops-analyst.md`

- [ ] **Step 1: Update architect agent — narrow dim 5 framing**

Open `shield/agents/architect.md`. Find the section that briefs the agent on dim 5 (NFR coverage). Replace the dim 5 prompt content with:

```markdown
**Dim 5 — UX-impacting constraints (narrowed from legacy NFR coverage):**

Grade four checks. Each is graded against the rubric in `prd/rubric.md` (Dim 5).

| ID | Check |
|---|---|
| 5a | Privacy / data-handling visible to user |
| 5b | Error & degradation user-facing behavior |
| 5c | Accessibility |
| 5d | Third-party-failure UX |

DO NOT grade implementation-level NFRs (p99, capacity, scale, SKU
choices). If the PRD includes them, do not penalize dim 5 for their
presence — the DX engineer's `implementation-detail-bleed`
anti-pattern handles that.

If the PRD has §3 Current context and that section describes p99 /
SKUs / internal services as background, treat that as in-scope
context — do NOT grade it under dim 5.
```

- [ ] **Step 2: Update architect dim 6 framing (light touch — section names)**

Find any references in architect.md to "§15 Rollout plan" and confirm they read "§14 Rollout plan" after this PR. Similarly "§5 Architecture" → "§3 Current context" (background-only).

- [ ] **Step 3: Update finops-analyst — narrow dim 13 framing**

Open `shield/agents/finops-analyst.md`. Find the dim 13 (Cost) prompt content and replace with:

```markdown
**Dim 13 — Cost estimate (lump only):**

Grade three checks. Each is graded against the rubric in `prd/rubric.md` (Dim 13).

| ID | Check |
|---|---|
| 13a | Infrastructure cost estimated as a lump (no per-resource SKU) |
| 13b | Vendor / API cost estimated |
| 13c | Internal effort estimated |

**Auto-fail rule for 13a:** if §15 Cost estimate contains any phrase
matching this list, set 13a grade to F regardless of other content:

- "Aurora" (any RDS engine)
- "RDS" (without lump framing)
- "DynamoDB"
- "EC2 m{N}." / "EC2 c{N}." / "EC2 r{N}." (instance type SKUs)
- "EBS gp3" / "EBS io2" (volume SKUs)
- "NAT gateway"
- "ALB" / "NLB" (load balancer SKUs)
- "us-east-1" / any region in the cost figure
- Per-resource dollar amounts ($N for X resource)

These belong in `/plan`, not the PRD. Record the offending line as
`evidence_quote`. Output the grade with an explicit gap explaining
the rule.
```

- [ ] **Step 4: Sanity-check both agents**

```bash
grep -n "p99\|capacity targets\|scale numbers" shield/agents/architect.md
# Expected: matches only in the "DO NOT grade" carve-out.

grep -n "Aurora\|NAT gateway\|RDS multi-AZ" shield/agents/finops-analyst.md
# Expected: matches only in the auto-fail list.
```

- [ ] **Step 5: Commit**

```bash
git add shield/agents/architect.md shield/agents/finops-analyst.md
git commit -m "feat(agents): narrow dim 5 (architect) + dim 13 (finops-analyst)

Architect agent: dim 5 narrowed to UX-impacting NFRs only. DX
anti-pattern handles implementation-bleed; architect doesn't double-
penalize.
Finops-analyst: dim 13 auto-fails per-resource SKU mentions
(Aurora, NAT gateway, EC2 instance types, region-specific costs).
Lump-estimate framing only."
```

---


## Task 6: Add `persona-weights.yaml` + refactor `aggregate_review.py` to consume it

Plan 1 self-review flagged the hardcoded `DIM_PERSONA` + `PERSONA_WEIGHTS` dicts in `aggregate_review.py` as a SSoT violation against `dimensions.md`. Fix by moving the table into a YAML config that both the script and the dimensions doc reference.

**Files:**
- Create: `shield/skills/general/prd/persona-weights.yaml`
- Modify: `shield/scripts/prd/aggregate_review.py`
- Modify: `shield/scripts/prd/test_aggregate_review.py` (add a test for YAML loading)

- [ ] **Step 1: Write the YAML**

Write to `shield/skills/general/prd/persona-weights.yaml`:

```yaml
# shield/skills/general/prd/persona-weights.yaml
#
# Single source of truth for the dim→persona mapping AND persona-weight
# table used by aggregate-review.sh. Mirrored (commented) in
# dimensions.md for human reference.
#
# Grade ↔ numeric: A=4, B=3, C=2, D=1, F=0.
# Per-persona grade = arithmetic mean of dim grades for that persona.
# Composite = weighted mean of persona grades.

dim_to_persona:
  1:  product-manager
  2:  product-manager
  3:  product-manager
  4:  agile-coach
  5:  tech-lead
  6:  tech-lead
  7:  product-manager
  8:  product-manager
  9:  product-manager
  10: product-manager
  11: product-manager
  12: product-manager
  13: finops-analyst

persona_weights:
  product-manager: 1.0
  agile-coach:     1.0
  tech-lead:       1.0
  dx-engineer:     0.7    # anti-patterns only, no dim
  finops-analyst:  0.7
```

- [ ] **Step 2: Add failing test for YAML loading**

Append the following to `shield/scripts/prd/test_aggregate_review.py`:

```python
def test_loads_persona_weights_from_yaml(tmp_path: Path) -> None:
    """If --persona-weights is provided, the script reads from it (not hardcoded)."""
    # Custom YAML with non-default weights — verify they're respected.
    custom = tmp_path / "weights.yaml"
    custom.write_text("""\
dim_to_persona:
  1:  product-manager
  2:  product-manager
  3:  product-manager
  4:  agile-coach
  5:  tech-lead
  6:  tech-lead
  7:  product-manager
  8:  product-manager
  9:  product-manager
  10: product-manager
  11: product-manager
  12: product-manager
  13: finops-analyst
persona_weights:
  product-manager: 2.0    # doubled
  agile-coach:     1.0
  tech-lead:       1.0
  dx-engineer:     0.5
  finops-analyst:  0.5
""")
    d = _write_dispatch_dir(tmp_path, {
        "dim-1.json": _per_dim(1, "Problem clarity", "F"),  # F=0
        "dim-2.json": _per_dim(2, "Scope", "A"),
        "dim-3.json": _per_dim(3, "Measurable success", "A"),
        "dim-7.json": _per_dim(7, "RACI", "A"),
        "dim-8.json": _per_dim(8, "Legal", "A"),
        "dim-9.json": _per_dim(9, "GTM", "A"),
        "dim-10.json": _per_dim(10, "Support", "A"),
        "dim-11.json": _per_dim(11, "Why now", "A"),
        "dim-12.json": _per_dim(12, "Risks", "A"),
        "agile-coach.json": _per_persona("agile-coach", "A", [_per_dim(4, "AC", "A")]),
        "architect.json": _per_persona("tech-lead", "A", [_per_dim(5, "NFR", "A"), _per_dim(6, "Rollout", "A")]),
        "dx-engineer.json": _per_persona("dx-engineer", "A", [], anti_patterns=[]),
        "finops-analyst.json": _per_persona("finops-analyst", "A", [_per_dim(13, "Cost", "A")]),
    })
    out_dir = tmp_path / "out"; out_dir.mkdir()
    code, payload = _run("--dispatch-dir", str(d), "--out-dir", str(out_dir),
                         "--persona-weights", str(custom))
    assert code == 0
    # PM is doubled weight, so the F=0 in dim 1 (PM persona) pulls composite
    # harder than it would with default weights. With doubled PM weight,
    # composite should be measurably lower than default.
    assert payload["data"]["composite"] < 3.0


def test_default_persona_weights_resolved_from_skill_dir() -> None:
    """When --persona-weights omitted, script falls back to default location."""
    # Default lives at shield/skills/general/prd/persona-weights.yaml.
    default_yaml = SCRIPT_DIR.parent.parent / "skills" / "general" / "prd" / "persona-weights.yaml"
    # This test asserts the file exists; the script must find it on its own.
    assert default_yaml.exists(), f"missing default config: {default_yaml}"
```

- [ ] **Step 3: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_aggregate_review.py::test_loads_persona_weights_from_yaml -v`
Expected: FAIL — the script ignores `--persona-weights` today.

- [ ] **Step 4: Refactor `aggregate_review.py` to load YAML**

In `shield/scripts/prd/aggregate_review.py`:

(a) Delete the hardcoded `DIM_PERSONA` and `PERSONA_WEIGHTS` dicts near the top of the file.

(b) Add this loader and the new arg right after the EXIT/GRADE constants:

```python
import yaml

DEFAULT_WEIGHTS_PATH = SCRIPT_DIR.parent.parent / "skills" / "general" / "prd" / "persona-weights.yaml"


def _load_weights(path: Path | None) -> tuple[dict[int, str], dict[str, float]]:
    p = path or DEFAULT_WEIGHTS_PATH
    if not p.exists():
        raise FileNotFoundError(f"persona-weights config not found at {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return data["dim_to_persona"], data["persona_weights"]
```

(c) Update `main()` to accept `--persona-weights` (optional) and pass the loaded dicts down:

```python
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatch-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--persona-weights", default=None,
                        help="path to persona-weights.yaml (default: shield/skills/general/prd/persona-weights.yaml)")
    args = parser.parse_args(argv)

    # ... existing dispatch-dir/out-dir validation ...

    try:
        dim_persona, persona_weights = _load_weights(Path(args.persona_weights) if args.persona_weights else None)
    except FileNotFoundError as e:
        emit_error(code=EXIT_INVALID_INPUT, category="invalid_input", reason=str(e))
        return

    # ... pass dim_persona + persona_weights into _persona_grades and _composite ...
```

(d) Update `_persona_grades(dim_blocks)` to take `dim_persona` as an arg:

```python
def _persona_grades(dim_blocks: list[dict], dim_persona: dict[int, str]) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for d in dim_blocks:
        persona = dim_persona.get(d["id"])
        if persona is None:
            continue
        buckets.setdefault(persona, []).append(GRADE_VALUES.get(d.get("grade", "F"), 0.0))
    return {p: sum(vs) / len(vs) for p, vs in buckets.items() if vs}
```

(e) Update `_composite(persona_grades)` to take `persona_weights` as an arg:

```python
def _composite(persona_grades: dict[str, float], persona_weights: dict[str, float]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for persona, grade in persona_grades.items():
        w = persona_weights.get(persona, 1.0)
        weighted_sum += grade * w
        total_weight += w
    return (weighted_sum / total_weight) if total_weight > 0 else 0.0
```

(f) Update the call sites in `main()` accordingly.

- [ ] **Step 5: Run all aggregate tests, verify pass**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_aggregate_review.py -v`
Expected: 7 passed (5 original + 2 new).

- [ ] **Step 6: Update `aggregate-review.sh` to keep the --with pyyaml flag**

Open `shield/scripts/prd/aggregate-review.sh`. Confirm the `exec uv run` line includes `--with pyyaml`. If not, add it:

```bash
exec uv run --quiet --with pyyaml -- python "$SCRIPT_DIR/aggregate_review.py" "$@"
```

- [ ] **Step 7: Commit**

```bash
git add shield/skills/general/prd/persona-weights.yaml
git add shield/scripts/prd/aggregate_review.py shield/scripts/prd/aggregate-review.sh
git add shield/scripts/prd/test_aggregate_review.py
git commit -m "refactor(scripts/prd): move persona weights to persona-weights.yaml SSoT

Aggregate-review now reads dim_to_persona + persona_weights from
shield/skills/general/prd/persona-weights.yaml. Removes hardcoded
dicts that duplicated dimensions.md. Supports --persona-weights
override for tests + future tuning."
```

---

## Task 7: Extend `update-manifest.sh` to regenerate `index.html`

Per spec §8(f), `update-manifest.sh` should rebuild BOTH `manifest.json` AND `index.html`. Plan 1 deferred the HTML step. Implement it now.

**Files:**
- Modify: `shield/scripts/prd/update_manifest.py` (add index.html generation)
- Modify: `shield/scripts/prd/test_update_manifest.py` (add tests for index)
- Modify: `shield/scripts/prd/update-manifest.sh` (no code change — same wrapper)

- [ ] **Step 1: Add failing test for index.html generation**

Append to `shield/scripts/prd/test_update_manifest.py`:

```python
def test_index_html_generated(tmp_path: Path) -> None:
    root = tmp_path / "docs" / "shield"
    _make_feature(root, "alpha-20260520", with_prd=True, with_research=True)
    _make_feature(root, "beta-20260521", with_prd=True)
    code, payload = _run("--output-dir", str(root))
    assert code == 0
    assert payload["data"]["index_html_regenerated"] is True
    index_path = root / "index.html"
    assert index_path.exists()
    html = index_path.read_text()
    # Both features appear.
    assert "alpha-20260520" in html
    assert "beta-20260521" in html
    # Feature links to its prd.md.
    assert "alpha-20260520/prd.md" in html or "alpha-20260520/outputs/prd.html" in html
    # Self-contained: no external CSS or JS references (per manifest-schema.md).
    assert "https://" not in html or "cdn.jsdelivr.net/npm/mermaid" in html  # mermaid CDN allowed for HTML rendering parity
    # Embedded manifest reference.
    assert "fetch('manifest.json')" in html or 'fetch("manifest.json")' in html


def test_index_html_features_sorted_by_date_descending(tmp_path: Path) -> None:
    root = tmp_path / "docs" / "shield"
    _make_feature(root, "alpha-20260520", with_prd=True)
    _make_feature(root, "older-20260101", with_prd=True)
    _make_feature(root, "newer-20260601", with_prd=True)
    _run("--output-dir", str(root))
    html = (root / "index.html").read_text()
    # newer-20260601 must appear before older-20260101 in the rendered HTML.
    idx_newer = html.index("newer-20260601")
    idx_alpha = html.index("alpha-20260520")
    idx_older = html.index("older-20260101")
    assert idx_newer < idx_alpha < idx_older
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_update_manifest.py -v`
Expected: 2 new tests FAIL — index.html not written and/or feature sort wrong.

- [ ] **Step 3: Add the index.html generator to `update_manifest.py`**

In `shield/scripts/prd/update_manifest.py`:

(a) Add a function that builds the HTML from a manifest dict:

```python
import html as html_escape
import re

DATE_TAIL_RE = re.compile(r"-(\d{8})$")


def _feature_date(name: str) -> str:
    """Extract YYYYMMDD tail; fall back to empty string for sorting (oldest)."""
    m = DATE_TAIL_RE.search(name)
    return m.group(1) if m else ""


def _format_feature_card(feature: dict) -> str:
    name = feature["name"]
    artifacts = feature.get("artifacts", {})
    reviews = feature.get("reviews", {})
    updated = feature.get("updated", "")

    parts: list[str] = []
    parts.append(f'<article class="feature-card">')
    parts.append(f'  <h2>{html_escape.escape(name)}</h2>')
    parts.append(f'  <p class="updated">Updated: {html_escape.escape(updated)}</p>')

    # Artifact links.
    parts.append('  <ul class="artifacts">')
    if artifacts.get("research"):
        parts.append(f'    <li><a href="{name}/research.md">Research</a></li>')
    if artifacts.get("prd"):
        parts.append(f'    <li><a href="{name}/prd.md">PRD (md)</a> · <a href="{name}/outputs/prd.html">PRD (html)</a></li>')
    if artifacts.get("plan_md"):
        parts.append(f'    <li><a href="{name}/plan.md">Plan</a> · <a href="{name}/outputs/plan.html">Plan (html)</a></li>')
    if artifacts.get("plan_arch_md"):
        parts.append(f'    <li><a href="{name}/plan-architecture.md">Architecture</a></li>')
    parts.append('  </ul>')

    # Review counts.
    rev_lines: list[str] = []
    for rtype in ("prd", "plan", "code"):
        info = reviews.get(rtype, {})
        count = info.get("count", 0)
        if count == 0:
            continue
        latest = info.get("latest", "")
        href = f"{name}/reviews/{rtype}/{latest}/summary.md"
        rev_lines.append(f'    <li>{rtype.upper()} reviews: {count} · <a href="{href}">latest ({latest})</a></li>')
    if rev_lines:
        parts.append('  <ul class="reviews">')
        parts.extend(rev_lines)
        parts.append('  </ul>')

    parts.append('</article>')
    return "\n".join(parts)


def _build_index_html(manifest: dict) -> str:
    features = sorted(
        manifest.get("features", []),
        key=lambda f: _feature_date(f["name"]),
        reverse=True,
    )
    cards = "\n".join(_format_feature_card(f) for f in features)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Shield — Features</title>
<style>
body {{ font-family: system-ui; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
h1 {{ border-bottom: 1px solid #ddd; padding-bottom: .4rem; }}
.feature-card {{ background: #fff; padding: 1rem 1.2rem; margin: 1rem 0; border: 1px solid #e2e6ea; border-radius: 8px; }}
.feature-card h2 {{ margin: 0 0 .4rem; font-size: 1.2rem; }}
.updated {{ color: #666; font-size: .85rem; margin: 0 0 .8rem; }}
ul.artifacts, ul.reviews {{ margin: .4rem 0; padding-left: 1.2rem; }}
a {{ text-decoration: none; }}
</style>
</head><body>
<h1>Shield — Features</h1>
<p><small>Self-contained. Re-rendered on every manifest update by update-manifest.sh.</small></p>
{cards}
<script>
// Runtime manifest reference for client-side enhancement (no behavior change here).
fetch('manifest.json').then(r => r.json()).then(manifest => {{ window.__shieldManifest = manifest; }});
</script>
</body></html>
"""
```

(b) In `main()`, after writing the manifest, generate and write the index:

```python
    manifest = build_manifest(output_dir)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    index_html = _build_index_html(manifest)
    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")

    emit_success({
        "manifest_path": str(manifest_path.resolve()),
        "index_html_path": str(index_path.resolve()),
        "feature_count": len(manifest["features"]),
        "index_html_regenerated": True,
    })
```

(c) Add `import html as html_escape` + `import re` to the top imports.

- [ ] **Step 4: Run all update_manifest tests, verify pass**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_update_manifest.py -v`
Expected: all tests pass (originals plus the 2 new index tests).

- [ ] **Step 5: Smoke test the index visually**

```bash
mkdir -p /tmp/smoke-idx/docs/shield/alpha-20260520
echo "# x" > /tmp/smoke-idx/docs/shield/alpha-20260520/prd.md
shield/scripts/prd/update-manifest.sh --output-dir /tmp/smoke-idx/docs/shield
cat /tmp/smoke-idx/docs/shield/index.html | head -30
# Open in browser to eyeball: open /tmp/smoke-idx/docs/shield/index.html (macOS)
```

- [ ] **Step 6: Commit**

```bash
git add shield/scripts/prd/update_manifest.py shield/scripts/prd/test_update_manifest.py
git commit -m "feat(scripts/prd): update-manifest now regenerates index.html

Implements spec §8(f). Per-feature cards sorted by YYYYMMDD tail
(newest first). Self-contained HTML — embedded manifest.json
reference via script tag. Closes the deferred item from Plan 1's
self-review."
```

---

## Task 8: Extend `finalize-prd.sh` with full HTML shell (TOC + nav + sidecar-meta)

Plan 1 used a minimal `{{BODY}}`-only shell. Replace it with the full shell defined in `templates.md`'s HTML-shell section, with placeholder substitution for `{{FEATURE_NAME}}`, `{{NAV_PATH}}`, `{{OWNER}}`, `{{STATUS}}`, `{{LAST_UPDATED}}`.

**Files:**
- Modify: `shield/scripts/prd/finalize_prd.py`
- Modify: `shield/scripts/prd/test_finalize_prd.py` (add tests for new shell features)

- [ ] **Step 1: Add failing tests for the new shell**

Append to `shield/scripts/prd/test_finalize_prd.py`:

```python
def test_html_has_nav_header(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    draft = feat_dir / ".prd-draft.md"
    draft.write_text("# Alpha PRD\n\n## 1. Header\n\n## 2. Terminologies\n\n## 3. Current context\n")
    code, _ = _run("--entry", "prd", "--feature-dir", str(feat_dir),
                   "--draft", str(draft), "--output-dir", str(output_dir))
    assert code == 0
    html = (feat_dir / "outputs" / "prd.html").read_text()
    # Nav links back to ../../index.html (feature/outputs/ → docs/shield/).
    assert "../../index.html" in html
    # Sidecar meta tag points to prd.meta.json.
    assert '<meta name="sidecar"' in html
    assert "prd.meta.json" in html
    # Feature name appears in the nav.
    assert "alpha-20260523" in html


def test_html_has_toc(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    draft = feat_dir / ".prd-draft.md"
    draft.write_text("""# Alpha PRD

## 1. Header

## 2. Terminologies

## 3. Current context

## 4. Personas
""")
    code, _ = _run("--entry", "prd", "--feature-dir", str(feat_dir),
                   "--draft", str(draft), "--output-dir", str(output_dir))
    assert code == 0
    html = (feat_dir / "outputs" / "prd.html").read_text()
    # TOC entries reference each §-heading by name.
    assert "Current context" in html
    assert "Personas" in html


def test_html_meta_banner_uses_meta_json(tmp_path: Path) -> None:
    output_dir = _setup_output_tree(tmp_path)
    feat_dir = output_dir / "alpha-20260523"
    # Pre-existing meta.json with a known owner.
    (feat_dir / "prd.meta.json").write_text('{"owner":"alice","status":"In review","type":"standard"}')
    draft = feat_dir / ".prd-draft.md"
    draft.write_text("# alpha\n")
    code, _ = _run("--entry", "prd", "--feature-dir", str(feat_dir),
                   "--draft", str(draft), "--output-dir", str(output_dir))
    assert code == 0
    html = (feat_dir / "outputs" / "prd.html").read_text()
    # Banner reflects the owner + status from meta.json.
    assert "alice" in html
    assert "In review" in html
```

- [ ] **Step 2: Run new tests, verify fail**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_finalize_prd.py::test_html_has_nav_header test_finalize_prd.py::test_html_has_toc test_finalize_prd.py::test_html_meta_banner_uses_meta_json -v`
Expected: FAIL — minimal shell lacks nav, TOC, sidecar-meta.

- [ ] **Step 3: Replace the minimal shell with the full shell in `finalize_prd.py`**

In `shield/scripts/prd/finalize_prd.py`:

(a) Replace the `MIN_SHELL_HTML` constant with `FULL_SHELL_HTML`:

```python
FULL_SHELL_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PRD — {{FEATURE_NAME}}</title>
  <meta name="sidecar" content="../prd.meta.json">
  <style>
    body { font-family: system-ui; max-width: 980px; margin: 0 auto; padding: 0 1rem; line-height: 1.5; }
    nav.shield-nav { background:#f8f9fa;padding:8px 16px;border-bottom:1px solid #dee2e6;font-family:system-ui;font-size:14px;margin: 0 -1rem 1.5rem; }
    nav.shield-nav a { text-decoration:none; }
    .meta-banner { background:#fff8e7;padding:10px 14px;border-radius:6px;margin-bottom:1rem;font-size:14px; }
    code { background:#f4f4f4;padding:.1rem .3rem;border-radius:3px; }
    pre { background:#f4f4f4;padding:.7rem;border-radius:6px;overflow-x:auto; }
    table { border-collapse:collapse;width:100%; }
    th,td { border:1px solid #ddd;padding:.4rem .6rem;text-align:left; }
    .toc { background:#f4f6f8;padding:1rem;border-radius:6px;margin-bottom:1.5rem; }
    .toc ul { margin: 0; padding-left: 1.2rem; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true,theme:'neutral'});</script>
</head>
<body>
<nav class="shield-nav">
  <a href="{{NAV_PATH}}index.html">← All Features</a> |
  <strong>{{FEATURE_NAME}}</strong> |
  <a href="../prd.md">PRD source</a> ·
  <a href="../prd.meta.json">Meta</a>
</nav>
<div class="meta-banner">
  <strong>PRD</strong> — Owner: {{OWNER}} · Status: {{STATUS}} · Last updated: {{LAST_UPDATED}}
</div>
{{TOC}}
{{BODY}}
</body></html>
"""
```

(b) Add a placeholder-substitution helper:

```python
def _substitute_shell_placeholders(shell: str, *, feature_name: str, owner: str, status: str, last_updated: str) -> str:
    return (
        shell
        .replace("{{FEATURE_NAME}}", feature_name)
        .replace("{{NAV_PATH}}", "../../")
        .replace("{{OWNER}}", owner or "(unset)")
        .replace("{{STATUS}}", status or "Draft")
        .replace("{{LAST_UPDATED}}", last_updated)
    )
```

(c) Update `_render_html(feature_dir)` to read `prd.meta.json` and substitute placeholders BEFORE calling render-markdown.sh:

```python
def _render_html(feature_dir: Path) -> Path:
    outputs = feature_dir / "outputs"
    outputs.mkdir(exist_ok=True)

    # Read meta for shell substitutions.
    meta_path = feature_dir / "prd.meta.json"
    meta: dict = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {}
    feature_name = feature_dir.name
    owner = meta.get("owner", "")
    status = meta.get("status", "")
    last_updated = meta.get("last_updated", "")

    shell_substituted = _substitute_shell_placeholders(
        FULL_SHELL_HTML,
        feature_name=feature_name,
        owner=owner,
        status=status,
        last_updated=last_updated,
    )

    shell = feature_dir / ".prd.shell.html"
    shell.write_text(shell_substituted, encoding="utf-8")
    renderer = SCRIPT_DIR.parent / "render-markdown.sh"
    try:
        subprocess.run(
            [str(renderer),
             "--md", "prd.md",
             "--shell", ".prd.shell.html",
             "--out", "outputs/prd.html"],
            cwd=str(feature_dir),
            check=True,
            capture_output=True,
        )
    finally:
        if shell.exists():
            shell.unlink()
    return outputs / "prd.html"
```

(d) **Ordering note:** `_render_html` reads `prd.meta.json` for the meta banner, but `_write_meta` updates `last_updated` after the render. To ensure the rendered HTML reflects the *new* `last_updated`, reorder `main()` so `_write_meta` runs BEFORE `_render_html`:

```python
    # Step 2: copy draft → prd.md
    canonical = feature_dir / "prd.md"
    canonical.write_text(draft.read_text(encoding="utf-8"), encoding="utf-8")

    # Step 3: meta (BEFORE render so shell substitutions see the new last_updated).
    meta_path = _write_meta(
        feature_dir,
        source_command=args.entry,
        review_link=review_dir if args.entry == "prd-review" else None,
    )

    # Step 4: render HTML (reads meta from disk).
    html_path = _render_html(feature_dir)

    # Step 5: delete temp draft + sidecars (unchanged).
    # Step 6: rebuild manifest (unchanged).
```

- [ ] **Step 4: Run all finalize-prd tests, verify pass**

Run: `cd shield/scripts/prd && uv run --with pyyaml --with pytest pytest test_finalize_prd.py -v`
Expected: all tests pass (5 original + 3 new).

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/prd/finalize_prd.py shield/scripts/prd/test_finalize_prd.py
git commit -m "feat(scripts/prd): finalize-prd uses full HTML shell (TOC, nav, sidecar-meta)

Replaces the minimal Plan-1 shell with the full template defined in
prd/templates.md: nav header linking to all-features + prd source +
meta sidecar, mermaid CDN for diagrams, meta banner with owner/status/
last_updated. Reorders main() to write meta BEFORE rendering so the
shell substitution sees the new last_updated value."
```

---


## Task 9: Write the consolidated `shield/skills/general/prd/SKILL.md`

The single orchestrator backing both `/prd` and `/prd-review`. Long file (~400 lines). Built in 4 steps so each step's content is reviewable independently.

**Files:**
- Create: `shield/skills/general/prd/SKILL.md`

- [ ] **Step 1: Write the frontmatter + paths + when-to-use sections**

Write to `shield/skills/general/prd/SKILL.md`:

````markdown
---
name: prd
description: Use when authoring a new PRD or refining an existing one. /prd authors from scratch via context-ingest + optional /research + one-shot generation + low-confidence walk + manual review + finalize. /prd-review starts from an existing PRD via ingest + 13-dim reviewer dispatch + optional additional context + one-shot corrected PRD + manual review + finalize. Both produce the same output shape: {feature}/prd.md + {feature}/outputs/prd.html + {feature}/prd.meta.json. Triggers on /prd, /prd-review, "author a PRD", "review my PRD".
---

# PRD (consolidated)

Author a new PRD or refine an existing one. Two entry paths share one orchestrator and one finalize step. The output shape is identical regardless of entry.

## Output Paths — MANDATORY

```
{output_dir}/{feature}/
├── prd.md            ← registry: {prd}      = {feature_dir}/prd.md
├── outputs/prd.html  ← registry: {prd_html} = {feature_outputs}/prd.html
├── prd.meta.json     ← side-artifact metadata sidecar
└── reviews/prd/{date}{_counter}/   ← side-artifact (only when entry=prd-review)
    ├── source-prd.md
    ├── summary.md
    ├── review-comments.json
    └── detailed/<persona>.md × 5
```

`{output_dir}` from `.shield.json` (default `docs/shield`). `{feature}` is the feature folder (`{kebab-name}-YYYYMMDD`).

`{date}{_counter}` for the review folder is resolved by `next-review-dir.sh` (Plan 1) — same-day collisions use `_2`, `_3`, etc.

## When to Use

- User invokes `/prd` to author a new PRD.
- User invokes `/prd-review` to refine an existing PRD (local file / URL / paste).
- User invokes `/prd` in a feature folder containing a legacy 20-section PRD — triggers the legacy-fold flow (treated as `/prd-review` against the existing PRD).

## When NOT to Use

- **Generate a plan** from a PRD — use `/plan`.
- **Review a plan** — use `/plan-review`.
- **Capture pre-PRD context** — use `/research`. `/prd` will offer to invoke `/research` for you.

## Two-entry-path overview

```
                                ┌─ /prd       → context ingest → optional /research → one-shot draft
                                │              → low-confidence walk → §2 fill → manual review
                                │              → finalize
{user invokes} ───────────────  ┤
                                │
                                └─ /prd-review → ingest source → dispatch 13 reviewers
                                                → optional additional context → one-shot corrected PRD
                                                → §2 fill → manual review → finalize

                                                      ↓ finalize (shared)
                                                {feature}/prd.md
                                                {feature}/outputs/prd.html
                                                {feature}/prd.meta.json
```

The shared finalize step is `finalize-prd.sh` (Plan 1). It enforces the invariant that `prd.md` and `prd.html` are written together — neither without the other.

## Configuration

Read `.shield.json` for:
- `output_dir` (default `docs/shield`)
- `prd_template` (default null — use built-in scaffold from `templates.md`)
- `prd_required_sections` (default: ["Current context", "Goals & non-goals", "Success metrics", "Out of scope", "Open questions"])
- `prd_review_personas` (default all 5 — used by `/prd-review` dispatch)
- `prd_ingest_resolvers` (default `[]`)

## Script invocation reminder (from `.claude/skills/script-llm-contract/`)

Every script in `shield/scripts/prd/` emits JSON on stdout and signals categories via exit code 0/1/2/3/4/5. On any non-zero exit, read the payload's `suggested_action` and `fallback` keys before deciding the next move. Never retry a code-2 (invalid input) call with the same arguments.
````

- [ ] **Step 2: Append the `/prd` step skeleton + workflow**

Append the following to `shield/skills/general/prd/SKILL.md`:

````markdown
---

## `/prd` — Step Skeleton (author from scratch)

| Step | Action | Script (Plan 1) | Mandatory |
|---|---|---|---|
| 1 | Determine feature folder context (`--feature` flag, cwd hint, or new with today's date) | — | Yes |
| 2 | Ask user where context comes from (multi-select: Notion / Jira / Confluence / Linear / file / paste / "none") | — | Yes |
| 3 | For each source, ingest via `prd-ingest.sh`; react per contract | `prd-ingest.sh` | Yes (per source) |
| 4 | Ask user whether to run `/research` now | — | Yes |
| 5 | If yes → invoke `/research`; if no → skip | — | Conditional |
| 6 | One-shot generate full draft prd.md + confidence sidecar | LLM | Yes |
| 7 | Identify low-confidence §s | `filter-low-confidence.sh` | Yes |
| 8 | walkSection(§N) for each low-confidence § (accept / edit / skip) | LLM | Conditional |
| 9 | Build §2 Terminologies via the body-grounding protocol (always last) | `extract-glossary-candidates.sh` + `count-term-in-body.sh` | Yes |
| 10 | Present full draft; user manually reviews | — | Yes |
| 11 | On confirm → `finalize-prd.sh --entry prd`; on reject → leave temp, exit | `finalize-prd.sh` | Yes |

## `/prd` — Workflow

### Step 1. Feature folder context

- If `--feature <name>` passed → use that.
- Else look at recent feature activity and ask user to confirm: "Continue with `{feature}` or create a new feature folder?"
- If new → `{kebab-name}-{YYYYMMDD}` using today's date.

### Step 2-3. Context ingest

Prompt:

```
Where's your context coming from? (multi-select)
  [ ] Notion page or database
  [ ] Jira issue or epic
  [ ] Confluence page
  [ ] Linear issue
  [ ] Local file
  [ ] Paste content
  [ ] None — I'll provide it inline
```

For each selected source, invoke `prd-ingest.sh` with the user-supplied path / URL:

```
prd-ingest.sh --source <path|url>
```

**On exit 0:** capture `data.content` and `data.source_type`.

**On exit 4 (`needs_human`)** with `resource=notion_mcp`: use the Notion MCP `notion-fetch` tool to retrieve the page, then re-invoke as:

```
echo "<fetched-content>" | prd-ingest.sh --paste-from-stdin
```

**On exit 4** with `resource=atlassian_mcp`: same pattern but via Atlassian MCP.

**On exit 4** with `resource=webfetch`: use the WebFetch tool, then re-invoke with `--paste-from-stdin`.

**On exit 2 (`invalid_input`)**: re-examine inputs; never auto-retry the same call.

### Step 4-5. Research opt-in

After ingest:

```
Want to run /research now too? (Recommended if context is light or the
problem is new.)
  ( ) Yes — invoke /research, then continue
  ( ) No — proceed with ingested context only
```

If yes → invoke the `shield:research` skill. Research transcript writes to `{output_dir}/{feature}/.session-transcript.md`.

### Step 6. One-shot draft generation

Construct the LLM prompt:
- Inputs: ingested content + research transcript (if any) + the new 20-section scaffold from `templates.md` (or 8-section lean if user selected lean) + `dim-section-map.yaml` for section context.
- **§2 Terminologies MUST be left as the placeholder block from `templates.md` — do NOT fill in this pass.**
- Generation MUST emit:
  - `{output_dir}/{feature}/.prd-draft.md` — the full draft
  - `{output_dir}/{feature}/.prd-draft.confidence.json` — `{"sections":[{"id":N,"confidence":"high|medium|low"},...]}` for §3..§20 (§2 is N/A and omitted)

### Step 7-8. Low-confidence walk

```
filter-low-confidence.sh --sidecar {feature}/.prd-draft.confidence.json
```

On exit 0, the payload's `data.section_ids` is the list of §s to walk. For each:

```
walkSection(§N):
  - Show current draft content for §N.
  - Ask: "Accept / edit / skip?"
  - On accept → continue.
  - On edit → user provides new content; substitute into the draft.
  - On skip → continue with current content.
```

Update `.prd-draft.md` in place with any edits.

### Step 9. §2 Terminologies — body-grounding protocol

Per spec §5.1, populated last from PRD body content. See "§2 Terminologies protocol" section below for the full algorithm. Substitute the resulting table into the §2 placeholder block in `.prd-draft.md`.

### Step 10-11. Manual review + finalize

Show the user the full `.prd-draft.md`. Ask:

```
Manually review the draft. Confirm to finalize into {feature}/prd.md?
  ( ) Confirm  — finalize-prd.sh runs; temp deleted; prd.html rendered.
  ( ) Reject   — keep .prd-draft.md; exit (you can re-run /prd to resume).
```

On confirm:

```
finalize-prd.sh \
  --entry prd \
  --feature-dir {output_dir}/{feature} \
  --draft {output_dir}/{feature}/.prd-draft.md \
  --output-dir {output_dir}
```

`finalize-prd.sh` (Plan 1) copies draft → `prd.md`, renders `outputs/prd.html`, updates `prd.meta.json`, deletes `.prd-draft.md` + `.prd-draft.confidence.json`, rebuilds manifest + `index.html`.

On reject: nothing is finalized. The draft and sidecar remain in place.
````

- [ ] **Step 3: Append the `/prd-review` step skeleton + workflow**

Append the following to `shield/skills/general/prd/SKILL.md`:

````markdown
---

## `/prd-review` — Step Skeleton (refine existing PRD)

| Step | Action | Script (Plan 1) | Mandatory |
|---|---|---|---|
| 1 | Classify + ingest source PRD (local / URL / paste) → snapshot to `source-prd.md` | `prd-ingest.sh` + `next-review-dir.sh` | Yes |
| 2 | Detect PRD type (lean / standard); confirm with user | `detect-prd-type.sh` | Yes |
| 3 | **PHASE A** — dispatch 13 reviewer invocations in parallel | LLM Agents | Yes |
| 4 | Aggregate reviewer outputs → `review-comments.json`, `summary.md`, `detailed/<persona>.md` | `aggregate-review.sh` | Yes |
| 5 | Identify sparse §s (Critical D/F findings) | `sparse-sections.sh` | Yes |
| 6 | If sparse, ask user whether to gather more context; if yes, re-ingest + optional /research | `prd-ingest.sh` | Conditional |
| 7 | **PHASE B** — one-shot generate corrected PRD using source + gaps + additional context | `map-gaps-to-sections.sh` + LLM | Yes |
| 8 | Build §2 Terminologies via the body-grounding protocol against the corrected PRD | `extract-glossary-candidates.sh` + `count-term-in-body.sh` | Yes |
| 9 | Present corrected PRD; user manually reviews | — | Yes |
| 10 | On accept → `finalize-prd.sh --entry prd-review`; on reject → leave corrected-prd.md in review folder | `finalize-prd.sh` | Yes |

## `/prd-review` — Workflow

### Step 1. Ingest + snapshot

```
next-review-dir.sh --reviews-root {output_dir}/{feature}/reviews/prd --date {today}
```

→ payload's `data.absolute_path` is `{review_dir}`. Create the directory.

Ingest the source:

```
prd-ingest.sh --source <path|url>
```

Same error handling as `/prd` step 3. On success, write the content to `{review_dir}/source-prd.md` — this snapshot is **immutable** for the rest of the run.

### Step 2. PRD type detection

```
detect-prd-type.sh {review_dir}/source-prd.md
```

Payload returns `type: lean | standard | ambiguous` and `section_count`. Confirm with the user:

```
Detected: {type} ({section_count} sections). Correct?
  [y] yes
  [n] no — pick manually: lean | standard
```

### Step 3. PHASE A — Reviewer dispatch (parallel)

Dispatch 13 reviewer invocations in a **single response** (parallel). See `dimensions.md` for the registry.

- 9 PM dimensions via `general-purpose` Agents loaded with prompts from `prompts/`:
  - `prompts/problem-clarity.md` (dim 1)
  - `prompts/scope-discipline.md` (dim 2)
  - `prompts/measurable-success.md` (dim 3)
  - `prompts/raci-and-approvals.md` (dim 7)
  - `prompts/legal-privacy-compliance.md` (dim 8)
  - `prompts/gtm-customer-comms.md` (dim 9)
  - `prompts/support-cx-impact.md` (dim 10)
  - `prompts/why-now-cost-of-inaction.md` (dim 11)
  - `prompts/risks-and-assumptions.md` (dim 12)

- 4 legacy persona dispatches:
  - `shield:agile-coach` (dim 4)
  - `shield:architect` (dims 5 + 6 — one dispatch returns both)
  - `shield:dx-engineer` (anti-patterns — includes the new `implementation-detail-bleed` per Task 4 of Plan 2)
  - `shield:finops-analyst` (dim 13, narrowed to lump cost per Task 5 of Plan 2)

Each agent returns JSON to a unique file under `{review_dir}/_dispatch/`:

```
{review_dir}/_dispatch/dim-1.json
{review_dir}/_dispatch/dim-2.json
...
{review_dir}/_dispatch/agile-coach.json
{review_dir}/_dispatch/architect.json
{review_dir}/_dispatch/dx-engineer.json
{review_dir}/_dispatch/finops-analyst.json
```

### Step 4. Aggregate

```
aggregate-review.sh --dispatch-dir {review_dir}/_dispatch --out-dir {review_dir}
```

Writes:
- `{review_dir}/review-comments.json` (canonical structured per-dim gaps)
- `{review_dir}/summary.md` (scored gap analysis + verdict)
- `{review_dir}/detailed/<persona>.md` × 5 (per-reviewer reports — Phase A subagents declare these; aggregator copies into `detailed/`)

On exit 5 (`partial`): some dim JSON files were malformed or missing. Read `partial.missing_dims` and ask user: "Dim N reviewer returned malformed output. Re-dispatch?" Decision goes back through Phase A.

### Step 5-6. Sparse-section detection + optional context gather

```
sparse-sections.sh --review {review_dir}/review-comments.json --dim-map shield/skills/general/prd/dim-section-map.yaml
```

If `data.section_ids` is non-empty, ask the user:

```
Sections {X, Y, Z} look sparse based on the review (Critical findings
graded D or F). Want to gather more context before applying corrections?
  ( ) Yes — Notion / Jira / Confluence / etc.
  ( ) No  — proceed with current source PRD
```

If yes → repeat the `/prd` step 2-3 ingest flow (same `prd-ingest.sh` invocations). Then offer `/research` (same as `/prd` step 4-5).

### Step 7. PHASE B — Corrected PRD generation

```
map-gaps-to-sections.sh --review {review_dir}/review-comments.json --dim-map shield/skills/general/prd/dim-section-map.yaml
```

→ payload's `data.gaps_by_section` is a `{§-id: [gap entries]}` map.

Construct the LLM prompt:
- Inputs:
  - `{review_dir}/source-prd.md` (the original)
  - `data.gaps_by_section` from `map-gaps-to-sections.sh` (per-section guidance)
  - Additional ingested context from step 6 (if any)
  - `templates.md` scaffold (new 20-section structure)
- **§2 Terminologies MUST be left as the placeholder block** — do NOT fill in this pass.
- **Legacy fold rule:** if the source PRD has a standalone §5 Architecture (legacy 20-section), fold its content into §3 Current context's "What exists today" subsection. Do NOT keep §5 in the output.

Output: `{review_dir}/corrected-prd.md`.

### Step 8. §2 Terminologies protocol on the corrected PRD

Same protocol as `/prd` step 9, but run against `{review_dir}/corrected-prd.md`. Substitute the resulting table into §2's placeholder block.

### Step 9-10. Manual review + finalize

Present `{review_dir}/corrected-prd.md` to the user. Ask:

```
Manually review the corrected PRD. Confirm to finalize into {feature}/prd.md?
  ( ) Confirm  — corrected-prd.md becomes {feature}/prd.md; prd.html re-rendered.
  ( ) Reject   — corrected-prd.md stays in {review_dir}/; canonical untouched.
```

On confirm:

```
finalize-prd.sh \
  --entry prd-review \
  --feature-dir {output_dir}/{feature} \
  --draft {review_dir}/corrected-prd.md \
  --review-dir {review_dir} \
  --output-dir {output_dir}
```

`finalize-prd.sh` (Plan 1) copies corrected-prd.md → `{feature}/prd.md`, renders `outputs/prd.html`, updates `prd.meta.json` (with `review_link` pointing at `{review_dir}`), deletes `{review_dir}/corrected-prd.md`. The other side-artifacts (`source-prd.md`, `summary.md`, `detailed/`, `review-comments.json`) remain in `{review_dir}` as audit trail.
````

- [ ] **Step 4: Append the §2 Terminologies protocol + Common Mistakes + See Also**

Append the following to `shield/skills/general/prd/SKILL.md`:

````markdown
---

## §2 Terminologies protocol (shared — runs last in both entry paths)

§2 is populated AFTER §3..§20 are accepted. Until then the placeholder block from `templates.md` remains in place. **A §2 entry whose term doesn't appear in the PRD body is the error** — the opposite of the legacy "ALL Source A rows MUST appear" rule.

```
Step 9 (/prd) or Step 8 (/prd-review):

1. Extract candidates:
   (a) Source A — research transcript glossary (if present):
       extract-glossary-candidates.sh {output_dir}/{feature}/.session-transcript.md
       → payload's data.candidates is [{term, definition, source: "research"}, ...]
   (b) Source B — LLM body scan of §3..§20:
       Propose 5-15 candidates that meet ANY of:
         - ALL-CAPS acronyms used 2+ times (e.g., "SLA", "RBAC")
         - Capitalized multi-word phrases used as named concepts
         - Domain nouns in §4 Personas / §9 UX-impacting constraints / §11
           Dependencies without prior definition
         - Internal product / service names in §11 / §14 / §16

2. Filter by body-occurrence:
   For each candidate from Source A + Source B:
     count-term-in-body.sh --term "<term>" --prd {draft-path}
   Drop candidates with count=0 — INCLUDING Source A candidates.

3. Deduplicate by lowercased term. On conflict, Source A's definition
   wins (research is authoritative for terms it defines).

4. Present the filtered list to the user. Offer accept-all / edit /
   add / remove. Default: accept all.

5. Substitute the final table into §2, replacing the placeholder block.
```

**Rationale:** if a research-glossary term is genuinely important, the body should reference it (the user can add the reference during the walk / review). If the term isn't referenced, it doesn't belong in §2.

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Filling §2 Terminologies during the one-shot generation pass | §2 is LAST. Use the placeholder block from templates.md; fill via the body-grounding protocol after §3..§20 are accepted. |
| Copying all research-glossary terms verbatim into §2 (legacy rule) | New rule: drop any term that has 0 occurrences in §3..§20 — including research terms. Body-grounding wins. |
| Writing prd.md without re-rendering prd.html | `finalize-prd.sh` is the only sanctioned way to write prd.md — it always re-renders. Never `cp` directly. |
| Walking every section in `/prd` instead of only low-confidence ones | `/prd` walks LOW-CONFIDENCE only (per `filter-low-confidence.sh`). The rest pass through the one-shot draft to manual review. |
| Dispatching reviewers sequentially in `/prd-review` Phase A | Dispatch all 13 in a SINGLE response (parallel). Aggregating after waits. |
| Overwriting source-prd.md after Phase A | Source snapshot is immutable. Only corrected-prd.md gets generated. |
| Keeping enhanced-prd.md / corrected-prd.md after finalize | Temp file is deleted on finalize. Side-artifacts (summary.md, detailed/, source-prd.md, review-comments.json) stay. |
| Including standalone §5 Architecture in a corrected PRD when the source has it | Fold §5 content into §3 Current context's "What exists today" subsection. The new scaffold has no standalone §5. |
| Including per-resource cost SKUs in §15 (e.g., "Aurora us-east-1") | §15 is lump only. The finops-analyst reviewer auto-fails these per Plan 2 Task 5. Move to /plan. |
| Implementation details in §8 / §9 (Redis / p99 / etc.) | DX engineer flags as `implementation-detail-bleed`. Exception: §3 Current context's "What exists today" may describe current architecture as background. |
| Skipping `update-manifest.sh` / index.html regeneration | `finalize-prd.sh` calls it automatically. If you wrote prd.md directly (don't), call `update-manifest.sh --output-dir {output_dir}` to recover. |

## See Also

- `templates.md` — 20-section scaffold + lean variant + HTML shell
- `rubric.md` — 13 dimensions narrowed for product framing
- `dimensions.md` — dispatch registry (which agent grades which dim)
- `dim-section-map.yaml` — dim → § map for sparse detection + gap routing
- `persona-weights.yaml` — SSoT for composite scoring
- `prompts/*.md` — 9 skill-internal PM dim prompts
- `scoring.md` — A-F → composite + P0-gate logic
- `ingest.md` — input classification + resolver chain (consumed by prd-ingest.sh)
- `meta-schema.md` — prd.meta.json schema
- `type-detection.md` — lean vs standard heuristics
- `.claude/skills/script-llm-contract/SKILL.md` — exit-code contract every script in shield/scripts/prd/ follows
````

- [ ] **Step 5: Sanity-check + commit**

```bash
wc -l shield/skills/general/prd/SKILL.md
# Expected: 350-500 lines

grep -c "^## " shield/skills/general/prd/SKILL.md
# Expected: 10-15 top-level headings

# Verify no stale references to dropped concepts.
grep -nE "§5 Architecture|enhanced-prd\.md|legacy_" shield/skills/general/prd/SKILL.md
# Expected: matches only inside "Common Mistakes" or "Legacy fold rule" contexts.

git add shield/skills/general/prd/SKILL.md
git commit -m "feat(prd): consolidated SKILL.md orchestrator for both entry paths

Replaces prd-docs/SKILL.md + prd-review/SKILL.md with a single skill
that backs both /prd (one-shot draft + low-confidence walk) and
/prd-review (dispatch + corrected PRD). Both flows converge at
finalize-prd.sh. Documents the script invocations, exit-code branches,
§2 body-grounding protocol, legacy-fold rule, and full Common Mistakes
table for the new product-focused framing."
```

---


## Task 10: Rewrite `shield/commands/prd.md`

Update the user-facing command to document the new entry flow.

**Files:**
- Modify: `shield/commands/prd.md`

- [ ] **Step 1: Replace `shield/commands/prd.md` with the new content**

Write to `shield/commands/prd.md`:

````markdown
---
name: prd
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Author a new PRD via context-ingest → optional /research → one-shot draft → low-confidence walk → §2 body-grounded fill → manual review → finalize. New 20-section product-focused scaffold; legacy §5 Architecture is gone. Outputs prd.md + prd.html + prd.meta.json.
outputs: [prd, prd_html]
---

# /prd

Author a PRD interactively. Backed by the consolidated `shield:prd` skill, which orchestrates context ingest, optional `/research`, one-shot draft generation, low-confidence walk, §2 Terminologies fill, manual review, and finalize.

## Usage

```
/prd                              # interactive — prompts for feature + context source(s)
/prd <topic>                      # uses topic as seed for feature name
/prd --feature <name>             # explicit feature folder
```

## Paths

| Registry key | Resolved path |
|---|---|
| `prd` | `{output_dir}/{feature}/prd.md` |
| `prd_html` | `{output_dir}/{feature}/outputs/prd.html` |

`prd.meta.json` is a metadata sidecar written to `{output_dir}/{feature}/prd.meta.json` — not a primary deliverable.

## What it does

1. Reads `.shield.json` for `output_dir`, `prd_template`, `prd_required_sections`.
2. Resolves feature folder context.
3. **Asks the user where context comes from** (multi-select: Notion / Jira / Confluence / Linear / file / paste / "none").
4. For each source, invokes `prd-ingest.sh` and reacts per the script-LLM contract (`.claude/skills/script-llm-contract/`). URLs that need MCP fetching are surfaced as exit-4 prompts.
5. **Asks the user whether to run `/research`** now (recommended for thin context). If yes → invokes the `shield:research` skill.
6. **One-shot generates** a full `.prd-draft.md` + `.prd-draft.confidence.json` from ingested context + research transcript + `templates.md` scaffold. §2 Terminologies is left as the placeholder block.
7. Runs `filter-low-confidence.sh` to identify §s tagged `low`.
8. Walks each low-confidence § with the user (accept / edit / skip).
9. Builds §2 Terminologies via the body-grounding protocol (Source A research-glossary candidates + Source B body-scan candidates, filtered by `count-term-in-body.sh`).
10. Presents the full draft for manual review.
11. On confirm → invokes `finalize-prd.sh --entry prd`. On reject → leaves `.prd-draft.md` in place for resumption.

## Output

```
{output_dir}/{feature}/
├── prd.md            ← canonical
├── outputs/prd.html  ← rendered
└── prd.meta.json     ← metadata sidecar
```

## Reference

Full behavior in `shield/skills/general/prd/SKILL.md`.

## See also

- `/prd-review` — refine an existing PRD (same output shape; different entry path)
- `/plan` — generate a technical plan from this PRD
- `/research` — capture product+tech context before authoring (offered automatically during /prd)
````

- [ ] **Step 2: Sanity-check + commit**

```bash
head -10 shield/commands/prd.md   # frontmatter intact
grep -c "^## " shield/commands/prd.md   # ~5-7 headings

git add shield/commands/prd.md
git commit -m "feat(commands): rewrite /prd for new context-ingest entry flow

/prd now asks where context comes from (Notion / Jira / Confluence /
Linear / file / paste), optionally runs /research, one-shot generates
a draft, walks only low-confidence sections, builds §2 last via the
body-grounding protocol, and finalizes via finalize-prd.sh. Output
shape matches /prd-review."
```

---

## Task 11: Rewrite `shield/commands/prd-review.md`

**Files:**
- Modify: `shield/commands/prd-review.md`

- [ ] **Step 1: Replace `shield/commands/prd-review.md` with the new content**

Write to `shield/commands/prd-review.md`:

````markdown
---
name: prd-review
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Refine an existing PRD. Ingests source (file/URL/paste), dispatches 13 reviewers in parallel, optionally gathers more context for sparse sections, one-shot generates a corrected PRD, then finalizes into the canonical {feature}/prd.md. Same output shape as /prd; review artifacts kept as audit trail.
outputs:
  - prd
  - prd_html
  - review_summary
  - review_summary_html
---

# /prd-review

Refine an existing PRD. Backed by the consolidated `shield:prd` skill (same as `/prd`); selects the prd-review entry path.

## Usage

```
/prd-review                              # prompts for a source
/prd-review <path>                       # local file path
/prd-review <url>                        # any URL (Notion, Confluence, Google Docs, public web)
/prd-review --paste                      # read pasted content from prompt
/prd-review --feature <name> <source>    # explicit feature folder
```

## Paths

Canonical outputs (same as `/prd`):

| Registry key | Resolved path |
|---|---|
| `prd` | `{output_dir}/{feature}/prd.md` |
| `prd_html` | `{output_dir}/{feature}/outputs/prd.html` |

Review side-artifacts at `{output_dir}/{feature}/reviews/prd/{date}{_counter}/`:

| Registry key | Resolved path |
|---|---|
| `review_summary` | `{review_dir}/summary.md` |
| `review_summary_html` | `{output_dir}/{feature}/outputs/reviews/prd/{date}{_counter}/summary.html` |

Side-artifacts NOT in the registry (audit trail):
- `source-prd.md` — verbatim source snapshot (immutable after step 1)
- `review-comments.json` — canonical machine-readable gap export
- `detailed/<persona>.md` × 5 — per-reviewer reports

The temp `corrected-prd.md` is deleted by `finalize-prd.sh` on accept.

## What it does

1. Classifies the input (local file / URL / paste) and invokes `prd-ingest.sh` (uses Notion / Atlassian MCP via exit-4 routing when needed).
2. Snapshots the source to `{review_dir}/source-prd.md` (immutable). `{review_dir}` is resolved by `next-review-dir.sh`.
3. Detects PRD type (lean / standard) via `detect-prd-type.sh`; confirms with user.
4. **PHASE A — Dispatch.** 13 reviewer invocations in parallel: 9 PM-dim prompts via `general-purpose` Agents (problem-clarity, scope-discipline, measurable-success, raci-and-approvals, legal-privacy-compliance, gtm-customer-comms, support-cx-impact, why-now-cost-of-inaction, risks-and-assumptions) + 4 legacy persona dispatches (`shield:agile-coach`, `shield:architect` for dims 5+6 with narrowed UX-only NFR rubric, `shield:dx-engineer` for anti-patterns including the new `implementation-detail-bleed`, `shield:finops-analyst` for dim 13 with lump-only auto-fail).
5. Aggregates dispatch outputs via `aggregate-review.sh` → `summary.md`, `review-comments.json`, `detailed/<persona>.md`.
6. Runs `sparse-sections.sh` to identify §s with Critical D/F findings. **Asks the user** whether to gather more context (same Notion / Jira / etc. prompt as `/prd`); optionally invokes `/research`.
7. **PHASE B — Corrected PRD.** One-shot generates `corrected-prd.md` using source + reviewer gaps (routed per-section via `map-gaps-to-sections.sh`) + any additional context. Legacy §5 Architecture folds into §3 Current context's "What exists today" automatically.
8. Builds §2 Terminologies via the body-grounding protocol against `corrected-prd.md`.
9. **Presents corrected PRD for manual review.** On accept → `finalize-prd.sh --entry prd-review` copies to canonical, renders HTML, updates meta with `review_link`, deletes the temp. On reject → keeps `corrected-prd.md` in `{review_dir}`.

## Output

```
{output_dir}/{feature}/
├── prd.md            ← canonical (overwritten on accept)
├── outputs/prd.html  ← rendered (re-rendered on accept)
├── prd.meta.json     ← updated (review_link points at {review_dir})
└── reviews/prd/{date}{_counter}/
    ├── source-prd.md
    ├── summary.md
    ├── review-comments.json
    └── detailed/<persona>.md × 5
```

## Reference

Full behavior in `shield/skills/general/prd/SKILL.md`.

## See also

- `/prd` — author a new PRD (same output shape; different entry path)
- `/plan` — generate a technical plan from a PRD
- `/plan-review` — review a generated plan
- `/research` — gather product + tech context (offered automatically during /prd-review when sparse sections are detected)
````

- [ ] **Step 2: Sanity-check + commit**

```bash
head -10 shield/commands/prd-review.md   # frontmatter intact
grep -nE "enhanced-prd|legacy_review" shield/commands/prd-review.md
# Expected: NO matches — the new flow uses corrected-prd.md (temp, deleted on accept).

git add shield/commands/prd-review.md
git commit -m "feat(commands): rewrite /prd-review for ingest + dispatch + corrected-PRD flow

/prd-review now ingests source, dispatches 13 reviewers in parallel,
optionally gathers more context for sparse sections, one-shot generates
a corrected PRD, and finalizes into the canonical {feature}/prd.md
on user accept. Output shape matches /prd. enhanced-prd.md is gone;
corrected-prd.md is a temp file deleted on accept."
```

---


## Task 12: Add `shield/evals/prd/` evals (10 evals)

Eval suite for the `/prd` entry path. Each eval is a markdown file with YAML frontmatter; runner is the shield eval framework (same as today's `shield/evals/prd-docs/`).

**Files:**
- Create: `shield/evals/prd/prd-context-gathering.eval.md`
- Create: `shield/evals/prd/prd-research-opt-in.eval.md`
- Create: `shield/evals/prd/prd-low-confidence-walk.eval.md`
- Create: `shield/evals/prd/prd-current-context-section.eval.md`
- Create: `shield/evals/prd/prd-no-architecture-section.eval.md`
- Create: `shield/evals/prd/prd-cost-high-level.eval.md`
- Create: `shield/evals/prd/prd-finalize-html-rendered.eval.md`
- Create: `shield/evals/prd/prd-temp-cleanup.eval.md`
- Create: `shield/evals/prd/prd-terminologies-body-grounded.eval.md`
- Create: `shield/evals/prd/prd-terminologies-placeholder-until-last.eval.md`

- [ ] **Step 1: Write `prd-context-gathering.eval.md`**

```markdown
---
name: prd-context-gathering
skill_under_test: shield:prd
scenario: /prd asks where context comes from and ingests via prd-ingest.sh
---

## Setup
```bash
mkdir -p docs/shield/widget-flow-20260524
cat > /tmp/source-context.md <<'EOF'
# Widget flow notes
Users complain about losing form data when their session expires.
EOF
```

## Prompt
> Author a standard PRD for feature folder "widget-flow-20260524" using the shield:prd skill. When asked where context comes from, select "Local file" and provide /tmp/source-context.md. When asked about /research, say no. After ingest, list the steps you'd take next.

## Success criteria

### Structural
- prd-ingest\.sh
- widget-flow-20260524
- (where context|Where's your context|context comes from)

### Qualitative
- The agent invokes prd-ingest.sh against the local file (exit 0 success path).
- After ingest succeeds, the agent describes the next steps (research opt-in, then one-shot generation).
- The agent does NOT proceed to one-shot generation in this turn — it stops after listing next steps.

## Pass threshold
3 of 3 structural + 3 of 3 qualitative.
```

- [ ] **Step 2: Write `prd-research-opt-in.eval.md`**

```markdown
---
name: prd-research-opt-in
skill_under_test: shield:prd
scenario: After context ingest, /prd offers /research and handles yes/no
---

## Setup
```bash
mkdir -p docs/shield/onboarding-20260524
```

## Prompt
> You are running the shield:prd skill for feature "onboarding-20260524". Context ingest has completed (assume a Notion page was fetched). Now offer the user the /research opt-in and explain what happens on yes vs no. Do not proceed beyond the opt-in.

## Success criteria

### Structural
- (research|/research)
- (Recommended)
- (Yes|yes)
- (No|no|skip)

### Qualitative
- The opt-in prompt mentions that /research is recommended when context is light.
- The agent does NOT auto-invoke /research without user input.

## Pass threshold
3 of 4 structural + 2 of 2 qualitative.
```

- [ ] **Step 3: Write `prd-low-confidence-walk.eval.md`**

```markdown
---
name: prd-low-confidence-walk
skill_under_test: shield:prd
scenario: One-shot generation emits a confidence sidecar; walk visits only low-confidence sections
---

## Setup
```bash
mkdir -p docs/shield/checkout-20260524
cat > docs/shield/checkout-20260524/.prd-draft.confidence.json <<'EOF'
{"sections":[
  {"id":3,"confidence":"high"},
  {"id":4,"confidence":"low"},
  {"id":6,"confidence":"medium"},
  {"id":9,"confidence":"low"},
  {"id":15,"confidence":"low"}
]}
EOF
```

## Prompt
> Using the shield:prd skill, you have a draft at docs/shield/checkout-20260524/.prd-draft.md (assume it exists) and the confidence sidecar above. Run filter-low-confidence.sh against the sidecar and report which sections will be walked. Do NOT actually walk them — just list the section IDs and explain why §3 and §6 are skipped.

## Success criteria

### Structural
- filter-low-confidence\.sh
- \[4, 9, 15\]
- (high|medium)

### Qualitative
- Agent reports section_ids [4, 9, 15] as the walk targets.
- Agent correctly identifies §3 (high) and §6 (medium) as skipped.

## Pass threshold
3 of 3 structural + 2 of 2 qualitative.
```

- [ ] **Step 4: Write `prd-current-context-section.eval.md`**

```markdown
---
name: prd-current-context-section
skill_under_test: shield:prd
scenario: §3 Current context is filled with all four subsections
---

## Setup
```bash
mkdir -p docs/shield/billing-20260524
```

## Prompt
> Author the §3 Current context section of a PRD for "billing-20260524". The feature is migrating from a custom billing engine to Stripe Billing. Output only §3 content (markdown). Use the four-subsection structure: What exists today / The problem we're facing / What we're proposing to change / Why now.

## Success criteria

### Structural
- ### What exists today
- ### The problem we're facing
- ### What we're proposing to change
- ### Why now

### Qualitative
- "What exists today" describes the current custom billing engine as background — may include a Mermaid diagram or short architecture sketch, but does NOT prescribe a new design.
- "Why now" articulates urgency (e.g., maintenance burden, compliance, scale, competitive pressure) — not "we should do this".

## Pass threshold
4 of 4 structural + 2 of 2 qualitative.
```

- [ ] **Step 5: Write `prd-no-architecture-section.eval.md`**

```markdown
---
name: prd-no-architecture-section
skill_under_test: shield:prd
scenario: New scaffold has no standalone §5 Architecture (negative check)
---

## Setup
```bash
mkdir -p docs/shield/auth-rewrite-20260524
```

## Prompt
> Author a standard PRD outline for "auth-rewrite-20260524" — list ONLY the section headings (no body content). Use the new 20-section scaffold from shield:prd templates.md.

## Success criteria

### Structural
- ## 1\. Header
- ## 3\. Current context
- ## 14\. Rollout plan
- ## 20\. Sign-offs

### Qualitative
- The outline has NO standalone "Architecture" section.
- The outline has NO standalone "Functional requirements" section (replaced by §8 Product behavior).
- The outline has NO standalone "Non-functional requirements" section (replaced by §9 UX-impacting constraints).

## Pass threshold
4 of 4 structural + 3 of 3 qualitative.
```

- [ ] **Step 6: Write `prd-cost-high-level.eval.md`**

```markdown
---
name: prd-cost-high-level
skill_under_test: shield:prd
scenario: §15 Cost has lump estimates; per-resource SKUs are absent
---

## Setup
```bash
mkdir -p docs/shield/search-20260524
```

## Prompt
> Author the §15 Cost estimate section for a PRD about a new search feature backed by Elasticsearch + a vendor embedding API. Output the §15 content only. Follow the lump-estimate rule: infrastructure as a single category, vendor APIs as a single category, internal effort as engineer-weeks. Do NOT list per-resource SKUs.

## Success criteria

### Structural
- ## 15\. Cost
- (Infrastructure|infra)
- (Vendor|vendor|API)
- (engineer-weeks|engineering-weeks|engineer weeks)

### Must-not-find (structural)
- Aurora us-east-1
- NAT gateway \$
- EC2 m\d+\.
- gp3
- RDS multi-AZ

## Pass threshold
4 of 4 structural + 0 of 5 must-not-find matches.
```

- [ ] **Step 7: Write `prd-finalize-html-rendered.eval.md`**

```markdown
---
name: prd-finalize-html-rendered
skill_under_test: shield:prd
scenario: finalize-prd.sh re-renders prd.html whenever prd.md changes
---

## Setup
```bash
mkdir -p docs/shield/api-pagination-20260524
cat > docs/shield/api-pagination-20260524/.prd-draft.md <<'EOF'
# API Pagination — PRD

## 1. Header
Owner: alice

## 3. Current context
### What exists today
We return all rows in one response.

### The problem we're facing
Slow responses for large datasets.

### What we're proposing to change
Cursor-based pagination.

### Why now
Sales complaint Q2.
EOF
```

## Prompt
> Run finalize-prd.sh --entry prd --feature-dir docs/shield/api-pagination-20260524 --draft docs/shield/api-pagination-20260524/.prd-draft.md --output-dir docs/shield. Then verify that docs/shield/api-pagination-20260524/outputs/prd.html exists and contains both the feature name "api-pagination-20260524" and the H1 from the markdown.

## Success criteria

### Structural
- finalize-prd\.sh
- outputs/prd\.html
- api-pagination-20260524

### Qualitative
- finalize-prd.sh exited 0.
- outputs/prd.html exists.
- prd.html contains "API Pagination" (the H1 from the source).
- .prd-draft.md was deleted by finalize.

## Pass threshold
3 of 3 structural + 4 of 4 qualitative.
```

- [ ] **Step 8: Write `prd-temp-cleanup.eval.md`**

```markdown
---
name: prd-temp-cleanup
skill_under_test: shield:prd
scenario: After finalize, .prd-draft.md and .prd-draft.confidence.json are removed
---

## Setup
```bash
mkdir -p docs/shield/feature-flags-20260524
echo "# Feature flags" > docs/shield/feature-flags-20260524/.prd-draft.md
echo '{"sections":[]}' > docs/shield/feature-flags-20260524/.prd-draft.confidence.json
```

## Prompt
> Run finalize-prd.sh --entry prd against the feature-flags-20260524 feature. After it completes, list the contents of the feature folder. Confirm that .prd-draft.md and .prd-draft.confidence.json are gone, but prd.md is present.

## Success criteria

### Structural
- prd\.md
- prd\.meta\.json

### Qualitative
- After finalize: .prd-draft.md does NOT exist.
- After finalize: .prd-draft.confidence.json does NOT exist.
- After finalize: prd.md exists with the H1 from the original draft.
- After finalize: outputs/prd.html exists.

## Pass threshold
2 of 2 structural + 4 of 4 qualitative.
```

- [ ] **Step 9: Write `prd-terminologies-body-grounded.eval.md`**

```markdown
---
name: prd-terminologies-body-grounded
skill_under_test: shield:prd
scenario: §2 contains ONLY terms used in §3..§20; unused research-glossary terms are dropped
---

## Setup
```bash
mkdir -p docs/shield/auth-2026-20260524
cat > docs/shield/auth-2026-20260524/.session-transcript.md <<'EOF'
# Auth 2026 — research

## Glossary
| Term | Definition |
|---|---|
| JWT | JSON Web Token |
| OAuth | Open Authorization protocol |
| PLG | Product-led growth |
EOF
cat > /tmp/prd-body.md <<'EOF'
# Auth 2026 — PRD

## 1. Header
Owner: alice

## 2. Terminologies

<!-- placeholder -->

## 3. Current context
We use JWT today via OAuth.

## 7. User stories
Story 1: Anika signs in with OAuth.

## 8. Product behavior
JWT rotation handled by the backend.
EOF
```

## Prompt
> The research transcript contains JWT, OAuth, PLG. The PRD body uses JWT (twice) and OAuth (twice) but does NOT use PLG. Run the §2 Terminologies body-grounding protocol from shield:prd SKILL.md against /tmp/prd-body.md. Use extract-glossary-candidates.sh on the transcript and count-term-in-body.sh for each candidate. Show the final §2 table. The table MUST contain JWT and OAuth but NOT PLG.

## Success criteria

### Structural
- \| JWT \|
- \| OAuth \|

### Must-not-find (structural)
- \| PLG \|

### Qualitative
- Agent invokes extract-glossary-candidates.sh against the transcript.
- Agent invokes count-term-in-body.sh for each candidate.
- PLG is dropped because count=0 in the PRD body.

## Pass threshold
2 of 2 structural + 0 of 1 must-not-find + 3 of 3 qualitative.
```

- [ ] **Step 10: Write `prd-terminologies-placeholder-until-last.eval.md`**

```markdown
---
name: prd-terminologies-placeholder-until-last
skill_under_test: shield:prd
scenario: During one-shot generation and the walk, §2 stays as the placeholder block
---

## Setup
```bash
mkdir -p docs/shield/notifications-20260524
```

## Prompt
> Author a standard PRD for "notifications-20260524" via shield:prd. Stop AFTER the one-shot generation step (do NOT run the §2 protocol or finalize). Output the current state of .prd-draft.md's §2 Terminologies section only.

## Success criteria

### Structural
- ## 2\. Terminologies
- placeholder
- \| Term \| Definition \|

### Must-not-find (structural)
- ^\| [A-Z]+ \| [A-Z]    # No filled term/definition rows yet

### Qualitative
- §2 is present but empty (placeholder block only).
- No actual terminology rows have been filled at this stage.

## Pass threshold
3 of 3 structural + 0 must-not-find + 2 of 2 qualitative.
```

- [ ] **Step 11: Commit**

```bash
git add shield/evals/prd/
git commit -m "test(evals/prd): 10 evals for new /prd entry flow

Covers context-ingest, research opt-in, low-confidence walk, current-
context section structure, scaffold-has-no-architecture, lump-only
cost, finalize-renders-html, temp cleanup, §2 body-grounding, §2
placeholder-until-last."
```

---


## Task 13: Add `shield/evals/prd-review/` evals (8 evals)

**Files:** 8 eval files at `shield/evals/prd-review/`.

- [ ] **Step 1: Write `prd-review-walk-output-shape.eval.md`**

```markdown
---
name: prd-review-walk-output-shape
skill_under_test: shield:prd
scenario: /prd-review finalize produces the same output shape as /prd (prd.md + prd.html + prd.meta.json)
---

## Setup
```bash
mkdir -p docs/shield/refunds-20260524/reviews/prd/2026-05-24
cat > docs/shield/refunds-20260524/reviews/prd/2026-05-24/corrected-prd.md <<'EOF'
# Refunds — PRD

## 1. Header
Owner: alice

## 3. Current context
### What exists today
Refunds happen via support tickets.

### The problem we're facing
Slow + manual.

### What we're proposing to change
Self-service refund flow.

### Why now
Q3 sales unblock.
EOF
```

## Prompt
> Run finalize-prd.sh --entry prd-review --feature-dir docs/shield/refunds-20260524 --draft docs/shield/refunds-20260524/reviews/prd/2026-05-24/corrected-prd.md --review-dir docs/shield/refunds-20260524/reviews/prd/2026-05-24 --output-dir docs/shield. List the resulting files in docs/shield/refunds-20260524/.

## Success criteria

### Structural
- refunds-20260524/prd\.md
- refunds-20260524/outputs/prd\.html
- refunds-20260524/prd\.meta\.json
- review_link

### Qualitative
- {feature}/prd.md, outputs/prd.html, and prd.meta.json are all present.
- prd.meta.json contains review_link pointing at the review-dir.
- corrected-prd.md in the review-dir is deleted.

## Pass threshold
4 of 4 structural + 3 of 3 qualitative.
```

- [ ] **Step 2: Write `prd-review-sparse-detection.eval.md`**

```markdown
---
name: prd-review-sparse-detection
skill_under_test: shield:prd
scenario: sparse-sections.sh identifies §s with Critical D/F findings
---

## Setup
```bash
mkdir -p /tmp/sparse-test
cat > /tmp/sparse-test/review-comments.json <<'EOF'
{
  "dimensions": [
    {"id":1,"name":"Problem clarity","grade":"D","evaluation_points":[
      {"id":"1a","grade":"F","severity":"Critical","gap":"no persona","suggestion":"add Anya"}]},
    {"id":3,"name":"Measurable success","grade":"B","evaluation_points":[
      {"id":"3a","grade":"B","severity":"Critical","gap":null,"suggestion":null}]},
    {"id":5,"name":"NFR","grade":"D","evaluation_points":[
      {"id":"5a","grade":"D","severity":"Critical","gap":"privacy unclear","suggestion":"specify PII"}]}
  ]
}
EOF
```

## Prompt
> Run sparse-sections.sh --review /tmp/sparse-test/review-comments.json --dim-map shield/skills/general/prd/dim-section-map.yaml. Report the section_ids returned.

## Success criteria

### Structural
- section_ids
- \[3, 9, 10, 11\]

### Qualitative
- Dim 1 (1a=F Critical) maps to §3 → included.
- Dim 5 (5a=D Critical) maps to §9, §10, §11 → all three included.
- Dim 3 (3a=B Critical) excluded (B is not D/F).

## Pass threshold
2 of 2 structural + 3 of 3 qualitative.
```

- [ ] **Step 3: Write `prd-review-additional-context-flow.eval.md`**

```markdown
---
name: prd-review-additional-context-flow
skill_under_test: shield:prd
scenario: When sparse sections are detected, /prd-review asks for additional context and ingests it
---

## Setup
```bash
mkdir -p docs/shield/onboarding-v2-20260524/reviews/prd/2026-05-24
echo '{"dimensions":[{"id":1,"name":"Problem","grade":"F","evaluation_points":[{"id":"1a","grade":"F","severity":"Critical","gap":"no problem","suggestion":"add"}]}]}' > docs/shield/onboarding-v2-20260524/reviews/prd/2026-05-24/review-comments.json
```

## Prompt
> In the /prd-review flow for "onboarding-v2-20260524", sparse-sections.sh has returned section_ids=[3] (§3 Current context is sparse). What does the agent ask the user next? Show the exact prompt the user would see. Do NOT proceed past the prompt.

## Success criteria

### Structural
- (sparse|sparse based)
- §3
- (Notion|Jira|Confluence|Linear|file|paste)
- (gather more context|additional context)

### Qualitative
- Agent surfaces the specific § (§3 Current context) that's sparse.
- Agent offers the same source list as /prd's initial context-gathering prompt.
- Agent does NOT auto-proceed without user input.

## Pass threshold
4 of 4 structural + 3 of 3 qualitative.
```

- [ ] **Step 4: Write `prd-review-dispatch-aggregation.eval.md`**

```markdown
---
name: prd-review-dispatch-aggregation
skill_under_test: shield:prd
scenario: aggregate-review.sh deterministically produces composite + P0-gate from dim-block JSON
---

## Setup
```bash
mkdir -p /tmp/agg-test/dispatch
# All A grades except one Critical-D in dim 1.
for d in 1 2 3 7 8 9 10 11 12; do
  ep_grade=A; sev=Critical
  if [ "$d" = "1" ]; then ep_grade=D; fi
  cat > /tmp/agg-test/dispatch/dim-${d}.json <<EOF
{"id":${d},"name":"Dim ${d}","grade":"A","evaluation_points":[
  {"id":"${d}a","grade":"${ep_grade}","severity":"Critical","gap":null,"suggestion":null}]}
EOF
done
cat > /tmp/agg-test/dispatch/agile-coach.json <<'EOF'
{"persona":"agile-coach","persona_grade":"A","dimensions":[
  {"id":4,"name":"AC","grade":"A","evaluation_points":[]}]}
EOF
cat > /tmp/agg-test/dispatch/architect.json <<'EOF'
{"persona":"tech-lead","persona_grade":"A","dimensions":[
  {"id":5,"name":"NFR","grade":"A","evaluation_points":[]},
  {"id":6,"name":"Rollout","grade":"A","evaluation_points":[]}]}
EOF
cat > /tmp/agg-test/dispatch/dx-engineer.json <<'EOF'
{"persona":"dx-engineer","persona_grade":"A","dimensions":[],"anti_patterns":[]}
EOF
cat > /tmp/agg-test/dispatch/finops-analyst.json <<'EOF'
{"persona":"finops-analyst","persona_grade":"A","dimensions":[
  {"id":13,"name":"Cost","grade":"A","evaluation_points":[]}]}
EOF
mkdir -p /tmp/agg-test/out
```

## Prompt
> Run aggregate-review.sh --dispatch-dir /tmp/agg-test/dispatch --out-dir /tmp/agg-test/out. Report verdict, composite, and p0_count from the success envelope.

## Success criteria

### Structural
- verdict
- p0_count
- Needs Work

### Qualitative
- p0_count is 1 (the Critical D in dim 1).
- Verdict is "Needs Work" despite all dim grades being A — P0-gate forces it.
- /tmp/agg-test/out/review-comments.json is written.
- /tmp/agg-test/out/summary.md is written.

## Pass threshold
3 of 3 structural + 4 of 4 qualitative.
```

- [ ] **Step 5: Write `prd-review-corrected-cleanup.eval.md`**

```markdown
---
name: prd-review-corrected-cleanup
skill_under_test: shield:prd
scenario: After finalize, corrected-prd.md is deleted; side-artifacts (summary.md, source-prd.md, etc.) are retained
---

## Setup
```bash
mkdir -p docs/shield/billing-v2-20260524/reviews/prd/2026-05-24/detailed
echo "# Corrected" > docs/shield/billing-v2-20260524/reviews/prd/2026-05-24/corrected-prd.md
echo "scorecard" > docs/shield/billing-v2-20260524/reviews/prd/2026-05-24/summary.md
echo "original" > docs/shield/billing-v2-20260524/reviews/prd/2026-05-24/source-prd.md
echo '{}' > docs/shield/billing-v2-20260524/reviews/prd/2026-05-24/review-comments.json
echo "pm" > docs/shield/billing-v2-20260524/reviews/prd/2026-05-24/detailed/product-manager.md
```

## Prompt
> Run finalize-prd.sh --entry prd-review against billing-v2-20260524's review folder. After it completes, list the contents of docs/shield/billing-v2-20260524/reviews/prd/2026-05-24/. Confirm corrected-prd.md is gone but summary.md, source-prd.md, review-comments.json, and detailed/ are preserved.

## Success criteria

### Structural
- summary\.md
- source-prd\.md
- review-comments\.json
- detailed

### Qualitative
- corrected-prd.md does NOT exist after finalize.
- summary.md, source-prd.md, review-comments.json, detailed/product-manager.md all still exist.

## Pass threshold
4 of 4 structural + 2 of 2 qualitative.
```

- [ ] **Step 6: Write `prd-review-rubric-narrowing.eval.md`**

```markdown
---
name: prd-review-rubric-narrowing
skill_under_test: shield:architect
scenario: Dim 5 fails per-resource SKU mentions; passes UX-only NFRs
---

## Setup
```bash
mkdir -p /tmp/rubric-test
cat > /tmp/rubric-test/source-prd-good.md <<'EOF'
# Feature
## 9. UX-impacting constraints
If Stripe rate-limits us, the user sees a 'Try again in 30s' banner and we retry automatically for up to 5 minutes before surfacing a hard error.
Accessibility: all forms reachable by keyboard.
EOF
cat > /tmp/rubric-test/source-prd-bad.md <<'EOF'
# Feature
## 9. UX-impacting constraints
p99 latency target: 50ms.
Use Redis for session cache.
EBS gp3 volumes for primary storage.
EOF
```

## Prompt
> Using the shield:architect agent's dim 5 prompt (narrowed UX-only per shield:prd rubric.md), grade /tmp/rubric-test/source-prd-good.md and /tmp/rubric-test/source-prd-bad.md. Report the grade for each.

## Success criteria

### Qualitative
- The "good" PRD scores A or B on dim 5 (mentions third-party failure UX + accessibility).
- The "bad" PRD does NOT score A or B on dim 5 — implementation-detail content does not count toward UX grading.
- The agent does NOT penalize the "good" PRD for omitting p99 / capacity / SKUs.

## Pass threshold
3 of 3 qualitative.
```

- [ ] **Step 7: Write `prd-review-cost-anti-pattern.eval.md`**

```markdown
---
name: prd-review-cost-anti-pattern
skill_under_test: shield:finops-analyst
scenario: Dim 13 auto-fails per-resource SKU mentions in §15 Cost estimate
---

## Setup
```bash
mkdir -p /tmp/cost-test
cat > /tmp/cost-test/lump.md <<'EOF'
# Feature
## 15. Cost estimate
| Category | Estimate | Notes |
|---|---|---|
| Infrastructure | ~$8k/mo (with HA) | DB + compute |
| Vendor / APIs | ~$2k/mo | Stripe + Twilio |
| Internal effort | 6 engineer-weeks | one-time delivery |
EOF
cat > /tmp/cost-test/skus.md <<'EOF'
# Feature
## 15. Cost estimate
| Category | Estimate | Notes |
|---|---|---|
| Aurora us-east-1 multi-AZ | $4500/mo | primary db |
| NAT gateway | $150/mo | egress |
| EC2 m5.xlarge × 4 | $700/mo | app tier |
EOF
```

## Prompt
> Using the shield:finops-analyst agent (narrowed dim 13 per shield:prd rubric.md), grade /tmp/cost-test/lump.md and /tmp/cost-test/skus.md. Report grade + evidence_quote for 13a in each.

## Success criteria

### Qualitative
- lump.md scores A on 13a (lump categories, no SKUs).
- skus.md scores F on 13a (auto-fail: "Aurora", "NAT gateway", "EC2 m5.xlarge" all present).
- The skus.md evidence_quote cites one of the offending lines verbatim.

## Pass threshold
3 of 3 qualitative.
```

- [ ] **Step 8: Write `prd-review-legacy-fold.eval.md`**

```markdown
---
name: prd-review-legacy-fold
skill_under_test: shield:prd
scenario: A legacy PRD with standalone §5 Architecture has its content folded into §3 Current context's "What exists today"
---

## Setup
```bash
mkdir -p docs/shield/audit-log-20260524/reviews/prd/2026-05-24
cat > docs/shield/audit-log-20260524/reviews/prd/2026-05-24/source-prd.md <<'EOF'
# Audit Log — PRD (legacy 20-section)

## 1. Header
Owner: alice

## 3. Problem
Customers can't see when admins access their data.

## 5. Architecture & flows
```mermaid
graph LR
  App --> AuditService --> Postgres
```
Today: AuditService writes synchronously to a single Postgres instance.

## 6. Goals
- Surface admin-access events to customers.
EOF
```

## Prompt
> The source PRD at docs/shield/audit-log-20260524/reviews/prd/2026-05-24/source-prd.md is a legacy 20-section PRD with a standalone §5 Architecture & flows. Generate the corrected PRD (PHASE B of /prd-review) using the new 20-section scaffold. Output ONLY §3 Current context. The architecture content from legacy §5 MUST appear inside §3's "What exists today" subsection. The corrected PRD must NOT have a standalone §5 Architecture section.

## Success criteria

### Structural
- ## 3\. Current context
- ### What exists today
- AuditService
- (mermaid|graph LR|Postgres)

### Must-not-find (structural)
- ## 5\. Architecture
- ## 5\. Architecture & flows

### Qualitative
- The Mermaid diagram from legacy §5 appears inside §3 "What exists today".
- The corrected output has NO standalone §5 Architecture heading.

## Pass threshold
4 of 4 structural + 0 of 2 must-not-find + 2 of 2 qualitative.
```

- [ ] **Step 9: Commit**

```bash
git add shield/evals/prd-review/
git commit -m "test(evals/prd-review): 8 evals for new /prd-review entry flow

Covers output-shape parity with /prd, sparse detection, additional-
context flow, dispatch+aggregation (incl P0-gate), corrected-cleanup
post-finalize, rubric narrowing for dim 5 and dim 13, and legacy
§5 Architecture folding into §3 Current context."
```

---

## Task 14: Add `.claude/skills/script-llm-contract/evals/` (3 evals)

**Files:** 3 eval files at `.claude/skills/script-llm-contract/evals/`.

- [ ] **Step 1: Write `script-exit-code-contract.eval.md`**

```markdown
---
name: script-exit-code-contract
skill_under_test: script-llm-contract
scenario: A fixture script returns code 3 with JSON payload; LLM follows the documented branch (retry / fallback / prompt)
---

## Setup
```bash
mkdir -p /tmp/contract-fixture
cat > /tmp/contract-fixture/fixture.sh <<'BASH'
#!/usr/bin/env bash
echo '{"ok":false,"code":3,"category":"external_resource_unavailable","resource":"notion_mcp","reason":"401 unauthorized","suggested_action":"ask_user_to_authenticate_notion_mcp","fallback":"webfetch"}'
exit 3
BASH
chmod +x /tmp/contract-fixture/fixture.sh
```

## Prompt
> Run /tmp/contract-fixture/fixture.sh. Per the script-llm-contract skill, the exit code is 3 (external_resource_unavailable). What's your next move? List the options the contract documents (retry / fallback / prompt user) and pick one given the script's suggested_action.

## Success criteria

### Structural
- exit (code )?3
- external_resource_unavailable
- notion_mcp
- (suggested_action|webfetch|MCP)

### Qualitative
- Agent reads exit code 3 and JSON payload (not just parsing stderr).
- Agent enumerates the documented options: retry, fallback (webfetch), prompt user.
- Agent picks an action that's consistent with the suggested_action field.

## Pass threshold
4 of 4 structural + 3 of 3 qualitative.
```

- [ ] **Step 2: Write `script-no-prompting.eval.md`**

```markdown
---
name: script-no-prompting
skill_under_test: script-llm-contract
scenario: A fixture script that reads stdin interactively (via `read`) violates the contract; the skill flags it as wrong
---

## Setup
```bash
mkdir -p /tmp/bad-script
cat > /tmp/bad-script/asks.sh <<'BASH'
#!/usr/bin/env bash
read -p "What's your name? " name
echo "{\"ok\":true,\"data\":{\"name\":\"$name\"}}"
BASH
chmod +x /tmp/bad-script/asks.sh
```

## Prompt
> Review /tmp/bad-script/asks.sh against the script-llm-contract skill. Is this script compliant? If not, what specifically violates the contract and how should it be fixed?

## Success criteria

### Structural
- (read -p|interactive|prompt)
- exit (code )?4
- needs_human

### Qualitative
- Agent identifies `read -p` (or `input()`-style interactive prompting) as a violation.
- Agent points the author at the exit-4 / needs_human pattern as the fix.
- Agent notes that the script should accept the value via arg or stdin, not interactive prompt.

## Pass threshold
3 of 3 structural + 3 of 3 qualitative.
```

- [ ] **Step 3: Write `proactive-script-suggestion.eval.md`**

```markdown
---
name: proactive-script-suggestion
skill_under_test: script-llm-contract
scenario: When editing a SKILL.md with deterministic steps coded as LLM-only, the skill proactively suggests scripts
---

## Setup
```bash
mkdir -p /tmp/skill-fixture
cat > /tmp/skill-fixture/SKILL.md <<'EOF'
---
name: my-skill
description: Example LLM-driven skill
---

# my-skill

## Workflow

1. Read all *.json files in <input-dir>.
2. For each file, parse the "score" field and compute the average.
3. If the average is below 70, write a warning to stderr.
4. Build a markdown table summarizing scores per file.
5. Walk the user through the table and ask which files to keep.
EOF
```

## Prompt
> Review /tmp/skill-fixture/SKILL.md against the script-llm-contract skill. Identify which steps are deterministic (could be a script) vs which require LLM judgment. Recommend scripts for the deterministic steps.

## Success criteria

### Structural
- (script|deterministic)
- (average|parse|compute)
- (walk|judgment|interactive)

### Qualitative
- Agent identifies steps 1-4 (JSON parsing, average computation, threshold check, markdown table) as deterministic — should be a script.
- Agent identifies step 5 (interactive walk) as LLM territory.
- Agent suggests at least one concrete script (e.g., `score-summary.sh` that takes input-dir and emits a JSON envelope with the table).

## Pass threshold
3 of 3 structural + 3 of 3 qualitative.
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/script-llm-contract/evals/
git commit -m "test(skill/script-llm-contract): 3 evals for contract compliance

Covers exit-code branching (LLM reads code 3 + JSON payload),
no-prompting (script using `read -p` flagged as violation), and
proactive script suggestion when reviewing a SKILL.md with
deterministic steps coded as LLM-only."
```

---


## Task 15: Delete `shield/evals/prd-docs/`

The legacy evals test rules that are now reversed (e.g., `01-terminologies-autofill.md` requires "ALL Source A rows MUST appear" — the opposite of the new body-grounding rule). Task 12 wrote the replacement evals at `shield/evals/prd/`. Delete the legacy directory.

**Files:**
- Delete: `shield/evals/prd-docs/` (entire directory, 5 files)

- [ ] **Step 1: Sanity-check that Task 12 evals exist before deletion**

```bash
ls shield/evals/prd/ | wc -l
# Expected: 10 (the evals from Task 12).

ls shield/evals/prd-docs/
# Expected: 5 legacy files (01-...md through 05-...md).
```

If `shield/evals/prd/` is empty or has fewer than 10 files, STOP and complete Task 12 first.

- [ ] **Step 2: Delete the legacy directory**

```bash
git rm -r shield/evals/prd-docs/
```

- [ ] **Step 3: Verify no references remain**

```bash
grep -rn "evals/prd-docs" shield/ docs/ .claude/ 2>/dev/null
# Expected: NO matches (or only matches in this plan document).
```

If matches turn up outside this plan file, update those references to point at `shield/evals/prd/` before committing.

- [ ] **Step 4: Commit**

```bash
git commit -m "test(evals): delete legacy shield/evals/prd-docs/

Tests rules that are reversed in the new prd/ design (e.g., the
'ALL Source A glossary rows MUST appear' rule is now the opposite —
body-grounding wins). Replaced by shield/evals/prd/ in Task 12."
```

---

## Task 16: Delete legacy `prd-docs/` and `prd-review/` skill directories

The consolidated `shield/skills/general/prd/` (Task 1 + Task 9 + Tasks 6/7/8 edits) backs both `/prd` and `/prd-review` now. Commands (Task 10, 11) and agents (Task 4, 5) reference the new skill. Time to cut over.

**Files:**
- Delete: `shield/skills/general/prd-docs/` (entire directory)
- Delete: `shield/skills/general/prd-review/` (entire directory)

- [ ] **Step 1: Pre-flight — verify replacements exist**

```bash
# New skill files all present?
test -f shield/skills/general/prd/SKILL.md           && echo "SKILL: OK"
test -f shield/skills/general/prd/templates.md       && echo "templates: OK"
test -f shield/skills/general/prd/rubric.md          && echo "rubric: OK"
test -f shield/skills/general/prd/dimensions.md      && echo "dimensions: OK"
test -f shield/skills/general/prd/scoring.md         && echo "scoring: OK"
test -f shield/skills/general/prd/ingest.md          && echo "ingest: OK"
test -f shield/skills/general/prd/meta-schema.md     && echo "meta-schema: OK"
test -f shield/skills/general/prd/type-detection.md  && echo "type-detection: OK"
test -f shield/skills/general/prd/dim-section-map.yaml && echo "dim-section-map: OK"
test -f shield/skills/general/prd/persona-weights.yaml && echo "persona-weights: OK"
test -d shield/skills/general/prd/prompts            && echo "prompts/: OK"
ls shield/skills/general/prd/prompts/ | wc -l
# Expected: 9 prompt files.
```

If ANY file is missing, STOP and complete the relevant earlier task first.

- [ ] **Step 2: Pre-flight — verify command + agent references already point at new skill**

```bash
grep -E "(skill_under_test:|shield:prd-docs|shield:prd-review)" \
  shield/commands/prd.md shield/commands/prd-review.md \
  shield/agents/*.md \
  shield/evals/prd/*.eval.md shield/evals/prd-review/*.eval.md
# Expected: only `shield:prd` matches; NO `shield:prd-docs` or `shield:prd-review`.
```

If old references remain, update them before deletion.

- [ ] **Step 3: Delete the legacy directories**

```bash
git rm -r shield/skills/general/prd-docs/
git rm -r shield/skills/general/prd-review/
```

- [ ] **Step 4: Verify no remaining references in the codebase**

```bash
grep -rn "skills/general/prd-docs\|skills/general/prd-review" \
  shield/ docs/ .claude/ 2>/dev/null \
  | grep -v "docs/superpowers/specs/" \
  | grep -v "docs/superpowers/plans/"
# Expected: NO matches outside of specs/plans documentation.
```

- [ ] **Step 5: Smoke test — invoke the new skill from a fresh prompt**

In a fresh terminal:
```bash
ls shield/skills/general/
# Expected: prd/ is present, prd-docs/ and prd-review/ are gone.
```

- [ ] **Step 6: Commit**

```bash
git commit -m "refactor(prd): delete legacy prd-docs/ and prd-review/ skill directories

Consolidated into shield/skills/general/prd/ (Task 1 + Task 9 of the
cutover plan). /prd and /prd-review commands point at shield:prd;
agents reference the narrowed dim 5 + dim 13 rubric; evals updated."
```

---

## Task 17: Bump `.claude-plugin/marketplace.json` Shield version

Per repo convention (`CLAUDE.md` Git Conventions), bump the version in `marketplace.json` only — NOT in `plugin.json` for relative-path plugins. This is a minor bump (new product-facing feature: restructured PRD scaffold + reviewer flow).

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current version**

```bash
grep -A 1 '"name": "shield"' .claude-plugin/marketplace.json | head -5
```

Capture the current Shield version. Expected format: `"version": "2.X.Y"`.

- [ ] **Step 2: Bump the minor version**

Open `.claude-plugin/marketplace.json` and locate Shield's entry. Increment the minor version by 1 (e.g., `2.19.0` → `2.20.0`). Reset patch to 0.

Run: `grep -A 1 '"name": "shield"' .claude-plugin/marketplace.json | head -5`
Confirm the new version reads correctly.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.X.0 — prd + prd-review restructure

Major behavior changes (user-visible): consolidated /prd and /prd-review
share a 20-section product-focused scaffold; /prd-review produces the
same output shape as /prd; reviewer rubric narrows dim 5 (UX-only NFRs)
and dim 13 (lump cost); §2 Terminologies is body-grounded and populated
last. Internal: deterministic scripts under shield/scripts/prd/ with a
documented script-LLM contract; legacy prd-docs/ + prd-review/
directories removed."
```

(Substitute the actual incremented version number for `2.X.0` in the commit body.)

---

## Self-Review

**Spec coverage:**

| Spec entry | Plan 2 task |
|---|---|
| Consolidated `prd/` skill dir (spec §4) | Task 1 (carry over) + Task 9 (SKILL.md) |
| 20-section scaffold + lean variant + HTML shell (spec §5) | Task 2 |
| `/prd` entry flow (spec §6) | Task 9 SKILL.md + Task 10 commands/prd.md |
| `/prd-review` entry flow (spec §7) | Task 9 SKILL.md + Task 11 commands/prd-review.md |
| Shared finalize step (spec §8) | Plan 1 Task 14 wrote it; Plan 2 Task 8 extends shell |
| Rubric narrowing dim 5 + dim 13 (spec §9.1, §9.2) | Task 3 (rubric.md) + Task 5 (architect + finops agents) |
| `implementation-detail-bleed` anti-pattern (spec §9.3) | Task 4 (DX agent) |
| `dim-section-map.yaml` (spec §10) | Plan 1 Task 2 |
| `persona-weights.yaml` SSoT (spec §11 + Plan 1 self-review) | Task 6 |
| Index.html regeneration (spec §8 step f, Plan 1 deferred) | Task 7 |
| Full HTML shell with TOC/nav/sidecar (spec §8 step c, Plan 1 deferred) | Task 8 |
| §2 Terminologies body-grounded protocol (spec §5.1) | Task 9 SKILL.md (protocol section) |
| Lazy legacy migration (spec §14) | Task 9 SKILL.md "Legacy fold rule" + Task 13 eval `prd-review-legacy-fold` |
| Delete legacy directories (spec §15) | Task 15 (evals) + Task 16 (skills) |
| Marketplace version bump (spec §17) | Task 17 |
| All 19 evals from spec §13 | Task 12 (10 prd evals) + Task 13 (8 prd-review evals) + Task 14 (3 script-llm-contract evals) |

**Placeholder scan:** None — every step has full code or full markdown content inline. The `2.X.0` placeholder in Task 17 is intentional (depends on the current version, which the engineer reads in Step 1).

**Type consistency:**
- Script invocation signatures match Plan 1's published interfaces:
  - `prd-ingest.sh --source <path|url> | --paste-from-stdin`
  - `detect-prd-type.sh <prd-path>`
  - `next-review-dir.sh --reviews-root <path> --date <YYYY-MM-DD>`
  - `sparse-sections.sh --review <path> --dim-map <path>`
  - `map-gaps-to-sections.sh --review <path> --dim-map <path>`
  - `aggregate-review.sh --dispatch-dir <path> --out-dir <path> [--persona-weights <path>]`
  - `filter-low-confidence.sh --sidecar <path>`
  - `update-manifest.sh --output-dir <path>`
  - `finalize-prd.sh --entry prd|prd-review --feature-dir <path> --draft <path> --output-dir <path> [--review-dir <path>]`
  - `extract-glossary-candidates.sh <transcript-path>`
  - `count-term-in-body.sh --term <str> --prd <path>`
- Same exit-code categories everywhere (0/1/2/3/4/5).
- Same JSON envelope shape (`{"ok":..., "data": ...}` / `{"ok":false,"code":N,...}`).

**Risks called out:**

- Task 6 refactor adds `--persona-weights` arg to `aggregate_review.py`. If Plan 1's `aggregate-review.sh` is invoked from anywhere outside `prd/SKILL.md`, those call sites continue to work (the arg is optional with a default). Plan 2 doesn't add other consumers.
- Task 8 reorders `finalize_prd.py` `main()` to write meta BEFORE rendering. If existing call sites rely on the previous ordering, this could break — but there are no existing external call sites (only test cases, which are updated in the same task).
- Task 16's directory deletion is irreversible from this branch. Pre-flight checks in Steps 1-2 must pass before the `git rm -r`. If a referenced file in the new `prd/` directory is missing, the deletion would leave references dangling.
- Plan 2 assumes Plan 1 has merged. If not, Task 1 has nothing to carry into and Plan 2 cannot start. The plan header calls this out, but worth re-validating before kickoff.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-prd-restructure-cutover.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Plan 2 has 17 tasks; some (Task 9 SKILL.md, Task 12 evals, Task 13 evals) have multiple sub-steps that are themselves bite-sized. Best subagent fit: one subagent per task, with the orchestrator reviewing each commit before unblocking the next.

**2. Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Reasonable for Plan 2 since most edits are markdown content rather than algorithmic code.

Which approach? Prerequisite: Plan 1 must have merged before Plan 2 starts.
