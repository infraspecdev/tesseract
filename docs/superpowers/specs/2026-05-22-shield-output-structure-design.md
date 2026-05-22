# Shield Output Structure Redesign — Design Spec

**Date:** 2026-05-22
**Status:** Draft for review
**Author:** Brainstorm session, ashwini.manoj@aspora.com

## 1. Problem

Shield commands today produce a confusing per-feature footprint in `docs/shield/{feature}/`. A single feature taken through research → prd → plan → plan-review → implement → code-review can yield 20–40 files spread across six numbered-run subfolders.

Three specific pain points (confirmed in brainstorm):

1. **Too many subfolders per feature** — `research/`, `prd/`, `prd-review/`, `plan/`, `plan-review/`, `code-review/` is too much taxonomy at one level.
2. **Numbered runs (`{N}-{slug}/`) pile up** — every re-invocation creates a new folder; prior runs linger; "latest" is not obvious.
3. **Three formats for the same artifact** — `plan.json` + `plan.md` + `plan.html` + `architecture.html` blur which file is canonical.

Per-agent reviewer detail files (e.g. `detailed/backend-engineer.md`) are *not* a pain point and should be preserved.

## 2. Goals

- Predictable per-feature layout with fixed top-level filenames.
- Clear separation between **source artifacts** (committed, edited, regenerable from prompts) and **rendered artifacts** (committed, regenerable from source).
- One place to change when directory schema evolves (no duplicated path templates across 17+ commands).
- Git history replaces ad-hoc archive folders.

## 3. Non-goals

- Removing per-agent reviewer detail files.
- Letting consumers override per-path templates (YAGNI — `output_dir` remains the only seam).
- Migrating the global `docs/shield/index.html` semantics (only its physical location moves).

## 4. New per-feature layout

```
docs/shield/
├── manifest.json                        ← only non-rendered file at top level
├── outputs/
│   └── index.html                       ← global card grid (regenerated from manifest)
└── {feature}-YYYYMMDD/
    ├── README.md                        ← entry point: status + links (auto-generated)
    ├── research.md                      ← source (overwrite on re-run; git keeps history)
    ├── prd.md                           ← source
    ├── plan.json                        ← source — machine-readable, PM sync truth
    ├── plan.md                          ← source — human-readable plan with Mermaid inline
    ├── plan-architecture.md             ← source — ADR-style architecture document
    ├── reviews/
    │   ├── prd/
    │   │   └── YYYY-MM-DD[_N]/
    │   │       ├── summary.md
    │   │       └── enhanced-prd.md      ← proposed adoption; diff against prd.md
    │   ├── plan/
    │   │   └── YYYY-MM-DD[_N]/
    │   │       ├── summary.md
    │   │       ├── enhanced-plan.md
    │   │       └── detailed/
    │   │           └── {agent}.md
    │   └── code/
    │       └── YYYY-MM-DD[_N]/
    │           └── summary.md           ← no enhanced doc (code lives outside docs/shield)
    └── outputs/                         ← mirrors source paths, .md → .html
        ├── README.html
        ├── prd.html
        ├── plan.html
        ├── plan-architecture.html
        └── reviews/
            ├── prd/YYYY-MM-DD[_N]/{summary.html, enhanced-prd.html}
            ├── plan/YYYY-MM-DD[_N]/{summary.html, enhanced-plan.html, detailed/*.html}
            └── code/YYYY-MM-DD[_N]/summary.html
```

### 4.1 Source-file rules

- **Fixed top-level filenames.** `research.md`, `prd.md`, `plan.json`, `plan.md`, `plan-architecture.md`, `README.md` — no slug or run number in the name.
- **Re-run overwrites.** Git is the history. No `.archive/` folder.
- **Reviews are dated, not numbered.** Each review run is a discrete event, not a re-do of the same thing. Naming: `YYYY-MM-DD`. Same-day collisions append `_N` (underscore separator to disambiguate from the date hyphens): `2026-05-21`, `2026-05-21_2`, `2026-05-21_3`. Latest = lexically highest folder name.
- **Reviews never mutate source.** `enhanced-prd.md` and `enhanced-plan.md` are proposals. Adoption is manual (user diffs and merges).
- **Per-agent detail files** live in `reviews/{type}/{date[_N]}/detailed/{agent}.md`. Only present for plan-review (which dispatches multiple reviewer subagents).
- **Code-review has no enhanced doc.** Source code is outside `docs/shield/`; the review just reports findings.

