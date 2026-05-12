# PRD Templates

The 17-section problem-first scaffold (standard) and 7-section lean variant. Plus the HTML render template that mirrors prd.md.

## Standard scaffold (17 sections)

```markdown
# <Feature name>

## 1. Header
| Field | Value |
|---|---|
| Owner | @<handle> |
| Status | Draft |
| PRD type | Standard |
| Date created | YYYY-MM-DD |
| Last updated | YYYY-MM-DD |
| Linked design spec | <path or null> |
| Linked research | <path or null> |
| Decision-maker | @<handle> |
| Sign-off contacts | Legal: @<handle>, Security: @<handle>, Support: @<handle> |
| Linked plans | _(auto-populated by /plan)_ |

## 2. Problem & context
What's broken, who hurts, baseline data, why now (cost-of-inaction).

## 3. Target users / personas
| ID | Persona | Goals | Frictions today |
|---|---|---|---|
| P1 | <name> | <user-language goals> | <current pain> |

## 4. Goals & non-goals
### Goals
1. <goal 1>
2. <goal 2>
### Non-goals
- <explicitly NOT trying to do>

## 5. Success metrics
| Metric | Type | Target | Counter |
|---|---|---|---|
| <metric> | Leading / Lagging | <numeric threshold> | <counter-metric> |
**Dashboard plan:** <where will this be tracked>

## 6. User stories & scenarios

### Story <ID>: <name>
- **Persona:** <P-id>
- **Goal:** <user-language goal>
- **Happy path:** <numbered steps>
- **Error / timeout / abandon paths:** <branches>
- **Edge cases:** <enumeration>
- **State transitions:** <if applicable>
- **Cross-functional handoffs:** <who/when downstream teams pulled in>
- **Acceptance criteria (Given/When/Then):**
  - Given <pre>, When <action>, Then <outcome>

## 7. Functional requirements
Per-story or per-feature; uses Given/When/Then. May reference Section 6 stories.

## 8. Non-functional requirements
| NFR | Requirement |
|---|---|
| Performance | <budget> |
| Security | <auth model + threat model> |
| Accessibility | <WCAG level> |
| Privacy | <data classification + retention> |
| Telemetry / event taxonomy | <named events> |
| i18n / l10n | <RTL, encoding, formats, translation pipeline — or N/A> |

## 9. RBAC & permissions matrix
| Role | Can do |
|---|---|
| <role> | <permissions> |

## 10. Dependencies
Internal services, third parties, integration contracts.

## 11. Risks & mitigations
| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | <risk> | L/M/H | L/M/H | <mitigation> | @<handle> |

## 12. Assumptions
| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | <assumption> | Validated / Unvalidated | <consequence> |

## 13. Rollout plan
- Flag plan: <feature flag>
- Canary: <staged rollout slices>
- Kill-switch: <criteria>
- Abort thresholds: <specific metric values>
- Data migration: <plan if touching existing data>
- Backward compatibility: <commitments>

## 14. Cost & resource impact
| Component | Cost dimension | Estimate |
|---|---|---|
| Build cost | Engineering time | <estimate> |
| Run cost | LLM / compute / storage / bandwidth | <$X/month at projected scale> |
| Counter-metric | <should not exceed $Y/user/month> | |

## 15. GTM & customer-comms
- Pricing / packaging implications: <description>
- In-app messaging plan: <description>
- Release notes: <description>
- CS / sales enablement: <description>
- Beta / early-access plan: <description or N/A>

## 16. Support / CX impact
- Day-1 ticket owner: @<handle>
- Runbook: <link or description>
- Escalation path: <description>
- Sales enablement: <description>
- Training plan: <description>

## 17. Open questions
| # | Question | Owner | Target resolution |
|---|---|---|---|

## 18. Out of scope / Non-goals
- <named item with one-line rationale>
```

## Lean variant (7 sections)

```markdown
# <Feature name>

## 1. Header
(Same Header table as standard)

## 2. Problem & context
What's broken, who hurts, baseline data, why now.

## 3. Target users / personas
| ID | Persona | Goals | Frictions today |

## 4. Goals & non-goals
### Goals
### Non-goals

## 5. Success metrics
| Metric | Type | Target | Counter |

## 6. Open questions

## 7. Out of scope / Non-goals

---

> **This is a lean PRD.** It intentionally omits the following standard sections:
> - Section 6 — User stories & scenarios
> - Section 7 — Functional requirements
> - Section 8 — Non-functional requirements
> - Section 9 — RBAC & permissions matrix
> - Section 10 — Dependencies
> - Section 11 — Risks & mitigations
> - Section 12 — Assumptions
> - Section 13 — Rollout plan
> - Section 14 — Cost & resource impact
> - Section 15 — GTM & customer-comms
> - Section 16 — Support / CX impact
>
> If scope grows or stakeholders need more detail, run `/prd` again — Shield
> will offer to add specific sections or upgrade to `standard`.
```

## Story template (used inside Section 6 of standard scaffold)

```markdown
### Story <ID>: <name>
- **Persona:** <P-id>
- **Goal:** <user-language goal>
- **Happy path:** <numbered steps>
- **Error / timeout / abandon paths:** <branches>
- **Edge cases:** <enumeration>
- **State transitions:** <if applicable>
- **Cross-functional handoffs:** <who/when downstream teams pulled in>
- **Acceptance criteria (Given/When/Then):**
  - Given <pre>, When <action>, Then <outcome>
```

## HTML render template

The prd.html mirrors prd.md, rendered with Shield's standard CSS conventions:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PRD — <feature name></title>
  <style>
    /* Reuse from plan-docs CSS conventions: */
    :root {
      --accent: #1a73e8; /* Shield blue */
      --bg: #ffffff;
      --text: #1f1f1f;
    }
    body {
      max-width: 900px;
      margin: 0 auto;
      padding: 48px 24px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.6;
      color: var(--text);
      background: var(--bg);
    }
    h1, h2, h3 { color: var(--accent); }
    table { border-collapse: collapse; width: 100%; margin: 14px 0; }
    th, td { padding: 8px 12px; border-bottom: 1px solid #e0e0e0; text-align: left; }
    blockquote { border-left: 3px solid var(--accent); margin: 14px 0; padding-left: 16px; color: #555; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: "JetBrains Mono", monospace; }
  </style>
  <meta name="sidecar" content="prd.meta.json">
</head>
<body>
  <!-- Render each prd.md section here. Convert markdown to HTML via the Bash command:
       pandoc prd.md -o prd.html  (if pandoc available)
       OR manual HTML generation per section if pandoc absent. -->
</body>
</html>
```

**Implementation note:** Shield uses a markdown-to-HTML conversion approach that mirrors `plan-docs`. Reuse that helper rather than re-implementing.
