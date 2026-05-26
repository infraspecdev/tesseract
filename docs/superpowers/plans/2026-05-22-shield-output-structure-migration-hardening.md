# Shield Output Structure — Migration Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `migrate_outputs.py` safe and complete for real consumer trees. Today the script only handles 3 legacy patterns and silently overwrites on destination collisions — running `--apply` on a real shield-managed project (e.g. flow-research) loses data. This plan closes those gaps.

**Architecture:** Three changes layered on top of foundations:
1. Registry amendment — add 4 missing artifact paths (`prd_meta_json`, `source_prd`, `review_comments_json`, `code_review_changes`) discovered by auditing shield commands.
2. Migration script hardening — collision detection (latest-mtime wins, discards logged), dirty-tree warn-and-confirm, expanded legacy pattern coverage with mtime-derived dates for review folders.
3. Eval pattern strengthening — update the Phase 3 cutover Reference task so each command's eval asserts the *exact* set of written paths, rejecting silently-introduced extras.

**Tech Stack:** Same as foundations — Python 3.11+ with `pyyaml`/`pytest` via `uv run`. No new runtime dependencies.

**Scope:** Slots **between Phase 3 (cutover) and Phase 4 (live migration)**. Numbering stays as-is on existing committed plans; this one is just "migration hardening" (no phase number). It is a **prerequisite for Phase 4** but **independent of Phase 3** (can land in parallel).

**Prerequisites:**
- Foundations PR (`feat/shield-output-foundations`) merged.
- `git status` clean on `main`.

