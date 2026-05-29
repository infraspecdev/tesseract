# /lld Command — M3 Review Wiring + Negative Coverage + Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the `/plan-review` rules that govern the LLD surface (touches_lld drift gate, lld_components integrity, undocumented-LLD finding, LLD-draft structural-review rubric); ship the full negative eval-fixture suite (~18 fixtures, each failing with a named error); wire the eval into CI on every relevant PR; bump the Shield plugin version and write the CHANGELOG entry that ships the M1 + M2 + M3 surface as one user-visible cutover.

**Architecture:** Four new rules layered onto the existing `shield/skills/general/plan-review/SKILL.md` rubric, each backed by a focused eval fixture pair (positive that already passed in M1/M2 + negative landed here). Each rule is a thin wrapper around `shield/scripts/validate_plan.py` outputs (Tasks 1–2) or a new check in plan-review skill prose (Tasks 3–4). The negative fixtures land in batches (always-on missing × 8, forced-subsection missing × 4, structural issues × 6) to make iterative add-and-verify tractable. CI workflow mirrors `shield/evals/plan-trd.yaml`'s sibling GitHub Actions YAML if one exists; otherwise, a fresh one. Version bump + CHANGELOG land last.

**Tech Stack:** Markdown skill docs, YAML (eval declarations + GitHub Actions), Python (extension to `run-lld-docs.py`'s negative-fixture handling), JSON (negative plan.json fixtures), Markdown (negative LLD fixtures).

**Spec:** [`docs/superpowers/specs/2026-05-28-lld-command-design.md`](../specs/2026-05-28-lld-command-design.md). Cross-reference §8 (rows 9, 10 — quality findings), §9 (testing strategy), §10 (risk 1 — heuristic mismatch surfacing).

**Depends on M1 + M2:** all of M1 (templates, lld-docs skill, /lld command, schema 1.5, validate_plan.py drift checks) AND all of M2 (Path B emission, step 5h, eval runner real-CLI wiring).

---

## File Structure

**Files to create (this plan):**

| Path | Responsibility |
|---|---|
| `shield/evals/lld-docs/fixtures/neg-missing-section-{1..8}/lld.md` | 8 negative fixtures, 4 per template, each missing one always-on section. |
| `shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-{1..4}/lld.md` | 4 negative fixtures, 2 per template, each missing one §12 forced subsection. |
| `shield/evals/lld-docs/fixtures/neg-vague-tbd/lld.md` | Vague TBD in an always-on section. |
| `shield/evals/lld-docs/fixtures/neg-pod-lifted-vague/lld.md` | Promote-on-demand lifted but content is vague. |
| `shield/evals/lld-docs/fixtures/neg-component-not-in-registry/plan.json` | `design_refs[].component` not in `lld_components[]`. |
| `shield/evals/lld-docs/fixtures/neg-touches-lld-drift/plan.json` | Persisted `touches_lld[]` ≠ rollup. |
| `shield/evals/lld-docs/fixtures/neg-invalid-type/plan.json` | `lld_components[].type` not in `{backend, infra}`. |
| `shield/evals/lld-docs/fixtures/neg-undocumented-lld/plan.json` + `neg-undocumented-lld/canonical-on-disk.md` | Canonical exists on disk but `design_refs[].anchor_url` is null. |
| `shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught/plan.json` + sidecars | Fork drift triggered without `/implement` having a chance to auto-heal — `/plan-review` surfaces it as a finding before /implement runs. |
| `.github/workflows/eval-lld.yml` | CI workflow that runs the eval on relevant PRs. |

**Files to modify (this plan):**

| Path | What changes |
|---|---|
| `shield/skills/general/plan-review/SKILL.md` | Four new rules: `touches_lld_drift`, `lld_components_integrity`, `undocumented_lld`, `lld_draft_review`. Each with severity, fixture references, suggested-fix output. |
| `shield/evals/lld-docs.yaml` | Add `fixtures.negative[]` entries with declared expected named-errors per fixture. |
| `shield/evals/run-lld-docs.py` | Extend to handle negative fixtures: confirm the expected named-error fires; FAIL the eval if a negative silently passes. |
| `shield/CHANGELOG.md` (create if absent) | User-facing changelog entry covering /lld command, schema 1.5, step 5h, plan-review rules — the full M1 + M2 + M3 surface. |
| `.claude-plugin/marketplace.json` | Bump the `shield` plugin version (e.g. 2.20.0 → 2.21.0 — minor bump for new commands + new user-visible schema field). |

**Decomposition rationale:**
- /plan-review rules first (Tasks 1–4): the rules cite negative fixtures in their docs, so the rule descriptions are coherent. Some rule wrappers around `validate_plan.py` outputs (already implemented in M1 Task 4); others need fresh plan-review-skill logic.
- Negative fixtures next (Tasks 5–14): each fixture's content is small but precise. Batched 2–4 per task to keep diffs reviewable.
- Eval-runner negative-handling (Task 15): once fixtures exist, the runner needs to verify each FAILs with the named error.
- CI workflow (Task 16): only after the eval suite is fully exercising both positives and negatives.
- Version bump + CHANGELOG (Task 17): the last task, gating the cutover PR.

Total: 17 tasks.

---

## Phase 1 — /plan-review rules

### Task 1: Add `touches_lld_drift` rule to plan-review/SKILL.md

**Files:**
- Modify: `shield/skills/general/plan-review/SKILL.md`

- [ ] **Step 1: Find the existing rule table**

Run: `grep -n '^|\s*[0-9]\+[a-z]\?\s*|' shield/skills/general/plan-review/SKILL.md | head -20`

Identify the existing rule-table block (the one introduced by the TRD refactor in M2 of the prior cutover, where rules like `0e` Implementation-manual live).

- [ ] **Step 2: Add the rule row**

In the rule table, after the existing `0e` row (or wherever rules are
numbered), add:

```markdown
| 0f | `touches_lld_drift` — persisted `milestones[i].touches_lld[]` ≠ rollup of `design_refs[].component` per milestone | when plan.json is schema 1.5+ | Yes — High |
```

- [ ] **Step 3: Add the rule documentation block**

After the rule table, in the per-rule documentation section, add:

````markdown
### `touches_lld_drift` rule

Wraps `shield/scripts/validate_plan.py`'s `_check_touches_lld_drift` output
(introduced in M1 plan, Task 4). For every milestone in the plan:

```python
persisted = set(milestone["touches_lld"])
rollup = {ref.component for story in milestone.stories
                       for ref in story.design_refs
                       if ref.doc == "lld"}
if persisted != rollup:
    flag as `touches_lld_drift`
```

**Why it matters:** The persisted field exists so PM-sync, reviewers, and
humans can read it without recomputing. Drift means the persisted value is
lying — the source-of-truth `design_refs[]` and the convenience `touches_lld[]`
have diverged.

**Severity:** High. The plan.json is internally inconsistent.

**Suggested fix output:**

```
For milestone <M>:
  persisted touches_lld: [list]
  rollup from design_refs[]: [list]
  To fix: update plan.json milestones[<M>].touches_lld = [rollup].
```

**Fixture reference:** `shield/evals/lld-docs/fixtures/neg-touches-lld-drift/plan.json`.
````

- [ ] **Step 4: Render and commit**

```bash
bash shield/scripts/render-markdown.sh shield/skills/general/plan-review/SKILL.md /tmp/plan-review.html
git add shield/skills/general/plan-review/SKILL.md
git commit -m "feat(shield/plan-review): touches_lld_drift rule (severity High)"
```

---

### Task 2: Add `lld_components_integrity` rule to plan-review/SKILL.md

**Files:**
- Modify: `shield/skills/general/plan-review/SKILL.md`

- [ ] **Step 1: Add the rule row**

After the `0f` row, add:

```markdown
| 0g | `lld_components_integrity` — every `design_refs[].component` (where doc==lld) must appear in `lld_components[]`; type must be in enum; no duplicate names | when plan.json is schema 1.5+ | Yes — High |
```

- [ ] **Step 2: Add the rule documentation block**

````markdown
### `lld_components_integrity` rule

Wraps `shield/scripts/validate_plan.py`'s `_check_lld_component_missing`
output, plus inline checks for `type` enum and duplicate names.

**Three sub-checks:**

1. **Missing registry entry.** For every `design_refs[].component` (where
   `doc == "lld"`), confirm it appears in `lld_components[].name`.
2. **Type enum.** Every `lld_components[].type` is in `{"backend", "infra"}`.
   Other values fail.
3. **Duplicate names.** `lld_components[].name` values are unique. Duplicates
   mean the registry contradicts itself.

**Why it matters:** The registry is the single source of truth for per-component
metadata (type, fork_blob_sha). When it disagrees with `design_refs[]`, the
M2 step 5h promotion can't reliably pick a template.

**Severity:** High.

**Suggested fix output (per sub-check):**

```
Missing registry entry for component 'user-service':
  Referenced by: EPIC-1-S1, EPIC-1-S2
  To fix: add to lld_components[]: { "name": "user-service", "type": "<inferred-or-asked>", "fork_blob_sha": null }
```

```
Invalid type for component 'foo': 'lambda'
  Valid values: backend, infra
  To fix: update lld_components[<index>].type.
```

```
Duplicate component name in lld_components[]: 'foo' (entries at indices 0 and 2)
  To fix: drop one entry (the duplicate); confirm fork_blob_sha matches across both before dropping.
```

**Fixture references:**
- `shield/evals/lld-docs/fixtures/neg-component-not-in-registry/plan.json`
- `shield/evals/lld-docs/fixtures/neg-invalid-type/plan.json`
````

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/plan-review/SKILL.md
git commit -m "feat(shield/plan-review): lld_components_integrity rule (severity High)"
```

---

### Task 3: Add `undocumented_lld` rule to plan-review/SKILL.md

**Files:**
- Modify: `shield/skills/general/plan-review/SKILL.md`

- [ ] **Step 1: Add the rule row**

```markdown
| 0h | `undocumented_lld` — `docs/lld/<c>.md` exists on disk but a story's `design_refs[].anchor_url` for that component is null | when canonical LLDs exist | Yes — Medium |
```

- [ ] **Step 2: Add the rule documentation block**

````markdown
### `undocumented_lld` rule

Detects the gap state where an LLD has landed at the canonical path but
the plan.json still has TODO placeholders for it.

**Check:**

```python
for epic in plan.epics:
    for story in epic.stories:
        for ref in story.design_refs:
            if ref.doc == "lld" and ref.anchor_url is None:
                canonical = Path(f"docs/lld/{ref.component}.md")
                if canonical.exists():
                    # Compute the would-be anchor via the same token-overlap
                    # heuristic /implement uses (shield/scripts/lld_anchor_heuristic.py).
                    slug, match_type = select_anchor(story.name, slugs_for(ref.component))
                    finding(story.id, ref.component, slug, match_type)
```

**Why it matters:** Before /implement's step 5h has run, design_refs[] entries
may legitimately carry `anchor_url: null` (the LLD doesn't exist yet). After
the LLD lands, those entries should be back-filled. If they're still null
post-promotion, either /implement skipped the back-fill (bug) or a human
edited plan.json afterward (drift). Either way, the LLD layer's value is
diminished — stories don't know which section they implement.

**Severity:** Medium. Doesn't block /implement runs but degrades traceability.

**Suggested fix output:**

```
Story EPIC-1-S1 has a TODO LLD ref for component 'user-service', but
docs/lld/user-service.md exists.

Suggested back-fill:
  anchor_url: lld-user-service.md#data-model
  label: §4 Data model
  match type: [heuristic]

To apply: update plan.json epics[].stories[].design_refs[].
```

**Fixture reference:** `shield/evals/lld-docs/fixtures/neg-undocumented-lld/`.
````

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/plan-review/SKILL.md
git commit -m "feat(shield/plan-review): undocumented_lld rule (severity Medium)"
```

---

### Task 4: Add `lld_draft_review` rule to plan-review/SKILL.md

**Files:**
- Modify: `shield/skills/general/plan-review/SKILL.md`

This is the structural-review rubric: same shape as the TRD review (which
already exists in plan-review/SKILL.md), but applied to feature-folder
LLD drafts.

- [ ] **Step 1: Add the rule row**

```markdown
| 0i | `lld_draft_review` — apply the LLD structural rubric (missing always-on, missing forced subsection, vague TBDs in always-on, PoD lifted but vague) to every `docs/shield/{feature}/lld-*.md` draft | when feature-folder LLD drafts exist | Yes — High (missing always-on), Medium (missing forced subsection), Review (vague TBD / PoD vague) |
```

- [ ] **Step 2: Add the rule documentation block**

````markdown
### `lld_draft_review` rule

Mirrors the TRD-review rubric pattern, applied to LLD drafts in the
feature folder.

**Procedure for each `docs/shield/{feature}/lld-*.md`:**

1. Parse the provenance comment to determine template type
   (look for `<!-- generated by /lld v… -->`; the filename `lld-<name>.md`
   gives the component; the matching `lld_components[]` entry gives the
   `type`).
2. Load the slug allow-list from `shield/schema/lld-sections-<type>.yaml`.
3. **Always-on presence check:** for every section where `promote_on_demand: false`,
   verify the heading + anchor are present in the draft. If absent → finding.
4. **Forced-subsection check:** for §12, verify every entry in
   `forced_subsections[]` has its sub-anchor present. If absent → finding.
5. **`n/a — <reason>` escape check:** any section may declare `n/a — <reason>`
   in place of populated content. Verify the prose after the section header
   either has at least one non-empty paragraph OR matches the pattern
   `n/a — <reason>` (where `<reason>` is non-empty). Vague placeholders
   (`TBD`, `TODO`, `to be determined`, `to do`, `[fill in]`) in always-on
   sections → finding.
6. **PoD lifted-but-vague check:** for promote-on-demand sections rendered as
   `<details open>` (lifted), verify content is non-vague. A lifted PoD
   section with only `TBD` or `n/a` is a finding.

**Severities:**
- Missing always-on section → **High**.
- Missing §12 forced subsection → **Medium**.
- Vague TBD in always-on → **Review** (informational; human decides).
- PoD lifted but vague → **Review**.

**Suggested fix output:**

```
Draft docs/shield/{feature}/lld-foo.md:
  - Missing always-on section: §3 module-layout (severity: High)
  - Missing forced subsection: §12.4 latency-breakdown (severity: Medium)
  - Vague TBD in §1 overview (severity: Review)

To fix:
  - Add the missing sections per shield/schema/lld-sections-backend.yaml.
  - Replace `TBD` with concrete content or `n/a — <reason>`.
```

**Fixture references:**
- `shield/evals/lld-docs/fixtures/neg-missing-section-1/lld.md` through `…-8`
- `shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-1/lld.md` through `…-4`
- `shield/evals/lld-docs/fixtures/neg-vague-tbd/lld.md`
- `shield/evals/lld-docs/fixtures/neg-pod-lifted-vague/lld.md`
````

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/plan-review/SKILL.md
git commit -m "feat(shield/plan-review): lld_draft_review rule — structural rubric for LLD drafts"
```

---

## Phase 2 — Negative fixtures: missing always-on sections

### Task 5: Author 4 backend missing-always-on fixtures

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-1/lld.md` (missing §3 Module layout)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-2/lld.md` (missing §4 Data model)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-3/lld.md` (missing §7 Error handling)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-4/lld.md` (missing §10 Observability)

These pick representative always-on sections — one per quadrant of the
template (structure / data / error / ops).

- [ ] **Step 1: Build the fixtures from the positive backend fixture**

```bash
for n in 1 2 3 4; do
  mkdir -p shield/evals/lld-docs/fixtures/neg-missing-section-${n}
done

# n=1: drop §3 Module layout
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-backend.md').read()
out = re.sub(r'## §3 Module layout \{#module-layout\}.*?(?=## §4 Data model)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-1/lld.md', 'w').write(out)
print('OK n=1')
"

# n=2: drop §4 Data model
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-backend.md').read()
out = re.sub(r'## §4 Data model \{#data-model\}.*?(?=## §5 API contracts)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-2/lld.md', 'w').write(out)
print('OK n=2')
"

# n=3: drop §7 Error handling
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-backend.md').read()
out = re.sub(r'## §7 Error handling \{#error-handling\}.*?(?=## §8 Concurrency)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-3/lld.md', 'w').write(out)
print('OK n=3')
"

# n=4: drop §10 Observability
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-backend.md').read()
out = re.sub(r'## §10 Observability \{#observability\}.*?(?=## §11 Security)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-4/lld.md', 'w').write(out)
print('OK n=4')
"
```

- [ ] **Step 2: Verify each fixture has the expected gap**

```bash
for n in 1 2 3 4; do
  case $n in
    1) anchor='module-layout' ;;
    2) anchor='data-model' ;;
    3) anchor='error-handling' ;;
    4) anchor='observability' ;;
  esac
  content=$(cat shield/evals/lld-docs/fixtures/neg-missing-section-${n}/lld.md)
  if grep -q "{#${anchor}}" <<< "$content"; then
    echo "FAIL: neg-missing-section-${n} still has #${anchor}"
  else
    echo "OK: neg-missing-section-${n} missing #${anchor}"
  fi
