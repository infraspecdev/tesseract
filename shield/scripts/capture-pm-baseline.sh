#!/usr/bin/env bash
# Capture PM agent's finding count against PRD-review test fixtures.
#
# This is the merge-gate baseline for the v0 restructure (PM persona →
# focused subagents). The numbers committed in
# shield/evals/baselines/prd-review-pm.json were captured by dispatching
# shield:product-manager-reviewer (session-cached old name; behavior is
# today's PM, unaffected by the rename PR) against the 4 fixtures via
# Claude Code's Agent tool.
#
# This script documents the methodology so a reviewer can verify by
# re-running it.
#
# A "finding" = an evaluation point with grade != A and grade != N/A
# (i.e., a real gap identified — not a no-issue check, not an exempted
# dimension).
#
# Usage:
#   ./capture-pm-baseline.sh
#
# Outputs: writes shield/evals/baselines/prd-review-pm.json (if missing)
#          AND prints summary to stdout
#
# This is documentation-grade; not a fully-automated CI gate. The actual
# capture happens via Claude Code's Agent tool dispatch in an interactive
# session (the dispatch protocol is reproduced below for transparency).

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
FIXTURES_DIR="$REPO_ROOT/shield/skills/general/prd-review/test-fixtures"
BASELINE_FILE="$REPO_ROOT/shield/evals/baselines/prd-review-pm.json"

if [[ ! -f "$BASELINE_FILE" ]]; then
  echo "Baseline file missing: $BASELINE_FILE"
  echo "To capture: dispatch shield:product-manager (or product-manager-reviewer pre-rename)"
  echo "against each of the 4 fixtures below, count distinct gap findings, and"
  echo "write the JSON per the schema in the existing baseline file template."
  exit 1
fi

echo "=== Existing baseline ==="
cat "$BASELINE_FILE" | python3 -m json.tool 2>/dev/null || cat "$BASELINE_FILE"
echo ""
echo "=== Fixtures (4 expected) ==="
ls -1 "$FIXTURES_DIR"

echo ""
echo "=== Reproducibility ==="
echo "To re-capture, dispatch shield:product-manager (or pre-rename product-manager-reviewer)"
echo "via the Agent tool with this prompt structure for each fixture:"
cat <<'PROMPT'

You are reviewing a PRD in PRD-Review mode. Mode: Standalone.
PRD source: <fixture path>
PRD type: <standard | lean - confirmed by user>
Your assigned dimensions: 1, 2, 3, 7, 8, 9, 10, 11, 12

Rubric: Read shield/skills/general/prd-review/rubric.md

Your job:
1. Read the PRD at the path above.
2. For each of YOUR assigned dimensions, grade each evaluation point A-F (or N/A with reasoning).
3. Aggregate to a per-dimension grade.
4. Aggregate your dimensions to a persona grade.
5. Identify gaps - for each non-A grade, write a one-sentence gap description.
6. For each gap, suggest a fix.

Output: ONLY JSON conforming to the spec.
PROMPT
echo ""
echo "Then count evaluation_points where grade not in (A, N/A) - that's the finding count per fixture."
