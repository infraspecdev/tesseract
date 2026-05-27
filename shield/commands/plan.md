---
name: plan
description: Generate plan documents — a 14-section TRD and a detailed execution plan with stories, plus a JSON sidecar for project management sync
outputs:
  - plan_json
  - plan_md
  - plan_trd_md
  - plan_html
  - plan_trd_html
  - prd_meta_json   # updates the PRD sidecar's linked_plans field
---

# Plan

Generate Shield plan documents with a machine-readable sidecar.

## Usage

`/plan [--name <plan-name>] [topic or requirements]`

## Paths

This command writes the following registry-tracked paths (see `shield/schema/output-paths.yaml`):

| Registry key | Resolved path |
|---|---|
| `plan_json` | `{output_dir}/{feature}/plan.json` |
| `plan_md` | `{output_dir}/{feature}/plan.md` |
| `plan_trd_md` | `{output_dir}/{feature}/trd.md` |
| `plan_html` | `{output_dir}/{feature}/outputs/plan.html` |
| `plan_trd_html` | `{output_dir}/{feature}/outputs/trd.html` |
| `prd_meta_json` | `{output_dir}/{feature}/prd.meta.json` (updated — appends to `linked_plans`) |

The global dashboard `{output_dir}/index.html` (registry key `global_index_html`) is updated as a side effect; it is not declared in `outputs:` because it is a cross-feature artifact, not a per-run deliverable.

**Legacy keys:** `plan_arch_md` and `plan_arch_html` are deprecated and no longer written by `/plan`. They remain in the registry with `deprecated: true` so older folders containing a `plan-architecture.md` stay readable. **`/plan` never deletes or modifies an existing `plan-architecture.md`** — see "Re-run behavior" below.

## Output Paths — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read the `output_dir` field from `.shield.json` (default: `docs/shield` if not set). Then write each artifact using the Write tool to:

1. `{project_root}/{output_dir}/{feature}/plan.json` — machine-readable sidecar (registry: `{plan_json}`)
2. `{project_root}/{output_dir}/{feature}/plan.md` — canonical detailed plan markdown (registry: `{plan_md}`)
3. `{project_root}/{output_dir}/{feature}/trd.md` — canonical 14-section Technical Requirements Document (registry: `{plan_trd_md}`)
4. `{project_root}/{output_dir}/{feature}/outputs/plan.html` — rendered detailed plan HTML (registry: `{plan_html}`)
5. `{project_root}/{output_dir}/{feature}/outputs/trd.html` — rendered TRD HTML (registry: `{plan_trd_html}`)
6. `{project_root}/{output_dir}/index.html` — single dashboard linking to all artifacts (create or update; cross-feature side-effect)

Where:
- `{output_dir}` = the `output_dir` value from `.shield.json` (default: `docs/shield`)
- `{feature}` = `{feature-name}-YYYYMMDD`, derived from `--name` or topic in kebab-case + current date

If `--name` is not provided, derive from the topic in kebab-case. Example: `/plan input validation` → feature folder `input-validation-20260319/`.

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

Numbered run subfolders (`plan/{N}-{slug}/`) are gone — each plan is a single canonical pair of markdown sources at feature root, with rendered HTML under `outputs/`. Re-running `/plan` updates the same files (the plan.json sidecar is the source of truth and is updated in place).

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. **Do NOT** delegate to superpowers or other skills that write to different paths. The Write tool creates directories automatically.

## Behavior

