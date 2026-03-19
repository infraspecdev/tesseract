# Product Manager Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Technical Product Manager agent to Shield with 4 modes (research framing, research review, plan review, standalone) and integrate it into the research and plan-review workflows.

**Architecture:** A new agent definition (`product-manager-reviewer.md`) following the existing reviewer agent pattern, a thin orchestration skill (`pm-analysis/SKILL.md`), and updates to the research skill, plan-review skill, personas, and scoring files.

**Tech Stack:** Markdown (agent/skill definitions), no code — all files are Claude Code plugin markdown.

**Spec:** `docs/superpowers/specs/2026-03-19-product-manager-agent-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `shield/agents/product-manager-reviewer.md` | Agent definition — persona, 4 modes, checklists, review process, output formats |
| Create | `shield/skills/general/pm-analysis/SKILL.md` | Thin orchestrator — mode selection, dispatch, context gathering |
| Modify | `shield/skills/general/research/SKILL.md` | Wire in PM framing (step 2) and PM review (step 5) |
| Modify | `shield/skills/general/plan-review/personas.md:5-12` | Add PM agent row to persona catalog table |
| Modify | `shield/skills/general/plan-review/personas.md:40-45` | Add PM selection rule |
| Modify | `shield/skills/general/plan-review/scoring.md:29-38` | Add PM + operations-reviewer to persona weights table |
| Modify | `shield/skills/general/plan-review/SKILL.md:104` | Update "all 5 agents" to "all 7 agents" |
| Modify | `.claude-plugin/marketplace.json:12` | Bump shield version to 2.4.0 |

---

### Task 1: Create the PM Agent Definition

**Files:**
- Create: `shield/agents/product-manager-reviewer.md`

- [ ] **Step 1: Create the agent file with frontmatter and persona**

Write `shield/agents/product-manager-reviewer.md` with the YAML frontmatter (`name: product-manager-reviewer`, `description`, `model: inherit`), Persona section, Trigger Keywords, and Weight (0.7). Use the exact persona text from the spec (line 53).

- [ ] **Step 2: Add the Modes table**

Add the Modes section with the 4-mode table (Research Framing, Research Review, Plan Review, Standalone) matching spec lines 65-72.

- [ ] **Step 3: Add the Research Framing checklist (PF1-PF6)**

Add the Research Framing Checklist section with the note that this mode does not produce a graded scorecard. Include all 6 checks (PF1-PF6) from spec lines 76-87.

- [ ] **Step 4: Add the PM Evaluation Points (PM1-PM10)**

Add the PM Evaluation Points section for the 3 evaluative modes. Include all 10 checks (PM1-PM10) from spec lines 89-104.

- [ ] **Step 5: Add Review Process sections**

Add two Review Process subsections:
1. Research Framing Mode — 8 steps from spec lines 110-117
2. Research Review, Plan Review, and Standalone Modes — 11 steps from spec lines 121-131

- [ ] **Step 6: Add Output Format sections**

Add two Output Format subsections:
1. Research Framing Mode — the structured brief template from spec lines 139-162. No scorecard.
2. Research Review, Plan Review, and Standalone Modes — the hybrid template with `### Product Manager Review (Grade: X)` header, 4 narrative sections, scorecard table, Key Finding, and Recommendations table from spec lines 168-205.

- [ ] **Step 7: Verify agent file matches existing patterns**

Compare the structure of `product-manager-reviewer.md` against `shield/agents/security-reviewer.md` and `shield/agents/agile-coach-reviewer.md`. Verify:
- Frontmatter has `name`, `description`, `model: inherit`
- Sections follow: Persona → Trigger Keywords → Weight → Modes → Evaluation Points → Review Process → Output Format
- Output header uses `### Product Manager Review (Grade: X)` (matching `###` level used by architecture-reviewer and agile-coach-reviewer)

- [ ] **Step 8: Commit**

```bash
git add shield/agents/product-manager-reviewer.md
git commit -m "feat(shield): add product manager reviewer agent

Technical PM agent with 4 modes: research framing (PF1-PF6),
research review, plan review, and standalone (PM1-PM10)."
```

---

### Task 2: Create the PM Analysis Skill