**Out of scope:**
- Running `migrate_outputs.py --apply` against any real tree (still Phase 4's job).
- Removing `legacy_*` registry entries (still Phase 5's job).

---

## Reference test fixture (used throughout)

Several tasks in Sections B–D build the same synthetic tree shaped like a real consumer (flow-research). Define it once here; tasks reference it as `_make_realistic_tree`.

```python
def _make_realistic_tree(root: Path) -> Path:
    """Build a synthetic feature tree shaped like a real shield-managed project.

    Returns the feature root. Caller can compose multiple features under `root`.
    """
    feature = root / "bill-payments-platform-20260430"
    files = {
        # Already-flat
        "plan.json": '{"epics": []}',
        # Research (two runs — collision case)
        "research/1-platform-foundations/findings.md":           "platform foundations findings",
        "research/2-multi-geo-data-and-execution-residency/findings.md": "multi-geo findings",
        # PRD source + render + meta
        "prd/1-bill-payments-platform-v2/prd.md":      "# PRD body",
        "prd/1-bill-payments-platform-v2/prd.html":    "<html>PRD</html>",
        "prd/1-bill-payments-platform-v2/prd.meta.json": '{"version": 2}',
        # PRD review run
        "prd-review/1-bill-payments-platform-v2/summary.md":           "# Summary",
        "prd-review/1-bill-payments-platform-v2/enhanced-prd.md":      "# Enhanced PRD",
        "prd-review/1-bill-payments-platform-v2/source-prd.md":        "# Source snapshot",
        "prd-review/1-bill-payments-platform-v2/review-comments.json": '{"comments": []}',
        "prd-review/1-bill-payments-platform-v2/detailed/agile-coach.md":     "agile findings",
        "prd-review/1-bill-payments-platform-v2/detailed/tech-lead-reviewer.md": "tech findings",
        # Plan render
        "plan/1-prd-v2-foundation/architecture.html": "<html>arch</html>",
        "plan/1-prd-v2-foundation/plan.html":         "<html>plan</html>",
        # Plan review
        "plan-review/1-bill-payments-platform/detailed/architecture-reviewer.md": "arch reviewer",
        # Ad-hoc (orphan)
        "plans/product-note.md": "side note",
    }
    for relpath, content in files.items():
        p = feature / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return feature
```

Note: when collision testing matters, callers should `touch` files with explicit mtimes (`os.utime`) so latest-vs-older is deterministic.

---

## Section A: Registry amendment

Add the four missed paths. These come from auditing shield commands — every artifact actually emitted by `/shield prd`, `/shield prd-review`, and `/shield review` should be in the registry.

### Task A1: Add four new registry entries

**Files:**
- Modify: `shield/schema/output-paths.yaml`
- Modify: `shield/scripts/test_path_resolver.py`

- [ ] **Step 1: Write the failing test**

Append to `test_path_resolver.py`:

```python
def test_resolve_added_artifacts() -> None:
    base = dict(output_dir="docs/shield", feature="f")
    review_base = {**base, "review_type": "prd", "date": "2026-05-21", "_counter": ""}

    assert resolve("prd_meta_json", **base) == "docs/shield/f/prd.meta.json"
    assert resolve("source_prd", **review_base) == "docs/shield/f/reviews/prd/2026-05-21/source-prd.md"
    assert resolve("review_comments_json", **review_base) == \
        "docs/shield/f/reviews/prd/2026-05-21/review-comments.json"

    code_base = {**base, "review_type": "code", "date": "2026-05-22", "_counter": ""}
    assert resolve("code_review_changes", **code_base) == \
        "docs/shield/f/reviews/code/2026-05-22/changes.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py::test_resolve_added_artifacts -v`
Expected: FAIL — none of these names are in the registry.

- [ ] **Step 3: Add the entries to the registry**

Edit `shield/schema/output-paths.yaml` — under the existing per-feature and reviews sections:

```yaml
paths:
  # ... existing entries ...

  # Per-feature (added 2026-05-22)
  prd_meta_json:        "{feature_dir}/prd.meta.json"

  # Reviews (source, added 2026-05-22)
  source_prd:           "{review_dir}/source-prd.md"        # bound with review_type=prd
  review_comments_json: "{review_dir}/review-comments.json" # bound with review_type=prd
  code_review_changes:  "{review_dir}/changes.md"           # bound with review_type=code
```

(Place each near its logical neighbors — `prd_meta_json` near other per-feature paths, the review entries near `review_summary`, `review_enhanced`, `review_detailed`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
Expected: all tests pass (now 10 instead of 9).

- [ ] **Step 5: Run lint on the real repo**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0. The new entries don't reference any new variables, so the registry self-check stays green.

- [ ] **Step 6: Commit**

```bash
git add shield/schema/output-paths.yaml shield/scripts/test_path_resolver.py
git commit -m "feat(shield): add prd_meta_json, source_prd, review_comments_json, code_review_changes to registry"
```

---

### Task A2: Amend the design spec to reflect the registry additions

**Files:**
- Modify: `docs/superpowers/specs/2026-05-22-shield-output-structure-design.md`

- [ ] **Step 1: Add the four entries to §5.1 of the spec**

Open the spec at `docs/superpowers/specs/2026-05-22-shield-output-structure-design.md` and find the `paths:` block under §5.1. Add the same entries you added to `output-paths.yaml`, in matching positions.

Also append a short note at the end of §5.1:

> **Amendment 2026-05-22:** the original §5.1 missed four artifacts emitted by current shield commands (`prd.meta.json` from `/shield prd`; `source-prd.md`, `review-comments.json` from `/shield prd-review`; `changes.md` from `/shield review` and its domain variants). These were added during migration hardening after auditing actual command bodies.

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-05-22-shield-output-structure-design.md
git commit -m "docs(shield): amend spec §5.1 to reflect 4 added registry entries"
```

---

## Section B: Collision detection and resolution

When two source paths map to the same destination, the current `apply_moves` silently overwrites. Switch to latest-mtime-wins with explicit logging.

### Task B1: Detect destination collisions in `plan_moves`

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
import os


def test_plan_moves_returns_collision_resolutions(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    _make_tree(feature, [
        "research/1-old/findings.md",
        "research/2-new/findings.md",
    ])
    # Make 2-new newer
    older = feature / "research/1-old/findings.md"
    newer = feature / "research/2-new/findings.md"
    os.utime(older, (1700000000, 1700000000))
    os.utime(newer, (1800000000, 1800000000))

    moves, warnings = plan_moves(feature)
    # Exactly one move to research.md (the newer one)
    moves_to_research = [
        (src, dst) for src, dst in moves
        if dst.name == "research.md"
    ]
    assert len(moves_to_research) == 1
    chosen_src, _ = moves_to_research[0]
    assert chosen_src == newer, f"Expected newer file to win; got {chosen_src}"

    # Older one must be reported in warnings as a discard
    discard_warnings = [w for w in warnings if "discarded" in w.lower() and "1-old" in w]
    assert len(discard_warnings) == 1, f"Expected one discard warning; got {warnings!r}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_plan_moves_returns_collision_resolutions -v`
Expected: FAIL — current `plan_moves` returns both moves (or one of them arbitrarily), no discard warning.

- [ ] **Step 3: Implement collision resolution**

In `shield/scripts/migrate_outputs.py`, replace `plan_moves` with a version that detects collisions and picks the latest-mtime source. After collecting raw moves, group by destination and resolve:

```python
def plan_moves(feature_dir: Path) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Walk a feature directory and return (moves, warnings).

    On destination collisions, the latest-mtime source wins; older sources are
    discarded with a warning (their content remains recoverable via git history
    of the source path, provided the source tree was committed before migration).
    """
    raw_moves: list[tuple[Path, Path]] = []
    warnings: list[str] = []

    for path in sorted(feature_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(feature_dir).as_posix()
        target = map_legacy_path(rel)
        if target is not None:
            raw_moves.append((path, feature_dir / target))
            continue
        if "/" not in rel:
            if rel not in KNOWN_ROOT_FILES:
                warnings.append(f"{rel}: unrecognized file at feature root, left in place")
        else:
            warnings.append(f"{rel}: unrecognized nested file, left in place")

    # Resolve destination collisions: latest mtime wins.
    by_dst: dict[Path, list[Path]] = {}
    for src, dst in raw_moves:
        by_dst.setdefault(dst, []).append(src)

    resolved: list[tuple[Path, Path]] = []
    for dst, srcs in by_dst.items():
        if len(srcs) == 1:
            resolved.append((srcs[0], dst))
            continue
        # Pick latest-mtime, discard others.
        srcs_sorted = sorted(srcs, key=lambda p: p.stat().st_mtime, reverse=True)
        winner = srcs_sorted[0]
        resolved.append((winner, dst))
        for loser in srcs_sorted[1:]:
            rel_loser = loser.relative_to(feature_dir).as_posix()
            rel_winner = winner.relative_to(feature_dir).as_posix()
            rel_dst = dst.relative_to(feature_dir).as_posix()
            warnings.append(
                f"{rel_loser}: discarded on collision (newer {rel_winner} wins for {rel_dst})"
            )

    return resolved, warnings
```

- [ ] **Step 4: Run all migration tests**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: all existing tests still pass; the new `test_plan_moves_returns_collision_resolutions` passes.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): plan_moves resolves dest collisions by latest mtime"
```

---

### Task B2: CLI output explicitly logs collision discards

The CLI already prints warnings, so this is a verification that the discard message renders well to a user.

**Files:**
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
def test_cli_dry_run_logs_collision_discard(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    _make_tree(feature, [
        "research/1-old/findings.md",
        "research/2-new/findings.md",
    ])
    older = feature / "research/1-old/findings.md"
    newer = feature / "research/2-new/findings.md"
    os.utime(older, (1700000000, 1700000000))
    os.utime(newer, (1800000000, 1800000000))

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"), "--root", str(tmp_path)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    out = result.stdout + result.stderr
    assert "discarded on collision" in out
    assert "1-old" in out  # older one explicitly mentioned
```

- [ ] **Step 2: Run test**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_cli_dry_run_logs_collision_discard -v`
Expected: PASS — the existing CLI already prints warnings via the same path. If it fails, inspect the CLI's warning loop and confirm it writes warnings to stdout/stderr.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/test_migrate_outputs.py
git commit -m "test(shield): CLI logs collision discards visibly"
```

---

## Section C: Dirty-tree warn-and-confirm

When `--apply` is invoked against a source tree with uncommitted changes, prior versions of overwritten files won't be recoverable from git. Warn the user and require explicit confirmation.

### Task C1: Detect uncommitted changes under `--root`

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
from migrate_outputs import git_dirty_paths  # type: ignore[import-not-found]


def test_git_dirty_paths_clean_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "a.md").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    assert git_dirty_paths(tmp_path) == []


def test_git_dirty_paths_with_uncommitted(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "a.md").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "b.md").write_text("b")  # untracked
    dirty = git_dirty_paths(tmp_path)
    assert "b.md" in [d.split()[-1] for d in dirty]


