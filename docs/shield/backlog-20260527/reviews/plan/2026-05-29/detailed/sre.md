# SRE / Operations — Detailed Findings

> Back to [summary](../summary.md)

**Persona grade: A−.** Operationally mature: all four prior SRE findings landed with verbatim fidelity; failure-mode analysis is genuinely strong (safe-failure direction is explicit and testable). Remaining risk is concentrated in the N4 recovery path.

## Prior-finding verification

| Finding | Landed? | Sufficient? |
|---|---|---|
| OP1 — log every removal with rationale `{entry id, feature, epic, match-kind, triggering run, gating plan.json path}` | Yes (TRD §5 F9, EPIC-3-S2, lld-reconciler §10) | Yes — elevated to single integrity surface (TRD §9) |
| OP7 — kill switch | Yes (TRD §5 F10, §14, EPIC-3-S3, lld-reconciler §9) | Mostly — see P2-1: a single boolean disables **both**; "independently" is not actually delivered |
| OP4 — uncommitted-state recovery gap | Yes (TRD §6 N4, §9, §14, EPIC-3-S3, lld-reconciler §8) | Yes for eager path; see P1-1 — the OR is unresolved |
| OP2/OP5 — N2 latency instrumented | Yes (TRD §6 N2, EPIC-3-S3, lld-reconciler §10/§12.4) | Yes — wired to a §14 rollback trigger |

## Evaluation points (A–F)

| # | Point | Grade |
|---|---|---|
| OP1 | Observability plan | A |
| OP2 | Monitoring & alerting | B |
| OP3 | Failure mode analysis | A |
| OP4 | Backup & recovery | B+ |
| OP5 | Capacity planning | A− |
| OP6 | Change management | A |
| OP7 | On-call readiness | B+ |

## Findings

| Priority | Point | Recommendation |
|---|---|---|
| P1 | OP4 (P1-1) | N4 recovery mechanism is an unresolved OR with divergent semantics (commit-before-prune → `git revert`, vs removed-log → replay). The §14 runbook can't be written precisely. Pick one v1 default — recommend removed-log (avoids forcing a possibly-dirty-tree commit on every prune; decouples recovery from git state, which matters mid-`/implement`). Make the other an explicit non-goal; update EPIC-3-S3 AC + §14 step 2. |
| P2 | OP7 (P2-1) | Kill switch doesn't disable triggers "independently" — one coupled boolean. Drop the "independently" framing (coupled is the right v1 scope) or split into `auto_reconcile.eager`/`.lazy`. |
| P2 | OP2 (P2-2) | Wrong-removal detection is pull-only (operator must read the log). Have `/backlog view` surface "N entries removed since last view (see backlog-removed.log)" when the log grows. |
| P2 | OP4 (P2-3) | Removed-log lifecycle undefined (git-tracked vs gitignored, rotation, max size). Specify — and the tracked/ignored choice ties to P1-1. |
| P2 | OP7 (P2-4) | EPIC-4-S2 AC lists feature docs for SKILL.md but not the recovery procedure. Add: SKILL.md documents wrong-removal recovery (flip kill switch → locate F9 log line → revert/replay). |
| P2 | OP7 (P2-5) | Audit interval still "e.g. monthly" — commit to an actual interval. |
| P2 | OP1 (P2-6) | Specify no-op eager prune logging (if lazy sweep beat it): "no-op prune emits no log line" to avoid duplicate recovery records. |

No P0 findings.
