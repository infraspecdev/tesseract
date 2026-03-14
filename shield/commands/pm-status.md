---
name: pm-status
description: Show sprint/epic status overview from your PM tool
args: "[epic] [--by status|assignee]"
---

# PM Status

Show sprint or epic status overview from your project management tool.

## Usage

`/pm-status [epic] [--by status|assignee]`

## Arguments

- `epic` (optional) — specific epic ID to show detail for
- `--by status|assignee` (optional) — group stories by status or assignee (default: by epic)

## Behavior

1. Check that a PM tool is configured
2. Call `pm_get_capabilities` to verify adapter supports status
3. Call `pm_get_status` with the epic filter and grouping option
4. Present results as a formatted table:
   - Epic summary: Total, Done, In Progress, Ready, Blocked
   - Story detail when specific epic is requested
5. If no PM tool configured, check if a plan sidecar JSON exists and show status from that instead
