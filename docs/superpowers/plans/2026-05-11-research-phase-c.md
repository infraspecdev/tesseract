# `/research` Phase 1 Enhancement — Phase C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Extend the existing `/research` command with **Phase 1** — a structured Q&A walk with silent repo auto-detection. The existing PM-framed external evidence-gathering becomes **Phase 2**, opt-in after Phase 1.

**Architecture:** Light extension of the existing `research` skill. Two new supporting docs (`repo-scan.md`, `qa-topics.md`); main `SKILL.md` updated to add Phase 1 before the existing workflow. Phase 2 (3 parallel research agents + citations) is preserved unchanged.

**Tech Stack:** Markdown skill content. No new Python code. Repo scan reuses Shield's existing domain-detection logic from `/plan` (CLAUDE.md domain markers like `package.json`, `pom.xml`, `pyproject.toml`, etc.).

**Phase A and B prerequisite:** Phase C is purely additive on top of `/research`; doesn't depend on Phases A and B technically. However, the value of Phase 1 enhancement is highest when feeding into `/prd` (Phase B) and `/prd-review` (Phase A). Ship after both.

---

## Spec reference

This plan implements **Phase C** of `docs/superpowers/specs/2026-05-09-prd-and-research-redesign-design.md`. Read the spec's "`/research` Phase 1" + "Repo-scan and transcript format" sections first.

## Scope of this plan (Phase C only)

**In scope:**
- Update `shield/skills/general/research/SKILL.md` — describe two-phase flow, Phase 1 workflow, Phase 2 invocation
- New: `shield/skills/general/research/repo-scan.md` — what to detect, how, what counts as confirmed vs corrected vs manual
- New: `shield/skills/general/research/qa-topics.md` — product + tech topic catalog with skip rules
- Update `shield/commands/research.md` to reflect two-phase behavior
- Test fixtures: 2 repos at `shield/skills/general/research/test-fixtures/` (small-node-app, minimal-repo)
- RED-GREEN validation
- Marketplace version bump (shield 2.13.0 → 2.14.0, assuming Phase B shipped 2.13.0)

**Out of scope:**
- Replacing Phase 2 (existing external evidence-gathering) — preserved entirely
- Phase 1 Q&A topic customization via `.shield.json` (uses built-in catalog only in Phase C)
- Context federation beyond repo scan (e.g., Confluence/Jira/Datadog MCPs) — future enhancement

**Dependencies:**
- Existing research skill at `shield/skills/general/research/`
- Domain-detection patterns from CLAUDE.md (package manifests, etc.)

---

## File structure

**New files:**

```
shield/skills/general/research/
├── repo-scan.md                    (~150 lines — detection rules per category)
├── qa-topics.md                    (~150 lines — product + tech topic catalog with skip rules)
└── test-fixtures/
    ├── small-node-app/             (test fixture — a minimal Node + TS + Postgres repo)
    │   ├── package.json
    │   ├── docker-compose.yml
    │   ├── CLAUDE.md
    │   └── .github/workflows/deploy.yml
    └── minimal-repo/               (test fixture — no manifests, just a README)
        └── README.md
```

**Modified files:**

```
shield/skills/general/research/SKILL.md     (~+100 lines — Phase 1 + Phase 2 sections)
shield/commands/research.md                 (~+15 lines — reflect two-phase behavior)
.claude-plugin/marketplace.json             (~1 line — version bump)
```

---

## Task 1: repo-scan.md

**Files:**
- Create: `shield/skills/general/research/repo-scan.md`

**Goal:** Define what Shield scans, where it looks, and how it tags each finding.

- [ ] **Step 1.1: Write repo-scan.md**

Path: `shield/skills/general/research/repo-scan.md`

