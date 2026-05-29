---
name: backlog
description: Capture, view, promote, and remove entries from the project backlog at docs/shield/backlog.json
---

# Backlog

Lightweight idea-capture for Shield projects. Entries live in a single global
`docs/shield/backlog.json`. Each entry is associated with a **feature** (the
reconciliation key) and an **epic** (the removal gate); either may be
proposed-new at capture.

## Usage

```
/backlog                                  # render the ordered backlog with status badges (alias of view)
/backlog view                             # explicit view
/backlog add "Rotate refresh tokens" \
            --feature auth --epic "Session mgmt"
/backlog remove <id>
/backlog promote <id> [--step plan|implement|prd|research]
/backlog sweep                            # run lazy reconciliation without rendering
```

## Paths

| Artifact | Path |
|---|---|
| Store | `docs/shield/backlog.json` |
| Removal log (recovery) | `.shield/backlog-removed.log` |
| Kill switch | `.shield.json` → `backlog.auto_reconcile` (default `true`) |

## Behavior

1. **view** — Read `docs/shield/backlog.json`; render entries sorted by `order`.
   Each line shows id, feature, epic, source, text. Pipeline status badges
   (`research / prd / plan`) are derived from `docs/shield/manifest.json`
   artifact flags at view time. Empty backlog renders `Backlog is empty — no entries.`
   The view path optionally runs a lazy reconciliation sweep before rendering
   (controlled by `.shield.json` kill switch).

2. **add** — Append an entry via `shield_backlog.store.capture()`. The helper
   assigns a fresh uuid4 id and the next integer `order`. Writes are atomic
   (temp-then-rename) with compare-before-replace; a concurrent on-disk change
   between read and replace is refused with `BacklogInvalid(lost_update)`.
   If no `--feature`/`--epic` matches the suggester output, the user may
   accept a proposed-new value at the prompt.

3. **remove** — Delete an entry by id. Plain delete, no retained history.
   A missing id reports `id_not_found` (exit 1). Recoverability boundary:
   `git revert` recovers only entries that reached a commit; a manual
   remove of an uncommitted entry is unrecoverable by design.

4. **promote** — Print the suggested next-step command (`/research`,
   `/prd`, `/plan`, or `/implement`) plus the transient `--backlog-ref <id>`
   to pass through. The reference is a **runtime argument only** — it is
   never stamped into `plan.json` or any story record (F6).
   The user starts the actual command; `/backlog` never auto-routes.

5. **sweep** — Standalone lazy reconciliation: walk all entries and remove
   any whose epic's work has since landed in `plan.json.epics[]` (matched
   by normalized exact name). Ambiguity, no-match, or unrecognized shape
   → entry stays. Every removal is logged with rationale (F9) and
   appended to `.shield/backlog-removed.log` for recovery.

## Implementation

The slash command dispatches to `shield/scripts/backlog_store.py`:

```bash
uv run --with jsonschema shield/scripts/backlog_store.py view
uv run --with jsonschema shield/scripts/backlog_store.py add "text" --feature X --epic Y
uv run --with jsonschema shield/scripts/backlog_store.py remove <id>
uv run --with jsonschema shield/scripts/backlog_store.py promote <id> --step plan
uv run --with jsonschema shield/scripts/backlog_store.py sweep
```

Skills can call the same code by importing the package directly:

```python
from shield_backlog import capture
new_id = capture("captured-mid-task idea", feature="auth", epic="Session mgmt", source="agent")
```

## Kill switch

Set `backlog.auto_reconcile: false` in `.shield.json` to disable eager prune
(end of /plan, /implement) and lazy sweep. Manual `remove` continues to work.
See `shield/skills/general/backlog/SKILL.md` for the recovery procedure when
a wrong removal happens.
