#!/usr/bin/env python3
"""steps_store.py — Shield per-skill step tracker (the producer of steps.json).

The `execute-steps` skill instructs skills to call this helper. It writes and
updates `steps.json`, the file the session-start hook reads to offer resume of
an interrupted phase.

CRITICAL: the path MUST match the hook, which reads
    ${SHIELD_HOME:-~/.shield}/projects/<project>/steps.json
where <project> is the `project` field of the nearest `.shield.json`.

CLI (called by skills, not users):

    uv run shield/scripts/steps_store.py init --skill research --feature f \\
        --steps-json '[{"id":1,"action":"Repo scan","mandatory":true}, ...]'
    uv run shield/scripts/steps_store.py start 2
    uv run shield/scripts/steps_store.py complete 2 --output docs/shield/f/research.md
    uv run shield/scripts/steps_store.py fail 2
    uv run shield/scripts/steps_store.py read        # current state, or "none"
    uv run shield/scripts/steps_store.py clear        # delete on completion

Every subcommand accepts `--steps-file PATH` (skip path resolution; used by tests)
and `--project NAME` (override the .shield.json lookup).

Exit codes:
  0 — success.
  1 — operation refused (StepsError; named error on stderr).
  2 — usage error (bad args).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

STATUSES = ("pending", "in_progress", "complete", "failed")
MARKER_FILE = ".shield.json"


class StepsError(Exception):
    """Operation refused — exit 1 with a named message on stderr."""


# ---------- path resolution (must match session-start.sh) ------------------

def _shield_home(shield_home: Path | None = None) -> Path:
    if shield_home is not None:
        return Path(shield_home)
    env = os.environ.get("SHIELD_HOME")
    return Path(env) if env else Path.home() / ".shield"


def _find_project(start_dir: Path) -> str | None:
    """Walk up from start_dir for .shield.json, return its `project` field."""
    dir_ = start_dir.resolve()
    while True:
        marker = dir_ / MARKER_FILE
        if marker.is_file():
            try:
                return json.loads(marker.read_text()).get("project")
            except (json.JSONDecodeError, OSError):
                return None
        if dir_.parent == dir_:
            return None
        dir_ = dir_.parent


def resolve_steps_path(
    *,
    project: str | None = None,
    shield_home: Path | None = None,
    start_dir: Path | None = None,
    override: Path | None = None,
) -> Path:
    """Resolve the steps.json path the hook reads. `override` short-circuits all
    resolution (used by tests and the `--steps-file` flag)."""
    if override is not None:
        return Path(override)
    if project is None:
        project = _find_project(start_dir or Path.cwd())
    if not project:
        raise StepsError("no_project: no .shield.json with a 'project' field found")
    return _shield_home(shield_home) / "projects" / project / "steps.json"


# ---------- core operations ------------------------------------------------

def _normalize_step(step: dict) -> dict:
    if "id" not in step or "action" not in step:
        raise StepsError("bad_step: each step needs an 'id' and an 'action'")
    out = {
        "id": step["id"],
        "action": step["action"],
        "mandatory": step.get("mandatory", True),
        "status": step.get("status", "pending"),
        "output": step.get("output"),
    }
    if step.get("phase") is not None:
        out["phase"] = step["phase"]
    if out["status"] not in STATUSES:
        raise StepsError(f"bad_status: {out['status']!r} not in {STATUSES}")
    return out


def init_steps(skill: str, feature: str, steps: list[dict], *, path: Path) -> Path:
    """Write a fresh steps.json skeleton (overwrites any existing file)."""
    doc = {
        "skill": skill,
        "feature": feature,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "steps": [_normalize_step(s) for s in steps],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return path


def read_steps(path: Path) -> dict | None:
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return None


def set_status(step_id: int, status: str, *, path: Path, output: str | None = None) -> dict:
    if status not in STATUSES:
        raise StepsError(f"bad_status: {status!r} not in {STATUSES}")
    doc = read_steps(path)
    if doc is None:
        raise StepsError(f"no_steps: no steps.json at {path}")
    step = next((s for s in doc["steps"] if s["id"] == step_id), None)
    if step is None:
        raise StepsError(f"id_not_found: no step with id={step_id}")
    step["status"] = status
    if output is not None:
        step["output"] = output
    Path(path).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return step


def clear_steps(path: Path) -> bool:
    """Delete steps.json. Returns True if removed, False if already absent."""
    try:
        Path(path).unlink()
        return True
    except FileNotFoundError:
        return False


# ---------- CLI ------------------------------------------------------------

def _path_from_args(args: argparse.Namespace) -> Path:
    return resolve_steps_path(
        override=Path(args.steps_file) if args.steps_file else None,
        project=args.project,
    )


def cmd_init(args: argparse.Namespace) -> int:
    try:
        steps = json.loads(args.steps_json) if args.steps_json else json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"FAIL: bad_json: {exc}", file=sys.stderr)
        return 2
    path = init_steps(args.skill, args.feature, steps, path=_path_from_args(args))
    print(path)
    return 0


def cmd_set_status(args: argparse.Namespace, status: str) -> int:
    step = set_status(
        args.id, status, path=_path_from_args(args), output=getattr(args, "output", None)
    )
    print(f"{step['id']}: {step['status']}")
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    doc = read_steps(_path_from_args(args))
    print(json.dumps(doc, indent=2, ensure_ascii=False) if doc is not None else "none")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    removed = clear_steps(_path_from_args(args))
    print("cleared" if removed else "already absent")
    return 0


def _add_common(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--steps-file", help="Explicit steps.json path (skips .shield.json resolution)")
    sp.add_argument("--project", help="Project name (overrides the .shield.json lookup)")


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="Write a fresh steps.json skeleton")
    i.add_argument("--skill", required=True)
    i.add_argument("--feature", required=True)
    i.add_argument("--steps-json", help="JSON array of steps (else read from stdin)")
    _add_common(i)
    i.set_defaults(func=cmd_init)

    for name, status in (("start", "in_progress"), ("complete", "complete"), ("fail", "failed")):
        sp = sub.add_parser(name, help=f"Set a step's status to {status}")
        sp.add_argument("id", type=int)
        if name == "complete":
            sp.add_argument("--output", help="Record the step's output path")
        _add_common(sp)
        sp.set_defaults(func=lambda a, _s=status: cmd_set_status(a, _s))

    r = sub.add_parser("read", help="Print the current steps.json (or 'none')")
    _add_common(r)
    r.set_defaults(func=cmd_read)

    c = sub.add_parser("clear", help="Delete steps.json (call on completion)")
    _add_common(c)
    c.set_defaults(func=cmd_clear)

    args = p.parse_args()
    try:
        return args.func(args)
    except StepsError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