```markdown
# Research Phase 1 — Repo Scan

Silent scan of the current repository to detect technical context before asking the user any questions. Findings surfaced for user confirmation/correction.

## Confidence tags

Each detected entry is tagged with a marker:

| Tag | Meaning |
|---|---|
| `(detected)` | Shield inferred from the repo; user has not confirmed or corrected |
| `(confirmed)` | Shield detected AND user said "yes" during confirmation step |
| `(corrected by user)` | Shield's initial guess was wrong; this is the user's correction |
| `(manual)` | User added during the confirmation step; Shield did not detect |

## Categories scanned

### Stack

Detection by file presence in the repo root or `src/` directory:

| File | Inferred stack |
|---|---|
| `package.json` (no Python markers nearby) | Node + JavaScript or TypeScript |
| `tsconfig.json` alongside `package.json` | Node + TypeScript |
| `pom.xml` | Java + Maven |
| `build.gradle` or `build.gradle.kts` | Java/Kotlin + Gradle |
| `pyproject.toml` | Python (poetry / hatch / similar) |
| `requirements.txt` (no pyproject) | Python (pip) |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `*.csproj` or `*.fsproj` | .NET |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `mix.exs` | Elixir |

Report each as: `<Stack> (detected) — *from <file>*`.

### Integrations

Detection by package dependencies + config files:

| Source | Inferred integration |
|---|---|
| `node_modules` or `package.json` deps containing `passport-*`, `auth0`, `firebase-admin` | Auth provider |
| Deps containing `@stripe/*`, `paypal-*` | Payment provider |
| Deps containing `pg`, `mysql2`, `mongodb`, `redis` | Datastore |
| Deps containing `bull`, `kafkajs`, `amqplib` | Message queue |
| Deps containing `@aws-sdk/*`, `gcp-*`, `azure-*` | Cloud provider |
| `docker-compose.yml` services | Runtime services (Postgres, Redis, etc.) |
| `helm/values.yaml` or `kustomization.yaml` | K8s deployment |
| `.env.example` keys mentioning auth/secret names | Inferred auth integrations |

Report as: `<Integration name> (detected) — *from <source>*`.

### Compliance markers

Search `CLAUDE.md`, `README.md`, `SECURITY.md`, `docs/` for these terms (case-insensitive):

| Keyword | Inferred compliance |
|---|---|
| `SOC2` | SOC 2 |
| `GDPR` | GDPR |
| `CCPA` | CCPA |
| `HIPAA` | HIPAA |
| `PCI-DSS` or `PCI DSS` | PCI-DSS |
| `RBI` | RBI (India payment regulation) |
| `DPDP` | DPDP (India data protection) |
| `PDPL` | PDPL (UAE / Saudi data protection) |

Report each as: `<Compliance> (detected) — *mentioned in <file>*`.

### Deployment / rollout pattern

| Source | Inferred pattern |
|---|---|
| `.github/workflows/deploy.yml` containing `canary`, `blue-green`, `rolling` | Inferred deployment strategy |
| `helm/values.yaml` containing canary stanza | Canary rollout |
| `argo-cd-app.yaml` or `Application.yaml` | ArgoCD |
| `.github/workflows/*.yml` with `terraform plan` | Terraform / Atmos |

Report as: `<Pattern> (detected) — *from <workflow file>*`.

### Recent activity

```bash
# Last 20 commits in touched paths
git log --oneline -20 --name-only | head -50
```

From this output, surface:
- Most recently touched directories
- Most active contributors (by commit count) in the inferred feature area

Report as: `<dir>: <N> commits last 30 days, mostly @<user> (confirmed) — *git log*`.

### Past decisions / ADRs

Glob `docs/decisions/*.md`, `docs/adr/*.md`, `**/ADR-*.md`. For each, surface:
- ADR number
- Title
- One-line summary

Report as: `ADR-001: <title> — <one-line>`.

### Prior Shield artifacts

Glob `{output_dir}/{feature}/research/*/transcript.md` and `{output_dir}/{feature}/research/*/findings.md`. If any exist:
- Note that prior research has been done
- Read the most recent transcript to carry forward context

## Output format in transcript.md

Render as a `## Detected Context` section at the top of `transcript.md`:

