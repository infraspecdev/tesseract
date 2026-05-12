# github-sprint-planner — Implementation Notes

**Date:** 2026-04-28
**Status:** Implemented (v1.0.0)
**PR:** https://github.com/infraspecdev/tesseract/pull/36

---

## What was built

A Claude Code plugin for sprint planning with GitHub Issues + Projects v2. Teams write sprint plan documents (HTML or markdown), then use the plugin to bulk-create GitHub Issues, link them as sub-issues to epics, and add them to a Projects v2 board — all in one command.

---

## How it works

```
1. User writes a plan doc (HTML file with story divs)
        ↓
2. /sprint-sync → parses plan doc + fetches current GitHub Issues
        ↓
3. Shows diff: which stories exist, which need to be created
        ↓
4. User confirms → sprint_bulk_create fires
        ↓
5. Issues created, linked to epic as sub-issues, added to Projects v2
        ↓
6. /sprint-status → shows epic overview table
```

---

## Files delivered

| File | Purpose |
|------|---------|
| `server/main.py` | FastMCP entry point — loads config, wires up all tools |
| `server/github_client.py` | GitHub REST v3 + GraphQL v4 wrapper |
| `server/config.py` | Pydantic models for `sprint-planner.json` |
| `server/action_log.py` | Append-only JSON log of all mutations |
| `server/parsers/html_parser.py` | Parses HTML plan docs via BeautifulSoup |
| `server/tools/sync.py` | `sprint_sync` — read-only diff |
| `server/tools/bulk_create.py` | `sprint_bulk_create` — create + link + add to project |
| `server/tools/bulk_update.py` | `sprint_bulk_update` — batch update assignees/labels/state |
| `server/tools/bulk_rename.py` | `sprint_bulk_rename` — preview/apply epic prefix renames |
| `server/tools/sprint_status.py` | `sprint_status` — epic overview with stats |
| `server/tools/action_log_tool.py` | `sprint_action_log` — query past operations |
| `commands/sprint-sync.md` | `/sprint-sync` slash command |
| `commands/sprint-plan.md` | `/sprint-plan` slash command |
| `commands/sprint-status.md` | `/sprint-status` slash command |
| `skills/sprint-planning/SKILL.md` | Auto-invoked skill — guides Claude to use bulk tools |
| `.gitignore` | Excludes `sprint-planner.json` and `epics/` |
| `examples/sprint-planner.example.json` | Example config |
| `README.md` | Setup and usage docs |

---

## Key implementation decisions

- **Projects v2 uses GraphQL** — REST API has no Projects v2 write support. All project board operations (add item, set iteration) go through GraphQL v4.
- **Sub-issue linking is native** — GitHub has a native sub-issues API (`POST /issues/{parent}/sub_issues`). No custom fields needed.
- **`gh auth token` fallback** — If `GITHUB_TOKEN` env var is not set, the server calls `gh auth token` automatically so users who ran `gh auth login` don't need to set anything.
- **Preview before mutating** — `sprint_sync` and `sprint_bulk_rename` both default to read-only/preview mode. Writes only happen when `apply=True` or the user confirms.
- **Action log** — Every write operation is appended to a JSON log with enough info to roll back manually.
