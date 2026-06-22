# Architect — Detailed Findings

> Back to [summary](../summary.md)

**Overall persona grade: A-**

Evaluation points reinterpreted for an author-time tooling refactor (markdown skills + YAML contracts + Python scripts), not cloud infra.

| # | Evaluation Point | Grade | Severity | Notes |
|---|-----------------|-------|----------|-------|
| CA1 | Component topology correctness | A | Critical | engine/contract/profile layering correct; dependency direction sound (contracts + profile are leaf sources; engine + scripts depend on them; guard is orthogonal). No cycles in §7 flowchart. |
| CA2 | Change-scalability / amplification | A | Critical | The thesis, rigorously done — blast-radius ceilings quantified per fact class, each asserted by a regression eval; roster-iteration makes adding a dimension/agent O(1). |
| CA3 | High availability | N/A | — | No runtime availability surface. |
| CA4 | Multi-region readiness | N/A | — | No regions; re-skin portability graded under CA8. |
| CA5 | Network design | N/A | — | No network topology. |
| CA6 | Blast radius | A | Important | The unit of analysis: measured baselines, committed ceilings, regression evals; failure-domain isolation via per-milestone revert and M5-last sequencing. |
| CA7 | Mechanism selection | A- | Important | Choices well-justified against §8 alternatives (rejected build-step template, mega-config, script-name registry). Residual: the resolution mechanism itself (how {ns}/{output_dir} resolve at load time) is deferred to a prototype, not designed in §7. |
| CA8 | Profile parity | B+ | Warning | Profile layer (M6) is the parity mechanism (acme vs shield, smoke test asserts zero brand-leak). Under-specified: open question #2 (profile filename + resolution order) gates M6; no statement of what distinguishes a profile from today's .shield.json. |
| CA9 | HLD adequacy (C4) | B | Critical→softened | §7 stays at Container level; both required diagrams present (flowchart + sequenceDiagram with a real failure branch). Gap: the authoring standard wants a `diagram` per milestone, but plan.json has zero — permissible only because the 1.5 sidecar grandfathers `milestone_no_diagram` (enforced at 1.6+). |

**Key finding:** Exemplary architecture plan for a tooling refactor — SSOT design, dependency direction, blast-radius ceilings, guard-eval enforcement all modeled with rigor and backed by regression evals. Substantive gaps: (1) the load-time resolution mechanism the whole design rests on is deferred to a prototype rather than documented in §7; (2) milestone-level diagrams absent (permissible only via the 1.5 grandfather).

## Recommendations
- **P1 (CA7/CA9):** Document the resolution mechanism in §7 (one paragraph) — when does `{output_dir}`/`{ns}`/`{registry-name}` get substituted: harness at skill-load, a preprocessor, or read at agent runtime? M1 should validate a hypothesis, not discover one.
- **P1/P2 (CA9):** Add a per-milestone `diagram` (Mermaid delta of the engine/contract/profile picture each milestone delivers), or bump the sidecar to 1.6 and let the validator enforce it. Shipping at 1.5 to dodge `milestone_no_diagram` dodges the bar.
- **P2 (CA8):** Resolve open question #2 and add one sentence on what a "profile" is relative to today's .shield.json (superset, rename, or new layer above it).
- **P2 (CA7):** State the indirection budget as a checkable rule and consider a guard that flags single-use facts that got externalized (protects against over-rotation in both directions).
