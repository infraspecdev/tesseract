---
name: research
description: Research a technical topic with structured citations and expert sources
---

# Research

Research a technical topic and produce a well-sourced document with direct quotes, industry references, and a clear recommendation.

## Usage

`/research [topic]`

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Then write the final document using the Write tool to:

```
{project_root}/shield/docs/research-YYYYMMDD-HHMMSS.md
```

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`, and `YYYYMMDD-HHMMSS` with the current date and time.

Example: if `.shield.json` is at `/home/user/myproject/.shield.json`, write to `/home/user/myproject/shield/docs/research-20260315-170930.md`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. If a topic is provided as an argument, use it directly
2. If no topic, ask the user what they'd like to research
3. Follow the research workflow: clarify scope, launch parallel research agents, synthesize findings
4. **You MUST write the document to the path above using the Write tool** — do not just output it as text
5. After writing, confirm the file path to the user
