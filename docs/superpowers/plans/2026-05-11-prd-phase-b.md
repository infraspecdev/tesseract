# PRD Author (`/prd`) — Phase B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship Phase B — the `/prd` author command — with the 17-section problem-first scaffold (lean variant available), custom-template merging, lean→standard upgrade flow, the story-coverage scaffolding step (consuming the skill shipped in Phase A), and PRD-to-Plan bidirectional linkage.

**Architecture:** Markdown-driven Shield skill following the existing `plan-docs` pattern. `/prd` orchestrates: (1) read `.shield.json` for `prd_template` config, (2) detect prior `/research` transcript to pre-populate sections, (3) ask user for PRD type (standard | lean), (4) walk sections one at a time, (5) between Sections 4 (Goals) and 6 (Stories), invoke `shield:story-coverage` for scaffolding, (6) merge custom-template content with required sections, (7) detect prior lean PRD in feature folder and offer upgrade flow, (8) write `prd.md`, `prd.html`, `prd.meta.json`.

**Tech Stack:** All markdown content (skills/commands/templates). No new Python code. HTML rendering reuses the existing `plan-docs` CSS conventions (`#1a73e8` blue accent, max-width 900px).

**Phase A prerequisite:** This plan assumes Phase A (`/prd-review` + `story-coverage` skill) is shipped. Phase B's story-coverage scaffolding step calls into the Phase A skill.

---

## Spec reference

This plan implements **Phase B** of `docs/superpowers/specs/2026-05-09-prd-and-research-redesign-design.md`. Read the spec's "Default PRD scaffold" + "Lean variant" + "PRD-to-Plan bidirectional linkage" sections first.

## Scope of this plan (Phase B only)

**In scope:**
- New skill: `shield/skills/general/prd-docs/` (4 files: SKILL.md, templates.md, meta-schema.md, type-detection.md)
- New command: `shield/commands/prd.md`
- Minor update to `shield/skills/general/plan-docs/SKILL.md` — consume `prd.md` as context if present
- Minor update to `shield/skills/general/plan-review/SKILL.md` — consume `prd.meta.json` if present
- Test fixtures: 3 cases at `shield/skills/general/prd-docs/test-fixtures/` (new-from-scratch, with-research-transcript, lean-upgrade)
- RED-GREEN validation
- Marketplace version bump (shield 2.12.0 → 2.13.0, assuming Phase A shipped 2.12.0)

**Out of scope:**
- The story-coverage skill itself (shipped in Phase A)
- `/prd-review` command (Phase A)
- `/research` Phase 1 enhancement (Phase C)
- Converters that post to external systems
- Sample / starter PRDs in `templates.md` (out of Phase B; tracked as future enhancement)
- PRD lifecycle / status beyond `Draft` (future enhancement)

**Dependencies:**
- Phase A must be shipped first — `/prd` invokes `shield:story-coverage` for scaffolding
- Existing `plan-docs` skill — for HTML rendering CSS conventions

---

## File structure

**New files:**

```
shield/
├── commands/
│   └── prd.md                              (~70 lines — command definition)
└── skills/general/prd-docs/
    ├── SKILL.md                            (~250 lines — orchestration workflow + step skeleton)
    ├── templates.md                        (~350 lines — 17-section scaffold + lean variant + HTML render templates)
    ├── meta-schema.md                      (~80 lines — prd.meta.json schema with linked_plans field)
    ├── type-detection.md                   (~60 lines — lean vs standard heuristics + override flow)
    └── test-fixtures/
        ├── new-from-scratch-expected.md    (~250 lines — expected prd.md output for a new feature)
        ├── with-research-transcript.md     (~80 lines — research transcript used as input)
        ├── with-research-transcript-expected.md  (~300 lines — expected prd.md output after pre-population)
        └── lean-upgrade-prior-prd.md       (~80 lines — lean PRD that triggers upgrade flow)
```

**Modified files:**

```
shield/skills/general/plan-docs/SKILL.md    (~+15 lines — read prd.md as context if present; record source_prd in plan.json)
shield/skills/general/plan-review/SKILL.md  (~+10 lines — read prd.meta.json if present to inform review)
shield/commands/plan.md                     (~+5 lines — mention PRD context if found)
.claude-plugin/marketplace.json             (~1 line — version bump)
```

---

## Task 1: Scaffold prd-docs skill directory + skeletons

**Files:**
- Create: `shield/skills/general/prd-docs/SKILL.md` (skeleton)
- Create: `shield/skills/general/prd-docs/test-fixtures/` (empty)

- [ ] **Step 1.1: Create SKILL.md skeleton**

Path: `shield/skills/general/prd-docs/SKILL.md`