```markdown
## Detected Context

### Stack
- Node.js + TypeScript (confirmed) — *from package.json + tsconfig.json*
- PostgreSQL (confirmed) — *from docker-compose.yml services*

### Integrations
- passport-google-oauth20 (confirmed) — *existing OAuth provider in package.json*
- Redis (detected) — *Redis service in docker-compose.yml*

### Compliance markers
- SOC2 (confirmed) — *mentioned in CLAUDE.md*
- GDPR (corrected by user) — *Shield missed; user added "EU users in scope"*

### Deployment pattern
- Helm + ArgoCD (confirmed) — *helm/ + .github/workflows/argo-sync.yml*
- Canary rollout (confirmed) — *helm/values.yaml has canary stanza*

### Recent activity
- src/auth/: 8 commits last 30 days, mostly @ashwinimanoj (confirmed) — *git log*

### Past decisions / ADRs
- ADR-001: Use Postgres for transactional data (2025-09-12)
- ADR-002: Adopt strangler pattern for v2 migration (2026-01-15)

### Prior Shield artifacts
- Prior research transcript at research/1-platform-foundations/transcript.md (2026-04-30)
```

## Performance budget

Scan must complete in ≤ 30 seconds for a typical repo. If scan exceeds 30s, skip lower-priority categories (Past decisions, Prior artifacts) and proceed with confirmed Stack + Integrations only.

## Failure modes

- **Empty repo / no manifests** — emit `## Detected Context` with the note "No technical context detected; proceeding with manual Q&A only."
- **Permission errors reading files** — skip that file silently; continue with others
- **Git not available** — skip Recent activity category
```

- [ ] **Step 1.2: Commit**

```bash
git add shield/skills/general/research/repo-scan.md
git commit -m "feat(shield): research repo-scan rules (Stack, Integrations, Compliance, Deployment, Activity, ADRs, Prior artifacts)"
```

---

## Task 2: qa-topics.md

**Files:**
- Create: `shield/skills/general/research/qa-topics.md`

**Goal:** The product + tech Q&A topic catalog with depth modes and skip rules.

- [ ] **Step 2.1: Write qa-topics.md**

Path: `shield/skills/general/research/qa-topics.md`

```markdown
# Research Phase 1 — Q&A Topic Catalog

The structured Q&A walk after repo scan. Topics are grouped by product / tech, ordered, and skip rules are explicit.

## Depth modes (configurable via `.shield.json` `research_depth`)

| Mode | Topics asked | Use when |
|---|---|---|
| `lean` | Required only — Problem, Users, Success criteria, Existing systems, Constraints | Small feature / bug fix / "stop me if this is wrong" |
| `standard` (default) | Required + Evidence, Alternatives, Integration points, Technical risks | Substantial feature |
| `deep` | Standard + Hypotheses, Migration plan, Detailed risks, Cross-functional handoffs | Compliance / migration / enterprise feature |

Auto-suggest at start:
- `lean` if topic mentions "small", "bug", "fix"
- `deep` if topic mentions "compliance", "migration", "enterprise", "regulatory"
- Else `standard`

User can override.

## Product topics

| Order | Topic | Required? | Skip rule | Example question |
|---|---|---|---|---|
| 1 | **Problem** | Yes | Skip if already answered in user's initial topic message OR in prior research | "What's the user problem driving this? Pick or describe..." |
| 2 | **Users** | Yes | Skip if persona named in topic message | "Which user segment is most affected — and roughly how many?" |
| 3 | **Evidence** | Standard+ | Skip if Problem answer cites data | "What's the strongest evidence the problem is real?" |
| 4 | **Alternatives** | Standard+ | Skip if topic explicitly excludes alternatives | "How are users coping today, and what other solutions have been considered?" |
| 5 | **Success criteria** | Yes | Never skip | "What metric will tell us this worked, and what's a credible target?" |
| 6 | **Why now** | Standard+ | Skip if obvious from Problem (regulatory deadline, etc.) | "Is there a reason to do this now vs. wait 6 months?" |
| 7 | **Hypotheses** | Deep | Always asked in deep mode | "What do you believe will be true if we ship this?" |

## Tech topics

