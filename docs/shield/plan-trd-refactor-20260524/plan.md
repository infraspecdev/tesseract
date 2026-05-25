# Plan — `/plan` TRD refactor

**Feature:** `plan-trd-refactor-20260524` · **Phase:** v1 cutover · **Source:** [`research.md`](./research.md) · [`plan-architecture.md`](./plan-architecture.md)
**Sidecar:** [`plan.json`](./plan.json) (schema v1.1)

## Milestones

| ID | Name | Outcome | Depends on |
|---|---|---|---|
| **M1** | TRD cutover | `/plan` emits `trd.md` (14 sections, stable anchors, domain-aware prompting for backend/infra); `plan.json` carries optional `design_refs[]`; eval coverage in place for both domains. | — |
| **M2** | Review + sync wiring | `/plan-review` grades against 14-section rubric (with `n/a — <reason>` escape) + duplication rule; `/pm-sync` adapters forward `design_refs[]` as web links. | M1 |
| **M3** | Drift + duplication hardening | `last_aligned_with` metadata + implementation-manual lint rule. | M2 |

---

## EPIC-1 · TRD generation and storage  ·  M1

### EPIC-1-S1 · Author the canonical 14-section TRD template with domain-aware prompting  ·  `priority: high`

Encode the 14-section TRD template (Document Overview through Rollback Strategy) in `plan-docs/SKILL.md` or a sibling `templates.md`. Each section has TWO authoring-guidance paragraphs: one for backend interpretation, one for infra interpretation. Sections that may not apply to one domain are documented with the `n/a — <reason>` escape pattern from the LLD sample's §12. Each section header in the emitted markdown carries an explicit `{#section-id}` kebab-case anchor.

**Tasks**
- Add a 'TRD template' subsection to `shield/skills/general/plan-docs/SKILL.md` (or extend `templates.md`) listing all 14 section titles, slug IDs, and per-domain authoring guidance sourced from `research.md §What the Industry Recommends`.
- Define the canonical slug allow-list: `['document-overview','problem-statement','objective-scope','product-journey','functional-requirements','non-functional-requirements','high-level-design','alternatives-considered','cross-cutting-concerns','milestones','apis-involved','open-questions','references','rollback-strategy']`.
- Document the explicit `{#section-id}` markdown-anchor convention used by `/plan` output.
- Document the `n/a — <reason>` escape: any section may declare `n/a — <reason>` when it genuinely doesn't apply (typical use: §4 on pure-infra plans). Vague TBDs and silent omissions are not allowed.
- Per-section domain guidance must explicitly call out where the infra interpretation differs from backend (notably §4, §5, §6, §7, §11, §14).

**Acceptance criteria**
- `shield/skills/general/plan-docs/SKILL.md` (or `templates.md`) contains the 14-section TRD template with slug IDs and per-domain authoring guidance.
- The slug allow-list is published as a machine-readable list (YAML or JSON sidecar under `shield/schema/`) so the eval can import it; the list has exactly 14 entries.
- A reader following `plan-docs/SKILL.md` can identify which section a given heading belongs to AND which domain interpretation applies, without re-reading `research.md`.
- The `n/a — <reason>` escape pattern is documented with at least one worked example per applicable section.

### EPIC-1-S2 · Update /plan to emit trd.md (unified backend + infra)  ·  `priority: high`

Modify `shield/commands/plan.md` and `shield/skills/general/plan-docs/SKILL.md` so `/plan` writes `trd.md` with all 14 sections for **both backend and infrastructure features**. Stop emitting `plan-architecture.md` going forward. Direct cutover: no feature flag, no side-by-side period. The generation prompt detects the dominant domain and surfaces the right per-section authoring guidance (backend vs infra) for the LLM.

**Tasks**
- Replace the 'Generate plan-architecture.md' step in `shield/commands/plan.md` with 'Generate trd.md per the unified 14-section template'.
- Update `shield/skills/general/plan-docs/SKILL.md` generation prompt to walk the 14 sections, select the domain-appropriate authoring guidance per section, and emit explicit `{#section-id}` anchors.
- Domain detection: reuse the existing detection (`*.tf` / `atmos.yaml` / `Chart.yaml` → infra; `pom.xml` / `pyproject.toml` / `package.json` / `go.mod` → backend). Mixed → annotate per section.
- Update `shield/schema/output-paths.yaml`: replace `plan_arch_md` with `plan_trd_md` (`{output_dir}/{feature}/trd.md`) and `plan_arch_html` with `plan_trd_html` (`{output_dir}/{feature}/outputs/trd.html`). Mirror in `shield/commands/plan.md` outputs: frontmatter.
- Update the render-markdown helper invocation in `plan-docs/SKILL.md` to render `trd.md` to `outputs/trd.html`.