```markdown
---
name: prd-docs
description: Use when authoring a new PRD or upgrading a lean PRD to standard. Walks user through 17-section problem-first scaffold (or 7-section lean), pre-populates from prior /research transcript if present, invokes shield:story-coverage between Sections 4 and 6, supports custom team templates via .shield.json. Triggers on /prd, write a PRD, author a PRD.
---

# PRD Docs

Author a new PRD with the Shield 17-section problem-first scaffold (or lean variant), or upgrade an existing lean PRD to standard by adding missing sections.

## Output Path — MANDATORY

```
{output_dir}/{feature}/prd/{N}-{slug}/
├── prd.md
├── prd.html
└── prd.meta.json
```

Where `{output_dir}` comes from `.shield.json`, `{feature}` is the feature folder, `{N}` is sequential. The `prd.meta.json` records type, status, owner, last_updated, rubric_version, and `linked_plans` (auto-populated by `/plan` when it runs).

## When to Use

- User invokes `/prd` to author a new PRD
- User invokes `/prd` in a feature folder containing a lean PRD (triggers upgrade flow)

## When NOT to Use

- **Review an existing PRD** — use `/prd-review` instead
- **Generate a plan from a PRD** — use `/plan` instead
- **Capture pre-PRD context** — use `/research` instead

## Workflow

(Filled in by Task 5 — orchestration workflow + step skeleton)

## See Also

- `templates.md` — 17-section scaffold + lean variant + HTML render templates
- `meta-schema.md` — prd.meta.json schema
- `type-detection.md` — lean vs standard heuristics
- `shield:story-coverage` skill — invoked between Sections 4 and 6 for scaffolding
```

- [ ] **Step 1.2: Create test-fixtures directory**

```bash
mkdir -p shield/skills/general/prd-docs/test-fixtures
```

- [ ] **Step 1.3: Commit**

```bash
git add shield/skills/general/prd-docs/SKILL.md shield/skills/general/prd-docs/test-fixtures/
git commit -m "feat(shield): scaffold prd-docs skill"
```

---

## Task 2: Templates — 17-section scaffold + lean variant

**Files:**
- Create: `shield/skills/general/prd-docs/templates.md`

**Goal:** The authoritative templates for both PRD variants + the HTML render template.

- [ ] **Step 2.1: Write templates.md — header + standard scaffold**

Path: `shield/skills/general/prd-docs/templates.md`

```markdown
# PRD Templates

The 17-section problem-first scaffold (standard) and 7-section lean variant. Plus the HTML render template that mirrors prd.md.

## Standard scaffold (17 sections)

```markdown
# <Feature name>

## 1. Header
| Field | Value |
|---|---|
| Owner | @<handle> |
| Status | Draft |
| PRD type | Standard |
| Date created | YYYY-MM-DD |
| Last updated | YYYY-MM-DD |
| Linked design spec | <path or null> |
| Linked research | <path or null> |
| Decision-maker | @<handle> |
| Sign-off contacts | Legal: @<handle>, Security: @<handle>, Support: @<handle> |
| Linked plans | _(auto-populated by /plan)_ |

## 2. Problem & context
What's broken, who hurts, baseline data, why now (cost-of-inaction).

## 3. Target users / personas
| ID | Persona | Goals | Frictions today |
|---|---|---|---|
| P1 | <name> | <user-language goals> | <current pain> |

## 4. Goals & non-goals
### Goals
1. <goal 1>
2. <goal 2>
### Non-goals
- <explicitly NOT trying to do>

## 5. Success metrics
| Metric | Type | Target | Counter |
|---|---|---|---|
| <metric> | Leading / Lagging | <numeric threshold> | <counter-metric> |
**Dashboard plan:** <where will this be tracked>

## 6. User stories & scenarios

### Story <ID>: <name>
- **Persona:** <P-id>
- **Goal:** <user-language goal>
- **Happy path:** <numbered steps>
- **Error / timeout / abandon paths:** <branches>
- **Edge cases:** <enumeration>
- **State transitions:** <if applicable>
- **Cross-functional handoffs:** <who/when downstream teams pulled in>
- **Acceptance criteria (Given/When/Then):**
  - Given <pre>, When <action>, Then <outcome>

## 7. Functional requirements
Per-story or per-feature; uses Given/When/Then. May reference Section 6 stories.

## 8. Non-functional requirements
| NFR | Requirement |
|---|---|
| Performance | <budget> |
| Security | <auth model + threat model> |
| Accessibility | <WCAG level> |
| Privacy | <data classification + retention> |
| Telemetry / event taxonomy | <named events> |
| i18n / l10n | <RTL, encoding, formats, translation pipeline — or N/A> |

## 9. RBAC & permissions matrix
| Role | Can do |
|---|---|
| <role> | <permissions> |

## 10. Dependencies
Internal services, third parties, integration contracts.

## 11. Risks & mitigations
| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | <risk> | L/M/H | L/M/H | <mitigation> | @<handle> |

## 12. Assumptions
| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | <assumption> | Validated / Unvalidated | <consequence> |

## 13. Rollout plan
- Flag plan: <feature flag>
- Canary: <staged rollout slices>
- Kill-switch: <criteria>
- Abort thresholds: <specific metric values>
- Data migration: <plan if touching existing data>
- Backward compatibility: <commitments>