### 4.2 Rendered-output rules

- **`outputs/` mirrors source paths with `.md → .html` substitution.** If `{feature}/plan.md` exists, `{feature}/outputs/plan.html` is its render. Same for reviews.
- **`plan.json` has no render** — JSON is already machine-readable.
- **Global `docs/shield/outputs/index.html`** is the only top-level rendered artifact; everything else is per-feature.
- **`outputs/` is committed**, not gitignored. Lets stakeholders view via GitHub raw/Pages links without local setup.

### 4.3 Why `outputs/` per-feature, not `docs/shield/outputs/{feature}/`

A single feature is self-contained: source + rendered side-by-side. Easier to bundle for handoff. Easier to delete (`rm -rf {feature}-YYYYMMDD/` removes both).

## 5. Central path registry

A new file `shield/schema/output-paths.yaml` defines every path template by name. Every command/skill/agent that writes files references paths *by name*, not by literal template.

### 5.1 Registry schema

```yaml
# shield/schema/output-paths.yaml
# Plugin-owned contract. Consumers should NOT edit.

variables:
  output_dir:       "Set by consumer in .shield.json"
  feature:          "Auto-derived from command (e.g. 'vpc-module-20260319')"
  review_type:      "One of: prd, plan, code"
  date:             "YYYY-MM-DD of the review run"
  _counter:         "Empty for first run on a date; '_2', '_3', ... on same-day collisions"
  agent:            "Agent slug for per-agent detail files (e.g. 'backend-engineer')"

paths:
  # Top-level
  manifest:           "{output_dir}/manifest.json"
  global_outputs_dir: "{output_dir}/outputs"
  global_index_html:  "{global_outputs_dir}/index.html"

  # Per-feature
  feature_dir:        "{output_dir}/{feature}"
  readme:             "{feature_dir}/README.md"
  research:           "{feature_dir}/research.md"
  prd:                "{feature_dir}/prd.md"
  plan_json:          "{feature_dir}/plan.json"
  plan_md:            "{feature_dir}/plan.md"
  plan_arch_md:       "{feature_dir}/plan-architecture.md"

  # Per-feature rendered
  feature_outputs:    "{feature_dir}/outputs"
  readme_html:        "{feature_outputs}/README.html"
  prd_html:           "{feature_outputs}/prd.html"
  plan_html:          "{feature_outputs}/plan.html"
  plan_arch_html:     "{feature_outputs}/plan-architecture.html"

  # Reviews (source)
  review_dir:         "{feature_dir}/reviews/{review_type}/{date}{_counter}"
  review_summary:     "{review_dir}/summary.md"
  review_enhanced:    "{review_dir}/enhanced-{review_type}.md"
  review_detailed:    "{review_dir}/detailed/{agent}.md"

  # Reviews (rendered)
  review_outputs_dir:    "{feature_outputs}/reviews/{review_type}/{date}{_counter}"
  review_summary_html:   "{review_outputs_dir}/summary.html"
  review_enhanced_html:  "{review_outputs_dir}/enhanced-{review_type}.html"
  review_detailed_html:  "{review_outputs_dir}/detailed/{agent}.html"
```

### 5.2 Per-asset references

Each command/skill/agent's frontmatter lists the registry path names it writes:

```yaml
---
name: plan
description: Generate plan documents...
outputs:
  - plan_json
  - plan_md
  - plan_arch_md
  - plan_html
  - plan_arch_html
---
```

For multi-agent outputs (one file per dispatched reviewer):

```yaml
---
name: shield:plan-reviewer-backend
outputs:
  - review_detailed  # writes detailed/backend-engineer.md
---
```