| Order | Topic | Required? | Skip rule | Example question |
|---|---|---|---|---|
| 8 | **Existing systems** | Yes | Skip if repo scan auto-filled this | "What authentication / data / queue layers exist today? (mostly auto-filled from repo scan)" |
| 9 | **Constraints** | Yes | Skip if repo scan detected compliance markers | "Any hard constraints — compliance, deployment, regulatory, performance?" |
| 10 | **Integration points** | Standard+ | Skip if topic is greenfield with no existing integrations | "Which existing systems will this feature touch?" |
| 11 | **Technical risks** | Standard+ | Skip if topic is trivial | "What technical risks should we be aware of?" |
| 12 | **Migration plan** | Deep | Skip if greenfield | "If touching existing data, what's the migration approach?" |
| 13 | **Cross-functional handoffs** | Deep | Always asked in deep mode | "Which other teams (CS, Finance, Legal, Security) will be pulled in?" |
| 14 | **Open technical questions** | Yes | Never skip — surface as catch-all | "What technical questions are you unsure about?" |

## Skip rule mechanics

For each topic, before asking:
1. Check if user's initial invocation message answers it (regex / keyword match)
2. Check if repo scan auto-filled it
3. Check if a prior research transcript already covered it
4. If covered → mark as auto-filled, surface "✓ <Topic> (from <source>): <answer>"
5. If partially covered → ask only the missing piece
6. If unanswered → ask the full question

## "Skip" / "I don't know" handling

The user can reply `skip` or `i don't know` to any question:
- Shield records `[unanswered]` for that field
- Surfaces it as an Open Question in the transcript's `## Open Questions` section
- Does NOT block progression

## Final transcript structure

```markdown
## Product Context
### Problem
<answer>
### Users
<answer>
### Evidence
<answer or [unanswered]>
...

## Technical Context
### Existing systems
<auto-filled from Detected Context — confirmed entries>
### Constraints
<answer + compliance markers from Detected Context>
...

## Open Questions
- <unanswered topic 1>
- <unanswered topic 2>
- ...

## External Findings (Phase 2)
<populated only if Phase 2 ran>
```

## Phase 2 trigger criteria

After Phase 1 completes, Shield surfaces unanswered + technical questions and offers Phase 2:

```
Phase 1 captured your context. These open questions would benefit from external evidence:
- <question 1>
- <question 2>

Run external evidence-gathering on these? (yes / no / pick specific)
```

If yes, run the existing PM-framing + 3-agent flow on the chosen questions only. Output appended as `## External Findings` in `transcript.md`, and `findings.md` written alongside.
```

- [ ] **Step 2.2: Commit**

```bash
git add shield/skills/general/research/qa-topics.md
git commit -m "feat(shield): research qa-topics catalog (product + tech) with depth modes + skip rules"
```

---

## Task 3: Update research SKILL.md for two-phase flow

**Files:**
- Modify: `shield/skills/general/research/SKILL.md`

**Goal:** Restructure the workflow into Phase 1 (new) + Phase 2 (existing).

- [ ] **Step 3.1: Read current research SKILL.md to find the right insertion point**

```bash
cat shield/skills/general/research/SKILL.md | head -80
```

Identify the current workflow section (likely titled `## Workflow` or `## Step Skeleton`).

- [ ] **Step 3.2: Update the SKILL.md description (frontmatter)**

```diff
- description: Use when comparing approaches, evaluating tools, building evidence-based decisions, or the user needs citations and industry backing. Triggers on /research, investigate, compare, evaluate.
+ description: Use when starting work on a new feature — gathers product + tech context via Q&A walk (Phase 1) with repo auto-detection, then optionally runs external evidence-gathering with citations (Phase 2). Triggers on /research, investigate, compare, evaluate.
```

- [ ] **Step 3.3: Add Phase 1 section to workflow**

Insert before the existing Phase 2 (which is the current workflow):

```markdown
## Workflow

### Phase 1 — Structured Q&A with repo auto-detection (Phase C addition)

#### Step 1: Repo scan (silent)

See `repo-scan.md`. Scan in background. Categories: Stack, Integrations, Compliance markers, Deployment pattern, Recent activity, Past decisions / ADRs, Prior Shield artifacts. Performance budget ≤ 30s; degrade gracefully on large repos.

#### Step 2: Surface detected context + confirm with user

Display the `## Detected Context` block to the user. Prompt:

