#!/usr/bin/env bash
# PRD-Review merge gate — re-runs the EPIC-1-S11 verification.
#
# Dispatches all 9 PM dim prompts against each of the 4 PRD-review test fixtures
# (36 dispatches total), counts findings per dim per fixture, writes a fresh
# prd-review-pm-postchange.json, and compares to the baseline. Exits 1 if the
# merge gate criteria fail.
#
# Usage:
#   ./shield/evals/run-prd-review-merge-gate.sh                  # default paths
#   ./shield/evals/run-prd-review-merge-gate.sh --dry-run        # show plan only
#   ./shield/evals/run-prd-review-merge-gate.sh --jobs 4         # N parallel claude calls
#
# Gate criteria (from shield/evals/baselines/prd-review-pm.json):
#   - PM total findings >= 62 (baseline pm_total_findings)
#   - No fixture regresses by more than 10% from its baseline finding count
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BASELINE="$SCRIPT_DIR/baselines/prd-review-pm.json"
POSTCHANGE="$SCRIPT_DIR/baselines/prd-review-pm-postchange.json"
FIXTURE_DIR="$REPO_ROOT/shield/skills/general/prd-review/test-fixtures"
PROMPT_DIR="$REPO_ROOT/shield/skills/general/prd-review/prompts"

DRY_RUN=0
JOBS=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --jobs) JOBS="$2"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if ! command -v claude >/dev/null 2>&1; then
  echo "merge-gate: requires the \`claude\` CLI in PATH" >&2
  exit 127
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "merge-gate: requires jq" >&2
  exit 127
fi

# Fixture name → fixture file basename → expected PRD type
# Lean PRDs get prd_type=lean; everything else is standard. The dim 9 and dim 10
# prompts use prd_type to apply the lean-mode informational exemption.
FIXTURES=(
  "well-formed-standard:standard"
  "standard-with-gaps:standard"
  "lean-with-gaps:lean"
  "internal-tool:standard"
)

# Prompt slug → dim id → dim name (used in postchange.json output)
PROMPTS=(
  "problem-clarity:1:problem_clarity"
  "scope-discipline:2:scope_boundaries"
  "measurable-success:3:measurable_success"
  "raci-and-approvals:7:raci_approvals"
  "legal-privacy-compliance:8:legal_privacy"
  "gtm-customer-comms:9:gtm_comms"
  "support-cx-impact:10:support_cx"
  "why-now-cost-of-inaction:11:why_now"
  "risks-and-assumptions:12:risks_assumptions"
)

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
RESULTS_DIR="$WORKDIR/results"
mkdir -p "$RESULTS_DIR"

dispatch_one() {
  local prompt_slug="$1"
  local dim_id="$2"
  local fixture_name="$3"
  local prd_type="$4"

  local prompt_file="$PROMPT_DIR/${prompt_slug}.md"
  local fixture_file="$FIXTURE_DIR/${fixture_name}.md"
  local out_file="$RESULTS_DIR/${fixture_name}__dim${dim_id}.json"

  if [[ ! -f "$prompt_file" ]]; then
    echo "MISSING PROMPT: $prompt_file" >&2
    return 1
  fi
  if [[ ! -f "$fixture_file" ]]; then
    echo "MISSING FIXTURE: $fixture_file" >&2
    return 1
  fi

  local wrapper_prompt
  wrapper_prompt=$(cat <<EOF
Read the prompt file at $prompt_file and apply it verbatim as your operating prompt.

Inputs:
- prd_path: $fixture_file
- prd_type: $prd_type

Steps:
1. Read the prompt file to load criteria, exception clause, and output shape.
2. Read the PRD at prd_path. Ignore '> **Gap**:' annotations and any '<!-- ... -->' HTML comments (including the pointer to shield/evals/baselines/ that replaced the old EXPECTED REVIEW OUTCOMES blocks) — those are author / test markers, not PRD content.
3. Grade each evaluation point per the prompt's criteria. Apply the lean-mode exemption or N/A exception if the prompt and inputs indicate it.
4. Return ONLY valid JSON matching the prompt's output_shape. No prose, no markdown fences.
EOF
)

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] $prompt_slug × $fixture_name (prd_type=$prd_type) → $out_file"
    return 0
  fi

  claude --print --dangerously-skip-permissions \
    --append-system-prompt "You are a PRD-review dim grader. Return only the JSON object specified by the prompt — no prose before or after, no markdown fences." \
    <<<"$wrapper_prompt" >"$out_file" 2>"${out_file}.err" || {
      echo "DISPATCH FAILED: $prompt_slug × $fixture_name" >&2
      return 1
    }
}

# Build the work list
WORK=()
for fixture_spec in "${FIXTURES[@]}"; do
  IFS=':' read -r fixture_name prd_type <<<"$fixture_spec"
  for prompt_spec in "${PROMPTS[@]}"; do
    IFS=':' read -r prompt_slug dim_id _dim_name <<<"$prompt_spec"
    WORK+=("$prompt_slug:$dim_id:$fixture_name:$prd_type")
  done
done

echo "merge-gate: ${#WORK[@]} dispatches (${#FIXTURES[@]} fixtures × ${#PROMPTS[@]} prompts), parallelism=$JOBS"
echo "merge-gate: workdir=$WORKDIR"

# Dispatch (sequential by default; --jobs N for naive parallelism)
if [[ "$JOBS" -le 1 ]]; then
  for spec in "${WORK[@]}"; do
    IFS=':' read -r prompt_slug dim_id fixture_name prd_type <<<"$spec"
    echo "  → $prompt_slug × $fixture_name"
    dispatch_one "$prompt_slug" "$dim_id" "$fixture_name" "$prd_type"
  done
else
  # Parallel via xargs. Export the function and required vars.
  export -f dispatch_one
  export PROMPT_DIR FIXTURE_DIR RESULTS_DIR DRY_RUN
  printf '%s\n' "${WORK[@]}" | xargs -P "$JOBS" -I {} bash -c '
    spec="$1"
    IFS=":" read -r prompt_slug dim_id fixture_name prd_type <<<"$spec"
    echo "  → $prompt_slug × $fixture_name"
    dispatch_one "$prompt_slug" "$dim_id" "$fixture_name" "$prd_type"
  ' _ {}
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "merge-gate: dry-run complete; not parsing results."
  exit 0
fi

# Parse + score. Uses uv run since shield/evals/ is the scripts area and we
# don't ship a requirements.txt. jq is sufficient for finding-counting; we use
# python only for the final JSON write and gate comparison.
python3 "$SCRIPT_DIR/_score_merge_gate.py" \
  --results-dir "$RESULTS_DIR" \
  --baseline "$BASELINE" \
  --output "$POSTCHANGE" \
  --fixtures "${FIXTURES[*]}" \
  --prompts "${PROMPTS[*]}"
