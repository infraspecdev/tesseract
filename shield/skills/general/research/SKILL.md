---
name: research
description: Use when comparing approaches, evaluating tools, building evidence-based decisions, or the user needs citations and industry backing. Triggers on /research, investigate, compare, evaluate.
---

# Research Skill

Research a technical topic and produce a well-sourced document with direct quotes, industry references, and a clear recommendation.

## Output Path — MANDATORY

Write the final document using the Write tool to **exactly** this path:

```
{output_dir}/{feature-name}-YYYYMMDD/research/{N}-{slug}/findings.md
```

Where:
- `{output_dir}` — read from `.shield.json` `output_dir` field (default: `docs/shield`)
- `{feature-name}-YYYYMMDD` — the feature folder (ask user if no active feature context: "No active feature context. What feature name should this go under?")
- `{N}` — run number (count existing folders in `{feature}/research/` + 1)
- `{slug}` — slugified research topic (lowercase, hyphens only, max 50 chars)

**Do NOT** use any other path, filename, or directory. The Write tool creates directories automatically. After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

## When to Use

- Comparing architectural approaches (monorepo vs multi-repo, REST vs gRPC, etc.)
- Evaluating tools or technologies for adoption
- Building evidence-based ADRs or decision documents
- Any time the user needs citations and industry backing for a decision

## When NOT to Use

- Breaking down work into stories — use `shield:plan-docs`
- Reviewing existing code or plans — use `shield:review` or `shield:plan-review`
- Quick factual lookups that don't need citations

## Workflow

1. **Clarify topic** — skip if user already provided enough context
2. **PM framing** — dispatch PM agent in research-framing mode
3. **Research with parallel agents** — shaped by PM framing output
4. **Synthesize findings**
5. **PM review** — dispatch PM agent in research-review mode
6. **Write to `{output_dir}/{feature}/research/{N}-{slug}/findings.md`** — the Write tool creates directories automatically

## Clarify Topic & Scope

Skip if the user already provided enough context. Otherwise ask:
- What decision or question are they trying to answer?
- Any constraints or preferences to bias toward?

## PM Framing

Dispatch the PM agent in **research-framing** mode with the research topic as input. Use the Agent tool with `subagent_type: "shield:product-manager-reviewer"`.

The agent returns a structured brief with: stakeholders, decision(s) to make, success criteria, prioritized research questions, scope boundaries, and timeline constraints.

This output shapes the research agent prompts in the next step. If PM framing fails or times out, proceed with research without framing context — do not block the workflow.

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

## Synthesize Findings

- Identify consensus across sources
- Note disagreements and what drives them
- Map findings to the user's specific context
- Form a clear recommendation with reasoning

## PM Review

After synthesizing findings, dispatch the PM agent in **research-review** mode with the synthesized findings as input. Use the Agent tool with `subagent_type: "shield:product-manager-reviewer"`.

The agent returns a hybrid output: narrative sections (User Impact Analysis, Scope Recommendation, Prioritization Framework, Stakeholder Summary) plus a graded scorecard (PM1-PM10).

Include this output as a `## Product Lens` section in the final document, placed after `## Summary` and before `## References`.

## Write Document

**Output: `{output_dir}/{feature}/research/{N}-{slug}/findings.md`**

```markdown
# [Decision Title]

**Status:** Proposed
**Date:** [date]
**Context:** [1-2 sentences on what prompted this]

## Decision
[Clear statement of the recommended approach]

## Why Not [Alternative]?
[Comparison table if applicable]

## What the Industry Recommends
### [Source Name] ([Role/Context])
> *"Direct quote"*
> — [Source with link]
[Repeat for 4-8 authoritative sources]

## How This Works in Practice
[Concrete examples relevant to the user's setup]

## Migration Path / Reversibility
[How to change course if the decision turns out wrong]

## Summary
[2-3 sentence wrap-up tying recommendation to evidence]

## Product Lens
[PM review output — narrative sections and scorecard from the PM agent's research-review mode]

## References
- [All source URLs as clickable links]
```

## Rules

1. **Every claim needs a source** — no unsourced opinions
2. **Use direct quotes** — don't paraphrase when the original wording is impactful
3. **Bias toward the user's context** — frame advice relative to their scale
4. **Include dissenting views** — present both sides when sources disagree
5. **Make it actionable** — end with concrete next steps
6. **Keep it skimmable** — tables, headers, bullet points

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping PM framing because "the topic is straightforward" | Always run PM framing — it prioritizes research questions and sets scope boundaries, preventing unfocused research |
| Paraphrasing sources instead of using direct quotes | Use the original wording with attribution — paraphrases lose credibility and make claims harder to verify |
| All 3 research agents returning the same sources | Each agent has a distinct source type (official docs, industry voices, community) — if they overlap, the prompts need sharper differentiation |
| Writing Product Lens as a separate document instead of a section | PM review output goes inside findings.md as `## Product Lens` between Summary and References |
| Including recommendations without source backing | Every recommendation must trace to at least one cited source — unsupported opinions violate rule 1 |
| Omitting dissenting views when sources agree | If all sources agree, state that explicitly — the absence of disagreement is itself a finding worth noting |
