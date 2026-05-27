---
name: plan-docs
description: Use when breaking down a project phase into stories with acceptance criteria, creating ADRs, or planning infrastructure work. Triggers on /plan, story breakdown, detailed plan, architecture doc.
---

# Plan Docs

**You MUST produce all five artifacts. No exceptions.**

## Output Paths — MANDATORY

Write each artifact using the Write tool to **exactly** these paths:

| Registry key | Resolved path | Purpose |
|---|---|---|
| `plan_json` | `{output_dir}/{feature}/plan.json` | Machine-readable sidecar (source of truth for stories/tasks/ACs/design_refs, PM-sync target) |
| `plan_trd_md` | `{output_dir}/{feature}/trd.md` | Canonical Technical Requirements Document — 14 sections, domain-aware. Replaces the legacy `plan-architecture.md`. |
| `plan_md` | `{output_dir}/{feature}/plan.md` | Canonical detailed-plan markdown — the "what to do" (narrative view of plan.json) |
| `plan_trd_html` | `{output_dir}/{feature}/outputs/trd.html` | Rendered TRD HTML (rendered from `{plan_trd_md}`) |
| `plan_html` | `{output_dir}/{feature}/outputs/plan.html` | Rendered detailed plan HTML (rendered from `{plan_md}`) |

**Legacy keys** (`plan_arch_md`, `plan_arch_html`): kept in `shield/schema/output-paths.yaml` with `deprecated: true` for a transition window. `/plan` no longer writes to them. Existing `plan-architecture.md` files in old feature folders are **never** modified or deleted by `/plan` re-runs — see "Re-run behavior" in `trd-template.md`.

The global dashboard `{output_dir}/index.html` is updated as a side effect of every run (cross-feature artifact, not a per-run deliverable).

Where:
- `{output_dir}` — read from `.shield.json` `output_dir` field (default: `docs/shield`)
- `{feature}` — `{feature-name}-YYYYMMDD`, derived from plan name in kebab-case (e.g., `input-validation-20260319`)

Numbered run subfolders (`plan/{N}-{slug}/`) are gone — each plan is a single canonical pair of markdown sources at feature root, with rendered HTML under `outputs/`. Re-running `/plan` on the same feature updates the same files (the plan.json sidecar is the source of truth and is updated in place).

**Do NOT** use any other path, filename, or directory. The Write tool creates directories automatically. After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

## Critical: Sidecar First, Markdown Second, HTML Last

**Always generate the sidecar JSON first, then the markdown sources, then render HTML.** The sidecar (`{plan_json}`) is the structured source of truth for stories/tasks/ACs/design_refs (used by PM-sync and tooling). The markdown files (`{plan_md}`, `{plan_trd_md}`) are the human-readable narrative deliverables — `plan.md` is a markdown render of plan.json's stories with prose context, and `trd.md` is the canonical Technical Requirements Document (14 sections, see `trd-template.md`). The HTML files are rendered from the markdown via `scripts/render-markdown.sh` (the same helper `/prd` uses), so they share the strict CommonMark guarantees.

When anything changes (AC edits, status updates, PM sync), the sidecar is updated, the markdown is regenerated from the sidecar (plus preserved TRD prose), and the HTML is re-rendered.

## Plan Sidecar JSON

The sidecar MUST be written to `{plan_json}` = `{output_dir}/{feature}/plan.json`. See `sidecar-schema.md` for the full JSON schema and rules.

## When to Use

- Creating a new project phase or milestone
- Breaking down a large initiative into executable stories
- Writing an architecture decision record with a paired execution plan
- User mentions "phase plan", "detailed plan", "architecture doc", "story breakdown"
- Invoked by the `/plan` command

## When NOT to Use

- Pure research without implementation stories — use `/research` instead
- Reviewing an existing plan — use `/plan-review` instead
- Single task that doesn't need stories — just implement directly

## Markdown Sources (canonical)

After the sidecar is created, generate the two markdown source files. These are the canonical, human-readable deliverables. HTML is rendered from them.

### 1. `{plan_trd_md}` — Technical Requirements Document

The 14-section TRD that replaces the legacy `plan-architecture.md`. **See
`trd-template.md` for the full template, per-section domain-aware authoring
guidance, the `n/a — <reason>` escape pattern, the anchor convention, and the
provenance-stamp + atomic-write rules.**

**Authoring loop:**
1. Detect the dominant domain (read `.shield.json` `plan.template_override` first;
   otherwise scan repo markers per `shield/commands/plan.md`).
2. For each of the 14 sections in `shield/schema/trd-sections.yaml` (in canonical
   order §1 → §14):
   - Emit `## §N Title {#section-id}` with the exact slug from the YAML.
   - Choose the per-section authoring guidance from `trd-template.md`:
     - backend / infra / mixed (mixed emits `[backend]` and `[infra]` labeled
       subsections inside `domain_divergent` sections).
   - Fill the body with concrete content. If a section genuinely does not apply,
     write `n/a — <reason>` on a single line (no vague TBDs, no silent omissions).