**Acceptance criteria**
- Running `/plan` in a fresh feature folder writes `docs/shield/{feature}/trd.md` and `docs/shield/{feature}/outputs/trd.html`.
- `/plan` no longer writes `plan-architecture.md` anywhere.
- `shield/schema/output-paths.yaml` lists `plan_trd_md` and `plan_trd_html`; `plan_arch_md` and `plan_arch_html` are removed.
- Running `/plan` on a feature folder with only infra markers produces a TRD where the infra interpretation is reflected in §4–7, §11, and §14 prose; sections like §4 may legitimately carry `n/a — <reason>`.
- Running `/plan` on a feature folder with only backend markers produces a TRD where the backend interpretation is reflected in §4–7, §11, and §14 prose.

### EPIC-1-S3 · Update existing-feature behavior on re-run  ·  `priority: medium`

When `/plan` is re-run in a feature folder that has both an old `plan-architecture.md` and a new `trd.md` (or only an old `plan-architecture.md`), make the behavior deterministic: leave old `plan-architecture.md` untouched, write/overwrite `trd.md`. Old folders remain readable; no migration.

**Tasks**
- Add a guard in `plan-docs/SKILL.md` that does not delete `plan-architecture.md` if it exists.
- Document the re-run behavior in `shield/commands/plan.md` ('plan-architecture.md is no longer generated; existing files are left in place').

**Acceptance criteria**
- Re-running `/plan` on a feature folder with an existing `plan-architecture.md` does not delete or modify that file.
- The new `trd.md` is written alongside (or overwrites prior `trd.md`).

---

## EPIC-2 · Story schema and design traceability  ·  M1

### EPIC-2-S1 · Extend plan.json schema with optional design_refs[]  ·  `priority: high`

Add an optional `design_refs[]` array to each story in the `plan.json` sidecar. Shape: `{doc, component?, section_id, anchor_url, label}`. Bump sidecar schema to 1.2; preserve back-compat (missing field is ignored).

**Tasks**
- Edit `shield/skills/general/plan-docs/sidecar-schema.md` to add `design_refs[]` field on the story record with the field shape above.
- Bump version key in the schema example from `'1.1'` to `'1.2'`.
- Document back-compat: 1.1/1.0 sidecars without `design_refs[]` remain valid.
- Add a 'design_refs[] field' subsection explaining the per-field semantics (`doc ∈ {trd, lld, prd}`; `component` for LLD scoping; `anchor_url` stable across heading renames).

**Acceptance criteria**
- `shield/skills/general/plan-docs/sidecar-schema.md` documents `design_refs[]` with version 1.2.
- A `plan.json` with no `design_refs[]` still validates as 1.2.
- A `plan.json` with `design_refs[]` populated validates as 1.2.

### EPIC-2-S2 · Populate design_refs[] when /plan has TRD context  ·  `priority: high`

When `/plan` generates stories, populate each story's `design_refs[]` with a forward link to the TRD section it implements. `lld` refs are emitted as TODO entries until `/lld` lands.

**Tasks**
- Update `plan-docs/SKILL.md` generation prompt: for each story, identify which TRD §7 (HLD), §10 (Milestones), or §11 (APIs Involved) section the story implements, and emit a `design_refs` entry pointing at `trd.md#{section-id}`.
- For LLD references, emit placeholder entries with `doc='lld'`, `component=null`, `anchor_url=null`, `label='TODO: link when /lld <component> lands'`.
- Document the heuristic for picking `section_id` (story title keyword → TRD section anchor).

**Acceptance criteria**
- A `/plan` run on a feature with a `trd.md` emits at least one `design_refs` entry per story pointing at a real `trd.md` anchor.
- Each story has at least one TRD design_ref; LLD refs are emitted as TODO placeholders.
- Re-running `/plan` does not duplicate entries; existing entries are preserved or updated in place.

---

## EPIC-3 · Eval coverage for TRD format  ·  M1

### EPIC-3-S1 · Author positive TRD eval fixtures (backend + infra)  ·  `priority: high`

Create **two** positive fixture `trd.md` files: one for a backend feature (full 14 sections populated with realistic content), one for an infra feature (full 14 sections with realistic content where infra interpretation applies; at least one section uses `n/a — <reason>` to exercise the escape pattern). The positive eval asserts: all 14 anchors present, each section non-empty OR carrying a valid `n/a — <reason>` line, slug allow-list matches.

