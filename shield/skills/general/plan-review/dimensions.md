# Plan Review Dispatch Registry

The dispatch registry used by `/plan-review` after the pm-restructure-v0 cutover. The PM
persona is now decomposed into 10 focused global subagents (PM1-PM10); all other personas
retain their legacy dispatch path. Use this registry alongside `personas.md`, which still
controls the dynamic selection flowchart.

## PM persona — decomposed into 10 global dim subagents (Pattern A)

When the dynamic-selection flow includes the PM persona, dispatch ALL 10 of these in parallel
(instead of one omnibus `shield:product-manager` call). Each carries `persona: product-manager`
frontmatter so the orchestrator can roll them back up under the PM persona for `summary.md`
aggregation.

| Dim | Dim name | Subagent | Severity |
|---|---|---|---|
| PM1 | User impact clarity | `shield:user-impact-clarity` | Critical |
| PM2 | Problem-solution fit | `shield:problem-solution-fit` | Critical |
| PM3 | Scope discipline (plan) | `shield:scope-discipline-of-plan` | Important |
| PM4 | Prioritization rationale | `shield:prioritization-rationale` | Important |
| PM5 | Stakeholder communicability | `shield:stakeholder-communicability` | Important |
| PM6 | Market / competitive awareness | `shield:market-competitive-awareness` | Warning |
| PM7 | Adoption & rollout risk | `shield:adoption-rollout-risk` | Important |
| PM8 | Success metrics | `shield:success-metrics-defined` | Important |
| PM9 | Reversibility & exit cost | `shield:reversibility-exit-cost` | Warning |
| PM10 | Business value alignment | `shield:business-value-alignment` | Critical |

PM11 (`shield:framing-coverage-honored`) is intentionally NOT in this list — it applies only
to Research-Review, not Plan-Review.

Each subagent returns a single-check JSON object (id, name, persona, grade, severity,
evidence_quote, gap, suggestion). The orchestrator collects these into a synthetic PM
per-persona block with `persona_grade` computed by averaging the 10 PM dim grades numerically
per `scoring.md`.

## Legacy persona dispatches (unchanged from `personas.md`)

These continue to dispatch as full persona agents — they are not decomposed in v0.

| Persona | Subagent | Weight | Notes |
|---|---|---|---|
| Architect | `shield:architect` | 1.0 | Service topology, scalability, HA, HLD adequacy (C4 level + diagrams per `architecture-authoring.md`) |
| Agile coach | `shield:agile-coach` | 0.7 | Story quality, sprint readiness |
| DX engineer | `shield:dx-engineer` | 1.0 | Plan clarity, anti-patterns |
| FinOps analyst | `shield:finops-analyst` | 0.7 | Cost awareness, right-sizing |
| SRE | `shield:sre` | 0.7 | Monitoring, failure modes |
| Platform engineer | `shield:platform-engineer` | 1.0 | K8s, Helm, RBAC, operational readiness |
| Backend engineer | `shield:backend-engineer` | 1.0 | Application code, API design |
| Security engineer | `shield:security-engineer` | 1.0 | Security posture, threat modeling |

Persona weights (used by `scoring.md` composite calculation) are unchanged from `personas.md`.
The PM persona weight is 0.7 — it now applies to the aggregated PM grade rolled up from the
10 dim subagents.

## Dispatch shape per pattern

- **Pattern A — global named subagent (PM1-PM10 and all legacy personas):** dispatch via the
  `Agent` tool with `subagent_type: <name>`, passing the plan doc path as input.
- **Pattern B — skill-internal prompt (not used in plan-review v0):** reserved for future
  decomposition work (architect dim 5/6, agile-coach dim 4 sub-checks, etc.).

## See also

- `personas.md` — dynamic selection flowchart (PM trigger keywords, story-detection, etc.)
- `SKILL.md` — dispatch sequencing and aggregation steps
- `scoring.md` — A-F → composite + verdict rules
- `shield/agents/*` — the PM1-PM10 subagent files