3. Stamp the first line after frontmatter:
   `<!-- generated by /plan v{shield-plugin-version} on {YYYY-MM-DD} -->`.
4. Write `trd.md.tmp` first, then rename to `trd.md` (atomic write — never leave
   a partial file behind).
5. **Do not delete** any existing `plan-architecture.md` in the same folder.

### 2. `{plan_md}` — Detailed Execution Plan

The "what to do" — stories rendered as markdown from the sidecar plus narrative context.

**Structure:**
1. Phase heading with summary
2. Epic metadata (name, status, timeline)
3. Stories summary table with status
4. Story sections — each rendered from the sidecar data (description, tasks, ACs)
5. A sidecar back-reference line at the top: `<!-- sidecar: ./plan.json -->`

## HTML Render

After the markdown sources are written, render both into `{output_dir}/{feature}/outputs/` using `render-markdown.sh` (the same helper `/prd` uses — strict CommonMark + plugins):

```bash
cd "{output_dir}/{feature}"
mkdir -p outputs

# TRD
"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    trd.md \
  --shell trd.shell.html \
  --out   outputs/trd.html

# Detailed plan
"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" \
  --md    plan.md \
  --shell plan.shell.html \
  --out   outputs/plan.html
```

Each rendered HTML file MUST include a meta tag in its shell template that references the sidecar:
```html
<meta name="sidecar" content="../plan.json">
```

Delete the `.shell.html` files once the helper succeeds.

### Story Format in HTML

Each story renders from the sidecar JSON:

```
┌─ Story N: [name from sidecar] ──────────────────────┐
│  [Status badge]  [Week range]                         │
│                                                       │
│  Description (from sidecar.description)              │
│                                                       │
│  Tasks (from sidecar.tasks)                          │
│  - [ ] Task 1                                        │
│  - [ ] Task 2                                        │
│                                                       │
│  Acceptance Criteria (from sidecar.acceptance_criteria)│
│  - [ ] Criterion 1                                   │
│  - [ ] Criterion 2                                   │
└───────────────────────────────────────────────────────┘
```

## CSS & HTML Templates

See `templates.md` in this skill directory for CSS and HTML scaffolding. Key rules:
- h1/blockquote accent: `#1a73e8` (blue)
- `max-width: 900px` for architecture, `960px` for detailed plan

## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Condition | Mandatory |
|------|--------|-----------|-----------|
| 1 | Gather requirements | skip if spec/topic provided | No |
| 1a | Detect prior PRD in feature folder | skip if no PRD exists | No |
| 2 | Check for prior research / gather context | skip if no research exists | No |
| 2a | Milestone resolution — extract from PRD §15/§8 or invoke `shield:milestone-coverage` as fallback; user refines | always | Yes |
| 2b | Detect dominant domain — `.shield.json` `plan.template_override` first, then repo markers (backend / infra / mixed) | always | Yes |
| 3 | Generate `{plan_json}` sidecar (stories include `design_refs[]` pointing into the TRD) | always | Yes |
| 4 | Generate `{plan_trd_md}` per the 14-section TRD template (atomic write, provenance stamp) | always | Yes |
| 5 | Generate `{plan_md}` (detailed plan markdown) | always | Yes |
| 6 | Render `{plan_trd_html}` and `{plan_html}` via render-markdown.sh | always | Yes |
| 7 | Update manifest + index.html | always | Yes |

## Workflow

1. **Load prior research** — read `{output_dir}/{feature}/research.md` (i.e. `{research}`) if it exists, and use the research findings to inform the plan. Falls back to `.session-transcript.md` only if `research.md` is absent. If neither exists, proceed without it.
1a. **Detect prior PRD in feature folder** — read `{output_dir}/{feature}/prd.md` (i.e. `{prd}`). If it exists:
   - Read the PRD content
   - Read its `prd.meta.json` for type, sections_present, status
   - Treat the PRD as authoritative context for: Problem, Users, Goals, Stories, NFRs, Risks
   - Append this plan's `{plan_md}` path to `prd.meta.json.linked_plans` (auto-updates the bidirectional linkage)
   - Record `source_prd` (relative path to prd.md) and `prd_rubric_version_at_planning` (read from prd.meta.json.rubric_version) into the `{plan_json}` sidecar
2. **Gather context** — ask about: problem being solved, existing infrastructure, proposed approach, dependencies, timeline

### 2a. Milestone resolution

Before generating stories, resolve milestones:

- **If a PRD was detected (Step 1a) and it contains milestones** (Section 15 standard, Section 8 lean): extract them. Present to the user for confirmation. Allow edits (rename, add exit criteria, change depends_on). Copy approved milestones into the sidecar `milestones[]`.

- **If a PRD was detected but has no milestones** (or an empty Milestones table — back-compat case for PRDs authored against rubric_version 1.0): invoke `shield:milestone-coverage` with:
   - `personas`: from PRD Section 4
   - `goals`: from PRD Section 6
   - `stories`: from PRD Section 8 (if present; empty for lean)
   - `feature_domain`: inferred or read from PRD type-detection metadata

   Present merged proposal + `open_conflicts` to the user (same flow as `/prd` §7a). User refines. Sidecar-only — do NOT write back to the PRD.