Body prose in command/skill bodies refers to paths by their registry name, e.g. *"Write to `{plan_md}`"* — a lint script substitutes the template at validation time.

## 6. Config ownership

| File | Owner | Purpose | Changes? |
|---|---|---|---|
| `.shield.json` | consumer | `output_dir`, project name, domains, PM creds ref | Minor: gitignore patterns updated (drop numbered-run patterns) |
| `manifest.json` | shield (auto-generated) | Registry of features and their artifacts | Schema simplified — see §6.1 |
| `shield/schema/output-paths.yaml` | plugin | Path template contract | **New file** |

Folding `output-paths.yaml` into `.shield.json` was considered and rejected: different lifecycles (plugin vs project), different audiences (read-only contract vs user-edited), and consumers editing path templates would silently break commands.

### 6.1 New `manifest.json` schema

```json
{
  "schema_version": 2,
  "features": [
    {
      "name": "agent-behavior-decomposition-20260520",
      "artifacts": {
        "research": true,
        "prd": true,
        "plan_json": true,
        "plan_md": true,
        "plan_arch_md": false,
        "readme": true
      },
      "reviews": {
        "prd":  { "latest": "2026-05-21",   "count": 1 },
        "plan": { "latest": "2026-05-21_2", "count": 2 },
        "code": { "latest": "2026-05-22",   "count": 1 }
      },
      "updated": "2026-05-22T10:00:00Z"
    }
  ]
}
```

`schema_version: 2` lets the migration script detect old manifests and rewrite them.

## 7. Migration of existing folders

Three feature folders exist today in the old format. Mapping:

| Old path | New path | Notes |
|---|---|---|
| `agent-behavior-decomposition-20260520/plan.json` | unchanged | already at root |
| `agent-behavior-decomposition-20260520/plan/1-behavior-catalog-migration/architecture.html` | `agent-behavior-decomposition-20260520/outputs/plan-architecture.html` | source `.md` is missing — commit HTML, note in README |
| `devcontainer-implement-20260518/research/1-claude-implement-isolation/findings.md` | `devcontainer-implement-20260518/research.md` | |
| `devcontainer-implement-20260518/research/1-claude-implement-isolation/transcript.md` | `devcontainer-implement-20260518/.session-transcript.md` | session transcript, kept as hidden file (not a first-class artifact) |
| `pm-restructure-v0-20260521/plan.json` | unchanged | |
| `pm-restructure-v0-20260521/handoff.md` | unchanged | not part of new schema — left as ad-hoc; warn user |

Migration is performed by `shield/scripts/migrate-outputs.py`:

- Walks `{output_dir}/` and maps known patterns to new locations.
- **Dry-run by default**; `--apply` flag executes moves.
- Idempotent — re-running on already-migrated tree is a no-op.
- Unrecognized files (like `handoff.md`) are left alone with a warning.
- Regenerates `manifest.json` at the end.

## 8. Code touch points

### 8.1 New files

- `shield/schema/output-paths.yaml` — central registry.
- `shield/schema/path-resolver.py` — small utility that takes a registry name + variable bindings and returns the resolved path. Used by lint script, evals, and (optionally) commands.
- `shield/scripts/lint-output-paths.py` — validates that every asset's `outputs:` list references real registry names, and that every registry template uses only declared variables. Also scans `docs/shield/` for orphans (files matching no registered template) and dead declarations (templates with no on-disk presence in any feature).
- `shield/scripts/migrate-outputs.py` — one-time migration (§7).
- `shield/evals/output-structure/` — eval fixtures and test cases (§9).

### 8.2 Modified files

- **All `shield/commands/*.md`** (~17 files): add `outputs:` frontmatter list; rewrite body prose to reference paths by registry name.
- **`shield/skills/*/SKILL.md`** that emit files (notably `pm-sync` and `devcontainer` scaffolders).
- **Agent definitions** that write files (per-dim PM reviewer subagents writing `detailed/{agent}.md`).
- **`shield/commands/init.md`** and **`shield/commands/migrate.md`**: update gitignore patterns, defaults; remove numbered-run path references.

## 9. Testing — TDD requirement

