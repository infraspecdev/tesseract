---
name: prd-docs
description: Use when authoring a new PRD or upgrading a lean PRD to standard. Walks user through 17-section problem-first scaffold (or 7-section lean), pre-populates from prior /research transcript if present, invokes shield:story-coverage between Sections 4 and 6, supports custom team templates via .shield.json. Triggers on /prd, write a PRD, author a PRD.
---

# PRD Docs

Author a new PRD with the Shield 17-section problem-first scaffold (or lean variant), or upgrade an existing lean PRD to standard by adding missing sections.

## Output Path — MANDATORY

```
{output_dir}/{feature}/prd/{N}-{slug}/
├── prd.md
├── prd.html
└── prd.meta.json
```

Where `{output_dir}` comes from `.shield.json`, `{feature}` is the feature folder, `{N}` is sequential. The `prd.meta.json` records type, status, owner, last_updated, rubric_version, and `linked_plans` (auto-populated by `/plan` when it runs).

## When to Use

- User invokes `/prd` to author a new PRD
- User invokes `/prd` in a feature folder containing a lean PRD (triggers upgrade flow)

## When NOT to Use

- **Review an existing PRD** — use `/prd-review` instead
- **Generate a plan from a PRD** — use `/plan` instead
- **Capture pre-PRD context** — use `/research` instead

## Step Skeleton

| Step | Action | Condition | Mandatory |
|---|---|---|---|
| 1 | Read `.shield.json` for `prd_template`, `prd_required_sections` | always | Yes |
| 2 | Resolve feature folder context (`--feature`, current feature, or prompt) | always | Yes |
| 3 | Check for prior PRD in feature folder (lean → trigger upgrade flow) | only if prior PRD exists | conditional |
| 4 | Ask user for PRD type (standard | lean) | always | Yes |
| 5 | Check for prior `/research` transcript; pre-populate Problem/Users/Constraints if present | only if research exists | conditional |
| 6 | Walk Sections 1-4 (Header, Problem, Personas, Goals) | always | Yes |
| 7 | Invoke `shield:story-coverage` skill between Sections 4 and 6; scaffold expected stories | always (standard only; skip for lean) | conditional |
| 8 | Walk Sections 5, 6 content, 7-17 | always (lean: only 5, 16, 17) | Yes |
| 9 | Apply custom-template merging if `.shield.json.prd_template` is set | only if config set | conditional |
| 10 | Write `prd.md`, `prd.html`, `prd.meta.json` | always | Yes |
| 11 | Update manifest, regenerate index.html | always | Yes |

## Workflow

### 1. Configuration

Read `.shield.json`:
- `output_dir` (default `docs/shield`)
- `prd_template` (default null — use built-in scaffold from `templates.md`)
- `prd_required_sections` (default: ["Problem", "Goals & non-goals", "Success metrics", "Out of scope", "Open questions"] — see spec)

### 2. Feature context

Determine which feature folder this PRD belongs to:
- If `--feature <name>` flag passed → use that
- Else look at current working directory hint (recent activity) and ask user to confirm
- If no prior feature folders exist → create one with today's date

### 3. Detect prior lean PRD (upgrade flow)

Glob `{output_dir}/{feature}/prd/*/prd.meta.json`. If any have `type: "lean"`:

Offer the user a multi-select:

```
I found a lean PRD in this feature folder. What would you like to do?

  [ ] Add sections (a new run is created with your existing content + new sections)
       [x] Section 6 — User stories & scenarios
       [x] Section 7 — Functional requirements
       [x] Section 8 — Non-functional requirements
       [x] Section 9 — RBAC & permissions matrix
       [x] Section 10 — Dependencies
       [x] Section 11 — Risks & mitigations
       [x] Section 12 — Assumptions
       [x] Section 13 — Rollout plan
       [x] Section 14 — Cost & resource impact
       [x] Section 15 — GTM & customer-comms
       [x] Section 16 — Support / CX impact

  ( ) Start fresh — new run, blank slate
  ( ) Cancel
```

If user picks "Add sections":
- Create new run folder `prd/{N+1}-{slug}/`
- Copy existing lean content forward
- Walk the user through the chosen new sections only

If "Start fresh" or no prior lean PRD detected, proceed to Step 4.

### 4. PRD type prompt

```
Which PRD type would you like?
1. Standard — full 17-section scaffold (recommended for substantial features)
2. Lean — 7-section variant (good for 1-pagers, small features, "stop me if this is wrong" docs)
```

Record user choice. Type is per-invocation; not stored in `.shield.json`.

### 5. Pre-populate from prior research