## 14. Cost & resource impact
| Component | Cost dimension | Estimate |
|---|---|---|
| Build cost | Engineering time | <estimate> |
| Run cost | LLM / compute / storage / bandwidth | <$X/month at projected scale> |
| Counter-metric | <should not exceed $Y/user/month> | |

## 15. GTM & customer-comms
- Pricing / packaging implications: <description>
- In-app messaging plan: <description>
- Release notes: <description>
- CS / sales enablement: <description>
- Beta / early-access plan: <description or N/A>

## 16. Support / CX impact
- Day-1 ticket owner: @<handle>
- Runbook: <link or description>
- Escalation path: <description>
- Sales enablement: <description>
- Training plan: <description>

## 17. Open questions
| # | Question | Owner | Target resolution |
|---|---|---|---|

## 18. Out of scope / Non-goals
- <named item with one-line rationale>
```

## Lean variant (7 sections)

```markdown
# <Feature name>

## 1. Header
(Same Header table as standard)

## 2. Problem & context
What's broken, who hurts, baseline data, why now.

## 3. Target users / personas
| ID | Persona | Goals | Frictions today |

## 4. Goals & non-goals
### Goals
### Non-goals

## 5. Success metrics
| Metric | Type | Target | Counter |

## 6. Open questions

## 7. Out of scope / Non-goals

---

> **This is a lean PRD.** It intentionally omits the following standard sections:
> - Section 6 — User stories & scenarios
> - Section 7 — Functional requirements
> - Section 8 — Non-functional requirements
> - Section 9 — RBAC & permissions matrix
> - Section 10 — Dependencies
> - Section 11 — Risks & mitigations
> - Section 12 — Assumptions
> - Section 13 — Rollout plan
> - Section 14 — Cost & resource impact
> - Section 15 — GTM & customer-comms
> - Section 16 — Support / CX impact
>
> If scope grows or stakeholders need more detail, run `/prd` again — Shield
> will offer to add specific sections or upgrade to `standard`.
```

## Story template (used inside Section 6 of standard scaffold)

```markdown
### Story <ID>: <name>
- **Persona:** <P-id>
- **Goal:** <user-language goal>
- **Happy path:** <numbered steps>
- **Error / timeout / abandon paths:** <branches>
- **Edge cases:** <enumeration>
- **State transitions:** <if applicable>
- **Cross-functional handoffs:** <who/when downstream teams pulled in>
- **Acceptance criteria (Given/When/Then):**
  - Given <pre>, When <action>, Then <outcome>
```

## HTML render template

The prd.html mirrors prd.md, rendered with Shield's standard CSS conventions:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PRD — <feature name></title>
  <style>
    /* Reuse from plan-docs CSS conventions: */
    :root {
      --accent: #1a73e8; /* Shield blue */
      --bg: #ffffff;
      --text: #1f1f1f;
    }
    body {
      max-width: 900px;
      margin: 0 auto;
      padding: 48px 24px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.6;
      color: var(--text);
      background: var(--bg);
    }
    h1, h2, h3 { color: var(--accent); }
    table { border-collapse: collapse; width: 100%; margin: 14px 0; }
    th, td { padding: 8px 12px; border-bottom: 1px solid #e0e0e0; text-align: left; }
    blockquote { border-left: 3px solid var(--accent); margin: 14px 0; padding-left: 16px; color: #555; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: "JetBrains Mono", monospace; }
  </style>
  <meta name="sidecar" content="prd.meta.json">
</head>
<body>
  <!-- Render each prd.md section here. Convert markdown to HTML via the Bash command:
       pandoc prd.md -o prd.html  (if pandoc available)
       OR manual HTML generation per section if pandoc absent. -->
</body>
</html>
```

**Implementation note:** Shield uses a markdown-to-HTML conversion approach that mirrors `plan-docs`. Reuse that helper rather than re-implementing.
```

- [ ] **Step 2.2: Commit**

```bash
git add shield/skills/general/prd-docs/templates.md
git commit -m "feat(shield): prd-docs templates (17-section standard + 7-section lean + HTML render)"
```

---

## Task 3: meta-schema.md

**Files:**
- Create: `shield/skills/general/prd-docs/meta-schema.md`

- [ ] **Step 3.1: Write meta-schema.md**

Path: `shield/skills/general/prd-docs/meta-schema.md`

```markdown
# prd.meta.json Schema

Lightweight metadata sidecar accompanying every `prd.md`. Records type, status, owner, last-updated, rubric-version, and the bidirectional linkage to plans.

## Schema (v1.0)

```json
{
  "schema_version": "1.0",
  "type": "standard | lean",
  "status": "Draft | In Review | Approved | In Implementation | Shipped | Retired",
  "owner": "@<handle>",
  "decision_maker": "@<handle>",
  "sign_off_contacts": {
    "legal": "@<handle> | null",
    "security": "@<handle> | null",
    "support": "@<handle> | null"
  },
  "date_created": "YYYY-MM-DD",
  "last_updated": "YYYY-MM-DD",
  "rubric_version": "1.0",
  "sections_present": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
  "sections_missing_from_standard": [],
  "linked_research": "research/1-some-slug/findings.md | null",
  "linked_design_spec": "<path or null>",
  "linked_plans": ["plan/1-foundation-slug/", "plan/2-rollout-slug/"]
}
```