**Current gap**: there are no tests covering output-directory-changing scenarios. This redesign must close that gap before any structural code change lands.

### 9.1 TDD discipline

For each modified asset:

1. **RED**: write a failing test that asserts the asset writes its declared outputs at the new paths (with `output_dir` set to a fixture directory, not the project default).
2. **GREEN**: update the asset to match the new contract.
3. **REFACTOR**: deduplicate path resolution via `path-resolver.py`.

The order matters. No asset change ships without a corresponding failing-then-passing test in the same PR.

### 9.2 Test categories

- **Path resolver unit tests**: given a registry name and variable bindings, returns the expected path. Cover counter logic (empty, `_2`, `_3`), missing variables (clear error), unknown registry names (clear error).
- **Per-asset output declaration tests**: every command/skill/agent under test has its `outputs:` list parsed, and every entry resolves to a valid path. (Lint-script-driven.)
- **End-to-end output-directory test**: run a sample command flow with `output_dir = /tmp/shield-test-<n>` and assert the on-disk tree matches expectations. Repeat with a different `output_dir` to prove no hardcoded paths remain.
- **Migration script tests**: build a synthetic old-format tree, run `migrate-outputs.py --apply`, assert resulting tree matches the new schema. Re-run and assert idempotence. Run on a tree with unrecognized files and assert they survive with warnings.
- **Manifest schema test**: generate `manifest.json` for a fixture tree, validate against schema (v2), assert reviews counter logic.

### 9.3 Eval coverage (repo policy)

Per `CLAUDE.md`, every modified plugin asset needs eval coverage in the same PR. The umbrella `shield/evals/output-structure/` directory holds:

- One eval per modified command, verifying it emits its declared outputs at the new paths.
- An invariants eval: `outputs/` mirrors source paths; no asset writes outside its declared paths; lint script passes.

## 10. Implementation order

Suggested sequencing (each step lands in its own PR with TDD):

1. **Foundations**: registry file + path resolver + lint script (no asset changes yet). To keep lint green during the cutover, register the *current* path templates under `legacy_*` names (e.g. `legacy_research_dir: "{output_dir}/{feature}/research/{n}-{slug}/findings.md"`). Each asset's frontmatter initially references its `legacy_*` names; later steps switch them to the new names. The `legacy_*` block is removed in step 5.
2. **New registry entries + migration script** (dry-run only). Tests prove the migration mapping is correct on fixture trees.
3. **Per-asset cutover, one command family at a time**:
   - `research`, `prd`, `prd-review`
   - `plan`, `plan-review`
   - `review`, `review-*` family
   - `pm-sync`, init, migrate
4. **Run migration on the live `docs/shield/` tree** once all assets are cut over.
5. **Remove legacy registry entries** and any backwards-compat shims.

Each PR includes evals demonstrating its asset's new behavior.

## 11. Open questions deferred to implementation

- **Path resolver implementation**: Python helper invoked by hooks/scripts, or pure-prose substitution by Claude reading the registry? Spec assumes the former; YAGNI says try prose-only first and add the helper if drift becomes a problem.
- **Lint script enforcement**: pre-commit hook, CI-only, or both? Default to CI-only initially; promote to pre-commit once stable.
- **Render-on-demand vs always-render HTML**: spec assumes commands render `.html` at the time they write source. Could be a separate `/shield render` command. Decide during implementation.

## 12. Risks

- **17+ command edits is a large surface**. Mitigation: cut over one family at a time (§10), with evals.
- **Existing `docs/shield/` content needs migration before any consumer hits the new structure**. Mitigation: migration script + dry-run + idempotence tests.
- **Path resolver as a runtime dependency**: if any command depends on it being installed/runnable, that's a new shape of failure. Mitigation: prefer prose-only substitution; only introduce the helper if drift is a problem.
- **Lint script may flag legitimate ad-hoc files** (e.g. `handoff.md` in `pm-restructure-v0-20260521/`). Mitigation: lint warns, doesn't fail, on unrecognized files; provide an opt-in `.shield-ignore` mechanism if needed.
