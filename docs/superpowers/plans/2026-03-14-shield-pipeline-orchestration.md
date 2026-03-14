# Shield Pipeline Orchestration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create all slash commands that orchestrate the Shield pipeline phases, plus single-domain review commands. These commands are the user-facing entry points that invoke skills and dispatch agents.

**Architecture:** Each command is a markdown file in `shield/commands/` that instructs Claude how to handle the user's request. Commands invoke skills, dispatch agents, and coordinate the pipeline flow. Some are ported from existing plugins, some are new.

**Tech Stack:** Markdown command definitions

---

## Chunk 1: Pipeline Phase Commands

### Task 1: Create /research command

**Files:**
- Create: `shield/commands/research.md`

- [ ] **Step 1: Create the command**

```markdown
---
name: research
description: Research a technical topic with structured citations and expert sources
---

# Research

Invoke the Shield research skill to investigate a technical topic.

## Usage

`/research [topic]`

## Behavior

1. If a topic is provided as an argument, use it directly
2. If no topic, ask the user what they'd like to research
3. Invoke the `shield:general:research` skill with the topic
4. The skill handles the full research workflow: clarify scope, parallel research, synthesize, write document
5. After completion, invoke the `shield:general:summarize` skill to produce a research summary
6. Write the summary to the run directory
```

- [ ] **Step 2: Commit**

```
feat: add /research command
```

### Task 2: Create /plan command

**Files:**
- Create: `shield/commands/plan.md`

- [ ] **Step 1: Create the command**

```markdown
---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories
---

# Plan

Invoke the Shield plan-docs skill to create planning documents.

## Usage

`/plan [topic or requirements]`

## Behavior

1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning
3. Invoke the `shield:general:plan-docs` skill
4. The skill generates:
   - Architecture/ADR document (HTML)
   - Detailed execution plan with stories (HTML)
   - Plan sidecar JSON (machine-readable story data)
5. After completion, invoke `shield:general:summarize` to produce a plan summary
6. Write the summary to the run directory
7. Offer next steps:
   - `/plan-review` — run multi-agent review on the plan
   - `/pm-sync` — sync stories to PM tool
```

- [ ] **Step 2: Commit**

```
feat: add /plan command
```

### Task 3: Create /plan-review command

**Files:**
- Create: `shield/commands/plan-review.md`

- [ ] **Step 1: Read the source command**

Read `/Users/ashwinimanoj/projects/tesseract/dev-workflow/commands/plan-review.md` for reference.

- [ ] **Step 2: Create the command**

Adapt from the source. Key changes:
- Reference `shield:general:plan-review` skill instead of `dev-workflow:plan-review`
- Reference Shield agent names (shield:security-reviewer, shield:architecture-reviewer, etc.)
- Add summarize step at the end
- Add next step suggestions (/pm-sync, /implement)

```markdown
---
name: plan-review
description: Run multi-agent plan review with scored analysis
args: "[path to plan file]"
---

# Plan Review

Run the Shield multi-persona plan review on a plan document.

## Usage

`/plan-review [path]`

## Behavior

1. If a path is provided, use that plan file
2. If no path, auto-detect recent plan files in the working directory
3. Invoke the `shield:general:plan-review` skill
4. The skill:
   - Reads the plan and extracts keywords
   - Selects reviewers (auto-detect + config overrides from `~/.tesseract/config.json`)
   - Dispatches selected agents in parallel (plan review mode)
   - Parses grades, calculates scores
   - Classifies recommendations (P0/P1/P2)
   - Writes analysis and enhanced plan to `review/` directory
5. Present results with three options:
   - Apply recommendations as-is
   - Apply with edits
   - Skip
6. Invoke `shield:general:summarize` to produce a plan-review summary
7. Offer next steps: `/pm-sync`, `/implement`
```

- [ ] **Step 3: Commit**

```
feat: add /plan-review command
```

### Task 4: Create /pm-sync command

**Files:**
- Create: `shield/commands/pm-sync.md`

- [ ] **Step 1: Read the source command**

Read `/Users/ashwinimanoj/projects/tesseract/clickup-sprint-planner/commands/sprint-sync.md` for reference.

- [ ] **Step 2: Create the command**

Adapt from sprint-sync. Key changes:
- Reference `shield:pm-sync` skill instead of clickup-specific tools
- Use abstract pm_* operations
- Read from plan sidecar JSON instead of HTML parsing
- Add summarize step

