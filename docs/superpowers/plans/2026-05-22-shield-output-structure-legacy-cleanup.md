# Shield Output Structure — Legacy Cleanup (Phase 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `legacy_*` registry entries and the migration script's regex patterns now that the live tree is fully migrated and no asset references legacy paths.

**Architecture:** Pure deletion of backwards-compatibility code. Tests prove that removal does not break anything: the lint and migration tests should still pass with `legacy_*` entries gone, and a final whole-repo lint should be clean.

**Tech Stack:** None new — just removing code added in earlier phases.

**Scope:** Phase 5 of design spec.

**Prerequisites:**
- Phases 1–4 merged. Specifically:
  - Foundations plan delivered the registry + scripts.
  - Cutover plan migrated every asset to reference non-`legacy_*` registry names.
  - Live migration plan moved all existing feature folders to the new layout.
- `git status` shows a clean working tree.
- `find docs/shield -type d -name "[0-9]-*"` returns empty.

**Out of scope:**
- Any new functionality.

---

## Task L1: Verify nothing references `legacy_*`

- [ ] **Step 1: Search the repo for `legacy_` references**

Run: `grep -rE "legacy_(research_dir|plan_dir)" /Users/apple/projects/infraspecdev/tesseract/shield/ /Users/apple/projects/infraspecdev/tesseract/docs/ 2>/dev/null | grep -v ".git"`
Expected output: only matches in
- `shield/schema/output-paths.yaml` (the entries themselves)
- `shield/scripts/migrate_outputs.py` (the regex patterns)
- `shield/scripts/test_path_resolver.py` (the `test_legacy_paths_resolve` test)
- `shield/scripts/test_migrate_outputs.py` (legacy fixture test paths)
- Design spec / plans (documentation references — OK to keep)

If any asset under `shield/commands/`, `shield/skills/`, or `shield/agents/` matches, STOP — the cutover plan was incomplete. Go back and finish that asset before proceeding.

- [ ] **Step 2: Confirm migration is idempotent on the live tree**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/migrate_outputs.py --root docs/shield`
Expected: `dry-run: 0 moves, M warnings` (M ≥ 0, just unrecognized-file warnings).

If any moves are listed, STOP — Phase 4 was incomplete.

- [ ] **Step 3: Create a fresh branch**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git checkout -b feat/shield-legacy-cleanup`

---

## Task L2: Remove `legacy_*` entries from the registry

**Files:**
- Modify: `shield/schema/output-paths.yaml`

- [ ] **Step 1: Remove the legacy block from the registry**

Open `shield/schema/output-paths.yaml`. Delete the `Legacy (pre-redesign)` section — the `legacy_research_dir` and `legacy_plan_dir` entries — and the corresponding lines in the `variables:` block (`n:` and `slug:` markers tagged "legacy only").

Also remove the explanatory comment line `# Legacy (pre-redesign). Removed in Phase 5 (see design §10).`.

After this edit, the registry should contain only the active path entries from spec §5.1.

- [ ] **Step 2: Update the resolver legacy test**

Open `shield/scripts/test_path_resolver.py`. Delete the function `test_legacy_paths_resolve` entirely — it references registry entries that no longer exist.

- [ ] **Step 3: Run the resolver tests**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py -v`
Expected: all remaining tests pass; the deleted test is gone from the output.

- [ ] **Step 4: Run lint**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0 — no asset references `legacy_*`, so removing those entries from the registry doesn't surface any lint errors.

- [ ] **Step 5: Commit**

```bash
git add shield/schema/output-paths.yaml shield/scripts/test_path_resolver.py
git commit -m "chore(shield): remove legacy_* registry entries (Phase 5)"
```

---

## Task L3: Remove legacy patterns from the migration script

**Files:**
- Modify: `shield/scripts/migrate_outputs.py`
- Modify: `shield/scripts/test_migrate_outputs.py`

- [ ] **Step 1: Decide what to keep vs. remove**

The migration script's regex patterns (`_RESEARCH_FINDINGS`, `_RESEARCH_TRANSCRIPT`, `_PLAN_ARCH_HTML`) and the `map_legacy_path` function are what enabled Phase 4. They're no longer needed for future operation, but removing them deletes a tool that future consumers may run if they discover an unmigrated legacy tree.

Two options:
- **Option A (remove entirely):** delete `map_legacy_path`, the regex patterns, and the migration tests. Smaller maintenance surface. Future legacy users would need to write their own script.
- **Option B (keep tool, drop default invocation):** keep `map_legacy_path` and its tests, but remove the script from any default workflow. Default behavior unchanged: `migrate_outputs.py` runs only when explicitly invoked.

**Recommended: Option B** — the script is small, the tests are isolated, and keeping it means new consumers who clone the plugin and have a legacy tree can still run the migration. Phase 5's job is to drop the dead `legacy_*` registry entries, not to delete useful tooling.

If choosing Option A, follow the strikethrough steps; if Option B, skip Task L3.

- [ ] **Step 2 (Option A only): Remove the regex patterns and function**

Open `shield/scripts/migrate_outputs.py`. Delete:
- The three regex constants (`_RESEARCH_FINDINGS`, `_RESEARCH_TRANSCRIPT`, `_PLAN_ARCH_HTML`).
- The `map_legacy_path` function.
- The call site inside `plan_moves`. Replace with `target = None`.

- [ ] **Step 3 (Option A only): Update tests**

Open `shield/scripts/test_migrate_outputs.py`. Delete tests that reference legacy paths: `test_map_legacy_path` and any test in `test_plan_moves_typical_feature_tree` / `test_apply_moves_*` that depends on a legacy mapping.

- [ ] **Step 4 (Option A only): Run remaining tests**

Run: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_migrate_outputs.py -v`
Expected: all remaining tests pass.

