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
2. **Research with parallel agents**
3. **Synthesize findings**
4. **Write to `{output_dir}/{feature}/research/{N}-{slug}/findings.md`** — the Write tool creates directories automatically

## Clarify Topic & Scope

Skip if the user already provided enough context. Otherwise ask:
- What decision or question are they trying to answer?
- Any constraints or preferences to bias toward?

## Research (Parallel Agents)

Launch **3 parallel agents** to maximize coverage:

- **Agent 1: Official sources** — docs from primary tools/frameworks
- **Agent 2: Industry voices** — blog posts, conference talks, expert recommendations
- **Agent 3: Community experience** — GitHub discussions, Stack Overflow, case studies

Each agent returns: direct quotes with attribution, source URLs, key data points.

## Synthesize Findings

- Identify consensus across sources
- Note disagreements and what drives them
- Map findings to the user's specific context
- Form a clear recommendation with reasoning

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
