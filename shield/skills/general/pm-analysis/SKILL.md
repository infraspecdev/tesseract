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
3. **Read the agent file** — use the Read tool to load `shield/agents/product-manager-reviewer.md`
4. **Dispatch the PM agent** — invoke `shield:product-manager-reviewer` using the Agent tool with the mode and input in the prompt
5. **Return output** — pass the agent's output back to the calling workflow unchanged

### Dispatch Prompt Template

```
You are a Technical Product Manager reviewing [input type].

<persona>
{Read and inject full content of shield/agents/product-manager-reviewer.md}
</persona>

<mode>[research-framing|research-review|plan-review|standalone]</mode>

<input>
{the input material}
</input>

[For evaluative modes only:]
<scoring-rubric>
{Read and inject full content of shield/skills/general/plan-review/scoring.md}
</scoring-rubric>

Operate in the specified mode. Follow the Review Process and Output Format for that mode exactly.
```

**Notes:**
- The `<scoring-rubric>` block is only included for evaluative modes (`research-review`, `plan-review`, `standalone`). Omit it for `research-framing`.
- The `[input type]` in the opening line should reflect the mode: "a research topic" (framing), "research findings" (research-review), "an implementation plan" (plan-review), or "the following input" (standalone).
