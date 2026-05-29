# Backend Engineer — Detailed Findings

> Back to [summary](../summary.md)

## Backend Reviewer — Plan Review: Shield Backlog

**Scope:** plan.md, trd.md, plan.json (4 epics / 11 stories / 3 milestones), grounded against `shield/schema/plan-sidecar.schema.json` and `docs/shield/manifest.json`.
**Stack:** Python (uv), JSON-schema deliverables, command/skill markdown. No framework skills apply.

### Scorecard

| # | Evaluation Point | Grade | Basis |
|---|---|---|---|
| 1 | Data contract / schema design | B | `backlog.json` contract is fully specified (§11, F1, EPIC-1-S1): `{schema_version:int, entries:[{id, order:int, kind, source, feature, epic, text}]}`, draft-2020-12, named errors. Gap: `id` has no type/format/uniqueness rule, and the `id` *generation* strategy is undefined (see P1-a). `epic`/`feature` typed only as bare strings with no "proposed-new vs existing" discriminator. |
| 2 | API / interface design | C | The skill-facing write-helper — explicitly the carried-forward PRD-review P1 — is **still open** (Q3: "exact function signature / module location … Resolution: lock in /lld backlog-store or at EPIC-1-S2 implementation"). §11 describes it only as "documented function/contract taking `{text, kind, feature?, epic?, source}`; returns the created entry id." Deferring the *signature* of the one cross-skill contract to implementation time is the central interface risk (P1-b). |
| 3 | File I/O correctness & atomicity (N1) | B | Strong: temp-then-rename + validate-or-refuse, crash leaves at most `.tmp` cleaned next run, git-tracked recoverability (N1, N4, EPIC-1-S2). Gaps: (a) no `fsync`/`os.replace` durability detail — "rename" on POSIX via `os.replace` is atomic but the plan doesn't name the primitive; (b) **no concurrency primitive named** — N1 claims "concurrent capture racing reconciliation must never corrupt" but temp-then-rename alone does not prevent *lost updates* (two writers each read-modify-rename → last-writer-wins drops an entry). No lock/CAS/re-read-under-lock mentioned (P1-c). |
| 4 | Error handling | A | Consistently specified: named validator errors (`unknown_kind_enum`, `missing_required_field`, `schema_version_too_new`), absent-id no-op, empty-backlog message, malformed-upstream → entry-stays-with-log, never-crash (N3, F5, §9). Degradation paths are explicit and testable. |
| 5 | Testing strategy | A | EPIC-4-S1 mandates self-contained executable evals (no API/LLM) under `shield/evals/`, named fixtures (prd-only-stays, plan-committed-removed, ambiguous-stays, malformed-stays), RED→GREEN in PR, CI gate. Directly satisfies CLAUDE.md eval mandate. One missing case: no eval for the **lost-update concurrency** path (ties to P1-c) and none for `schema_version_too_new` migration. |
| 6 | Framework / idiom fit | A | Correct for the repo: uv-run scripts, pydantic+jsonschema, schema at `shield/schema/`, skill at `shield/skills/general/backlog/`, command at `shield/commands/`, version bump in marketplace.json + pyproject (EPIC-4-S2). Matches existing `validate_*`/`reconcile_*` script conventions. |

**Schema-grounding check (read-contract, N3 / §11):** I verified the consumed shapes against the live files. `manifest.json` is `features[].{name, artifacts.{research,prd,plan_json,...}}` — **§11 is accurate.** `plan-sidecar.schema.json` has `epics[].{id (^EPIC-[0-9]+$), name, stories[]}` with `story.status ∈ {ready,in-progress,in-review,done,blocked}` — **§11's `epics[].{id,name,stories[]}` is accurate.** The read-contract claim is correct, which lifts N3 from a guess to a verified coupling. Good.

---

### Prioritized Recommendations

**P1 — Important gaps (C/incomplete on important points):**

- **P1-a · `id` contract underspecified (Eval point 1).** F1 / §11 / the schema task list `id` as a required field but never define its type, format, or **how it's generated**. Manual-remove (`/backlog remove <id>`), promotion (`promote <id>`), and eager-prune all key off `id`, yet uniqueness and collision behavior are unstated. *Action:* in EPIC-1-S1, specify `id` type (string?), generation (uuid4 / monotonic / slug), and a uniqueness constraint in the schema. Add an AC: "schema rejects duplicate `id`."

