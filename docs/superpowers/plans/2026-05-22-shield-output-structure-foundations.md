# Shield Output Structure — Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational tooling — central path registry, path resolver, lint script, and migration script — that the per-asset cutover (a follow-up plan) will rely on.

**Architecture:** A YAML registry (`shield/schema/output-paths.yaml`) is the single source of truth for every artifact path shield emits. A Python resolver (`shield/scripts/path_resolver.py`) substitutes variables into templates and supports nested template references. A lint script (`shield/scripts/lint_output_paths.py`) validates the registry and any asset frontmatter that references it. A migration script (`shield/scripts/migrate_outputs.py`) maps the existing numbered-run tree to the new flat layout, dry-run by default with `--apply` to execute.

**Tech Stack:** Python 3.11+, `pyyaml` (loaded via `uv run --with pyyaml`), `pytest` (via `uv run --with pytest`). All scripts run under `uv` per repo CLAUDE.md.

**Scope:** Phases 1 + 2 of design spec (`docs/superpowers/specs/2026-05-22-shield-output-structure-design.md`). Phases 3–5 (per-command cutover, live migration, legacy cleanup) are separate plans.

**Out of scope for this plan:**
- Editing any command, skill, or agent file under `shield/commands/`, `shield/skills/`, or `shield/agents/`.
- Running the migration script against the real `docs/shield/` tree.
- Any eval coverage (no plugin assets are being modified — only new scripts added; per repo policy, eval gate kicks in at Phase 3).

---

## File Structure

**New files (created in this plan):**
- `shield/schema/output-paths.yaml` — central path registry (data only).
- `shield/scripts/path_resolver.py` — resolver module (`resolve(name, **vars) -> str`).
- `shield/scripts/test_path_resolver.py` — resolver unit tests.
- `shield/scripts/lint_output_paths.py` — lint script with CLI.
- `shield/scripts/test_lint_output_paths.py` — lint unit tests.
- `shield/scripts/migrate_outputs.py` — migration script with CLI.
- `shield/scripts/test_migrate_outputs.py` — migration unit + fixture tests.

**Modified files:** none.

**Why this split:**
- `output-paths.yaml` is plugin contract — separated from scripts, easy for humans to diff during structure changes.
- `path_resolver.py` is the only file that knows how to read the registry. Both lint and migration scripts depend on it. Centralizing avoids duplicated parsing logic.
- Lint and migration scripts are independent CLIs that share the resolver — kept in separate files so each has a clear single responsibility and can be invoked independently.
- Tests live alongside scripts (`shield/scripts/test_*.py`), matching the existing convention (see `test_detect_stack.py`).

**Deliberate deviation from spec §8.1:** the spec lists `shield/schema/path-resolver.py`, but this plan puts the resolver at `shield/scripts/path_resolver.py`. Reason: `shield/schema/` is data-only (registry YAML); all Python lives in `shield/scripts/` per existing convention, and tests need to import the resolver from a script-adjacent location. The spec's file path is a cosmetic mismatch with the codebase's convention — call it out here so the plan reads cleanly against the spec.

---

## Section A: Path resolver and registry

### Task A1: Resolver — basic variable substitution

**Files:**
- Create: `shield/schema/output-paths.yaml`
- Create: `shield/scripts/path_resolver.py`
- Create: `shield/scripts/test_path_resolver.py`

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_path_resolver.py`:

```python
# shield/scripts/test_path_resolver.py
"""Tests for path_resolver.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from path_resolver import resolve  # type: ignore[import-not-found]


def test_resolve_simple_template() -> None:
    result = resolve("feature_dir", output_dir="docs/shield", feature="vpc-20260522")
    assert result == "docs/shield/vpc-20260522"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py::test_resolve_simple_template -v`
Expected: FAIL — `path_resolver` module does not exist.

- [ ] **Step 3: Create minimal registry**

Create `shield/schema/output-paths.yaml`:

```yaml
# shield/schema/output-paths.yaml
# Plugin-owned contract. Consumers should NOT edit.
# See docs/superpowers/specs/2026-05-22-shield-output-structure-design.md §5.

variables:
  output_dir: "Set by consumer in .shield.json"
  feature:    "Auto-derived from command (e.g. 'vpc-module-20260319')"

paths:
  feature_dir: "{output_dir}/{feature}"
```

- [ ] **Step 4: Implement minimal resolver**

Create `shield/scripts/path_resolver.py`:

```python
# shield/scripts/path_resolver.py
"""Resolve shield artifact paths from the central registry.

Runnable as a library: `from path_resolver import resolve`.
The registry lives at `shield/schema/output-paths.yaml`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "output-paths.yaml"


def _load_registry() -> dict[str, Any]:
    with SCHEMA_PATH.open() as f:
        return yaml.safe_load(f)


def resolve(name: str, **bindings: str) -> str:
    """Resolve a registered path name to a concrete filesystem path.

    Args:
        name: Path name as declared in the registry's `paths:` block.
        **bindings: Variable substitutions (e.g. output_dir, feature, ...).

    Returns:
        The fully-substituted path string.
    """
    registry = _load_registry()
    template = registry["paths"][name]
    return template.format(**bindings)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py::test_resolve_simple_template -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add shield/schema/output-paths.yaml shield/scripts/path_resolver.py shield/scripts/test_path_resolver.py
git commit -m "feat(shield): add path registry + resolver skeleton"
```

---

### Task A2: Resolver — nested path references

The registry should let one path template reference another by name. For example `research: "{feature_dir}/research.md"` should resolve `{feature_dir}` from the registry, not from caller-supplied bindings.

**Files:**
- Modify: `shield/scripts/path_resolver.py`
- Modify: `shield/scripts/test_path_resolver.py`
- Modify: `shield/schema/output-paths.yaml`

- [ ] **Step 1: Write the failing test**

Append to `shield/scripts/test_path_resolver.py`:

```python
def test_resolve_nested_template() -> None:
    # `research` template = "{feature_dir}/research.md", and `feature_dir` is itself a template
    result = resolve("research", output_dir="docs/shield", feature="vpc-20260522")
    assert result == "docs/shield/vpc-20260522/research.md"
