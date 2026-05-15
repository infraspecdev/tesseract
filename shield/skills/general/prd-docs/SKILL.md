---
name: prd-docs
description: Use when authoring a new PRD or upgrading a lean PRD to standard. Walks user through 20-section problem-first scaffold (or 10-section lean), pre-populates from prior /research transcript if present, defers Terminologies (§2) until after the rest is drafted (auto-fills from research glossary + scan of body), invokes shield:story-coverage between Sections 6 and 8 and shield:milestone-coverage between Sections 8 and 15, prompts for story Type (new/enhancement/existing), supports custom team templates via .shield.json. Triggers on /prd, write a PRD, author a PRD.
---

# PRD Docs

Author a new PRD with the Shield 20-section problem-first scaffold (or 10-section lean variant), or upgrade an existing lean PRD to standard by adding missing sections.

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
| 2 | Resolve feature folder context | always | Yes |
| 3 | Check for prior PRD in feature folder (lean → trigger upgrade flow) | only if prior PRD exists | conditional |
| 4 | Ask user for PRD type (standard | lean) | always | Yes |
| 5 | Check for prior `/research` transcript; pre-populate Problem/Personas/Dependencies if present | only if research exists | conditional |
| 6 | Walk Section 1 (Header) | always | Yes |
| 6a | Insert empty Terminologies placeholder for §2; fill later (step 13) | always | Yes |
| 7 | Walk Sections 3, 4 (Problem, Personas) | always | Yes |
| 7a | Walk Section 5 (Architecture & flows) — optional; user adds Mermaid blocks / image links, or leaves empty | always | Yes |
| 8 | Walk Section 6 (Goals) | always | Yes |
| 9 | Invoke `shield:story-coverage` between Sections 6 and 8 — scaffold expected stories | standard only | conditional |
| 10 | Walk Section 7 (Metrics) and Section 8 (Stories with Type prompt) | always (lean: only §7) | Yes |
| 11 | Invoke `shield:milestone-coverage` between Sections 8 and 15 (standard) or after Section 7 (lean) | always | Yes |
| 12 | Walk Section 15 rollout-mechanics; Sections 16..20 (standard) or §9, §10 (lean) | standard only for §15-§20 | conditional |
| 13 | Build Terminologies (§2) — research-glossary copy + LLM scan of drafted body, user confirms | always | Yes |
| 14 | Apply custom-template merging if `.shield.json.prd_template` is set | only if config set | conditional |
| 15 | Write `prd.md`, `prd.html`, `prd.meta.json` | always | Yes |
| 16 | Update manifest, regenerate index.html | always | Yes |

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
       [x] Section 8 — User stories & scenarios
       [x] Section 9 — Functional requirements
       [x] Section 10 — Non-functional requirements
       [x] Section 11 — RBAC & permissions matrix
       [x] Section 12 — Dependencies
       [x] Section 13 — Risks & mitigations
       [x] Section 14 — Assumptions
       [x] Section 15 — Rollout plan (mechanics; milestones already in lean §8)
       [x] Section 16 — Cost & resource impact
       [x] Section 17 — GTM & customer-comms
       [x] Section 18 — Support / CX impact

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
1. Standard — full 20-section scaffold (recommended for substantial features)
2. Lean — 10-section variant (good for 1-pagers, small features, "stop me if this is wrong" docs)
```

Record user choice. Type is per-invocation; not stored in `.shield.json`.

### 5. Pre-populate from prior research

Look for `{output_dir}/{feature}/research/*/transcript.md` (Phase C, falls back to `findings.md` if Phase C not yet shipped). If found:
- Read it
- Extract Problem context, Target Users (personas), Constraints (Existing systems / compliance markers)
- Pre-populate the corresponding sections in the PRD draft
- Tell user: "I pre-populated Sections 3 (Problem), 4 (Personas), 12 (Dependencies) from your research transcript. Confirm or edit before we continue."

### 6. Walk Section 1 and defer Section 2

Walk Section 1 (Header) — present the template fields and ask the user for content. Then insert an empty Terminologies table as a placeholder for Section 2; do NOT walk it now. It is filled in step 13 once the rest of the PRD has content to scan.

### 7. Walk Sections 3, 4, then 5, then 6

Walk Section 3 (Problem) and Section 4 (Personas) — skip pre-populated fields unless the user wants to edit.

Then walk Section 5 (Architecture & flows). Prompt the user:

```
Optional: Add a system overview or key flow diagrams? You can write Mermaid
code blocks (preferred — they render in prd.html) or link images stored
alongside prd.md. Leave empty if this feature has no notable architecture
or flows worth diagramming.
```

If the user adds Mermaid, sanity-check the syntax by trying a quick parse (the renderer will surface errors; don't block on syntax). If the user leaves it empty, leave the section content as a brief comment so the heading still appears.

Then walk Section 6 (Goals).

### 8. Story coverage scaffolding (standard only)

Once Sections 4 (Personas) and 6 (Goals) are captured, invoke `shield:story-coverage` skill with:
- `personas`: from Section 4
- `goals`: from Section 6
- `feature_domain`: inferred (see story-coverage SKILL.md "Domain detection")

The skill returns `expected_stories[]`. Present them to the user with multi-select:

```
For coverage of your personas and goals, you'll likely want these stories:

  [x] P1-S1 — Anika resets her password (persona-goal: P1 + G1, severity P0)
  [x] P1-S2 — Anika handles login lockout (archetype: account-recovery, severity P1)
  [x] P2-S1 — Rohan changes his email (archetype: email-change, severity P2)

Pick which to scaffold (defaults to all suggested), or add your own.
```

Selected stories are seeded into Section 8 with the standard story template structure (blank for the user to fill). Each scaffolded story is created with `Type: new` as the default placeholder — the user will override during the walk in step 10.

### 9. Story Type prompt protocol

For each story (scaffolded by step 8 or added by the user), walk the template fields. For the Type field, prompt:

```
Story <ID>: <name> — what's the Type?
  1. new — behavior does not exist today (default)
  2. enhancement — modifies existing user-visible behavior
  3. existing — already exists; documenting for context (regression surface)
```

If the user picks `enhancement` or `existing`, also prompt:

```
Briefly name the existing behavior (path, link, or one-line description):
```

Substitute both fields into the story template before walking the remaining fields.

This protocol is applied during `### 10`'s §8 walk, not at this heading.

### 10. Walk Sections 7 and 8

Walk Section 7 (Success metrics), then Section 8 (User stories — scaffolded by step 8; apply the Type prompt protocol from step 9 to each story as you walk it).

### 11. Milestone scaffolding (both scaffolds)

After Section 8 (standard, once stories are filled) or after Section 7 (lean, once metrics are filled), invoke `shield:milestone-coverage` with:

- `personas`: from Section 4
- `goals`: from Section 6
- `stories`: from Section 8 (standard only — pass empty for lean)
- `feature_domain`: same inference as story-coverage
- `success_metrics`: from Section 7 (optional)

The skill returns `milestones[]` plus `open_conflicts[]`. Present them to the user:

```
Milestone proposal — refine before approving:

  [x] M1 — Login core (PM + agile-coach agreed)
       Outcome: Users can log in with email + password
       Exit: Login endpoint returns 200 + session token...
       Depends on: —

  [x] M2 — Password recovery (PM + agile-coach disagreed on depends_on — see below)
       Outcome: Users can reset a forgotten password without contacting support
       Exit: Recovery email delivered within 60s; reset link single-use, 15-min TTL
       Depends on: M1
       ⚠ Conflict: PM proposed `depends_on: []`. Agile-coach proposed `depends_on: [M1]`.
         Agile-coach reason: "Recovery needs the session middleware shipped in M1."
         Decision needed: keep [M1] / clear / edit.

Pick which to keep (defaults to all suggested), edit fields per row, or add your own.
```

Selected and edited milestones are written into:
- **Standard:** §15 Milestones table (then walk §15 rollout-mechanics fields next as in the standard flow).
- **Lean:** §8 Milestones table (then proceed to §9 Open questions).

If the user declines (empty selection), leave the Milestones table empty. `/plan` will re-run `shield:milestone-coverage` as a fallback if needed.

### 12. Walk Sections 9-20

Walk Sections 9-14 in order. Section 15's Milestones table is pre-populated by step 11 — walk only the Rollout-mechanics fields beneath it. Then walk Sections 16-20.

For lean PRDs, walk lean §9 (Open questions), then §10 (Out of scope). Do NOT walk standard §8-§18; lean omits them intentionally. Use the lean scaffold from `templates.md`, not the standard one.

### 13. Build Terminologies (§2)

Now that Sections 3-20 have content (or 3-10 for lean), populate the Terminologies placeholder inserted in step 6a.

**Source A — research transcript glossary.** If a `/research` transcript exists at `{output_dir}/{feature}/research/*/transcript.md` (or `findings.md`), scan it for any `## Glossary`, `## Terminology`, or `## Terms` section. Parse rows (table or bullet list) and seed those terms into the Terminologies table.