> "I scanned your repo and found: <summary>. Confirm or correct before I ask the rest?"

Update tags based on user feedback: `(detected)` → `(confirmed)` if user says yes; `(corrected by user)` if user pushes back with a different value; `(manual)` if user adds something Shield missed.

#### Step 3: Q&A walk

See `qa-topics.md` for the topic catalog, depth modes, and skip rules. Walk topics in order, asking only what's not auto-answered.

Skip handling: `skip` or `I don't know` → record `[unanswered]`, surface in Open Questions section.

#### Step 4: Surface unanswered + offer Phase 2

After Phase 1 completes:

```
Phase 1 captured your context. These open questions would benefit from external evidence-gathering:
- <question 1>
- <question 2>

Run Phase 2 (external research)? (yes / no / pick specific)
```

If user says yes or picks specific questions, proceed to Phase 2 (Step 5+). If no, write transcript.md and finish.

### Phase 2 — External evidence-gathering (existing behavior preserved)

#### Step 5: PM framing on the chosen questions

(Existing PM-framing logic. Dispatches `shield:product-manager-reviewer` in research-framing mode.)

#### Step 6: Three parallel research agents

(Existing 3-agent flow: official sources, industry voices, community experience. Each agent runs with the PM framing context.)

#### Step 7: Synthesize findings

(Existing synthesis logic.)

#### Step 8: PM review on findings

(Existing PM-review mode.)

#### Step 9: Write findings.md

(Existing write to `{output_dir}/{feature}/research/{N}-{slug}/findings.md`.)

### Combined output

After both phases complete, the run folder contains:
- `transcript.md` — Phase 1 Q&A + repo scan summary + product/tech context (always present)
- `findings.md` — Phase 2 external evidence with citations (present only if Phase 2 ran)
```

- [ ] **Step 3.4: Update existing references to phase numbering**

Search the rest of the file for places that say "the research workflow" or "this skill" and update where helpful to "Phase 2" (existing) vs "Phase 1" (new).

- [ ] **Step 3.5: Commit**

```bash
git add shield/skills/general/research/SKILL.md
git commit -m "feat(shield): research SKILL.md describes two-phase flow (Phase 1 Q&A + Phase 2 evidence)"
```

---

## Task 4: Update /research command

**Files:**
- Modify: `shield/commands/research.md`

- [ ] **Step 4.1: Read current /research command**

```bash
cat shield/commands/research.md
```

- [ ] **Step 4.2: Update the description and workflow summary**

Update to reflect the two-phase behavior:

```markdown
---
allowed-tools: Read, Write, Bash, Agent, Glob, Grep, WebFetch
description: Capture product + tech context for a new feature. Phase 1: Q&A walk with repo auto-detection. Phase 2 (optional): external evidence-gathering with citations.
---

# /research

Two-phase research command. Phase 1 captures internal context via Q&A + repo scan. Phase 2 (opt-in) runs external evidence-gathering on open questions.

## Usage

```
/research <topic>             # interactive — both phases offered
/research --lean <topic>      # use lean depth mode (5 topics only)
/research --deep <topic>      # use deep depth mode (~15 topics)
/research --phase2-only       # skip Phase 1, run only external evidence-gathering (legacy behavior)
```

## What it does

### Phase 1 (new)

1. **Silent repo scan** — detects Stack, Integrations, Compliance markers, Deployment pattern, Recent activity, ADRs, Prior research artifacts
2. **Confirm detected context with user** — yes / no / correct / add
3. **Q&A walk** — asks product + tech topics, skipping any auto-answered from invocation message, repo scan, or prior transcript
4. **Surface open questions** + offer Phase 2

### Phase 2 (existing — opt-in after Phase 1)

5. **PM framing** on chosen questions
6. **3 parallel agents** — official sources, industry voices, community experience
7. **Synthesize** with citations
8. **PM review** on synthesis
9. **Write `findings.md`** with sourced evidence

## Output

