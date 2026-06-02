#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jsonschema>=4.0",
# ]
# ///
"""validate_plan.py — JSON Schema validator for shield plan.json sidecars.

Invoked by /plan-review (first check, before rubric grading) and the
shield/evals/run.py eval runner.

Exit codes:
  0  — sidecar is valid (may emit WARN lines on stderr for soft issues).
  1  — sidecar fails validation (named error printed to stderr).
  2  — usage error (file not found, malformed JSON).

Named errors (stderr prefix on FAIL):
  schema_violation      — JSON Schema rejected the doc
  unknown_doc_enum      — design_refs[].doc has unknown value
  missing_design_refs   — story has no design_refs[] AND a TRD is present
                           (WARN by default; FAIL only with --strict-design-refs)
  milestone_id_unknown  — story.milestone_id points at a non-existent milestone
  milestone_id_orphan   — milestones[] non-empty but story.milestone_id is null
                           (WARN, not FAIL)
  cycle_in_milestones   — milestones depends_on graph has a cycle

Usage:
  uv run shield/scripts/validate_plan.py PATH_TO_PLAN_JSON [--strict-design-refs]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover — surfaced clearly when uv misconfigures
    print("validate_plan: requires jsonschema (uv run will install it)", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "shield" / "schema" / "plan-sidecar.schema.json"
TRD_SECTIONS_PATH = REPO_ROOT / "shield" / "schema" / "trd-sections.yaml"

CURRENT_VERSION = (1, 6)


def _parse_version(v: str) -> tuple[int, int]:
    try:
        major, minor = v.split(".", 1)
        return int(major), int(minor)
    except (ValueError, AttributeError):
        return (0, 0)


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


def _detect_cycle(milestones: list[dict[str, Any]]) -> list[str] | None:
    """Return one cycle as a list of milestone IDs, or None if the graph is a DAG."""
    graph: dict[str, list[str]] = {m["id"]: list(m.get("depends_on") or []) for m in milestones}

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {k: WHITE for k in graph}
    stack: list[str] = []
    cycle_path: list[str] | None = None

    def dfs(node: str) -> bool:
        nonlocal cycle_path
        color[node] = GRAY
        stack.append(node)
        for nbr in graph.get(node, []):
            if nbr not in color:
                continue
            if color[nbr] == GRAY:
                idx = stack.index(nbr)
                cycle_path = stack[idx:] + [nbr]
                return True
            if color[nbr] == WHITE and dfs(nbr):
                return True
        stack.pop()
        color[node] = BLACK
        return False

    for n in list(graph):
        if color[n] == WHITE and dfs(n):
            return cycle_path
    return None


def _trd_present_for(plan_path: Path) -> bool:
    return (plan_path.parent / "trd.md").exists()


def _emit(severity: str, code: str, message: str) -> None:
    print(f"{severity}: {code}: {message}", file=sys.stderr)


def validate(plan_path: Path, *, strict_design_refs: bool = False) -> int:
    if not plan_path.is_file():
        _emit("FAIL", "file_not_found", str(plan_path))
        return 2
    try:
        plan = json.loads(plan_path.read_text())
    except json.JSONDecodeError as e:
        _emit("FAIL", "invalid_json", f"{plan_path}: {e.msg} at line {e.lineno}")
        return 2

    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(plan), key=lambda e: e.path)
    fail = False

    # Forward-compat policy.
    declared_v = _parse_version(plan.get("version", ""))
    if declared_v > CURRENT_VERSION:
        _emit("WARN", "forward_compat", f"sidecar version {plan.get('version')} > current {CURRENT_VERSION[0]}.{CURRENT_VERSION[1]} — best-effort validation")

    for err in errors:
        path = "/".join(str(p) for p in err.path) or "<root>"
        # Map common cases to named error codes for stable test assertions.
        code = "schema_violation"
        if "design_refs" in [str(p) for p in err.path] and "is not one of" in err.message:
            code = "unknown_doc_enum"
        _emit("FAIL", code, f"{path}: {err.message}")
        fail = True

    if fail:
        return 1

    # Milestone-graph checks (beyond JSON Schema).
    milestones = plan.get("milestones") or []
    milestone_ids = {m["id"] for m in milestones}
    cycle = _detect_cycle(milestones)
    if cycle:
        _emit("FAIL", "cycle_in_milestones", " -> ".join(cycle))
        return 1

    # Story-level checks.
    trd_present = _trd_present_for(plan_path)
    for epic in plan.get("epics") or []:
        for story in epic.get("stories") or []:
            mid = story.get("milestone_id")
            if milestones and mid is None:
                _emit("WARN", "milestone_id_orphan", f"{story.get('id')} has milestone_id=null while milestones[] is non-empty")
            elif mid is not None and mid not in milestone_ids:
                _emit("FAIL", "milestone_id_unknown", f"{story.get('id')} references unknown milestone_id={mid}")
                fail = True
            refs = story.get("design_refs") or []
            if trd_present and not refs:
                sev = "FAIL" if strict_design_refs else "WARN"
                _emit(sev, "missing_design_refs", f"{story.get('id')} has empty design_refs[] but a TRD is present")
                if strict_design_refs:
                    fail = True

    # 1.5 structural checks — rollup invariants.
    drift_failures = _check_touches_lld_drift(plan)
    for mid, persisted, rollup in drift_failures:
        _emit("FAIL", "touches_lld_drift", f"milestone {mid}: persisted={persisted} rollup={rollup}")
        fail = True

    missing_failures = _check_lld_component_missing(plan)
    for sid, name in missing_failures:
        _emit(
            "FAIL",
            "lld_component_missing",
            f"story {sid} references component '{name}' which is not in lld_components[]",
        )
        fail = True

    return 1 if fail else 0


def _check_touches_lld_drift(plan: dict[str, Any]) -> list[tuple[str, list[str], list[str]]]:
    """Verify persisted milestones[i].touches_lld[] equals the rollup of
    unique(design_refs[].component for stories where doc=='lld').

    Returns a list of (milestone_id, persisted, rollup) tuples for failures.
    """
    failures: list[tuple[str, list[str], list[str]]] = []
    stories_by_milestone: dict[str, list[dict[str, Any]]] = {}
    for epic in plan.get("epics") or []:
        for story in epic.get("stories") or []:
            mid = story.get("milestone_id")
            if mid is None:
                continue
            stories_by_milestone.setdefault(mid, []).append(story)
    for milestone in plan.get("milestones") or []:
        # touches_lld is 1.5+ — absent in older sidecars; skip drift check then.
        if "touches_lld" not in milestone:
            continue
        mid = milestone["id"]
        persisted = set(milestone.get("touches_lld") or [])
        rollup: set[str] = set()
        for story in stories_by_milestone.get(mid, []):
            for ref in story.get("design_refs") or []:
                if ref.get("doc") == "lld" and ref.get("component"):
                    rollup.add(ref["component"])
        if persisted != rollup:
            failures.append((mid, sorted(persisted), sorted(rollup)))
    return failures


def _check_lld_component_missing(plan: dict[str, Any]) -> list[tuple[str, str]]:
    """Verify every design_refs[].component (where doc=='lld') appears in
    lld_components[].name. Skipped when lld_components is absent (back-compat).

    Returns a list of (story_id, component_name) tuples for failures.
    """
    if "lld_components" not in plan:
        return []
    registered = {c["name"] for c in plan.get("lld_components") or []}
    failures: list[tuple[str, str]] = []
    for epic in plan.get("epics") or []:
        for story in epic.get("stories") or []:
            for ref in story.get("design_refs") or []:
                if ref.get("doc") == "lld":
                    name = ref.get("component")
                    if name and name not in registered:
                        failures.append((story["id"], name))
    return failures


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("plan_json", help="Path to a plan.json sidecar.")
    parser.add_argument(
        "--strict-design-refs",
        action="store_true",
        help="Treat empty design_refs[] (with a TRD present) as FAIL, not WARN.",
    )
    args = parser.parse_args(argv)
    return validate(Path(args.plan_json), strict_design_refs=args.strict_design_refs)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
