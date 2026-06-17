# Shield Artifacts

Everything Shield writes lands under `{output_dir}` (default `docs/shield`, configured per project in `.shield.json`). This page is a contributor-facing map of *what each file is for*. For exact path templates, see `shield/schema/output-paths.yaml`; for schema details, see the per-file schema docs linked below.

## Top-level (one per project)

### `manifest.json`

Inventory of every feature folder under `{output_dir}` — feature names, artifact-presence flags, review counts, last-updated timestamps. Read by `outputs/index.html` to render the project dashboard. Built deterministically from disk by `shield/scripts/migrate_outputs.py:build_manifest()`.

Does NOT contain plan or PRD content. It is a directory index, not state of record — the file system is the source of truth.

- Schema: [`skills/general/manifest-schema.md`](../skills/general/manifest-schema.md)
- Written/refreshed by: every Shield command after writing an artifact

### `outputs/index.html`

Top-level dashboard. Renders `manifest.json` as a card grid linking to every feature's artifacts. Regenerated whenever `manifest.json` changes.

## Per-feature (one per feature folder)

Each feature lives at `{output_dir}/{feature}/`. Source markdown is committed; rendered HTML lands under `outputs/` (build artifact — gitignored; rebuild locally with `/shield render`).

### `research.md`

Captured context for the feature — domain background, prior art, stakeholder voices, source-type coverage matrix. Written by `/research`; consumed by `/prd` and `/plan` as input.

### `prd.md`

Product Requirements Document — problem, users, scope, success metrics, non-goals. Written by `/prd`; consumed by `/plan`, `/prd-review`, and `/implement`.

### `plan.json`

The **plan body** — milestones, epics, stories, tasks, acceptance criteria, `design_refs[]`, and PM tool IDs/URLs. The single source of truth for what gets built and what gets synced. The companion `plan.md` is the human-readable rendering of the same content.

- Written by: `/plan`
- Mutated by: `/pm-sync` (backfills `pm_id`/`pm_url`), `/implement` (updates `last_aligned_with` when stories close)
- Validated by: `/plan-review` and `shield/scripts/validate_plan.py`
- Walked by: `/implement` (story-by-story)
- Schema: [`skills/general/plan-docs/sidecar-schema.md`](../skills/general/plan-docs/sidecar-schema.md) (also `schema/plan-sidecar.schema.json` as JSON Schema)

Contrast with `manifest.json`: `manifest.json` records only that this feature's `plan.json` is present; `plan.json` is where the content lives.

#### Epics vs Milestones — orthogonal grouping axes

Stories belong to **two** independent groupings inside `plan.json`. Epics and milestones are not hierarchical; they answer different questions.

| Concept | Lives in | Answers | Identifier |
|---|---|---|---|
| **Milestone** | `prd.md` §15 + `plan.json.milestones[]` | "What ships when" — roadmap, stakeholder-facing | `M1`, `M2`, `M3` |
| **Epic** | `plan.json.epics[]` only | "What kind of work" — engineering organization, PM-tool friendly | `EPIC-1`, `EPIC-2` |

Every story has both: an implicit parent epic (its position in the JSON tree) AND an explicit `milestone_id` (foreign key to `milestones[].id`). The axes are independent — one epic's stories can span multiple milestones, and one milestone's stories can span multiple epics.

**PRD vs plan asymmetry.** PRDs have milestones (§15) but NOT epics — epics are a plan-layer-only construct. The plan inherits milestones from the PRD (via the milestone-resolution step in `plan-docs/SKILL.md`) and adds epics during work breakdown. PRDs are user/business-facing (milestones map to value delivery); plans are engineering-facing (epics map to work-stream ownership).

**PM-tool mapping.** `/pm-sync` uses the JSON tree to mirror the **epic = parent-task / story = child-task** convention that ClickUp / Jira / Notion expect, while milestones map to sprint labels or release tags. The two-axis split is what makes that mapping clean.

**Validation scope.** `/plan-review` enforces structural rules on milestones (referential integrity of `milestone_id`, ≥ 1 covering story per milestone, DAG check on `depends_on`). It does NOT enforce anything about epics — they're a pure organization tool. An empty epic does not trigger a finding.

### `plan.md`

Markdown rendering of `plan.json` for human readers. Generated alongside `plan.json` by `/plan`. Re-rendered after any `plan.json` mutation (e.g. after `/pm-sync` backfills PM IDs).

### `trd.md`

14-section Technical Requirements Document. Written by `/plan`. Successor to the now-deprecated `plan-architecture.md` (see `schema/output-paths.yaml` `deprecated:` list).

