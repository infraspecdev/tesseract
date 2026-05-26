# Shield Output Structure — Live Migration (Phase 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run `migrate_outputs.py --apply` against the real `docs/shield/` tree, commit the resulting flat layout, and verify nothing downstream broke.

**Architecture:** This plan is a careful one-shot apply of the migration script built in the foundations plan, against a live repository. Most of the work is verification — confirming what the script will move, applying it, and asserting the new tree shape is correct. No new code is written.

**Tech Stack:** Existing migration script (`shield/scripts/migrate_outputs.py`), git, basic shell tools.

**Scope:** Phase 4 of design spec.

**Prerequisites:**
- Foundations plan (Phases 1+2) merged: `shield/scripts/migrate_outputs.py` exists and is tested.
- Cutover plan (Phase 3) merged: all assets reference registry paths. (Optional but strongly recommended — running the migration before cutover leaves assets pointing at paths that no longer exist.)
- `git status` shows a clean working tree.
- A current backup or a fresh branch — this plan moves files in bulk.

**Out of scope:**
- Removing `legacy_*` registry entries or migration script patterns (Phase 5 plan).
- Editing any command, skill, or agent.

---

## Task M1: Pre-flight dry-run

- [ ] **Step 1: Verify clean working tree**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git status`
Expected: working tree clean. If anything is staged or modified, stop and reconcile before proceeding.

- [ ] **Step 2: Create a fresh branch for the migration**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git checkout -b feat/shield-live-output-migration`

- [ ] **Step 3: Run migration in dry-run mode and capture output**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/migrate_outputs.py --root docs/shield 2>&1 | tee /tmp/shield-migration-dryrun.txt`
Expected: exit 0. Output lists `would move:` lines plus any `warning:` lines.

- [ ] **Step 4: Review the dry-run output**

Open `/tmp/shield-migration-dryrun.txt` and confirm:
- Every `would move:` line maps a real legacy file to its expected new location.
- The set of warnings is expected (e.g. `pm-restructure-v0-20260521/handoff.md: unrecognized file at feature root, left in place`).
- No surprising moves — nothing under `docs/shield/` that should stay flat is being moved.

If any line is surprising, STOP. Investigate by reading the source file at the listed old location, then either:
(a) extend `map_legacy_path` in `shield/scripts/migrate_outputs.py` to cover the new case (with a test, in a separate commit on this branch); or
(b) document the file as a known exception in the migration plan's "Known exceptions" section below.

- [ ] **Step 5: Verify filesystem is unchanged**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git status`
Expected: still clean — dry-run does not touch the filesystem.

- [ ] **Step 6: No commit yet** — this is verification.

---

## Task M2: Apply migration

- [ ] **Step 1: Run migration with --apply**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/migrate_outputs.py --root docs/shield --apply 2>&1 | tee /tmp/shield-migration-apply.txt`
Expected: exit 0. Output lists `moving:` lines (not `would move:`) and ends with `wrote manifest: docs/shield/manifest.json` plus a summary line `applied: N moves, M warnings`.

- [ ] **Step 2: Inspect what changed**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git status docs/shield`
Expected: a mix of:
- Deleted paths under old numbered-run folders (e.g. `devcontainer-implement-20260518/research/1-claude-implement-isolation/findings.md`).
- New paths at flat locations (e.g. `devcontainer-implement-20260518/research.md`).
- New `docs/shield/manifest.json`.

- [ ] **Step 3: Spot-check a moved file**

Pick one moved file (e.g. `devcontainer-implement-20260518/research.md`) and a sibling under the old path:

Run: `diff <(cat /tmp/shield-migration-apply.txt | grep "moving:" | head -1) <(echo "moving: devcontainer-implement-20260518/research/1-claude-implement-isolation/findings.md -> devcontainer-implement-20260518/research.md")`
(Adjust the right-hand side based on actual content.)

Or simpler: open the new file and confirm content matches what was at the old location.

Run: `head -20 /Users/apple/projects/infraspecdev/tesseract/docs/shield/devcontainer-implement-20260518/research.md`
Expected: content of the original `findings.md`.

- [ ] **Step 4: Verify manifest.json is v2**

