---
name: pm-analysis
description: |
  Use when any workflow needs a product lens — user impact analysis, prioritization,
  scope discipline, or stakeholder framing. Triggers on product analysis, PM review,
  user impact, business value.
---

# PM Analysis Skill

Thin orchestrator that dispatches the appropriate focused subagent(s) based on mode. Post
pm-restructure-v0, the omnibus `shield:product-manager` agent has been decomposed; this skill
now routes to:

- `research-framing` mode → `shield:research-framer`
- `research-review` mode → `shield:research-reviewer-narrative` + `shield:user-impact-clarity` (PM1) + ... + `shield:business-value-alignment` (PM10) + `shield:framing-coverage-honored` (PM11), dispatched in parallel
- `plan-review` mode → `shield:user-impact-clarity` (PM1) + ... + `shield:business-value-alignment` (PM10), dispatched in parallel
- `standalone` mode → same as `plan-review` (PM1-PM10 in parallel)

The domain knowledge lives in the focused subagents — this skill only determines the mode,
gathers input, and dispatches.

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

1. **Determine mode** — use the explicit parameter from the calling skill, or default to `standalone`.
2. **Gather input material** — raw topic (for framing), research doc (for research-review), plan doc (for plan-review), or caller-provided input (for standalone).
3. **Dispatch the appropriate subagent(s)** per the routing table below.
4. **Return output** — pass the subagent output(s) back to the calling workflow unchanged. For multi-subagent dispatches (research-review, plan-review, standalone) the orchestrator returns the merged narrative + scorecard the caller expects.

### Routing table

| Mode | Dispatches (parallel) | Inputs |
|---|---|---|
| `research-framing` | `shield:research-framer` | `topic`, optional `decision_context`, optional `urgency` |
| `research-review` | `shield:research-reviewer-narrative` + PM1-PM10 + `shield:framing-coverage-honored` (PM11) | `findings_path`, `framing_brief_path` |
| `plan-review` | PM1-PM10 (10 parallel dispatches; no PM11) | `doc_path` |
| `standalone` | PM1-PM10 | `doc_path` |

PM1-PM10 are the 10 global subagents `shield:user-impact-clarity`, `shield:problem-solution-fit`,
`shield:scope-discipline-of-plan`, `shield:prioritization-rationale`, `shield:stakeholder-
communicability`, `shield:market-competitive-awareness`, `shield:adoption-rollout-risk`,
`shield:success-metrics-defined`, `shield:reversibility-exit-cost`, `shield:business-value-
alignment`.

### Notes

- The scoring rubric (`scoring.md`) is loaded by each PM dim subagent's frontmatter context as
  needed; this skill no longer inlines the rubric in the dispatch prompt.
- `framing_brief_path` should reference the markdown brief produced by `shield:research-framer`
  upstream. PM11 returns `N/A` if no framing brief is supplied.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dispatching `shield:product-manager` | That agent was deleted in pm-restructure-v0. Route by mode per the table above. |
| Dispatching subagents sequentially in research-review / plan-review / standalone modes | Always dispatch PM1-PM10 in PARALLEL — sequential calls throw away the depth gains from decomposition. |
| Skipping framing in research because "the topic is clear enough" | Always run framing — it shapes research agent prompts, not just the user's understanding. |
| Omitting `framing_brief_path` from research-review mode | PM11 returns N/A without it; provide it whenever a framing brief was produced upstream. |
| Treating PM review output as optional | The Product Lens section is a required part of the research document. |