def test_git_dirty_paths_non_git_returns_none(tmp_path: Path) -> None:
    # No git init at all
    assert git_dirty_paths(tmp_path) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_git_dirty_paths_clean_repo test_migrate_outputs.py::test_git_dirty_paths_with_uncommitted test_migrate_outputs.py::test_git_dirty_paths_non_git_returns_none -v`
Expected: FAIL — `git_dirty_paths` not defined.

- [ ] **Step 3: Implement `git_dirty_paths`**

Append to `shield/scripts/migrate_outputs.py`:

```python
def git_dirty_paths(root: Path) -> list[str] | None:
    """Return a list of dirty git paths (porcelain output lines) under `root`.

    Returns:
        [] if the tree is git-tracked and clean.
        [non-empty list of paths] if there are uncommitted changes.
        None if `root` is not inside a git repo (no git tracking to consult).
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        # Not a git repo, or git unavailable
        return None
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    return lines
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): detect uncommitted changes under migration --root"
```

---

### Task C2: Confirmation flow on `--apply` with dirty tree

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
def test_apply_with_dirty_tree_aborts_without_yes(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    feature = tmp_path / "f"
    _make_tree(feature, ["research/1-foo/findings.md"])
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    # Now create dirt
    (tmp_path / "untracked.md").write_text("dirty")

    # No --yes, no stdin input → must abort
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"),
         "--root", str(tmp_path), "--apply"],
        capture_output=True, text=True, check=False,
        input="",  # empty stdin → no confirmation
    )
    assert result.returncode != 0
    assert "dirty" in (result.stdout + result.stderr).lower() or \
           "uncommitted" in (result.stdout + result.stderr).lower()
    # Migration must not have happened
    assert (feature / "research/1-foo/findings.md").exists()
    assert not (feature / "research.md").exists()


def test_apply_with_dirty_tree_proceeds_with_yes(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    feature = tmp_path / "f"
    _make_tree(feature, ["research/1-foo/findings.md"])
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "untracked.md").write_text("dirty")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "migrate_outputs.py"),
         "--root", str(tmp_path), "--apply", "--yes"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (feature / "research.md").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py::test_apply_with_dirty_tree_aborts_without_yes test_migrate_outputs.py::test_apply_with_dirty_tree_proceeds_with_yes -v`
Expected: FAIL — no `--yes`, no dirty check.

- [ ] **Step 3: Wire the confirmation into the CLI**

In `shield/scripts/migrate_outputs.py`, edit the `main` function: add a `--yes` argument, and before any apply work, call `git_dirty_paths(output_dir)`. If non-empty and not `args.yes`, print a warning naming the dirty paths and read a `y/N` response from stdin. Abort with non-zero exit if no `y`.

```python
def main(argv: list[str] | None = None) -> int:
    import argparse, json

    parser = argparse.ArgumentParser(...)
    # ... existing args ...
    parser.add_argument("--yes", action="store_true",
                        help="Skip dirty-tree confirmation prompt (for scripted use)")
    args = parser.parse_args(argv)

    output_dir = Path(args.root).resolve()
    # ... existing existence check ...

    if args.apply:
        dirty = git_dirty_paths(output_dir)
        if dirty:
            print("WARNING: source tree has uncommitted changes:", file=sys.stderr)
            for ln in dirty[:10]:
                print(f"  {ln}", file=sys.stderr)
            if len(dirty) > 10:
                print(f"  ... and {len(dirty) - 10} more", file=sys.stderr)
            print(
                "If migration discards older versions on collision, the older "
                "content will NOT be recoverable from git history.",
                file=sys.stderr,
            )
            if not args.yes:
                print("Proceed anyway? [y/N] ", end="", file=sys.stderr, flush=True)
                resp = sys.stdin.readline().strip().lower()
                if resp != "y":
                    print("Aborted.", file=sys.stderr)
                    return 3

    # ... rest of existing logic ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): dirty-tree warn-and-confirm on migrate --apply (--yes to bypass)"
```

---

## Section D: Expanded legacy pattern coverage

Eight more pattern groups discovered in the flow-research tree. Each gets its own task to keep PRs / commits granular.

### Task D1: `prd/{N}-{slug}/prd.md` → `prd.md`

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

Append to `test_migrate_outputs.py`:

```python
@pytest.mark.parametrize("old,new", [
    ("prd/1-foo/prd.md",          "prd.md"),
    ("prd/3-bar-baz-qux/prd.md",  "prd.md"),
])
def test_map_prd_md(old: str, new: str) -> None:
    assert map_legacy_path(old) == new
```

- [ ] **Step 2: Verify failure, add pattern**

Run the test (FAIL). Then in `migrate_outputs.py`:

```python
_PRD_MD = re.compile(r"^prd/\d+-[^/]+/prd\.md$")

# In map_legacy_path:
if _PRD_MD.match(relpath):
    return "prd.md"
```

- [ ] **Step 3: Re-run; commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): migrate prd/{N}-{slug}/prd.md -> prd.md"
```

---

### Task D2: `prd/{N}-{slug}/prd.html` → `outputs/prd.html`

Follow Task D1's pattern.

```python
@pytest.mark.parametrize("old,new", [
    ("prd/1-foo/prd.html", "outputs/prd.html"),
])
def test_map_prd_html(old: str, new: str) -> None:
    assert map_legacy_path(old) == new
```

Add regex `_PRD_HTML = re.compile(r"^prd/\d+-[^/]+/prd\.html$")`, branch to `"outputs/prd.html"`. Commit `feat(shield): migrate prd/{N}-{slug}/prd.html -> outputs/prd.html`.

---

### Task D3: `prd/{N}-{slug}/prd.meta.json` → `prd.meta.json`

Test, add pattern, commit. Resolved target: `"prd.meta.json"`. Add `prd.meta.json` to `KNOWN_ROOT_FILES` so subsequent re-runs don't warn about it.

Commit: `feat(shield): migrate prd/{N}-{slug}/prd.meta.json -> prd.meta.json`.

---

### Task D4: `plan/{N}-{slug}/plan.html` → `outputs/plan.html`

Same pattern. Test, regex `_PLAN_HTML`, target `"outputs/plan.html"`, commit `feat(shield): migrate plan/{N}-{slug}/plan.html -> outputs/plan.html`.

---

### Task D5: Date derivation helper (mtime-based)

Review folders in the new schema use `YYYY-MM-DD[_N]`. Old `prd-review/{N}-{slug}/` etc. don't encode a date — derive it from the folder's mtime.

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime, timezone

from migrate_outputs import derive_review_date  # type: ignore[import-not-found]


def test_derive_review_date_from_dir_mtime(tmp_path: Path) -> None:
    d = tmp_path / "prd-review" / "1-foo"
    d.mkdir(parents=True)
    (d / "summary.md").write_text("x")
    # Set the dir mtime explicitly
    ts = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    os.utime(d, (ts, ts))
    assert derive_review_date(d) == "2026-04-30"
```

- [ ] **Step 2: Implement**

```python
from datetime import datetime, timezone


def derive_review_date(legacy_review_dir: Path) -> str:
    """Return YYYY-MM-DD derived from the directory's mtime (UTC)."""
    ts = legacy_review_dir.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