done
```

Expected: 4 lines, all `OK:`.

- [ ] **Step 3: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-missing-section-{1,2,3,4}/
git commit -m "test(shield/lld-docs): 4 backend missing-always-on fixtures (§3, §4, §7, §10)"
```

---

### Task 6: Author 4 infra missing-always-on fixtures

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-5/lld.md` (missing §3 Module topology)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-6/lld.md` (missing §5 State model)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-7/lld.md` (missing §8 Cost surface)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-section-8/lld.md` (missing §10 Observability & tagging)

- [ ] **Step 1: Build the fixtures from the positive infra fixture**

```bash
for n in 5 6 7 8; do
  mkdir -p shield/evals/lld-docs/fixtures/neg-missing-section-${n}
done

# n=5: drop §3 Module topology
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-infra.md').read()
out = re.sub(r'## §3 Module topology \{#module-topology\}.*?(?=## §4 Variable interface)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-5/lld.md', 'w').write(out)
print('OK n=5')
"

# n=6: drop §5 State model
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-infra.md').read()
out = re.sub(r'## §5 State model & lifecycle \{#state-model-and-lifecycle\}.*?(?=## §6 Drift)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-6/lld.md', 'w').write(out)
print('OK n=6')
"

# n=7: drop §8 Cost surface
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-infra.md').read()
out = re.sub(r'## §8 Cost surface \{#cost-surface\}.*?(?=## §9 Reliability)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-7/lld.md', 'w').write(out)
print('OK n=7')
"

# n=8: drop §10 Observability & tagging
python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-infra.md').read()
out = re.sub(r'## §10 Observability & tagging \{#observability-and-tagging\}.*?(?=## §11 Migration)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-section-8/lld.md', 'w').write(out)
print('OK n=8')
"
```