- **P1-b · Write-helper signature still open is a P0-shaped risk parked as Q3 (EvalPoint 2).** This is the *exact* PRD-review P1 the plan claims to resolve in EPIC-1-S2, but §11 + Q3 punt the signature to "/lld or implementation." Since EPIC-1-S2 is the contract *every capturing skill builds against*, an unspecified signature means downstream skills can't be written or tested against a stable shape. *Action:* lock the helper signature (name, module path, params, return, raise-on-invalid behavior) in EPIC-1-S1/S2 acceptance criteria — not deferred to LLD. At minimum pin: `capture(text, *, kind="task", feature=None, epic=None, source) -> entry_id` and where it lives (`shield/scripts/backlog_store.py`?).

- **P1-c · Atomicity ≠ isolation; lost-update path unaddressed (EvalPoint 3, N1).** N1's threat model is "concurrent capture racing reconciliation." Temp-then-rename guarantees no *torn* file, but two concurrent read-modify-write cycles still silently drop one writer's entry (both read N entries, each writes N+1, second rename wins → one entry lost, no corruption flagged). The plan treats "no corruption" as equivalent to "no data loss." *Action:* name the concurrency strategy — single-writer assumption documented as such, OR a lockfile / re-read-and-merge under exclusive open / `O_EXCL` temp. Add an eval fixture for two interleaved captures. If single-actor is the real assumption (N5 says "single actor"), state it explicitly in N1 and downgrade the "racing reconciliation" language, because eager-prune-at-end-of-/plan can genuinely run while an agent captures.

**P2 — Warnings / minor gaps on B items:**

- **P2-a · "Epic landed" gate is ambiguous (EvalPoint 1/5, F7).** F7 says remove "when its epic's work appears in the feature's `plan.json`," EPIC-3-S2 AC says "whose epic's **stories** appear," but the schema guarantees an epic always has `stories[] (minItems:1)` the moment it's written. So "stories appear" = "epic exists" — meaning an entry is pruned as soon as `/plan` *writes* the epic, regardless of whether any story is `done`. That may be intended (plan-committed = removed) but it's stated three slightly different ways. *Action:* state the gate as one precise predicate, e.g. "epic with matching id/name is present in `plan.json.epics[]`" — and explicitly note story `status` is **not** consulted. Removes reviewer ambiguity and pins the eval assertion.

- **P2-b · Proposed-new "match by epic name" fragility is acknowledged but not bounded (EvalPoint 2).** Match key for proposed-new epics is `epic name` with "names expected stable" as an *unvalidated assumption* (PRD §10). The mitigation (§14: "disable eager prune on repeated name collisions") is reactive. *Action:* add normalization rules to EPIC-3-S2 (case/whitespace-insensitive? exact?) and an AC for the collision case ("two epics same normalized name → ambiguous → entry stays"), which the "ambiguous-stays" fixture should already exercise — wire it explicitly to name-collision, not just structural ambiguity.

- **P2-c · `schema_version` migration is policy-only, no executable path (EvalPoint 1/5).** The read-old/write-new policy is documented but EPIC-1-S1 only validates `schema_version_too_new` (reject). There's no migration *function* or eval for read-old. Acceptable for v1 (only one version exists), but the AC overstates ("migration policy present" = a doc, not code). *Action:* either add a no-op `migrate(doc)->doc` seam now with a test, or explicitly scope migration as doc-only-until-v2 in the AC so it isn't mistaken for working code.

---

### Overall Persona Grade: **B (3.0)**

Average of point grades: (B + C + B + A + A + A) = (3+2+3+4+4+4)/6 = 3.33 → **B**.

The plan is well-grounded — the reconciliation read-contract is *verified accurate* against the live schemas (not assumed), error handling and testing strategy are A-grade, and the atomic-write framing is sound. It is held back from A by two important, named-but-unresolved interface/correctness gaps: the **skill-facing write-helper signature is still open (Q3)** despite being the headline PRD-review carry-forward, and **N1 conflates atomicity with isolation**, leaving the lost-update path under a "single actor" assumption that isn't stated where the threat is described. Resolve P1-b (lock the helper signature in EPIC-1-S1/S2 ACs) and P1-c (name the concurrency strategy + add the interleaved-capture eval) and this is an A.
