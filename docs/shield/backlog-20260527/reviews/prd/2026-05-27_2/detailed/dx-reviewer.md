# DX reviewer — detailed report (run _2)

Persona grade: **B** (weight 0.7). Focus: consistency of the re-edited removal model + actionability.

## Anti-patterns
1. **(P1) Residual contradiction — §2 "only when".** Line 23: "the entry is removed **only when** this epic's work appears in `plan.json`." Contradicts the **manual remove** trigger (entries decided-against never hit a plan) added in §5/§6/§9. Leftover from the earlier gate-only model. → Change "only when" → "when", or add "(or removed manually)".
2. **(P1) Capture-from-skill interface undefined.** §8 M1 / §5 require capture "usable from any Shield skill," but the contract an implementer builds against (function/command name, fields) is never defined.
3. **(P2) Eager-removal "transient promotion reference" underspecified.** Line 104 names it but not the mechanism (CLI arg shape, who reads it, what "on success" means). → Pin in `/plan`/TRD.
4. **(P2) Eager-prune vs lazy-sweep overlap.** Line 74 — state both are idempotent (remove-if-present) so an already-pruned entry re-evaluated by the sweep is a no-op.

## Clarity notes (strengths)
- Removal model is now **consistent across §5, §5-mermaid, §6, §8 M3, §9** — the earlier "on /backlog view only" wording is fully gone. The §2 "only when" is the sole residual leftover.
- Proposed-new-epic match key defined + consistent in §2 (l25), §9 (l105), §10 (l128): existing → epic id, new → epic name (names assumed stable).
- "Never remove on doubt" invariant stated consistently in §2/§9/§10 — good defensive-design signal.
- §9 "Still open: feature/epic discovery cost" leaves the read path (open flagged plan.json vs project-level index) unresolved — acceptable open question, but the reconciliation read-cost path isn't fully implementable as-specified.
- Lean NFR/rollout omissions are appropriate; the concurrent-write risk (§10) covers the one hazard that matters for a single-file store.
