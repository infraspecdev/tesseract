---
description: "Run a quick Atmos component hygiene check (conventions, file layout, baseline variables)"
disable-model-invocation: true
---

# Hygiene Review

Run a quick Atmos component hygiene check against the current repository.

## Process

1. Invoke the `infra-review:atmos-component-hygiene` skill
2. Run all repository-level checks (R1-R8) and per-component checks (C1-C10)
3. Present results in the standard hygiene check output format
4. Write results to `claude/infra-review/hygiene-review.md` in the repository root

This is a lightweight, fast check — no agent dispatch needed. Just run the skill checklist directly.
