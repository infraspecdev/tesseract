---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories, plus a JSON sidecar for project management sync
outputs:
  - plan_json
  - plan_md
  - plan_arch_md
  - plan_html
  - plan_arch_html
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
| `plan_arch_md` | `{output_dir}/{feature}/plan-architecture.md` |
| `plan_html` | `{output_dir}/{feature}/outputs/plan.html` |
| `plan_arch_html` | `{output_dir}/{feature}/outputs/plan-architecture.html` |

The global dashboard `{output_dir}/index.html` (registry key `global_index_html`) is updated as a side effect; it is not declared in `outputs:` because it is a cross-feature artifact, not a per-run deliverable.

## Output Paths — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read the `output_dir` field from `.shield.json` (default: `docs/shield` if not set). Then write each artifact using the Write tool to:

1. `{project_root}/{output_dir}/{feature}/plan.json` — machine-readable sidecar (registry: `{plan_json}`)
2. `{project_root}/{output_dir}/{feature}/plan.md` — canonical detailed plan markdown (registry: `{plan_md}`)
3. `{project_root}/{output_dir}/{feature}/plan-architecture.md` — canonical architecture markdown (registry: `{plan_arch_md}`)
4. `{project_root}/{output_dir}/{feature}/outputs/plan.html` — rendered detailed plan HTML (registry: `{plan_html}`)
5. `{project_root}/{output_dir}/{feature}/outputs/plan-architecture.html` — rendered architecture HTML (registry: `{plan_arch_html}`)
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
8. **Domain detection.** Walk the project root for stack/domain markers:
   - `pom.xml` / `build.gradle*` → backend (Java/Kotlin)
   - `pyproject.toml` / `requirements.txt` → backend (Python)
   - `package.json` → backend (Node/TS)
   - `go.mod` → backend (Go)
   - `*.tf` / `terraform.tfvars` → terraform
   - `Chart.yaml` / `values.yaml` → kubernetes
   - `kustomization.yaml` → kubernetes
   - `*.yaml` with `kind:` and `apiVersion:` → kubernetes
   - `atmos.yaml` → atmos

   For each domain detected, read all `SKILL.md` files under `shield/skills/<domain>/` as **context** when generating stories and ACs. Skills inform what the plan should cover (API design conventions, test strategy, deployment safety, etc.) but are NOT applied as gating checks — that happens at /plan-review and /review.

   If no domain markers are found, generate a generic plan; the LLM uses its general knowledge.
9. **Generate `{plan_json}` first** — the sidecar JSON with epics, stories, tasks, and acceptance criteria. See the `shield:plan-docs` skill for the schema.
10. **Generate `{plan_arch_md}`** — canonical architecture markdown (the "why and how")
11. **Generate `{plan_md}`** — canonical detailed plan markdown (stories rendered from the sidecar)
12. **Render HTML** — produce `{plan_arch_html}` and `{plan_html}` under `{output_dir}/{feature}/outputs/` via the render-markdown helper (mirrors the `/prd` rendering flow); see `shield:plan-docs` for the exact invocation
13. **Update `manifest.json`** in `{output_dir}/` and **regenerate `index.html`** — single dashboard linking to all artifacts
14. **You MUST produce all five artifacts (`{plan_json}`, `{plan_md}`, `{plan_arch_md}`, `{plan_html}`, `{plan_arch_html}`) and write them to the paths above.** No exceptions.
15. Verify the sidecar JSON contains at least 1 epic with stories, each with acceptance criteria
16. Offer next steps:
    - `/plan-review` — run multi-agent review on the plan
    - `/pm-sync` — sync stories to project management tool
