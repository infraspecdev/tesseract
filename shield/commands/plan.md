---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories, plus a JSON sidecar for project management sync
---

# Plan

Generate Shield plan documents with a machine-readable sidecar.

## Usage

`/plan [--name <plan-name>] [topic or requirements]`

## Output Paths — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read the `output_dir` field from `.shield.json` (default: `docs/shield` if not set). Then write each artifact using the Write tool to:

1. `{project_root}/{output_dir}/{feature-name}-YYYYMMDD/plan.json` — machine-readable sidecar (updated in place at feature root)
2. `{project_root}/{output_dir}/{feature-name}-YYYYMMDD/plan/{N}-{slug}/architecture.html` — the "why and how"
3. `{project_root}/{output_dir}/{feature-name}-YYYYMMDD/plan/{N}-{slug}/plan.html` — the "what to do", rendered from the sidecar
4. `{project_root}/{output_dir}/index.html` — single dashboard linking to all artifacts (create or update)

Where:
- `{output_dir}` = the `output_dir` value from `.shield.json` (default: `docs/shield`)
- `{feature-name}` = derived from `--name` or topic in kebab-case
- `YYYYMMDD` = current date
- `{N}` = run number, determined by counting existing folders in `{feature-name}-YYYYMMDD/plan/` + 1
- `{slug}` = the plan name in kebab-case

If `--name` is not provided, derive from the topic in kebab-case. Example: `/plan input validation` → feature folder `input-validation-20260319/`.

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. **Do NOT** delegate to superpowers or other skills that write to different paths. The Write tool creates directories automatically.

## Behavior

1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning
3. Read `output_dir` from `.shield.json` (default: `docs/shield`)
4. If `--name` not provided, derive from topic in kebab-case
5. Feature folder = `{plan-name}-YYYYMMDD`
6. Determine run number by counting existing folders in `{output_dir}/{feature}/plan/` + 1
7. Check for prior research: glob for `{project_root}/{output_dir}/{feature}/research/*/findings.md` and read the most recent one if it exists
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
9. **Generate `{feature}/plan.json` first** — the sidecar JSON with epics, stories, tasks, and acceptance criteria. See the `shield:plan-docs` skill for the schema.
10. **Generate architecture HTML** — the "why and how" document
11. **Generate plan HTML** — stories rendered from the sidecar, includes `<meta name="sidecar" content="../plan.json">`
12. **Update `manifest.json`** in `{output_dir}/` and **regenerate `index.html`** — single dashboard linking to all artifacts
13. **You MUST produce all four artifacts and write them to the paths above.** No exceptions.
14. Verify the sidecar JSON contains at least 1 epic with stories, each with acceptance criteria
15. Offer next steps:
    - `/plan-review` — run multi-agent review on the plan
    - `/pm-sync` — sync stories to project management tool
