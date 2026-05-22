---
name: review-backend
description: Run backend-only code review with stack detection, agnostic + framework skills, and specialist agent dispatch
args: "[path or scope] [--full]"
---

# Review Backend

Run a focused backend code review. Detects the stack (Java/Kotlin, Python, Node/TS, Go) from repo markers, loads agnostic and framework-specific skills under `shield/skills/backend/`, and dispatches cross-cutting concerns to specialist agents.

## Usage

`/review-backend [path or scope] [--full]`

- `/review-backend` (no arg, on a branch) — review changed files vs `main`
- `/review-backend services/api/` — review a specific subtree
- `/review-backend --full` or `/review-backend .` — review the whole repo (excluding the default exclude list)

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name (e.g., `auth-feature-20260319`). If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available from plan context, otherwise use the current git branch name.

Write the review summary using the Write tool to:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/summary.md
```

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. Resolve scope per the usage rules above
2. Invoke the `backend-engineer` agent with the resolved scope
3. The agent runs stack detection, loads skills, dispatches specialists, and aggregates findings — see `shield/agents/backend-engineer.md` for full agent behavior
4. Per-agent detailed findings written to `{output_dir}/{feature}/code-review/{N}-{slug}/detailed/<agent>.md`
5. Applied fixes logged to `{output_dir}/{feature}/code-review/{N}-{slug}/changes.md`
6. **Write review summary, detailed findings, and changes log to the paths above**
7. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
8. Present to user with options: apply all, select specific, skip, post to PM
9. Apply selected fixes

## Relationship to /review

`/review` is comprehensive — it includes backend, terraform, kubernetes, atmos, and any other detected domain in one pass. Use `/review-backend` when you want backend-only feedback (faster) or when running against a backend-only repo. The two commands share the same output writer; they differ only in which domain skills/agents are loaded.

## Single-Agent Shortcuts

Within a backend review, individual specialists can also be dispatched directly:

- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only (note: not dispatched from `/review-backend` because cost is infra-flavored)
- `/review-well-architected` — AWS Well-Architected Framework review (not dispatched from `/review-backend`)
