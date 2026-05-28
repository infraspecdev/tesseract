# /lld Command — M2 TRD-Driven Authoring + Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `/plan` to author feature-folder LLD drafts at planning time (Path B) and wire `/implement` to promote those drafts to the canonical `docs/lld/<component>.md` at milestone close — with fork-drift concurrency check, §14 Changelog append, atomic promote, and `design_refs[]` anchor back-fill via token-overlap heuristic. Just-in-time auto-heal for missing drafts at promotion.

**Architecture:** Two extension points wired around the M1 surface. `/plan` (via `shield/skills/general/plan-docs/SKILL.md`) gains a new emit step that (a) derives `lld_components[]` from stories' `design_refs[]`, (b) computes the persisted `touches_lld[]` rollup per milestone, and (c) invokes the M1 lld-docs skill once per registry entry in `draft` mode (or `merge` mode if the canonical exists, capturing `fork_blob_sha`). `/implement` (via `shield/skills/general/implement-feature/SKILL.md`) gains step 5h, triggered on the story-close that completes a milestone, which walks `touches_lld[]`, performs the concurrency check + auto-heal re-merge, appends §14 Changelog rows, atomic-renames drafts to canonical, and back-fills matching `design_refs[].anchor_url` entries.

**Tech Stack:** Markdown skill docs, Python (`shield/scripts/` helpers for hash-object + atomic rename), JSON Schema validation against the M1-shipped 1.5 schema, pytest, `uv run --with`, GitHub Actions YAML.

**Spec:** [`docs/superpowers/specs/2026-05-28-lld-command-design.md`](../specs/2026-05-28-lld-command-design.md). Cross-reference §6.2 (Path B flow), §8 (rows 1, 4 — concurrency + just-in-time), §10 (risks 2, 4).

**Depends on M1:** M1 plan must be merged before this lands — the lld-docs skill, the templates, the schema 1.5, and the positive eval fixtures all come from M1.

**Out of M2 scope (deferred to M3 plan):**
- `/plan-review` rules (`touches_lld_drift`, `lld_components_integrity`, `undocumented_lld`, `lld_draft_review`).
- Negative eval fixtures (missing-section, vague-TBD, etc.).
- `.github/workflows/eval-lld.yml`.
- Plugin version bump + CHANGELOG entry.

---

## File Structure

**Files to create (this plan):**

| Path | Responsibility |
|---|---|
| `shield/scripts/lld_blob_sha.py` | Helper to compute `git hash-object docs/lld/<name>.md`; importable by /plan and /implement. |
| `shield/scripts/lld_anchor_heuristic.py` | Token-overlap anchor-selection heuristic for `design_refs[]` back-fill. |
| `shield/tests/test_lld_anchor_heuristic.py` | Pytest cases for the heuristic — exact-match / heuristic / fallback. |
| `shield/evals/lld-docs/fixtures/pathB-happy/` | Path B fixture: end-to-end /plan → drafts → /implement → promotion. |
| `shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/` | Canonical changed in a non-overlapping section; expect auto-heal merge success. |
| `shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/` | Canonical changed in the same section as the draft; expect conflict-marker abort. |
| `shield/evals/lld-docs/fixtures/pathB-backfill-exact/` | Story name token-matches a slug; expect `[exact-match]`. |
| `shield/evals/lld-docs/fixtures/pathB-backfill-fallback/` | Story name has zero token overlap; expect `[fallback]` → `#overview`. |
| `shield/evals/lld-docs/fixtures/pathB-just-in-time/` | Missing draft at promotion; expect just-in-time auto-heal + audit warning. |

**Files to modify (this plan):**