1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning
3. Read `output_dir` from `.shield.json` (default: `docs/shield`)
4. If `--name` not provided, derive from topic in kebab-case
5. Feature folder = `{plan-name}-YYYYMMDD`
6. Check for prior research: read `{output_dir}/{feature}/research.md` (i.e. `{research}`) if it exists; falls back to `.session-transcript.md` only if `research.md` is absent
7. **Check for prior PRD:** If `{output_dir}/{feature}/prd.md` (i.e. `{prd}`) exists, read it as context — Problem, Users, Goals, Stories, NFRs, Risks all inform the plan. Record `source_prd` in plan.json and append this plan's `{plan_md}` path to `prd.meta.json.linked_plans`.
8. **Domain detection.** Read `.shield.json` `plan.template_override` first; if set to one of `{backend, infra, mixed}`, use that and skip marker walking. Otherwise walk the project root for stack/domain markers:
   - `pom.xml` / `build.gradle*` → backend (Java/Kotlin)
   - `pyproject.toml` / `requirements.txt` → backend (Python)
   - `package.json` → backend (Node/TS)
   - `go.mod` → backend (Go)
   - `*.tf` / `terraform.tfvars` → infra (terraform)
   - `Chart.yaml` / `values.yaml` → infra (kubernetes/helm)
   - `kustomization.yaml` → infra (kubernetes)
   - `*.yaml` with `kind:` and `apiVersion:` → infra (kubernetes)
   - `atmos.yaml` → infra (atmos)

   If **both** infra and backend markers are present, domain is **mixed** — the TRD emits `[backend]` and `[infra]` labeled subsections inside every domain-divergent section (§4, §5, §6, §7, §11, §14 per `shield/schema/trd-sections.yaml` `domain_divergent`). See `shield/skills/general/plan-docs/trd-template.md` for the worked example.

   For each domain detected, read all `SKILL.md` files under `shield/skills/<domain>/` as **context** when generating stories and ACs. Skills inform what the plan should cover (API design conventions, test strategy, deployment safety, etc.) but are NOT applied as gating checks — that happens at /plan-review and /review.

   If no domain markers are found and no override is set, generate a generic plan and use the backend per-section guidance as the default (it is the broader interpretation).
9. **Generate `{plan_json}` first** — the sidecar JSON with epics, stories, tasks, acceptance criteria, and `design_refs[]`. See `shield:plan-docs/sidecar-schema.md` for the schema (version 1.2) and the section-ID selection heuristic.
10. **Generate `{plan_trd_md}`** — emit the 14-section TRD per `shield:plan-docs/trd-template.md`. The emitter:
    - Walks §1 → §14 in canonical order.
    - For each section, surfaces the domain-appropriate authoring guidance (backend / infra / mixed-labeled subsections).
    - Emits explicit `{#section-id}` anchors using the slugs from `shield/schema/trd-sections.yaml`.
    - Stamps the first line after frontmatter: `<!-- generated by /plan v{shield-plugin-version} on {YYYY-MM-DD} -->` where `{shield-plugin-version}` is read from `.claude-plugin/marketplace.json`.
    - Writes `trd.md.tmp` first, then renames to `trd.md` (atomic write). On any failure mid-write, removes `.tmp` and surfaces the error.
    - Allows `n/a — <reason>` on sections that genuinely don't apply; rejects vague TBDs and silent omissions.
11. **Generate `{plan_md}`** — canonical detailed plan markdown (stories rendered from the sidecar)
12. **Render HTML** — produce `{plan_trd_html}` and `{plan_html}` under `{output_dir}/{feature}/outputs/` via the render-markdown helper (mirrors the `/prd` rendering flow); see `shield:plan-docs` for the exact invocation
13. **Update `manifest.json`** in `{output_dir}/` and **regenerate `index.html`** — single dashboard linking to all artifacts
14. **You MUST produce all five artifacts (`{plan_json}`, `{plan_md}`, `{plan_trd_md}`, `{plan_html}`, `{plan_trd_html}`) and write them to the paths above.** No exceptions.
15. Verify the sidecar JSON contains at least 1 epic with stories, each with acceptance criteria and (when a TRD exists) at least one `design_refs[]` entry.
16. Offer next steps:
    - `/plan-review` — run multi-agent review on the plan
    - `/pm-sync` — sync stories to project management tool

## Re-run behavior

When `/plan` is re-run in a feature folder that already contains `trd.md`, the new
file overwrites the old one. When the folder contains a legacy `plan-architecture.md`
(from a pre-cutover plan), **`/plan` never deletes or modifies it** — the file remains
readable as historical context. The cutover is forward-only.

`design_refs[]` re-runs merge by the `(doc, section_id, component)` tuple per
`sidecar-schema.md` — entries whose anchor has since been deleted from `trd.md` are
preserved but tagged `stale: true` for `/plan-review` to surface.

## Rollback triggers

Revert this command's TRD-emission behavior (and roll back the marketplace version
bump) when any of the following observable signals fire within 48h of the cutover
merge:

- The `plan-trd` eval fails on any positive fixture in a subsequent CI run.
- Two or more user-reported `/plan` runs produce a `trd.md` that fails
  `validate_trd.py` against unchanged content.
- A `/pm-sync` adapter errors on a `design_refs[]` forward and the error trace
  points at schema 1.2 (rather than transport failure).

Rollback procedure: revert the cutover commit, re-publish the prior marketplace
version, and re-run the eval on the prior fixture set to confirm GREEN.
