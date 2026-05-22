# PRD Review Dispatch Registry

The 14 dispatch entries used by `/prd-review`. Replaces the persona-keyed table that lived in
`personas.md` (deleted in EPIC-3-S1). Each entry tells the orchestrator HOW to dispatch and
which rubric dim the returned grades roll up to.

## Registry

| Dim | Dim name | Owning persona | Dispatch type | Dispatch target | Persona weight |
|---|---|---|---|---|---|
| 1 | Problem clarity | product-manager | skill-internal prompt | `prompts/problem-clarity.md` (general-purpose Agent) | 1.0 |
| 2 | Scope boundaries | product-manager | skill-internal prompt | `prompts/scope-discipline.md` | 1.0 |
| 3 | Measurable success | product-manager | skill-internal prompt | `prompts/measurable-success.md` | 1.0 |
| 4 | Scenario coverage & AC | agile-coach | legacy persona | `shield:agile-coach` | 1.0 |
| 5 | NFR coverage | tech-lead | legacy persona | `shield:architect` (shares dispatch with dim 6) | 1.0 |
| 6 | Rollout & ops | tech-lead | legacy persona | `shield:architect` (shares dispatch with dim 5) | 1.0 |
| 7 | RACI & approvals | product-manager | skill-internal prompt | `prompts/raci-and-approvals.md` | 1.0 |
| 8 | Legal / privacy / compliance | product-manager | skill-internal prompt | `prompts/legal-privacy-compliance.md` | 1.0 |
| 9 | GTM / customer-comms | product-manager | skill-internal prompt | `prompts/gtm-customer-comms.md` | 1.0 |
| 10 | Support / CX impact | product-manager | skill-internal prompt | `prompts/support-cx-impact.md` | 1.0 |
| 11 | Why now & cost-of-inaction | product-manager | skill-internal prompt | `prompts/why-now-cost-of-inaction.md` | 1.0 |
| 12 | Risks & assumptions | product-manager | skill-internal prompt | `prompts/risks-and-assumptions.md` | 1.0 |
| 13 | Cost & resource impact | finops-analyst | legacy persona | `shield:finops-analyst` | 0.7 |
| — | Anti-patterns (cross-cutting) | dx-engineer | legacy persona | `shield:dx-engineer` | 0.7 |

Total: 14 entries. 9 skill-internal prompts (all owned by `product-manager` persona) +
5 legacy-persona rows that resolve to 4 unique dispatches (`shield:architect` is shared by
dim 5 and dim 6 — one dispatch returns both dim-blocks).

## Dispatch type semantics

- **skill-internal prompt** — the orchestrator reads the file at `shield/skills/general/prd-review/<target>`
  and passes its content as the system+user prompt to a `general-purpose` Agent. The agent returns
  a single dim-block JSON (see `output_shape` in each prompt). This is Pattern B from the
  pm-restructure-v0 handoff.
- **legacy persona** — the orchestrator dispatches the named subagent via `subagent_type: <agent-id>`
  using the prompt skeleton from the deprecated `personas.md` (kept inline in SKILL.md). The agent
  returns a per-persona JSON envelope wrapping one or more dim-blocks. Pattern A.

## Aggregation

The orchestrator collects dim-blocks from all dispatches — regardless of envelope shape — and
groups them by owning persona (using the "Owning persona" column above) before applying the
composite + P0-gate rules in `scoring.md`. Anti-patterns roll into `summary.md`'s anti-patterns
section, not into a numeric dim.

## Dispatch order

All 14 entries are dispatched in parallel from a single response (4 unique agent invocations:
9 general-purpose Agents loaded with the PM prompts, `shield:agile-coach`, `shield:architect`,
`shield:dx-engineer`, `shield:finops-analyst` — 13 parallel calls total).

## Persona weights (used by scoring)

| Persona | Weight |
|---|---|
| `product-manager` (rolled up from dims 1, 2, 3, 7, 8, 9, 10, 11, 12) | 1.0 |
| `agile-coach` (dim 4) | 1.0 |
| `tech-lead` (dims 5, 6) | 1.0 |
| `dx-engineer` (anti-patterns) | 0.7 |
| `finops-analyst` (dim 13) | 0.7 |

Persona weights are unchanged from the pre-restructure `personas.md` table — only the
PM dispatch shape has changed (9 focused prompts instead of one omnibus persona prompt).

## See also

- `rubric.md` — eval points + severity per dim
- `scoring.md` — A-F → composite + P0-gate (accepts both envelope shapes)
- `prompts/*.md` — the 9 skill-internal PM prompts
- The 4 legacy persona agents live in `shield/agents/` and retain their existing prompts
  for v0 (decomposition deferred to v1)
