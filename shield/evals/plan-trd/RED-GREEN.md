# plan-trd eval — RED → GREEN paper trail

This file captures the eval state before and after the `/plan` TRD cutover. It
satisfies the CLAUDE.md "Eval coverage — MANDATORY for plugin updates" rule for
the M1 milestone of the TRD-refactor plan.

## RED (pre-cutover baseline)

Before the cutover, no `trd.md` was emitted anywhere — `/plan` wrote
`plan-architecture.md`. The eval would fail on every positive fixture for the
trivial reason that the file under validation didn't exist. To produce a
reproducible RED that isolates the validator's behavior from the cutover,
strip the §7 high-level-design block from `positive-backend/trd.md` and run the
suite:

```
$ sed -i.bak '/{#high-level-design}/,/{#alternatives-considered}/{/{#alternatives-considered}/!d;}' \
      shield/evals/plan-trd/fixtures/positive-backend/trd.md
$ uv run --with pyyaml --with jsonschema shield/evals/run.py plan-trd --case positive-backend
=== eval suite: plan-trd (19 cases) ===
  FAIL positive-backend
      trd: expected PASS, got exit=1 stderr='FAIL: missing_section:high-level-design'
=== 0/1 cases passed ===
$ mv shield/evals/plan-trd/fixtures/positive-backend/trd.md.bak \
     shield/evals/plan-trd/fixtures/positive-backend/trd.md
```

This proves the validator is sensitive to the property under test
(14-section presence with canonical anchors), not just exit-code noise.

## GREEN (post-cutover)

After the cutover, the full eval suite (3 positives + 16 negatives = 19 cases)
passes with every case meeting its expected outcome:

```
$ uv run --with pyyaml --with jsonschema shield/evals/run.py plan-trd
=== eval suite: plan-trd (19 cases) ===
  PASS positive-backend
  PASS positive-infra
  PASS positive-mixed
  PASS missing-document-overview
  PASS missing-problem-statement
  PASS missing-objective-scope
  PASS missing-product-journey
  PASS missing-functional-requirements
  PASS missing-non-functional-requirements
  PASS missing-high-level-design
  PASS missing-alternatives-considered
  PASS missing-cross-cutting-concerns
  PASS missing-milestones
  PASS missing-apis-involved
  PASS missing-open-questions
  PASS missing-references
  PASS missing-rollback-strategy
  PASS extra-section
  PASS vague-tbd
=== 19/19 cases passed ===
```

## CI gate

`.github/workflows/eval-plan-trd.yml` runs this suite on every PR or push
touching:

- `shield/skills/general/plan-docs/**`
- `shield/schema/**`
- `shield/scripts/validate_trd.py` / `validate_plan.py`
- `shield/evals/run.py`, `shield/evals/plan-trd.yaml`, `shield/evals/plan-trd/**`
- the workflow file itself

The next edit that breaks the 14-section contract — by drift, by renaming an
anchor, by introducing vague TBD content, by removing a fixture — fails CI
before merge.
