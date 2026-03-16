---
name: plan
description: Generate plan documents — architecture/ADR docs and detailed execution plans with stories, plus a JSON sidecar for project management sync
---

# Plan

Generate Shield plan documents with a machine-readable sidecar.

## Usage

`/plan [topic or requirements]`

## Output Paths — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Then write each artifact using the Write tool to:

1. `{project_root}/shield/plan.json` — machine-readable sidecar (updated in place, no timestamp)
2. `{project_root}/shield/docs/architecture-YYYYMMDD-HHMMSS.html` — the "why and how"
3. `{project_root}/shield/docs/plan-YYYYMMDD-HHMMSS.html` — the "what to do", rendered from the sidecar
4. `{project_root}/shield/docs/index.html` — overview page linking to all artifacts (create or update)

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`, and `YYYYMMDD-HHMMSS` with the current date and time.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. **Do NOT** delegate to superpowers or other skills that write to different paths. The Write tool creates directories automatically.

## Behavior

1. If topic/requirements provided, use as starting context
2. If no topic, ask the user what they're planning
3. Check for prior research: glob for `{project_root}/shield/docs/research-*.md` and read the most recent one if it exists
4. **Generate `shield/plan.json` first** — the sidecar JSON with epics, stories, tasks, and acceptance criteria. See the `shield:plan-docs` skill for the schema.
5. **Generate architecture HTML** — the "why and how" document
6. **Generate plan HTML** — stories rendered from the sidecar, includes `<meta name="sidecar" content="./plan.json">`
7. **Generate or update `index.html`** — overview page linking to all artifacts in `shield/docs/`
8. **You MUST produce all four artifacts and write them to the paths above.** No exceptions.
8. Verify the sidecar JSON contains at least 1 epic with stories, each with acceptance criteria
9. Offer next steps:
    - `/plan-review` — run multi-agent review on the plan
    - `/pm-sync` — sync stories to project management tool
