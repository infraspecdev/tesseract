# Shield Single Canonical Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Markdown the single committed Shield output and demote HTML to a locally-built, gitignored artifact regenerated on demand by one build script.

**Architecture:** Reuse the existing renderers. First make the existing `rerender_all.py` *complete* so it regenerates every HTML we currently commit (main docs, review summaries, **and** the `enhanced-*` / `detailed/*` reviewer docs it currently skips). Add a thin `render-output.sh` that runs `rerender_all.py` (pages) then `write_shield_assets.py` (dashboard + assets). Add a `/shield render` command that just triggers the script. Then `.gitignore` all generated HTML/site assets and `git rm --cached` the 41 already-tracked HTML files + root assets. Finally update path-registry/CLAUDE.md prose to call HTML a build artifact.

**Tech Stack:** Bash + Python 3 (stdlib only for orchestration), `uv` for the markdown-it render dependency, `pytest` for evals. All under `shield/scripts/`.

---

## Spec

Design doc: `docs/superpowers/specs/2026-06-08-shield-single-canonical-output-design.md`

## File Structure

**Modify:**
- `shield/scripts/rerender_all.py` — extend `rerender_all()` to also render `enhanced-*.md` and `detailed/*.md` review sources. Stays page-rendering only (single responsibility).
- `.gitignore` — add rules for generated HTML + root site assets.
- `shield/schema/output-paths.yaml` — header note: `*_html` paths are local build artifacts.
- `CLAUDE.md` — the artifact-output note (currently says "Rendered HTML lands under …") gains "(build artifact — gitignored; run `/shield render`)".

**Create:**
- `shield/scripts/render-output.sh` — the build script (orchestrator): `rerender_all.py` + `write_shield_assets.py`.
- `shield/commands/render.md` — `/shield render` command (thin trigger).
- `shield/scripts/test_rerender_all.py` — eval: completeness of rendered set.
- `shield/scripts/test_render_output.py` — eval: end-to-end build produces pages **and** assets.
- `shield/scripts/test_gitignore_html_artifacts.py` — eval: `.gitignore` covers the generated artifacts.

**Remove from git (keep on disk):**
- 41 tracked `*.html` under `docs/shield/**/outputs/`, plus `docs/shield/index.html` and `docs/shield/manifest.js`.

---

## Task 1: Make `rerender_all.py` render the complete HTML set

Today `rerender_all.py` renders the five main docs + `reviews/*/*/summary.md` only. It silently skips `enhanced-*.md` and `detailed/*.md`, which ARE committed as HTML today. Fix that so nothing is lost when we stop committing HTML.

**Files:**
- Create: `shield/scripts/test_rerender_all.py`
- Modify: `shield/scripts/rerender_all.py` (the `rerender_all` function body, after the existing `summary.md` loop)

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_rerender_all.py`:

```python
"""Eval for rerender_all.py — renders the COMPLETE committed HTML set,
including enhanced-* and detailed/* review docs (regression: those were skipped)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

SPEC = Path(__file__).resolve().parent / "rerender_all.py"
_spec = importlib.util.spec_from_file_location("rerender_all", SPEC)
ra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ra)


def _fixture(root: Path) -> None:
    """A feature with a main doc + a plan review that has summary, enhanced, detailed."""
    feat = root / "feat-x"
    (feat).mkdir(parents=True)
    (root / "manifest.json").write_text(json.dumps({"schema_version": "2.1", "features": []}))
    (feat / "prd.md").write_text("# PRD\n\nbody\n")
    rev = feat / "reviews" / "plan" / "2026-06-08"
    (rev / "detailed").mkdir(parents=True)
    (rev / "summary.md").write_text("# Summary\n\nbody\n")
    (rev / "enhanced-plan.md").write_text("# Enhanced\n\nbody\n")
    (rev / "detailed" / "agile-coach.md").write_text("# Agile\n\nbody\n")


def test_renders_enhanced_and_detailed(tmp_path):
    _fixture(tmp_path)
    rc = ra.rerender_all(tmp_path)
    assert rc == 0
    out = tmp_path / "feat-x" / "outputs"
    expected = [
        out / "prd.html",
        out / "reviews" / "plan" / "2026-06-08" / "summary.html",
        out / "reviews" / "plan" / "2026-06-08" / "enhanced-plan.html",
        out / "reviews" / "plan" / "2026-06-08" / "detailed" / "agile-coach.html",
    ]
    for p in expected:
        assert p.is_file(), f"missing rendered page: {p}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_rerender_all.py -v`
Expected: FAIL — `enhanced-plan.html` and `detailed/agile-coach.html` are missing (rerender_all skips them today).

- [ ] **Step 3: Add the enhanced + detailed render loops**

In `shield/scripts/rerender_all.py`, inside `rerender_all()`, immediately AFTER this existing block:

```python
        for summary in feature.glob("reviews/*/*/summary.md"):
            rel = summary.relative_to(feature).with_suffix(".html")
            _render(summary, feature / "outputs" / rel,
                    f"Review — {feature.name}", output_dir)
            count += 1
```

add:

```python
        for enhanced in feature.glob("reviews/*/*/enhanced-*.md"):
            rel = enhanced.relative_to(feature).with_suffix(".html")
            _render(enhanced, feature / "outputs" / rel,
                    f"Review — {feature.name}", output_dir)
            count += 1
        for detailed in feature.glob("reviews/*/*/detailed/*.md"):
            rel = detailed.relative_to(feature).with_suffix(".html")
            _render(detailed, feature / "outputs" / rel,
                    f"Review — {feature.name}", output_dir)
            count += 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" pytest test_rerender_all.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/rerender_all.py shield/scripts/test_rerender_all.py
git commit -m "fix(shield): rerender_all renders enhanced-* and detailed/* review docs"
```

---

## Task 2: Create `render-output.sh` build script

The orchestrator the user asked for: renders all pages, then writes the dashboard + shared assets. Idempotent.

**Files:**
- Create: `shield/scripts/render-output.sh`
- Create: `shield/scripts/test_render_output.py`

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_render_output.py`:

```python
"""Eval for render-output.sh — the full build: pages + dashboard assets."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "render-output.sh"