```markdown
---
name: pm-sync
description: Sync plan stories to your PM tool (ClickUp, Jira, etc.)
---

# PM Sync

Sync plan document stories against your project management tool.

## Usage

`/pm-sync`

## Behavior

1. Check that a PM tool is configured (`~/.tesseract/config.json` → `pm_tool`)
2. If not configured, suggest running `/shield init` to set up PM integration
3. Invoke the `shield:pm-sync` skill
4. The skill:
   - Calls `pm_get_capabilities` to verify adapter supports sync
   - Reads the plan sidecar JSON for story data
   - Calls `pm_sync` to diff against PM state
   - Presents diff as table (match/new/updated/unlinked)
   - Asks user: apply all / pick which / cancel
   - For new stories: calls `pm_bulk_create`
   - For updates: calls `pm_bulk_update`
   - Updates the sidecar JSON with PM IDs and URLs
   - Re-renders HTML from updated sidecar
5. Invoke `shield:general:summarize` to produce a sync summary
6. Offer next steps: `/pm-status`, `/implement`
```

- [ ] **Step 3: Commit**

```
feat: add /pm-sync command
```

### Task 5: Create /pm-status command

**Files:**
- Create: `shield/commands/pm-status.md`

- [ ] **Step 1: Read the source command**

Read `/Users/ashwinimanoj/projects/tesseract/clickup-sprint-planner/commands/sprint-status.md` for reference.

- [ ] **Step 2: Create the command**

```markdown
---
name: pm-status
description: Show sprint/epic status overview from your PM tool
args: "[epic] [--by status|assignee]"
---

# PM Status

Show sprint or epic status overview from your project management tool.

## Usage

`/pm-status [epic] [--by status|assignee]`

## Arguments

- `epic` (optional) — specific epic ID to show detail for
- `--by status|assignee` (optional) — group stories by status or assignee (default: by epic)

## Behavior

1. Check that a PM tool is configured
2. Call `pm_get_capabilities` to verify adapter supports status
3. Call `pm_get_status` with the epic filter and grouping option
4. Present results as a formatted table:
   - Epic summary: Total, Done, In Progress, Ready, Blocked
   - Story detail when specific epic is requested
5. If no PM tool configured, check if a plan sidecar JSON exists and show status from that instead
```

- [ ] **Step 3: Commit**

```
feat: add /pm-status command
```

### Task 6: Create /implement command

**Files:**
- Create: `shield/commands/implement.md`

- [ ] **Step 1: Create the command**

```markdown
---
name: implement
description: Start TDD-based feature implementation with progress tracking
args: "[feature description or story ID]"
---

# Implement

Start implementing a feature using test-driven development with progress tracking.

## Usage

`/implement [feature or story ID]`

## Behavior

1. If a story ID is provided (e.g., EPIC-1-S1), look up the story in the plan sidecar JSON
2. If a feature description is provided, use it as the starting context
3. If nothing provided, ask what the user wants to implement

### Acceptance Criteria Confirmation

4. If story context exists (from sidecar or PM tool):
   - Present acceptance criteria to the user
   - Ask to confirm, edit, or skip:
     ```
     Acceptance Criteria:
       1. Regional pools allocate /20 CIDRs
       2. No CIDR overlap across regions

     [a] Proceed as-is  [b] Edit criteria  [c] Skip
     ```
   - If edited, update the sidecar JSON and re-render HTML

### Implementation

5. Invoke the `shield:general:implement-feature` skill
6. If superpowers is available, delegate TDD to `superpowers:test-driven-development`
7. After each implementation step:
   - Run a lightweight review (code correctness + domain skill only)
   - Present any findings
   - Commit the step
8. After all steps complete, invoke `shield:general:summarize`

### Final Review

9. Offer to run a full `/review` for comprehensive agent-based review
10. Offer next steps: `/review`, `/pm-sync` (to update status)
```

- [ ] **Step 2: Commit**

```
feat: add /implement command
```

### Task 7: Create /review command

**Files:**
- Create: `shield/commands/review.md`

- [ ] **Step 1: Create the command**

```markdown
---
name: review
description: Run comprehensive code review with domain-specific agents and AC verification
args: "[path or scope]"
---

# Review

Run a comprehensive code review that covers code correctness, domain-specific checks, agent reviews, and acceptance criteria verification.

## Usage

`/review [path or scope]`

## Arguments

- `path` (optional) — specific file or directory to review
- If omitted, reviews all changed files (git diff against main)

## Behavior

1. Invoke the `shield:general:review` skill
2. The skill determines context and runs the appropriate depth:
   - Code correctness review on changed files
   - Domain-specific review skills (terraform, atmos, etc.)
   - Agent reviews (security, cost, architecture, operations — selected by auto-detect + config)
   - Acceptance criteria verification (if story context exists)
3. Findings are merged, deduplicated, sorted by severity
4. Present to user with options:
   - Apply all fixes
   - Select specific fixes
   - Skip (review only)
   - Post findings to PM card
5. Apply selected fixes
6. Invoke `shield:general:summarize` to produce a review summary
7. If fixes were applied, offer to re-run review to verify

## Single-Agent Shortcuts

For targeted reviews, use:
- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only
- `/review-well-architected` — AWS Well-Architected Framework review
```