```
{output_dir}/{feature}/research/{N}-{slug}/
├── transcript.md           # always present
└── findings.md             # only if Phase 2 ran
```

## Reference

Full behavior in `shield/skills/general/research/SKILL.md`. See `repo-scan.md` for detection rules and `qa-topics.md` for the topic catalog.

## See also

- `/prd` — author a PRD informed by this research
- `/prd-review` — review an existing PRD
- `/plan` — generate a technical plan
```

- [ ] **Step 4.3: Commit**

```bash
git add shield/commands/research.md
git commit -m "feat(shield): /research command reflects two-phase flow"
```

---

## Task 5: Test fixtures

**Files:**
- Create: `shield/skills/general/research/test-fixtures/small-node-app/...`
- Create: `shield/skills/general/research/test-fixtures/minimal-repo/...`

**Goal:** Two fixture repos for RED-GREEN testing of repo-scan + Q&A skip behavior.

- [ ] **Step 5.1: Create `small-node-app` fixture**

```bash
mkdir -p shield/skills/general/research/test-fixtures/small-node-app/.github/workflows
```

Files:

`package.json` (~30 lines):
```json
{
  "name": "small-node-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0",
    "passport": "^0.7.0",
    "passport-google-oauth20": "^2.0.0",
    "pg": "^8.11.0",
    "redis": "^4.6.0",
    "@stripe/stripe-js": "^2.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

`tsconfig.json`:
```json
{ "compilerOptions": { "target": "ES2022", "module": "commonjs" } }
```

`docker-compose.yml`:
```yaml
services:
  postgres:
    image: postgres:16
  redis:
    image: redis:7
```

`CLAUDE.md`:
```markdown
# Project conventions

This service handles user authentication and payment processing.
- SOC2 compliance required
- Uses helm + ArgoCD for deployment
- Canary releases per `helm/values.yaml` canary stanza
```

`.github/workflows/deploy.yml`:
```yaml
name: deploy
on: { push: { branches: [main] } }
jobs:
  deploy:
    steps:
      - name: canary
        run: helm upgrade --install --set canary.enabled=true ...
```

**Expected repo-scan output:**
- Stack: Node.js + TypeScript (detected) — *from package.json + tsconfig.json*
- Integrations: passport-google-oauth20 (detected), Stripe (detected), Postgres (detected), Redis (detected)
- Compliance markers: SOC2 (detected) — *from CLAUDE.md*
- Deployment pattern: Helm + canary (detected) — *from CLAUDE.md + .github/workflows/deploy.yml*

- [ ] **Step 5.2: Create `minimal-repo` fixture**

```bash
mkdir -p shield/skills/general/research/test-fixtures/minimal-repo
```

`README.md`:
```markdown
# Empty project

Just getting started.
```

**Expected repo-scan output:** No detections; falls through to manual Q&A only.

- [ ] **Step 5.3: Commit**

```bash
git add shield/skills/general/research/test-fixtures/
git commit -m "test(shield): research test fixtures (small-node-app + minimal-repo)"
```

---

## Task 6: RED test — baseline

- [ ] **Step 6.1: Run `/research <topic>` on each fixture WITHOUT repo-scan.md and qa-topics.md loaded**

For `small-node-app`:

```
cd shield/skills/general/research/test-fixtures/small-node-app
/research "add multi-factor authentication"
```

Document baseline: how many questions does the existing skill ask? Does it ask about Node/TS even though it's obvious from package.json?

For `minimal-repo`: similar baseline.

- [ ] **Step 6.2: Save baseline**

`shield/skills/general/research/test-fixtures/RED-baseline.md` (temporary).

```bash
git add shield/skills/general/research/test-fixtures/RED-baseline.md
git commit -m "test(shield): research RED baseline"
```

---

## Task 7: GREEN test — with Phase 1 enhancements

- [ ] **Step 7.1: Run `/research <topic>` on each fixture WITH repo-scan + Q&A loaded**

For `small-node-app`:

Expected behavior:
- Shield scans repo silently
- Surfaces detected context (Stack, Integrations, Compliance, Deployment)
- Asks user to confirm
- Skips Q&A topics 8 (Existing systems), 9 (Constraints) because repo scan auto-filled them
- Asks only Product topics + remaining Tech topics
- Offers Phase 2 at end

Verify:
- ✓ `## Detected Context` section in `transcript.md`
- ✓ Each detected entry tagged correctly
- ✓ Q&A skip rules applied (fewer questions than baseline)
- ✓ Phase 2 offered, can be declined

For `minimal-repo`:
- ✓ Empty Detected Context with a note "no technical context detected"
- ✓ Full Q&A walk asked (no auto-fills)

- [ ] **Step 7.2: Iterate on gaps**

Common gaps to fix:
- Repo-scan detection too narrow (missing a common manifest file) → expand the table in `repo-scan.md`
- Skip rules not applied → check `qa-topics.md` skip-rule mechanics in SKILL.md workflow
- Detected context not surfaced clearly → tighten the user prompt

- [ ] **Step 7.3: Cleanup + commit**

```bash
rm shield/skills/general/research/test-fixtures/RED-baseline.md
git add shield/skills/general/research/
git commit -m "test(shield): research GREEN — Phase 1 Q&A + repo scan verified"
```

---

## Task 8: Integration test — Phase 1 → Phase 2

- [ ] **Step 8.1: Run `/research` and proceed to Phase 2**

Run `/research "add multi-factor authentication"` on `small-node-app`. Accept Phase 1 results. Then say "yes" to Phase 2.

Verify:
- Phase 2's existing 3-agent flow runs
- Output: `transcript.md` (from Phase 1) AND `findings.md` (from Phase 2) both present
- `## External Findings` section appears in `transcript.md` referencing `findings.md`

- [ ] **Step 8.2: Run `/research --phase2-only`**

Verify legacy behavior — skip Phase 1, run Phase 2 only. This preserves backward compatibility.

- [ ] **Step 8.3: Run `/research --lean`**

Verify lean depth mode asks ~5 questions only.

- [ ] **Step 8.4: Commit integration baseline**

```bash
mkdir -p shield/skills/general/research/test-fixtures/integration/
cp -r shield/skills/general/research/test-fixtures/small-node-app/.research/ shield/skills/general/research/test-fixtures/integration/phase1-phase2-baseline/ 2>/dev/null || true
git add shield/skills/general/research/test-fixtures/integration/
git commit -m "test(shield): research integration baseline (Phase 1 + Phase 2)"
```

---

## Task 9: Marketplace version bump

- [ ] **Step 9.1: Bump shield version**

```diff
- "version": "2.13.0",
+ "version": "2.14.0",
```

- [ ] **Step 9.2: Commit + push**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.14.0 — Phase C /research Phase 1 enhancement"
git push
```

---

## Spec → plan coverage check

| Spec requirement | Implemented in task |
|---|---|
| Repo auto-detect (Stack, Integrations, Compliance, Deployment, Recent activity, ADRs, Prior artifacts) | Task 1 (repo-scan.md) |
| Confidence tags (detected / confirmed / corrected / manual) | Task 1 |
| Q&A topic catalog (product + tech) | Task 2 (qa-topics.md) |
| Depth modes (lean / standard / deep) with auto-suggest | Task 2 |
| Skip rules (invocation context, repo scan, prior transcript) | Task 2, Task 3 (SKILL.md workflow) |
| "Skip" / "I don't know" handling | Task 2 |
| Two-phase flow (Phase 1 internal Q&A + Phase 2 existing external) | Task 3 (SKILL.md) |
| Transcript structure (## Detected Context + ## Product Context + ## Technical Context + ## Open Questions + ## External Findings) | Task 3 |
| Phase 2 trigger after Phase 1 | Tasks 2, 3 |
| `--phase2-only` legacy mode | Task 4 |
| Test fixtures | Task 5 |
| RED-GREEN validation | Tasks 6, 7 |
| Integration test | Task 8 |
| Version bump | Task 9 |

This plan is Phase C only. With Phase A, B, and C all shipped, the full PRD-and-Research redesign is complete.
