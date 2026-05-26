#!/usr/bin/env python3
"""Score the PRD-Review merge gate.

Reads per-dispatch JSON files (one per fixture x dim) written by
run-prd-review-merge-gate.sh, counts findings per dim per fixture, writes the
postchange JSON, and exits 1 if the merge gate criteria fail.

A 'finding' = an evaluation_point with grade not in {'A', 'N/A', 'informational'}.
For prompts that return grade 'N/A' or 'informational' at the dim level (e.g.
dim 2/8/9/10 on internal-tool fixture, dim 9/10 on lean fixture), the dim
contributes 0 findings and is recorded as N/A or informational in the breakdown.

Gate criteria (matching shield/evals/baselines/prd-review-pm.json gate_criteria):
- PM total findings >= baseline pm_total_findings (62 today)
- No individual fixture regresses by more than 10%
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

PROMPT_DIM_NAME_BY_ID = {
    1: "problem_clarity",
    2: "scope_boundaries",
    3: "measurable_success",
    7: "raci_approvals",
    8: "legal_privacy",
    9: "gtm_comms",
    10: "support_cx",
    11: "why_now",
    12: "risks_assumptions",
}


def extract_json(raw: str) -> dict | None:
    """Pull the first balanced JSON object out of a model response."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = raw.find("{")
        if start == -1:
            return None
        depth = 0
        for i, ch in enumerate(raw[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = raw[start : i + 1]
                    break
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def count_findings(dim_block: dict) -> tuple[int, str]:
    """Return (findings_count, status_token) for a dim block."""
    grade = (dim_block.get("grade") or "").strip()
    if grade in ("N/A", "n/a"):
        return 0, "NA"
    if grade.lower() == "informational":
        return 0, "informational"
    eps = dim_block.get("evaluation_points") or []
    findings = sum(
        1
        for ep in eps
        if (ep.get("grade") or "").strip().upper() not in {"A", "N/A"}
        and (ep.get("grade") or "").strip().lower() != "informational"
    )
    return findings, "graded"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixtures", required=True, help="space-separated fixture:type pairs")
    parser.add_argument("--prompts", required=True, help="space-separated slug:dim_id:name triples")
    args = parser.parse_args()

    fixtures = [tuple(f.split(":")) for f in args.fixtures.split() if f]
    prompts = [tuple(p.split(":")) for p in args.prompts.split() if p]

    baseline = json.loads(args.baseline.read_text())

    fixture_results: dict[str, dict] = {}
    for fixture_name, _prd_type in fixtures:
        breakdown: dict[str, int | str] = {}
        na_dims: list[int] = []
        informational_dims: list[int] = []
        total = 0
        for prompt_slug, dim_id_s, _name in prompts:
            dim_id = int(dim_id_s)
            dim_name = PROMPT_DIM_NAME_BY_ID[dim_id]
            result_file = args.results_dir / f"{fixture_name}__dim{dim_id}.json"
            if not result_file.is_file():
                print(f"  [{fixture_name} dim{dim_id}] MISSING result file", file=sys.stderr)
                breakdown[f"dim_{dim_id}_{dim_name}_MISSING"] = 0
                continue
            raw = result_file.read_text()
            dim_block = extract_json(raw)
            if dim_block is None:
                print(f"  [{fixture_name} dim{dim_id}] UNPARSEABLE output", file=sys.stderr)
                breakdown[f"dim_{dim_id}_{dim_name}_UNPARSEABLE"] = 0
                continue
            count, status = count_findings(dim_block)
            total += count
            if status == "NA":
                breakdown[f"dim_{dim_id}_{dim_name}_NA"] = 0
                na_dims.append(dim_id)
            elif status == "informational":
                breakdown[f"dim_{dim_id}_{dim_name}_informational"] = 0
                informational_dims.append(dim_id)
            else:
                breakdown[f"dim_{dim_id}_{dim_name}"] = count
        fixture_results[fixture_name] = {
            "findings_count": total,
            "findings_breakdown": breakdown,
        }
        if na_dims:
            fixture_results[fixture_name]["na_dims"] = na_dims
        if informational_dims:
            fixture_results[fixture_name]["informational_dims"] = informational_dims

    pm_total = sum(r["findings_count"] for r in fixture_results.values())
    baseline_total = baseline.get("pm_total_findings", 62)

    regressions: list[str] = []
    deltas: dict[str, str] = {}
    for fixture_name, _ in fixtures:
        post = fixture_results[fixture_name]["findings_count"]
        base = baseline.get("fixtures", {}).get(fixture_name, {}).get("findings_count", 0)
        delta = post - base
        deltas[fixture_name] = f"{base} -> {post} ({delta:+d})"
        if base > 0 and (base - post) / base > 0.10:
            regressions.append(
                f"{fixture_name}: {base} -> {post} ({100 * (post - base) / base:+.1f}%)"
            )

    gate = {
        "baseline_total": baseline_total,
        "postchange_total": pm_total,
        "merge_blocking_check": (
            f"PASS ({pm_total} >= {baseline_total})"
            if pm_total >= baseline_total
            else f"FAIL ({pm_total} < {baseline_total})"
        ),
        "per_fixture_regression_check": (
            "PASS (no fixture regresses more than 10%)"
            if not regressions
            else f"FAIL ({', '.join(regressions)})"
        ),
        "stretch_goal_check": (
            f"MET ({pm_total} >= 81)"
            if pm_total >= 81
            else f"NOT MET ({pm_total} < 81; informational)"
        ),
        "overall": "PASS" if pm_total >= baseline_total and not regressions else "FAIL",
    }

    output_doc = {
        "purpose": (
            "Post-restructure PM finding counts captured by "
            "shield/evals/run-prd-review-merge-gate.sh. Compared to "
            "shield/evals/baselines/prd-review-pm.json to enforce the merge gate."
        ),
        "captured_at": date.today().isoformat(),
        "fixtures": fixture_results,
        "pm_total_findings": pm_total,
        "merge_gate_result": gate,
        "per_fixture_deltas": deltas,
    }

    args.output.write_text(json.dumps(output_doc, indent=2) + "\n")

    print(f"\nPM total findings: {pm_total} (baseline {baseline_total})")
    print(f"Merge gate: {gate['merge_blocking_check']}")
    print(f"Regression check: {gate['per_fixture_regression_check']}")
    print(f"Stretch goal:    {gate['stretch_goal_check']}")
    print(f"Overall:         {gate['overall']}")
    print(f"\nWrote: {args.output}")

    return 0 if gate["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
