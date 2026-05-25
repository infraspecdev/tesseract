#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "jsonschema>=4.0",
# ]
# ///
"""shield/evals/run.py — deterministic eval runner for shield/evals/<name>.yaml.

Currently wires the `plan-trd` suite, which binds TRD/plan fixture directories
to expected outcomes from `validate_trd.py` and `validate_plan.py`.

Usage:
    uv run shield/evals/run.py plan-trd
    uv run shield/evals/run.py plan-trd --verbose
    uv run shield/evals/run.py plan-trd --case positive-backend

Exit codes:
    0  — all cases met expectations.
    1  — one or more cases failed.
    2  — usage error.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "shield" / "evals"
SCRIPTS_DIR = REPO_ROOT / "shield" / "scripts"
VALIDATE_TRD = SCRIPTS_DIR / "validate_trd.py"
VALIDATE_PLAN = SCRIPTS_DIR / "validate_plan.py"


def _run_validator(script: Path, target: Path) -> tuple[int, str]:
    """Run a validator and return (exit_code, combined_stderr)."""
    proc = subprocess.run(
        [sys.executable, str(script), str(target)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stderr.strip()


def _matches(expectation: str, exit_code: int, stderr: str) -> tuple[bool, str]:
    """Return (matched, evidence). PASS means exit 0; otherwise expect the
    named-error code (e.g. `missing_section:high-level-design`) to appear in
    stderr."""
    if expectation == "PASS":
        if exit_code == 0:
            return True, ""
        return False, f"expected PASS, got exit={exit_code} stderr={stderr!r}"
    needle = expectation
    if needle in stderr and exit_code != 0:
        return True, ""
    return False, f"expected {needle!r} in stderr, got exit={exit_code} stderr={stderr!r}"


def run_suite(suite_name: str, only_case: str | None = None, verbose: bool = False) -> int:
    suite_path = EVAL_DIR / f"{suite_name}.yaml"
    if not suite_path.is_file():
        print(f"eval suite not found: {suite_path}", file=sys.stderr)
        return 2
    suite = yaml.safe_load(suite_path.read_text())
    cases = suite.get("cases") or []
    total = passed = 0

    print(f"=== eval suite: {suite_name} ({len(cases)} cases) ===")
    for case in cases:
        name = case["name"]
        if only_case and only_case != name:
            continue
        total += 1
        fixture_dir = (EVAL_DIR / suite_name / case["fixture"]).resolve()
        if not fixture_dir.is_dir():
            print(f"  FAIL {name}: fixture dir not found: {fixture_dir}")
            continue

        expect = case.get("expect") or {}
        failed_assertions: list[str] = []

        # TRD check (always present in this suite).
        trd_expect = expect.get("trd")
        trd_path = fixture_dir / "trd.md"
        if trd_expect is not None:
            rc, stderr = _run_validator(VALIDATE_TRD, trd_path)
            ok, evidence = _matches(trd_expect, rc, stderr)
            if not ok:
                failed_assertions.append(f"trd: {evidence}")
            elif verbose:
                print(f"    trd OK ({trd_expect})")

        # plan.json check (positive cases only).
        plan_expect = expect.get("plan")
        plan_path = fixture_dir / "plan.json"
        if plan_expect is not None and plan_path.exists():
            rc, stderr = _run_validator(VALIDATE_PLAN, plan_path)
            ok, evidence = _matches(plan_expect, rc, stderr)
            if not ok:
                failed_assertions.append(f"plan: {evidence}")
            elif verbose:
                print(f"    plan OK ({plan_expect})")

        if failed_assertions:
            print(f"  FAIL {name}")
            for fa in failed_assertions:
                print(f"      {fa}")
        else:
            passed += 1
            print(f"  PASS {name}")

    print(f"=== {passed}/{total} cases passed ===")
    return 0 if passed == total else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("suite", help="Eval suite name (e.g. plan-trd).")
    parser.add_argument("--case", default=None, help="Run a single case by name.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    return run_suite(args.suite, only_case=args.case, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