**Tasks**
- Author `shield/evals/plan-trd/fixtures/positive-backend/trd.md` with all 14 sections (use Bytebite-style fictional feature so content is realistic).
- Author `shield/evals/plan-trd/fixtures/positive-infra/trd.md` with all 14 sections (use a fictional terraform/atmos change — e.g., new VPC module, new Aurora cluster — so content is realistic). At least one section must use `n/a — <reason>` (e.g., §4 Product Journey marked `n/a — declarative state change, no runtime path`).
- Author the corresponding `plan.json` sidecars with `design_refs[]` entries pointing at the fixture `trd.md` anchors.
- Write `shield/evals/plan-trd.yaml` with both positive cases wired.

**Acceptance criteria**
- `shield/evals/plan-trd/fixtures/positive-backend/trd.md` contains all 14 sections with explicit `{#section-id}` anchors.
- `shield/evals/plan-trd/fixtures/positive-infra/trd.md` contains all 14 sections with explicit `{#section-id}` anchors and uses `n/a — <reason>` on at least one section.
- Running the eval on both positive fixtures passes (exit code 0).
- The fixtures are self-contained: no external API calls, no LLM dispatches.

### EPIC-3-S2 · Author missing-section + drift + vague-TBD negative fixtures  ·  `priority: high`

For each of the 14 required sections, author a fixture `trd.md` that omits that section. Add one drift-by-addition fixture (unprompted 15th section). Add one vague-TBD fixture (section present but contents are 'TBD' instead of either real content or `n/a — <reason>`). The eval must fail on each with a named, distinguishable error.

**Tasks**
- For each section in the slug allow-list (14 entries), derive a positive fixture and remove only that section to create a negative fixture under `shield/evals/plan-trd/fixtures/missing-{section-id}/trd.md`.
- Wire each negative fixture into `shield/evals/plan-trd.yaml` with `expected_error` including the missing section's slug.
- Add one drift-by-addition negative fixture under `shield/evals/plan-trd/fixtures/extra-section/`: add an unprompted 15th section; eval fails with 'unexpected section'.
- Add one vague-TBD negative fixture under `shield/evals/plan-trd/fixtures/vague-tbd/`: §6 Non-Functional Requirements contains only 'TBD' (no real content, no `n/a — <reason>`); eval fails with 'vague section content'.

**Acceptance criteria**
- 14 missing-section negative fixtures exist, one per required section.
- Running the eval on each missing-section fixture fails with an error naming the missing section's slug.
- The drift-by-addition fixture fails with an 'unexpected section' error.
- The vague-TBD fixture fails with a 'vague section content' error (distinguishable from missing-section).

### EPIC-3-S3 · Wire eval into CI / RED-GREEN paper trail  ·  `priority: high`

Run the eval before and after the `/plan` command changes land to produce the RED→GREEN paper trail required by CLAUDE.md. Capture both runs in the implementation PR description.

**Tasks**
- Before any `/plan` command changes: run the eval and confirm RED (positive fixture missing `trd.md` → expected fail).
- After `/plan` changes land: run the eval and confirm GREEN (positive fixture passes; all 13 negatives fail with the right error).
- Capture both run outputs in the PR description.

**Acceptance criteria**
- PR body contains a 'RED' section showing the eval failing before the changes.
- PR body contains a 'GREEN' section showing the eval passing positive + failing all 13 negatives with named errors after the changes.
- The eval is invocable via `uv run shield/evals/run.py plan-trd` (or equivalent existing eval runner).

---

## EPIC-4 · /plan-review and /pm-sync wiring  ·  M2

### EPIC-4-S1 · Add 14-section presence rule to /plan-review  ·  `priority: high`

Extend the `/plan-review` rubric to check that `trd.md` contains all 14 required sections with the canonical slug anchors. Sections containing `n/a — <reason>` pass; sections containing only 'TBD' or empty content fail. Report missing or vague sections as Critical severity.

**Tasks**
- Edit `shield/skills/general/plan-review/SKILL.md` to add a 'TRD section presence' rule that imports the slug allow-list (14 entries) and checks each anchor exists in `trd.md`.
- Add a 'TRD section content' rule that, for each section, accepts either real content or a `n/a — <reason>` line; flags 'TBD'/empty.
- Add corresponding eval fixtures under `shield/evals/plan-review-trd/` exercising both rules (positive + missing-section + vague-TBD + n/a-without-reason).

**Acceptance criteria**
- `/plan-review` on a feature folder with a TRD missing any required section reports that section by slug as a Critical finding.
- `/plan-review` on a feature folder with all 14 sections present (including any `n/a — <reason>` escapes) does not flag section presence or content.
- `/plan-review` on a TRD with a section containing only 'TBD' flags it as a vague-content Critical finding.
- `/plan-review` on a TRD with a section containing 'n/a' (no reason) flags it as a missing-reason finding.