- Schema: section slugs + canonical order at [`schema/trd-sections.yaml`](../schema/trd-sections.yaml); validator at [`shield/scripts/validate_trd.py`](../scripts/validate_trd.py).
- **§10 Milestones is rendered, not hand-written.** Its body is the deterministic output of [`shield/scripts/render_trd_section.py milestones <plan.json>`](../scripts/render_trd_section.py) wrapped between `<!-- BEGIN rendered:milestones … -->` and `<!-- END rendered:milestones -->` markers. `plan.json.milestones[]` is the upstream; §10 is the downstream view. To change a milestone, edit `plan.json` and re-run `/plan` — never hand-edit the rendered region. `validate_trd.py` emits a Critical `milestone_drift` finding if the live region diverges (mirrors `/plan-review` gate 0c stale-anchor severity). Same render seam will fan out to §5 / §7 / §11 in future work.

### `outputs/{prd,plan,trd}.html`

Rendered HTML siblings of the source markdown — local build artifact, gitignored. Rebuild with `/shield render` (regenerates the whole site).

## Reviews

Each review run lives under `{feature}/reviews/{review_type}/{date}{_counter}/` where `{review_type}` is `prd`, `plan`, or `code` and `{date}` is `YYYY-MM-DD`. Same-day reruns get `_2`, `_3`, etc. Runs never overwrite.

### `summary.md`

Top-level review verdict, scorecard, and severity-tiered findings list. Written by `/{type}-review` or `/review`.

### `enhanced-{type}.md`

The reviewed document with inline suggested fixes annotated. The review command offers apply-as-is / apply-with-edits / skip at the end.

### `detailed/{agent}.md`

Per-agent detailed findings. One file per reviewer dispatched (e.g. `architect.md`, `backend-engineer.md`).

### `source-{type}.md`

Frozen copy of the source artifact (e.g. the PRD as reviewed). Lets reviewers see the exact state at review time even after the source evolves.

## Project-internal QA

These artifacts are not Shield outputs — they're tesseract-repo contributor
tooling that runs locally during development. They don't ship with the Shield
plugin and don't land under `{output_dir}`.

### `.claude/hooks/check-doc-drift.py` + `.claude/hooks/doc-drift-map.yaml`

A **Stop hook** that prints a soft reminder when a plugin asset moves without its
docs being co-modified. Wired in `.claude/settings.json` under `hooks.Stop[]`;
runs after every Claude Code stop in this repo.

- **What it does.** Reads `doc-drift-map.yaml` (the source→docs rule set:
  skills/SKILL.md, commands, agents, scripts → `artifacts.md` + `shield/README.md`),
  walks `git diff --name-only HEAD` + untracked files, and emits one stderr block
  per rule whose source matches a touched file while its listed docs don't.
- **Severity.** Always exit 0 — advisory, never blocks Claude or `git commit`.
  Test files (`test_*.py`, `*_test.py`), `*.lock`, `*.tmp`, `__init__.py` are
  filtered as noise.
- **New files vs modifications.** Untracked-not-gitignored files are listed
  via `git ls-files --others --exclude-standard` and treated identically to
  modified files — a brand-new SKILL.md triggers the same hint a modified one
  would. Files in directories no rule covers are silently allowed; if you add
  a new asset *category*, extend `doc-drift-map.yaml`.
- **Tests.** `.claude/hooks/test_check_doc_drift.py` — pure-function tests for
  the glob matcher and `compute_hints`, plus one end-to-end integration test
  against a tempdir git repo. Run via `uv run --with pyyaml .claude/hooks/test_check_doc_drift.py`.
- **Adding a rule.** Append to `doc-drift-map.yaml` under `rules:` with `source`
  (fnmatch glob, `**` is cross-directory) and `docs` (list of paths to nag about).

If the reminder fires and you're sure the listed docs don't need touching,
just ignore it — the hook is checking heuristically, not asserting truth.

## Pointers

- Path templates: [`schema/output-paths.yaml`](../schema/output-paths.yaml)
- Manifest schema: [`skills/general/manifest-schema.md`](../skills/general/manifest-schema.md)
- Plan sidecar schema: [`skills/general/plan-docs/sidecar-schema.md`](../skills/general/plan-docs/sidecar-schema.md)
- Output-structure design: `docs/superpowers/specs/2026-05-22-shield-output-structure-design.md`
- Doc-drift hook source: [`.claude/hooks/check-doc-drift.py`](../../.claude/hooks/check-doc-drift.py) + [`doc-drift-map.yaml`](../../.claude/hooks/doc-drift-map.yaml)
