# Plan (Enhanced) — `/plan` TRD refactor

**Feature:** `plan-trd-refactor-20260524` · **Phase:** v1 cutover · **Source:** [`../../../research.md`](../../../research.md) · [`../../../plan-architecture.md`](../../../plan-architecture.md)
**Sidecar:** [`../../../plan.json`](../../../plan.json) (schema v1.1)
**Review applied:** [summary.md](summary.md) (composite B; 6 P0 + 15 P1 + 18 P2 recommendations)

## What changed vs original `plan.md`

Six P0 fixes and the most consequential P1s have been folded in. Specifically:

- **P0-1 fixed:** "13" purged from all artifacts; EPIC-3-S3 AC now correctly references 16 negatives (14 missing-section + 1 drift + 1 vague-TBD)
- **P0-2 fixed:** **new EPIC-4-S0** added — adapter package scaffolding (Jira/Confluence/Notion don't exist as `uv` packages today; only ClickUp does). EPIC-4-S3 now consumes that scaffolding rather than implying it
- **P0-3 fixed:** EPIC-4-S3 now specifies the **`forward_design_refs(task_id, refs) → ForwardResult`** contract and the `globalId = sha256(story_id + anchor_url)[:32]` idempotency key
- **P0-4 fixed:** **new AC in EPIC-4-S3** — "Running `/pm-sync` twice in succession produces the same remote state"
- **P0-5 fixed:** EPIC-3-S3 renamed to "Wire eval into recurring CI + RED→GREEN paper trail" with an explicit `.github/workflows/` task
- **P0-6 fixed:** EPIC-1-S2 now defines "Mixed → annotate per section" with a worked example; **EPIC-3-S1 adds `positive-mixed/` fixture**

P1s addressed inline:
- EPIC-2-S2 section_id heuristic (P1-1) and merge semantics (P1-2) now concretely specified
- EPIC-4-S3 adapter file paths (P1-3) enumerated
- EPIC-1-S2 reconciled — domain detection consults repo markers only; `.shield.json` `plan.template_override` is the override key (P1-5)
- EPIC-4-S1 gets a stale-anchor detection rule (P1-6)
- **New EPIC-2-S3:** JSON Schema validator (P1-7)
- EPIC-4-S3 observability shape spelled out — `action='forward_design_ref'` with structured fields (P1-8)
- EPIC-1-S2 keeps `plan_arch_md`/`plan_arch_html` keys marked `deprecated: true` (P1-9)
- EPIC-1-S2 gets a provenance-stamp AC (P1-10)
- **New EPIC-1-S4:** version bumps in marketplace.json + pyproject.toml (P1-12)
- EPIC-4-S3 gets a tool-and-access requirements subsection naming test tenants + credential storage (P1-13)
- EPIC-1-S2 gets an atomic-write AC (P1-14)
- `sidecar-schema.md` gets a forward-compat policy paragraph (P1-15)

P2s **deferred** to a follow-up review pass: rollback-trigger language in plan-architecture.md (P1-11 — needs prose addition not a story change), `trd_sha` content hash, `template_version` field, round-trip integration eval, `--dry-run` mode, troubleshooting page, magic-number defenses. See summary.md §P2 for the full list.

---

## Milestones

| ID | Name | Outcome | Depends on |
|---|---|---|---|
| **M1** | TRD cutover | `/plan` emits `trd.md` (14 sections, stable anchors, domain-aware prompting for backend/infra, atomic write, provenance stamp); `plan.json` carries optional `design_refs[]`; schema validator wired; eval coverage for both domains **plus mixed**; recurring CI gate in place. | — |
| **M2** | Review + sync wiring | `/plan-review` grades against 14-section rubric (with `n/a — <reason>` escape) + duplication rule + stale-anchor rule; `/pm-sync` adapters forward `design_refs[]` as web links with idempotent upsert. | M1 |
| **M3** | Drift + duplication hardening | `last_aligned_with` metadata + implementation-manual lint rule. | M2 |

---

## EPIC-1 · TRD generation and storage · M1

### EPIC-1-S1 · Author the canonical 14-section TRD template with domain-aware prompting · `priority: high`

*(unchanged from plan.md — see [plan.md EPIC-1-S1](../../../plan.md#epic-1-s1--author-the-canonical-14-section-trd-template-with-domain-aware-prompting--prioritynbsphigh))*

### EPIC-1-S2 · Update /plan to emit trd.md (unified backend + infra) · `priority: high`

Modify `shield/commands/plan.md` and `shield/skills/general/plan-docs/SKILL.md` so `/plan` writes `trd.md` with all 14 sections for both backend and infrastructure features. Stop emitting `plan-architecture.md`. Direct cutover: no feature flag, no side-by-side period. The generation prompt detects the dominant domain from repo markers (with `.shield.json` `plan.template_override` as the manual override key) and surfaces the right per-section authoring guidance.

**Tasks**
- Replace 'Generate plan-architecture.md' with 'Generate trd.md per the unified 14-section template'.
- Update `plan-docs/SKILL.md` generation prompt to walk 14 sections, select domain-appropriate authoring guidance, emit explicit `{#section-id}` anchors.
- **Domain detection (P1-5):** reuse existing repo-marker detection (`*.tf` / `atmos.yaml` / `Chart.yaml` → infra; `pom.xml` / `pyproject.toml` / `package.json` / `go.mod` → backend). For manual override, read `.shield.json` `plan.template_override` ∈ `{infra, backend, mixed}`. Document this in `shield/commands/plan.md`.
- **Mixed-domain handling (P0-6):** when both infra and backend markers are detected (or `plan.template_override == "mixed"`), the generator prepends `[backend]` and `[infra]` labels to subsection bullets within each section that has divergent interpretations. Worked example: §11 APIs Involved emits a `### [backend] HTTP API contracts` subsection AND a `### [infra] Module interfaces & cloud-API surface` subsection. A `positive-mixed/` eval fixture in EPIC-3-S1 demonstrates the shape.
- **Output-paths deprecation overlap (P1-9):** add `plan_trd_md` (`{output_dir}/{feature}/trd.md`) and `plan_trd_html` (`{output_dir}/{feature}/outputs/trd.html`) to `shield/schema/output-paths.yaml`. Keep `plan_arch_md` and `plan_arch_html` with `deprecated: true` in the entry; remove in M3 or a follow-up PR. Mirror in `shield/commands/plan.md` outputs: frontmatter.
- Update render-markdown helper invocation to render `trd.md` to `outputs/trd.html`.
- **Provenance stamp (P1-10):** the generator emits a top-of-file HTML comment in `trd.md`: `<!-- generated by /plan v{plugin-version} on {YYYY-MM-DD} -->` where `{plugin-version}` is read from `.claude-plugin/marketplace.json`.
- **Atomic write (P1-14):** the generator writes `trd.md.tmp` first, then renames to `trd.md`. If any step fails (template-load error, prompt error, write error), it removes `trd.md.tmp` and surfaces the error message — never leaves a partial `trd.md` behind.

**Acceptance criteria**
- Running `/plan` in a fresh feature folder writes `trd.md` and `outputs/trd.html`.
- `/plan` no longer writes `plan-architecture.md` anywhere.
- `output-paths.yaml` lists `plan_trd_md` and `plan_trd_html`; `plan_arch_md` and `plan_arch_html` are marked `deprecated: true`.
- Running `/plan` on a folder with only infra markers produces a TRD where infra interpretation dominates §4–7, §11, §14.
- Running `/plan` on a folder with only backend markers produces a TRD where backend interpretation dominates the same sections.
- **(P0-6)** Running `/plan` on a folder with both infra and backend markers produces a TRD where divergent sections carry `[backend]` and `[infra]` labeled subsections.
- **(P1-5)** Setting `.shield.json` `plan.template_override` to one of `{infra, backend, mixed}` overrides repo-marker detection.
- **(P1-10)** Emitted `trd.md` carries a `<!-- generated by /plan vX.Y.Z on YYYY-MM-DD -->` comment as the first line after frontmatter.
- **(P1-14)** Killing `/plan` mid-write (e.g., SIGTERM during generation) does not leave a corrupted `trd.md`; only `trd.md.tmp` may remain and is removed on next invocation.

### EPIC-1-S3 · Update existing-feature behavior on re-run · `priority: medium`

*(unchanged from plan.md)*

### **EPIC-1-S4 · Bump plugin version per CLAUDE.md mandate · `priority: high`** *(new — P1-12)*

CLAUDE.md "Plugin isolation / Versioning" requires bumping `.claude-plugin/marketplace.json` and `pyproject.toml` in the same commit as any plugin update. The TRD refactor is silent on this; add the bump here.

**Tasks**
- Bump `.claude-plugin/marketplace.json` `version` field for the Shield plugin entry.
- Bump `pyproject.toml` version in any package modified (`shield/adapters/clickup/pyproject.toml`, plus new adapter packages from EPIC-4-S0).
- Update Shield's user-facing CHANGELOG (or create one if absent) noting the cutover from `plan-architecture.md` to `trd.md`.

**Acceptance criteria**
- The M1 PR includes both version bumps in the same commit as the SKILL.md changes.
- CHANGELOG mentions the cutover and the schema 1.1 → 1.2 bump.

---

## EPIC-2 · Story schema and design traceability · M1

### EPIC-2-S1 · Extend plan.json schema with optional design_refs[] · `priority: high`

Add an optional `design_refs[]` array to each story in the `plan.json` sidecar. Shape: `{doc, component?, section_id, anchor_url, label}`. Bump sidecar schema to 1.2; preserve back-compat.

**Tasks**
- Edit `sidecar-schema.md` to add `design_refs[]` field on the story record.
- Bump version key in schema example from `'1.1'` to `'1.2'`.
- Document back-compat: 1.1/1.0 sidecars without `design_refs[]` remain valid.
- **(P1-15)** Add a **forward-compat policy** subsection to `sidecar-schema.md`: when `/plan-review` encounters `version > current`, it warns but does not reject; unknown top-level keys are preserved on round-trip; unknown `doc` enum values fail validation.
- Add a 'design_refs[] field' subsection with per-field semantics (`doc ∈ {trd, lld, prd}`; `component` for LLD scoping; `anchor_url` stable across heading renames).
- **(P2-6)** Add an inline example `design_refs[]` JSON instance (one TRD ref + one LLD placeholder).

**Acceptance criteria**
- `sidecar-schema.md` documents `design_refs[]` with version 1.2 and a forward-compat policy.
- A `plan.json` with no `design_refs[]` still validates as 1.2.
- A `plan.json` with `design_refs[]` populated validates as 1.2.
- An inline example is present in the schema doc.

### EPIC-2-S2 · Populate design_refs[] when /plan has TRD context · `priority: high`

When `/plan` generates stories, populate each story's `design_refs[]` with a forward link to the TRD section it implements.

**Tasks**
- Update generation prompt: for each story, emit at least one `design_refs` entry pointing at a real `trd.md#{section-id}` anchor.
- **(P1-1) Section-ID selection heuristic:** lowercase the story's `name`, tokenize on whitespace and punctuation, score each TRD section anchor slug by token-overlap count (Jaccard similarity), pick the highest-scoring slug. Tie-break by section order (lower § number wins). If no token overlaps with any slug, fall back to §7 `high-level-design`.
- For LLD references, emit placeholders with `doc='lld'`, `component=null`, `anchor_url=null`, `label='TODO: link when /lld <component> lands'`.
- **(P1-2) Re-run merge semantics:** on `/plan` re-run, match existing `design_refs[]` entries by `(doc, section_id, component)` tuple. If found: replace `label` and `anchor_url` if changed, never duplicate. If a stored entry no longer has a matching TRD section (anchor deleted), preserve it but mark `stale: true`. New refs append.

**Acceptance criteria**
- A `/plan` run on a feature with `trd.md` emits at least one `design_refs` entry per story.
- Each story has at least one TRD `design_ref`; LLD refs are TODO placeholders.
- **(P1-1)** Story name "Implement POST /users endpoint" resolves to `section_id: "api-create-user"` if that anchor exists, else `high-level-design`.
- **(P1-2)** Running `/plan` twice on the same plan does not duplicate `design_refs[]` entries — verified by an eval fixture.
- **(P1-2)** Deleting a TRD section between `/plan` runs results in the matching `design_refs[]` entry being marked `stale: true` (rather than removed).

### **EPIC-2-S3 · Add JSON Schema validator for plan.json · `priority: high`** *(new — P1-7)*

Two version bumps (1.1 → 1.2 → 1.3) without a machine-readable validator is the drift inflection. Add it now.

**Tasks**
- Create `shield/scripts/validate_plan.py` using `pydantic` (preferred — already in the deps tree via clickup adapter) or `jsonschema`.
- Schema definition lives at `shield/schema/plan-sidecar.schema.json` (machine-readable counterpart to `sidecar-schema.md`).
- Validator is invoked by `/plan-review` (first check) and the eval runner (in EPIC-3).
- Reject unknown `doc` enum values, enforce `design_refs[]` cardinality (min 1 per story when populated), reject unknown sidecar versions newer than current.

**Acceptance criteria**
- `uv run shield/scripts/validate_plan.py <path>` exits 0 on valid sidecars and non-zero with a named error on invalid ones.
- `/plan-review` invokes the validator before applying rubric checks and aborts on schema failure.
- Sidecar version forward-compat behavior matches the policy in `sidecar-schema.md` (warn on `> current`, accept-with-ignored-unknown-keys).

---

## EPIC-3 · Eval coverage for TRD format · M1

### EPIC-3-S1 · Author positive TRD eval fixtures (backend + infra + mixed) · `priority: high`

Create **three** positive fixture `trd.md` files: backend, infra, **and mixed** (P0-6). The infra fixture uses `n/a — <reason>` on at least one section; the mixed fixture uses `[backend]`/`[infra]` labeled subsections on at least §11 APIs Involved.

**Tasks**
- Author `shield/evals/plan-trd/fixtures/positive-backend/trd.md` with all 14 sections (Bytebite-style fictional feature).
- Author `shield/evals/plan-trd/fixtures/positive-infra/trd.md` with all 14 sections (fictional terraform/atmos change). At least one section uses `n/a — <reason>`.
- **(P0-6)** Author `shield/evals/plan-trd/fixtures/positive-mixed/trd.md` with all 14 sections for a fictional feature that has both backend code and an infra component (e.g., a new internal microservice with its own RDS instance). §11 APIs Involved demonstrates the `[backend]` / `[infra]` labeled-subsection shape.
- Author corresponding `plan.json` sidecars with `design_refs[]` entries pointing at fixture `trd.md` anchors.
- Write `shield/evals/plan-trd.yaml` with all three positive cases wired.

**Acceptance criteria**
- All three positive fixtures pass the eval.
- The infra fixture uses `n/a — <reason>` on at least one section.
- The mixed fixture uses labeled subsections on at least §11.
- Fixtures are self-contained (no external API calls, no LLM dispatches).

### EPIC-3-S2 · Author missing-section + drift + vague-TBD negative fixtures · `priority: high`

**(P0-1, P0-4)** For each of the 14 required sections, author a fixture that omits it. Add one drift-by-addition fixture (15th section). Add one vague-TBD fixture. **Total: 16 negative fixtures.**

**Tasks**
- 14 missing-section fixtures under `shield/evals/plan-trd/fixtures/missing-{section-id}/trd.md`.
- 1 drift-by-addition fixture under `shield/evals/plan-trd/fixtures/extra-section/trd.md`.
- 1 vague-TBD fixture under `shield/evals/plan-trd/fixtures/vague-tbd/trd.md` (§6 NFRs contains only 'TBD').
- Wire each into `shield/evals/plan-trd.yaml` with named `expected_error`.

**Acceptance criteria**
- **16 negative fixtures total** exist and fail with the expected named errors.
- Drift fixture fails with 'unexpected section'; vague-TBD fails with 'vague section content'; missing-section fixtures fail with their section's slug in the error message.

### EPIC-3-S3 · Wire eval into recurring CI + RED-GREEN paper trail · `priority: high` *(P0-5, P1-4 — renamed)*

Wire `shield/evals/plan-trd.yaml` into a recurring CI job, not just one-shot PR-body capture. Capture RED→GREEN trail in the implementation PR.

**Tasks**
- **(P0-5)** Create or extend `.github/workflows/eval-plan-trd.yml` (or wire into the existing eval workflow if one exists) that runs `uv run shield/evals/run.py plan-trd` on every PR touching `shield/skills/general/plan-docs/**`, `shield/schema/**`, or `shield/evals/plan-trd/**`.
- Before any `/plan` command changes: run the eval and confirm RED.
- After `/plan` changes land: run the eval and confirm GREEN (3 positives pass; **16 negatives** fail with the right named errors).
- Capture both runs in the implementation PR description.

**Acceptance criteria**
- A GitHub Actions workflow exists that runs the eval on PRs touching the relevant paths.
- The workflow fails the build if the eval reports any fixture mismatch.
- PR body for the M1 cutover contains both RED and GREEN sections, showing **3 positives + 16 negatives** behaving as expected before and after.
- The eval invocation is consistently `uv run shield/evals/run.py plan-trd` (no "or equivalent" hedge).

---

## EPIC-4 · /plan-review and /pm-sync wiring · M2

### **EPIC-4-S0 · Scaffold Jira / Confluence / Notion adapter packages · `priority: high`** *(new — P0-2)*

Only `shield/adapters/clickup/` exists today as a `uv` package. EPIC-4-S3 implies four adapters land in one story but three of them have no `pyproject.toml`, no `tests/`, no MCP server skeleton. Scaffold them first.

**Tasks**
- Create `shield/adapters/jira/` with `pyproject.toml` declaring `requests` (or `atlassian-python-api`) as a dep, `server/` skeleton mirroring clickup's layout, `tests/` directory with a placeholder contract test, and `.mcp.json` entry.
- Same for `shield/adapters/confluence/`.
- Same for `shield/adapters/notion/`.
- Create `shield/adapters/_common/design_refs.py` exposing the `DesignRef` dataclass and the `forward_design_refs` protocol interface (see EPIC-4-S3 for shape).
- Update top-level pyproject if needed to add the new packages to the workspace.

**Acceptance criteria**
- Each new adapter directory has a working `pyproject.toml` resolvable by `uv sync`.
- Each new adapter has a placeholder contract test that runs (and may be skipped) under `uv run pytest shield/adapters/<tool>/tests/`.
- `shield/adapters/_common/design_refs.py` exports `DesignRef`, `ForwardResult`, `ForwardError`, and a protocol/abstract class for `forward_design_refs`.
- `.mcp.json` entries for the new adapters are present (even if disabled until EPIC-4-S3 lands the real logic).

### EPIC-4-S1 · Add 14-section presence rule + stale-anchor rule to /plan-review · `priority: high` *(P1-6 added)*

Extend `/plan-review` rubric to check 14 required sections, the `n/a — <reason>` escape, and **stale `design_refs[]` anchors**.

**Tasks**
- TRD section presence rule (imports 14-entry slug allow-list; checks each anchor exists).
- TRD section content rule (accepts real content or `n/a — <reason>`; flags 'TBD'/empty).
- **(P1-6) Stale-anchor rule:** for each story's `design_refs[].anchor_url`, parse the `#section-id` and assert it exists in the linked `trd.md`. Report mismatches as Critical findings.
- Eval fixtures under `shield/evals/plan-review-trd/` exercising all three rules.

**Acceptance criteria**
- `/plan-review` flags missing sections by slug as Critical.
- `/plan-review` does not flag presence/content for valid TRDs (including `n/a — <reason>`).
- TBD-only sections flag as vague-content Critical.
- `n/a` without reason flags as missing-reason.
- **(P1-6)** A `plan.json` whose story `design_refs[].anchor_url` points at a non-existent anchor in `trd.md` flags as Critical with the offending anchor in the message.

### EPIC-4-S2 · Add PRD↔TRD duplication-detection rule to /plan-review · `priority: medium`

*(unchanged from plan.md)*

### EPIC-4-S3 · /pm-sync emits design_refs[] as web links with idempotent upsert · `priority: high` *(P0-3, P0-4, P1-3, P1-8 added)*

Update `/pm-sync` adapters to forward each story's `design_refs[]` entries as web links on the synced task. Use a deterministic idempotency key to prevent duplicates on re-run.

**Adapter file paths (P1-3):**
- `shield/adapters/clickup/server/tools/sync.py` — extend existing
- `shield/adapters/jira/server/tools/sync.py` — new (per EPIC-4-S0)
- `shield/adapters/confluence/server/tools/sync.py` — new
- `shield/adapters/notion/server/tools/sync.py` — new

**Adapter interface contract (P0-3):**
Each adapter exposes:
```python
def forward_design_refs(task_id: str, refs: list[DesignRef]) -> ForwardResult: ...
```
where `ForwardResult` is `{created: int, skipped: int, errors: list[ForwardError]}`. `DesignRef` and `ForwardResult` are defined in `shield/adapters/_common/design_refs.py` (from EPIC-4-S0).

**Idempotency key:** each `DesignRef` produces `idempotency_key = sha256(story_id + anchor_url)[:32]`. Adapters use this as:
- Jira: the `globalId` field on `remote_issue_link`
- Confluence: the `name` field on `remote_link`
- ClickUp: the comparison key for URL custom field deduplication before write
- Notion: the comparison key for URL property deduplication before write

**Observability (P1-8):** each forwarded ref emits one `action_log` entry with `action='forward_design_ref'`, fields `{story_id, adapter, anchor_url, outcome, idempotency_key}`. Failures emit `action='forward_design_ref_failed'` with `{error_class, http_status, idempotency_key}`.

**Tool & access requirements (P1-13):**
- **Test tenants:** each adapter integration test uses a free-tier sandbox tenant (Confluence Cloud free tier, Jira Cloud free tier, ClickUp free workspace, Notion free workspace) OR uses HTTP mocking via `responses` library (preferred — credential-free CI).
- **Credentials in tests:** when integration tests run live, credentials come from `SHIELD_<ADAPTER>_TOKEN` env vars; CI defaults to mocked mode.
- **Python deps:** Jira → `requests`; Confluence → `requests`; ClickUp → existing `httpx`; Notion → `requests`. All declared in each adapter's `pyproject.toml`.

**Idempotency test (P0-4):**
- Eval fixture under `shield/adapters/<tool>/tests/test_idempotency.py` that runs `forward_design_refs` twice with the same input against a mocked remote and asserts the second call produces 0 `created` and N `skipped`.

**Tasks**
- Edit `shield/commands/pm-sync.md` to describe `design_refs[]` forwarding contract and idempotency key.
- Implement `forward_design_refs` in each of the four adapter files above.
- Adapters that have no link affordance log `'design_refs forwarding skipped — adapter does not support web links'` instead of failing.
- Adapter eval fixtures using `responses` / `respx` HTTP mocking; **plus the idempotency test from P0-4**.

**Acceptance criteria**
- Running `/pm-sync` against each of {Confluence, Jira, ClickUp, Notion} forwards `design_refs[]` URLs on the synced task.
- Running `/pm-sync` with empty `design_refs[]` succeeds with no side effect.
- Adapter fixtures pass in `shield/evals/`.
- **(P0-4)** Running `/pm-sync` twice on the same plan produces no duplicates — verified by per-adapter idempotency test.
- **(P0-3)** All four adapters implement the same `forward_design_refs(task_id, refs) → ForwardResult` signature from `shield/adapters/_common/design_refs.py`.
- **(P1-8)** `action_log` entries are emitted per ref with the documented fields.

---

## EPIC-5 · Drift + duplication hardening · M3

*(unchanged from plan.md — EPIC-5-S1 and EPIC-5-S2 stay as drafted)*

---

## Out of scope (locked)

| Item | Status |
|---|---|
| `/lld <component>` command | Template locked at 14 sections per [PR #43 sample](https://github.com/infraspecdev/tesseract/pull/43); authoring command is a separate epic. Typically backend-only. |
| Adapter auto-creation of design-doc pages in Confluence/Notion | v2 enhancement. |
| Structured ClickUp/Notion relationships beyond URL fields | v2 enhancement. |
| Migration tool for existing `plan-architecture.md` | Direct cutover; files stay readable. |
| `trd_sha` content hash (vs commit SHA) | Deferred (Architect P2). Worth revisiting after M3 ships if `last_aligned_with` proves insufficient. |
| `template_version` field on TRD frontmatter | Deferred (Architect P2). |
| Round-trip integration eval (`/plan` → `/plan-review` no Criticals) | Deferred (Architect P2). |
| `--dry-run` mode for `/plan` | Deferred (SRE P2). |
| `plan-troubleshooting.md` | Deferred (SRE P2). |
| Concurrent `/pm-sync` safety (single-writer note) | Deferred (Backend P2). |
| Magic-number defenses for §8 duplication threshold + §7 implementation-manual threshold | Deferred (Architect P2) — keep as documented constants in EPIC-4-S2 / EPIC-5-S2 tasks. |
| Explicit rollback-trigger statement in plan-architecture.md | Deferred (SRE P1-11) — add to plan-architecture.md in a follow-up commit, not a new story. |

---

## Next steps

After applying this enhanced plan (replacing `plan.md` and updating `plan.json`):

1. **Update `plan.json`** to reflect the structural changes (new stories EPIC-1-S4, EPIC-2-S3, EPIC-4-S0; modified ACs/tasks on EPIC-1-S2, EPIC-2-S2, EPIC-3-S1, EPIC-3-S2, EPIC-3-S3, EPIC-4-S1, EPIC-4-S3). Bump M1 milestone exit criteria.
2. Re-run `/plan-review` and confirm composite ≥ B+ (target: 3.0+).
3. `/pm-sync` to push updated stories.
4. `/implement` starting with **EPIC-4-S0** (adapter scaffolding) or **EPIC-3-S1** (positive eval fixtures) per the RED → GREEN trail.