- **If no PRD exists:** invoke `shield:milestone-coverage` with whatever inputs were gathered during requirements (Step 2). Sidecar-only.

- **If the user explicitly opts out of milestones:** sidecar stores `milestones: []`. All subsequent stories will have `milestone_id: null`. This is the back-compat single-implicit-milestone case (see `sidecar-schema.md`).

3. **Read `.shield.json`** — get project name, active domains, and `plan.template_override` (`backend` | `infra` | `mixed` | unset → auto-detect)
3a. **Resolve domain** — if `plan.template_override` is set, use it; otherwise walk repo markers per `shield/commands/plan.md` §Domain detection. If both infra and backend markers are present, domain is `mixed`. The chosen domain selects per-section TRD guidance (see `trd-template.md`).
4. **Generate sidecar JSON first (milestone-by-milestone)** — write `{plan_json}`:
   - For each milestone in `milestones[]` (resolved in §2a), generate the epics and stories needed to satisfy that milestone's exit criteria. Each story is born with `milestone_id` set to the milestone's `id`.
   - For each story, populate `design_refs[]`: at minimum one entry pointing at the TRD section the story implements (typically §7 high-level-design, §10 milestones, or §11 apis-involved). For LLD references, emit a placeholder with `doc='lld'`, `component=null`, `anchor_url=null`, `label='TODO: link when /lld <component> lands'`. See `sidecar-schema.md` "design_refs[]" for the exact field shape and merge rules.
   - When `milestones: []` (opt-out case), generate stories flat with `milestone_id: null` on each — the back-compat path.
   - Acceptance criteria per story remain the same testable standard; exit criteria on the milestone are the higher-level rollup.
5. **Verify sidecar quality** — every story has tasks, testable acceptance criteria, and at least one `design_refs[]` entry (TRD anchor or LLD placeholder)
6. **Generate `{plan_trd_md}`** — emit the 14-section TRD per `trd-template.md`. Atomic write (`trd.md.tmp` → rename). Provenance stamp on the first line after frontmatter. **Do not delete or modify any existing `plan-architecture.md`.**
7. **Generate `{plan_md}`** (detailed plan markdown) — renders stories from the sidecar as markdown sections; includes a `<!-- sidecar: ./plan.json -->` reference at top
8. **Render HTML** — invoke `render-markdown.sh` per the "HTML Render" section above to produce `{plan_trd_html}` and `{plan_html}` under `{output_dir}/{feature}/outputs/`
9. **Invoke `shield:summarize`** — produce a plan summary
10. **Offer next steps:**
   - `/plan-review` — multi-agent review of the plan
   - `/pm-sync` — sync stories to project management tool

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing only the markdown without HTML render | You MUST produce all 5 artifacts: `{plan_json}` + `{plan_md}` + `{plan_trd_md}` + `{plan_html}` + `{plan_trd_html}` |
| Skipping HTML because "it's simpler" | HTML is required. Render from the markdown via `render-markdown.sh`. Hand-rendered HTML or pandoc/python-markdown output is NOT acceptable (same rules as `/prd`) |
| Generating markdown or HTML without the sidecar | Always write `{plan_json}` first; markdown is derived from it, HTML is derived from markdown |
| Writing `plan-architecture.md` instead of `trd.md` | The plan-architecture.md path is deprecated. Always write the 14-section TRD to `{plan_trd_md}` = `{output_dir}/{feature}/trd.md`. Existing `plan-architecture.md` files are left in place but never created or overwritten by `/plan`. |
| Omitting the `{#section-id}` anchor on TRD headers | Every TRD section header MUST carry the kebab-case anchor from `shield/schema/trd-sections.yaml`. The validator and `/plan-review` reject TRDs without anchors. |
| Leaving a TRD section body as "TBD" or empty | Either fill the section with concrete content OR write `n/a — <reason>` on a single line. Vague TBDs and silent omissions fail the eval. |
| Writing an extra (15th+) section in the TRD | The slug allow-list in `trd-sections.yaml` is exhaustive. Drift-by-addition fails the eval. |
| Writing under a numbered run folder (`plan/{N}-{slug}/`) | Numbered run subfolders are gone — write the markdown sources flat at `{output_dir}/{feature}/` and render HTML under `{output_dir}/{feature}/outputs/` |
| Vague acceptance criteria | Testable: specific commands, measurable states |
| Missing acceptance criteria on stories | Every story MUST have at least 1 criterion |
| Missing `design_refs[]` on stories | Every story SHOULD carry at least one TRD design_ref. LLD refs may be TODO placeholders until `/lld` lands. |
| Empty tasks list | Every story needs concrete, actionable tasks |
| Not reading .shield.json | Project name, domains, and `plan.template_override` come from the marker |
| Writing to `shield/plan.json` (old path) | Write to `{plan_json}` = `{output_dir}/{feature}/plan.json` — plan sidecar at feature root |
