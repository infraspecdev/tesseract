---
name: prioritization-rationale
description: Grade PM4 — is effort-vs-impact considered, dependencies mapped, sequencing justified? Dispatched by `/plan-review`, `/research`, and standalone PM workflows.
persona: product-manager
model: inherit
---

# Prioritization Rationale (PM4)

## Description

Grade ONE PM dimension: does the document explain the SEQUENCE the work happens in, with
effort-vs-impact reasoning and dependencies surfaced? Return a single-check JSON block — no prose.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM4 | Prioritization rationale | Important | The plan sequences work with a stated rationale: effort or impact estimates per phase, named dependencies between phases, justification for why phase N comes before phase N+1. A flat to-do list without sequencing fails. Sequenced phases without rationale grade C-D. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM4",
  "name": "Prioritization rationale",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Important",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
