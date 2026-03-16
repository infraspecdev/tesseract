#!/usr/bin/env bash
set -euo pipefail

# Shield agent eval runner
# Validates agent output against criteria YAML files
#
# Usage: ./run-evals.sh [criteria-file]
# If no file specified, runs all criteria in expected/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPECTED_DIR="${SCRIPT_DIR}/expected"
RESULTS_DIR="${SCRIPT_DIR}/results"
mkdir -p "$RESULTS_DIR"

PASS=0
FAIL=0
WARN=0

check_criteria() {
  local criteria_file="$1"
  local output_file="$2"
  local category="$3"  # must_find, should_find, must_not_false_positive

  python3 -c "
import yaml, re, sys

with open('$criteria_file') as f:
    criteria = yaml.safe_load(f)

with open('$output_file') as f:
    output = f.read()

category = '$category'
items = criteria.get(category, [])
results = []

for item in items:
    item_id = item['id']
    desc = item['description']
    if category == 'must_not_false_positive':
        pattern = item.get('match_absence_in', '')
        found = bool(re.search(pattern, output, re.IGNORECASE)) if pattern else False
        results.append({
            'id': item_id,
            'description': desc,
            'passed': not found,
            'category': category,
        })
    else:
        pattern = item.get('match', '')
        found = bool(re.search(pattern, output, re.IGNORECASE)) if pattern else False
        results.append({
            'id': item_id,
            'description': desc,
            'passed': found,
            'category': category,
        })

for r in results:
    status = 'PASS' if r['passed'] else ('FAIL' if r['category'] == 'must_find' or r['category'] == 'must_not_false_positive' else 'WARN')
    print(f\"{status} [{r['category']}] {r['id']}: {r['description']}\")
" 2>/dev/null
}

run_eval() {
  local criteria_file="$1"
  local basename=$(basename "$criteria_file" .yaml)

  echo "=== Evaluating: $basename ==="

  # Check if a results file exists for this eval
  local output_file="${RESULTS_DIR}/${basename}.txt"
  if [ ! -f "$output_file" ]; then
    echo "  SKIP: No output file at $output_file"
    echo "  To run: capture agent output to $output_file first"
    echo ""
    return
  fi

  for category in must_find should_find must_not_false_positive; do
    check_criteria "$criteria_file" "$output_file" "$category"
  done

  echo ""
}

# Run specified criteria or all
if [ -n "${1:-}" ]; then
  run_eval "$1"
else
  for criteria in "$EXPECTED_DIR"/*.yaml; do
    [ -f "$criteria" ] && run_eval "$criteria"
  done
fi

echo "=== Eval Summary ==="
echo "To generate agent output for evaluation:"
echo "  1. Run the agent against the input module"
echo "  2. Save output to shield/evals/results/<criteria-name>.txt"
echo "  3. Re-run this script"
