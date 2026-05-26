---
name: pm-sync
description: Sync plan stories to your PM tool (ClickUp, Jira, etc.)
outputs:
  - plan_json    # updated in place with PM tool IDs and URLs after sync
---

# PM Sync

Sync plan document stories against your project management tool.

## Usage

`/pm-sync`

## Paths

This command mutates `{plan_json}` = `{output_dir}/{feature}/plan.json` in place — adding PM tool IDs and URLs to stories after sync. It does NOT write any new files; the `{plan_md}` / `{plan_html}` renders are regenerated from the updated sidecar by the `/plan` rendering flow.

## Behavior

1. Check that a PM tool is configured (`~/.shield/projects/<project>/pm.json` → `adapter`)
2. If not configured, suggest running `/shield init` to set up PM integration
3. Invoke the `shield:pm-sync` skill
4. The skill:
   - Calls `pm_get_capabilities` to verify adapter supports sync
   - Reads `{plan_json}` = `{output_dir}/{feature}/plan.json` for story data
   - Calls `pm_sync` to diff against PM state
   - Presents diff as table (match/new/updated/unlinked)
   - Asks user: apply all / pick which / cancel
   - For new stories: calls `pm_bulk_create`
   - For updates: calls `pm_bulk_update`
   - Updates `{plan_json}` with PM IDs and URLs
   - Re-renders `{plan_md}` / `{plan_html}` from the updated sidecar
5. Invoke `shield:summarize` to produce a sync summary
6. Offer next steps: `/pm-status`, `/implement`