- [ ] **Step 2: Verify and commit**

```bash
for n in 5 6 7 8; do
  case $n in
    5) anchor='module-topology' ;;
    6) anchor='state-model-and-lifecycle' ;;
    7) anchor='cost-surface' ;;
    8) anchor='observability-and-tagging' ;;
  esac
  content=$(cat shield/evals/lld-docs/fixtures/neg-missing-section-${n}/lld.md)
  if grep -q "{#${anchor}}" <<< "$content"; then
    echo "FAIL: neg-missing-section-${n} still has #${anchor}"
  else
    echo "OK: neg-missing-section-${n} missing #${anchor}"
  fi
done

git add shield/evals/lld-docs/fixtures/neg-missing-section-{5,6,7,8}/
git commit -m "test(shield/lld-docs): 4 infra missing-always-on fixtures (§3, §5, §8, §10)"
```

Expected: 4 `OK:` lines + clean commit.

---

## Phase 3 — Negative fixtures: missing forced subsections

### Task 7: Author 2 backend missing-forced-subsection fixtures

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-1/lld.md` (missing §12.4 Latency breakdown)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-2/lld.md` (missing §12.8 Degradation)

- [ ] **Step 1: Build**

```bash
for n in 1 2; do
  mkdir -p shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-${n}
done

python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-backend.md').read()
# n=1: drop §12.4 Latency breakdown
out = re.sub(r'### §12\.4 Latency breakdown \{#latency-breakdown\}.*?(?=### §12\.5 Capacity)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-1/lld.md', 'w').write(out)

# n=2: drop §12.8 Degradation
out = re.sub(r'### §12\.8 Degradation \{#degradation\}.*?(?=## §13)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-2/lld.md', 'w').write(out)
print('OK')
"
```