## Field rules

- **`schema_version`**: bumped if schema changes (e.g., new field added). Current = "1.0".
- **`type`**: "standard" if all 17 sections present; "lean" if only the 7 lean sections are present. See `type-detection.md`.
- **`status`**: lifecycle stages. Default "Draft" on first write. Updated by user externally (Shield doesn't manage transitions in Phase B; future enhancement).
- **`sections_missing_from_standard`**: populated only for lean PRDs; lists which standard sections are deliberately omitted. Empty for standard.
- **`linked_plans`**: auto-appended by `/plan` when it runs against a feature folder containing a PRD. Each entry is a relative path to the plan run folder (`plan/{N}-{slug}/`).
- **`rubric_version`**: records which version of the PRD-review rubric was relevant at PRD authoring time. Read from `shield/skills/general/prd-review/rubric.md` header (add a version comment there in Phase A if missing).

## Read/Write contracts

- **Created by:** `/prd` command (Phase B) on first run; updates `last_updated` on subsequent runs in the same feature folder
- **Read by:** `/prd-review` (consumes `type`, `sections_present`, `sections_missing_from_standard` for rubric selection), `/plan` (consumes `linked_plans` to know what's already planned), `/plan-review` (consumes `sections_present` to inform plan-vs-PRD alignment review — future)
- **Appended by:** `/plan` on each run, adds an entry to `linked_plans`

## Schema evolution

When dim 14 was added in the spec, no schema change was needed (the schema stayed at v1.0). The schema only changes if a new field is added or an existing field's shape changes. Adding a new field is non-breaking; consumers ignore unknown fields. Removing or changing a field requires a `schema_version` bump.
```

- [ ] **Step 3.2: Commit**

```bash
git add shield/skills/general/prd-docs/meta-schema.md
git commit -m "feat(shield): prd-docs meta-schema (v1.0) with linked_plans bidirectional linkage"
```

---

## Task 4: type-detection.md

**Files:**
- Create: `shield/skills/general/prd-docs/type-detection.md`

- [ ] **Step 4.1: Write type-detection.md**

Path: `shield/skills/general/prd-docs/type-detection.md`

```markdown
# PRD Type Detection

How `/prd` (and `/prd-review` ingest) determines whether a PRD is `standard` or `lean`.

## Detection rules

Parse the PRD's top-level `## <N>. <section name>` headings:

1. **Lean** — only these headings present:
   - Header
   - Problem & context
   - Target users / personas
   - Goals & non-goals
   - Success metrics
   - Open questions
   - Out of scope / Non-goals

2. **Standard** — at least 12 of the 18 numbered standard sections present (sections 6 through 17 are the load-bearing standard-only sections; presence of any 4+ implies standard intent)

3. **Custom** — heading set doesn't match either pattern. Treat as standard for grading purposes; user can override.

## Override flow

After auto-detection, ALWAYS confirm with the user:

```
"This looks like a {type} PRD ({reason}). Apply {type} treatment? (yes / lean / standard)"
```

User can override. Override is recorded in `prd.meta.json.type`.

## Edge cases

- **Empty PRD** (just header): treated as in-progress; type defaults to standard
- **Lean PRD with one extra section** (e.g., Risks added): treated as still lean structurally but flag that it's drifting; user can override
- **Standard PRD missing a section** (e.g., GTM section omitted): treated as standard, missing-section flagged by `/prd-review` rubric
- **Heading variations** (e.g., "## 1. Header" vs "## Header"): normalize by stripping leading numbering before matching
```

- [ ] **Step 4.2: Commit**

```bash
git add shield/skills/general/prd-docs/type-detection.md
git commit -m "feat(shield): prd-docs type-detection (lean vs standard with override flow)"
```

---

## Task 5: prd-docs SKILL.md — orchestration workflow

**Files:**
- Modify: `shield/skills/general/prd-docs/SKILL.md` (fill in `## Workflow` placeholder from Task 1)

- [ ] **Step 5.1: Replace Workflow section**

Open `shield/skills/general/prd-docs/SKILL.md`. Replace the line `(Filled in by Task 5 — orchestration workflow + step skeleton)` with:

```markdown
## Step Skeleton

| Step | Action | Condition | Mandatory |
|---|---|---|---|
| 1 | Read `.shield.json` for `prd_template`, `prd_required_sections` | always | Yes |
| 2 | Resolve feature folder context (`--feature`, current feature, or prompt) | always | Yes |
| 3 | Check for prior PRD in feature folder (lean → trigger upgrade flow) | only if prior PRD exists | conditional |
| 4 | Ask user for PRD type (standard | lean) | always | Yes |
| 5 | Check for prior `/research` transcript; pre-populate Problem/Users/Constraints if present | only if research exists | conditional |
| 6 | Walk Sections 1-4 (Header, Problem, Personas, Goals) | always | Yes |
| 7 | Invoke `shield:story-coverage` skill between Sections 4 and 6; scaffold expected stories | always (standard only; skip for lean) | conditional |
| 8 | Walk Sections 5, 6 content, 7-17 | always (lean: only 5, 16, 17) | Yes |
| 9 | Apply custom-template merging if `.shield.json.prd_template` is set | only if config set | conditional |
| 10 | Write `prd.md`, `prd.html`, `prd.meta.json` | always | Yes |
| 11 | Update manifest, regenerate index.html | always | Yes |

## Workflow

### 1. Configuration

Read `.shield.json`:
- `output_dir` (default `docs/shield`)
- `prd_template` (default null — use built-in scaffold from `templates.md`)
- `prd_required_sections` (default: ["Problem", "Goals & non-goals", "Success metrics", "Out of scope", "Open questions"] — see spec)

### 2. Feature context

Determine which feature folder this PRD belongs to:
- If `--feature <name>` flag passed → use that
- Else look at current working directory hint (recent activity) and ask user to confirm
- If no prior feature folders exist → create one with today's date

### 3. Detect prior lean PRD (upgrade flow)

Glob `{output_dir}/{feature}/prd/*/prd.meta.json`. If any have `type: "lean"`:

Offer the user a multi-select:

```
I found a lean PRD in this feature folder. What would you like to do?

  [ ] Add sections (a new run is created with your existing content + new sections)
       [x] Section 6 — User stories & scenarios
       [x] Section 7 — Functional requirements
       [x] Section 8 — Non-functional requirements
       [x] Section 9 — RBAC & permissions matrix
       [x] Section 10 — Dependencies
       [x] Section 11 — Risks & mitigations
       [x] Section 12 — Assumptions
       [x] Section 13 — Rollout plan
       [x] Section 14 — Cost & resource impact
       [x] Section 15 — GTM & customer-comms
       [x] Section 16 — Support / CX impact

  ( ) Start fresh — new run, blank slate
  ( ) Cancel
```

If user picks "Add sections":
- Create new run folder `prd/{N+1}-{slug}/`
- Copy existing lean content forward
- Walk the user through the chosen new sections only

If "Start fresh" or no prior lean PRD detected, proceed to Step 4.

### 4. PRD type prompt

```
Which PRD type would you like?
1. Standard — full 17-section scaffold (recommended for substantial features)
2. Lean — 7-section variant (good for 1-pagers, small features, "stop me if this is wrong" docs)
```

Record user choice. Type is per-invocation; not stored in `.shield.json`.

### 5. Pre-populate from prior research

Look for `{output_dir}/{feature}/research/*/transcript.md` (Phase C, falls back to `findings.md` if Phase C not yet shipped). If found:
- Read it
- Extract Problem context, Target Users (personas), Constraints (Existing systems / compliance markers)
- Pre-populate the corresponding sections in the PRD draft
- Tell user: "I pre-populated Sections 2 (Problem), 3 (Personas), 10 (Dependencies) from your research transcript. Confirm or edit before we continue."

### 6. Walk Sections 1-4

For each of Sections 1, 2, 3, 4: present the template fields and ask the user for content. Skip pre-populated fields unless user wants to edit.

### 7. Story coverage scaffolding (standard only)

Once Sections 3 (Personas) and 4 (Goals) are captured, invoke `shield:story-coverage` skill with:
- `personas`: from Section 3
- `goals`: from Section 4
- `feature_domain`: inferred (see story-coverage SKILL.md "Domain detection")

The skill returns `expected_stories[]`. Present them to the user with multi-select:

```
For coverage of your personas and goals, you'll likely want these stories:

  [x] P1-S1 — Anika resets her password (persona-goal: P1 + G1, severity P0)
  [x] P1-S2 — Anika handles login lockout (archetype: account-recovery, severity P1)
  [x] P2-S1 — Rohan changes his email (archetype: email-change, severity P2)

Pick which to scaffold (defaults to all suggested), or add your own.
```

Selected stories are seeded into Section 6 with the standard story template structure (blank for the user to fill).

### 8. Walk remaining sections

Walk Sections 5, then Section 6 (filling in content for the scaffolded stories), then 7-17 in order.

For lean PRDs, only walk Sections 5, 16 (Open Questions), 17 (Out of Scope) — skip 6-15 entirely.

### 9. Custom-template merging

If `.shield.json.prd_template` is set:
- Read the custom template file
- Parse its top-level `##` headings
- Compare against `prd_required_sections`
- For any required section MISSING in the custom template, APPEND it to the end with a marker:
  ```markdown
  ## Required section — added by Shield
  <!-- Shield: added required section -->
  (Author content here)
  ```
- Report to user: "Your template was missing: <list>. I appended them at the end."
- Walk the user through filling content for any sections they hadn't yet filled

### 10. Write artifacts

- Write `{output_dir}/{feature}/prd/{N}-{slug}/prd.md`
- Render and write `{output_dir}/{feature}/prd/{N}-{slug}/prd.html` (using HTML template from `templates.md`)
- Write `{output_dir}/{feature}/prd/{N}-{slug}/prd.meta.json` (per `meta-schema.md`)

### 11. Update dashboard

- Append new entry to `{output_dir}/manifest.json`
- Regenerate `{output_dir}/index.html`

### 12. Offer next steps

```
PRD authored. What's next?

- /prd-review prd/{N}-{slug}/prd.md   — review for gaps
- /plan                                — generate a technical plan from this PRD
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing prd.md without prd.meta.json | Both are mandatory; meta.json holds the type + linked_plans for downstream commands |
| Skipping story-coverage scaffolding for standard PRDs | Required step for standard; skipping leads to poor dim 4 grades downstream |
| Walking lean PRD through all 17 sections | Lean is intentionally 7 sections; walk only those |
| Forgetting custom-template required-section merging | Custom templates MUST have all required sections; Shield appends missing ones with markers |
| Auto-detecting type without confirming with user | Type detection is best-effort; ALWAYS confirm with user |
| Writing to a path other than {output_dir}/{feature}/prd/{N}-{slug}/ | This is the only valid output path |
```

- [ ] **Step 5.2: Commit**

```bash
git add shield/skills/general/prd-docs/SKILL.md
git commit -m "feat(shield): prd-docs orchestration workflow + step skeleton"
```

---

## Task 6: /prd command

**Files:**
- Create: `shield/commands/prd.md`

- [ ] **Step 6.1: Write commands/prd.md**

Path: `shield/commands/prd.md`

```markdown
---
allowed-tools: Read, Write, Bash, Agent, Glob, Grep
description: Author a new PRD with Shield's 17-section problem-first scaffold (or 7-section lean variant). Supports custom team templates, lean→standard upgrade flow, and consumes prior /research transcripts as pre-population.
---

# /prd

Author a PRD interactively. Walks the user through the scaffold; invokes `shield:story-coverage` for story scaffolding; writes `prd.md`, `prd.html`, `prd.meta.json`.

## Usage

```
/prd                          # interactive — prompts for everything
/prd <topic>                  # uses topic as seed for Problem / feature name
/prd --feature <name>         # explicit feature folder
```

## What it does

1. **Reads `.shield.json`** for `prd_template` (custom team template path, optional)
2. **Resolves feature folder** — `--feature` flag or current context
3. **Detects prior lean PRD** in the folder — if present, offers upgrade flow (multi-select of standard sections to add)
4. **Asks for PRD type** — standard (17 sections) or lean (7 sections)
5. **Pre-populates from prior `/research` transcript** if present
6. **Walks Sections 1-4** (Header, Problem, Personas, Goals)
7. **Invokes `shield:story-coverage`** between Sections 4 and 6 — scaffolds expected stories (persona × goal + archetypal flows) for user confirmation/skip
8. **Walks remaining sections** (5, 6 content, 7-17 for standard; 5, 16, 17 for lean)
9. **Merges custom template** if configured — appends missing required sections with `<!-- Shield: added required section -->` markers
10. **Writes** `prd.md`, `prd.html` (rendered via Shield's standard CSS), `prd.meta.json` (with linked_plans field — auto-populated by `/plan` later)

## Output

```
{output_dir}/{feature}/prd/{N}-{slug}/
├── prd.md
├── prd.html
└── prd.meta.json
```

## Reference

Full behavior in `shield/skills/general/prd-docs/SKILL.md`.

## See also

- `/prd-review` — multi-persona gap review on this PRD
- `/plan` — generate technical breakdown from this PRD
- `/research` — capture product+tech context before authoring
```

- [ ] **Step 6.2: Commit**

```bash
git add shield/commands/prd.md
git commit -m "feat(shield): /prd command (Phase B)"
```

---

## Task 7: Test fixtures

**Files:**
- Create: `shield/skills/general/prd-docs/test-fixtures/new-from-scratch-expected.md`
- Create: `shield/skills/general/prd-docs/test-fixtures/with-research-transcript.md`
- Create: `shield/skills/general/prd-docs/test-fixtures/with-research-transcript-expected.md`
- Create: `shield/skills/general/prd-docs/test-fixtures/lean-upgrade-prior-prd.md`

**Goal:** Validate the three primary authoring scenarios.

- [ ] **Step 7.1: `new-from-scratch-expected.md`** — full standard PRD output for a hypothetical feature ("Add gift-card support")

Use the standard scaffold from `templates.md` filled in completely with realistic content (~250 lines). Reference the existing PRD at `docs/superpowers/specs/2026-05-11-prd-and-research-redesign-prd.md` for style.

Trailing comment:

```markdown
<!--
EXPECTED OUTPUT for `/prd "Add gift-card support"` (no prior research, no custom template, type=standard):
  Sections 1-17 + 18 (out of scope) all filled
  Section 6 has 3 stories matching story-coverage scaffolding for payment domain
  Sections 9 (RBAC), 14 (Cost), 15 (GTM), 16 (Support) all have content (not N/A)
-->
```

- [ ] **Step 7.2: `with-research-transcript.md`** — example research transcript for "Add gift-card support"

Simulates a research transcript covering Problem (gift-card market), Users (P1: gift recipients, P2: gift senders), Constraints (PCI-DSS for gift-card data). ~80 lines.

- [ ] **Step 7.3: `with-research-transcript-expected.md`** — expected PRD output when /prd consumes the transcript

Same as 7.1 but Sections 2, 3, 10 are pre-populated from the transcript with `<!-- pre-populated from research -->` markers. ~300 lines.

- [ ] **Step 7.4: `lean-upgrade-prior-prd.md`** — minimal lean PRD that triggers upgrade flow

```markdown
# Lean PRD — Add gift-card support

## 1. Header
| Field | Value |
| Owner | @pm-name |
| Status | Draft |
| PRD type | Lean |
| Date created | 2026-04-15 |

## 2. Problem & context
Customers want to send gift cards to friends.

## 3. Target users
P1: gift recipients · P2: gift senders

## 4. Goals
1. Customers can buy + send gift cards to other users
2. Recipients can redeem gift-card balance against purchases

## 5. Success metrics
Gift cards sold / month: target 1000 in first 90 days.

## 6. Open questions
- Maximum gift-card value?
- Expiration policy?

## 7. Out of scope
- Physical gift cards
- Gift cards purchased outside the app

<!--
EXPECTED: When /prd runs in the same feature folder, offer multi-select to add Sections 6-15.
-->
```

- [ ] **Step 7.5: Commit fixtures**

```bash
git add shield/skills/general/prd-docs/test-fixtures/
git commit -m "test(shield): prd-docs test fixtures (3 scenarios)"
```

---

## Task 8: RED test — baseline without skill

For each test fixture, run `/prd` interactively (simulated) WITHOUT the prd-docs skill loaded. Document baseline behavior.

- [ ] **Step 8.1: Baseline — author from scratch**

Without the prd-docs skill, Shield doesn't know about the 17-section scaffold. A generic LLM prompt to author a PRD will produce inconsistent structure. Document this baseline.

- [ ] **Step 8.2: Baseline — with research transcript**

Without the skill, no pre-population from `/research/transcript.md`. Document baseline.

- [ ] **Step 8.3: Baseline — lean upgrade**

Without the skill, no detection of prior lean PRD. Document baseline.

- [ ] **Step 8.4: Record baselines**

Save to `shield/skills/general/prd-docs/test-fixtures/RED-baseline.md` (temporary).

```bash
git add shield/skills/general/prd-docs/test-fixtures/RED-baseline.md
git commit -m "test(shield): prd-docs RED baseline"
```

---

## Task 9: GREEN test — with skill loaded

- [ ] **Step 9.1: Run `/prd` end-to-end against each fixture scenario**

For each:
- Author from scratch — verify the output matches `new-from-scratch-expected.md` structure
- With research — verify Sections 2, 3, 10 pre-populated correctly
- Lean upgrade — verify multi-select offered, original lean preserved, new run created

- [ ] **Step 9.2: Verify `prd.meta.json` schema**

```bash
cat docs/shield/<feature>/prd/1-<slug>/prd.meta.json | jq .
```

Verify required fields: `schema_version`, `type`, `status`, `owner`, `date_created`, `last_updated`, `rubric_version`, `sections_present`, `linked_plans`.

- [ ] **Step 9.3: Verify HTML render**

```bash
ls -la docs/shield/<feature>/prd/1-<slug>/prd.html
# Open in browser; verify Shield blue accent, max-width, semantic structure
```

- [ ] **Step 9.4: Iterate if gaps**

Common gaps to fix:
- Custom-template merging clobbers user content → must append only at end, not mid-section
- Story-coverage skill not invoked → check Step 7 in SKILL.md workflow
- HTML render missing sections → templates.md needs more complete render template

- [ ] **Step 9.5: Cleanup + commit**

```bash
rm shield/skills/general/prd-docs/test-fixtures/RED-baseline.md
git add shield/skills/general/prd-docs/
git commit -m "test(shield): prd-docs GREEN — author flow + pre-population + upgrade verified"
```

---

## Task 10: Update plan-docs to consume prd.md as context

**Files:**
- Modify: `shield/skills/general/plan-docs/SKILL.md`
- Modify: `shield/commands/plan.md` (optional — small mention)

**Goal:** When `/plan` runs in a feature folder containing a PRD, read it as context and record `source_prd` + `prd_rubric_version_at_planning` in `plan.json`.

- [ ] **Step 10.1: Read current plan-docs SKILL.md**

```bash
cat shield/skills/general/plan-docs/SKILL.md | head -100
```

- [ ] **Step 10.2: Add a workflow step for PRD context**

Append to plan-docs SKILL.md workflow (in the right ordering, after configuration step):

```markdown
### Step N: Detect prior PRD in feature folder

Glob `{output_dir}/{feature}/prd/*/prd.md` to find any prior PRDs. If multiple exist, pick the most recent (highest `{N}`).

If found:
- Read the PRD content
- Read its `prd.meta.json` for type, sections_present, status
- Treat the PRD as authoritative context for: Problem, Users, Goals, Stories, NFRs, Risks
- Append the plan's run folder path to `prd.meta.json.linked_plans` (auto-updates the bidirectional linkage)
- Record `source_prd` and `prd_rubric_version_at_planning` (read from prd.meta.json.rubric_version) into the plan.json sidecar
```

- [ ] **Step 10.3: Update plan.md command** (optional)

If wanted, add a note to `shield/commands/plan.md`:
> "If a PRD exists in the feature folder, `/plan` reads it as context."

- [ ] **Step 10.4: Commit**

```bash
git add shield/skills/general/plan-docs/SKILL.md shield/commands/plan.md
git commit -m "feat(shield): plan-docs reads prior PRD as context; records bidirectional linkage"
```

---

## Task 11: Update plan-review to consume prd.meta.json

**Files:**
- Modify: `shield/skills/general/plan-review/SKILL.md`

**Goal:** When `/plan-review` runs, if a prd.meta.json exists in the feature folder, read it to inform the review.

- [ ] **Step 11.1: Add a workflow step to plan-review SKILL.md**

```markdown
### Step N: Detect prior PRD

If `{output_dir}/{feature}/prd/*/prd.meta.json` exists, read the latest one. Use its `sections_present` and `type` to inform the plan-vs-PRD alignment check (future enhancement; for now, just record it in plan-review/summary.md as "Source PRD: <path>" header).
```

- [ ] **Step 11.2: Commit**

```bash
git add shield/skills/general/plan-review/SKILL.md
git commit -m "feat(shield): plan-review aware of prd.meta.json (informational)"
```

---

## Task 12: End-to-end integration test

- [ ] **Step 12.1: Author a new standard PRD via /prd**

```
/prd "Add gift-card support"
```

Walk through the full flow. Verify story-coverage scaffolds 3+ stories from payment archetypes.

- [ ] **Step 12.2: Run /prd-review against the freshly-authored PRD**

```
/prd-review docs/shield/<feature>/prd/1-<slug>/prd.md
```

Verify Phase A `/prd-review` works on Phase B output. Confirm verdict + persona grades + artifact paths.

- [ ] **Step 12.3: Run /plan against the same feature folder**

```
/plan
```

Verify `/plan` detects the PRD, uses it as context, records `source_prd` in plan.json, and appends to prd.meta.json.linked_plans.

- [ ] **Step 12.4: Verify bidirectional linkage**

```bash
cat docs/shield/<feature>/prd/1-<slug>/prd.meta.json | jq .linked_plans
cat docs/shield/<feature>/plan.json | jq .source_prd
```

Both should be populated and reference each other.

- [ ] **Step 12.5: Commit integration baseline**

```bash
mkdir -p shield/skills/general/prd-docs/test-fixtures/integration/
cp -r docs/shield/<feature>/ shield/skills/general/prd-docs/test-fixtures/integration/full-flow-baseline/
git add shield/skills/general/prd-docs/test-fixtures/integration/
git commit -m "test(shield): integration baseline — /prd → /prd-review → /plan with linkage"
```

---

## Task 13: Marketplace version bump

- [ ] **Step 13.1: Bump shield version**

Edit `.claude-plugin/marketplace.json`:

```diff
- "version": "2.12.0",
+ "version": "2.13.0",
```

- [ ] **Step 13.2: Commit + push**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.13.0 — Phase B /prd command"
git push
```

---

## Spec → plan coverage check

| Spec requirement | Implemented in task |
|---|---|
| 17-section problem-first scaffold | Task 2 (templates.md) |
| Lean variant (7 sections) | Task 2 (templates.md) |
| Story template structure | Task 2 (templates.md) |
| PRD-type prompt at generation time | Task 5 Step 4 |
| Pre-population from prior `/research` | Task 5 Step 5 |
| Story-coverage scaffolding (consumes Phase A skill) | Task 5 Step 7 |
| Custom-template merging | Task 5 Step 9 |
| Lean → standard upgrade flow (multi-select) | Task 5 Step 3 |
| HTML rendering | Task 2 (templates.md HTML section) |
| prd.meta.json with linked_plans | Tasks 3, 10 |
| PRD-to-Plan bidirectional linkage | Tasks 10 (prd → plan), 11 (plan-review aware) |
| `/prd` command | Task 6 |
| Test fixtures + RED-GREEN validation | Tasks 7, 8, 9 |
| Integration test | Task 12 |
| Version bump | Task 13 |

This plan is Phase B only. Phase C tracked separately.