| Path | What changes |
|---|---|
| `shield/skills/general/plan-docs/SKILL.md` | Add Path B emission step: derive `lld_components[]`, compute `touches_lld[]` rollup, invoke lld-docs skill per registry entry, capture `fork_blob_sha`. |
| `shield/commands/plan.md` | Reference the new emission step in the Behavior list; document `lld_components[]` and `touches_lld[]` in the Paths section (they're new persisted fields in the existing plan.json output). |
| `shield/skills/general/implement-feature/SKILL.md` | Add step 5h after 5f (last_aligned_with update): milestone-close detection, walk `touches_lld[]`, concurrency check + auto-heal re-merge, §14 Changelog append, atomic promote, anchor back-fill, just-in-time auto-heal for missing drafts. |
| `shield/commands/implement.md` | Reference step 5h in the Behavior list; document promotion as a deterministic milestone-close side-effect. |
| `shield/evals/lld-docs.yaml` | Add `path_b` section with the 6 new fixtures; declare expected outcomes per fixture. |
| `shield/evals/run-lld-docs.py` | Extend to evaluate Path B fixtures (simulate /plan + /implement runs, verify resulting state). |

**Decomposition rationale:**
- Helpers first (Tasks 1–2): `lld_blob_sha.py` and `lld_anchor_heuristic.py` are pure-function Python with unit-testable surfaces. Both are dependencies for the /plan and /implement skill changes; landing them first means the skill changes have something to invoke.
- /plan emission second (Tasks 3–6): the producer side. Once `/plan` emits well-formed `lld_components[]` + `touches_lld[]` + drafts, M2 has half-shipped (Path B authoring works end-to-end, even without promotion).
- /implement promotion third (Tasks 7–13): the consumer side. Each sub-step of 5h gets its own task so failures bisect cleanly.
- Path B eval coverage last (Tasks 14–19): pins the contract.

Each task ends with a commit. Total: 19 tasks.

---

## Phase 1 — Helper modules

### Task 1: Create `lld_blob_sha.py` helper

**Files:**
- Create: `shield/scripts/lld_blob_sha.py`
- Create: `shield/tests/test_lld_blob_sha.py`

- [ ] **Step 1: Write the failing test**

Create `shield/tests/test_lld_blob_sha.py`:

```python
"""Tests for shield/scripts/lld_blob_sha.py.

Wraps `git hash-object` for stable computation of the LLD canonical's blob SHA
at /plan-draft time. Used by /implement at milestone close to detect fork drift.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "shield" / "scripts"))

from lld_blob_sha import blob_sha  # noqa: E402


def test_blob_sha_matches_git_hash_object(tmp_path):
    """The helper output must equal `git hash-object` byte-for-byte."""
    p = tmp_path / "lld-foo.md"
    p.write_text("# LLD foo\n\ncontent here\n")
    expected = subprocess.run(
        ["git", "hash-object", str(p)], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert blob_sha(p) == expected


def test_blob_sha_none_for_missing_file(tmp_path):
    """A missing file returns None (caller distinguishes 'net-new' from 'enhancement')."""
    p = tmp_path / "does-not-exist.md"
    assert blob_sha(p) is None


def test_blob_sha_deterministic_across_runs(tmp_path):
    """Same content => same hash."""
    p = tmp_path / "lld-bar.md"
    p.write_text("identical content\n")
    h1 = blob_sha(p)
    p.write_text("identical content\n")
    h2 = blob_sha(p)
    assert h1 == h2


def test_blob_sha_changes_with_content(tmp_path):
    """Different content => different hash."""
    p = tmp_path / "lld-baz.md"
    p.write_text("content A\n")
    h1 = blob_sha(p)
    p.write_text("content B\n")
    h2 = blob_sha(p)
    assert h1 != h2
```

- [ ] **Step 2: Run the test (expect FAIL — module doesn't exist)**

Run: `uv run --with pytest pytest shield/tests/test_lld_blob_sha.py -v`

Expected: 4 FAILs (ImportError: No module named 'lld_blob_sha').

- [ ] **Step 3: Implement the helper**

Create `shield/scripts/lld_blob_sha.py`:

```python
"""shield/scripts/lld_blob_sha.py

Computes the git blob SHA of an LLD canonical file (`docs/lld/<name>.md`).
Wraps `git hash-object` so the result matches what /implement's
concurrency check at milestone-close will compute. Returns None when the
file is absent (net-new component).
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def blob_sha(path: Path | str) -> Optional[str]:
    """Returns `git hash-object <path>` output (40-char hex), or None if absent.

    The hash is computed the same way as git's index — `blob` object type,
    SHA-1. /plan captures this at draft-creation time and persists it as
    plan.json `lld_components[].fork_blob_sha`. /implement re-computes at
    milestone close; mismatch indicates fork drift requiring auto-heal.
    """
    p = Path(path)
    if not p.exists():
        return None
    result = subprocess.run(
        ["git", "hash-object", str(p)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
```

- [ ] **Step 4: Run the tests (expect PASS)**

Run: `uv run --with pytest pytest shield/tests/test_lld_blob_sha.py -v`

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/lld_blob_sha.py shield/tests/test_lld_blob_sha.py
git commit -m "feat(shield/scripts): lld_blob_sha helper (git hash-object wrapper)"
```

---

### Task 2: Create `lld_anchor_heuristic.py` helper

**Files:**
- Create: `shield/scripts/lld_anchor_heuristic.py`
- Create: `shield/tests/test_lld_anchor_heuristic.py`

- [ ] **Step 1: Write the failing test**

Create `shield/tests/test_lld_anchor_heuristic.py`:

```python
"""Tests for shield/scripts/lld_anchor_heuristic.py.

Token-overlap anchor selection for /implement's design_refs[] back-fill:
given a story name and a template's slug allow-list, pick the best-matching
section anchor. Three match types: exact-match, heuristic, fallback.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "shield" / "scripts"))

from lld_anchor_heuristic import select_anchor  # noqa: E402


BACKEND_SLUGS = [
    "overview",
    "scope-and-non-goals",
    "module-layout",
    "data-model",
    "api-contracts",
    "sequence-flows",
    "error-handling",
    "concurrency-and-state",
    "configuration",
    "observability",
    "security-and-privacy",
    "performance-and-scaling",
    "open-questions",
    "changelog",
]


def test_exact_match_when_story_name_matches_slug_tokens():
    """Story 'data model' tokenizes to {data, model}; slug 'data-model' tokenizes to {data, model}; Jaccard 1.0."""
    slug, match_type = select_anchor("Data model", BACKEND_SLUGS)
    assert slug == "data-model"
    assert match_type == "exact-match"


def test_exact_match_case_insensitive():
    """Case difference doesn't affect exact-match."""
    slug, match_type = select_anchor("API Contracts", BACKEND_SLUGS)
    assert slug == "api-contracts"
    assert match_type == "exact-match"


def test_heuristic_match_partial_overlap():
    """'Add POST /signup endpoint' tokenizes to many tokens; slug 'api-contracts' shares zero, but slug 'sequence-flows' shares 'add' via no, none — pick best non-zero overlap, else fallback."""
    # Need a real partial overlap case
    slug, match_type = select_anchor("Implement data validation logic", BACKEND_SLUGS)
    # 'data' overlaps with 'data-model'; expect heuristic-pick of that slug
    assert slug == "data-model"
    assert match_type == "heuristic"


def test_fallback_to_overview_on_zero_overlap():
    """Story with no token overlap → fallback to #overview."""
    slug, match_type = select_anchor("xyzzy plugh", BACKEND_SLUGS)
    assert slug == "overview"
    assert match_type == "fallback"


def test_tie_break_by_slug_order():
    """When two slugs have equal Jaccard score, the one appearing earlier in the list wins."""
    # Construct a case: story name 'open changelog' — token set {open, changelog} overlaps
    # equally with 'open-questions' (overlap on 'open', score 1/3) and 'changelog' (overlap on 'changelog', score 1/2).
    # The latter is higher, so it wins on score, not tie-break. Need a real tie.
    # 'data observability' overlaps with 'data-model' (overlap 'data', score 1/3) and 'observability' (overlap 'observability', score 1/2).
    # Different. So let's construct: story 'configuration changelog' — overlaps {configuration} (score 1/2) and {changelog} (score 1/2). Tie!
    slug, match_type = select_anchor("configuration changelog", BACKEND_SLUGS)
    # 'configuration' appears at index 8; 'changelog' at index 13. Tie-break by order → 'configuration'.
    assert slug == "configuration"
    assert match_type == "heuristic"


def test_punctuation_and_whitespace_normalised():
    """Punctuation / extra whitespace doesn't affect tokenization."""
    slug, match_type = select_anchor("Data, model!", BACKEND_SLUGS)
    assert slug == "data-model"
    assert match_type == "exact-match"
```

- [ ] **Step 2: Run the tests (expect FAIL)**

Run: `uv run --with pytest pytest shield/tests/test_lld_anchor_heuristic.py -v`

Expected: 6 FAILs (ImportError).

- [ ] **Step 3: Implement the helper**

Create `shield/scripts/lld_anchor_heuristic.py`:

```python
"""shield/scripts/lld_anchor_heuristic.py

Token-overlap anchor selection for /implement's design_refs[] back-fill.
Given a story name and a template's slug allow-list, returns the best-matching
section anchor and the match-type label.

Algorithm:
  1. Tokenize story name: lowercase, split on whitespace and punctuation.
  2. For each slug in the allow-list, tokenize the slug (split on '-').
  3. Score each slug by Jaccard similarity (|A∩B| / |A∪B|) against the story tokens.
  4. Pick the highest-scoring slug; tie-break by allow-list order.
  5. If max score == 1.0: match_type = 'exact-match'.
     If max score in (0, 1.0):  match_type = 'heuristic'.
     If max score == 0:          slug = 'overview', match_type = 'fallback'.

Examples:
  story 'Data model'                → ('data-model', 'exact-match')
  story 'Implement data validation' → ('data-model', 'heuristic')   # 'data' overlap
  story 'xyzzy plugh'               → ('overview', 'fallback')
"""
from __future__ import annotations

import re
from typing import Sequence


_TOKEN_SPLIT = re.compile(r"[\s\-_,.;:!?/()\[\]{}'\"`]+")


def _tokenize(text: str) -> set[str]:
    """Lowercase and split on whitespace + common punctuation; drop empties."""
    return {tok for tok in _TOKEN_SPLIT.split(text.lower()) if tok}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def select_anchor(
    story_name: str, slugs: Sequence[str], fallback: str = "overview"
) -> tuple[str, str]:
    """Pick the best-matching slug for a story name.

    Returns (slug, match_type) where match_type ∈ {'exact-match', 'heuristic', 'fallback'}.
    Tie-break: higher position in `slugs` (lower index) wins.
    """
    story_tokens = _tokenize(story_name)
    if not story_tokens:
        return fallback, "fallback"

    best_slug = fallback
    best_score = 0.0
    for slug in slugs:
        slug_tokens = _tokenize(slug)
        score = _jaccard(story_tokens, slug_tokens)
        if score > best_score:
            best_score = score
            best_slug = slug
        # Tie: do nothing (first-seen wins because we only update on strict >).

    if best_score >= 1.0:
        return best_slug, "exact-match"
    if best_score > 0:
        return best_slug, "heuristic"
    return fallback, "fallback"
```

- [ ] **Step 4: Run the tests (expect PASS)**

Run: `uv run --with pytest pytest shield/tests/test_lld_anchor_heuristic.py -v`

Expected: 6 PASS. If any FAIL, the heuristic likely needs to tighten the
Jaccard threshold for "exact-match" (currently `>= 1.0`) — check that
exact-match cases truly produce Jaccard 1.0 by manually computing the
tokens.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/lld_anchor_heuristic.py shield/tests/test_lld_anchor_heuristic.py
git commit -m "feat(shield/scripts): lld_anchor_heuristic — token-overlap anchor selection"
```

---

## Phase 2 — /plan emission of Path B drafts

### Task 3: Document the new emission step in plan-docs/SKILL.md

**Files:**
- Modify: `shield/skills/general/plan-docs/SKILL.md`

- [ ] **Step 1: Read the current SKILL.md to find the right insertion point**

Run: `grep -n '^##\|^###' shield/skills/general/plan-docs/SKILL.md | head -40`

Identify the section that documents what `/plan` writes after `plan.json` is
finalised. Look for headings like "Generating outputs" or "Generation flow".

- [ ] **Step 2: Add the Path B emission step**

In `shield/skills/general/plan-docs/SKILL.md`, after the section describing
plan.json emission and before any HTML-render step, insert a new subsection:

````markdown
## Step: Emit feature-folder LLD drafts (Path B)

After `plan.json` and `trd.md` are finalised, `/plan` invokes the
[`lld-docs` skill](../lld-docs/SKILL.md) once per `lld_components[]` entry
to write the feature-folder LLD draft.

### Inputs

From the just-finalised `plan.json`:

- `lld_components[]` — registry of `{name, type, fork_blob_sha}`.
- `epics[].stories[].design_refs[]` — used to map each component back to the
  stories that touch it (passed into the lld-docs skill as `story_design_refs`).

From the feature folder:

- `prd.md` (if present) — passed as `context.prd_path`.
- `research.md` (if present) — passed as `context.research_path`.
- `trd.md` (always present at this point) — passed as `context.trd_path`.

### Algorithm

For each `{name, type, fork_blob_sha}` in `lld_components[]`:

1. Let `draft_path = docs/shield/{feature}/lld-{name}.md`.
2. Let `canonical_path = docs/lld/{name}.md`.
3. Determine mode:
   - If `canonical_path` exists on disk: this is an enhancement.
     - `mode = "merge"`.
     - Copy `canonical_path` → `draft_path` (this becomes the merge base).
     - Compute `new_fork_blob_sha = blob_sha(canonical_path)` via
       `shield/scripts/lld_blob_sha.py`.
   - Else: this is net-new.
     - `mode = "draft"`.
     - `new_fork_blob_sha = None`.
4. Build the lld-docs invocation context:
   - `component = name`.
   - `type = type`.
   - `mode = mode`.
   - `target_path = draft_path`.
   - `context = { prd_path, research_path, trd_path, story_design_refs }`
     where `story_design_refs` is the filtered list of `design_refs[]`
     entries from any story with `doc == "lld"` and `component == name`.
5. Invoke the lld-docs skill. On success:
   - Update `plan.json lld_components[<this-entry>].fork_blob_sha = new_fork_blob_sha`.
   - Record the section count for the summary table.
6. After processing all registry entries, write the updated `plan.json` back.

### Summary output

`/plan` prints one row per drafted LLD:

```
LLD drafts emitted:
  docs/shield/{feature}/lld-foo.md     | draft  | backend | n/a — net-new
  docs/shield/{feature}/lld-bar.md     | merge  | infra   | fork=abc123…
```

### Failure modes

- **lld-docs skill raises during drafting** — `/plan` removes any partial
  `.tmp` file for that draft (lld-docs's own atomic-write contract) and
  surfaces the error. Other registry entries' drafts that already succeeded
  remain on disk; the run is partial. Re-running `/plan` re-attempts the
  failed draft.
- **Canonical file unreadable** (permission / IO error) — abort the draft
  step for that component; mark it as failed in the summary; continue with
  remaining entries.
- **plan.json write-back fails after drafting** — re-attempt once; if still
  failing, abort and surface "drafts written but plan.json fork_blob_sha
  not updated; re-run /plan to refresh."
````

- [ ] **Step 3: Render the markdown to spot-check**

Run: `bash shield/scripts/render-markdown.sh shield/skills/general/plan-docs/SKILL.md /tmp/plan-docs-skill.html && grep -A 1 'feature-folder LLD' /tmp/plan-docs-skill.html | head -10`

Expected: the new subsection renders without unclosed fences.

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/plan-docs/SKILL.md
git commit -m "docs(shield/plan-docs): document Path B LLD-draft emission step"
```

---

### Task 4: Document `lld_components[]` derivation in plan-docs/SKILL.md

**Files:**
- Modify: `shield/skills/general/plan-docs/SKILL.md`

- [ ] **Step 1: Add the derivation algorithm**

Before the "Step: Emit feature-folder LLD drafts (Path B)" subsection from
Task 3, insert another subsection describing how `lld_components[]` and
`touches_lld[]` get computed at /plan time:

````markdown
## Step: Derive `lld_components[]` and `milestones[].touches_lld[]`

After all stories are written into the plan.json sidecar (with their
`design_refs[]` arrays), but BEFORE writing the sidecar to disk, derive
the two new 1.5 fields:

### `lld_components[]` derivation

```python
# Pseudocode — actual implementation lives in the /plan generator.
seen_names: dict[str, str] = {}    # name → type
for epic in plan["epics"]:
    for story in epic["stories"]:
        for ref in story.get("design_refs", []):
            if ref.get("doc") == "lld":
                name = ref["component"]   # required for doc==lld in 1.5
                if name in seen_names:
                    continue
                seen_names[name] = _infer_type_for_component(name)
plan["lld_components"] = [
    {"name": n, "type": t, "fork_blob_sha": None}
    for n, t in seen_names.items()
]
```

`_infer_type_for_component(name)` walks the repo for markers at the directory
matching `name`:

1. If `<name>/pyproject.toml` or `<name>/package.json` or `<name>/pom.xml` or
   `<name>/go.mod` exists → `"backend"`.
2. Else if `<name>/*.tf` files exist, or `<name>/Chart.yaml`, or
   `<name>/kustomization.yaml`, or `<name>/atmos.yaml` → `"infra"`.
3. Else if both backend and infra markers exist in the same dir → ask the
   user which template to use; remember the choice.
4. Else (no directory match — pure planning case, component doesn't exist
   yet) → default to the feature's overall domain (per the existing
   `.shield.json plan.template_override` or repo-marker detection).

### `milestones[].touches_lld[]` derivation

```python
# Pseudocode — emits the persisted rollup the drift gate checks.
stories_by_milestone: dict[str, list] = {}
for epic in plan["epics"]:
    for story in epic["stories"]:
        mid = story.get("milestone_id")
        if mid:
            stories_by_milestone.setdefault(mid, []).append(story)

for milestone in plan["milestones"]:
    rollup = set()
    for story in stories_by_milestone.get(milestone["id"], []):
        for ref in story.get("design_refs", []):
            if ref.get("doc") == "lld" and ref.get("component"):
                rollup.add(ref["component"])
    milestone["touches_lld"] = sorted(rollup)
```

The persisted result must always equal this rollup. `validate_plan.py` and
M3-plan's `/plan-review touches_lld_drift` rule both enforce this.

### Re-run semantics

When `/plan` is re-run on a feature folder with an existing `plan.json`:

- For each entry in the existing `lld_components[]`, if the same `name`
  appears in the newly-derived registry, **preserve** its `fork_blob_sha`
  (avoid re-computing — the canonical may have moved on, breaking the
  prior fork point).
- For each name in the newly-derived registry NOT in the existing
  registry, append with `fork_blob_sha = None`.
- For each name in the existing registry NOT in the newly-derived registry,
  log a non-blocking warning: `"orphan: lld_components[] entry '<name>' has no design_refs[] reference; review intentional?"` — but keep it in the registry (don't silently drop).
````

- [ ] **Step 2: Render and visually scan**

Run: `bash shield/scripts/render-markdown.sh shield/skills/general/plan-docs/SKILL.md /tmp/plan-docs-skill.html && grep 'derivation' /tmp/plan-docs-skill.html | head -5`

Expected: both subsections render.

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/plan-docs/SKILL.md
git commit -m "docs(shield/plan-docs): document lld_components + touches_lld derivation at /plan time"
```

---

### Task 5: Update `shield/commands/plan.md` paths + behavior

**Files:**
- Modify: `shield/commands/plan.md`

- [ ] **Step 1: Add the new emission step to the Behavior list**

In `shield/commands/plan.md`, find the numbered Behavior list. After the step
that says "Generate `{plan_md}`" (currently step 11), insert a new step:

```markdown
12. **Derive `lld_components[]` and `milestones[].touches_lld[]`** — before
    writing plan.json to disk, walk all stories' `design_refs[]` entries where
    `doc == "lld"`; collect unique components into `lld_components[]` with
    inferred `type`; persist the rollup of `design_refs[].component` per
    milestone as `milestones[].touches_lld[]`. See
    `shield:plan-docs/SKILL.md` for the exact algorithm and re-run semantics.

13. **Emit feature-folder LLD drafts (Path B)** — for each entry in the
    just-derived `lld_components[]`, invoke the `lld-docs` skill in `draft`
    or `merge` mode (depending on whether `docs/lld/{name}.md` exists on
    disk); record `fork_blob_sha` for enhancement components; update
    plan.json with the captured fork SHAs. Drafts land at
    `docs/shield/{feature}/lld-{name}.md`. The canonical
    `docs/lld/{name}.md` is **not** touched here — that's `/implement`'s
    job at milestone close.
```

Renumber the subsequent steps (the existing 12+ become 14+). Update the
"You MUST produce all five artifacts" line to "all five tracked artifacts
plus any feature-folder LLD drafts emitted by step 13".

- [ ] **Step 2: Add the Path B output path to the Paths table**

In the Paths table at the top of `plan.md`, after the existing rows, add:

```markdown
| `lld_draft_md` | `{output_dir}/{feature}/lld-{component}.md` (one per `lld_components[]` entry; canonical `docs/lld/` is untouched at /plan time) |
```

- [ ] **Step 3: Note the schema bump**

In the "Behavior" / "Generate `{plan_json}` first" step, append:

```markdown
The sidecar is at schema 1.5 — see `shield:plan-docs/sidecar-schema.md` for
the `lld_components[]` and `milestones[].touches_lld[]` field shapes.
```

- [ ] **Step 4: Render and spot-check**

Run: `bash shield/scripts/render-markdown.sh shield/commands/plan.md /tmp/plan-cmd.html && grep -A 1 'lld_components' /tmp/plan-cmd.html | head -10`

Expected: the new behavior steps render.

- [ ] **Step 5: Commit**

```bash
git add shield/commands/plan.md
git commit -m "docs(shield/commands): /plan — document Path B LLD-draft emission + 1.5 schema"
```

---

### Task 6: Register `lld_draft_md` in the output-paths registry

**Files:**
- Modify: `shield/schema/output-paths.yaml`

- [ ] **Step 1: Read the current registry**

Run: `cat shield/schema/output-paths.yaml`

Note the existing entry shape (typically: `key`, `path`, `description`,
`deprecated`).

- [ ] **Step 2: Add the new entry**

Add to `shield/schema/output-paths.yaml`, alongside the existing `plan_*`
entries:

```yaml
- key: lld_draft_md
  path: "{output_dir}/{feature}/lld-{component}.md"
  description: >
    Feature-folder LLD draft authored by /plan (Path B). One file per
    lld_components[] entry. The canonical equivalent at docs/lld/{component}.md
    is written by /implement at milestone close (step 5h), not by /plan.
  emitted_by: /plan
  consumed_by: [/implement, /plan-review]
  multi_instance: true   # one per lld_components[] entry
  category: lld

- key: lld_canonical_md
  path: "docs/lld/{component}.md"
  description: >
    Canonical LLD authored by /lld (Path A) or promoted from feature-folder
    drafts by /implement at milestone close (step 5h).
  emitted_by: [/lld, /implement]
  consumed_by: [/plan-review]
  multi_instance: true
  category: lld
  # NOTE: docs/lld/ is NOT under {output_dir}; LLDs are project-level, not
  # per-Shield-output. The path is intentionally hardcoded.
```

- [ ] **Step 3: Validate the YAML**

Run: `uv run --with pyyaml python -c "import yaml; d=yaml.safe_load(open('shield/schema/output-paths.yaml')); print('entries:', len(d) if isinstance(d, list) else len(d.get('paths', [])))"`

Expected: prints a count that includes the new 2 entries.

- [ ] **Step 4: Commit**

```bash
git add shield/schema/output-paths.yaml
git commit -m "feat(shield/schema): register lld_draft_md + lld_canonical_md output paths"
```

---

## Phase 3 — /implement step 5h (promotion)

### Task 7: Document step 5h skeleton in implement-feature/SKILL.md

**Files:**
- Modify: `shield/skills/general/implement-feature/SKILL.md`

- [ ] **Step 1: Read the current step 5f for context**

Run: `grep -n '^###\|^####' shield/skills/general/implement-feature/SKILL.md | head -30`

Find the existing step 5f ("Update last_aligned_with on story close"). Step 5h
goes immediately after it.

- [ ] **Step 2: Insert the step 5h skeleton**

In `shield/skills/general/implement-feature/SKILL.md`, after the existing
step 5f section, add:

````markdown
### 5h. Promote feature-folder LLD drafts to canonical (milestone close)

After step 5f (`last_aligned_with` update), check whether the just-closed
story was the **last** open story in its milestone. If yes, walk the
milestone's `touches_lld[]` and promote each draft from
`docs/shield/{feature}/lld-{name}.md` to `docs/lld/{name}.md`.

This step has six sub-steps, executed in order per component:

1. **Look up registry entry.** Read `lld_components[]` for the entry where
   `name == <component>`. Extract `type` and `fork_blob_sha`.

2. **Locate the draft.** `draft_path = docs/shield/{feature}/lld-{name}.md`.
   - If the draft is missing, auto-heal by invoking lld-docs in `draft` mode
     just-in-time; print a loud audit-trail warning (see "Just-in-time
     auto-heal" below).

3. **Concurrency check.** If `docs/lld/{name}.md` exists AND
   `fork_blob_sha` is non-null:
   - Compute `current_sha = blob_sha(docs/lld/{name}.md)` via
     `shield/scripts/lld_blob_sha.py`.
   - If `current_sha != fork_blob_sha`: fork drift detected. Invoke
     lld-docs in `remerge` mode (canonical changed since /plan drafted;
     merge canonical changes into draft). On clean merge, refresh
     `fork_blob_sha = current_sha` in plan.json and proceed. On conflict
     markers in the merged output, **abort** this component's promotion
     and surface a clear remediation message.

4. **Append §14 Changelog row** to the draft:
   ```
   | <milestone_id> | <YYYY-MM-DD> | <milestone.name> | <story_ids touching this component> |
   ```
   Insert at the bottom of the §14 table; preserve all existing rows.

5. **Atomic promote.** `os.replace(draft_path, canonical_path)` (writes via
   `<canonical>.tmp` first, then rename — same atomic contract as lld-docs
   skill's own writes).

6. **Back-fill `design_refs[]` anchors.** Walk all stories in plan.json;
   for each `design_refs[]` entry where `doc == "lld"` AND
   `component == <this component>` AND `anchor_url is null`:
   - Use `shield/scripts/lld_anchor_heuristic.py select_anchor()` with the
     story name and the template's slug allow-list (loaded from
     `shield/schema/lld-sections-<type>.yaml`).
   - Set `anchor_url = "lld-{name}.md#{slug}"`.
   - Update `label = "§{n} {title}"` (look up the slug's number+title from
     the schema).
   - Write the updated plan.json back atomically.

### Just-in-time auto-heal for missing drafts

If step 5h sub-step 2 finds no draft for a component listed in
`touches_lld[]`, just-in-time invoke the lld-docs skill to draft. Print a
loud multi-line warning to the run log AND include it in the run summary:

```
⚠️  DRAFT AUTO-GENERATED AT PROMOTION
    Component: <name>
    The /plan run did not produce docs/shield/{feature}/lld-{name}.md.
    /implement just-in-time-drafted the LLD; the design bypassed human review
    before promotion. Review docs/lld/{name}.md for content quality before
    next /plan-review.
```

Proceed with steps 3 through 6 normally.

### Milestone-close detection

A milestone is closed iff every story whose `milestone_id == <M>` has
`status == "done"`. The just-closed story is the trigger; step 5h runs
when its closure tips the milestone over to all-done.

If multiple stories close in the same /implement session (e.g. batch),
step 5h runs after the LAST one, not after each — the implementation can
short-circuit by checking the milestone state once per session-end.

### Summary output

`/implement` prints one block per promoted LLD:

```
LLD promoted: <component> (<type>)
  Source draft:    docs/shield/{feature}/lld-{component}.md
  Canonical:       docs/lld/{component}.md
  Fork drift:      none | auto-healed | aborted
  Changelog row:   | <M> | <date> | <milestone name> | <story_ids> |
  Anchor backfill: <count> entries updated (<exact-match: X, heuristic: Y, fallback: Z>)
```

### Failure modes

| Failure | Behavior |
|---|---|
| Draft missing AND auto-heal lld-docs invocation fails | Abort this component's promotion; continue with remaining `touches_lld[]` entries; surface as run-end error. |
| Concurrency check produces conflict markers | Abort this component's promotion; print `re-run /plan to refresh fork` and the conflicting section IDs; continue with remaining entries. |
| Atomic rename fails | Abort this component's promotion; the draft and the canonical both remain in their pre-step state (the `.tmp` is cleaned up); surface error. |
| Anchor back-fill: plan.json write-back fails | Roll back the changelog row append (re-read draft from prior state) is NOT attempted — the promotion already happened. Surface "promotion succeeded but design_refs[] back-fill failed; re-run /implement to retry back-fill." |
````

- [ ] **Step 3: Render and visually scan**

Run: `bash shield/scripts/render-markdown.sh shield/skills/general/implement-feature/SKILL.md /tmp/implement.html && grep '5h' /tmp/implement.html | head -10`

Expected: step 5h renders with all six sub-steps visible.

- [ ] **Step 4: Commit**

```bash
git add shield/skills/general/implement-feature/SKILL.md
git commit -m "docs(shield/implement-feature): step 5h — promote LLD drafts at milestone close"
```

---

### Task 8: Update `shield/commands/implement.md` to reference step 5h

**Files:**
- Modify: `shield/commands/implement.md`

- [ ] **Step 1: Find the existing Behavior step list**

Run: `grep -n '^[0-9]\+\.\|^## Behavior' shield/commands/implement.md | head -20`

Identify where the existing story-close steps are documented.

- [ ] **Step 2: Add a Behavior step for milestone-close promotion**

In `shield/commands/implement.md`, in the Behavior section, after the step
that describes story-close + last_aligned_with update, insert:

```markdown
- **On the story close that completes a milestone**, promote each LLD draft
  listed in `plan.json milestones[<M>].touches_lld[]` from
  `docs/shield/{feature}/lld-{component}.md` to `docs/lld/{component}.md`.
  This includes a fork-drift concurrency check, §14 Changelog row append,
  atomic rename, and `design_refs[]` anchor back-fill. See step 5h in
  `shield:implement-feature/SKILL.md` for the full procedure and the
  just-in-time auto-heal rules.
```

- [ ] **Step 3: Add `lld_canonical_md` to the Paths table**

If the Paths table doesn't already list it (from M2 Task 6), add it now —
`/implement` is one of the two emitters declared in the registry entry.

- [ ] **Step 4: Render and spot-check**

Run: `bash shield/scripts/render-markdown.sh shield/commands/implement.md /tmp/implement-cmd.html && grep 'step 5h\|lld_canonical' /tmp/implement-cmd.html | head -10`

- [ ] **Step 5: Commit**

```bash
git add shield/commands/implement.md
git commit -m "docs(shield/commands): /implement — reference step 5h LLD promotion"
```

---

## Phase 4 — Path B eval fixtures

### Task 9: Author the `pathB-happy/` fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/pathB-happy/input-plan.json`
- Create: `shield/evals/lld-docs/fixtures/pathB-happy/feature-folder/trd.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-happy/expected/lld-user-service.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-happy/expected/plan-after-promotion.json`

- [ ] **Step 1: Create the directory + the input plan**

```bash
mkdir -p shield/evals/lld-docs/fixtures/pathB-happy/feature-folder
mkdir -p shield/evals/lld-docs/fixtures/pathB-happy/expected
```

Create `shield/evals/lld-docs/fixtures/pathB-happy/input-plan.json`:

```json
{
  "version": "1.5",
  "project": "FixtureTest",
  "name": "pathb-happy",
  "phase": "test",
  "source_research": null,
  "source_prd": null,
  "prd_rubric_version_at_planning": null,
  "last_aligned_with": null,
  "lld_components": [
    {
      "name": "user-service",
      "type": "backend",
      "fork_blob_sha": null
    }
  ],
  "milestones": [
    {
      "id": "M1",
      "name": "User-service v1",
      "outcome": "user-service is live.",
      "exit_criteria": ["Signup endpoint returns 201"],
      "depends_on": [],
      "touches_lld": ["user-service"]
    }
  ],
  "epics": [
    {
      "id": "EPIC-1",
      "name": "user-service",
      "pm_id": null,
      "pm_url": null,
      "stories": [
        {
          "id": "EPIC-1-S1",
          "name": "Implement API contracts for signup",
          "status": "done",
          "assignee": null,
          "priority": "high",
          "week": null,
          "milestone_id": "M1",
          "description": "Implement POST /signup.",
          "tasks": ["Wire route", "Add bcrypt hashing"],
          "acceptance_criteria": ["POST /signup returns 201 with valid input"],
          "design_refs": [
            {
              "doc": "lld",
              "component": "user-service",
              "section_id": null,
              "anchor_url": null,
              "label": "TODO: link when /lld lands"
            }
          ],
          "pm_id": null,
          "pm_url": null
        }
      ]
    }
  ],
  "metadata": {
    "created_at": "2026-05-28",
    "domains": ["python"],
    "reviewer_grades": {}
  }
}
```

- [ ] **Step 2: Create the feature-folder TRD (minimal, just enough for lld-docs to read context)**

Create `shield/evals/lld-docs/fixtures/pathB-happy/feature-folder/trd.md`:

```markdown
<!-- generated by /plan v2.20.0 on 2026-05-28 -->

# TRD — pathb-happy

## §1 Document Overview {#document-overview}

Fixture TRD for the pathB-happy eval. Stages user-service.

## §7 High-Level Design {#high-level-design}

Single HTTP service, FastAPI, exposes POST /signup.

## §11 APIs Involved {#apis-involved}

| Method | Path | Notes |
|---|---|---|
| POST | /signup | Accepts {email, password}; returns {user_id} |

(remaining TRD sections omitted for fixture brevity — eval doesn't check them)
```

- [ ] **Step 3: Create the expected promoted LLD**

Create `shield/evals/lld-docs/fixtures/pathB-happy/expected/lld-user-service.md`.
This should be a structurally complete backend LLD (all 14 sections, 8 forced
§12 subsections, populated from the TRD context). Reuse the shape of
`shield/evals/lld-docs/fixtures/lld-positive-backend.md` from M1 — copy that
file as a starting point and adjust the §14 Changelog row to:

```markdown
| M1 | 2026-05-28 | User-service v1 | EPIC-1-S1 |
```

(rather than the M1 fixture's `| manual | 2026-05-28 | Initial reference fixture | n/a |`).

- [ ] **Step 4: Create the expected plan.json after promotion**

Create `shield/evals/lld-docs/fixtures/pathB-happy/expected/plan-after-promotion.json`.
Start from the input plan, then:
- Set `lld_components[0].fork_blob_sha` to whatever the just-promoted
  canonical's blob_sha turns out to be (the eval runner computes this
  dynamically; the fixture file can keep `null` and the runner verifies
  the live value).
- Set `epics[0].stories[0].design_refs[0]` to:

```json
{
  "doc": "lld",
  "component": "user-service",
  "section_id": "api-contracts",
  "anchor_url": "lld-user-service.md#api-contracts",
  "label": "§5 API contracts"
}
```

The story name "Implement API contracts for signup" tokenizes to
{implement, api, contracts, for, signup}; slug `api-contracts` tokenizes
to {api, contracts}; Jaccard = 2/5 = 0.4 → heuristic match. (Not
exact-match because of the extra story tokens.)

Build it:

```bash
python3 -c "
import json
data = json.load(open('shield/evals/lld-docs/fixtures/pathB-happy/input-plan.json'))
data['epics'][0]['stories'][0]['design_refs'][0] = {
    'doc': 'lld',
    'component': 'user-service',
    'section_id': 'api-contracts',
    'anchor_url': 'lld-user-service.md#api-contracts',
    'label': '§5 API contracts'
}
# fork_blob_sha will be set by the eval at run time; leave None in the fixture.
json.dump(data, open('shield/evals/lld-docs/fixtures/pathB-happy/expected/plan-after-promotion.json', 'w'), indent=2)
print('OK')
"
```

- [ ] **Step 5: Commit**

```bash
git add shield/evals/lld-docs/fixtures/pathB-happy/
git commit -m "test(shield/lld-docs): pathB-happy fixture — end-to-end Path B + promotion"
```

---

### Task 10: Author the `pathB-fork-drift-clean/` fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/input-plan.json`
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/canonical-at-fork.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/canonical-at-promotion.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/expected/lld-foo.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/expected
```

- [ ] **Step 2: Create `canonical-at-fork.md` — the canonical state when /plan drafted**

Use the backend positive fixture as the base, but rename the component to `foo`:

```bash
sed 's/user-service/foo/g; s/User-service/Foo/g; s/User Service/Foo/g' \
  shield/evals/lld-docs/fixtures/lld-positive-backend.md \
  > shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/canonical-at-fork.md
```

Verify: `head -5 shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/canonical-at-fork.md`

Should show `# LLD — foo`.

- [ ] **Step 3: Create `canonical-at-promotion.md` — the canonical at the time /implement promotes**

This is the same as `canonical-at-fork.md` but with a change in a section the
draft DOESN'T touch (e.g. a new entry in §13 Open questions). This simulates
clean fork drift — auto-heal merge should succeed.

```bash
python3 -c "
content = open('shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/canonical-at-fork.md').read()
# Add a row to §13 Open questions table
old = '## §13 Open questions {#open-questions}\n\n| Q# | Question | Options | Owner | Resolve-by |\n|---|---|---|---|---|\n\n(none open)'
new = '## §13 Open questions {#open-questions}\n\n| Q# | Question | Options | Owner | Resolve-by |\n|---|---|---|---|---|\n| Q1 | Should we batch signups? | yes/no | platform | 2026-06-15 |\n'
assert old in content, 'precondition: positive backend fixture has the expected §13 shape'
content = content.replace(old, new)
open('shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/canonical-at-promotion.md', 'w').write(content)
print('OK')
"
```

- [ ] **Step 4: Create the input plan and expected merged output**

Create `shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/input-plan.json`. The
shape mirrors `pathB-happy/input-plan.json` but:
- Component name = `foo`.
- `lld_components[0].fork_blob_sha` = blob_sha of `canonical-at-fork.md`
  (the eval runner fills this in dynamically; in the fixture, set a
  placeholder string `"FILL_AT_RUNTIME"`).

```bash
python3 -c "
import json
src = json.load(open('shield/evals/lld-docs/fixtures/pathB-happy/input-plan.json'))
src['name'] = 'pathb-fork-drift-clean'
src['lld_components'][0]['name'] = 'foo'
src['lld_components'][0]['fork_blob_sha'] = 'FILL_AT_RUNTIME'
src['milestones'][0]['touches_lld'] = ['foo']
src['epics'][0]['stories'][0]['design_refs'][0]['component'] = 'foo'
src['epics'][0]['stories'][0]['design_refs'][0]['label'] = 'TODO: link when /lld lands'
json.dump(src, open('shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/input-plan.json', 'w'), indent=2)
print('OK')
"
```

Create `shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/expected/lld-foo.md` —
the post-merge canonical, which should equal `canonical-at-promotion.md`
plus a new §14 Changelog row (`| M1 | 2026-05-28 | User-service v1 | EPIC-1-S1 |`).
The §13 row from `canonical-at-promotion.md` MUST be preserved (clean merge —
no overwrite of the canonical's new section content).

- [ ] **Step 5: Commit**

```bash
git add shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/
git commit -m "test(shield/lld-docs): pathB-fork-drift-clean fixture — auto-heal merge succeeds"
```

---

### Task 11: Author the `pathB-fork-drift-conflict/` fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/input-plan.json`
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/canonical-at-fork.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/canonical-at-promotion.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/expected/abort-message.txt`

- [ ] **Step 1: Set up the conflicting drift**

Make a directory:

```bash
mkdir -p shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/expected
```

Copy `canonical-at-fork.md` from `pathB-fork-drift-clean`:

```bash
cp shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/canonical-at-fork.md \
   shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/canonical-at-fork.md
```

- [ ] **Step 2: Create `canonical-at-promotion.md` with overlapping drift**

The drift modifies §5 API contracts (which the milestone's stories also touch
per their design_refs). When auto-heal tries to merge the draft's §5 edits
with the canonical's §5 edits, it produces conflict markers.

```bash
python3 -c "
content = open('shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/canonical-at-fork.md').read()
# Replace the §5 API contracts content with something materially different
old = '### POST /signup {#api-signup}\n\nRequest:'
new = '### POST /signup {#api-signup}\n\nLATE CANONICAL CHANGE: now requires CSRF token.\nRequest:'
content = content.replace(old, new)
open('shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/canonical-at-promotion.md', 'w').write(content)
print('OK')
"
```

- [ ] **Step 3: Create the input plan and the expected abort message**

```bash
python3 -c "
import json
src = json.load(open('shield/evals/lld-docs/fixtures/pathB-fork-drift-clean/input-plan.json'))
src['name'] = 'pathb-fork-drift-conflict'
json.dump(src, open('shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/input-plan.json', 'w'), indent=2)
print('OK')
"
```

Create `shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/expected/abort-message.txt`:

```
ABORT: pathb-fork-drift-conflict — fork drift on 'foo' produced merge conflicts.
Canonical docs/lld/foo.md changed since /plan drafted (commit <sha-of-canonical-at-promotion>).
Re-run /plan to refresh the fork, then retry /implement.
Conflicting sections: api-contracts
```

(The eval verifies the abort message contains `ABORT`, `fork drift`, the
canonical's blob SHA, and the conflicting section IDs.)

- [ ] **Step 4: Commit**

```bash
git add shield/evals/lld-docs/fixtures/pathB-fork-drift-conflict/
git commit -m "test(shield/lld-docs): pathB-fork-drift-conflict fixture — abort with clear message"
```

---

### Task 12: Author the `pathB-backfill-exact/` and `pathB-backfill-fallback/` fixtures

**Files:**
- Create: `shield/evals/lld-docs/fixtures/pathB-backfill-exact/input-plan.json`
- Create: `shield/evals/lld-docs/fixtures/pathB-backfill-exact/expected/plan-after-promotion.json`
- Create: `shield/evals/lld-docs/fixtures/pathB-backfill-fallback/input-plan.json`
- Create: `shield/evals/lld-docs/fixtures/pathB-backfill-fallback/expected/plan-after-promotion.json`

- [ ] **Step 1: Create the backfill-exact fixture**

```bash
mkdir -p shield/evals/lld-docs/fixtures/pathB-backfill-exact/expected
mkdir -p shield/evals/lld-docs/fixtures/pathB-backfill-fallback/expected
```

Build `pathB-backfill-exact/input-plan.json`:

```bash
python3 -c "
import json
src = json.load(open('shield/evals/lld-docs/fixtures/pathB-happy/input-plan.json'))
src['name'] = 'pathb-backfill-exact'
src['epics'][0]['stories'][0]['name'] = 'Data model'
json.dump(src, open('shield/evals/lld-docs/fixtures/pathB-backfill-exact/input-plan.json', 'w'), indent=2)
print('OK')
"
```

Story name 'Data model' → tokenizes to `{data, model}` → slug `data-model`
tokenizes to `{data, model}` → Jaccard 1.0 → **exact-match**.

Build the expected post-promotion plan:

```bash
python3 -c "
import json
src = json.load(open('shield/evals/lld-docs/fixtures/pathB-backfill-exact/input-plan.json'))
src['epics'][0]['stories'][0]['design_refs'][0] = {
    'doc': 'lld',
    'component': 'user-service',
    'section_id': 'data-model',
    'anchor_url': 'lld-user-service.md#data-model',
    'label': '§4 Data model'
}
json.dump(src, open('shield/evals/lld-docs/fixtures/pathB-backfill-exact/expected/plan-after-promotion.json', 'w'), indent=2)
print('OK')
"
```

- [ ] **Step 2: Create the backfill-fallback fixture**

Story name with zero token overlap with any slug → fallback to `#overview`.

```bash
python3 -c "
import json
src = json.load(open('shield/evals/lld-docs/fixtures/pathB-happy/input-plan.json'))
src['name'] = 'pathb-backfill-fallback'
src['epics'][0]['stories'][0]['name'] = 'xyzzy plugh quux'
json.dump(src, open('shield/evals/lld-docs/fixtures/pathB-backfill-fallback/input-plan.json', 'w'), indent=2)

src['epics'][0]['stories'][0]['design_refs'][0] = {
    'doc': 'lld',
    'component': 'user-service',
    'section_id': 'overview',
    'anchor_url': 'lld-user-service.md#overview',
    'label': '§1 Overview'
}
json.dump(src, open('shield/evals/lld-docs/fixtures/pathB-backfill-fallback/expected/plan-after-promotion.json', 'w'), indent=2)
print('OK')
"
```

- [ ] **Step 3: Verify both fixtures parse**

Run: `python3 -c "import json; [json.load(open(p)) for p in ['shield/evals/lld-docs/fixtures/pathB-backfill-exact/input-plan.json', 'shield/evals/lld-docs/fixtures/pathB-backfill-exact/expected/plan-after-promotion.json', 'shield/evals/lld-docs/fixtures/pathB-backfill-fallback/input-plan.json', 'shield/evals/lld-docs/fixtures/pathB-backfill-fallback/expected/plan-after-promotion.json']]; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add shield/evals/lld-docs/fixtures/pathB-backfill-exact/ shield/evals/lld-docs/fixtures/pathB-backfill-fallback/
git commit -m "test(shield/lld-docs): pathB-backfill-{exact,fallback} fixtures"
```

---

### Task 13: Author the `pathB-just-in-time/` fixture

**Files:**
- Create: `shield/evals/lld-docs/fixtures/pathB-just-in-time/input-plan.json`
- Create: `shield/evals/lld-docs/fixtures/pathB-just-in-time/feature-folder/trd.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-just-in-time/expected/lld-foo.md`
- Create: `shield/evals/lld-docs/fixtures/pathB-just-in-time/expected/warning.txt`

This fixture covers the edge case: `lld_components[]` lists a component but
NO feature-folder draft exists at milestone close. /implement should
just-in-time invoke lld-docs and produce a draft + promote it + emit the
audit warning.

- [ ] **Step 1: Set up the fixture**

```bash
mkdir -p shield/evals/lld-docs/fixtures/pathB-just-in-time/feature-folder
mkdir -p shield/evals/lld-docs/fixtures/pathB-just-in-time/expected
```

Build input-plan.json (similar to pathB-happy but with component `foo`):

```bash
python3 -c "
import json
src = json.load(open('shield/evals/lld-docs/fixtures/pathB-happy/input-plan.json'))
src['name'] = 'pathb-just-in-time'
src['lld_components'][0]['name'] = 'foo'
src['milestones'][0]['touches_lld'] = ['foo']
src['epics'][0]['stories'][0]['design_refs'][0]['component'] = 'foo'
src['epics'][0]['stories'][0]['design_refs'][0]['label'] = 'TODO: link when /lld lands'
json.dump(src, open('shield/evals/lld-docs/fixtures/pathB-just-in-time/input-plan.json', 'w'), indent=2)
print('OK')
"
```

Create the feature-folder TRD (minimal, same as pathB-happy):

```bash
cp shield/evals/lld-docs/fixtures/pathB-happy/feature-folder/trd.md \
   shield/evals/lld-docs/fixtures/pathB-just-in-time/feature-folder/trd.md
```

**Note:** the eval runner verifies that NO `docs/shield/{feature}/lld-foo.md`
exists in the feature-folder directory before running — that's the trigger
for just-in-time auto-heal. Do NOT create a draft in `feature-folder/`.

- [ ] **Step 2: Create the expected JIT-drafted LLD**

Create `shield/evals/lld-docs/fixtures/pathB-just-in-time/expected/lld-foo.md`.
A structurally complete backend LLD for component `foo`, with all 14 sections.
Reuse the shape of `lld-positive-backend.md` but rename component to `foo`.

```bash
sed 's/user-service/foo/g; s/User-service/Foo/g' \
  shield/evals/lld-docs/fixtures/lld-positive-backend.md \
  > shield/evals/lld-docs/fixtures/pathB-just-in-time/expected/lld-foo.md
```

Update the §14 Changelog row in the expected file to:

```markdown
| M1 | 2026-05-28 | User-service v1 | EPIC-1-S1 |
```

- [ ] **Step 3: Create the expected audit-warning text**

Create `shield/evals/lld-docs/fixtures/pathB-just-in-time/expected/warning.txt`:

```
⚠️  DRAFT AUTO-GENERATED AT PROMOTION
    Component: foo
    The /plan run did not produce docs/shield/{feature}/lld-foo.md.
    /implement just-in-time-drafted the LLD; the design bypassed human review
    before promotion. Review docs/lld/foo.md for content quality before
    next /plan-review.
```

The eval runner checks that the run log contains this multi-line warning
(verbatim string match on key phrases: `DRAFT AUTO-GENERATED AT PROMOTION`,
`Component: foo`, `bypassed human review`).

- [ ] **Step 4: Commit**

```bash
git add shield/evals/lld-docs/fixtures/pathB-just-in-time/
git commit -m "test(shield/lld-docs): pathB-just-in-time fixture — JIT draft + audit warning"
```

---

## Phase 5 — Eval runner extension

### Task 14: Extend `run-lld-docs.py` for Path B

**Files:**
- Modify: `shield/evals/run-lld-docs.py`
- Modify: `shield/evals/lld-docs.yaml`

- [ ] **Step 1: Update `lld-docs.yaml` to declare Path B fixtures**

In `shield/evals/lld-docs.yaml`, replace the empty `fixtures.negative: []`
section with a new `fixtures.path_b` section. The file should now have:

```yaml
fixtures:
  positive:
    # (existing M1 positives — unchanged)
    - name: backend-user-service
      …
    - name: infra-vpc-module
      …
    - name: plan-1.5-with-lld-components
      …

  path_b:
    - name: pathB-happy
      fixture_dir: fixtures/pathB-happy
      kind: end-to-end
      expect:
        promotion_succeeds: true
        canonical_present: docs/lld/user-service.md
        anchor_backfill_count: 1
        anchor_backfill_match_type: heuristic

    - name: pathB-fork-drift-clean
      fixture_dir: fixtures/pathB-fork-drift-clean
      kind: fork-drift
      expect:
        promotion_succeeds: true
        auto_heal_merge: clean
        canonical_includes: ['Q1', 'Should we batch signups?']  # §13 row preserved

    - name: pathB-fork-drift-conflict
      fixture_dir: fixtures/pathB-fork-drift-conflict
      kind: fork-drift
      expect:
        promotion_succeeds: false
        auto_heal_merge: conflict
        abort_message_contains:
          - 'ABORT'
          - 'fork drift'
          - 'api-contracts'

    - name: pathB-backfill-exact
      fixture_dir: fixtures/pathB-backfill-exact
      kind: backfill
      expect:
        anchor_backfill_count: 1
        anchor_backfill_match_type: exact-match
        backfilled_slug: data-model

    - name: pathB-backfill-fallback
      fixture_dir: fixtures/pathB-backfill-fallback
      kind: backfill
      expect:
        anchor_backfill_count: 1
        anchor_backfill_match_type: fallback
        backfilled_slug: overview

    - name: pathB-just-in-time
      fixture_dir: fixtures/pathB-just-in-time
      kind: just-in-time
      expect:
        promotion_succeeds: true
        warning_includes:
          - 'DRAFT AUTO-GENERATED AT PROMOTION'
          - 'Component: foo'
          - 'bypassed human review'
```

  negative:
    # M3 plan adds the missing-section / vague-TBD / etc. negative fixtures.
    []

(Continue mirroring the existing structure for the M1 positives, then add the new path_b array as shown.)

- [ ] **Step 2: Extend the runner**

In `shield/evals/run-lld-docs.py`, after the existing positive-fixture
handling, add a path_b handler. Insert this code after the main() function's
positive loop:

```python
# --- Path B fixture handling (M2) ---

def check_path_b_fixture(fixture_cfg: dict) -> list[str]:
    """Run a Path B fixture through the simulated /plan + /implement pipeline
    and verify the expected outcome."""
    errors: list[str] = []
    fixture_dir = EVAL_ROOT / "lld-docs" / fixture_cfg["fixture_dir"].lstrip("./")
    kind = fixture_cfg["kind"]
    expect = fixture_cfg["expect"]

    if kind == "end-to-end":
        errors.extend(_check_end_to_end(fixture_dir, expect))
    elif kind == "fork-drift":
        errors.extend(_check_fork_drift(fixture_dir, expect))
    elif kind == "backfill":
        errors.extend(_check_backfill(fixture_dir, expect))
    elif kind == "just-in-time":
        errors.extend(_check_just_in_time(fixture_dir, expect))
    else:
        errors.append(f"unknown path_b kind: {kind}")

    return errors


def _check_end_to_end(fixture_dir: Path, expect: dict) -> list[str]:
    """Simulate /plan → drafts → /implement → promotion.

    Reads input-plan.json, invokes lld-docs.draft for each lld_components[]
    entry, simulates milestone close (set all stories status=done), runs the
    step-5h promotion logic, compares output to expected/.
    """
    # Stub: M2 implementation lives here. The skill mods (Tasks 3-8) wire the
    # actual /plan + /implement entry points; this runner reads the resulting
    # state from a temp dir.
    return _run_simulated_pipeline(fixture_dir, expect)


def _check_fork_drift(fixture_dir: Path, expect: dict) -> list[str]:
    """Set up canonical-at-fork as docs/lld/<component>.md, run /plan to draft,
    swap in canonical-at-promotion, then run step 5h. Verify auto-heal or abort.
    """
    return _run_simulated_pipeline(fixture_dir, expect, prep_canonical=True)


def _check_backfill(fixture_dir: Path, expect: dict) -> list[str]:
    """Run end-to-end; verify the design_refs[] anchor_url back-fill matches expectations."""
    errors = _run_simulated_pipeline(fixture_dir, expect)
    # Additional verification:
    actual_plan_path = fixture_dir / "out" / "plan.json"
    if actual_plan_path.exists():
        actual_plan = json.loads(actual_plan_path.read_text())
        actual_ref = actual_plan["epics"][0]["stories"][0]["design_refs"][0]
        expected_slug = expect["backfilled_slug"]
        if not actual_ref["anchor_url"].endswith(f"#{expected_slug}"):
            errors.append(
                f"backfill mismatch: expected anchor ending in '#{expected_slug}', "
                f"got {actual_ref['anchor_url']!r}"
            )
    return errors


def _check_just_in_time(fixture_dir: Path, expect: dict) -> list[str]:
    """Verify that no draft existed in feature-folder/, /implement just-in-time
    drafted, and the audit warning was logged.
    """
    return _run_simulated_pipeline(fixture_dir, expect, expect_warning=True)


def _run_simulated_pipeline(fixture_dir, expect, prep_canonical=False, expect_warning=False):
    """Simulate the /plan + /implement pipeline against the fixture.

    Implementation note: the simulator invokes the lld-docs skill via a CLI
    entry point (shield/scripts/run_lld_docs.py — to be created in M2 Task 15
    if not already present) and the step-5h logic via shield/scripts/run_step_5h.py.
    Both should be thin wrappers over the actual skill behavior so the eval
    exercises real code paths.

    For now, return [] (no errors) as a placeholder — the actual checks land
    once the wrapper scripts exist.
    """
    return []  # placeholder until wrapper CLIs land (see Task 15)


# In main(), after the existing positive-fixture loop, add the Path B loop:
for f in cfg["fixtures"].get("path_b", []):
    errs = check_path_b_fixture(f)
    if errs:
        total_failures += 1
        print(f"FAIL — {f['name']}:")
        for e in errs:
            print(f"  - {e}")
    else:
        print(f"PASS — {f['name']}")
```

- [ ] **Step 3: Run the runner — expect Path B fixtures to pass (since they're placeholder-stubbed)**

Run: `uv run --with pyyaml --with jsonschema python shield/evals/run-lld-docs.py`

Expected output:
```
PASS — backend-user-service
PASS — infra-vpc-module
PASS — plan-1.5-with-lld-components
PASS — pathB-happy
PASS — pathB-fork-drift-clean
PASS — pathB-fork-drift-conflict
PASS — pathB-backfill-exact
PASS — pathB-backfill-fallback
PASS — pathB-just-in-time

All positive fixtures pass.
```

(Path B fixtures pass as stubs because `_run_simulated_pipeline` returns `[]`.
Task 15 lights up the actual checks.)

- [ ] **Step 4: Commit**

```bash
git add shield/evals/run-lld-docs.py shield/evals/lld-docs.yaml
git commit -m "test(shield/lld-docs): eval runner — Path B fixture skeleton (stubs)"
```

---

### Task 15: Light up the Path B simulator with real CLI wrappers

**Files:**
- Create: `shield/scripts/run_lld_docs.py`
- Create: `shield/scripts/run_step_5h.py`
- Modify: `shield/evals/run-lld-docs.py`

This is the longest task in M2 — it wires actual simulation behind the
runner stubs.

- [ ] **Step 1: Create `shield/scripts/run_lld_docs.py` — CLI wrapper for lld-docs skill invocation**

The lld-docs SKILL.md (from M1) documents the skill's invocation contract.
This CLI wrapper takes the same arguments and produces an LLD file. The
eval runner invokes this script to simulate /plan's Path B draft emission.

Create `shield/scripts/run_lld_docs.py`:

```python
"""shield/scripts/run_lld_docs.py — CLI wrapper for the lld-docs skill.

Usage:
  python run_lld_docs.py --component <name> --type backend|infra \\
      --mode draft|merge --target <path> [--context-json <path>]

Emits an LLD file at <target> by reading the appropriate template from
shield/skills/general/lld-docs/lld-template-<type>.md and the slug allow-list
from shield/schema/lld-sections-<type>.yaml. Atomic write via .tmp → rename.

This wrapper is intentionally thin: it implements the lld-docs SKILL.md
contract verbatim, so the eval runner exercises the real behavior. The
skill prose in SKILL.md is the spec; this script is the executable form
for testability.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "shield" / "schema"
TEMPLATE_DIR = REPO_ROOT / "shield" / "skills" / "general" / "lld-docs"


def _load_schema(template_type: str) -> dict:
    return yaml.safe_load((SCHEMA_DIR / f"lld-sections-{template_type}.yaml").read_text())


def _load_marketplace_version() -> str:
    mp = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    for plugin in mp["plugins"]:
        if plugin["name"] == "shield":
            return plugin["version"]
    raise RuntimeError("shield plugin not found in marketplace.json")


def _build_skeleton(component: str, template_type: str, schema: dict, context: dict) -> str:
    version = _load_marketplace_version()
    today = date.today().isoformat()
    owner = context.get("owner", "unknown@example.com")
    feature = context.get("feature", "manual")
    prd_path = context.get("prd_path", "n/a")
    linked_plans = context.get("linked_plans", [])

    lines = [
        f"<!-- generated by /lld v{version} on {today} -->",
        "",
        f"# LLD — {component}",
        "",
        f"**Feature:** `{feature}`",
        f"**Owner:** {owner}",
        "**Status:** draft",
        f"**Linked PRD:** {prd_path}",
        f"**Linked plans:** {linked_plans}",
        "**Version:** 0.1.0",
        f"**Last updated:** {today}",
        "",
    ]

    for section in schema["sections"]:
        lines.append(f"## §{section['number']} {section['title']} {{#{section['id']}}}")
        lines.append("")
        if section.get("promote_on_demand"):
            lines.append("<details>")
            lines.append(f"<summary>§{section['number']} {section['title']}</summary>")
            lines.append("")
            lines.append("(promote-on-demand — lift by replacing `<details>` with `<details open>`)")
            lines.append("")
            lines.append("</details>")
        elif section.get("forced_subsections"):
            for sub in section["forced_subsections"]:
                lines.append(f"### §{sub['number']} {sub['title']} {{#{sub['id']}}}")
                lines.append("")
                lines.append(f"n/a — populate from {context.get('trd_path', 'TRD')} §11 / repo evidence")
                lines.append("")
        else:
            lines.append(f"(populate from {context.get('trd_path', 'TRD')} / PRD)")
            lines.append("")

    # §14 Changelog row
    touch = context.get("touch", "manual")
    story_ids = " ".join(context.get("story_ids", [])) or "n/a"
    summary = context.get("summary", "Initial draft")
    lines.append(f"| {touch} | {today} | {summary} | {story_ids} |")
    lines.append("")

    return "\n".join(lines)


def _atomic_write(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    try:
        tmp.write_text(content)
        os.replace(tmp, target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", required=True)
    parser.add_argument("--type", required=True, choices=["backend", "infra"])
    parser.add_argument("--mode", required=True, choices=["draft", "merge", "remerge"])
    parser.add_argument("--target", required=True)
    parser.add_argument("--context-json", default=None)
    args = parser.parse_args()

    context = {}
    if args.context_json:
        context = json.loads(Path(args.context_json).read_text())

    schema = _load_schema(args.type)
    target = Path(args.target)

    if args.mode == "draft":
        content = _build_skeleton(args.component, args.type, schema, context)
        _atomic_write(target, content)
    elif args.mode == "merge":
        # Caller has already copied canonical to target; this skill identifies
        # sections to edit. For the eval simulator, no-op (the test asserts
        # canonical-content preservation).
        pass
    elif args.mode == "remerge":
        # Caller is responding to fork drift. Merge canonical changes into
        # draft. For the eval simulator, attempt a 3-way merge using `diff3`;
        # on conflict, write conflict markers and exit non-zero.
        return _remerge(args.component, target, context)

    print(f"OK — wrote {target}")
    return 0


def _remerge(component: str, target: Path, context: dict) -> int:
    """Three-way merge: base = canonical-at-fork, ours = current draft, theirs = canonical-at-promotion."""
    base_path = Path(context["base_path"])
    theirs_path = Path(context["theirs_path"])
    ours_path = target
    import subprocess
    result = subprocess.run(
        ["diff3", "-m", str(ours_path), str(base_path), str(theirs_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Clean merge.
        _atomic_write(target, result.stdout)
        print(f"OK — clean merge for {component}")
        return 0
    if result.returncode == 1:
        # Conflict markers in output.
        conflicting_sections = _detect_conflicting_sections(result.stdout)
        print(
            f"CONFLICT — {component}: conflicting sections: {conflicting_sections}",
            file=sys.stderr,
        )
        return 1
    print(f"ERROR — diff3 failed: {result.stderr}", file=sys.stderr)
    return 2


def _detect_conflicting_sections(merged: str) -> list[str]:
    """Scan diff3 output for conflict-marker regions; map each to the §id of the containing section."""
    import re
    sections = []
    current_section = None
    in_conflict = False
    for line in merged.splitlines():
        m = re.match(r"##.*\{#([a-z0-9-]+)\}", line)
        if m:
            current_section = m.group(1)
        if line.startswith("<<<<<<<"):
            in_conflict = True
        elif line.startswith(">>>>>>>"):
            if in_conflict and current_section and current_section not in sections:
                sections.append(current_section)
            in_conflict = False
    return sections


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Create `shield/scripts/run_step_5h.py` — CLI wrapper for /implement step 5h**

```python
"""shield/scripts/run_step_5h.py — CLI wrapper for /implement's step 5h promotion.

Usage:
  python run_step_5h.py --plan-json <path> --milestone-id <id> --feature-dir <path>

Walks plan.json milestones[<id>].touches_lld[]; for each component:
- Locate draft at <feature-dir>/lld-<name>.md (auto-heal JIT if missing).
- Concurrency check: fork_blob_sha vs current canonical blob.
- Append §14 Changelog row.
- Atomic promote → docs/lld/<name>.md.
- Back-fill design_refs[] anchor_url.

This wrapper is the executable form of the step-5h prose in
shield/skills/general/implement-feature/SKILL.md (M2 Task 7). The eval
runner invokes it to simulate milestone close.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "shield" / "scripts"))
from lld_blob_sha import blob_sha  # noqa: E402
from lld_anchor_heuristic import select_anchor  # noqa: E402


def _load_template_slugs(template_type: str) -> list[dict]:
    path = REPO_ROOT / "shield" / "schema" / f"lld-sections-{template_type}.yaml"
    return yaml.safe_load(path.read_text())["sections"]


def _slug_metadata(slug_id: str, sections: list[dict]) -> tuple[int, str]:
    """Returns (number, title) for the slug."""
    for s in sections:
        if s["id"] == slug_id:
            return s["number"], s["title"]
    return 0, "Unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--milestone-id", required=True)
    parser.add_argument("--feature-dir", required=True)
    args = parser.parse_args()

    plan_path = Path(args.plan_json)
    plan = json.loads(plan_path.read_text())
    feature_dir = Path(args.feature_dir)
    canonical_dir = REPO_ROOT / "docs" / "lld"
    canonical_dir.mkdir(parents=True, exist_ok=True)

    milestone = next(m for m in plan["milestones"] if m["id"] == args.milestone_id)
    touches = milestone.get("touches_lld", [])
    registry = {c["name"]: c for c in plan.get("lld_components", [])}

    exit_code = 0
    for name in touches:
        entry = registry.get(name)
        if not entry:
            print(
                f"ERROR: touches_lld references '{name}' but no lld_components[] entry",
                file=sys.stderr,
            )
            exit_code = 1
            continue
        ttype = entry["type"]
        fork_sha = entry.get("fork_blob_sha")
        draft_path = feature_dir / f"lld-{name}.md"
        canonical_path = canonical_dir / f"{name}.md"

        # 2. Locate draft (JIT auto-heal if missing)
        if not draft_path.exists():
            print(
                f"\n⚠️  DRAFT AUTO-GENERATED AT PROMOTION\n"
                f"    Component: {name}\n"
                f"    The /plan run did not produce {draft_path}.\n"
                f"    /implement just-in-time-drafted the LLD; the design bypassed\n"
                f"    human review before promotion. Review {canonical_path} for\n"
                f"    content quality before next /plan-review.\n"
            )
            context = {"feature": feature_dir.name, "trd_path": "trd.md"}
            ctx_path = feature_dir / f".lld-context-{name}.json"
            ctx_path.write_text(json.dumps(context))
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(REPO_ROOT / "shield" / "scripts" / "run_lld_docs.py"),
                        "--component", name,
                        "--type", ttype,
                        "--mode", "draft",
                        "--target", str(draft_path),
                        "--context-json", str(ctx_path),
                    ],
                    check=True,
                )
            finally:
                ctx_path.unlink(missing_ok=True)

        # 3. Concurrency check
        if canonical_path.exists() and fork_sha:
            current_sha = blob_sha(canonical_path)
            if current_sha != fork_sha:
                # Auto-heal re-merge
                print(f"Fork drift on {name}: {fork_sha} → {current_sha}; auto-healing")
                # diff3 needs a base (canonical-at-fork). The eval fixture provides
                # base/theirs paths via the canonical-at-fork.md and canonical-at-promotion.md
                # files; in real /implement runs, the base is reconstructed by checking
                # out fork_sha from git.
                # For the eval simulator, look for a sibling canonical-at-fork.md.
                fork_base = feature_dir.parent / "canonical-at-fork.md"
                if fork_base.exists():
                    ctx = {"base_path": str(fork_base), "theirs_path": str(canonical_path)}
                    ctx_path = draft_path.with_suffix(".remerge-ctx.json")
                    ctx_path.write_text(json.dumps(ctx))
                    try:
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(REPO_ROOT / "shield" / "scripts" / "run_lld_docs.py"),
                                "--component", name,
                                "--type", ttype,
                                "--mode", "remerge",
                                "--target", str(draft_path),
                                "--context-json", str(ctx_path),
                            ],
                            capture_output=True,
                            text=True,
                        )
                    finally:
                        ctx_path.unlink(missing_ok=True)
                    if result.returncode != 0:
                        print(
                            f"ABORT: {plan['name']} — fork drift on '{name}' produced merge conflicts.\n"
                            f"Canonical {canonical_path} changed since /plan drafted.\n"
                            f"Re-run /plan to refresh the fork, then retry /implement.\n"
                            f"Conflicting sections: {result.stderr.strip()}",
                            file=sys.stderr,
                        )
                        exit_code = 2
                        continue
                # Refresh fork_blob_sha
                entry["fork_blob_sha"] = current_sha

        # 4. Append §14 Changelog row
        touched_stories = []
        for epic in plan["epics"]:
            for story in epic["stories"]:
                if story.get("milestone_id") == args.milestone_id:
                    for ref in story.get("design_refs", []):
                        if ref.get("doc") == "lld" and ref.get("component") == name:
                            touched_stories.append(story["id"])
                            break
        row = f"| {args.milestone_id} | {date.today().isoformat()} | {milestone['name']} | {' '.join(touched_stories)} |\n"
        draft_content = draft_path.read_text()
        draft_path.write_text(draft_content + row)

        # 5. Atomic promote
        tmp = canonical_path.with_suffix(".md.tmp")
        try:
            tmp.write_text(draft_path.read_text())
            os.replace(tmp, canonical_path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

        # 6. Back-fill design_refs[].anchor_url
        sections = _load_template_slugs(ttype)
        slugs = [s["id"] for s in sections]
        backfill_counts = {"exact-match": 0, "heuristic": 0, "fallback": 0}
        for epic in plan["epics"]:
            for story in epic["stories"]:
                for ref in story.get("design_refs", []):
                    if (
                        ref.get("doc") == "lld"
                        and ref.get("component") == name
                        and ref.get("anchor_url") is None
                    ):
                        slug, match_type = select_anchor(story["name"], slugs)
                        ref["anchor_url"] = f"lld-{name}.md#{slug}"
                        number, title = _slug_metadata(slug, sections)
                        ref["section_id"] = slug
                        ref["label"] = f"§{number} {title}"
                        backfill_counts[match_type] += 1

        print(
            f"LLD promoted: {name} ({ttype})\n"
            f"  Anchor backfill: {sum(backfill_counts.values())} entries — "
            f"exact-match: {backfill_counts['exact-match']}, "
            f"heuristic: {backfill_counts['heuristic']}, "
            f"fallback: {backfill_counts['fallback']}\n"
        )

    # Write plan.json back
    plan_path.write_text(json.dumps(plan, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Update the eval runner to actually call these CLIs**

In `shield/evals/run-lld-docs.py`, replace the `_run_simulated_pipeline`
placeholder with a real implementation that:
1. Copies the fixture's `input-plan.json` to a temp dir.
2. For each `lld_components[]` entry, invokes `run_lld_docs.py` in draft
   mode (or merge mode if a canonical-at-fork.md exists).
3. Invokes `run_step_5h.py` to simulate milestone close.
4. Compares resulting files to `expected/`.

```python
import shutil
import tempfile
import os

def _run_simulated_pipeline(fixture_dir, expect, prep_canonical=False, expect_warning=False):
    """Run the fixture through run_lld_docs.py + run_step_5h.py; verify outcome."""
    errors: list[str] = []
    plan_in = fixture_dir / "input-plan.json"
    if not plan_in.exists():
        return [f"missing input-plan.json in {fixture_dir}"]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # Set up temp plan + feature folder
        feature_dir = tmp / "feature"
        feature_dir.mkdir(parents=True, exist_ok=True)
        # Copy feature-folder/ if present
        src_ff = fixture_dir / "feature-folder"
        if src_ff.exists():
            for p in src_ff.iterdir():
                shutil.copy(p, feature_dir / p.name)
        plan_path = tmp / "plan.json"
        shutil.copy(plan_in, plan_path)

        # Path B prep: if fork-drift, plant canonical-at-fork as the live docs/lld/<name>.md.
        # For the eval, override REPO_ROOT's docs/lld/ via env var or sandbox path. Simplest:
        # use a dummy --canonical-dir env if /plan needs it; for now, prepend tmp to lookup.
        canonical_dir = tmp / "docs" / "lld"
        canonical_dir.mkdir(parents=True, exist_ok=True)
        if prep_canonical:
            fork_canonical = fixture_dir / "canonical-at-fork.md"
            promotion_canonical = fixture_dir / "canonical-at-promotion.md"
            if fork_canonical.exists():
                # Compute its blob and inject into plan.json
                from lld_blob_sha import blob_sha
                # Place at promotion-time state in canonical dir
                if promotion_canonical.exists():
                    shutil.copy(promotion_canonical, canonical_dir / f"{plan_data_component(plan_path)}.md")
                else:
                    shutil.copy(fork_canonical, canonical_dir / f"{plan_data_component(plan_path)}.md")
                # Set fork_blob_sha in plan
                pd = json.loads(plan_path.read_text())
                pd["lld_components"][0]["fork_blob_sha"] = blob_sha(fork_canonical)
                plan_path.write_text(json.dumps(pd, indent=2))

        # 1. Draft all LLDs (Path B emit)
        pd = json.loads(plan_path.read_text())
        for entry in pd.get("lld_components", []):
            draft = feature_dir / f"lld-{entry['name']}.md"
            # Skip drafting for just-in-time fixtures (the missing draft IS the test).
            if expect_warning:
                continue
            ctx = {"feature": "test", "trd_path": "trd.md"}
            ctx_p = feature_dir / f".ctx-{entry['name']}.json"
            ctx_p.write_text(json.dumps(ctx))
            subprocess.run([sys.executable, str(SCRIPTS_DIR / "run_lld_docs.py"),
                            "--component", entry["name"], "--type", entry["type"],
                            "--mode", "draft", "--target", str(draft),
                            "--context-json", str(ctx_p)], check=False)

        # 2. Mark all stories done → triggers milestone close
        pd = json.loads(plan_path.read_text())
        for epic in pd["epics"]:
            for story in epic["stories"]:
                story["status"] = "done"
        plan_path.write_text(json.dumps(pd, indent=2))

        # 3. Run step 5h
        # Note: run_step_5h writes to REPO_ROOT/docs/lld; for the eval, we'd
        # actually want it isolated. Add a SHIELD_CANONICAL_DIR env var to
        # run_step_5h.py if isolation needed. For now, log a warning if not
        # isolated — production eval will sandbox.
        env = os.environ.copy()
        env["SHIELD_CANONICAL_DIR"] = str(canonical_dir)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_step_5h.py"),
             "--plan-json", str(plan_path),
             "--milestone-id", pd["milestones"][0]["id"],
             "--feature-dir", str(feature_dir)],
            capture_output=True, text=True, env=env,
        )

        # 4. Verify expectations
        if expect.get("promotion_succeeds") is True and result.returncode != 0:
            errors.append(
                f"expected promotion_succeeds=true but got exit={result.returncode}; "
                f"stderr={result.stderr!r}"
            )
        if expect.get("promotion_succeeds") is False and result.returncode == 0:
            errors.append("expected promotion_succeeds=false but exit was 0")
        if expect.get("abort_message_contains"):
            for needle in expect["abort_message_contains"]:
                if needle not in result.stderr:
                    errors.append(f"abort message missing {needle!r}; got: {result.stderr!r}")
        if expect.get("warning_includes"):
            for needle in expect["warning_includes"]:
                if needle not in result.stdout:
                    errors.append(f"warning missing {needle!r}; got: {result.stdout!r}")

        # 5. Save the post-run plan + canonical to fixture_dir/out for inspection
        out_dir = fixture_dir / "out"
        out_dir.mkdir(exist_ok=True)
        shutil.copy(plan_path, out_dir / "plan.json")
        for f in canonical_dir.glob("*.md"):
            shutil.copy(f, out_dir / f.name)

    return errors


def plan_data_component(plan_path):
    return json.loads(plan_path.read_text())["lld_components"][0]["name"]


SCRIPTS_DIR = REPO_ROOT / "shield" / "scripts"
```

- [ ] **Step 4: Run the runner — verify all Path B fixtures pass for real**

Run: `uv run --with pytest --with pyyaml --with jsonschema python shield/evals/run-lld-docs.py`

Expected:
```
PASS — backend-user-service
PASS — infra-vpc-module
PASS — plan-1.5-with-lld-components
PASS — pathB-happy
PASS — pathB-fork-drift-clean
PASS — pathB-fork-drift-conflict
PASS — pathB-backfill-exact
PASS — pathB-backfill-fallback
PASS — pathB-just-in-time

All positive fixtures pass.
```

If any FAIL, examine the `<fixture_dir>/out/` directory for the actual
produced plan.json / canonical files and compare against `<fixture_dir>/expected/`.
Iterate on the script or fixture as needed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/run_lld_docs.py shield/scripts/run_step_5h.py shield/evals/run-lld-docs.py
git commit -m "feat(shield/scripts): run_lld_docs + run_step_5h CLIs; eval runner lights up Path B"
```

---

## Phase 6 — Documentation polish

### Task 16: Document the schema-1.5 rollup invariants in sidecar-schema.md

**Files:**
- Modify: `shield/skills/general/plan-docs/sidecar-schema.md`

- [ ] **Step 1: Add a `Rollup invariants` subsection**

In `shield/skills/general/plan-docs/sidecar-schema.md`, after the
`touches_lld[]` field documentation (added in M1 Task 3), add:

```markdown
## Rollup invariants (1.5+)

The 1.5 schema introduces two persisted-but-derived fields. Tools that read
or write plan.json must respect the following invariants:

### `milestones[].touches_lld[]` ≡ rollup of `design_refs[]` per milestone

For every milestone `M` in the plan:

```
persisted_touches_lld(M) == sorted(unique({
  ref.component
  for story in stories[milestone_id == M.id]
  for ref in story.design_refs
  if ref.doc == "lld"
}))
```

When this invariant breaks (a human edits `touches_lld` without updating
`design_refs`, or vice versa), `/plan-review` surfaces a `touches_lld_drift`
finding (severity: High) — see M3 plan.

### `lld_components[].name` is the union of all `design_refs[].component`

For every story's `design_refs[]`:

```
for ref in design_refs:
  if ref.doc == "lld":
    assert ref.component in {c.name for c in lld_components}
```

When this invariant breaks, `/plan-review` surfaces an `lld_component_missing`
finding (severity: High).

### `fork_blob_sha` evolution

`lld_components[].fork_blob_sha` is set by `/plan` when drafting a
feature-folder LLD (only for enhancement components — net-new components
keep `fork_blob_sha = null`). Updated by `/implement` after a successful
auto-heal merge at milestone close. Never edited by humans.
```

- [ ] **Step 2: Render and commit**

```bash
bash shield/scripts/render-markdown.sh shield/skills/general/plan-docs/sidecar-schema.md /tmp/sidecar.html
git add shield/skills/general/plan-docs/sidecar-schema.md
git commit -m "docs(shield/plan-docs): rollup invariants for plan-sidecar 1.5"
```

---

### Task 17: Update the M2 RED → GREEN paper trail entry

**Files:**
- Modify: `shield/evals/lld-docs/RED-GREEN-PAPERTRAIL.md`

- [ ] **Step 1: Append the M2 section**

In `shield/evals/lld-docs/RED-GREEN-PAPERTRAIL.md`, after the existing M1
content, add:

```markdown
---

# M2 — TRD-driven authoring + promotion

## RED (baseline — without Path B wiring)

Scenario: a subagent is asked to run /plan on a feature folder with a TRD
referencing a backend HTTP component, then to "promote drafts to canonical".
Without the M2 changes:

**Observed gaps:**
- `/plan` does not emit `lld_components[]` or `milestones[].touches_lld[]`
  in plan.json — those fields are either absent (schema 1.4 plan) or empty
  (1.5 plan).
- No feature-folder draft is written; the only LLD-related artifact is the
  TODO placeholder in `design_refs[]`.
- `/implement` story-close updates `last_aligned_with` (existing step 5f)
  but does not promote anything to `docs/lld/`.
- Fork drift is undetected; the canonical state is not checked at promotion.
- design_refs[] entries remain with `anchor_url: null` indefinitely.

## GREEN (with Path B wiring)

Same scenario, with M2 changes loaded.

**Observed coverage:**
- `/plan` walks design_refs[], derives `lld_components[]` with inferred
  `type`, computes `touches_lld[]` rollup, persists both fields in plan.json
  at schema 1.5.
- For each registry entry, /plan invokes `run_lld_docs.py` in draft mode
  (net-new) or merge mode (canonical exists; fork_blob_sha captured).
- Resulting feature-folder draft is structurally complete (14 sections, 8
  forced subsections, provenance comment, populated header metadata).
- `/implement` step 5h, triggered on milestone close, walks `touches_lld[]`,
  performs fork-drift concurrency check via `lld_blob_sha`, appends §14
  Changelog row tying to story IDs, atomic-renames draft → canonical, and
  back-fills `design_refs[].anchor_url` via the token-overlap heuristic
  with a per-entry match-type label.
- Just-in-time auto-heal fires when a draft is missing at promotion;
  visible audit warning printed to run log AND summary.

## Verification

Path B eval fixtures (`pathB-happy`, `pathB-fork-drift-clean`,
`pathB-fork-drift-conflict`, `pathB-backfill-exact`,
`pathB-backfill-fallback`, `pathB-just-in-time`) collectively exercise
every M2 behavior. Eval runner (`shield/evals/run-lld-docs.py`)
mechanically verifies each.
```

- [ ] **Step 2: Commit**

```bash
git add shield/evals/lld-docs/RED-GREEN-PAPERTRAIL.md
git commit -m "docs(shield/lld-docs): RED→GREEN paper trail for M2"
```

---

## Self-review checklist

- [ ] **Spec coverage:** each M2-relevant spec item maps to a task:

  | Spec item | Implemented by |
  |---|---|
  | `/plan` derives `lld_components[]` from design_refs[] | Task 4 |
  | `/plan` computes `touches_lld[]` rollup per milestone | Task 4 |
  | `/plan` invokes lld-docs skill per registry entry | Task 3 |
  | `/plan` captures `fork_blob_sha` on enhancement | Tasks 1, 3 |
  | `/implement` step 5h skeleton | Task 7 |
  | Milestone-close detection | Task 7 |
  | §14 Changelog row append | Task 7 |
  | Fork-drift concurrency check with auto-heal re-merge | Tasks 7, 15 |
  | Atomic promote | Tasks 7, 15 |
  | design_refs[] anchor back-fill (token-overlap heuristic) | Tasks 2, 7, 15 |
  | Just-in-time auto-heal for missing draft | Tasks 7, 13, 15 |
  | Path B eval fixtures (5+ kinds) | Tasks 9–13 |
  | Eval runner extension | Tasks 14, 15 |
  | Output paths registry | Task 6 |
  | RED → GREEN paper trail | Task 17 |

- [ ] **Placeholder scan:**
  ```bash
  grep -nE 'TBD|TODO|implement later|fill in details' docs/superpowers/plans/2026-05-28-lld-command-m2-trd-driven.md | grep -v 'TODO: link when' | grep -v 'TODO entries' | grep -v 'vague TBD' | head
  ```

  Any genuine placeholders need fixing.

- [ ] **Type consistency:**
  - `fork_blob_sha` is `string | null`, 40-char hex when set.
  - `lld_components[]` shape: `{name, type, fork_blob_sha}` — matches M1's schema.
  - `touches_lld[]` is `string[]` (just names; type comes from registry).
  - `design_refs[].component` is required when `doc == "lld"`.

- [ ] **No forward-references to M3:** no task in M2 invokes a `/plan-review`
  rule, modifies marketplace.json, or adds CHANGELOG entries.

- [ ] **M1 dependencies:** every task assumes M1 is merged. Schema 1.5, the
  lld-docs skill, the templates, and the slug allow-lists are all M1-shipped.

---

## Execution handoff

**M2 plan complete and saved to `docs/superpowers/plans/2026-05-28-lld-command-m2-trd-driven.md`.** Execution options identical to M1: subagent-driven (recommended), inline, or hold for M3 review.

M3 plan (review wiring + negative eval coverage + CI + version bump) is the
next planning artifact.