- [ ] **Step 2: Verify**

```bash
grep -L 'latency-breakdown' shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-1/lld.md && echo "OK 1"
grep -L 'degradation' shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-2/lld.md && echo "OK 2"
```

Expected: both `OK` lines.

- [ ] **Step 3: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-{1,2}/
git commit -m "test(shield/lld-docs): 2 backend missing-forced-subsection fixtures (§12.4, §12.8)"
```

---

### Task 8: Author 2 infra missing-forced-subsection fixtures

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-3/lld.md` (missing §12.2 Policy checks)
- Create: `shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-4/lld.md` (missing §12.5 Smoke test)

- [ ] **Step 1: Build**

```bash
for n in 3 4; do
  mkdir -p shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-${n}
done

python3 -c "
import re
src = open('shield/evals/lld-docs/fixtures/lld-positive-infra.md').read()
out3 = re.sub(r'### §12\.2 Policy checks \{#policy-checks\}.*?(?=### §12\.3 Apply checks)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-3/lld.md', 'w').write(out3)

out4 = re.sub(r'### §12\.5 Smoke test \{#smoke-test\}.*?(?=### §12\.6 Rollback verify)', '', src, flags=re.DOTALL)
open('shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-4/lld.md', 'w').write(out4)
print('OK')
"

git add shield/evals/lld-docs/fixtures/neg-missing-forced-subsection-{3,4}/
git commit -m "test(shield/lld-docs): 2 infra missing-forced-subsection fixtures (§12.2, §12.5)"
```

---

## Phase 4 — Negative fixtures: structural issues

### Task 9: Author vague-TBD fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-vague-tbd/lld.md`

- [ ] **Step 1: Build**

```bash
mkdir -p shield/evals/lld-docs/fixtures/neg-vague-tbd
python3 -c "
src = open('shield/evals/lld-docs/fixtures/lld-positive-backend.md').read()
# Replace §1 Overview content with a literal 'TBD'
old = '## §1 Overview {#overview}\n\n\`user-service\` is the HTTP service that owns user registration, authentication\nsessions, and profile reads. It serves the \`/signup\`, \`/login\`, and \`/users/:id\`\nendpoints. Runtime: Python FastAPI; deployed as a single replica set behind\nthe API gateway.'
new = '## §1 Overview {#overview}\n\nTBD'
out = src.replace(old, new)
open('shield/evals/lld-docs/fixtures/neg-vague-tbd/lld.md', 'w').write(out)
print('OK')
"
```

- [ ] **Step 2: Verify the TBD is present in §1**

```bash
grep -A 2 'overview' shield/evals/lld-docs/fixtures/neg-vague-tbd/lld.md | head -5
```

Expected: `TBD` appears below the §1 heading.

- [ ] **Step 3: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-vague-tbd/
git commit -m "test(shield/lld-docs): vague-TBD fixture (TBD in §1 Overview)"
```

---

### Task 10: Author PoD-lifted-vague fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-pod-lifted-vague/lld.md`

- [ ] **Step 1: Build**

A PoD section (e.g. backend §9 Configuration) rendered as `<details open>` but with only `TBD` inside.

```bash
mkdir -p shield/evals/lld-docs/fixtures/neg-pod-lifted-vague
python3 -c "
src = open('shield/evals/lld-docs/fixtures/lld-positive-backend.md').read()
# Replace the §9 Configuration <details> block with a <details open> containing only TBD
import re
out = re.sub(
    r'<details>\n<summary>§9 Configuration</summary>.*?</details>',
    '<details open>\n<summary>§9 Configuration</summary>\n\nTBD\n\n</details>',
    src,
    flags=re.DOTALL,
)
open('shield/evals/lld-docs/fixtures/neg-pod-lifted-vague/lld.md', 'w').write(out)
print('OK')
"
```

- [ ] **Step 2: Verify**

```bash
grep -A 2 'details open' shield/evals/lld-docs/fixtures/neg-pod-lifted-vague/lld.md | head -5
```

Expected: `<details open>` present followed by minimal content (TBD).

- [ ] **Step 3: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-pod-lifted-vague/
git commit -m "test(shield/lld-docs): PoD-lifted-vague fixture (§9 opened with TBD)"
```

---

### Task 11: Author component-not-in-registry fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-component-not-in-registry/plan.json`

- [ ] **Step 1: Build**

```bash
mkdir -p shield/evals/lld-docs/fixtures/neg-component-not-in-registry
python3 -c "
import json
src = json.load(open('shield/tests/fixtures/plan-1.5-valid.json'))
src['name'] = 'neg-component-not-in-registry'
# Drop the vpc-module entry from lld_components but keep the design_refs[] reference
src['lld_components'] = [c for c in src['lld_components'] if c['name'] != 'vpc-module']
# Also drop touches_lld 'vpc-module' to NOT trigger drift in addition
src['milestones'][0]['touches_lld'] = ['user-service']
# But the EPIC-1-S2 design_refs still points to component 'vpc-module' → triggers integrity rule
json.dump(src, open('shield/evals/lld-docs/fixtures/neg-component-not-in-registry/plan.json', 'w'), indent=2)
print('OK')
"
```

- [ ] **Step 2: Verify**

Run: `uv run --with jsonschema python shield/scripts/validate_plan.py shield/evals/lld-docs/fixtures/neg-component-not-in-registry/plan.json 2>&1 | tail -3`

Expected: exit code 3 (or whatever the script uses for lld_component_missing); message mentions `vpc-module` and `lld_component_missing`.

- [ ] **Step 3: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-component-not-in-registry/
git commit -m "test(shield/lld-docs): neg-component-not-in-registry fixture"
```

---

### Task 12: Author touches_lld-drift and invalid-type fixtures

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-touches-lld-drift/plan.json`
- Create: `shield/evals/lld-docs/fixtures/neg-invalid-type/plan.json`

- [ ] **Step 1: Build the touches-lld-drift fixture**

(Already created in M1 Task 4 as a test fixture — copy it here.)

```bash
mkdir -p shield/evals/lld-docs/fixtures/neg-touches-lld-drift
cp shield/tests/fixtures/plan-1.5-touches-drift.json \
   shield/evals/lld-docs/fixtures/neg-touches-lld-drift/plan.json
```

- [ ] **Step 2: Build the invalid-type fixture**

```bash
mkdir -p shield/evals/lld-docs/fixtures/neg-invalid-type
python3 -c "
import json
src = json.load(open('shield/tests/fixtures/plan-1.5-valid.json'))
src['name'] = 'neg-invalid-type'
src['lld_components'][0]['type'] = 'lambda'  # not in enum
json.dump(src, open('shield/evals/lld-docs/fixtures/neg-invalid-type/plan.json', 'w'), indent=2)
print('OK')
"
```

- [ ] **Step 3: Verify both fail validate_plan.py**

