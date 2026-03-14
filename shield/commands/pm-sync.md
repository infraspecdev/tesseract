---
name: pm-sync
description: Sync plan stories to your PM tool (ClickUp, Jira, etc.)
---

# PM Sync

Sync plan document stories against your project management tool.

## Usage

`/pm-sync`

## Behavior

1. Check that a PM tool is configured (`~/.tesseract/config.json` → `pm_tool`)
2. If not configured, suggest running `/shield init` to set up PM integration
3. Invoke the `shield:pm-sync` skill
4. The skill:
   - Calls `pm_get_capabilities` to verify adapter supports sync
   - Reads the plan sidecar JSON for story data
   - Calls `pm_sync` to diff against PM state
   - Presents diff as table (match/new/updated/unlinked)
   - Asks user: apply all / pick which / cancel
   - For new stories: calls `pm_bulk_create`
   - For updates: calls `pm_bulk_update`
   - Updates the sidecar JSON with PM IDs and URLs
   - Re-renders HTML from updated sidecar
5. Invoke `shield:general:summarize` to produce a sync summary
6. Offer next steps: `/pm-status`, `/implement`
