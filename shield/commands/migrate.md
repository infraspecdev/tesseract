---
name: migrate
description: Migrate from old plugins (infra-review, clickup-sprint-planner, dev-workflow) to Shield
---

# Shield Migrate

Detect and migrate configuration from old Tesseract plugins to the Shield config structure.

## Steps

1. **Detect old plugins** — scan for:
   - `sprint-planner.json` or `clickup-sprint-planner/examples/sprint-planner.json` → ClickUp config
   - `claude/infra-review/` directory → infra-review was active
   - Old plugin directories (`infra-review/`, `clickup-sprint-planner/`, `dev-workflow/`) → detect which were installed

2. **Report findings:**
   ```
   Detected old plugins:
     - clickup-sprint-planner (sprint-planner.json found)
     - infra-review (claude/infra-review/ directory found)
     - dev-workflow (commands detected)
   ```
   If nothing detected, suggest `/shield init` instead.

3. **Gather project info:**
   - Ask for project name (default: repo directory name)
   - Infer domains from detected plugins:
     - `infra-review` detected → suggest `terraform`, `atmos`
   - Ask user to confirm/adjust

4. **Create `.tesseract.json`** with confirmed project name and domains

5. **Migrate sprint-planner.json** (if found):
   - Read the old config file
   - Map fields to new structure:

   | Old field | New location |
   |-----------|-------------|
   | `workspace_id` | `~/.tesseract/projects/<project>/pm.json` → `workspace_id` |
   | `space_id` | `~/.tesseract/projects/<project>/pm.json` → `space_id` |
   | `naming.*` | `~/.tesseract/projects/<project>/pm.json` → `naming.*` |
   | `api_token` (if present) | `~/.tesseract/credentials.json` → `clickup.api_token` |

   - Set `adapter: "clickup"` and `adapter_mode: "hybrid"` in pm.json
   - If `CLICKUP_API_TOKEN` env var is set, offer to save it to credentials.json

6. **Create `~/.tesseract/config.json`** with defaults:
   - Set `pm_tool: "clickup"` if sprint-planner was found, otherwise `"none"`
   - Set `review_on_commit.enabled: false`
   - Set default reviewers config

7. **Show migration summary:**
   ```
   Migrated sprint-planner.json:
     ✓ workspace_id → ~/.tesseract/projects/<project>/pm.json
     ✓ space_id → ~/.tesseract/projects/<project>/pm.json
     ✓ naming config → ~/.tesseract/projects/<project>/pm.json
     ⚠ No API token found in config. Add to ~/.tesseract/credentials.json manually.

   Created:
     ✓ .tesseract.json (project marker)
     ✓ ~/.tesseract/config.json (global defaults)
     ✓ ~/.tesseract/projects/<project>/pm.json (PM config)

   Old files left in place (safe to delete after verifying):
     - sprint-planner.json
     - claude/infra-review/

   Next steps:
     1. Add API token to ~/.tesseract/credentials.json
     2. Uninstall old plugins: infra-review, clickup-sprint-planner, dev-workflow
     3. Enable auto-updates: /plugin update --auto-update shield@tesseract
     4. Run /pm-status to verify ClickUp connection
   ```

## Important
- Do NOT delete old config files — leave them in place for user to verify
- Do NOT overwrite existing `~/.tesseract/` files — warn and ask
- Do NOT store API tokens in `.tesseract.json` or pm.json
- Validate migrated config against schemas in `${CLAUDE_PLUGIN_ROOT}/schemas/`
- If `sprint-planner.json` has fields not in the mapping, warn the user about unmapped fields