```bash
for fix in touches-lld-drift invalid-type; do
  echo "--- $fix ---"
  uv run --with jsonschema python shield/scripts/validate_plan.py shield/evals/lld-docs/fixtures/neg-${fix}/plan.json 2>&1 | tail -2
done
```

Expected: each prints a named error (`touches_lld_drift` and a JSON Schema error on `type` respectively).

- [ ] **Step 4: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-touches-lld-drift/ shield/evals/lld-docs/fixtures/neg-invalid-type/
git commit -m "test(shield/lld-docs): neg-touches-lld-drift + neg-invalid-type fixtures"
```

---

### Task 13: Author undocumented-LLD fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-undocumented-lld/plan.json`
- Create: `shield/evals/lld-docs/fixtures/neg-undocumented-lld/canonical-on-disk.md`

- [ ] **Step 1: Build**

```bash
mkdir -p shield/evals/lld-docs/fixtures/neg-undocumented-lld

python3 -c "
import json
src = json.load(open('shield/tests/fixtures/plan-1.5-valid.json'))
src['name'] = 'neg-undocumented-lld'
# Set EPIC-1-S1's user-service design_ref back to TODO state
src['epics'][0]['stories'][0]['design_refs'][1] = {
    'doc': 'lld',
    'component': 'user-service',
    'section_id': None,
    'anchor_url': None,
    'label': 'TODO: link when /lld lands',
}
json.dump(src, open('shield/evals/lld-docs/fixtures/neg-undocumented-lld/plan.json', 'w'), indent=2)
print('OK')
"

# Copy a populated backend LLD as the on-disk canonical state
cp shield/evals/lld-docs/fixtures/lld-positive-backend.md \
   shield/evals/lld-docs/fixtures/neg-undocumented-lld/canonical-on-disk.md
```

- [ ] **Step 2: Note in the fixture how the eval will use it**

The `canonical-on-disk.md` represents what's at `docs/lld/user-service.md`.
The plan.json's design_ref has `anchor_url: null`. The `undocumented_lld`
rule should fire.

- [ ] **Step 3: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-undocumented-lld/
git commit -m "test(shield/lld-docs): neg-undocumented-lld fixture"
```

---

### Task 14: Author the fork-drift-uncaught fixture (caught at /plan-review time, not /implement)

**Files:**
- Create: `shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught/plan.json`
- Create: `shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught/canonical-now.md`

This catches the case where a canonical LLD has changed between /plan
drafting and /plan-review — before /implement gets a chance to auto-heal.
The relevant fingerprint is `lld_components[].fork_blob_sha` vs the
current canonical blob.

- [ ] **Step 1: Build**

```bash
mkdir -p shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught

python3 -c "
import json
src = json.load(open('shield/tests/fixtures/plan-1.5-valid.json'))
src['name'] = 'neg-fork-drift-uncaught'
# Set fork_blob_sha to a specific 40-hex string that won't match the live canonical
src['lld_components'][0]['fork_blob_sha'] = '0' * 40
json.dump(src, open('shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught/plan.json', 'w'), indent=2)
print('OK')
"

# canonical-now.md is just any populated LLD — its blob SHA won't equal '0'*40
cp shield/evals/lld-docs/fixtures/lld-positive-backend.md \
   shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught/canonical-now.md
```

- [ ] **Step 2: Note the rule wiring**

This requires a fifth /plan-review rule (`lld_fork_drift_uncaught`) or
extending the `lld_components_integrity` rule (Task 2) to also check
`fork_blob_sha` against the live canonical.

For M3 simplicity, **extend `lld_components_integrity`** to add a 4th
sub-check:

> If `lld_components[].fork_blob_sha` is non-null AND `docs/lld/<name>.md`
> exists AND `blob_sha(canonical) != fork_blob_sha` → finding
> `lld_fork_drift_uncaught` (severity: Medium). Suggested fix: re-run
> /plan to refresh fork_blob_sha.

Update `shield/skills/general/plan-review/SKILL.md` Task 2's rule
documentation block to include this fourth sub-check inline. Run a quick
edit:

```bash
# Append a note to the lld_components_integrity rule block.
# The actual edit goes in the M3 Task 2 commit — for this Task 14, just
# create the fixture; the rule update may have already happened.
echo "Reminder: ensure plan-review SKILL.md's lld_components_integrity rule covers fork_blob_sha drift."
```

If the rule edit hasn't happened, do it now: add to the block in plan-review/SKILL.md (Task 2):

```markdown
4. **Fork drift uncaught.** For every `lld_components[]` entry where
   `fork_blob_sha` is non-null AND `docs/lld/<name>.md` exists,
   verify `git hash-object docs/lld/<name>.md == fork_blob_sha`.
   Mismatch → finding `lld_fork_drift_uncaught` (Medium). Suggested fix:
   re-run /plan to refresh fork_blob_sha — /implement's step 5h will
   then auto-heal at milestone close.