Look for `{output_dir}/{feature}/research/*/transcript.md` (Phase C, falls back to `findings.md` if Phase C not yet shipped). If found:
- Read it
- Extract Problem context, Target Users (personas), Constraints (Existing systems / compliance markers)
- Pre-populate the corresponding sections in the PRD draft
- Tell user: "I pre-populated Sections 2 (Problem), 3 (Personas), 10 (Dependencies) from your research transcript. Confirm or edit before we continue."

### 6. Walk Sections 1-4

For each of Sections 1, 2, 3, 4: present the template fields and ask the user for content. Skip pre-populated fields unless user wants to edit.

### 7. Story coverage scaffolding (standard only)

Once Sections 3 (Personas) and 4 (Goals) are captured, invoke `shield:story-coverage` skill with:
- `personas`: from Section 3
- `goals`: from Section 4
- `feature_domain`: inferred (see story-coverage SKILL.md "Domain detection")

The skill returns `expected_stories[]`. Present them to the user with multi-select:

```
For coverage of your personas and goals, you'll likely want these stories:

  [x] P1-S1 — Anika resets her password (persona-goal: P1 + G1, severity P0)
  [x] P1-S2 — Anika handles login lockout (archetype: account-recovery, severity P1)
  [x] P2-S1 — Rohan changes his email (archetype: email-change, severity P2)

Pick which to scaffold (defaults to all suggested), or add your own.
```

Selected stories are seeded into Section 6 with the standard story template structure (blank for the user to fill).

### 8. Walk remaining sections

Walk Sections 5, then Section 6 (filling in content for the scaffolded stories), then 7-17 in order.

For lean PRDs, only walk the lean scaffold's sections 5 (Success metrics), 6 (Open questions), 7 (Out of scope) — these map to standard sections 5, 17, 18. Do NOT walk standard sections 6-16; lean omits them intentionally. Use the lean scaffold from `templates.md`, not the standard one.

### 9. Custom-template merging

If `.shield.json.prd_template` is set:
- Read the custom template file
- Parse its top-level `##` headings
- Compare against `prd_required_sections`
- For any required section MISSING in the custom template, APPEND it to the end with a marker:
  ```markdown
  ## Required section — added by Shield
  <!-- Shield: added required section -->
  (Author content here)
  ```
- Report to user: "Your template was missing: <list>. I appended them at the end."
- Walk the user through filling content for any sections they hadn't yet filled

### 10. Write artifacts

- Write `{output_dir}/{feature}/prd/{N}-{slug}/prd.md`
- Render `prd.html` via the helper (see `templates.md` → HTML render template):
  1. Write `prd.shell.html` next to `prd.md` containing the full HTML scaffold from `templates.md` with a literal `{{BODY}}` placeholder where the markdown body should appear. Fill in the title and meta-banner directly (owner, status, sidecar/research links) — those are not placeholders.
  2. Run `"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" --md prd.md --shell prd.shell.html --out prd.html`.
  3. Delete `prd.shell.html` once the helper succeeds.
  Do NOT hand-render `prd.html` or pipe through pandoc/`python-markdown` — those mis-handle nested lists, lists-after-paragraphs, and loose/tight wrapping.
- Write `{output_dir}/{feature}/prd/{N}-{slug}/prd.meta.json` (per `meta-schema.md`)

### 11. Update dashboard

- Append new entry to `{output_dir}/manifest.json`
- Regenerate `{output_dir}/index.html`

### 12. Offer next steps

```
PRD authored. What's next?

- /prd-review prd/{N}-{slug}/prd.md   — review for gaps
- /plan                                — generate a technical plan from this PRD
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing prd.md without prd.meta.json | Both are mandatory; meta.json holds the type + linked_plans for downstream commands |
| Skipping story-coverage scaffolding for standard PRDs | Required step for standard; skipping leads to poor dim 4 grades downstream |
| Walking lean PRD through all 17 sections | Lean is intentionally 7 sections (its own numbering); use the lean scaffold from templates.md, not the standard one |
| Forgetting custom-template required-section merging | Custom templates MUST have all required sections; Shield appends missing ones with markers |
| Auto-detecting type without confirming with user | Type detection is best-effort; ALWAYS confirm with user |
| Writing to a path other than {output_dir}/{feature}/prd/{N}-{slug}/ | This is the only valid output path |

## See Also

- `templates.md` — 17-section scaffold + lean variant + HTML render templates
- `meta-schema.md` — prd.meta.json schema
- `type-detection.md` — lean vs standard heuristics
- `shield:story-coverage` skill — invoked between Sections 4 and 6 for scaffolding
