# DX reviewer — detailed report

Persona grade: **B** (weight 0.7). Primary output: anti-patterns + clarity notes.

## Anti-patterns

1. **(P1) M3 vs §9 contradiction** — line 95 vs 100. §8 M3 exit criteria says "`/backlog` reconciles on view" (settled); §9 still lists the reconciliation trigger as Open ("on view / end of /plan / both"). A developer can't implement M3 against an unsettled trigger. → Resolve §9 or soften M3.
2. **(P2) "removed automatically" vs user-triggered** — line 70. §6 says entries are "removed automatically," but reconciliation runs on `/backlog` view (a user action), and §6's own non-goal disclaims "automatic surfacing machinery." → Replace with "removed on next `/backlog` view."
3. **(P1) Unfalsifiable success metrics** — line 85. "Majority", "often enough to save manual lookup", "one step" — no numeric thresholds, no measurement source (local JSON, no telemetry). → Specify thresholds + how measured.
4. **(P1) `kind` field undefined but assumed settled** — line 102. §6/M1 commit to "epic/story/task granularity" and M1 says "schema defined", but the backing `kind` field is open in §9. → Decide before M1.
5. **(P1) Capture-from-skill interface undefined** — line 93. M1 requires capture "usable from any Shield skill" but no command/API/write-contract is specified. → Define the capture entrypoint.
6. **(P1) Reconciliation match key unspecified for proposed-new epics** — line 25. With id-stamping removed, matching relies on feature + epic identity, but the PRD never defines how a proposed-new epic name maps to the eventual real epic in plan.json (string match? user confirmation?). This is the central removal-correctness decision, left implicit. → Specify the match key.

## Clarity notes (strengths — keep)
- Problem-first ordering: §3 problem before §5 solution.
- §2 Terminologies strong and internally consistent on the post-edit model (manifest = key, epic = gate, no ids) — reuse verbatim in the plan.
- The feature-association = reconciliation key / epic-association = removal gate distinction (lines 22-23) is load-bearing and well-defined — keep prominent.
- §9 open questions are honest, but three (reconciliation trigger, `kind`, ordering) gate M1/M3 — resolve or defer-with-default before `/plan`.
- Non-goals (§6, §10) thorough, each with rationale.
- Lean exemption footer is explicit and correct — do not flag NFR/rollout/cost omissions as gaps.
