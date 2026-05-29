"""Eager + lazy reconciliation triggers (EPIC-3-S3).

Both paths share the single `shield_backlog.reconciler.reconcile()` engine.
The kill switch (.shield.json → backlog.auto_reconcile=false) disables both
paths; manual `remove()` continues to work.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shield_backlog.reconciler import RemovalDecision, Verdict, reconcile
from shield_backlog.store import (
    BacklogInvalid,
    DEFAULT_BACKLOG_PATH,
    DEFAULT_REMOVED_LOG,
    read_backlog,
    remove,
)


# ----- helpers (defaults derived from the repo root) ----------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = _REPO_ROOT / "docs" / "shield" / "manifest.json"
DEFAULT_SHIELD_JSON = _REPO_ROOT / ".shield.json"


def kill_switch_enabled(shield_json_path: Path | None = None) -> bool:
    """Return False when `.shield.json` has `backlog.auto_reconcile = false`."""
    p = Path(shield_json_path) if shield_json_path else DEFAULT_SHIELD_JSON
    if not p.exists():
        return True
    try:
        cfg = json.loads(p.read_text())
    except json.JSONDecodeError:
        return True
    return bool((cfg.get("backlog") or {}).get("auto_reconcile", True))


def load_manifest(path: Path | None = None) -> dict[str, Any] | None:
    p = Path(path) if path else DEFAULT_MANIFEST
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def load_plans(manifest: dict[str, Any] | None, output_dir: Path) -> dict[str, dict[str, Any]]:
    """Build {feature-slug → parsed plan.json} for features with plan_json=True."""
    plans: dict[str, dict[str, Any]] = {}
    if not isinstance(manifest, dict):
        return plans
    for feat in manifest.get("features") or []:
        if not isinstance(feat, dict):
            continue
        if not (feat.get("artifacts") or {}).get("plan_json"):
            continue
        name = feat.get("name")
        if not isinstance(name, str):
            continue
        try:
            plans[name] = json.loads((output_dir / name / "plan.json").read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return plans


# ----- eager prune ---------------------------------------------------------

def eager_prune(
    entry_id: str,
    *,
    backlog_path: Path | None = None,
    manifest_path: Path | None = None,
    shield_json_path: Path | None = None,
    removed_log_path: Path | None = None,
) -> RemovalDecision | None:
    """End-of-run prune driven by a promotion reference (EPIC-3-S1/S3).
    Returns the RemovalDecision when an action was attempted; None when the
    entry was already absent (idempotent no-op — no log, no recovery record)
    or when the kill switch is engaged.
    """
    if not kill_switch_enabled(shield_json_path):
        return None

    bpath = Path(backlog_path) if backlog_path else DEFAULT_BACKLOG_PATH
    mpath = Path(manifest_path) if manifest_path else DEFAULT_MANIFEST

    doc = read_backlog(bpath)
    entry = next((e for e in doc.get("entries") or [] if e.get("id") == entry_id), None)
    if entry is None:
        return None  # idempotent

    manifest = load_manifest(mpath)
    plans = load_plans(manifest, output_dir=mpath.parent)
    decision = reconcile(entry, manifest=manifest or {}, plans=plans)

    if decision.verdict != Verdict.REMOVE:
        return decision  # caller sees the rationale; entry stays

    log_path = Path(removed_log_path) if removed_log_path else DEFAULT_REMOVED_LOG
    remove(
        entry_id,
        path=bpath,
        log_to_recovery=True,
        removed_log_path=log_path,
        rationale=f"eager_prune: {decision.reason}",
    )
    return decision


# ----- lazy sweep ----------------------------------------------------------

def lazy_sweep(
    *,
    backlog_path: Path | None = None,
    manifest_path: Path | None = None,
    shield_json_path: Path | None = None,
    removed_log_path: Path | None = None,
) -> list[RemovalDecision]:
    """Walk all entries; remove each whose reconciliation verdict is REMOVE.
    Idempotent and exception-safe (one bad entry doesn't stop the sweep).
    Returns the list of decisions that resulted in a removal."""
    if not kill_switch_enabled(shield_json_path):
        return []

    bpath = Path(backlog_path) if backlog_path else DEFAULT_BACKLOG_PATH
    mpath = Path(manifest_path) if manifest_path else DEFAULT_MANIFEST
    log_path = Path(removed_log_path) if removed_log_path else DEFAULT_REMOVED_LOG

    doc = read_backlog(bpath)
    manifest = load_manifest(mpath)
    plans = load_plans(manifest, output_dir=mpath.parent)

    removed_decisions: list[RemovalDecision] = []
    for entry in list(doc.get("entries") or []):
        decision = reconcile(entry, manifest=manifest or {}, plans=plans)
        if decision.verdict != Verdict.REMOVE:
            continue
        try:
            remove(
                entry["id"],
                path=bpath,
                log_to_recovery=True,
                removed_log_path=log_path,
                rationale=f"lazy_sweep: {decision.reason}",
            )
        except BacklogInvalid:
            # Skip this entry; preserve the rest of the sweep.
            continue
        removed_decisions.append(decision)
    return removed_decisions