```

- [ ] **Step 2: Add the nested template to the registry**

Edit `shield/schema/output-paths.yaml` — add `research:` under `paths:`:

```yaml
paths:
  feature_dir: "{output_dir}/{feature}"
  research:    "{feature_dir}/research.md"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py::test_resolve_nested_template -v`
Expected: FAIL — `{feature_dir}` is not in caller bindings.

- [ ] **Step 4: Implement nested resolution**

Replace `resolve` in `shield/scripts/path_resolver.py`:

```python
def resolve(name: str, **bindings: str) -> str:
    """Resolve a registered path name to a concrete filesystem path.

    Nested references (e.g. `{feature_dir}` inside another template) are
    resolved recursively from the registry. Variable bindings (e.g. `output_dir`)
    come from the caller.
    """
    registry = _load_registry()
    paths = registry["paths"]

    def expand(name_: str, seen: set[str]) -> str:
        if name_ in seen:
            raise ValueError(f"Circular reference detected for path '{name_}'")
        template = paths[name_]
        # Build a merged binding map: nested templates take precedence over bindings.
        merged: dict[str, str] = dict(bindings)
        for nested_name in list(paths.keys()):
            placeholder = "{" + nested_name + "}"
            if placeholder in template and nested_name not in seen:
                merged[nested_name] = expand(nested_name, seen | {name_})
        return template.format(**merged)

    return expand(name, set())
```

- [ ] **Step 5: Run both tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add shield/scripts/path_resolver.py shield/scripts/test_path_resolver.py shield/schema/output-paths.yaml
git commit -m "feat(shield): support nested template refs in path resolver"
```

---

### Task A3: Resolver — counter logic for review folders

The `_counter` variable is empty for first-of-day, `_2` / `_3` / ... on same-day collisions. The resolver itself doesn't choose the counter — that's the caller's job (lint/migration scripts probe filesystem). The resolver just substitutes whatever `_counter` value is passed.

**Files:**
- Modify: `shield/scripts/test_path_resolver.py`
- Modify: `shield/schema/output-paths.yaml`

- [ ] **Step 1: Write the failing test**

Append to `test_path_resolver.py`:

```python
def test_resolve_review_dir_first_run() -> None:
    result = resolve(
        "review_dir",
        output_dir="docs/shield",
        feature="vpc-20260522",
        review_type="plan",
        date="2026-05-21",
        _counter="",
    )
    assert result == "docs/shield/vpc-20260522/reviews/plan/2026-05-21"


def test_resolve_review_dir_same_day_rerun() -> None:
    result = resolve(
        "review_dir",
        output_dir="docs/shield",
        feature="vpc-20260522",
        review_type="plan",
        date="2026-05-21",
        _counter="_2",
    )
    assert result == "docs/shield/vpc-20260522/reviews/plan/2026-05-21_2"
```

- [ ] **Step 2: Add review_dir to registry**

Edit `shield/schema/output-paths.yaml` — add under `paths:`:

```yaml
  review_dir: "{feature_dir}/reviews/{review_type}/{date}{_counter}"
```

