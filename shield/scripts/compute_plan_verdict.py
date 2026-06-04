#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""compute_plan_verdict.py — deterministic verdict for /plan-review.

Turns aggregated per-persona grades plus the classified findings into a
composite readiness score and applies the P0-gate documented in
`shield/skills/general/plan-review/scoring.md`. This mechanizes the
"averaging problem" guard: a strong composite cannot hide a Critical-severity
D/F finding.

This module is the SINGLE SOURCE OF TRUTH for plan-review persona weights.
`scoring.md` and `dimensions.md` reference this table rather than restating it.

Input (JSON on stdin or a file path argument):

    {
      "personas": [ {"name": "architect", "grade": "B"}, ... ],
      "findings":  [ {"id": "PM2", "severity": "Critical", "grade": "F"}, ... ]
    }

- `personas[].name` must be a known persona (see WEIGHTS); unknown names error.
- `personas[].grade` is the persona's aggregated letter grade (A-F).
- `findings[]` is the classified finding list; a P0 is any finding with
  severity "Critical" graded D or F.

Output (stdout), three stable lines:

    composite: 2.93 (B)
    p0_count: 1
    verdict: Needs Work (composite 2.93, blocked by 1 P0)

Exit codes:
  0  — verdict computed.
  2  — usage / input error (unknown persona, bad grade, malformed JSON).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Canonical persona weights. Mirrors dimensions.md / personas.md. Core = 1.0,
# supporting = 0.7. The PM persona weight (0.7) applies to the grade rolled up
# from the 10 PM dim subagents (PM1-PM10).
WEIGHTS: dict[str, float] = {
    "architect": 1.0,
    "security-engineer": 1.0,
    "dx-engineer": 1.0,
    "platform-engineer": 1.0,
    "backend-engineer": 1.0,
    "finops-analyst": 0.7,
    "agile-coach": 0.7,
    "sre": 0.7,
    "product-manager": 0.7,
}

GRADE_TO_NUM: dict[str, int] = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}


def _letter(num: float) -> str:
    """Map a numeric average to a letter using scoring.md's range table."""
    if num >= 3.5:
        return "A"
    if num >= 2.5:
        return "B"
    if num >= 1.5:
        return "C"
    if num >= 0.5:
        return "D"
    return "F"


def _composite(personas: list[dict[str, Any]]) -> float:
    """Weighted average of activated persona grades. Denominator is the sum of
    weights for personas that actually ran — not all of WEIGHTS."""
    num = 0.0
    denom = 0.0
    for p in personas:
        name = p.get("name")
        if name not in WEIGHTS:
            raise ValueError(f"unknown persona: {name!r} (known: {sorted(WEIGHTS)})")
        grade = (p.get("grade") or "").strip().upper()
        if grade not in GRADE_TO_NUM:
            raise ValueError(f"bad grade {grade!r} for persona {name!r}")
        weight = WEIGHTS[name]
        num += GRADE_TO_NUM[grade] * weight
        denom += weight
    if denom == 0:
        raise ValueError("no activated personas — cannot compute composite")
    return num / denom


def _p0_count(findings: list[dict[str, Any]]) -> int:
    """P0 = grade D or F on a Critical-severity finding (scoring.md)."""
    count = 0
    for f in findings:
        severity = (f.get("severity") or "").strip().lower()
        grade = (f.get("grade") or "").strip().upper()
        if severity == "critical" and grade in {"D", "F"}:
            count += 1
    return count


def _verdict(composite: float, p0_count: int) -> str:
    """Composite + P0-gate. A high composite with any P0 is gated to Needs Work."""
    if composite < 1.5:
        return f"Not Ready (composite {composite:.2f})"
    if composite < 2.5:
        return f"Needs Work (composite {composite:.2f})"
    if p0_count > 0:
        plural = "P0" if p0_count == 1 else "P0s"
        return f"Needs Work (composite {composite:.2f}, blocked by {p0_count} {plural})"
    return f"Ready (composite {composite:.2f})"


def compute(payload: dict[str, Any]) -> str:
    personas = payload.get("personas") or []
    findings = payload.get("findings") or []
    composite = _composite(personas)
    p0 = _p0_count(findings)
    return (
        f"composite: {composite:.2f} ({_letter(composite)})\n"
        f"p0_count: {p0}\n"
        f"verdict: {_verdict(composite, p0)}"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "grades_json",
        nargs="?",
        default=None,
        help="Path to grades.json. Reads stdin when omitted.",
    )
    args = parser.parse_args(argv)
    try:
        raw = Path(args.grades_json).read_text() if args.grades_json else sys.stdin.read()
        payload = json.loads(raw)
        print(compute(payload))
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