**Files:**
- Create: `shield/skills/general/pm-analysis/SKILL.md`

- [ ] **Step 1: Create the skill file with frontmatter**

Write `shield/skills/general/pm-analysis/SKILL.md` with frontmatter from spec lines 211-219:
```yaml
---
name: pm-analysis
description: |
  Dispatch the product manager agent for product-lens analysis. Use when any workflow
  needs user impact, prioritization, scope, or stakeholder framing. Triggers on
  product analysis, PM review, user impact, business value.
---
```

- [ ] **Step 2: Add the overview and when-to-use sections**

Add a brief overview explaining this is a thin orchestrator that dispatches the PM agent. Add "When to Use" and "When NOT to Use" sections from spec lines 241-243.

- [ ] **Step 3: Add mode selection logic**

Add the mode selection table from spec lines 232-237:

| Context | Mode |
|---------|------|
| Called from research skill before research agents run | `research-framing` |
| Called from research skill after synthesis | `research-review` |
| Called from plan-review skill | `plan-review` |
| Called directly or from any other workflow | `standalone` (default) |

State: "The calling skill passes the mode explicitly. Standalone is the default when no mode is specified."

- [ ] **Step 4: Add the dispatch workflow**

Add the numbered workflow:
1. Determine mode (from explicit parameter or default to standalone)
2. Gather input material (raw topic, research doc, plan doc, or caller-provided input)
3. Dispatch the PM agent (`shield:product-manager-reviewer`) using the Agent tool with the mode and input in the prompt
4. Return the agent's output to the calling workflow

Include the dispatch prompt template:
```
You are a Technical Product Manager reviewing [input type].

<persona>
{full content of shield/agents/product-manager-reviewer.md}
</persona>

<mode>[research-framing|research-review|plan-review|standalone]</mode>

<input>
{the input material}
</input>

[For evaluative modes only:]
<scoring-rubric>
{full content of scoring.md}
</scoring-rubric>

Operate in the specified mode. Follow the Review Process and Output Format for that mode exactly.
```

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/pm-analysis/SKILL.md
git commit -m "feat(shield): add pm-analysis orchestration skill

Thin skill that dispatches product-manager-reviewer agent with
the right mode and context. Available to any Shield workflow."
```

---

### Task 3: Update the Research Skill

**Files:**
- Modify: `shield/skills/general/research/SKILL.md`

- [ ] **Step 1: Update the Workflow section**

Replace the `## Workflow` section (the current 4-step list) with the updated 6-step workflow:

```markdown
## Workflow

1. **Clarify topic** — skip if user already provided enough context
2. **PM framing** — dispatch PM agent in research-framing mode
3. **Research with parallel agents** — shaped by PM framing output
4. **Synthesize findings**
5. **PM review** — dispatch PM agent in research-review mode
6. **Write to `shield/docs/research-YYYYMMDD-HHMMSS.md`** — the Write tool creates the directory automatically
```

- [ ] **Step 2: Add PM Framing section after "Clarify Topic & Scope"**

Insert a new section after the `## Clarify Topic & Scope` section:

```markdown
## PM Framing

Dispatch the PM agent in **research-framing** mode with the research topic as input. Use the Agent tool with `subagent_type: "shield:product-manager-reviewer"`.

The agent returns a structured brief with: stakeholders, decision(s) to make, success criteria, prioritized research questions, scope boundaries, and timeline constraints.

This output shapes the research agent prompts in the next step. If PM framing fails or times out, proceed with research without framing context — do not block the workflow.
```

- [ ] **Step 3: Update the Research (Parallel Agents) section**

Replace the `## Research (Parallel Agents)` section to include PM framing context in agent prompts:

````markdown
## Research (Parallel Agents)

Launch **3 parallel agents** to maximize coverage:

- **Agent 1: Official sources** — docs from primary tools/frameworks
- **Agent 2: Industry voices** — blog posts, conference talks, expert recommendations
- **Agent 3: Community experience** — GitHub discussions, Stack Overflow, case studies

Each agent's prompt includes the PM framing context (if available):