```

- [ ] **Step 3: Run, commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): derive_review_date helper (mtime-based, UTC)"
```

---

### Task D6: `prd-review/{N}-{slug}/*` → `reviews/prd/{date}[_N]/*`

This is the first task that has multiple files-per-legacy-folder *and* uses date derivation. `map_legacy_path` (a pure pathname function) can't compute mtime — we need to extend it OR teach `plan_moves` to handle review-folder bundles specially.

Simpler approach: keep `map_legacy_path` pure for non-review patterns; add a `plan_review_moves(feature_dir)` helper that handles `prd-review/`, `plan-review/` directories specifically. `plan_moves` calls both and merges results.

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the failing test**

```python
def test_prd_review_folder_migrates_to_dated_dir(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    rev = feature / "prd-review" / "1-myslug"
    rev.mkdir(parents=True)
    (rev / "summary.md").write_text("s")
    (rev / "enhanced-prd.md").write_text("e")
    (rev / "source-prd.md").write_text("src")
    (rev / "review-comments.json").write_text("{}")
    detailed = rev / "detailed"
    detailed.mkdir()
    (detailed / "agile-coach.md").write_text("a")
    (detailed / "tech-lead-reviewer.md").write_text("t")

    ts = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    os.utime(rev, (ts, ts))

    moves, _warnings = plan_moves(feature)
    dst_paths = {dst.relative_to(feature).as_posix() for _src, dst in moves}

    expected = {
        "reviews/prd/2026-04-30/summary.md",
        "reviews/prd/2026-04-30/enhanced-prd.md",
        "reviews/prd/2026-04-30/source-prd.md",
        "reviews/prd/2026-04-30/review-comments.json",
        "reviews/prd/2026-04-30/detailed/agile-coach.md",
        "reviews/prd/2026-04-30/detailed/tech-lead-reviewer.md",
    }
    assert expected.issubset(dst_paths)
```