```

- [ ] **Step 3: Commit**

```bash
git add shield/evals/lld-docs/fixtures/neg-fork-drift-uncaught/ shield/skills/general/plan-review/SKILL.md
git commit -m "test(shield/lld-docs): neg-fork-drift-uncaught fixture; extend integrity rule"
```

---

## Phase 5 — Eval runner for negatives

### Task 15: Extend run-lld-docs.py to handle negative fixtures

**Files:**
- Modify: `shield/evals/lld-docs.yaml`
- Modify: `shield/evals/run-lld-docs.py`

- [ ] **Step 1: Declare the negative fixtures in lld-docs.yaml**

In `shield/evals/lld-docs.yaml`, replace `fixtures.negative: []` with:

```yaml
  negative:
    - name: neg-missing-section-1
      fixture_dir: fixtures/neg-missing-section-1
      template_type: backend
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: module-layout
      severity: High

    - name: neg-missing-section-2
      fixture_dir: fixtures/neg-missing-section-2
      template_type: backend
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: data-model
      severity: High

    - name: neg-missing-section-3
      fixture_dir: fixtures/neg-missing-section-3
      template_type: backend
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: error-handling
      severity: High

    - name: neg-missing-section-4
      fixture_dir: fixtures/neg-missing-section-4
      template_type: backend
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: observability
      severity: High

    - name: neg-missing-section-5
      fixture_dir: fixtures/neg-missing-section-5
      template_type: infra
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: module-topology
      severity: High

    - name: neg-missing-section-6
      fixture_dir: fixtures/neg-missing-section-6
      template_type: infra
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: state-model-and-lifecycle
      severity: High

    - name: neg-missing-section-7
      fixture_dir: fixtures/neg-missing-section-7
      template_type: infra
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: cost-surface
      severity: High

    - name: neg-missing-section-8
      fixture_dir: fixtures/neg-missing-section-8
      template_type: infra
      kind: missing-always-on-section
      expect_error: missing-section
      expected_missing_anchor: observability-and-tagging
      severity: High

    - name: neg-missing-forced-subsection-1
      fixture_dir: fixtures/neg-missing-forced-subsection-1
      template_type: backend
      kind: missing-forced-subsection
      expect_error: missing-forced-subsection
      expected_missing_anchor: latency-breakdown
      severity: Medium

    - name: neg-missing-forced-subsection-2
      fixture_dir: fixtures/neg-missing-forced-subsection-2
      template_type: backend
      kind: missing-forced-subsection
      expect_error: missing-forced-subsection
      expected_missing_anchor: degradation
      severity: Medium

    - name: neg-missing-forced-subsection-3
      fixture_dir: fixtures/neg-missing-forced-subsection-3
      template_type: infra
      kind: missing-forced-subsection
      expect_error: missing-forced-subsection
      expected_missing_anchor: policy-checks
      severity: Medium

    - name: neg-missing-forced-subsection-4
      fixture_dir: fixtures/neg-missing-forced-subsection-4
      template_type: infra
      kind: missing-forced-subsection
      expect_error: missing-forced-subsection
      expected_missing_anchor: smoke-test
      severity: Medium

    - name: neg-vague-tbd
      fixture_dir: fixtures/neg-vague-tbd
      template_type: backend
      kind: vague-tbd
      expect_error: vague-tbd-in-always-on
      severity: Review

    - name: neg-pod-lifted-vague
      fixture_dir: fixtures/neg-pod-lifted-vague
      template_type: backend
      kind: pod-lifted-vague
      expect_error: pod-lifted-vague
      severity: Review

    - name: neg-component-not-in-registry
      fixture_dir: fixtures/neg-component-not-in-registry
      kind: plan-validation
      expect_error: lld_component_missing
      severity: High

    - name: neg-touches-lld-drift
      fixture_dir: fixtures/neg-touches-lld-drift
      kind: plan-validation
      expect_error: touches_lld_drift
      severity: High

    - name: neg-invalid-type
      fixture_dir: fixtures/neg-invalid-type
      kind: plan-validation
      expect_error: schema-validation-failure
      severity: High

    - name: neg-undocumented-lld
      fixture_dir: fixtures/neg-undocumented-lld
      kind: plan-review-finding
      expect_error: undocumented_lld
      severity: Medium

    - name: neg-fork-drift-uncaught
      fixture_dir: fixtures/neg-fork-drift-uncaught
      kind: plan-review-finding
      expect_error: lld_fork_drift_uncaught
      severity: Medium
```

19 negatives total.

- [ ] **Step 2: Extend the runner to handle negatives**

In `shield/evals/run-lld-docs.py`, after the path_b loop, add:

```python
# --- Negative fixture handling ---

def check_negative_fixture(fixture_cfg: dict) -> list[str]:
    """Run a negative fixture and verify the expected named-error fires."""
    errors: list[str] = []
    fixture_dir = EVAL_ROOT / "lld-docs" / fixture_cfg["fixture_dir"].lstrip("./")
    kind = fixture_cfg["kind"]
    expect_error = fixture_cfg["expect_error"]

    if kind in ("missing-always-on-section", "missing-forced-subsection", "vague-tbd", "pod-lifted-vague"):
        # Apply the lld_draft_review rubric checks to the fixture's lld.md
        lld_path = fixture_dir / "lld.md"
        if not lld_path.exists():
            return [f"expected fixture file {lld_path} not found"]
        errs = _structural_check(lld_path, fixture_cfg["template_type"])
        # Verify the expected error category fires
        if not any(expect_error in e for e in errs):
            errors.append(
                f"expected to fire '{expect_error}' but got errors: {errs}"
            )
    elif kind == "plan-validation":
        # Validate the plan.json with validate_plan.py; expect non-zero + named error in output
        plan_path = fixture_dir / "plan.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPT_VALIDATE), str(plan_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            errors.append(f"expected validate_plan.py to fail but exit=0")
        else:
            combined = (result.stdout + result.stderr).lower()
            if expect_error.lower() not in combined:
                errors.append(
                    f"expected named error '{expect_error}' in output; got: {combined!r}"
                )
    elif kind == "plan-review-finding":
        # Simulated /plan-review: load the plan + canonical, run the relevant rule check
        errs = _simulate_plan_review_finding(fixture_dir, fixture_cfg)
        if not any(expect_error in e for e in errs):
            errors.append(
                f"expected to fire '{expect_error}' but got: {errs}"
            )
    else:
        errors.append(f"unknown negative kind: {kind}")

    return errors


def _structural_check(lld_path: Path, template_type: str) -> list[str]:
    """Run the same structural checks lld_draft_review rule applies."""
    errors: list[str] = []
    content = lld_path.read_text()
    schema = load_schema(template_type)
    # Always-on sections present?
    for s in schema["sections"]:
        if not s.get("promote_on_demand"):
            if f"{{#{s['id']}}}" not in content:
                errors.append(f"missing-section: §{s['number']} {s['id']}")
    # §12 forced subsections present?
    twelve = next(s for s in schema["sections"] if s["number"] == 12)
    for sub in twelve.get("forced_subsections", []):
        if f"{{#{sub['id']}}}" not in content:
            errors.append(f"missing-forced-subsection: §{sub['number']} {sub['id']}")
    # Vague TBDs in always-on sections?
    import re
    for s in schema["sections"]:
        if s.get("promote_on_demand"):
            continue
        # Look for the section heading + capture the section body until the next heading
        pat = rf"## §{s['number']} [^\n]+\{{#{s['id']}\}}\n+([^\n]*(?:\n(?!##)[^\n]*)*)"
        m = re.search(pat, content)
        if m:
            body = m.group(1).strip()
            if re.match(r"^(TBD|TODO|to be determined|to do|\[fill in\])\s*$", body, re.IGNORECASE):
                errors.append(f"vague-tbd-in-always-on: §{s['number']} {s['id']}")
    # PoD lifted but vague?
    pod_lifted_pat = r"<details open>\s*<summary>([^<]+)</summary>\s*\n+([^<]*)</details>"
    for m in re.finditer(pod_lifted_pat, content, flags=re.DOTALL):
        body = m.group(2).strip()
        if re.match(r"^(TBD|TODO|n/a)\s*$", body, re.IGNORECASE):
            errors.append(f"pod-lifted-vague: {m.group(1).strip()}")
    return errors