**Source B — LLM scan of drafted PRD body.** Scan Sections 3..20 (or 3..10 for lean) and propose 5–15 additional terms that meet at least one of:
- ALL-CAPS acronyms used 2+ times (e.g., "SLA", "RBAC")
- Capitalized multi-word phrases used as named concepts (e.g., "Sign-off Contact", "Kill-switch")
- Domain nouns in Personas, NFRs, or Dependencies without prior definition
- Internal product / service names referenced in Dependencies / GTM / Rollout

For each term, propose a one-line definition that prefers terminology from the PRD's own prose. Reference the research-transcript source path when applicable.

**Merge.** Deduplicate by lowercased term. Source A rows win on conflict.

**User confirmation.** Present the merged table. Offer: accept all, edit, add, remove rows. Default: accept all.

Substitute the final table into Section 2.

### 14. Custom-template merging

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

### 15. Write artifacts

- Write `{output_dir}/{feature}/prd/{N}-{slug}/prd.md`
- **Pre-flight: ensure `uv` is available.** Run `command -v uv` first. If missing, do NOT call the renderer yet — first prompt the user:
  ```
  prd.html rendering requires uv (one-time install, ~/.local/bin).
  Install now? (y/n)
    [y] Run: curl -LsSf https://astral.sh/uv/install.sh | sh
    [n] Skip — prd.md is written, prd.html will be missing until you re-run /prd after installing uv
  ```
  If user agrees, run the installer via Bash, then `export PATH="$HOME/.local/bin:$PATH"` in the same shell so the next step finds it. If user declines, write `prd.md` and `prd.meta.json` but skip `prd.html` and surface the warning in the step-16 summary.