- [ ] **Step 2: Implement**

Add `_plan_review_folder_moves(feature_dir, review_type, legacy_dir_name)` that walks each `{legacy_dir_name}/{N}-{slug}/` folder and produces moves to `reviews/{review_type}/{date}[_N]/...`. Call it twice in `plan_moves` (for `prd-review` and `plan-review`).

Handle same-day `_counter` by tracking dates already seen across multiple `prd-review/{N}-{slug}/` folders within the same feature: first occurrence on a date → no suffix, second → `_2`, etc.

Sketch:

```python
def _plan_review_folder_moves(
    feature_dir: Path, review_type: str, legacy_dir_name: str
) -> list[tuple[Path, Path]]:
    legacy_root = feature_dir / legacy_dir_name
    if not legacy_root.is_dir():
        return []
    seen_dates: dict[str, int] = {}
    out: list[tuple[Path, Path]] = []
    for run_dir in sorted(p for p in legacy_root.iterdir() if p.is_dir()):
        # Only legacy {N}-{slug} pattern
        if not re.match(r"^\d+-", run_dir.name):
            continue
        date = derive_review_date(run_dir)
        seen_dates[date] = seen_dates.get(date, 0) + 1
        counter = "" if seen_dates[date] == 1 else f"_{seen_dates[date]}"
        new_run = feature_dir / "reviews" / review_type / f"{date}{counter}"
        for src in run_dir.rglob("*"):
            if not src.is_file():
                continue
            rel_inside = src.relative_to(run_dir).as_posix()
            out.append((src, new_run / rel_inside))
    return out
```

