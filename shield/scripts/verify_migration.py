"""End-to-end smoke test for migrate_outputs.py against a copy of an output tree.

Copies the source tree to a temp dir and exercises the full migration cycle:
dry-run, apply, manifest verification, idempotence, no-data-loss. Source tree
is never touched.

Runnable: `uv run --with pyyaml shield/scripts/verify_migration.py [--source DIR] [--keep]`
  --source  output tree to verify against (default: docs/shield/ in repo).
  --keep    leave the temp dir in place on success (for manual inspection).

When --source is the default repo tree, also asserts known expected moves.
For custom --source dirs, only the structural checks run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_TREE = REPO_ROOT / "docs" / "shield"
MIGRATE_SCRIPT = REPO_ROOT / "shield" / "scripts" / "migrate_outputs.py"

# Known expected moves for the current real tree (as of 2026-05-22).
# Update when new legacy artifacts appear or features are added.
EXPECTED_MOVES = {
    "devcontainer-implement-20260518/research/1-claude-implement-isolation/findings.md":
        "devcontainer-implement-20260518/research.md",
    "devcontainer-implement-20260518/research/1-claude-implement-isolation/transcript.md":
        "devcontainer-implement-20260518/.session-transcript.md",
}

EXPECTED_WARNING_SUBSTRINGS = ["handoff.md"]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _collect_file_hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): _sha256(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def _run_migrate(root: Path, *, apply: bool) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(MIGRATE_SCRIPT), "--root", str(root)]
    if apply:
        cmd.append("--apply")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def verify(tmp_tree: Path, *, check_known_moves: bool) -> list[str]:
    failures: list[str] = []
    before = _collect_file_hashes(tmp_tree)
    print(f"baseline: {len(before)} files in copy")

    # 1. Dry-run runs cleanly. With known source, also asserts expected moves/warnings.
    dry = _run_migrate(tmp_tree, apply=False)
    if dry.returncode != 0:
        failures.append(f"dry-run exited {dry.returncode}: {dry.stderr.strip()}")
    if check_known_moves:
        for old, new in EXPECTED_MOVES.items():
            line = f"would move: {old} -> {new}"
            if line not in dry.stdout:
                failures.append(f"dry-run missing expected move line: {line!r}")
        for needle in EXPECTED_WARNING_SUBSTRINGS:
            if needle not in dry.stdout:
                failures.append(f"dry-run missing warning containing {needle!r}")

    # 2. --apply moves files and writes manifest.
    apply = _run_migrate(tmp_tree, apply=True)
    if apply.returncode != 0:
        failures.append(f"--apply exited {apply.returncode}: {apply.stderr.strip()}")

    if check_known_moves:
        for old, new in EXPECTED_MOVES.items():
            if (tmp_tree / old).exists():
                failures.append(f"source still present after --apply: {old}")
            if not (tmp_tree / new).exists():
                failures.append(f"destination missing after --apply: {new}")
                continue
            # Content preserved bit-for-bit.
            if old in before and before[old] != _sha256(tmp_tree / new):
                failures.append(f"content changed during move: {old} -> {new}")

    # 3. Manifest written with schema_version: 2 or "2.1".
    manifest_path = tmp_tree / "manifest.json"
    if not manifest_path.exists():
        failures.append("manifest.json not created by --apply")
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("schema_version") not in (2, "2.1"):
                failures.append(
                    f"manifest schema_version not in {{2, '2.1'}} (got {manifest.get('schema_version')!r})"
                )
            if not isinstance(manifest.get("features"), list):
                failures.append("manifest missing features list")
        except json.JSONDecodeError as exc:
            failures.append(f"manifest is not valid JSON: {exc}")

    # 4. Idempotent: rerun dry-run reports 0 moves. Warnings about unrecognized
    #    files (e.g. handoff.md) can legitimately persist — they describe stable
    #    facts about the tree, not pending work.
    rerun = _run_migrate(tmp_tree, apply=False)
    if "dry-run: 0 moves" not in rerun.stdout:
        failures.append(
            "not idempotent — second dry-run reported non-zero moves:\n" + rerun.stdout
        )

    # 5. No data loss: every original file hash still present somewhere
    #    (manifest.json is the only legitimate new file).
    after = _collect_file_hashes(tmp_tree)
    after_minus_manifest = {k: v for k, v in after.items() if k != "manifest.json"}
    if len(after_minus_manifest) != len(before):
        failures.append(
            f"file count changed: before={len(before)}, "
            f"after (excl. manifest)={len(after_minus_manifest)}"
        )
    missing_hashes = set(before.values()) - set(after_minus_manifest.values())
    if missing_hashes:
        failures.append(
            f"{len(missing_hashes)} original file hash(es) missing after migration — possible data loss"
        )

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=REAL_TREE,
                        help=f"output tree to verify (default: {REAL_TREE})")
    parser.add_argument("--keep", action="store_true",
                        help="don't delete the temp dir on success")
    parser.add_argument("--keep-on-failure", action="store_true",
                        help="leave the temp dir in place on failure (for inspection)")
    args = parser.parse_args(argv)

    source = args.source.resolve()
    if not source.exists():
        print(f"error: --source {source} does not exist", file=sys.stderr)
        return 2

    check_known_moves = source == REAL_TREE.resolve()

    tmp_root = Path(tempfile.mkdtemp(prefix="shield-verify-"))
    tmp_tree = tmp_root / "shield"
    print(f"copying {source} -> {tmp_tree}")
    if not check_known_moves:
        print("(custom --source: skipping known-moves assertions)")
    shutil.copytree(source, tmp_tree)

    exit_code = 0
    try:
        failures = verify(tmp_tree, check_known_moves=check_known_moves)
        if failures:
            print(f"\nFAIL ({len(failures)} issues):", file=sys.stderr)
            for f in failures:
                print(f"  - {f}", file=sys.stderr)
            exit_code = 1
        else:
            location = str(tmp_tree) if args.keep else "(cleaned up)"
            print(f"\nPASS — migration verified on copy at {location}")
            exit_code = 0
        return exit_code
    finally:
        if exit_code != 0 and args.keep_on_failure:
            print(f"[--keep-on-failure] preserved temp tree at: {tmp_root}", file=sys.stderr)
        elif exit_code != 0 or not args.keep:
            if tmp_root.exists():
                shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
