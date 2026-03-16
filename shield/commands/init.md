---
name: init
description: Set up Shield for a new project — creates .shield.json and ~/.shield/ config structure
---

# Shield Init

Set up Shield for this project. If this is a fresh setup, create configuration from scratch. If old plugins are detected, suggest running `/shield migrate` instead.

## Steps

1. **Check for existing setup**
   - If `.shield.json` already exists, show current config and ask if user wants to reconfigure
   - If old plugin config is detected (`sprint-planner.json`, `claude/infra-review/`), suggest `/shield migrate` instead
   - If `shield/plan.json` exists (old single-plan path), offer to migrate it to `shield/docs/plans/<name>.json` — derive `<name>` from the `project` or `phase` field in the JSON

2. **Gather project info**
   - Ask for project name (default: repo directory name)
   - Ask for active domains — show available options:
     - `terraform` — Terraform/HCL infrastructure
     - `atmos` — Atmos stack management
     - `github-actions` — CI/CD workflows
     - (more domains in future)
   - Allow multiple selections

3. **Create `.shield.json`** in the repo root:
   ```json
   {
     "project": "<project-name>",
     "domains": ["<selected-domains>"]
   }
   ```

4. **Create `~/.shield/` directory structure**:
   ```bash
   mkdir -p ~/.shield/projects/<project-name>/runs
   ```

5. **Create `~/.shield/config.json`** if it doesn't exist:
   - Copy from `${CLAUDE_PLUGIN_ROOT}/config-examples/config.example.json`
   - Ask user for PM tool preference (clickup / none / skip for now)

6. **If PM tool selected:**
   - Ask for workspace details (workspace_id, space_id, project_prefix)
   - Create `~/.shield/projects/<project-name>/pm.json`
   - Ask for API token and save to `~/.shield/credentials.json`
   - If `uv` is not on PATH and PM tool requires it, offer install instructions:
     ```
     PM adapter requires uv (Python package manager).
     Install: curl -LsSf https://astral.sh/uv/install.sh | sh
     Or skip PM setup for now — you can configure it later.
     ```

7. **Show summary** of what was created:
   ```
   Shield initialized for project: <name>

   Created:
     ✓ .shield.json (project marker)
     ✓ ~/.shield/config.json (global config)
     ✓ ~/.shield/projects/<name>/pm.json (PM config)

   Enable auto-updates:
     /plugin update --auto-update shield@tesseract

   Next: try /research or /plan to start your workflow
   ```

## Important
- Do NOT create `.shield.json` without user confirmation
- Do NOT overwrite existing `~/.shield/config.json` — merge if it exists
- Do NOT store API tokens in `.shield.json` — credentials go in `~/.shield/credentials.json` only
- Validate all inputs against the JSON schemas in `${CLAUDE_PLUGIN_ROOT}/schemas/`