- [ ] **Step 2: Commit**

```
feat: add /review command
```

## Chunk 2: Single-Domain Review Commands

### Task 8: Create /review-security command

**Files:**
- Create: `shield/commands/review-security.md`

- [ ] **Step 1: Read the source**

Read `/Users/ashwinimanoj/projects/tesseract/infra-review/commands/review-security.md` for reference.

- [ ] **Step 2: Create the command**

Adapt from source. Key changes:
- Reference `shield:security-reviewer` agent instead of `infra-review:security-reviewer`
- Reference `shield:terraform:security-audit` skill instead of `infra-review:terraform-security-audit`
- Add the appropriate mode (infra-code for Terraform, plan for plan docs)

```markdown
---
name: review-security
description: Run security-focused review with the security reviewer agent
---

# Security Review

Run a targeted security review using the Shield security reviewer agent.

## Behavior

1. Detect the review context:
   - If Terraform files are present → dispatch `shield:security-reviewer` in **infra-code** mode
   - If reviewing a plan document → dispatch in **plan** mode
2. Also invoke `shield:terraform:security-audit` skill if terraform domain is active
3. Present findings sorted by severity
4. Ask user which fixes to apply
5. Write findings to review summary
```

- [ ] **Step 3: Commit**

```
feat: add /review-security command
```

### Task 9: Create /review-cost command

**Files:**
- Create: `shield/commands/review-cost.md`

- [ ] **Step 1: Read the source**

Read `/Users/ashwinimanoj/projects/tesseract/infra-review/commands/review-cost.md` for reference.

- [ ] **Step 2: Create the command**

```markdown
---
name: review-cost
description: Run cost optimization review with the cost reviewer agent
---

# Cost Review

Run a targeted cost review using the Shield cost reviewer agent.

## Behavior

1. Detect the review context:
   - If Terraform files → dispatch `shield:cost-reviewer` in **infra-code** mode
   - If plan document → dispatch in **plan** mode
2. Also invoke `shield:terraform:cost-review` skill if terraform domain is active
3. Present findings with estimated cost impact
4. Show environment-specific recommendations (dev/staging/prod)
5. Ask user which fixes to apply
```

- [ ] **Step 3: Commit**

```
feat: add /review-cost command
```

### Task 10: Create /review-well-architected command

**Files:**
- Create: `shield/commands/review-well-architected.md`

- [ ] **Step 1: Read the source**

Read `/Users/ashwinimanoj/projects/tesseract/infra-review/commands/review-well-architected.md` for reference.

- [ ] **Step 2: Create the command**

```markdown
---
name: review-well-architected
description: Run AWS Well-Architected Framework review across all 6 pillars
---

# Well-Architected Review

Run a holistic infrastructure review using the AWS Well-Architected Framework.

## Behavior

1. Dispatch `shield:well-architected-reviewer` agent in **infra-code** mode
2. The agent evaluates across all 6 pillars:
   - Operational Excellence
   - Security
   - Reliability
   - Performance Efficiency
   - Cost Optimization
   - Sustainability
3. Cross-reference with specialized agents if available
4. Present pillar scores summary table
5. Show overall verdict and top 3 remediation items
6. Ask user which fixes to apply
```

- [ ] **Step 3: Commit**

```
feat: add /review-well-architected command
```

### Task 11: Create /analyze-plan command

**Files:**
- Create: `shield/commands/analyze-plan.md`

- [ ] **Step 1: Read the source**

Read `/Users/ashwinimanoj/projects/tesseract/infra-review/commands/analyze-plan.md` for reference.

- [ ] **Step 2: Create the command**

Adapt from source. Key changes:
- Reference `shield:terraform:plan-analysis` skill
- Keep the terraform plan detection logic

```markdown
---
name: analyze-plan
description: Analyze terraform plan output for security, cost, and destructive action impact
---

# Analyze Terraform Plan

Analyze `terraform plan -json` output for security, cost, and operational impact.

## Usage

`/analyze-plan [path to plan JSON]`

## Behavior

1. Detect the component (src/ vs components/terraform/)
2. Locate or generate plan:
   - User-provided JSON path
   - Existing .tfplan file
   - Or offer to run `terraform plan -json` (NEVER `terraform apply`)
3. Invoke `shield:terraform:plan-analysis` skill
4. The skill analyzes: change summary, destructive actions, security changes, cost impact, drift
5. Write report to run directory
6. Present summary with flagged items

## Important

- NEVER run `terraform apply`
- Use `-lock=false` when generating plans
- Flag destructive actions (destroy, replace) prominently
```

- [ ] **Step 3: Commit**

```
feat: add /analyze-plan command
```
