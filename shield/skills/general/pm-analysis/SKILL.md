---
name: pm-analysis
description: |
  Use when any workflow needs a product lens — user impact analysis, prioritization,
  scope discipline, or stakeholder framing. Triggers on product analysis, PM review,
  user impact, business value.
---

# PM Analysis Skill

Thin orchestrator that dispatches the `product-manager-reviewer` agent with the right mode and context. The domain knowledge lives entirely in the agent — this skill only determines the mode, gathers input, and dispatches.

## When to Use

- Any workflow that needs a product lens — user impact, prioritization, scope discipline, stakeholder framing
- Called from `research` skill to frame questions before research or review findings after synthesis
- Called from `plan-review` skill to add a PM perspective on plans
- Direct invocation for standalone PM analysis on any input (RFC, proposal, research doc)

## When NOT to Use

- Pure infrastructure or code reviews with no product decisions — use `shield:review` instead
- Quick factual lookups that don't need a product perspective

## Mode Selection

| Context | Mode |
|---------|------|
| Called from research skill before research agents run | `research-framing` |
| Called from research skill after synthesis | `research-review` |
| Called from plan-review skill | `plan-review` |
| Called directly or from any other workflow | `standalone` (default) |

The calling skill passes the mode explicitly. Standalone is the default when no mode is specified.

## Dispatch Workflow

1. **Determine mode** — use the explicit parameter from the calling skill, or default to `standalone`
2. **Gather input material** — raw topic (for framing), research doc (for research-review), plan doc (for plan-review), or caller-provided input (for standalone)
3. **Dispatch the PM agent** — use the Agent tool with `subagent_type: "shield:product-manager-reviewer"`. The agent definition is loaded automatically by the Agent tool — do NOT manually read the agent file.
4. **Return output** — pass the agent's output back to the calling workflow unchanged

### Dispatch Prompt

The `prompt` parameter for the Agent tool should contain:

```
You are a Technical Product Manager reviewing [input type].

Mode: [research-framing|research-review|plan-review|standalone]

Input:
{the input material}

[For evaluative modes only — read and include scoring.md:]
Scoring rubric:
{content of ${CLAUDE_PLUGIN_ROOT}/skills/general/plan-review/scoring.md}

Operate in the specified mode. Follow the Review Process and Output Format for that mode exactly.
```

**Notes:**
- The scoring rubric is only included for evaluative modes (`research-review`, `plan-review`, `standalone`). Omit it for `research-framing`.
- The `[input type]` should reflect the mode: "a research topic" (framing), "research findings" (research-review), "an implementation plan" (plan-review), or "the following input" (standalone).
- For the scoring rubric, read `scoring.md` relative to the plugin root: `${CLAUDE_PLUGIN_ROOT}/skills/general/plan-review/scoring.md`.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Manually reading the agent file before dispatching | The Agent tool with `subagent_type` loads the agent definition automatically — don't double-inject |
| Skipping PM framing in research because "the topic is clear enough" | Always run framing — it shapes research agent prompts, not just the user's understanding |
| Including scoring rubric in research-framing mode | Framing produces a structured brief, not a graded scorecard — omit the rubric |
| Treating PM review output as optional | The Product Lens section is a required part of the research document |
| Using relative paths for scoring.md | Use `${CLAUDE_PLUGIN_ROOT}/skills/general/plan-review/scoring.md` |