And add to `variables:` block (for documentation only — the resolver doesn't enforce variable names):

```yaml
variables:
  output_dir:  "Set by consumer in .shield.json"
  feature:     "Auto-derived from command (e.g. 'vpc-module-20260319')"
  review_type: "One of: prd, plan, code"
  date:        "YYYY-MM-DD of the review run"
  _counter:    "Empty for first run on a date; '_2', '_3', ... on same-day collisions"
```

- [ ] **Step 3: Run tests to verify both pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
Expected: 4 passed.

- [ ] **Step 4: Commit**

```bash
git add shield/scripts/test_path_resolver.py shield/schema/output-paths.yaml
git commit -m "feat(shield): register review_dir with counter logic"
```

---

### Task A4: Resolver — error cases (missing variable, unknown name)

**Files:**
- Modify: `shield/scripts/test_path_resolver.py`
- Modify: `shield/scripts/path_resolver.py`

- [ ] **Step 1: Write the failing tests**

Append to `test_path_resolver.py`:

```python
def test_resolve_unknown_name_raises() -> None:
    with pytest.raises(KeyError) as excinfo:
        resolve("not_a_registered_name", output_dir="docs/shield", feature="x")
    assert "not_a_registered_name" in str(excinfo.value)


def test_resolve_missing_variable_raises() -> None:
    # `research` needs `output_dir` and `feature`; omit `feature`.
    with pytest.raises(KeyError) as excinfo:
        resolve("research", output_dir="docs/shield")
    assert "feature" in str(excinfo.value)
```

- [ ] **Step 2: Run tests to verify they fail with unclear messages**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py::test_resolve_unknown_name_raises test_path_resolver.py::test_resolve_missing_variable_raises -v`
Expected: FAIL — current resolver raises `KeyError` from `paths[name]` for unknown name (lucky pass possible), and from `str.format` for missing variable (less clear).

- [ ] **Step 3: Improve error messages**

Replace `resolve` in `shield/scripts/path_resolver.py`:

```python
def resolve(name: str, **bindings: str) -> str:
    """Resolve a registered path name to a concrete filesystem path.

    Raises:
        KeyError: if `name` is not in the registry, or a required template
            variable is not supplied in `bindings`.
        ValueError: on circular references in the registry.
    """
    registry = _load_registry()
    paths = registry["paths"]
    if name not in paths:
        raise KeyError(f"Path '{name}' is not in the registry (shield/schema/output-paths.yaml)")

    def expand(name_: str, seen: set[str]) -> str:
        if name_ in seen:
            raise ValueError(f"Circular reference detected for path '{name_}'")
        template = paths[name_]
        merged: dict[str, str] = dict(bindings)
        for nested_name in list(paths.keys()):
            placeholder = "{" + nested_name + "}"
            if placeholder in template and nested_name not in seen:
                merged[nested_name] = expand(nested_name, seen | {name_})
        try:
            return template.format(**merged)
        except KeyError as exc:
            missing = exc.args[0]
            raise KeyError(
                f"Path '{name_}' requires variable '{missing}' but it was not supplied"
            ) from exc

    return expand(name, set())
```

- [ ] **Step 4: Run all resolver tests**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/test_path_resolver.py shield/scripts/path_resolver.py
git commit -m "feat(shield): clearer errors for unknown name / missing variable"
```

---

### Task A5: Populate full registry from spec §5

Add every path template from the design spec §5.1 to the registry, plus `legacy_*` entries that capture the *current* (pre-redesign) paths. The `legacy_*` entries exist so that lint can pass during the Phase 3 cutover — they will be removed in Phase 5.

**Files:**
- Modify: `shield/schema/output-paths.yaml`
- Modify: `shield/scripts/test_path_resolver.py`

- [ ] **Step 1: Write the failing coverage test**

Append to `test_path_resolver.py`:

```python
def test_all_spec_paths_resolve() -> None:
    """Smoke test: every path in the spec §5.1 resolves with sample bindings."""
    new_paths = [
        ("manifest",              dict(output_dir="docs/shield")),
        ("global_outputs_dir",    dict(output_dir="docs/shield")),
        ("global_index_html",     dict(output_dir="docs/shield")),
        ("feature_dir",           dict(output_dir="docs/shield", feature="f")),
        ("readme",                dict(output_dir="docs/shield", feature="f")),
        ("research",              dict(output_dir="docs/shield", feature="f")),
        ("prd",                   dict(output_dir="docs/shield", feature="f")),
        ("plan_json",             dict(output_dir="docs/shield", feature="f")),
        ("plan_md",               dict(output_dir="docs/shield", feature="f")),
        ("plan_arch_md",          dict(output_dir="docs/shield", feature="f")),
        ("feature_outputs",       dict(output_dir="docs/shield", feature="f")),
        ("readme_html",           dict(output_dir="docs/shield", feature="f")),
        ("prd_html",              dict(output_dir="docs/shield", feature="f")),
        ("plan_html",             dict(output_dir="docs/shield", feature="f")),
        ("plan_arch_html",        dict(output_dir="docs/shield", feature="f")),
        ("review_dir",            dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_summary",        dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_enhanced",       dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_detailed",       dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="",
                                       agent="backend-engineer")),
        ("review_outputs_dir",    dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_summary_html",   dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_enhanced_html",  dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="")),
        ("review_detailed_html",  dict(output_dir="docs/shield", feature="f",
                                       review_type="plan", date="2026-05-21", _counter="",
                                       agent="backend-engineer")),
    ]
    for name, bindings in new_paths:
        result = resolve(name, **bindings)
        assert result.startswith("docs/shield"), f"{name} did not resolve cleanly: {result!r}"


def test_legacy_paths_resolve() -> None:
    """Legacy entries (pre-redesign) must resolve so lint can pass during Phase 3 cutover."""
    legacy_paths = [
        ("legacy_research_dir", dict(output_dir="docs/shield", feature="f",
                                     n="1", slug="my-topic")),
        ("legacy_plan_dir",     dict(output_dir="docs/shield", feature="f",
                                     n="1", slug="my-plan")),
    ]
    for name, bindings in legacy_paths:
        result = resolve(name, **bindings)
        assert result.startswith("docs/shield"), f"{name} did not resolve: {result!r}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py::test_all_spec_paths_resolve test_path_resolver.py::test_legacy_paths_resolve -v`
Expected: FAIL — most path names are not yet in the registry.

- [ ] **Step 3: Fill in the full registry**

Replace contents of `shield/schema/output-paths.yaml`:

```yaml
# shield/schema/output-paths.yaml
# Plugin-owned contract. Consumers should NOT edit.
# See docs/superpowers/specs/2026-05-22-shield-output-structure-design.md §5.

variables:
  output_dir:   "Set by consumer in .shield.json"
  feature:      "Auto-derived from command (e.g. 'vpc-module-20260319')"
  review_type:  "One of: prd, plan, code"
  date:         "YYYY-MM-DD of the review run"
  _counter:     "Empty for first run on a date; '_2', '_3', ... on same-day collisions"
  agent:        "Agent slug for per-agent detail files (e.g. 'backend-engineer')"
  n:            "(legacy only) numbered-run prefix"
  slug:         "(legacy only) human-readable run slug"

paths:
  # Top-level
  manifest:           "{output_dir}/manifest.json"
  global_outputs_dir: "{output_dir}/outputs"
  global_index_html:  "{global_outputs_dir}/index.html"

  # Per-feature
  feature_dir:        "{output_dir}/{feature}"
  readme:             "{feature_dir}/README.md"
  research:           "{feature_dir}/research.md"
  prd:                "{feature_dir}/prd.md"
  plan_json:          "{feature_dir}/plan.json"
  plan_md:            "{feature_dir}/plan.md"
  plan_arch_md:       "{feature_dir}/plan-architecture.md"

  # Per-feature rendered
  feature_outputs:    "{feature_dir}/outputs"
  readme_html:        "{feature_outputs}/README.html"
  prd_html:           "{feature_outputs}/prd.html"
  plan_html:          "{feature_outputs}/plan.html"
  plan_arch_html:     "{feature_outputs}/plan-architecture.html"

  # Reviews (source)
  review_dir:         "{feature_dir}/reviews/{review_type}/{date}{_counter}"
  review_summary:     "{review_dir}/summary.md"
  review_enhanced:    "{review_dir}/enhanced-{review_type}.md"
  review_detailed:    "{review_dir}/detailed/{agent}.md"

  # Reviews (rendered)
  review_outputs_dir:    "{feature_outputs}/reviews/{review_type}/{date}{_counter}"
  review_summary_html:   "{review_outputs_dir}/summary.html"
  review_enhanced_html:  "{review_outputs_dir}/enhanced-{review_type}.html"
  review_detailed_html:  "{review_outputs_dir}/detailed/{agent}.html"

  # Legacy (pre-redesign). Removed in Phase 5 (see design §10).
  legacy_research_dir: "{output_dir}/{feature}/research/{n}-{slug}"
  legacy_plan_dir:     "{output_dir}/{feature}/plan/{n}-{slug}"
```

- [ ] **Step 4: Run all resolver tests**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/schema/output-paths.yaml shield/scripts/test_path_resolver.py
git commit -m "feat(shield): populate full path registry incl. legacy_* entries"
```

---

## Section B: Lint script

The lint script does three things:
1. **Validates the registry itself** — every template substitutes cleanly given declared variables.
2. **Validates asset frontmatter** — when a command/skill/agent declares an `outputs:` list, every name must exist in the registry.
3. **Scans for orphans** — files under `{output_dir}/` that match no registered template (warn-only).

For Phase 1, no assets have `outputs:` lists yet, so the script must handle the "no outputs declared" case gracefully (skip, no error).

### Task B1: Lint — discover assets and parse frontmatter

**Files:**
- Create: `shield/scripts/lint_output_paths.py`
- Create: `shield/scripts/test_lint_output_paths.py`

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_lint_output_paths.py`:

```python
# shield/scripts/test_lint_output_paths.py
"""Tests for lint_output_paths.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lint_output_paths import discover_assets, parse_outputs_block  # type: ignore[import-not-found]


def _write_asset(path: Path, frontmatter: str, body: str = "Body.\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}")


def test_discover_finds_md_files(tmp_path: Path) -> None:
    _write_asset(tmp_path / "commands" / "plan.md", "name: plan\n")
    _write_asset(tmp_path / "skills" / "x" / "SKILL.md", "name: x\n")
    (tmp_path / "README.md").write_text("not an asset\n")
    found = discover_assets(tmp_path)
    rels = sorted(p.relative_to(tmp_path).as_posix() for p in found)
    assert rels == ["commands/plan.md", "skills/x/SKILL.md"]


def test_parse_outputs_block_present(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n  - plan_json\n")
    assert parse_outputs_block(asset) == ["plan_md", "plan_json"]


def test_parse_outputs_block_absent(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\n")
    assert parse_outputs_block(asset) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
Expected: FAIL — `lint_output_paths` module does not exist.

- [ ] **Step 3: Implement discovery and frontmatter parsing**

Create `shield/scripts/lint_output_paths.py`:

```python
# shield/scripts/lint_output_paths.py
"""Lint shield assets and the path registry for consistency.

Runnable: `uv run --with pyyaml shield/scripts/lint_output_paths.py [--root .] [--strict]`
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

ASSET_DIRS = ("commands", "skills", "agents")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def discover_assets(root: Path) -> list[Path]:
    """Find all asset markdown files under any `commands/`, `skills/`, or `agents/` directory."""
    found: list[Path] = []
    for asset_dir in ASSET_DIRS:
        for path in root.rglob(f"{asset_dir}/**/*.md"):
            if path.is_file():
                found.append(path)
    return sorted(found)


def parse_outputs_block(asset_path: Path) -> list[str]:
    """Return the `outputs:` list from an asset's frontmatter, or [] if absent."""
    text = asset_path.read_text()
    match = FRONTMATTER_RE.match(text)
    if not match:
        return []
    try:
        front = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return []
    raw = front.get("outputs", [])
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/lint_output_paths.py shield/scripts/test_lint_output_paths.py
git commit -m "feat(shield): lint script can discover assets + parse outputs block"
```

---

### Task B2: Lint — validate output names against registry

**Files:**
- Modify: `shield/scripts/lint_output_paths.py`
- Modify: `shield/scripts/test_lint_output_paths.py`

- [ ] **Step 1: Write the failing test**

Append to `test_lint_output_paths.py`:

```python
from lint_output_paths import validate_asset  # type: ignore[import-not-found]


def test_validate_asset_passes_when_outputs_in_registry(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n  - plan_json\n")
    errors = validate_asset(asset, registry_names={"plan_md", "plan_json", "research"})
    assert errors == []


def test_validate_asset_fails_on_unknown_name(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n  - not_in_registry\n")
    errors = validate_asset(asset, registry_names={"plan_md"})
    assert len(errors) == 1
    assert "not_in_registry" in errors[0]
    assert asset.name in errors[0]


def test_validate_asset_no_outputs_is_ok(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\n")
    errors = validate_asset(asset, registry_names={"plan_md"})
    assert errors == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
Expected: FAIL — `validate_asset` not yet defined.

- [ ] **Step 3: Implement validate_asset**

Append to `shield/scripts/lint_output_paths.py`:

```python
def validate_asset(asset_path: Path, registry_names: set[str]) -> list[str]:
    """Return a list of human-readable error messages for an asset's outputs declarations.

    Empty list means the asset is clean (including the case where it declares no outputs).
    """
    errors: list[str] = []
    for name in parse_outputs_block(asset_path):
        if name not in registry_names:
            errors.append(
                f"{asset_path.name}: declared output '{name}' is not in the path registry"
            )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/lint_output_paths.py shield/scripts/test_lint_output_paths.py
git commit -m "feat(shield): lint validates asset outputs against registry names"
```

---

### Task B3: Lint — validate the registry itself

The registry can have its own bugs: a template referencing an undeclared variable, or a typo in a nested name.

**Files:**
- Modify: `shield/scripts/lint_output_paths.py`
- Modify: `shield/scripts/test_lint_output_paths.py`

- [ ] **Step 1: Write the failing test**

Append to `test_lint_output_paths.py`:

```python
from lint_output_paths import validate_registry  # type: ignore[import-not-found]


def test_validate_registry_passes_clean_registry() -> None:
    registry = {
        "variables": {"output_dir": "", "feature": ""},
        "paths": {
            "feature_dir": "{output_dir}/{feature}",
            "research":    "{feature_dir}/research.md",
        },
    }
    assert validate_registry(registry) == []


def test_validate_registry_flags_unknown_variable() -> None:
    registry = {
        "variables": {"output_dir": ""},
        "paths": {
            "research": "{output_dir}/{nonexistent}/research.md",
        },
    }
    errors = validate_registry(registry)
    assert len(errors) == 1
    assert "nonexistent" in errors[0]
    assert "research" in errors[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py::test_validate_registry_passes_clean_registry test_lint_output_paths.py::test_validate_registry_flags_unknown_variable -v`
Expected: FAIL — `validate_registry` not yet defined.

- [ ] **Step 3: Implement validate_registry**

Append to `shield/scripts/lint_output_paths.py`:

```python
PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")


def validate_registry(registry: dict) -> list[str]:
    """Check that every placeholder in a template is either a declared variable
    or another registered path name. Returns a list of human-readable errors.
    """
    errors: list[str] = []
    declared_vars = set(registry.get("variables", {}).keys())
    path_names = set(registry.get("paths", {}).keys())
    known = declared_vars | path_names

    for path_name, template in registry.get("paths", {}).items():
        for placeholder in PLACEHOLDER_RE.findall(template):
            if placeholder not in known:
                errors.append(
                    f"registry path '{path_name}' references undeclared variable '{placeholder}'"
                )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/lint_output_paths.py shield/scripts/test_lint_output_paths.py
git commit -m "feat(shield): lint validates registry self-consistency"
```

---

### Task B4: Lint — CLI entry with exit codes

The lint script must be runnable from the command line, walk the actual repo, and exit non-zero on errors.

**Files:**
- Modify: `shield/scripts/lint_output_paths.py`
- Modify: `shield/scripts/test_lint_output_paths.py`

- [ ] **Step 1: Write the failing test**

Append to `test_lint_output_paths.py`:

```python
import subprocess


def test_cli_passes_clean_tree(tmp_path: Path) -> None:
    # Build a minimal repo: registry + one asset with no outputs declared
    schema_dir = tmp_path / "shield" / "schema"
    schema_dir.mkdir(parents=True)
    (schema_dir / "output-paths.yaml").write_text(
        "variables:\n  output_dir: ''\n"
        "paths:\n  feature_dir: '{output_dir}/x'\n"
    )
    asset = tmp_path / "shield" / "commands" / "plan.md"
    asset.parent.mkdir(parents=True)
    _write_asset(asset, "name: plan\n")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "lint_output_paths.py"), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_fails_on_unknown_output_name(tmp_path: Path) -> None:
    schema_dir = tmp_path / "shield" / "schema"
    schema_dir.mkdir(parents=True)
    (schema_dir / "output-paths.yaml").write_text(
        "variables:\n  output_dir: ''\n"
        "paths:\n  feature_dir: '{output_dir}/x'\n"
    )
    asset = tmp_path / "shield" / "commands" / "plan.md"
    asset.parent.mkdir(parents=True)
    _write_asset(asset, "name: plan\noutputs:\n  - ghost_path\n")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "lint_output_paths.py"), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "ghost_path" in result.stdout + result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py::test_cli_passes_clean_tree test_lint_output_paths.py::test_cli_fails_on_unknown_output_name -v`
Expected: FAIL — script has no CLI entry yet.

- [ ] **Step 3: Implement CLI**

Append to `shield/scripts/lint_output_paths.py`:

```python
def _load_registry_from(root: Path) -> dict:
    schema = root / "shield" / "schema" / "output-paths.yaml"
    with schema.open() as f:
        return yaml.safe_load(f)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Lint shield asset outputs against path registry.")
    parser.add_argument("--root", default=".", help="Repo root (default: current dir)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    registry = _load_registry_from(root)

    errors: list[str] = []
    errors.extend(validate_registry(registry))
    registry_names = set(registry.get("paths", {}).keys())
    for asset in discover_assets(root / "shield"):
        errors.extend(validate_asset(asset, registry_names))

    if errors:
        print("Lint failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"Lint clean: registry + {len(discover_assets(root / 'shield'))} assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
Expected: 10 passed.

- [ ] **Step 5: Sanity-check lint on the real repo**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0 — the populated registry is self-consistent, and no existing commands declare an `outputs:` block (Phase 3 hasn't happened yet).

- [ ] **Step 6: Commit**

```bash
git add shield/scripts/lint_output_paths.py shield/scripts/test_lint_output_paths.py
git commit -m "feat(shield): lint CLI with exit codes and real-repo sanity check"
```

---

## Section C: Migration script

The migration script walks `{output_dir}/` and moves files from the legacy numbered-run layout to the new flat layout. Dry-run is the default; `--apply` actually moves files. Idempotent: re-running on an already-migrated tree is a no-op. Unrecognized files (like `handoff.md`) are left alone with a warning.

### Task C1: Migration — old → new path mapping function

This is a pure function: given a relative path under `{output_dir}/{feature}/`, return either the new path or `None` (meaning "leave alone, warn").

**Files:**
- Create: `shield/scripts/migrate_outputs.py`
- Create: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Create `shield/scripts/test_migrate_outputs.py`:

```python
# shield/scripts/test_migrate_outputs.py
"""Tests for migrate_outputs.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from migrate_outputs import map_legacy_path  # type: ignore[import-not-found]


@pytest.mark.parametrize("old,new", [
    # research findings → research.md
    ("research/1-claude-isolation/findings.md", "research.md"),
    ("research/2-rerun/findings.md",            "research.md"),
    # session transcripts → hidden file
    ("research/1-claude-isolation/transcript.md", ".session-transcript.md"),
    # plan architecture HTML → outputs/
    ("plan/1-foo/architecture.html", "outputs/plan-architecture.html"),
    # files already at root → unchanged (None signals "no move needed")
    ("plan.json", None),
    ("handoff.md", None),
    ("README.md", None),
])
def test_map_legacy_path(old: str, new: str | None) -> None:
    assert map_legacy_path(old) == new
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Implement map_legacy_path**

Create `shield/scripts/migrate_outputs.py`:

```python
# shield/scripts/migrate_outputs.py
"""Migrate a Shield output tree from the legacy numbered-run layout to the
flat per-feature layout defined in
docs/superpowers/specs/2026-05-22-shield-output-structure-design.md.

Runnable: `uv run --with pyyaml shield/scripts/migrate_outputs.py [--root docs/shield] [--apply]`
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

# Patterns: (compiled regex on POSIX relpath, callable returning new relpath or None)
_RESEARCH_FINDINGS = re.compile(r"^research/\d+-[^/]+/findings\.md$")
_RESEARCH_TRANSCRIPT = re.compile(r"^research/\d+-[^/]+/transcript\.md$")
_PLAN_ARCH_HTML = re.compile(r"^plan/\d+-[^/]+/architecture\.html$")


def map_legacy_path(relpath: str) -> Optional[str]:
    """Map a path under {output_dir}/{feature}/ to its new location.

    Returns None if the path is already at its new location (no move needed) or
    is unrecognized (caller decides whether to warn).
    """
    if _RESEARCH_FINDINGS.match(relpath):
        return "research.md"
    if _RESEARCH_TRANSCRIPT.match(relpath):
        return ".session-transcript.md"
    if _PLAN_ARCH_HTML.match(relpath):
        return "outputs/plan-architecture.html"
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: 7 passed (parametrized).

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): pure mapping function for legacy → new layout"
```

---

### Task C2: Migration — walk feature tree, return planned moves

Separate "what would I move" (pure function over filesystem) from "actually move them" (side-effecting).

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
from migrate_outputs import plan_moves  # type: ignore[import-not-found]


def _make_tree(root: Path, files: list[str]) -> None:
    for f in files:
        path = root / f
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content of " + f)


def test_plan_moves_typical_feature_tree(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, [
        "research/1-claude-isolation/findings.md",
        "research/1-claude-isolation/transcript.md",
        "plan.json",
        "plan/1-foo/architecture.html",
        "handoff.md",
    ])
    moves, warnings = plan_moves(feature)

    moves_set = {(src.relative_to(feature).as_posix(),
                  dst.relative_to(feature).as_posix())
                 for src, dst in moves}
    assert moves_set == {
        ("research/1-claude-isolation/findings.md",   "research.md"),
        ("research/1-claude-isolation/transcript.md", ".session-transcript.md"),
        ("plan/1-foo/architecture.html",              "outputs/plan-architecture.html"),
    }

    # handoff.md is unrecognized (under root, not in legacy patterns) → warning
    warning_paths = {w.split(":")[0] for w in warnings}
    assert "handoff.md" in warning_paths


def test_plan_moves_already_migrated_tree(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, ["research.md", "plan.json", "prd.md"])
    moves, warnings = plan_moves(feature)
    assert moves == []
    # Already-flat files at root that aren't in the new schema would warn, but research/prd/plan_json are.
    assert warnings == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_plan_moves_typical_feature_tree test_migrate_outputs.py::test_plan_moves_already_migrated_tree -v`
Expected: FAIL — `plan_moves` not defined.

- [ ] **Step 3: Implement plan_moves**

Append to `shield/scripts/migrate_outputs.py`:

```python
# Files that are valid at the feature root in the new schema (no warning if seen here).
KNOWN_ROOT_FILES = {
    "README.md", "research.md", "prd.md", "plan.json", "plan.md",
    "plan-architecture.md", ".session-transcript.md",
}


def plan_moves(feature_dir: Path) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Walk a feature directory and return (moves, warnings).

    moves: list of (src, dst) absolute pairs to move.
    warnings: human-readable messages for files we don't recognize.
    """
    moves: list[tuple[Path, Path]] = []
    warnings: list[str] = []

    for path in sorted(feature_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(feature_dir).as_posix()
        target = map_legacy_path(rel)
        if target is not None:
            moves.append((path, feature_dir / target))
            continue
        # No mapping. Is it already-correct, or unrecognized?
        if "/" not in rel:
            if rel not in KNOWN_ROOT_FILES:
                warnings.append(f"{rel}: unrecognized file at feature root, left in place")
            # else: file is already at its correct location
        else:
            # Nested file that's not a legacy pattern — warn.
            warnings.append(f"{rel}: unrecognized nested file, left in place")

    return moves, warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): plan_moves walks a feature tree, returns moves + warnings"
```

---

### Task C3: Migration — apply moves to filesystem

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
from migrate_outputs import apply_moves  # type: ignore[import-not-found]


def test_apply_moves_executes(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, [
        "research/1-claude-isolation/findings.md",
        "research/1-claude-isolation/transcript.md",
        "plan/1-foo/architecture.html",
    ])
    moves, _ = plan_moves(feature)
    apply_moves(moves)

    assert (feature / "research.md").exists()
    assert (feature / ".session-transcript.md").exists()
    assert (feature / "outputs" / "plan-architecture.html").exists()
    # Sources should be gone
    assert not (feature / "research" / "1-claude-isolation" / "findings.md").exists()


def test_apply_moves_removes_empty_dirs(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, ["research/1-claude-isolation/findings.md"])
    moves, _ = plan_moves(feature)
    apply_moves(moves)

    # The numbered-run folder and its parent should be cleaned up if empty
    assert not (feature / "research").exists() or not any((feature / "research").iterdir())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_apply_moves_executes test_migrate_outputs.py::test_apply_moves_removes_empty_dirs -v`
Expected: FAIL — `apply_moves` not defined.

- [ ] **Step 3: Implement apply_moves**

Append to `shield/scripts/migrate_outputs.py`:

```python
def apply_moves(moves: list[tuple[Path, Path]]) -> None:
    """Execute the moves and clean up empty parent directories."""
    parents_to_check: set[Path] = set()
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        parents_to_check.add(src.parent)

    # Sweep emptied numbered-run dirs and their parents (one level up).
    for p in sorted(parents_to_check, key=lambda x: len(x.as_posix()), reverse=True):
        if p.exists() and not any(p.iterdir()):
            p.rmdir()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): apply_moves executes moves and cleans empty dirs"
```

---

### Task C4: Migration — idempotence

Re-running migration on an already-migrated tree must be a no-op (no moves planned).

**Files:**
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
def test_apply_then_plan_is_noop(tmp_path: Path) -> None:
    feature = tmp_path / "vpc-20260322"
    _make_tree(feature, [
        "research/1-claude-isolation/findings.md",
        "plan/1-foo/architecture.html",
    ])
    moves1, _ = plan_moves(feature)
    apply_moves(moves1)

    # Second pass: nothing to migrate
    moves2, warnings2 = plan_moves(feature)
    assert moves2 == []
    assert warnings2 == []
```

- [ ] **Step 2: Run test to verify it passes immediately**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_apply_then_plan_is_noop -v`
Expected: PASS — `plan_moves` already returns empty for an already-migrated tree (Task C2 covered this case). If it fails, fix `plan_moves` until it does.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/test_migrate_outputs.py
git commit -m "test(shield): assert migrate is idempotent across runs"
```

---

### Task C5: Migration — regenerate manifest.json (v2)

After moves complete, write a v2-schema manifest.json reflecting the new tree shape.

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
import json
from migrate_outputs import build_manifest  # type: ignore[import-not-found]


def test_build_manifest_v2_structure(tmp_path: Path) -> None:
    output_dir = tmp_path / "docs" / "shield"
    feature = output_dir / "vpc-20260322"
    _make_tree(feature, [
        "research.md",
        "plan.json",
        "reviews/plan/2026-05-21/summary.md",
        "reviews/plan/2026-05-21_2/summary.md",
        "reviews/code/2026-05-22/summary.md",
    ])

    manifest = build_manifest(output_dir)

    assert manifest["schema_version"] == 2
    assert len(manifest["features"]) == 1
    feat = manifest["features"][0]
    assert feat["name"] == "vpc-20260322"
    assert feat["artifacts"]["research"] is True
    assert feat["artifacts"]["plan_json"] is True
    assert feat["artifacts"]["prd"] is False
    assert feat["reviews"]["plan"] == {"latest": "2026-05-21_2", "count": 2}
    assert feat["reviews"]["code"] == {"latest": "2026-05-22", "count": 1}
    assert "prd" not in feat["reviews"] or feat["reviews"]["prd"]["count"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_build_manifest_v2_structure -v`
Expected: FAIL — `build_manifest` not defined.

- [ ] **Step 3: Implement build_manifest**

Append to `shield/scripts/migrate_outputs.py`:

```python
from datetime import datetime, timezone

# Artifact filenames the manifest tracks per feature (matches design §6.1).
TRACKED_ARTIFACTS = {
    "research":     "research.md",
    "prd":          "prd.md",
    "plan_json":    "plan.json",
    "plan_md":      "plan.md",
    "plan_arch_md": "plan-architecture.md",
    "readme":       "README.md",
}


def _summarize_reviews(feature_dir: Path, review_type: str) -> dict[str, str | int]:
    review_root = feature_dir / "reviews" / review_type
    if not review_root.exists():
        return {"count": 0}
    runs = sorted(d.name for d in review_root.iterdir() if d.is_dir())
    if not runs:
        return {"count": 0}
    return {"latest": runs[-1], "count": len(runs)}


def build_manifest(output_dir: Path) -> dict:
    """Walk {output_dir} and return a v2 manifest dict."""
    features: list[dict] = []
    for feature_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        if feature_dir.name == "outputs":
            continue  # global rendered output, not a feature
        artifacts = {
            key: (feature_dir / fname).exists()
            for key, fname in TRACKED_ARTIFACTS.items()
        }
        reviews = {
            rt: _summarize_reviews(feature_dir, rt)
            for rt in ("prd", "plan", "code")
        }
        features.append({
            "name": feature_dir.name,
            "artifacts": artifacts,
            "reviews": reviews,
            "updated": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        })
    return {"schema_version": 2, "features": features}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): build_manifest produces v2 schema from tree"
```

---

### Task C6: Migration — CLI with dry-run default and --apply

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
import subprocess


def test_cli_dry_run_does_not_move(tmp_path: Path) -> None:
    output_dir = tmp_path / "docs" / "shield"
    feature = output_dir / "vpc-20260322"
    _make_tree(feature, ["research/1-claude-isolation/findings.md"])

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"), "--root", str(output_dir)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    # Dry-run: file should still be at old location
    assert (feature / "research" / "1-claude-isolation" / "findings.md").exists()
    assert not (feature / "research.md").exists()
    assert "dry-run" in result.stdout.lower() or "would move" in result.stdout.lower()


def test_cli_apply_moves_and_writes_manifest(tmp_path: Path) -> None:
    output_dir = tmp_path / "docs" / "shield"
    feature = output_dir / "vpc-20260322"
    _make_tree(feature, ["research/1-claude-isolation/findings.md", "plan.json"])

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"),
         "--root", str(output_dir), "--apply"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (feature / "research.md").exists()
    assert (output_dir / "manifest.json").exists()
    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["schema_version"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_cli_dry_run_does_not_move test_migrate_outputs.py::test_cli_apply_moves_and_writes_manifest -v`
Expected: FAIL — no CLI yet.

- [ ] **Step 3: Implement CLI**

Append to `shield/scripts/migrate_outputs.py`:

```python
def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Migrate Shield output tree to new flat layout."
    )
    parser.add_argument("--root", default="docs/shield",
                        help="Output directory to migrate (default: docs/shield)")
    parser.add_argument("--apply", action="store_true",
                        help="Actually move files (default: dry-run)")
    args = parser.parse_args(argv)

    output_dir = Path(args.root).resolve()
    if not output_dir.exists():
        print(f"error: --root {output_dir} does not exist", file=sys.stderr)
        return 2

    total_moves = 0
    total_warnings = 0

    for feature_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        if feature_dir.name == "outputs":
            continue
        moves, warnings = plan_moves(feature_dir)
        for src, dst in moves:
            rel_src = src.relative_to(output_dir).as_posix()
            rel_dst = dst.relative_to(output_dir).as_posix()
            verb = "moving" if args.apply else "would move"
            print(f"{verb}: {rel_src} -> {rel_dst}")
        for w in warnings:
            print(f"warning: {feature_dir.name}/{w}")
        if args.apply:
            apply_moves(moves)
        total_moves += len(moves)
        total_warnings += len(warnings)

    if args.apply:
        manifest = build_manifest(output_dir)
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"wrote manifest: {output_dir / 'manifest.json'}")

    mode = "applied" if args.apply else "dry-run"
    print(f"{mode}: {total_moves} moves, {total_warnings} warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: 15 passed.

- [ ] **Step 5: Dry-run on the real repo to sanity-check**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/migrate_outputs.py --root docs/shield`
Expected: prints "would move" lines for the three existing feature folders' legacy files, no files actually move. Exit 0.

(Do NOT pass `--apply` — running the real migration is a follow-up step that belongs in the cutover plan, not this foundations plan.)

- [ ] **Step 6: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): migrate_outputs CLI with dry-run default and --apply"
```

---

### Task C7: Migration — final verification on real repo (read-only)

A sanity check that the migration tooling produces the expected output for the three real feature folders, without touching anything.

**Files:** none modified.

- [ ] **Step 1: Run dry-run, capture stdout**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/migrate_outputs.py --root docs/shield`

- [ ] **Step 2: Verify expected moves are listed**

Confirm output mentions (at minimum) these would-moves:
- `devcontainer-implement-20260518/research/1-claude-implement-isolation/findings.md -> devcontainer-implement-20260518/research.md`
- `devcontainer-implement-20260518/research/1-claude-implement-isolation/transcript.md -> devcontainer-implement-20260518/.session-transcript.md`
- `agent-behavior-decomposition-20260520/plan/1-behavior-catalog-migration/architecture.html -> agent-behavior-decomposition-20260520/outputs/plan-architecture.html`

And these warnings (or similar):
- `pm-restructure-v0-20260521/handoff.md: unrecognized file at feature root`

- [ ] **Step 3: Confirm filesystem is unchanged**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git status docs/shield`
Expected: nothing changed in docs/shield.

- [ ] **Step 4: No commit needed** — this is a verification step, not a code change.

---

## Section D: Wrap-up

### Task D1: Add a `Makefile` target or README pointer (optional polish)

Make it easy to run the tools without remembering `uv run --with pyyaml ...`.

**Files:**
- Modify: `shield/scripts/README.md` if it exists, else skip this task.

- [ ] **Step 1: Check if a scripts README exists**

Run: `ls /Users/apple/projects/infraspecdev/tesseract/shield/scripts/README.md 2>/dev/null && echo "exists" || echo "skip"`

If `skip`: mark this task done and move on. Do NOT create a new README — repo convention does not require it.

- [ ] **Step 2 (only if README exists): Append usage notes**

Append a section like:

```markdown
## Output paths tooling (added 2026-05-22)

- `lint_output_paths.py` — validates the path registry and any asset `outputs:` declarations.
  Run: `uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
- `migrate_outputs.py` — migrates legacy numbered-run trees to the new flat layout.
  Run: `uv run --with pyyaml shield/scripts/migrate_outputs.py --root docs/shield` (dry-run).
  Add `--apply` to actually move files. See `docs/superpowers/specs/2026-05-22-shield-output-structure-design.md`.
```

- [ ] **Step 3: Commit if README was modified**

```bash
git add shield/scripts/README.md
git commit -m "docs(shield): document lint + migrate scripts in scripts/README"
```

---

### Task D2: Final integration check

Run all tests + lint on the real repo, end-to-end.

- [ ] **Step 1: Run all new tests together**

Run: `cd /Users/apple/projects/infraspecdev/tesseract/shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py test_lint_output_paths.py test_migrate_outputs.py -v`
Expected: all tests pass (8 + 10 + 15 = 33).

- [ ] **Step 2: Lint the real repo**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0, message "Lint clean: registry + N assets" where N is however many commands/skills/agents exist.

- [ ] **Step 3: Confirm git status is clean**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git status`
Expected: working tree clean, all foundation commits on branch.

- [ ] **Step 4: No commit needed** — this is a verification step.

---

## Definition of Done

- [ ] `shield/schema/output-paths.yaml` contains all path templates from spec §5.1 plus `legacy_*` entries.
- [ ] `shield/scripts/path_resolver.py` exposes `resolve(name, **bindings)` with nested-template support, clear errors for unknown name / missing variable, and circular-reference detection.
- [ ] `shield/scripts/lint_output_paths.py` validates the registry and asset frontmatter, exits non-zero on errors, exits zero on the current repo (since no asset declares `outputs:` yet).
- [ ] `shield/scripts/migrate_outputs.py` dry-runs by default, supports `--apply`, is idempotent, leaves unrecognized files alone with a warning, and writes a v2 `manifest.json` on apply.
- [ ] All three new test files pass under `uv run --with pyyaml --with pytest pytest -v`.
- [ ] The real-repo dry-run lists the expected moves for the three existing feature folders without touching the filesystem.
- [ ] No edits to any existing `shield/commands/*.md`, `shield/skills/*/SKILL.md`, or `shield/agents/*.md` (that's the follow-up cutover plan).

---

## Follow-up Plans (not in this plan's scope)

1. **Phase 3 — per-asset cutover:** add `outputs:` frontmatter to each command/skill/agent, rewrite body prose to reference registry path names. Likely one plan per command family (research/prd, plan, reviews, pm-sync, init/migrate). Each plan requires an eval per modified asset (repo CLAUDE.md mandate).
2. **Phase 4 — live migration:** run `migrate_outputs.py --apply` against the real `docs/shield/`, commit the resulting tree.
3. **Phase 5 — legacy cleanup:** remove `legacy_*` entries from `output-paths.yaml`; remove the corresponding regex patterns from `migrate_outputs.py`.