Read: `/Users/apple/projects/infraspecdev/tesseract/docs/shield/manifest.json`
Expected: top-level `"schema_version": 2`, `"features": [...]` array with one entry per feature folder.

---

## Task M3: Post-migration verification

- [ ] **Step 1: Confirm no legacy numbered folders remain**

Run: `find /Users/apple/projects/infraspecdev/tesseract/docs/shield -type d -name "[0-9]-*"`
Expected: no output (no folders matching `<digit>-<slug>` pattern).

- [ ] **Step 2: Verify expected new structure**

Run: `find /Users/apple/projects/infraspecdev/tesseract/docs/shield -maxdepth 2 -type f | sort`
Expected: each feature folder has at most these files at its root: `README.md`, `research.md`, `prd.md`, `plan.json`, `plan.md`, `plan-architecture.md`, `.session-transcript.md`, plus an `outputs/` subdir and possibly `reviews/`.

- [ ] **Step 3: Run lint on the now-migrated tree**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/lint_output_paths.py --root .`
Expected: exit 0.

- [ ] **Step 4: Re-run migration to confirm idempotence**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && uv run --with pyyaml shield/scripts/migrate_outputs.py --root docs/shield`
Expected: `dry-run: 0 moves, M warnings` (the same warnings as before — unmigrated unknown files like `handoff.md` still warn). Zero moves means the tree is fully migrated.

---

## Task M4: Commit the migration

- [ ] **Step 1: Review the diff**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git status docs/shield && echo "---" && git diff --stat docs/shield`
Expected: a long list of renames and the new `manifest.json`. Renames (vs delete+add) should dominate — git's rename detection should pick up most of the moved files since their content is identical.

- [ ] **Step 2: Stage the changes**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git add docs/shield`

- [ ] **Step 3: Confirm staged content**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git status`
Expected: all changes under `docs/shield/` staged, working tree clean elsewhere.

- [ ] **Step 4: Commit**

```bash
cd /Users/apple/projects/infraspecdev/tesseract && git commit -m "$(cat <<'EOF'
chore(shield): apply live output structure migration

Runs shield/scripts/migrate_outputs.py --apply against docs/shield/.
Moves all existing feature artifacts from the legacy numbered-run layout
to the new flat per-feature layout defined in
docs/superpowers/specs/2026-05-22-shield-output-structure-design.md.

Regenerates docs/shield/manifest.json with schema_version: 2.

Idempotent — re-running migrate_outputs.py produces zero moves after this
commit.
EOF
)"
```

- [ ] **Step 5: Verify commit**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git log -1 --stat | head -50`
Expected: commit summary shows all the file renames and the manifest.json addition.

---

## Known exceptions

These files are intentionally left in place by the migration:

- `pm-restructure-v0-20260521/handoff.md` — ad-hoc handoff doc, not part of the new schema. Kept at feature root with no migration mapping.
- Anything under `docs/superpowers/` — out of scope (different directory tree).

If new exceptions emerge during M1 review, append them here and to the migration script's known-warnings list before applying.

---

## Rollback

If the live migration produces unexpected results:

- [ ] **Step 1: Revert the commit**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git reset --hard HEAD~1`
Expected: tree restored to pre-migration state.

- [ ] **Step 2: Delete the branch**

Run: `cd /Users/apple/projects/infraspecdev/tesseract && git checkout main && git branch -D feat/shield-live-output-migration`

- [ ] **Step 3: Investigate**

Open `/tmp/shield-migration-apply.txt` (kept from M2 step 1) and identify the surprising move(s). Fix `map_legacy_path` or `plan_moves` in the foundations plan codebase, with tests, then restart this plan from M1.

---

## Definition of Done

- [ ] `docs/shield/` contains no numbered-run subfolders (`<digit>-<slug>/`).
- [ ] `docs/shield/manifest.json` exists with `schema_version: 2`.
- [ ] `uv run --with pyyaml shield/scripts/lint_output_paths.py --root .` exits 0.
- [ ] Re-running `migrate_outputs.py` produces zero moves.
- [ ] The migration is committed on a feature branch ready for PR.

---

## Follow-up

- **Phase 5 plan** (`2026-05-22-shield-output-structure-legacy-cleanup.md`) — remove `legacy_*` registry entries and migration script patterns.
