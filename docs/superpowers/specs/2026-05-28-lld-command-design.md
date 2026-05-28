# Design — `/lld` command and TRD-driven LLD authoring

**Feature:** `lld-command-20260528` · **Status:** brainstorming-complete, ready for `/plan` · **Owner:** ashwini.manoj@aspora.com · **Date:** 2026-05-28

**Related:**
- Reference TRD this LLD work was deferred from: [`docs/shield/plan-trd-refactor-20260524/`](../plan-trd-refactor-20260524/)
- Reference LLD sample (template anchor): [tesseract PR #43](https://github.com/infraspecdev/tesseract/pull/43) — `docs/superpowers/specs/2026-05-18-lld-sample.html`
- Research that defines the LLD shape and rationale: [`../plan-trd-refactor-20260524/research.md`](../plan-trd-refactor-20260524/research.md)

---

## 1. Summary

Shield's `/plan` emits a 14-section TRD (HLD layer) and a `plan.json` sidecar whose stories carry `design_refs[]`. Today, those `design_refs[]` can already reference `doc: "lld"` — but the LLDs themselves don't exist; the entries are TODO placeholders awaiting a `/lld` command. This design lands that command and wires the TRD-driven authoring + promotion lifecycle around it.

LLDs are **per-component** (C4 Container/Component level), and `/lld` supports **two distinct domains** with **two distinct templates**:

- **Backend** — pinned verbatim to the PR #43 sample (14 sections, 12 always-on + 2 promote-on-demand, with 8 forced subsections under §12 Performance & scaling).
- **Infra** — a 14-section template adapted to declarative IaC, with 6 forced subsections under §12 Validation.

LLDs are reached via two pathways:

- **Path A (human-invoked)** — `/lld <component>` writes/edits `docs/lld/<component>.md` directly. Used for reverse-documenting existing-but-undocumented components. No feature folder, no plan.json side-effects.
- **Path B (TRD-driven)** — `/plan` authors a feature-folder draft (`docs/shield/<feature>/lld-<component>.md`) for every entry in `plan.json lld_components[]`. `/implement` only promotes drafts to `docs/lld/<component>.md` at milestone close, with concurrency check, §14 Changelog append, and `design_refs[]` anchor back-fill.

The bidirectional graph between stories (`design_refs[]`) and LLDs (§14 Changelog) is preserved: each story knows which LLD sections it depends on, each LLD knows which stories touched it.

## 2. Goals & non-goals

**Goals (v1):**
- Land a `/lld` command that supports both Path A (reverse-doc existing component) and Path B (TRD-driven authoring at `/plan` time) via a single underlying skill.
- Two templates (backend + infra) with stable kebab-case anchors, `n/a — <reason>` escape, forced subsections under §12, header metadata, §14 Changelog convention.
- Bump `plan.json` schema 1.4 → 1.5 with `lld_components[]` registry and derived `milestones[].touches_lld[]` (persisted, drift-gated).
- `/plan` populates the registry; `/implement` promotes drafts at milestone close; `/plan-review` enforces drift gate and finds undocumented LLDs.
- Auto back-fill `design_refs[]` anchor URLs on promotion (heuristic, with summary table flagging heuristic vs exact-match).
- Liberal error handling: auto-heal where deterministic recovery is possible; warn-and-continue where correctness allows; hard-fail only on schema/atomic-write/ambiguous-marker integrity issues.
- Mandatory eval coverage per CLAUDE.md, with CI wiring and a RED → GREEN paper trail.
- Plugin version bump + CHANGELOG entry in the same PR.

**Non-goals (deferred):**
- Auto-creation of design-doc pages in external systems (Confluence, Notion) — v2 enhancement, same as the TRD refactor's deferral.
- Renaming the existing `docs/superpowers/specs/` LLD sample location.
- Backfilling LLDs for already-shipped Shield internal components — Path A makes this possible but it's not part of v1 scope.
- Cross-LLD link integrity (e.g., when `lld-a` references `lld-b#section`, detecting that `lld-b` no longer has that section) — v2.
- LLD-to-LLD diff/review tooling beyond `/plan-review`'s existing rubric.

## 3. Stakeholders & success criteria

**Primary user:** the Shield-using engineer who runs `/plan` on a backend or infra feature and wants the LLD layer to exist alongside the TRD.

**Success criteria:**
- A `/plan` run on a feature that touches three components produces three feature-folder LLD drafts of the appropriate template type, structurally complete, ready for human review.
- A `/implement` run that closes the last story of a milestone promotes all touched LLDs to `docs/lld/<component>.md` with §14 Changelog rows tying back to the stories.
- A human running `/lld user-service` on a codebase with `user-service` undocumented produces `docs/lld/user-service.md` of the correct template type, populated from repo evidence.
- `/plan-review` catches: missing always-on sections, vague TBDs in always-on sections, `lld_components[]` registry inconsistency, `touches_lld[]` drift, undocumented LLD (canonical exists but `anchor_url` null in `design_refs[]`).
- Eval coverage runs in CI on every PR touching LLD code.

## 4. Architecture & component map

**Single skill, two entry points.**

| Artifact | Purpose |
|---|---|
| `shield/skills/general/lld-docs/SKILL.md` | Single source of truth for LLD behaviour. Template selection by `type`, drafting prompt (backend vs infra), header + changelog convention, `{#section-id}` anchor emission, atomic write, provenance stamp, plan.json back-fill, promotion. Invoked by both `/lld` (Path A) and `/plan` (Path B). |
| `shield/skills/general/lld-docs/lld-template-backend.md` | Backend slug allow-list + per-section authoring guidance, pinned to PR #43 sample. |
| `shield/skills/general/lld-docs/lld-template-infra.md` | Infra slug allow-list + per-section authoring guidance, per Section 7 of this doc. |
| `shield/commands/lld.md` | Path A entry. `/lld <component> [--type backend\|infra]`. Bare `/lld` lists undocumented candidates. Path A always writes to `docs/lld/`; Path B (TRD-driven) always drafts to feature folder. |
| `shield/commands/plan.md` + `shield/skills/general/plan-docs/SKILL.md` | Path B trigger. After emitting plan.json with `lld_components[]`, `/plan` invokes lld-docs skill once per registry entry to draft into feature folder. |
| `shield/commands/implement.md` + `shield/skills/general/implement-feature/SKILL.md` | New step 5h (milestone close): concurrency check + §14 Changelog append + promote draft → canonical + back-fill `design_refs[]` anchors. No LLD authoring at `/implement` time except as fallback per §8 row 4. |
| `shield/schema/plan-sidecar.schema.json` | Bump 1.4 → 1.5: add `lld_components[]` and `milestones[].touches_lld[]`. Tighten `design_refs[]` so `component` is required when `doc=="lld"`. |
| `shield/skills/general/plan-docs/sidecar-schema.md` | Doc the schema 1.5 additions and back-compat policy. |
| `shield/skills/general/plan-review/SKILL.md` | Three new rules: (a) `touches_lld[]` drift gate; (b) `lld_components[]` integrity; (c) undocumented-LLD finding. Plus LLD draft review (same rubric pattern as TRD review). |
| `shield/scripts/validate_plan.py` | Already invoked as the `/plan-review` first-check gate; extends with 1.5 schema. |
| `shield/evals/lld-docs/` | New eval directory: positive + negative fixtures per Section 8. |
| `.github/workflows/eval-lld.yml` | CI wiring; runs on PRs touching the new code paths. |
| `.claude-plugin/marketplace.json` + `shield/adapters/clickup/pyproject.toml` | Version bump per CLAUDE.md mandate. |
| `CHANGELOG.md` (under shield/) | User-facing changelog entry. |

**Touch graph at runtime:**

```
/plan ──► writes TRD §10 + plan.json with lld_components[] + milestones[].touches_lld[]
   │
   ├─► invokes lld-docs skill once per lld_components[] entry
   │     │
   │     ▼
   │   docs/shield/<feature>/lld-<component>.md  (draft)
   │   plan.json lld_components[].fork_blob_sha = git hash-object docs/lld/<c>.md
   │                                              (null if no canonical exists)
   │
   ▼
human reviews drafts; iterates via /plan-review

[stories execute via /implement; NO lld authoring here]

/implement closes last story of milestone M:
   │
   ▼
For each lld_components[] entry whose component appears in milestones[M].touches_lld[]:
   ├─ concurrency check (fork_blob_sha vs HEAD blob)
   ├─ append §14 Changelog row (M, date, story_ids touching component)
   ├─ atomic rename feature-folder draft → docs/lld/<component>.md
   └─ back-fill design_refs[].anchor_url for matching stories
```

**Path A standalone:**

```
/lld [<component>] [--type ...]
   │
   ▼
docs/lld/<component>.md  (direct write/edit; no plan.json side-effects)
```

## 5. Schema delta (1.4 → 1.5)

**New top-level field — `lld_components[]`:**

```json
"lld_components": [
  {
    "name": "user-service",
    "type": "backend",
    "fork_blob_sha": "abc123…"
  },
  {
    "name": "vpc-module",
    "type": "infra",
    "fork_blob_sha": null
  }
]
```

- `name` (required): kebab-case component identifier; matches the filename `docs/lld/<name>.md`.
- `type` (required): enum `"backend" | "infra"`.
- `fork_blob_sha` (optional, default `null`): git blob SHA of `docs/lld/<name>.md` at the time `/plan` drafted the feature-folder copy. Used by `/implement` at promotion for the concurrency check. `null` means the canonical didn't exist at draft time (net-new component).

**New per-milestone field — `milestones[].touches_lld[]`:**

```json
"milestones": [
  {
    "id": "M1",
    "name": "...",
    "outcome": "...",
    "exit_criteria": [...],
    "depends_on": [],
    "touches_lld": ["user-service", "vpc-module"]
  }
]
```

- `touches_lld[]` (optional, default `[]`): persisted `string[]` of `lld_components[].name` values. Deterministically derived as the rollup of `unique(design_refs[].component for stories in this milestone where doc=="lld")`. `/plan-review` enforces the drift gate.

**Tightened — `design_refs[].component`:**

When `doc == "lld"`, `component` is **required** (was nullable in 1.4). Older sidecars with `component: null` and `doc: "lld"` are flagged by `/plan-review` as schema-drift findings until updated.

**Back-compat:** sidecars at version 1.0/1.1/1.2/1.3/1.4 remain valid; missing 1.5 fields default to empty. Existing `design_refs[]` TODO placeholders with `component: null` need updating before they can participate in back-fill, but they don't break read-only consumers.

## 6. Data flow

### 6.1 Path A — human, no feature folder

```
1. /lld [<component>] [--type backend|infra]

2. Resolve component:
   - arg given      → use it (must be kebab-case)
   - bare /lld      → scan repo for component-shaped dirs:
                       · pyproject.toml packages
                       · top-level *.tf module dirs
                       · Chart.yaml directories
                       · go.mod modules
                      subtract docs/lld/*.md filenames;
                      present list, user picks

3. Resolve type:
   - --type flag        → use it
   - else infer from repo markers near component path
   - else (ambiguous)   → ask user

4. If an active feature folder's lld_components[] contains this component,
   warn (per §8 row 6) and continue. Path A always writes to docs/lld/,
   never to a feature folder.

5. Select template (lld-template-backend.md | lld-template-infra.md)

6. Write target = docs/lld/<component>.md
   - exists?   → edit-in-place; append §14 Changelog row:
                 "| manual | <YYYY-MM-DD> | reverse-doc by <git user> | |"
   - absent?   → atomic .tmp write → rename; provenance stamp emitted

7. Done. Print summary: path written, type, template, sections populated/skipped.
```

### 6.2 Path B — TRD-driven, drafted at `/plan` time

```
/plan runs (existing flow: emits trd.md + plan.json with design_refs[])

NEW step in /plan flow, after plan.json is finalised:

For each {name, type, …} in plan.json.lld_components[]:

  draft_path = docs/shield/<feature>/lld-<name>.md

  if docs/lld/<name>.md exists (enhancement):
    ├─ copy canonical → draft_path
    ├─ fork_blob_sha = git hash-object docs/lld/<name>.md
    ├─ write fork_blob_sha into plan.json lld_components[name]
    └─ invoke lld-docs skill in "merge" mode:
       reads TRD §7/§11, PRD §X, research.md, stories with design_refs[]→name;
       identifies which sections the new milestone affects;
       appends/edits those sections in draft;
       does NOT touch the canonical

  else (net-new):
    ├─ fork_blob_sha = null
    ├─ atomic-write template (per `type`) → draft_path
    └─ invoke lld-docs skill in "draft" mode:
       reads TRD/PRD/research/stories;
       fills all always-on sections (or marks `n/a — <reason>`);
       lifts promote-on-demand sections only if the data warrants

After all drafts written: /plan prints a summary table of drafts emitted.

────────────────────────────────────────────────────────────
[stories execute via /implement, normal flow; NO lld authoring]
────────────────────────────────────────────────────────────

/implement closes a story:
  - update plan.json last_aligned_with = HEAD-sha           (existing step 5f)
  - check: is this the last story of milestone M?

  if yes (milestone close):
    For each {name} in plan.json.milestones[M].touches_lld[]:
      ├─ lookup {type, fork_blob_sha} from lld_components[]
      ├─ draft = docs/shield/<feature>/lld-<name>.md
      │
      ├─ if draft missing:                                   (per §8 row 4)
      │     just-in-time invoke lld-docs skill;
      │     print loud "DRAFT AUTO-GENERATED AT PROMOTION" warning
      │
      ├─ if docs/lld/<name>.md exists AND fork_blob_sha is not null:
      │     current = git hash-object docs/lld/<name>.md
      │     if current != fork_blob_sha:                     (fork drift)
      │       re-invoke lld-docs skill in "remerge" mode to merge
      │       canonical changes into draft; refresh fork_blob_sha;
      │       on conflict-marker output → abort, surface to human
      │
      ├─ append §14 Changelog row to draft:
      │     "| <M> | <YYYY-MM-DD> | <milestone.name> | <story_ids> |"
      │
      ├─ atomic rename draft → docs/lld/<name>.md
      │
      └─ back-fill plan.json:
          for each story.design_refs[] where
            doc=="lld" AND component==name AND anchor_url is null:
              candidates = template slug list (backend or infra)
              winner = highest token-overlap(story.name, candidates);
                      tie-break by slug order; default #overview
              anchor_url = "lld-<name>.md#<winner>"
              label updated
          print summary table:
            [exact-match] story X.Y → #api-create-user
            [heuristic]   story A.B → #data-model
```

## 7. Template structure

### 7.1 Shared header metadata (both templates, above §1)

```
Feature: <feature-folder slug>
Owner: <git user.email>
Status: draft | review | promoted
Linked PRD: <relative path>
Linked plans: [<relative path>, …]    ← list, because one LLD ↔ many plans
Version: <semver>
Last updated: <YYYY-MM-DD>
```

### 7.2 Backend template (`lld-template-backend.md`)

Pinned verbatim to PR #43 sample. 14 sections, 12 always-on + 2 promote-on-demand.

| # | Section | Mode |
|---|---|---|
| 1 | Overview | always |
| 2 | Scope & non-goals | always |
| 3 | Module layout | always (file tree with `new`/`mod`/`unchanged` badges) |
| 4 | Data model | always (tables + cache namespaces with column-level detail) |
| 5 | API contracts | always (per-endpoint sub-anchor `{#api-<name>}`) |
| 6 | Sequence flows | always (per-flow sub-anchor `{#flow-<name>}`; Mermaid diagrams) |
| 7 | Error handling | always (error codes + behavior matrix) |
| 8 | Concurrency & state | always (named race conditions + resolutions) |
| 9 | Configuration | promote-on-demand |
| 10 | Observability | always (logs, metrics, traces) |
| 11 | Security & privacy | promote-on-demand |
| 12 | Performance & scaling | **always; 8 forced subsections**: 12.1 Load · 12.2 SLO · 12.3 Bottleneck · 12.4 Latency breakdown · 12.5 Capacity · 12.6 Scale-out lever · 12.7 Caches · 12.8 Degradation. `n/a — <reason>` is the only escape; vague prose fails the eval. |
| 13 | Open questions | always (Q#, question, options, owner, resolve-by table) |
| 14 | Changelog | always (every edit ties to a story ID + sections touched) |

### 7.3 Infra template (`lld-template-infra.md`)

14 sections, 12 always-on + 2 promote-on-demand. Adapted to declarative IaC (terraform / k8s / helm).

| # | Section | Mode |
|---|---|---|
| 1 | Overview | always |
| 2 | Scope & non-goals | always |
| 3 | Module topology | always (file tree + resource dependency graph; `new`/`mod`/`unchanged` badges) |
| 4 | Variable interface | always (per-variable sub-anchor `{#var-<name>}`; inputs/outputs/types/defaults/validation) |
| 5 | State model & lifecycle | always (lifecycle blocks, `ignore_changes`, `moved` blocks, `depends_on`) |
| 6 | Drift / idempotency / destructive-change surface | always (explicit "what triggers replacement vs in-place" table) |
| 7 | Security posture | promote-on-demand |
| 8 | Cost surface | always |
| 9 | Reliability & blast radius | always (multi-AZ, backup/restore, failure modes) |
| 10 | Observability & tagging | always |
| 11 | Migration & cutover | promote-on-demand (move blocks, state import, blue-green) |
| 12 | Validation | **always; 6 forced subsections**: 12.1 Plan invariants · 12.2 Policy checks (OPA/conftest/sentinel) · 12.3 Apply checks · 12.4 Drift detection · 12.5 Smoke test · 12.6 Rollback verify. `n/a — <reason>` is the only escape. |
| 13 | Open questions | always |
| 14 | Changelog | always |

### 7.4 Conventions inherited by both templates

- Stable kebab-case `{#section-id}` anchors on every section AND subsection (especially forced subsections under §12 and per-endpoint/per-variable sub-anchors).
- `n/a — <reason>` is the only allowed escape; vague TBDs fail the eval.
- §14 Changelog row format: `| <plan/milestone or "manual"> | <YYYY-MM-DD> | <human-readable summary> | <story_ids> |`.
- `<!-- generated by /lld v<plugin-version> on YYYY-MM-DD -->` provenance comment as the first line after frontmatter.
- Promote-on-demand sections render as `<details>` collapsible blocks with the standard slug present; collapsed by default until lifted.

## 8. Error handling & edge cases

Liberal philosophy: **auto-heal where there's a deterministic recovery path; warn-and-continue where correctness allows; hard-fail only on schema-integrity / atomic-write / ambiguous-marker cases.** Every auto-heal prints an audit-trail line so the recovery is never silent.

| # | Situation | Behaviour |
|---|---|---|
| 1 | Fork drift at promotion (`fork_blob_sha` ≠ canonical HEAD) | **Auto-heal:** re-invoke lld-docs skill to merge canonical changes into the draft (most are different-section edits); refresh `fork_blob_sha`; retry promotion. If merge produces conflict markers, surface to human with "re-run /plan to resolve." Always print "merged §X §Y from canonical" summary. |
| 2 | `design_refs[].component` not in `lld_components[]` | **Auto-heal:** infer `type` from repo markers at the component path (clear case) or from feature-folder draft if present; append to registry; log "registry auto-extended with `<c>: <type>`." On ambiguous markers (.tf + .py in same dir), warn and ask. |
| 3 | `type` missing on `lld_components[]` | **Auto-heal:** same inference as #2; `validate_plan.py` hard-rejects only if explicitly set to a non-enum value. |
| 4 | `touches_lld[]` entry has no draft in feature folder | **Auto-heal:** `/implement` just-in-time invokes lld-docs skill at milestone close to draft, then promotes. Prints loud "DRAFT AUTO-GENERATED AT PROMOTION — review `docs/lld/<c>.md` for content quality before the next /plan-review." Audit gap visibly flagged. |
| 5 | Orphan LLD draft in feature folder (no `design_refs[]` references it) | **Warn + continue:** `/plan-review` lists it as "draft `lld-<c>.md` doesn't appear in any story's `design_refs[]` — intentional?" Non-blocking. |
| 6 | Path A run while an active feature folder owns the same component | **Warn + continue:** "component `<c>` is being planned in `<feature>`; this canonical write will be merged on next /plan. Proceeding." Don't block. |
| 7 | Bare `/lld` finds zero component-shaped dirs | Friendly error with explicit-name usage hint. (No auto-heal — nothing to suggest.) |
| 8 | Atomic write fails mid-write | `.tmp` → rename pattern; one retry on transient failure; remove `.tmp` and surface error. **Hard fail** — correctness-critical. |
| 9 | Vague TBD in always-on section | **/plan-review finding (severity: review).** Not a failure. Human decides. |
| 10 | PoD section lifted but content vague | **/plan-review finding (severity: review).** Not a failure. |
| 11 | Re-running `/plan` with existing `lld_components[]` | Merge by name. Unchanged components keep `fork_blob_sha`. `type` is authoritative from registry unless `--refresh-types` passed. New components appended. Removed components flagged "registry shrunk — review intentional?" as a warning. |
| 12 | Schema validation failure (`validate_plan.py`) | **Hard fail.** Structural integrity gate; nothing to auto-heal. |

**Net effect:** the only paths that fail loudly are atomic-write failure (#8), schema invalid (#12), and ambiguous repo markers when inferring type (#2 fallback). Everything else either self-heals (with a visible audit trail) or surfaces as a non-blocking finding.

## 9. Testing strategy (eval coverage)

Per CLAUDE.md's mandatory-eval-coverage policy: every plugin-asset change ships with at least one executable eval.

**Positive fixtures** (`shield/evals/lld-docs/fixtures/`):
- `lld-positive-backend.md` — fully-populated backend LLD per PR #43 shape; passes.
- `lld-positive-infra.md` — fully-populated infra LLD per §7.3; passes.
- `plan-with-lld-components.json` — `lld_components[]` + `milestones[].touches_lld[]` populated consistently; passes `validate_plan.py` against the 1.5 schema.

**Negative fixtures** (each fails with named error):
- Per template: 4 representative missing-always-on-section fixtures (sampled across the 14; not all 14, to keep eval runtime reasonable) → 8 total.
- Per template: 2 representative missing-forced-subsection fixtures (§12.x backend; §12.x infra) → 4 total.
- 1 vague-TBD-in-always-on-section fixture.
- 1 PoD-lifted-but-vague fixture.
- 1 `design_refs[].component` not in `lld_components[]` fixture.
- 1 `touches_lld[]` persisted ≠ rollup fixture (drift gate).
- 1 invalid `type` enum fixture.
- 1 undocumented-LLD finding fixture (canonical exists; design_ref `anchor_url` null).
- 1 fork_blob_sha drift fixture (simulate canonical changed since fork).

Total: ~20 negatives.

**Eval file:** `shield/evals/lld-docs.yaml` (mirrors the shape of `shield/evals/plan-trd.yaml`).

**RED → GREEN paper trail** in the PR body:
- **RED**: baseline subagent without lld-docs skill misses §12 forced-subsection presence, type-aware template selection, fork_blob_sha concurrency check, back-fill heuristic.
- **GREEN**: subagent with skill loaded catches all of the above, generates a structurally-complete LLD for both backend and infra fixtures, correctly auto-heals fork drift and missing-registry cases.

**CI wiring:** `.github/workflows/eval-lld.yml` runs on PRs touching:
- `shield/skills/general/lld-docs/**`
- `shield/schema/plan-sidecar.schema.json`
- `shield/commands/lld.md`
- `shield/commands/implement.md` (for the step-5h promotion code)
- `shield/commands/plan.md` (for the lld_components[] population code)
- `shield/skills/general/plan-review/SKILL.md` (for the three new rules)
- `shield/evals/lld-docs/**`

**Plugin version bump:** `.claude-plugin/marketplace.json` Shield entry; `shield/adapters/clickup/pyproject.toml` (only if touched). CHANGELOG entry covering: new `/lld` command, schema 1.4 → 1.5, `/implement` step 5h, `/plan-review` rules added.

## 10. Open questions & risks

| # | Question / risk | Mitigation in v1 |
|---|---|---|
| 1 | Heuristic anchor-selection mismatches in back-fill | Print summary table flagging `[heuristic]` vs `[exact-match]` so the human can spot-correct. |
| 2 | Two feature branches independently fork the same LLD; last promotion wins | `fork_blob_sha` concurrency check at promotion (§8 row 1) + auto-heal merge attempt. Conflict-marker output surfaces to human. |
| 3 | LLM authoring quality at `/plan` time when source material (PRD/research) is thin | LLD draft is reviewable like the TRD; `/plan-review` enforces structural completeness; content quality remains a human judgment call. |
| 4 | Just-in-time draft at `/implement` (§8 row 4) bypasses human review before promotion | Loud audit-trail warning; the draft survives in `docs/lld/` for next-/plan-review pickup. Acceptable per "liberal error handling" stance. |
| 5 | Schema 1.5 lands and 1.4 consumers (older `/pm-sync` runs) ignore new fields | Standard forward-compat policy from sidecar-schema.md §forward-compat-policy: warn but don't reject unknown fields. Already established by `/plan-review`. |
| 6 | Path A can write to a canonical doc while Path B has an open draft for the same component in a feature folder | The two paths have non-overlapping outputs: Path A always writes to `docs/lld/`; Path B always drafts to feature folder. Conflict surfaces when `/plan` re-runs and detects a canonical changed since fork — handled by §8 row 1 auto-heal. Path A on a component owned by an active feature folder warns (§8 row 6) but proceeds, since the next `/plan` merge will reconcile. |

## 11. Out of scope (locked)

| Item | Status |
|---|---|
| Auto-creation of design-doc pages in Confluence / Notion adapters | v2 enhancement, same as TRD refactor's deferral. |
| Cross-LLD link integrity (lld-a → lld-b#section validation) | v2. |
| LLD-to-LLD diff/review tooling beyond `/plan-review`'s rubric | v2. |
| Per-LLD ownership routing in `/pm-sync` (assign on Linked plans changes) | v2. |
| Backfilling LLDs for existing Shield internal components | Possible via Path A; not v1 deliverable. |
| Renaming `docs/superpowers/specs/2026-05-18-lld-sample.html` | Out of scope; sample stays as the canonical template anchor reference. |

## 12. Glossary

- **LLD (Low-Level Design)** — Per-component design document covering Structure / State / Algorithm / Resource viewpoints (vs HLD's Context / Composition / Logical / Interface). Component-scoped; one LLD ↔ many plans.
- **Component** — A C4 Container or Component (a service, library, or module). Identified by kebab-case `name`.
- **Path A** — Human-invoked `/lld <component>`. Writes directly to `docs/lld/`.
- **Path B** — TRD-driven authoring at `/plan` time. Drafts in feature folder; promoted at milestone close by `/implement`.
- **Feature folder** — `docs/shield/<feature>/`. Where Path B drafts live until promotion.
- **Canonical** — `docs/lld/<component>.md`. The promoted, durable LLD.
- **Fork blob SHA** — Git blob SHA of the canonical at the moment `/plan` drafted the feature-folder copy. Used for concurrency check at promotion.
- **Promote-on-demand (PoD)** — A section whose standard slug exists but defaults to collapsed/empty until the component's nature warrants lifting it. Backend: §9 Config, §11 Security. Infra: §7 Security, §11 Migration.
- **Forced subsection** — A subsection under §12 that must exist with non-vague content (or `n/a — <reason>`). 8 in backend (§12.1–12.8 Performance & scaling), 6 in infra (§12.1–12.6 Validation).
- **Back-fill** — Updating `design_refs[].anchor_url` for `doc:"lld"` TODO entries after the corresponding LLD lands. Heuristic, with summary table flagging matches.

---

**Next step:** invoke Shield's `/plan` skill on this `lld-command-20260528/` feature folder to produce `trd.md` + `plan.json` for the implementation work.