- Render `prd.html` via the helper (see `templates.md` → HTML render template):
  1. Write `prd.shell.html` next to `prd.md` containing the full HTML scaffold from `templates.md` with a literal `{{BODY}}` placeholder where the markdown body should appear. Fill in the title and meta-banner directly (owner, status, sidecar/research links) — those are not placeholders.
  2. Run `"$CLAUDE_PLUGIN_ROOT/scripts/render-markdown.sh" --md prd.md --shell prd.shell.html --out prd.html`.
  3. Delete `prd.shell.html` once the helper succeeds.
  Do NOT hand-render `prd.html` or pipe through pandoc/`python-markdown` — those mis-handle nested lists, lists-after-paragraphs, and loose/tight wrapping.
- Write `{output_dir}/{feature}/prd/{N}-{slug}/prd.meta.json` (per `meta-schema.md`)

### 16. Update dashboard

- Append new entry to `{output_dir}/manifest.json`
- Regenerate `{output_dir}/index.html`

### 17. Offer next steps

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
| Walking lean PRD through all 20 sections | Lean is intentionally 10 sections (its own numbering); use the lean scaffold from templates.md, not the standard one |
| Forgetting custom-template required-section merging | Custom templates MUST have all required sections; Shield appends missing ones with markers |
| Walking §2 (Terminologies) in order during the first pass | §2 is intentionally deferred; placeholder inserted in step 6a, content filled in step 13 after the rest of the PRD is drafted |
| Forcing diagrams in §5 (Architecture & flows) for every PRD | §5 is optional. If the feature has no notable architecture/flows, leave the section empty — don't manufacture diagrams |
| Forgetting the Type field on stories | Every story in §8 MUST have Type (new/enhancement/existing). For rewrites, "existing" stories make regression surface visible |
| Auto-detecting type without confirming with user | Type detection is best-effort; ALWAYS confirm with user |
| Writing to a path other than {output_dir}/{feature}/prd/{N}-{slug}/ | This is the only valid output path |

## See Also

- `templates.md` — 20-section scaffold + 10-section lean variant + HTML render templates
- `meta-schema.md` — prd.meta.json schema
- `type-detection.md` — lean vs standard heuristics
- `shield:story-coverage` skill — invoked between Sections 6 and 8 for scaffolding
- `shield:milestone-coverage` skill — invoked between Sections 8 and 15 (standard) or after Section 7 (lean) for milestone scaffolding
