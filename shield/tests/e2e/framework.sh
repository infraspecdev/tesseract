#!/usr/bin/env bash
# Shield E2E test framework
#
# Provides fixture setup and phase execution on top of test-helpers.sh.
# Source this instead of test-helpers.sh directly.
#
# Usage in a phase script:
#   source "$SCRIPT_DIR/../framework.sh"
#   PROJECT_DIR=$(prepare_project "post-research" "python-api")
#   run_phase_test "plan" "python-api" "$PROJECT_DIR"
#
# Usage in a pipeline:
#   source "$SCRIPT_DIR/framework.sh"
#   PROJECT_DIR=$(prepare_project "initialized" "python-api")
#   run_phase_test "research" "python-api" "$PROJECT_DIR"
#   run_phase_test "plan"     "python-api" "$PROJECT_DIR"

FRAMEWORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$FRAMEWORK_DIR/../.." && pwd)"
PHASES_DIR="$FRAMEWORK_DIR/phases"

source "$FRAMEWORK_DIR/test-helpers.sh"
source "$FRAMEWORK_DIR/fixtures/setup-fixture.sh"

# Prepare a project at a given fixture level
# Usage: PROJECT_DIR=$(prepare_project "post-research" "python-api")
prepare_project() {
  local level="$1"
  local example="$2"
  local project_dir="${E2E_OUTPUT_DIR}/project"

  setup_fixture_cold "$level" "$example" "$project_dir" > /dev/null
  echo "$project_dir"
}

# Run a single phase test against a project directory
# Loads the phase definition from phases/<name>.sh, runs Claude, asserts.
# Usage: run_phase_test "research" "python-api" "$PROJECT_DIR"
run_phase_test() {
  local phase_name="$1"
  local example="$2"
  local project_dir="$3"
  local phase_file="$PHASES_DIR/${phase_name}.sh"

  if [ ! -f "$phase_file" ]; then
    echo "ERROR: Phase file not found: $phase_file" >&2
    return 1
  fi

  # Source the phase definition (sets PHASE_FIXTURE, PHASE_TIMEOUT, phase_prompt, phase_assertions)
  source "$phase_file"

  local prompt
  prompt=$(phase_prompt "$example")
  local timeout="${PHASE_TIMEOUT:-1200}"

  echo "================================================================"
  echo "Phase: $phase_name ($example)"
  echo "================================================================"

  run_claude_in_project "$project_dir" "$prompt" "$timeout"
  local output="$LAST_OUTPUT"

  phase_assertions "$project_dir" "$output" "$example"
  report_tokens "$output" "$phase_name"
}

# Write phase result for pipeline aggregation
write_phase_result() {
  local phase_name="$1"
  echo "PASS=$PASS FAIL=$FAIL SKIP=$SKIP" > "${E2E_OUTPUT_DIR}/${phase_name}.result"
}

# Accumulate results from a phase result file
accumulate_phase_result() {
  local file="${E2E_OUTPUT_DIR}/${1}.result"
  [ -f "$file" ] || return 0
  local line
  line=$(cat "$file")
  local p f
  p=$(echo "$line" | grep -o 'PASS=[0-9]*' | cut -d= -f2)
  f=$(echo "$line" | grep -o 'FAIL=[0-9]*' | cut -d= -f2)
  TOTAL_PASS=$((TOTAL_PASS + ${p:-0}))
  TOTAL_FAIL=$((TOTAL_FAIL + ${f:-0}))
}

# Gate: stop pipeline if any assertions failed
check_gate() {
  if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "STOPPING: phase failed — subsequent phases depend on this output"
    print_summary
    exit 1
  fi
}

export -f write_phase_result
export -f accumulate_phase_result
