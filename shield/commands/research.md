---
name: research
description: Research a technical topic with structured citations and expert sources
---

# Research

Research a technical topic and produce a well-sourced document with direct quotes, industry references, and a clear recommendation.

## Usage

`/research [topic]`

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read the `output_dir` field from `.shield.json` (default: `docs/shield` if not set). Then write the final document using the Write tool to:

```
{project_root}/{output_dir}/{feature-name}-YYYYMMDD/research/{N}-{slug}/findings.md
```

Where:
- `{output_dir}` = the `output_dir` value from `.shield.json` (default: `docs/shield`)
- `{feature-name}` = the active feature name (from context or user input)
- `YYYYMMDD` = the date the feature folder was created
- `{N}` = run number, determined by counting existing folders in `{feature-name}-YYYYMMDD/research/` + 1
- `{slug}` = slugified version of the research topic argument (kebab-case)

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

Example: if `.shield.json` is at `/home/user/myproject/.shield.json` with `output_dir: "docs/shield"`, and the feature is `auth-flow-20260319`, write to `/home/user/myproject/docs/shield/auth-flow-20260319/research/1-oauth-token-caching/findings.md`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. If a topic is provided as an argument, use it directly
2. If no topic, ask the user what they'd like to research
3. If no active feature context, ask the user: "No active feature context. What feature name should this go under?"
4. Read `output_dir` from `.shield.json` (default: `docs/shield`)
5. Determine the run number by counting existing folders in `{feature-name}-YYYYMMDD/research/` + 1
6. Derive the slug from the research topic argument (kebab-case)
7. Follow the research workflow: clarify scope, launch parallel research agents, synthesize findings
8. **You MUST write the document to the path above using the Write tool** — do not just output it as text
9. After writing, update `manifest.json` in `{output_dir}/` and regenerate `{output_dir}/index.html`
10. Confirm the file path to the user
