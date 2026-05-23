---
name: review-backend
description: Run backend-only code review with stack detection, agnostic + framework skills, and specialist agent dispatch
args: "[path or scope] [--full]"
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, agent=backend-engineer (+ any specialists dispatched)
  - review_summary_html
  - review_detailed_html
---

# Review Backend

Run a focused backend code review. Detects the stack (Java/Kotlin, Python, Node/TS, Go) from repo markers, loads agnostic and framework-specific skills under `shield/skills/backend/`, and dispatches cross-cutting concerns to specialist agents.

## Usage

`/review-backend [path or scope] [--full]`

- `/review-backend` (no arg, on a branch) — review changed files vs `main`
- `/review-backend services/api/` — review a specific subtree
- `/review-backend --full` or `/review-backend .` — review the whole repo (excluding the default exclude list)

## Paths

Writes registry-tracked paths under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}` (review_type=code; primary agent=backend-engineer, with additional specialists writing their own `{review_detailed}` entries). See `shield/schema/output-paths.yaml` and the counter-resolution rule in `/review`. `changes.md` is a side-artifact (applied-fixes log, not in registry).

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name; if none exists yet, derive from current branch or story context + `-YYYYMMDD`). Resolve `{date}{_counter}` per the counter rule in `/review` (today's ISO date in `YYYY-MM-DD` format; empty `_counter` for first same-day run, `_2`/`_3`/... otherwise).

Write findings under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}/`:

```
{review_dir}/
├── summary.md              ← {review_summary}
├── changes.md              ← applied-fixes log (side-artifact)
└── detailed/
    ├── backend-engineer.md ← {review_detailed} (agent=backend-engineer)
    └── <specialist>.md     ← {review_detailed} (one per dispatched specialist)
```

Numbered run subfolders (`code-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. Resolve scope per the usage rules above
2. Invoke the `backend-engineer` agent with the resolved scope
3. The agent runs stack detection, loads skills, dispatches specialists, and aggregates findings — see `shield/agents/backend-engineer.md` for full agent behavior
4. Per-agent detailed findings written to `{review_dir}/detailed/<agent>.md` (i.e. `{review_detailed}` with the dispatched subagent's slug)
5. Applied fixes logged to `{review_dir}/changes.md` (side-artifact)
6. **Write `{review_summary}`, per-agent `{review_detailed}`, and the changes log to the paths above**
7. Render `{review_summary_html}` and `{review_detailed_html}` (per agent) under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/`
8. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
9. Present to user with options: apply all, select specific, skip, post to PM
10. Apply selected fixes

## Relationship to /review

`/review` is comprehensive — it includes backend, terraform, kubernetes, atmos, and any other detected domain in one pass. Use `/review-backend` when you want backend-only feedback (faster) or when running against a backend-only repo. The two commands share the same output writer; they differ only in which domain skills/agents are loaded.

## Single-Agent Shortcuts

Within a backend review, individual specialists can also be dispatched directly:

- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only (note: not dispatched from `/review-backend` because cost is infra-flavored)
- `/review-well-architected` — AWS Well-Architected Framework review (not dispatched from `/review-backend`)