```
Research [topic] from [source type].

Context from product analysis:
- Stakeholders: [from PM framing]
- Key questions to answer: [from PM framing, prioritized]
- Scope: [from PM framing]
- Timeline: [from PM framing]

Return direct quotes with attribution, source URLs, key data points. Prioritize findings that address the key questions above.
```

If PM framing was skipped, use the original prompt: `Research [topic] from [source type]. Return direct quotes with attribution, source URLs, key data points.`
````

- [ ] **Step 4: Add PM Review section after "Synthesize Findings"**

Insert a new section after the `## Synthesize Findings` section:

```markdown
## PM Review

After synthesizing findings, dispatch the PM agent in **research-review** mode with the synthesized findings as input. Use the Agent tool with `subagent_type: "shield:product-manager-reviewer"`.

The agent returns a hybrid output: narrative sections (User Impact Analysis, Scope Recommendation, Prioritization Framework, Stakeholder Summary) plus a graded scorecard (PM1-PM10).

Include this output as a `## Product Lens` section in the final document, placed after `## Summary` and before `## References`.
```

- [ ] **Step 5: Update the Write Document template**

In the `## Write Document` section, add a `## Product Lens` section to the output template (between `## Summary` and `## References`):

```markdown
## Product Lens
[PM review output — narrative sections and scorecard from the PM agent's research-review mode]
```

- [ ] **Step 6: Commit**

```bash
git add shield/skills/general/research/SKILL.md
git commit -m "feat(shield): integrate PM agent into research workflow

Add PM framing before research and PM review after synthesis.
Research agents now receive product context to shape their queries."
```

---

### Task 4: Update Plan-Review Personas and Scoring

**Files:**
- Modify: `shield/skills/general/plan-review/personas.md:5-12,40-45`
- Modify: `shield/skills/general/plan-review/scoring.md:29-38`

- [ ] **Step 1: Add PM agent to personas.md catalog table**

Add this row to the table at line 12 (after operations-reviewer):

```
| `shield:product-manager-reviewer` | 0.7 | User impact, scope discipline, prioritization, business value |
```

- [ ] **Step 2: Add PM selection rule to personas.md**

Add to the Selection Rules section (after line 44):

```markdown
- **Include** product-manager-reviewer when plan contains user-facing features, product decisions, or scope trade-offs (matched via trigger keywords)
```

- [ ] **Step 3: Add PM and operations-reviewer to scoring.md weights table**

Update the Persona Weights table (lines 31-37) to add two rows:

```
| Operations | 0.7 | Supporting |
| Product Manager | 0.7 | Supporting |
```

Update the line "Only activated personas contribute to the composite. The denominator is the sum of weights for personas that actually ran — not all 5." to say "not all 7."

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/plan-review/personas.md shield/skills/general/plan-review/scoring.md
git commit -m "feat(shield): add PM agent to plan-review persona catalog and scoring

Add product-manager-reviewer (0.7 weight) to personas and scoring.
Also fix pre-existing gap: add operations-reviewer to scoring weights."
```

---

### Task 5: Update Plan-Review SKILL.md Agent Count

**Files:**
- Modify: `shield/skills/general/plan-review/SKILL.md:104`

- [ ] **Step 1: Update "all 5 agents" reference**

Change line 104 from:
```
| Dispatching all 5 agents for a simple app plan with no infra | Follow trigger keyword matching — skip Cloud Architect and Cost/FinOps if no infra keywords |
```
to:
```
| Dispatching all 7 agents for a simple app plan with no infra | Follow trigger keyword matching — skip Cloud Architect and Cost/FinOps if no infra keywords |
```

- [ ] **Step 2: Commit**

```bash
git add shield/skills/general/plan-review/SKILL.md
git commit -m "fix(shield): update agent count in plan-review common mistakes

Reflects addition of product-manager-reviewer and correct count
including operations-reviewer."
```

---

### Task 6: Bump Shield Version

**Files:**
- Modify: `.claude-plugin/marketplace.json:12`

- [ ] **Step 1: Bump version to 2.4.0**

Change line 12 from:
```json
"version": "2.3.0",
```
to:
```json
"version": "2.4.0",
```

- [ ] **Step 2: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: bump shield version to 2.4.0"
```