def _simulate_plan_review_finding(fixture_dir: Path, cfg: dict) -> list[str]:
    """For neg-undocumented-lld and neg-fork-drift-uncaught, apply the relevant rule."""
    findings: list[str] = []
    expect = cfg["expect_error"]
    plan = json.loads((fixture_dir / "plan.json").read_text())
    if expect == "undocumented_lld":
        canonical = fixture_dir / "canonical-on-disk.md"  # stands in for docs/lld/<name>.md
        if not canonical.exists():
            return ["fixture missing canonical-on-disk.md"]
        # For each design_ref where doc==lld and anchor_url==null, if a matching canonical
        # exists, fire the finding.
        for epic in plan["epics"]:
            for story in epic["stories"]:
                for ref in story["design_refs"]:
                    if ref.get("doc") == "lld" and ref.get("anchor_url") is None:
                        if ref.get("component") and canonical.exists():
                            findings.append(
                                f"undocumented_lld: story {story['id']} component {ref['component']}"
                            )
    elif expect == "lld_fork_drift_uncaught":
        # Compute current canonical blob; compare to fork_blob_sha
        canonical = fixture_dir / "canonical-now.md"
        if not canonical.exists():
            return ["fixture missing canonical-now.md"]
        sys.path.insert(0, str(REPO_ROOT / "shield" / "scripts"))
        from lld_blob_sha import blob_sha
        for entry in plan.get("lld_components", []):
            if entry.get("fork_blob_sha"):
                current = blob_sha(canonical)
                if current != entry["fork_blob_sha"]:
                    findings.append(
                        f"lld_fork_drift_uncaught: component {entry['name']} "
                        f"fork={entry['fork_blob_sha']} current={current}"
                    )
    return findings


# In main(), after the path_b loop, add:
for f in cfg["fixtures"].get("negative", []):
    errs = check_negative_fixture(f)
    if errs:
        total_failures += 1
        print(f"FAIL — {f['name']}:")
        for e in errs:
            print(f"  - {e}")
    else:
        print(f"PASS (negative) — {f['name']}")
```

- [ ] **Step 3: Run the eval runner — verify every negative fires with the expected named error**

Run: `uv run --with pytest --with pyyaml --with jsonschema python shield/evals/run-lld-docs.py`

Expected: every negative fixture shows `PASS (negative)`, indicating the
expected error was raised. If any FAIL, the named-error string in
`lld-docs.yaml` (`expect_error`) might not match what the runner emits;
align the two.

- [ ] **Step 4: Commit**

```bash
git add shield/evals/lld-docs.yaml shield/evals/run-lld-docs.py
git commit -m "test(shield/lld-docs): eval runner — negative fixture handling (19 fixtures)"
```

---

## Phase 6 — CI wiring

### Task 16: Create .github/workflows/eval-lld.yml

**Files:**
- Create: `.github/workflows/eval-lld.yml`

- [ ] **Step 1: Inspect the existing eval workflows**

Run: `ls .github/workflows/ | grep -i eval`

If a similar eval workflow exists (e.g. `eval-plan-trd.yml`), mirror its
shape. Otherwise, write fresh.

- [ ] **Step 2: Write the workflow**

Create `.github/workflows/eval-lld.yml`:

```yaml
name: eval — lld-docs

on:
  pull_request:
    paths:
      - 'shield/skills/general/lld-docs/**'
      - 'shield/schema/plan-sidecar.schema.json'
      - 'shield/schema/lld-sections-backend.yaml'
      - 'shield/schema/lld-sections-infra.yaml'
      - 'shield/commands/lld.md'
      - 'shield/commands/plan.md'
      - 'shield/commands/implement.md'
      - 'shield/skills/general/plan-docs/**'
      - 'shield/skills/general/plan-review/SKILL.md'
      - 'shield/skills/general/implement-feature/SKILL.md'
      - 'shield/scripts/lld_blob_sha.py'
      - 'shield/scripts/lld_anchor_heuristic.py'
      - 'shield/scripts/run_lld_docs.py'
      - 'shield/scripts/run_step_5h.py'
      - 'shield/scripts/validate_plan.py'
      - 'shield/evals/lld-docs.yaml'
      - 'shield/evals/lld-docs/**'
      - 'shield/evals/run-lld-docs.py'
      - 'shield/tests/test_lld_*.py'
      - 'shield/tests/test_validate_plan_1_5.py'
      - '.github/workflows/eval-lld.yml'

jobs:
  eval-lld-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Run lld-docs eval
        run: |
          uv run --with pytest --with pyyaml --with jsonschema \
            python shield/evals/run-lld-docs.py

      - name: Run unit tests
        run: |
          uv run --with pytest --with pyyaml --with jsonschema \
            pytest shield/tests/test_validate_plan_1_5.py \
                   shield/tests/test_lld_blob_sha.py \
                   shield/tests/test_lld_anchor_heuristic.py \
                   -v
```

- [ ] **Step 3: Validate the YAML**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/eval-lld.yml')); print('OK')"`

Expected: `OK`.

- [ ] **Step 4: Push to a draft PR to verify the workflow fires on the right path triggers**

If running interactively, push to a feature branch with the workflow file
and confirm via `gh run list` that the workflow ran on the PR. (For
subagent execution, this step is informational; the PR opens at the very
end of M3.)

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/eval-lld.yml
git commit -m "ci(shield): eval-lld.yml — runs lld-docs eval + unit tests on relevant PRs"
```

---

## Phase 7 — Cutover

### Task 17: Plugin version bump + CHANGELOG entry

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify (or create): `shield/CHANGELOG.md`

- [ ] **Step 1: Bump the Shield plugin version**

In `.claude-plugin/marketplace.json`, find the `shield` plugin entry and
change its `version` from `"2.20.0"` to `"2.21.0"` (minor bump — new
commands, new schema field, no API breakage).

- [ ] **Step 2: Verify the version bump**

Run: `uv run --with jsonschema python -c "
import json
mp = json.load(open('.claude-plugin/marketplace.json'))
shield = next(p for p in mp['plugins'] if p['name'] == 'shield')
assert shield['version'] == '2.21.0', f'got {shield[\"version\"]}'
print('OK — shield@2.21.0')
"`

Expected: `OK — shield@2.21.0`

- [ ] **Step 3: Update or create shield/CHANGELOG.md**

If `shield/CHANGELOG.md` exists, prepend a new entry. If not, create it
with the entry as the only content.

Content:

```markdown
# Shield Changelog

## 2.21.0 — 2026-05-29

### Added

- **`/lld <component>` command (Path A)** — generate or update a
  component-scoped Low-Level Design at `docs/lld/<component>.md`. Two
  templates (backend pinned to PR #43, infra adapted to declarative IaC),
  selected automatically per repo markers or via `--type` flag. Bare
  `/lld` lists undocumented components.
- **TRD-driven LLD authoring (Path B)** — `/plan` now derives an
  `lld_components[]` registry from stories' `design_refs[]` (where
  `doc=="lld"`), computes a persisted `milestones[].touches_lld[]` rollup
  per milestone, and emits feature-folder drafts at
  `docs/shield/{feature}/lld-{component}.md` via the new `lld-docs` skill.
- **`/implement` step 5h — milestone-close promotion** — when the last
  story of a milestone closes, /implement walks `touches_lld[]`, performs
  a fork-drift concurrency check (with auto-heal re-merge), appends §14
  Changelog rows tying back to story IDs, atomic-renames each draft to
  `docs/lld/{component}.md`, and back-fills `design_refs[].anchor_url`
  via a token-overlap heuristic with `[exact-match] | [heuristic] | [fallback]`
  match-type labels.
- **`plan-sidecar.schema.json` 1.5** — adds the `lld_components[]` registry
  (`{name, type, fork_blob_sha}`) at the root and the persisted
  `milestones[].touches_lld[]` field. Tightens `design_refs[]` so
  `component` is required when `doc=="lld"`. Older sidecars (1.0–1.4)
  remain valid for read.
- **`/plan-review` rules** — four new rules: `touches_lld_drift` (High),
  `lld_components_integrity` (High; covers missing-registry-entry, type-enum,
  duplicate-name, and `lld_fork_drift_uncaught`), `undocumented_lld`
  (Medium; canonical exists but anchor_url null), `lld_draft_review`
  (High/Medium/Review depending on what's missing).
- **Eval coverage** — `shield/evals/lld-docs.yaml` ships 3 positive
  fixtures (backend LLD, infra LLD, 1.5 plan.json), 6 Path B fixtures
  (happy/fork-drift-clean/fork-drift-conflict/backfill-exact/backfill-fallback/
  just-in-time), and 19 negative fixtures covering every named error.
  `.github/workflows/eval-lld.yml` runs the suite on every relevant PR.

### Changed

- `shield/skills/general/plan-docs/SKILL.md` — `/plan` flow includes the
  new Path B emission step (derive registry, compute rollup, draft per
  registry entry, capture fork_blob_sha).
- `shield/skills/general/implement-feature/SKILL.md` — adds step 5h
  (milestone-close promotion) after step 5f (last_aligned_with update).
- `shield/skills/general/plan-review/SKILL.md` — new rule entries 0f–0i
  for the LLD surface.
- `shield/schema/output-paths.yaml` — registers `lld_draft_md` and
  `lld_canonical_md`.

### Back-compat

- 1.4 sidecars without `lld_components[]` validate as 1.5 (missing arrays
  default to empty).
- 1.4 sidecars with `design_refs[].doc=="lld"` and `component==null` are
  caught by `/plan-review`'s `lld_components_integrity` rule (High); fix
  the affected refs before upgrading.
- Path A (`/lld <component>`) works against repos with no plan.json at
  all — reverse-doc use case is supported without setup.

### Spec

- Brainstorming spec: [`docs/superpowers/specs/2026-05-28-lld-command-design.md`](docs/superpowers/specs/2026-05-28-lld-command-design.md).
- Implementation plans:
  - M1 — Foundation: [`docs/superpowers/plans/2026-05-28-lld-command-m1-foundation.md`](docs/superpowers/plans/2026-05-28-lld-command-m1-foundation.md)
  - M2 — TRD-driven authoring + promotion: [`docs/superpowers/plans/2026-05-28-lld-command-m2-trd-driven.md`](docs/superpowers/plans/2026-05-28-lld-command-m2-trd-driven.md)
  - M3 — Review wiring + cutover: [`docs/superpowers/plans/2026-05-28-lld-command-m3-review-and-cutover.md`](docs/superpowers/plans/2026-05-28-lld-command-m3-review-and-cutover.md)
```

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json shield/CHANGELOG.md
git commit -m "release(shield 2.21.0): /lld command + Path B + step 5h + plan-review rules

- /lld <component> (Path A) writes docs/lld/<component>.md (backend + infra)
- /plan emits Path B drafts at docs/shield/<feature>/lld-<component>.md
- /implement step 5h promotes drafts on milestone close
- plan-sidecar 1.5: lld_components[] + touches_lld[]
- /plan-review: touches_lld_drift + lld_components_integrity + undocumented_lld + lld_draft_review
- Eval coverage: 3 positives + 6 Path B + 19 negatives, CI workflow

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Self-review checklist

- [ ] **Spec coverage:** every M3-relevant spec item maps to a task:

  | Spec item | Implemented by |
  |---|---|
  | `/plan-review` touches_lld_drift rule | Task 1 |
  | `/plan-review` lld_components_integrity rule | Task 2 |
  | `/plan-review` undocumented_lld rule | Task 3 |
  | `/plan-review` lld_draft_review rule | Task 4 |
  | 8 missing-always-on negative fixtures | Tasks 5–6 |
  | 4 missing-forced-subsection fixtures | Tasks 7–8 |
  | Vague-TBD negative | Task 9 |
  | PoD-lifted-vague negative | Task 10 |
  | Component-not-in-registry negative | Task 11 |
  | Touches_lld-drift negative | Task 12 |
  | Invalid-type negative | Task 12 |
  | Undocumented-LLD negative | Task 13 |
  | Fork-drift-uncaught negative | Task 14 |
  | Eval runner negative handling | Task 15 |
  | CI workflow | Task 16 |
  | Plugin version bump + CHANGELOG | Task 17 |

- [ ] **Placeholder scan:**

  ```bash
  grep -nE 'TBD|TODO|implement later|fill in details' docs/superpowers/plans/2026-05-28-lld-command-m3-review-and-cutover.md | grep -v 'vague-tbd' | grep -v 'TODO: link when' | grep -v 'replace `TBD`' | grep -v 'TBD pattern' | head
  ```

  Any genuine placeholders (not in-content references to the TBD-detection
  rule) need fixing.

- [ ] **Type consistency:**
  - Rule names: `touches_lld_drift`, `lld_components_integrity`,
    `undocumented_lld`, `lld_draft_review`, `lld_fork_drift_uncaught`. Match
    across SKILL.md, eval YAML, and runner.
  - Severity labels: `High`, `Medium`, `Review`. Match across rule rows
    and rule blocks.
  - Negative fixture names: `neg-<kind>-<index>` pattern, kebab-case.

- [ ] **Dependencies on M1 + M2:** every task assumes both prior milestones
  are merged. Schema 1.5 (M1), step 5h (M2), eval-runner Path B handling
  (M2 Task 14–15) are all M3 prerequisites.

- [ ] **Cutover atomicity:** Task 17's version bump + CHANGELOG should be in
  the SAME commit as the last skill/code change. If Tasks 1–16 land in
  separate PRs, Task 17 is the final cutover commit. If all of M3 lands in
  one PR, Task 17 is just the last commit in the PR. Either way: no
  partial cutover where 2.21.0 ships without one of the new rules.

---

## Execution handoff

**M3 plan complete and saved to `docs/superpowers/plans/2026-05-28-lld-command-m3-review-and-cutover.md`.**

All three milestones are now planned:

| Milestone | Plan file | Approx tasks |
|---|---|---|
| M1 — Foundation | `2026-05-28-lld-command-m1-foundation.md` | 15 |
| M2 — TRD-driven authoring + promotion | `2026-05-28-lld-command-m2-trd-driven.md` | 17 |
| M3 — Review wiring + cutover | `2026-05-28-lld-command-m3-review-and-cutover.md` | 17 |

Execution options for whichever milestone we start with:

**1. Subagent-driven (recommended)** — fresh subagent per task; review between tasks; fast iteration.
**2. Inline** — work through tasks in this session.

**Which milestone first, and which approach?**
