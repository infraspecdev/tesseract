# Shield Evals

Two eval systems live here. They test different things and have different cost profiles. **Pick the one that matches what you're testing.**

## Pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com) to gate fast static checks on every commit. Install once after cloning:

```bash
pre-commit install
```

Hooks run automatically on `git commit`. To run them manually:

```bash
pre-commit run --all-files
```

Hooks included: whitespace hygiene, YAML/JSON validity, bash syntax, end-to-end eval format check, and `render-markdown` pytest (only when render-markdown files change). End-to-end and snapshot evals themselves are NOT run in the hook — those belong in CI (see "When to run evals" below if relevant).

---

## Two eval systems: snapshot and end-to-end

| | Snapshot eval | End-to-end eval |
|---|---|---|
| **Runner** | `run-evals.sh` | `run-eval.sh` |
| **Eval files** | `expected/*.yaml` | `<skill>/*.md` (e.g. `prd-docs/*.md`) |
| **What's tested** | A captured agent output (a saved review report) | A skill's effect on subagent behavior, end-to-end |
| **Iteration cost** | Capture once (slow), grade many times (fast) | Every run pays the full subagent-dispatch cost |
| **When to use** | Validating specialist agents (finops-analyst, security-engineer, product-manager) — where each agent run is expensive and you want to iterate on grading criteria without re-running | Validating skill behavior (`shield:prd-docs`, future skills) — where the thing being tested IS how the skill drives a subagent |
| **Inputs** | Pre-existing fixture directory under `inputs/` | Inline bash heredoc in the eval's Setup section |
| **Output capture** | Human-driven (run agent separately, save to `results/<name>.txt`) | Automated (runner dispatches subagent via `claude --print` and captures output) |
| **Assertions** | YAML regex with `must_find` / `should_find` / `must_not_false_positive` | Structural regex (bidirectional must-find) — every assertion matches ≥1 agent file AND every agent file matches ≥1 assertion. Qualitative LLM-judge is *optional*; deterministic evals omit `### Qualitative` and rely on structural alone. |
| **Severity tiers** | `must_find` (FAIL) / `should_find` (WARN) / `must_not_false_positive` (FAIL) | Pass threshold per bucket (e.g. `4 of 4 structural` or `3 of 3 structural + 2 of 3 qualitative`). Coverage check: any unaccounted agent file fails. Derived globals (`manifest.json`, `index.html`, anything under `outputs/`, `changes.md`) are implicitly exempt. |

**Why both exist:** specialist agents (finops-analyst, etc.) produce long reports against complex inputs; re-running them every time you tweak a regex is wasteful. Skills (prd-docs) are tested by *what the subagent does*, which isn't a static artifact — every behavior change needs a re-run.

Mental shortcut:
- Snapshot = "given this captured output, does it satisfy these properties?"
- End-to-end = "does the skill make the subagent do the right thing?"

---

## End-to-end evals (`run-eval.sh`)

For skill-behavior tests. Each eval is a markdown file with Setup + Prompt + Success criteria + Threshold.

### Running

```bash
# Single eval
./shield/evals/run-eval.sh prd-docs/01-terminologies-autofill

# All evals in a folder
./shield/evals/run-eval.sh prd-docs
```

Each eval prints structural and (if present) qualitative pass counts plus a `COVERAGE:` line showing how many agent-written files matched a structural pattern, then `RESULT: PASS|FAIL`. Aggregate summary at the end. Script exits 1 if any eval fails its threshold — usable as a CI gate. An eval fails if any agent-written file is unaccounted for (no structural pattern matches), unless that file is a derived global / side-artifact (`manifest.json`, `index.html`, `outputs/*`, `changes.md`).

### Eval file format

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

### Structural (deterministic, bidirectional must-find)
- <regex assertion — typically a full-path pattern so the coverage check is tight>
- <regex assertion>

### Qualitative (LLM-judged) — OPTIONAL
- <criterion phrased as a yes/no question for the judge>

## Pass threshold
<N> of <M> structural [+ <P> of <Q> qualitative]
```

Omit the `### Qualitative` section entirely for fully deterministic evals; the runner detects the absence and skips the LLM judge. Prefer structural-only when the criteria are expressible as path patterns.

### Adding a new eval

1. Pick the next sequential number in the folder (e.g., `06-…md`).
2. Write the markdown file following the format above.
3. Add a row to the Index table below.
4. Run it locally; commit only after it passes (or document why it currently fails).

### Index — prd-docs

| # | Name | Measures |
|---|---|---|
| 01 | terminologies-autofill | Research-glossary merge + LLM scan; no hallucinations |
| 02 | architecture-flows-prompting | Right prompting for flow-heavy vs trivial features |
| 03 | story-types-rewrite | new/enhancement/existing assignment for rewrites |
| 04 | walk-order | Terminologies deferral, §5 placement, story-coverage trigger |
| 05 | end-to-end-render | TOC, sections, Type labels, mermaid in final prd.html |

### Index — writing-style

| # | Name | Measures |
|---|---|---|
| 01 | tighten-prose | Cuts filler/passive voice, preserves facts, marker-wrapped scope guard |
| 02 | json-sidecar-scope | Tightens prose but leaves embedded JSON code blocks byte-identical |
| 03 | bluf-restructure | Moves a buried conclusion to the front of the paragraph |
| 04 | preserve-tight-prose | Already-tight prose is not over-compressed into cryptic shorthand |
| 05 | concrete-not-vague | Replaces vague claims ("improved significantly") with specific numbers/names from the doc |
| 06 | lld-scope-guards | Tightens LLD §1 prose; preserves provenance stamp, §14 Changelog rows, and `n/a — <reason>` escapes |

---

## Snapshot evals (`run-evals.sh`)

For specialist-agent output validation. The agent is run separately (typically by a human or a one-shot script) against a fixture under `inputs/`; its output is saved to `results/<name>.txt`; then `run-evals.sh` grades the saved report against the YAML criteria at `expected/<name>.yaml`.

### Running

```bash
# All eval criteria
./shield/evals/run-evals.sh

# One criteria file
./shield/evals/run-evals.sh expected/finops-analyst-terraform.yaml
```

If a `results/<name>.txt` is missing, the runner reports `SKIP` and tells you how to populate it. It does NOT invoke the agent itself.

### Workflow

```
1. Pick an eval criteria file:      expected/finops-analyst-terraform.yaml
2. Look up the input fixture:       inputs/insecure-vpc-module/
3. Run the agent (separately):      e.g., /shield:review against the fixture
4. Save the agent's report:         results/finops-analyst-terraform.txt
5. Grade:                           ./run-evals.sh expected/finops-analyst-terraform.yaml
```

### Criteria file format (YAML)

```yaml
agent: finops-analyst
mode: infra-code
input: insecure-vpc-module

must_find:
  - id: <stable-id>
    description: <human-readable>
    match: <regex, case-insensitive>

should_find:
  - id: <stable-id>
    description: <human-readable>
    match: <regex>

must_not_false_positive:
  - id: <stable-id>
    description: <human-readable>
    match_absence_in: <regex that must NOT match>
```

`must_find` failures count as FAIL. `should_find` failures count as WARN. `must_not_false_positive` failures (i.e., a forbidden pattern was found) count as FAIL.

### Adding a new snapshot eval

1. Create the input fixture under `inputs/<name>/` (or reuse an existing one).
2. Write the YAML criteria at `expected/<agent>-<input>.yaml`.
3. Run the agent against the fixture once; save the report to `results/<agent>-<input>.txt`.
4. Run `./run-evals.sh expected/<agent>-<input>.yaml` and confirm PASS.
