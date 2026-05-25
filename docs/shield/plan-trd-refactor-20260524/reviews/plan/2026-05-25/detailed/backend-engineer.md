# Backend Engineer — Detailed Findings

> Back to [summary](../summary.md)

## Backend Engineer Review (Grade: C+)

**Scope:** Python-touching stories in Shield's own codebase. Primary target: EPIC-4-S3 (adapter changes). Secondary: EPIC-2-S1 / EPIC-5-S1 (schema bumps), EPIC-3-S1/S2/S3 (eval wiring).
**Stack detected:** Python (uv-managed). `pyproject.toml` at `shield/adapters/clickup/`, plus `shield/adapters/sast/*/pyproject.toml`. No framework-specific Python skills yet — agnostic review applies.

### Score Summary

| Evaluation Point | Grade | Rationale |
|---|---|---|
| API design / adapter interface stability (EPIC-4-S3) | **C** | Schema shape locked, but adapter contract (signature, return type, error model, per-tool retry/idempotency) unspecified |
| Schema versioning discipline (EPIC-2-S1, EPIC-5-S1) | **B** | Bumps to 1.2/1.3 with explicit back-compat statements; no formal `$id`/`$schema`, no validator, no rejection of unknown future versions |
| Testing strategy (EPIC-3 + EPIC-4-S3 fixtures) | **B-** | Strong fixture topology for TRD format; per-adapter fixtures only sketched — HTTP-mocking strategy, fault-injection, and idempotency replay absent |
| Framework patterns / uv-based deps (adapter package layout) | **D** | Plan adds adapter logic in `shield/adapters/` for Confluence/Jira/Notion but only `clickup` is a packaged uv module today; no story scaffolds new packages, deps, or test harness |
| Error & observability (adapter failure modes) | **D+** | One log-line described; no structured logging, no partial-failure semantics, no metric/event surface |
| Concurrency & idempotency (sync re-runs, design_refs upserts) | **D** | EPIC-2-S2 mentions "preserved or updated in place"; nothing about idempotent remote-link upsert (Jira/Confluence remote-links can dupe on re-run without externalId) |
| Deployment safety / blast radius (direct cutover) | **C** | Direct cutover acknowledged; rollback path documented; but no kill switch, no canary, and EPIC-1-S2 mutates `output-paths.yaml` keys (consumer-facing contract) |

**Composite: C+** — the plan's *what* is well-shaped; the *how* leaks responsibility to implementation time for the parts that historically cause incidents (adapter idempotency, partial failures, schema validator wiring).

### Detailed Evaluation

#### 1. API design / adapter interface stability — **C**

**What the plan says:**
- EPIC-4-S3 task: "Update the relevant adapter logic (Python under `shield/adapters/`) for each tool: Confluence remote link, Jira remote-issue-link, ClickUp URL custom field, Notion URL property."
- EPIC-4-S3 task: "Adapters that do not understand `design_refs[]` (or have no link affordance) log 'design_refs forwarding skipped — adapter does not support web links' instead of failing."

**Gaps:**
- **No adapter interface contract.** No Python function/method signature for `design_refs[]` forwarding. Without a typed contract, four adapters will drift in shape.
- **No return-type discipline.** `pm-sync` already has a `pm_sync` MCP tool surface (`shield/adapters/clickup/server/tools/sync.py:115`). The plan doesn't say how the new forwarding result threads back into the existing `sync_auto_link` action_log path.
- **The four adapters are heterogeneous on link semantics** — Jira remote-issue-link, Confluence remote-link, ClickUp URL custom-field, Notion URL property. The plan treats them as a single bullet.
- **No idempotency key.** Jira/Confluence remote-links accept a `globalId` precisely so reruns don't duplicate.

#### 2. Schema versioning discipline — **B**

**Strengths:** Two version bumps with explicit back-compat statements. `DesignRef` shape published. `last_aligned_with: string | null` precisely typed.

**Gaps:**
- **No machine-readable JSON Schema.** The sidecar schema lives as prose+jsonc. No validator, no story to add one. This is the inflection point where prose-only schemas drift.
- **No forward-compat policy.** What does `/plan-review` do when it encounters `version: "1.4"` from a future Shield?
- **`doc ∈ {trd, lld, prd}` is an enum** but the plan does not say whether it's enforced. Unknown `doc` should fail validation.
- **`design_refs[]` cardinality.** EPIC-2-S2 says "at least one TRD design_ref per story" — should be lifted into `sidecar-schema.md` as a "minimum 1" constraint.

#### 3. Testing strategy — **B-**

**Strengths:** TRD-format eval matrix genuinely well-designed. 14 missing-section + drift + vague-TBD is right shape and matches CLAUDE.md eval-coverage mandate. "Named, distinguishable error" requirement (EPIC-3-S2 AC) is a sharp testability bar.

**Gaps:**
- **Adapter fixtures are one bullet for four heterogeneous REST APIs.** No mention of `responses`/`vcrpy`/in-memory fake. `shield/adapters/clickup/tests/test_contract.py` already exists — plan should explicitly extend that pattern.
- **No re-run / idempotency test.** EPIC-2-S2 AC says "Re-running /plan does not duplicate entries." Where is the fixture proving this? Same for EPIC-4-S3.
- **No failure-injection fixture for partial-success.** Confluence accepts, Jira 5xxs — does `/pm-sync` exit non-zero? Continue?
- **EPIC-3-S2 AC undercounts negatives.** "14 missing-section" + drift + vague-TBD = 16 total. EPIC-3-S3 says "all 13 negatives fail" — 14 vs 13 inconsistency.

