#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jsonschema>=4.0",
# ]
# ///
"""backlog_store.py — Shield backlog CLI + LOCKED capture()/remove() entrypoint.

This file is the LOCKED reference path for the capture() helper (TRD §11).
The real implementation lives in the importable package shield_backlog
(shield/backlog/shield_backlog/), so skills can do:

    from shield_backlog import capture, remove, read_backlog, BacklogInvalid

This module also wires a CLI used by the /backlog command:

    uv run shield/scripts/backlog_store.py view
    uv run shield/scripts/backlog_store.py add "text" --feature X --epic Y [--kind task]
    uv run shield/scripts/backlog_store.py remove <id>
    uv run shield/scripts/backlog_store.py promote <id> [--step plan|implement|prd|research]
    uv run shield/scripts/backlog_store.py sweep   # lazy reconciliation

Exit codes:
  0 — success.
  1 — operation refused (BacklogInvalid; named error on stderr).
  2 — usage error (bad args, missing file).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Make the shield_backlog package importable without an install step.
sys.path.insert(0, str(REPO_ROOT / "shield" / "backlog"))

from shield_backlog import (  # noqa: E402
    BacklogInvalid,
    capture,
    read_backlog,
    remove,
)
from shield_backlog.view import render  # noqa: E402


DEFAULT_BACKLOG = REPO_ROOT / "docs" / "shield" / "backlog.json"
DEFAULT_MANIFEST = REPO_ROOT / "docs" / "shield" / "manifest.json"
DEFAULT_SHIELD_JSON = REPO_ROOT / ".shield.json"


# ---------- helpers --------------------------------------------------------

def _load_manifest(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        # N3: unrecognized shape → caller treats as None (no badges, no crash)
        return None


def _load_plans_from_manifest(manifest: dict | None, output_dir: Path) -> dict[str, dict]:
    """Build {feature-slug → parsed plan.json} for features whose
    artifacts.plan_json is True. Path derivation only — not stored in manifest.
    A malformed plan.json is silently dropped from the map (treated as 'doubt')."""
    if not isinstance(manifest, dict):
        return {}
    plans: dict[str, dict] = {}
    for feat in manifest.get("features") or []:
        if not isinstance(feat, dict):
            continue
        if not (feat.get("artifacts") or {}).get("plan_json"):
            continue
        name = feat.get("name")
        if not isinstance(name, str):
            continue
        plan_path = output_dir / name / "plan.json"
        try:
            plans[name] = json.loads(plan_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return plans


def _kill_switch_enabled(shield_json: Path) -> bool:
    """When False, eager prune and lazy sweep are disabled."""
    if not shield_json.exists():
        return True  # default true
    try:
        cfg = json.loads(shield_json.read_text())
    except json.JSONDecodeError:
        return True
    return bool((cfg.get("backlog") or {}).get("auto_reconcile", True))


# ---------- subcommands ----------------------------------------------------

def cmd_view(args: argparse.Namespace) -> int:
    path = Path(args.path or DEFAULT_BACKLOG)
    manifest_path = Path(args.manifest or DEFAULT_MANIFEST)
    try:
        doc = read_backlog(path)
    except BacklogInvalid as exc:
        print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
        return 1

    manifest = _load_manifest(manifest_path)

    t0 = time.monotonic()

    # Optional lazy sweep before render (EPIC-3-S3).
    if args.sweep and _kill_switch_enabled(Path(args.shield_json or DEFAULT_SHIELD_JSON)):
        _run_sweep(path=path, manifest=manifest, output_dir=manifest_path.parent)
        # Re-read after sweep.
        try:
            doc = read_backlog(path)
        except BacklogInvalid as exc:
            print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
            return 1

    print(render(doc, manifest=manifest), end="")

    if args.debug_latency:
        elapsed = time.monotonic() - t0
        level = "WARN" if elapsed > 1.0 else "DEBUG"
        print(f"{level}: backlog_view_latency: {elapsed*1000:.1f}ms", file=sys.stderr)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    path = Path(args.path or DEFAULT_BACKLOG)
    try:
        new_id = capture(
            args.text,
            kind=args.kind,
            feature=args.feature,
            epic=args.epic,
            source=args.source,
            path=path,
        )
    except BacklogInvalid as exc:
        print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    print(new_id)
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    path = Path(args.path or DEFAULT_BACKLOG)
    try:
        removed = remove(args.id, path=path)
    except BacklogInvalid as exc:
        print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    if removed is None:
        print(f"FAIL: id_not_found: no entry with id={args.id}", file=sys.stderr)
        return 1
    print(f"removed: {removed['id']} ({removed['feature']} / {removed['epic']})")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    """Print the next-step suggestion. The actual /research|/prd|/plan|/implement
    run is launched by the user (Shield slash-commands stay separate). The
    promotion *reference* is the entry id passed as a transient runtime arg —
    NOT stamped into plan.json (F6)."""
    path = Path(args.path or DEFAULT_BACKLOG)
    try:
        doc = read_backlog(path)
    except BacklogInvalid as exc:
        print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    entry = next((e for e in doc.get("entries") or [] if e["id"] == args.id), None)
    if entry is None:
        print(f"FAIL: id_not_found: no entry with id={args.id}", file=sys.stderr)
        return 1

    step = args.step or "plan"
    feature = entry["feature"]
    print(f"Promote {entry['id']} ({feature} / {entry['epic']}) via /{step}.")
    print(f"Run: /{step} {feature} --backlog-ref {entry['id']}")
    print("(The --backlog-ref is a transient runtime arg; it is never stamped into plan.json.)")
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    """Standalone lazy sweep (no view). Same logic invoked optionally by `view --sweep`."""
    path = Path(args.path or DEFAULT_BACKLOG)
    manifest_path = Path(args.manifest or DEFAULT_MANIFEST)
    if not _kill_switch_enabled(Path(args.shield_json or DEFAULT_SHIELD_JSON)):
        print("sweep skipped: backlog.auto_reconcile=false (kill switch active)", file=sys.stderr)
        return 0
    manifest = _load_manifest(manifest_path)
    _run_sweep(path=path, manifest=manifest, output_dir=manifest_path.parent)
    return 0


def cmd_eager_prune(args: argparse.Namespace) -> int:
    """End-of-run eager prune driven by the promotion reference. Idempotent:
    a no-op when the entry is already absent (e.g. a prior lazy sweep removed
    it) — emits no log line and writes no recovery record (EPIC-3-S3 AC).

    Runs the same reconciliation engine as the lazy sweep; if the verdict is
    not REMOVE, the entry stays (never-remove-on-doubt)."""
    if not _kill_switch_enabled(Path(args.shield_json or DEFAULT_SHIELD_JSON)):
        # Silent skip: kill switch disables auto-reconciliation per design.
        return 0

    path = Path(args.path or DEFAULT_BACKLOG)
    manifest_path = Path(args.manifest or DEFAULT_MANIFEST)
    try:
        doc = read_backlog(path)
    except BacklogInvalid as exc:
        print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
        return 1

    entry = next((e for e in doc.get("entries") or [] if e.get("id") == args.id), None)
    if entry is None:
        # Idempotent: entry already gone. No log, no recovery record.
        return 0

    manifest = _load_manifest(manifest_path)
    plans = _load_plans_from_manifest(manifest, output_dir=manifest_path.parent)

    from shield_backlog.reconciler import reconcile, Verdict  # noqa: WPS433
    decision = reconcile(entry, manifest=manifest or {}, plans=plans)
    if decision.verdict != Verdict.REMOVE:
        # Surface why the eager prune declined — caller can log.
        print(
            f"eager-prune skipped: {decision.verdict.value}: {decision.reason}",
            file=sys.stderr,
        )
        return 0

    try:
        removed = remove(
            entry["id"],
            path=path,
            log_to_recovery=True,
            rationale=f"eager_prune: {decision.reason}",
        )
    except BacklogInvalid as exc:
        print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    if removed is not None:
        _emit_removal_log(removed, decision, trigger="eager_prune")
    return 0


def _run_sweep(*, path: Path, manifest: dict | None, output_dir: Path) -> int:
    """Lazy sweep — iterate all entries, call the reconciler, prune on REMOVE.
    Idempotent (entries already gone are a no-op). Implemented lazily here to
    avoid a hard circular import; reconciler is imported on demand."""
    from shield_backlog.reconciler import reconcile, Verdict  # noqa: WPS433
    try:
        doc = read_backlog(path)
    except BacklogInvalid as exc:
        print(f"FAIL: {exc.code}: {exc.message}", file=sys.stderr)
        return 1

    plans = _load_plans_from_manifest(manifest, output_dir=output_dir)
    pruned = 0
    for entry in list(doc.get("entries") or []):
        decision = reconcile(entry, manifest=manifest or {}, plans=plans)
        if decision.verdict == Verdict.REMOVE:
            try:
                remove(
                    entry["id"],
                    path=path,
                    log_to_recovery=True,
                    rationale=f"lazy_sweep: {decision.reason}",
                )
                pruned += 1
                _emit_removal_log(entry, decision, trigger="lazy_sweep")
            except BacklogInvalid as exc:
                print(f"WARN: sweep_skip: {exc.code}: {exc.message}", file=sys.stderr)
    if pruned:
        print(f"sweep removed {pruned} entries", file=sys.stderr)
    return 0


def _emit_removal_log(entry: dict, decision, *, trigger: str) -> None:
    """F9: log every removal with rationale — structured, single-line."""
    log = {
        "trigger": trigger,
        "entry_id": entry.get("id"),
        "feature": entry.get("feature"),
        "epic": entry.get("epic"),
        "match_kind": decision.match_kind,
        "gating_plan_json_path": decision.gating_plan_json_path,
        "reason": decision.reason,
    }
    print(f"REMOVE: {json.dumps(log, ensure_ascii=False)}", file=sys.stderr)


# ---------- entrypoint -----------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    # view
    v = sub.add_parser("view", help="Render the backlog (optionally with a lazy reconciliation sweep)")
    v.add_argument("--path", help=f"backlog.json path (default {DEFAULT_BACKLOG})")
    v.add_argument("--manifest", help=f"manifest.json path (default {DEFAULT_MANIFEST})")
    v.add_argument("--shield-json", dest="shield_json", help=".shield.json path (kill switch)")
    v.add_argument("--sweep", action="store_true", help="Run lazy reconciliation sweep before render")
    v.add_argument("--debug-latency", action="store_true", help="Emit WARN if view+sweep > 1s")
    v.set_defaults(func=cmd_view)

    # add
    a = sub.add_parser("add", help="Capture a new backlog entry")
    a.add_argument("text")
    a.add_argument("--feature", required=True)
    a.add_argument("--epic", required=True)
    a.add_argument("--kind", default="task", choices=["epic", "story", "task"])
    a.add_argument("--source", default="user", choices=["user", "agent"])
    a.add_argument("--path", help=f"backlog.json path (default {DEFAULT_BACKLOG})")
    a.set_defaults(func=cmd_add)

    # remove
    r = sub.add_parser("remove", help="Manually remove an entry by id")
    r.add_argument("id")
    r.add_argument("--path", help=f"backlog.json path (default {DEFAULT_BACKLOG})")
    r.set_defaults(func=cmd_remove)

    # promote
    pr = sub.add_parser("promote", help="Suggest the next slash-command for an entry")
    pr.add_argument("id")
    pr.add_argument("--step", choices=["research", "prd", "plan", "implement"])
    pr.add_argument("--path", help=f"backlog.json path (default {DEFAULT_BACKLOG})")
    pr.set_defaults(func=cmd_promote)

    # sweep
    s = sub.add_parser("sweep", help="Run the lazy reconciliation sweep without rendering")
    s.add_argument("--path", help=f"backlog.json path (default {DEFAULT_BACKLOG})")
    s.add_argument("--manifest", help=f"manifest.json path (default {DEFAULT_MANIFEST})")
    s.add_argument("--shield-json", dest="shield_json", help=".shield.json path (kill switch)")
    s.set_defaults(func=cmd_sweep)

    # eager-prune  (called at the end of a promoted /plan or /implement run)
    e = sub.add_parser(
        "eager-prune",
        help="Prune a single entry by promotion id IFF its epic landed (called by /plan, /implement)",
    )
    e.add_argument("id", help="The transient promotion --backlog-ref entry id")
    e.add_argument("--path", help=f"backlog.json path (default {DEFAULT_BACKLOG})")
    e.add_argument("--manifest", help=f"manifest.json path (default {DEFAULT_MANIFEST})")
    e.add_argument("--shield-json", dest="shield_json", help=".shield.json path (kill switch)")
    e.set_defaults(func=cmd_eager_prune)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
