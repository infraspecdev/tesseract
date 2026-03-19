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
   - If `shield/plan.json` exists (old single-plan path), offer to migrate it to `{output_dir}/{feature}/plans/` — derive name from the `project` or `phase` field in the JSON

2. **Gather project info**
   - Ask for project name (default: repo directory name)
   - Ask for output directory (default: `docs/shield`). This is where all Shield artifacts go.
   - Ask for active domains — show available options:
     - `terraform` — Terraform/HCL infrastructure
     - `atmos` — Atmos stack management
     - `github-actions` — CI/CD workflows
     - (more domains in future)
   - Allow multiple selections
   - Ask about reviewer preferences (optional):
     - `auto_select` — auto-pick reviewers based on content (default: true)
     - `always_include` — reviewers that always run (e.g., `["security"]`)
     - `never_include` — reviewers to skip

3. **Create `.shield.json`** in the repo root:
   ```json
   {
     "project": "<project-name>",
     "output_dir": "docs/shield",
     "domains": ["<selected-domains>"],
     "reviewers": {
       "auto_select": true,
       "always_include": ["security"],
       "never_include": []
     }
   }
   ```

4. **Add gitignore patterns** to the project's `.gitignore`:
   ```gitignore
   # Shield ephemeral review output
   **/docs/shield/*/plan-review/
   **/docs/shield/*/code-review/
   ```
   - If the user specified a custom `output_dir`, use that instead of `docs/shield` in the patterns
   - If `.gitignore` doesn't exist, create it
   - If the patterns already exist, skip

5. **Create `~/.shield/` directory structure**:
   ```bash
   mkdir -p ~/.shield/projects/<project-name>/runs
   ```

6. **Ask for PM tool preference** (clickup / jira / none / skip for now)

7. **If PM tool selected:**
   - Ask for workspace details (workspace_id, space_id, project_prefix)
   - Create `~/.shield/projects/<project-name>/pm.json`
   - Ask for API token and save to `~/.shield/credentials.json`
   - If `uv` is not on PATH and PM tool requires it, offer install instructions:
     ```
     PM adapter requires uv (Python package manager).
     Install: curl -LsSf https://astral.sh/uv/install.sh | sh
     Or skip PM setup for now — you can configure it later.
     ```
   - **Register the PM adapter MCP server:**
     - Read `${CLAUDE_PLUGIN_ROOT}/adapters/<pm-tool>/.mcp.json` to get the server entries
     - Merge those entries into `${CLAUDE_PLUGIN_ROOT}/.mcp.json` → `mcpServers` object
     - Tell the user: **"Reload the Shield plugin to start the PM adapter: `/plugin update shield@tesseract`"**

8. **Show summary** of what was created:
   ```
   Shield initialized for project: <name>

   Created:
     ✓ .shield.json (project config, output_dir: docs/shield)
     ✓ .gitignore patterns for ephemeral review output
     ✓ ~/.shield/projects/<name>/pm.json (PM config)
     ✓ PM adapter MCP server registered

   ⚠ Reload the Shield plugin to start the PM adapter:
     /plugin update shield@tesseract

   Enable auto-updates:
     /plugin update --auto-update shield@tesseract

   Next: try /research or /plan to start your workflow
   ```

## Important
- Do NOT create `.shield.json` without user confirmation
- Do NOT overwrite existing `.shield.json` — merge if it exists
- Do NOT store API tokens in `.shield.json` — credentials go in `~/.shield/credentials.json` only
- Validate all inputs against the JSON schemas in `${CLAUDE_PLUGIN_ROOT}/schemas/`