def test_build_produces_pages_and_assets(tmp_path):
    feat = tmp_path / "feat-x"
    feat.mkdir(parents=True)
    (tmp_path / "manifest.json").write_text(
        json.dumps({"schema_version": "2.1", "features": [{"name": "feat-x"}]})
    )
    (feat / "prd.md").write_text("# PRD\n\nbody\n")

    res = subprocess.run([str(SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    # pages
    assert (feat / "outputs" / "prd.html").is_file()
    # dashboard + shared assets
    for asset in ["manifest.js", "index.html", "shield.css",
                  "shield-nav.js", "shield-dashboard.js"]:
        assert (tmp_path / asset).is_file(), f"missing asset {asset}"


def test_missing_dir_errors(tmp_path):
    res = subprocess.run([str(SCRIPT), str(tmp_path / "nope")],
                         capture_output=True, text=True)
    assert res.returncode == 2
    assert "not a dir" in res.stderr
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pytest pytest test_render_output.py -v`
Expected: FAIL — `render-output.sh` does not exist yet.

- [ ] **Step 3: Write the build script**

Create `shield/scripts/render-output.sh`:

```bash
#!/usr/bin/env bash
# Build the full Shield HTML site from committed Markdown.
#
# Step 1: render every source .md to its outputs/*.html (rerender_all.py)
# Step 2: write the dashboard + shared assets (write_shield_assets.py)
#
# HTML is a build artifact: it is gitignored and regenerated on demand.
# Markdown + JSON sidecars are the committed source of truth.
#
# Usage:
#   render-output.sh [OUTPUT_DIR]
#     OUTPUT_DIR defaults to <repo-root>/docs/shield
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OUTPUT_DIR="${1:-}"
if [[ -z "$OUTPUT_DIR" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  OUTPUT_DIR="$ROOT/docs/shield"
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
  echo "render-output: not a dir: $OUTPUT_DIR" >&2
  exit 2
fi

python3 "$SCRIPT_DIR/rerender_all.py" --output-dir "$OUTPUT_DIR"
python3 "$SCRIPT_DIR/write_shield_assets.py" --output-dir "$OUTPUT_DIR"
echo "render-output: site built at $OUTPUT_DIR"
```

- [ ] **Step 4: Make it executable**

Run: `chmod +x shield/scripts/render-output.sh`
Expected: no output (the repo's pre-commit "scripts with shebangs are executable" hook requires this).

- [ ] **Step 5: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pytest pytest test_render_output.py -v`
Expected: PASS (both tests)

- [ ] **Step 6: Commit**

```bash
git add shield/scripts/render-output.sh shield/scripts/test_render_output.py
git commit -m "feat(shield): render-output.sh — one build script for the HTML site"
```

---

## Task 3: Add the `/shield render` command

A thin trigger. No logic — it invokes `render-output.sh`.

**Files:**
- Create: `shield/commands/render.md`

- [ ] **Step 1: Write the command**

Create `shield/commands/render.md` (mirrors the frontmatter style of `shield/commands/analyze-plan.md`):

```markdown
---
name: render
description: Build the browsable Shield HTML site locally from committed Markdown
args: "[output dir — optional, defaults to docs/shield]"
---

# Render Shield Output

Shield commits Markdown + JSON sidecars only. HTML (per-artifact pages and the
browsable dashboard) is a **local build artifact** — gitignored and regenerated
on demand. Run this command to (re)build the site, then open the HTML locally.

## Usage

`/shield render` — rebuild the whole site under `docs/shield/`
`/shield render <output dir>` — rebuild a site rooted at a custom dir

## Behavior

1. Run the build script, which renders every source `.md` to its
   `outputs/*.html` and then writes the dashboard (`index.html`) and shared
   assets (`manifest.js`, CSS, nav JS):

   ```bash
   "$CLAUDE_PLUGIN_ROOT/scripts/render-output.sh" "$ARGUMENTS"
   ```

   (`$ARGUMENTS` is empty for the default `docs/shield/` location.)

2. Report the built site path and remind the user the output is gitignored —
   open `docs/shield/index.html` in a browser to view.

## Important

- This command does NOT author or modify any Markdown — it only renders.
- HTML is never committed; do not `git add` anything under `outputs/` or the
  generated root assets.
```

- [ ] **Step 2: Verify the command file parses (frontmatter present)**

Run: `head -6 shield/commands/render.md`
Expected: shows the `---` frontmatter block with `name: render`.

- [ ] **Step 3: Commit**

```bash
git add shield/commands/render.md
git commit -m "feat(shield): /shield render command triggers render-output.sh"
```

---

## Task 4: Gitignore generated HTML and untrack the committed files

**Files:**
- Modify: `.gitignore`
- Create: `shield/scripts/test_gitignore_html_artifacts.py`
- Remove from index: tracked `*.html` + root assets under `docs/shield/`

- [ ] **Step 1: Write the failing hygiene test**

Create `shield/scripts/test_gitignore_html_artifacts.py`:

```python
"""Eval: .gitignore demotes Shield HTML to a build artifact."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
GITIGNORE = ROOT / ".gitignore"

REQUIRED_PATTERNS = [
    "**/docs/shield/*/outputs/",
    "**/docs/shield/index.html",
    "**/docs/shield/manifest.js",
]


def test_gitignore_has_html_artifact_rules():
    text = GITIGNORE.read_text()
    for pat in REQUIRED_PATTERNS:
        assert pat in text, f".gitignore missing rule: {pat}"


def test_no_shield_html_tracked():
    out = subprocess.run(
        ["git", "ls-files", "docs/shield/**/*.html", "docs/shield/manifest.js"],
        cwd=ROOT, capture_output=True, text=True,
    )
    tracked = [l for l in out.stdout.splitlines() if l.strip()]
    assert tracked == [], f"HTML/assets still tracked: {tracked}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pytest pytest test_gitignore_html_artifacts.py -v`
Expected: FAIL — patterns absent and 41+ HTML files still tracked.

- [ ] **Step 3: Add the `.gitignore` rules**

Append to `.gitignore` (after the existing `**/docs/shield/*/.session-transcript.md` block):

```gitignore
# Shield HTML is a BUILD ARTIFACT, not a source. Markdown + JSON sidecars are
# the committed source of truth. Regenerate the site locally with /shield
# render (scripts/render-output.sh). See docs/superpowers/specs/
# 2026-06-08-shield-single-canonical-output-design.md
**/docs/shield/*/outputs/
**/docs/shield/index.html
**/docs/shield/manifest.js
**/docs/shield/shield.css
**/docs/shield/shield-nav.js
**/docs/shield/shield-dashboard.js
```

- [ ] **Step 4: Untrack the already-committed HTML + root assets (keep on disk)**

Run:

```bash
git ls-files -z \
  'docs/shield/*/outputs/**' \
  'docs/shield/index.html' \
  'docs/shield/manifest.js' \
  'docs/shield/shield.css' \
  'docs/shield/shield-nav.js' \
  'docs/shield/shield-dashboard.js' \
  | xargs -0 --no-run-if-empty git rm --cached --quiet
```

Expected: lists the removed paths (≈41 html + index.html + manifest.js). Files remain on disk; only the index entries are dropped.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pytest pytest test_gitignore_html_artifacts.py -v`
Expected: PASS (both tests)

- [ ] **Step 6: Verify the build still reproduces what was removed**

Run: `shield/scripts/render-output.sh` then `git status --porcelain docs/shield | grep -c '\.html$' || true`
Expected: `0` — regenerated HTML is ignored (not showing as untracked), proving the build replaces the removed committed files.

- [ ] **Step 7: Commit**

```bash
git add .gitignore shield/scripts/test_gitignore_html_artifacts.py
git commit -m "build(shield): gitignore HTML build artifacts; untrack committed HTML"
```

---

## Task 5: Update path-registry + artifact-output prose

Stop describing HTML as a committed deliverable; point readers at `/shield render`. The "Rendered HTML lands under …" phrasing lives in exactly three places (confirmed by grep): `shield/hooks/scripts/session-start.sh`, `shield/docs/artifacts.md`, `shield/skills/general/manifest-schema.md`. The per-skill render steps still run unchanged — they just produce gitignored output.

**Files:**
- Modify: `shield/schema/output-paths.yaml` (top-of-file header comment)
- Modify: `shield/hooks/scripts/session-start.sh`
- Modify: `shield/docs/artifacts.md`
- Modify: `shield/skills/general/manifest-schema.md`

- [ ] **Step 1: Add a header note to `output-paths.yaml`**

At the very top of `shield/schema/output-paths.yaml`, add (above the first existing line):

```yaml
# NOTE: All `*_html` entries below are LOCAL BUILD ARTIFACTS — gitignored and
# regenerated on demand by /shield render (scripts/render-output.sh). The
# committed source of truth is the corresponding Markdown (+ JSON sidecars).
```

- [ ] **Step 2: Inspect the three "Rendered HTML lands under" call-sites**

Run: `grep -n "Rendered HTML lands under" shield/hooks/scripts/session-start.sh shield/docs/artifacts.md shield/skills/general/manifest-schema.md`
Expected: one matching line per file. Read each line's surrounding sentence so the edit in Step 3 matches the exact existing text.

- [ ] **Step 3: Append the build-artifact parenthetical in each of the three files**

In each file, edit the sentence that begins "Rendered HTML lands under `docs/shield/{feature}/outputs/`" so it ends with the parenthetical. The target sentence must read:

```
Rendered HTML lands under `docs/shield/{feature}/outputs/` (build artifact — gitignored; rebuild locally with `/shield render`).
```

(Preserve each file's surrounding punctuation/markup; only insert the ` (build artifact — gitignored; rebuild locally with `/shield render`)` clause before the trailing period.)

- [ ] **Step 4: Grep for any remaining "committed HTML" phrasing**

Run: `grep -rniE "commit.*\.html|html.*deliverable" shield/ || echo "none"`
Expected: `none` (no prose describing HTML as committed).

- [ ] **Step 5: Commit**

```bash
git add shield/schema/output-paths.yaml shield/hooks/scripts/session-start.sh \
        shield/docs/artifacts.md shield/skills/general/manifest-schema.md
git commit -m "docs(shield): describe HTML output as a gitignored build artifact"
```

---

## Task 6: Version bump

Per CLAUDE.md: bump the plugin version in `marketplace.json` for any plugin change. Shield has no root `pyproject.toml` (only `shield/backlog/` and `shield/parsers/` have them, untouched here), so only `marketplace.json` changes.

**Files:**
- Modify: `.claude-plugin/marketplace.json` (shield `version`)

- [ ] **Step 1: Bump shield version**

In `.claude-plugin/marketplace.json`, change the `shield` entry `"version": "2.27.0"` to `"version": "2.28.0"` (minor bump — new command + behavior change).

- [ ] **Step 2: Verify JSON is valid**

Run: `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.28.0 — Markdown-canonical output + /shield render"
```

---

## Final verification (run before opening PR)

- [ ] **Run the full new eval set:**

Run:
```bash
cd shield/scripts && uv run --with pytest --with "markdown-it-py>=3,<4" --with "mdit-py-plugins>=0.4,<1" \
  pytest test_rerender_all.py test_render_output.py test_gitignore_html_artifacts.py -v
```
Expected: all PASS.

- [ ] **Confirm no HTML is tracked and the build regenerates cleanly:**

Run:
```bash
git ls-files 'docs/shield/**/*.html' | wc -l   # expect 0
shield/scripts/render-output.sh
git status --porcelain docs/shield | grep '\.html$' || echo "clean (html ignored)"
```
Expected: `0`, then `clean (html ignored)`.

- [ ] **PR body notes:** the `/shield render` command is a thin trigger fully exercised by `test_render_output.py`; completeness regression covered by `test_rerender_all.py`; repo hygiene by `test_gitignore_html_artifacts.py`. No `pyproject.toml` bump (shield root has none).