#### 4. Framework patterns / uv-based deps — **D**

This is the weakest point.

- **Only one adapter exists today as a uv package.** Repo has `shield/adapters/clickup/pyproject.toml` and that's it. **There is no `shield/adapters/jira/`, `confluence/`, or `notion/`.** EPIC-4-S3 implies four-tool work but contains zero scaffolding tasks.
- **CLAUDE.md mandates uv-only Python.** Each new adapter needs its own `pyproject.toml` declaring deps like `atlassian-python-api` or `requests`, plus a dev-dep for the test harness. Plan does not name any HTTP-client library.
- **No shared utility module.** Four adapters will need the same `DesignRef` dataclass, the same "skip if no link affordance" decision, and the same logging shape. No `shield/adapters/_common/` story.

#### 5. Error & observability — **D+**

- **One log line ≠ observability.** No log level, no structured fields, no counter/event emission, no partial-failure surface.
- **No error taxonomy.** What happens on malformed `anchor_url`? Adapter 401/403 vs 4xx vs 5xx? Rate-limited?
- **No retry policy.** ClickUp adapter today almost certainly has retry/backoff. Plan doesn't say new adapters inherit it.
- **`action_log` integration.** Existing clickup adapter writes structured records (`action="sync_auto_link"` at `sync.py:319`). EPIC-4-S3 should require a new action type `forward_design_ref` for traceability.

#### 6. Concurrency & idempotency — **D**

- **Upsert semantics undefined.** Jira's remote-issue-link API uses `globalId` for upsert; without one, every `/pm-sync` re-run posts a duplicate. Obvious idempotency key: `globalId = sha256(story_id + anchor_url)`.
- **Confluence content-property** vs **inline-link** distinction — Confluence has multiple "remote link"-shaped affordances and plan does not pick one.
- **No concurrent-sync story.** Two engineers running `/pm-sync` on the same plan — locking or last-write-wins?
- **EPIC-5-S1 last_aligned_with race:** what if `/implement` flips two stories to `done` from concurrent sessions?

#### 7. Deployment safety / blast radius — **C**

**Strengths:** Rollback path explicit. `design_refs[]` and `last_aligned_with` are additive. Pre-refactor folders stay readable.

**Gaps:**
- **`shield/schema/output-paths.yaml` is a consumer-facing contract.** EPIC-1-S2 says "replace `plan_arch_md` with `plan_trd_md`." Header reads "Plugin-owned contract. Consumers should NOT edit." Consumers may depend on the key name. Plan should *add* `plan_trd_md` while keeping `plan_arch_md` deprecated.
- **No kill switch.** "Direct cutover" with eval-shaped safety is reasonable for internal tool — but worth one sentence acknowledging only remedy is revert-the-PR.
- **Cross-PR coupling.** EPIC-2-S1 (schema 1.2) in M1; EPIC-5-S1 (schema 1.3) in M3. If M2 ships and M3 stalls, sidecars stay at 1.2 with no `last_aligned_with` — fine because optional, but plan should affirm.

### Recommendations

#### P0 (block merge of plan into implementation)

**P0-1.** Specify the adapter interface for `design_refs[]` forwarding (EPIC-4-S3). Lock the function signature and idempotency key across all four adapters: `forward_design_refs(task_id: str, refs: list[DesignRef]) -> ForwardResult` with `ForwardResult{created, skipped, errors}`. Each ref produces `sha256(story_id + anchor_url)[:32]` used as `globalId`.

**P0-2.** Add an idempotency test fixture: "Running `/pm-sync` twice in succession on the same plan produces the same remote state — no duplicate remote-links, no duplicate ClickUp custom-field writes."

**P0-3.** Add an adapter-scaffolding story or split EPIC-4-S3 by adapter. Only ClickUp exists as a uv package today. Either split into EPIC-4-S3a/b/c/d each with own scaffold, or add EPIC-4-S0: "Scaffold `shield/adapters/{jira,confluence,notion}/` uv packages with `pyproject.toml`, MCP-server skeleton, `tests/`, and shared `shield/adapters/_common/design_refs.py`."

**P0-4.** Resolve the 14 vs 13 inconsistency across all artifacts.

#### P1 (fix before implementation milestone closes)

**P1-1.** Add a schema-validation story: `shield/scripts/validate_plan.py` using `pydantic` or `jsonschema`, invoked by `/plan-review` and the eval runner.

**P1-2.** Document forward-compat policy in `sidecar-schema.md`.

**P1-3.** Specify the HTTP test harness: "Adapter eval fixtures use `responses` (or `respx`) to mock the remote APIs. No live HTTP. Tests tagged `@pytest.mark.adapter_contract` so they can run in CI without secrets."

**P1-4.** Specify observability shape: one `action_log` entry per ref forwarded with `action='forward_design_ref'`, fields `{story_id, adapter, anchor_url, outcome, idempotency_key}`. Failures emit `forward_design_ref_failed`.

**P1-5.** Add deprecation overlap for `output-paths.yaml`: keep `plan_arch_md` / `plan_arch_html` keys marked `deprecated: true`.

#### P2 (polish, not blocking)

- Concurrent-sync acknowledgement in plan-architecture.md
- Rate-limit handling note per existing adapter posture
- Decide fate of this plan's own `plan-architecture.md` post-M1