Then in `plan_moves`, after the existing per-file scan:

```python
for review_type, legacy_dir_name in [("prd", "prd-review"), ("plan", "plan-review")]:
    raw_moves.extend(_plan_review_folder_moves(feature_dir, review_type, legacy_dir_name))
```

And exclude files inside `prd-review/` / `plan-review/` directories from the per-file scan (otherwise the "unrecognized nested file" warning fires on them). Add a `_LEGACY_REVIEW_DIRS = {"prd-review", "plan-review"}` and skip them in the rglob loop.

- [ ] **Step 3: Run all tests; commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "feat(shield): migrate prd-review/{N}/ -> reviews/prd/{date}[_N]/"
```

---

### Task D7: `plan-review/{N}-{slug}/*` → `reviews/plan/{date}[_N]/*`

Already enabled by Task D6's `_plan_review_folder_moves` call. Add a test that exercises it specifically:

```python
def test_plan_review_folder_migrates_to_dated_dir(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    rev = feature / "plan-review" / "1-foo"
    rev.mkdir(parents=True)
    (rev / "summary.md").write_text("s")
    (rev / "enhanced-plan.md").write_text("e")
    detailed = rev / "detailed"
    detailed.mkdir()
    (detailed / "backend-engineer.md").write_text("b")

    ts = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    os.utime(rev, (ts, ts))

    moves, _ = plan_moves(feature)
    dst_paths = {dst.relative_to(feature).as_posix() for _src, dst in moves}
    expected = {
        "reviews/plan/2026-05-21/summary.md",
        "reviews/plan/2026-05-21/enhanced-plan.md",
        "reviews/plan/2026-05-21/detailed/backend-engineer.md",
    }
    assert expected.issubset(dst_paths)
```

Run, confirm it passes, commit `test(shield): assert plan-review folder migration`.

---

### Task D8: Same-day counter at migration time

Two legacy `prd-review/` folders both with mtime on the same date should produce `reviews/prd/{date}/` and `reviews/prd/{date}_2/`.

```python
def test_same_day_review_folders_get_counter(tmp_path: Path) -> None:
    feature = tmp_path / "f"
    for i, slug in enumerate(["1-first", "2-second"]):
        d = feature / "prd-review" / slug
        d.mkdir(parents=True)
        (d / "summary.md").write_text(f"r{i}")
        ts = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()
        os.utime(d, (ts, ts))

    moves, _ = plan_moves(feature)
    dst_dirs = {dst.parent.relative_to(feature).as_posix() for _, dst in moves}
    assert "reviews/prd/2026-04-30" in dst_dirs
    assert "reviews/prd/2026-04-30_2" in dst_dirs
```

Run — should already pass thanks to D6's `seen_dates` counter logic. If not, fix. Commit `test(shield): assert same-day review folders get _N counter at migration`.

---

### Task D9: Integration test on the realistic fixture

**Files:**
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Write the test**

```python
def test_realistic_tree_full_migration(tmp_path: Path) -> None:
    feature = _make_realistic_tree(tmp_path)
    moves, warnings = plan_moves(feature)
    dst_paths = {dst.relative_to(feature).as_posix() for _, dst in moves}

    # Source files we expect to be moved (not exhaustive; spot-check critical ones)
    assert "prd.md" in dst_paths
    assert "outputs/prd.html" in dst_paths
    assert "prd.meta.json" in dst_paths
    assert "outputs/plan-architecture.html" in dst_paths
    assert "outputs/plan.html" in dst_paths

    # Reviews migrated under dated dirs
    review_dirs = {p for p in dst_paths if p.startswith("reviews/")}
    assert any("reviews/prd/" in p and "/summary.md" in p for p in review_dirs)
    assert any("reviews/plan/" in p and "/detailed/architecture-reviewer.md" in p for p in review_dirs)

    # Multiple research → exactly one research.md, with discard warning
    research_targets = [p for p in dst_paths if p == "research.md"]
    assert len(research_targets) == 1
    assert any("discarded on collision" in w for w in warnings)

    # plans/product-note.md is unrecognized → warning
    assert any("plans/product-note.md" in w for w in warnings)
```

- [ ] **Step 2: Add `_make_realistic_tree` helper** (the fixture from the "Reference test fixture" section at the top of this plan) into `test_migrate_outputs.py`.

- [ ] **Step 3: Run all tests**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add shield/scripts/test_migrate_outputs.py
git commit -m "test(shield): integration test on realistic flow-research-shaped tree"
```

---

## Section E: `verify_migration.py` ergonomics

### Task E1: Add `--keep-on-failure` flag

When the script fails (data-loss check, structural check), keep the temp dir for debugging instead of cleaning up.

**Files:**
- Modify: `shield/scripts/verify_migration.py`

- [ ] **Step 1: Add the flag and conditional cleanup**

In `verify_migration.py`'s `main` (or wherever the temp-dir cleanup happens):

```python
parser.add_argument("--keep-on-failure", action="store_true",
                    help="Leave the temp dir in place on failure (for inspection)")
```

Wrap the cleanup branch so it only fires on success:

```python
if exit_code != 0 and args.keep_on_failure:
    print(f"[--keep-on-failure] preserved temp tree at: {temp_dir}", file=sys.stderr)
elif exit_code != 0 or not args.keep:
    shutil.rmtree(temp_dir, ignore_errors=True)
```

- [ ] **Step 2: Verify it works**

Run a deliberately-broken verification (point `--source` at a tree with a collision); confirm the temp dir survives.

```bash
TEMP=$(mktemp -d) && cp -R /Users/apple/projects/aspora/flow-research/docs/shield "$TEMP/shield" && uv run --with pyyaml shield/scripts/verify_migration.py --source "$TEMP/shield" --keep-on-failure 2>&1 | grep "preserved"
```

Expected: a line like `[--keep-on-failure] preserved temp tree at: /var/folders/…/shield-verify-…`.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/verify_migration.py
git commit -m "feat(shield): verify_migration --keep-on-failure preserves temp tree"
```

---

## Section F: Strengthen the cutover eval pattern (cross-plan edit)

The Phase 3 cutover plan's Reference task currently says the eval "asserts files at declared paths exist." That's necessary but not sufficient — a command can also silently write to *undeclared* paths. Tighten to: the set of files written matches the set of declared paths exactly.

### Task F1: Update the cutover plan's Reference task

**Files:**
- Modify: `docs/superpowers/plans/2026-05-22-shield-output-structure-cutover.md`

- [ ] **Step 1: Find the Reference task's "Step 1: RED — write the failing eval" section**

Locate the bullet that describes what the eval asserts. Currently it says (in summary): "the assertion section lists each registry path name and the substituted concrete path that should exist on disk."

- [ ] **Step 2: Replace with a stricter assertion**

Change the assertion to:

> After running the command, the eval captures the full set of files written under `$output_dir` (e.g. via `find $output_dir -type f`). It then asserts:
>   - Every declared output path is present.
>   - No file is present that is not declared (allowing for `manifest.json` and `outputs/` rendered artifacts, which are derived).
>
> A command that silently writes to an undeclared path fails its eval. This is the load-bearing check against future registry drift — lint catches declaration errors, but only the eval catches the "command wrote files it didn't tell anyone about" case.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-05-22-shield-output-structure-cutover.md
git commit -m "docs(shield): cutover eval asserts exact written-paths set"
```

---

## Section G: Final integration

### Task G1: All tests + lint + dry-run sanity check

- [ ] **Step 1: Run all migration tests**

Run: `cd /Users/apple/projects/infraspecdev/tesseract/shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py test_lint_output_paths.py test_migrate_outputs.py -v`
Expected: all pass. Test count should be substantially higher than the foundations PR's 35 — likely 50+ depending on how many parametrized cases land in Section D.

- [ ] **Step 2: Lint clean**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0, "Lint clean: registry + N assets".

- [ ] **Step 3: Dry-run on flow-research's tree (the original failing case)**

Run: `uv run --with pyyaml shield/scripts/migrate_outputs.py --root /Users/apple/projects/aspora/flow-research/docs/shield 2>&1 | tail -40`
Expected:
- `moves: 4 → much more` — every legacy file now has a destination
- `warnings`: only `plans/product-note.md` (the genuine orphan) and the research discard warning
- Re-running produces ~0 moves (idempotence)

- [ ] **Step 4: verify_migration on the same tree, with --keep-on-failure for safety**

Run: `uv run --with pyyaml shield/scripts/verify_migration.py --source /Users/apple/projects/aspora/flow-research/docs/shield --keep-on-failure`
Expected: PASS. Hash-integrity check survives because the collision discard is now intentional + logged (no silent data loss).

- [ ] **Step 5: No commit — this is verification.**

---

## Definition of Done

- [ ] Registry has `prd_meta_json`, `source_prd`, `review_comments_json`, `code_review_changes`; spec §5.1 amended.
- [ ] `plan_moves` resolves destination collisions latest-mtime-wins, with discard warnings.
- [ ] `migrate_outputs.py --apply` warns on dirty source tree; `--yes` bypasses; abort on no/empty confirmation.
- [ ] `map_legacy_path` (or its companion `_plan_review_folder_moves`) covers: `prd/`, `prd-review/`, `plan-review/`, `plan/{N}/plan.html`, plus the 3 new artifact files inside those folders.
- [ ] Review folders migrate to mtime-derived `YYYY-MM-DD[_N]` dirs with same-day counter logic.
- [ ] `verify_migration.py --keep-on-failure` preserves temp tree for debugging.
- [ ] Cutover plan's Reference task tightened to assert exact written-paths set.
- [ ] All resolver/lint/migration tests pass (≥50).
- [ ] Dry-run on flow-research's `docs/shield/` produces full coverage; only legitimate orphans (`plans/product-note.md`) warn.
- [ ] `verify_migration.py` against flow-research passes.

---

## Why this fits between Phase 3 and Phase 4

- **Independent of Phase 3 cutover:** the cutover edits asset frontmatter and bodies; this plan edits scripts. No file overlap until the small cross-plan edit in Section F (a docs change to the cutover plan, idempotent).
- **Prerequisite for Phase 4 (live migration):** Phase 4 runs `--apply` against `docs/shield/`. If we don't ship this hardening first, Phase 4 either runs on the unverified script (data-loss risk on collision) or runs on the tesseract tree alone (which has no collisions, so it'd "work" but hide the bug for downstream consumers).

Phases 3 and this plan can be merged in either order. Phase 4 must come after both.