- [ ] **Step 5 (Option A only): Commit**

```bash
git add shield/scripts/migrate_outputs.py shield/scripts/test_migrate_outputs.py
git commit -m "chore(shield): remove legacy migration patterns (Phase 5 / Option A)"
```

---

## Task L4: Whole-repo verification

- [ ] **Step 1: Run lint**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0.

- [ ] **Step 2: Run all foundation tests**

Run: `cd /Users/apple/projects/infraspecdev/tesseract/shield/scripts && uv run --with pyyaml --with pytest pytest test_path_resolver.py test_lint_output_paths.py test_migrate_outputs.py -v`
Expected: all pass. Test count is lower than after the foundations plan by however many `legacy_*` tests were deleted.

- [ ] **Step 3: Run cutover evals**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && bash shield/evals/run-evals.sh shield/evals/output-paths/*.eval.md`
Expected: all PASS — none of these evals reference `legacy_*`, so removing the entries shouldn't break anything.

- [ ] **Step 4: Confirm `find` shows no numbered-run folders**

Run: `find /Users/apple/projects/infraspecdev/tesseract/docs/shield -type d -name "[0-9]-*"`
Expected: empty.

- [ ] **Step 5: No commit needed** — this is verification.

---

## Task L5: Update marketplace version and changelog

The Shield plugin's version lives in `.claude-plugin/marketplace.json` (per repo CLAUDE.md). After all five phases land, bump the version.

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `shield/pyproject.toml` if it has a version field (check first)

- [ ] **Step 1: Inspect current version**

Run: `grep -E '"version"' /Users/apple/projects/infraspecdev/tesseract/.claude-plugin/marketplace.json`
Expected: a line like `"version": "X.Y.Z"`.

- [ ] **Step 2: Bump the version**

Edit `.claude-plugin/marketplace.json`. Increment the minor version (this is a structural change to where artifacts live — minor bump is appropriate; major bump if the team wants to signal a breaking change for downstream consumers).

For example, `2.18.1` → `2.19.0`.

- [ ] **Step 3: Check pyproject.toml**

Run: `find /Users/apple/projects/infraspecdev/tesseract/shield -name "pyproject.toml" -not -path "*/adapters/*"`
Expected: usually no top-level `shield/pyproject.toml` (only adapter ones). If there is one and it has a version, sync it.

- [ ] **Step 4: Commit version bump**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump version after output structure redesign"
```

---

## Definition of Done

- [ ] No `legacy_*` entries in `shield/schema/output-paths.yaml`.
- [ ] No `legacy_*` references in `shield/commands/`, `shield/skills/`, or `shield/agents/`.
- [ ] If Option A chosen in L3: `map_legacy_path` and its regex patterns removed from `shield/scripts/migrate_outputs.py`; if Option B: tool kept, no edits.
- [ ] `uv run --with pyyaml shield/scripts/lint_output_paths.py --root .` exits 0.
- [ ] All resolver, lint, and migration tests pass.
- [ ] Marketplace version bumped in `.claude-plugin/marketplace.json`.
- [ ] All changes are on a feature branch ready for PR.

---

## Wrap-up

After this plan lands, the five-phase redesign is complete:

1. ✅ Foundations: registry + resolver + lint + migration script.
2. ✅ (Merged into Phase 1 plan): migration script tested in isolation.
3. ✅ Cutover: every asset references registry path names.
4. ✅ Live migration: `docs/shield/` reflects the new layout.
5. ✅ Cleanup: `legacy_*` entries gone, version bumped.

Future structure changes (renames, reorganization) require editing only `shield/schema/output-paths.yaml` plus the affected assets' `outputs:` lists — never editing literal path templates scattered across 19 commands.