### EPIC-4-S2 · Add PRD↔TRD duplication-detection rule to /plan-review  ·  `priority: medium`

Detect when a TRD section verbatim-restates content from the linked PRD. Use a substring-overlap heuristic on §2 Problem Statement and §5 Functional Requirements.

**Tasks**
- Add a 'TRD restates PRD' rule to `/plan-review` that compares `trd.md` §2 + §5 against the linked `prd.md`.
- Define the substring-overlap threshold (e.g., flag if > 80 characters of consecutive verbatim overlap).

**Acceptance criteria**
- A fixture pair where `trd.md` §2 copies `prd.md` problem section verbatim produces a duplication finding.
- A fixture pair where `trd.md` §2 paraphrases or summarizes the PRD problem section does not produce a finding.

### EPIC-4-S3 · /pm-sync emits design_refs[] as web links  ·  `priority: high`

Update `/pm-sync` adapters (Confluence, Jira, ClickUp, Notion) to forward each story's `design_refs[]` entries as web links on the synced task. Confluence/Jira use issue-link affordances; ClickUp uses URL custom field; Notion uses URL property.

**Tasks**
- Edit `shield/commands/pm-sync.md` to describe `design_refs[]` forwarding.
- Update the relevant adapter logic (Python under `shield/adapters/`) for each tool: Confluence remote link, Jira remote-issue-link, ClickUp URL custom field, Notion URL property.
- Adapters that do not understand `design_refs[]` (or have no link affordance) log 'design_refs forwarding skipped — adapter does not support web links' instead of failing.
- Add per-adapter eval fixtures covering both populated and empty `design_refs[]` cases.

**Acceptance criteria**
- Running `/pm-sync` against each of {Confluence, Jira, ClickUp, Notion} forwards `design_refs[]` URLs on the synced task.
- Running `/pm-sync` with an empty `design_refs[]` succeeds with no side effect.
- Adapter fixtures pass in `shield/evals/`.

---

## EPIC-5 · Drift + duplication hardening  ·  M3

### EPIC-5-S1 · Add last_aligned_with metadata to plan.json  ·  `priority: medium`

Add a top-level `last_aligned_with` field on `plan.json` that records the commit SHA of the most recent `/implement` run that closed a story. Countermeasure for undead-doc drift.

**Tasks**
- Bump `plan.json` schema to 1.3 to include `last_aligned_with: string | null`.
- Update `/implement` to write `last_aligned_with = HEAD-sha` after a story status flips to 'done'.
- Document semantics in `sidecar-schema.md`: `null` until first `/implement` run; updated on every subsequent story close.

**Acceptance criteria**
- Fresh `plan.json` has `last_aligned_with: null`.
- After `/implement` closes a story, `plan.json` has `last_aligned_with: <40-char hex sha>`.
- `/pm-sync` surfaces the value in the synced epic description.

### EPIC-5-S2 · Add implementation-manual / pseudo-code lint rule to /plan-review  ·  `priority: low`

Detect TRD §7 (HLD) sections that contain code blocks of more than N lines without an Alternatives Considered rationale within the same section — the 'design doc is really an implementation manual' anti-pattern from `research.md`.

**Tasks**
- Add a 'implementation-manual detection' rule to `/plan-review`.
- Threshold: code block > 20 lines triggers; rule passes if §8 Alternatives Considered is non-empty.
- Eval fixture: TRD with 30-line code block and empty §8 → flagged; TRD with 30-line code block and populated §8 → not flagged.

**Acceptance criteria**
- A TRD with a >20-line code block and an empty §8 produces a finding.
- A TRD with a >20-line code block and a populated §8 does not produce a finding.
- Threshold is documented in the rule's `SKILL.md`.

---

## Out of scope (locked)

| Item | Status |
|---|---|
| `/lld <component>` command | Template locked at 14 sections per [PR #43 sample](https://github.com/infraspecdev/tesseract/pull/43); authoring command is a separate epic. |
| Adapter auto-creation of design-doc pages in Confluence/Notion | v2 enhancement. |
| Structured ClickUp/Notion relationships beyond URL fields | v2 enhancement. |
| Migration tool for existing `plan-architecture.md` | Direct cutover; files stay readable in old folders. |

## Next steps

- `/plan-review docs/shield/plan-trd-refactor-20260524/plan.json` — multi-agent review.
- `/pm-sync docs/shield/plan-trd-refactor-20260524/plan.json --tool <clickup|jira|notion>` — sync to PM tool.
- `/implement` — start with EPIC-3-S1 (positive eval fixture) to anchor the RED → GREEN trail per CLAUDE.md.
