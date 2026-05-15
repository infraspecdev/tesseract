# Shield Evals

Lightweight quality measurements for shield skills. Each eval is a markdown file with:
- **Setup** — what state the working directory should be in.
- **Prompt** — what we tell the subagent under test.
- **Success criteria** — structural assertions (deterministic) + qualitative checks (LLM-judged).
- **Pass threshold** — how many checks must pass.

## Running an eval

```bash
# Single eval
./shield/evals/run-eval.sh prd-docs/01-terminologies-autofill

# All evals in a folder
./shield/evals/run-eval.sh prd-docs
```

Each eval produces a transcript and a pass/fail verdict. Aggregate results print at the end.

## Eval file format

```markdown
---
name: <kebab-case slug matching filename>
skill_under_test: shield:<skill-name>
scenario: <one-line description>
---

## Setup
<bash steps to create the working directory state>

## Prompt
> <prompt sent to the subagent>

## Success criteria

### Structural (deterministic)
- <assert exact text in output>
- <regex match on output file>

### Qualitative (LLM-judged)
- <criterion phrased as a yes/no question for the judge>

## Pass threshold
<N> of <M> structural checks + <P> of <Q> qualitative checks.
```

## Adding a new eval

1. Pick the next sequential number in the folder.
2. Write the markdown file following the format above.
3. Add a short row to this README's "Index" table below.
4. Run it locally; commit only after it passes (or document why it currently fails).

## Index — prd-docs

| # | Name | Measures |
|---|---|---|
| 01 | terminologies-autofill | Research-glossary merge + LLM scan; no hallucinations |
| 02 | architecture-flows-prompting | Right prompting for flow-heavy vs trivial features |
| 03 | story-types-rewrite | new/enhancement/existing assignment for rewrites |
| 04 | walk-order | Terminologies deferral, §5 placement, story-coverage trigger |
| 05 | end-to-end-render | TOC, sections, Type labels, mermaid in final prd.html |
