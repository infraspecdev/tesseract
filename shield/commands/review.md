---
name: review
description: Run comprehensive code review with domain-specific agents and AC verification
args: "[path or scope]"
outputs:
  - review_summary    # review_type=code
  - review_detailed   # review_type=code, multiple agents
  - review_summary_html
  - review_detailed_html
---

# Review

Run a comprehensive code review that covers code correctness, domain-specific checks, agent reviews, and acceptance criteria verification.

## Usage

`/review [path or scope]`

## Paths

This command writes the following registry-tracked paths (see `shield/schema/output-paths.yaml`). All resolve under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}`:

| Registry key | Resolved path |
|---|---|
| `review_summary` | `{review_dir}/summary.md` |
| `review_detailed` (per agent) | `{review_dir}/detailed/{agent}.md` |
| `review_summary_html` | `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/summary.html` |
| `review_detailed_html` | `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/detailed/{agent}.html` |

The applied-fixes log `{review_dir}/changes.md` is a side-artifact (run history, not a deliverable) and is not in the registry. Source code itself lives outside `docs/shield/` and is therefore not covered by an `enhanced-*` deliverable (unlike PRD/plan reviews).

### Resolving the counter

Before writing, list `{output_dir}/{feature}/reviews/code/` for entries matching today's ISO date. If `{date}/` does not exist, use `_counter=""`. Otherwise, find the highest `{date}_<N>/` (with `<N>` starting at 2 for the second same-day run) and use `_counter="_<N+1>"`. Reviews never overwrite prior runs.

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Determine `{feature}` (current feature directory name, e.g. `auth-feature-20260319`; if none exists yet, derive from the current branch or story context + `-YYYYMMDD`). Resolve `{date}` and `{_counter}` per the section above.

Write artifacts using the Write tool under `{review_dir}`:

```
{review_dir}/
├── summary.md              ← {review_summary}
├── changes.md              ← applied-fixes log (side-artifact)
└── detailed/
    └── <agent>.md          ← {review_detailed} (one per dispatched agent)
```

Numbered run subfolders (`code-review/{N}-{slug}/`) are gone — runs are date-keyed and never overwrite.

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. Follow the review workflow:
   - Code correctness review on changed files
   - Domain-specific review skills (terraform, atmos, kubernetes, backend, etc.)
   - Agent reviews (security, cost, architecture, operations)
   - Acceptance criteria verification (if story context from `{plan_json}` = `{output_dir}/{feature}/plan.json`)
2. Findings are merged, deduplicated, sorted by severity
   - Per-agent detailed findings written to `{review_dir}/detailed/<agent>.md` (i.e. `{review_detailed}` with `agent=<that-subagent-slug>`)
   - Applied fixes logged to `{review_dir}/changes.md`
3. **Write `{review_summary}`, per-agent `{review_detailed}`, and the side-artifact changes log to the paths above**
4. Render HTML — produce `{review_summary_html}` and one `{review_detailed_html}` per agent under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/` via render-markdown.sh
5. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
6. Present to user with options: apply all, select specific, skip, post to PM
7. Apply selected fixes

## Single-Agent Shortcuts

- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only
- `/review-well-architected` — AWS Well-Architected Framework review
