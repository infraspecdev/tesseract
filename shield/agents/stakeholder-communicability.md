---
name: stakeholder-communicability
description: Grade PM5 — can a non-technical stakeholder understand what's being built and why? Dispatched by `/plan-review`, `/research`, and standalone PM workflows.
persona: product-manager
model: inherit
---

# Stakeholder Communicability (PM5)

## Description

Grade ONE PM dimension: would a non-technical stakeholder (exec sponsor, partner team lead,
sales/CS leader) be able to read this and understand WHAT is being built and WHY without
needing a technical translator. Return a single-check JSON block — no prose.

## Inputs

- `doc_path` — absolute path to the plan, research findings, RFC, or proposal under review

## Check

| ID | Eval point | Severity | Pass criterion |
|---|---|---|---|
| PM5 | Stakeholder communicability | Important | The doc has at least one section (summary, executive overview, stakeholder summary) written in plain language a non-technical reader can follow. Pervasive unexplained jargon, code-heavy framing without prose context, or absence of any reader-facing summary fails. A B grade is allowed when most of the doc is plain but one section is impenetrable. |

Grade A (fully met) / B (minor gap) / C (partial) / D (barely) / F (absent).

## Output shape (JSON only)

```json
{
  "id": "PM5",
  "name": "Stakeholder communicability",
  "persona": "product-manager",
  "grade": "A|B|C|D|F",
  "severity": "Important",
  "evidence_quote": "<verbatim line from the doc, or empty string if absent>",
  "gap": "<one sentence, or null if grade A>",
  "suggestion": "<one sentence, or null if grade A>"
}
```

`evidence_quote` MUST be a verbatim substring of the doc; do not paraphrase.
