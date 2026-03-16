#!/usr/bin/env bash
set -euo pipefail
trap 'trap - INT TERM; kill -- -$$ 2>/dev/null; wait; exit 1' INT TERM

# E2E Pipeline Test: Python API
# Runs all phases sequentially against a shared project.
#
# Usage:
#   ./test-pipeline-python.sh                    # Full pipeline
#   ./test-pipeline-python.sh research           # Single phase (cold fixture)
#   ./test-pipeline-python.sh plan --warm        # Single phase (run prior phases first)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/framework.sh"
check_claude

EXAMPLE="python-api"
PHASE_ARG="${1:-}"
WARM_FLAG="${2:-}"

# --- Single phase mode ---
if [ -n "$PHASE_ARG" ] && [ "$PHASE_ARG" != "all" ]; then
  echo "=== Phase Test: $PHASE_ARG ($EXAMPLE) ==="
  echo ""

  # Load phase to get its fixture requirement
  source "$PHASES_DIR/${PHASE_ARG}.sh"

  if [ "$WARM_FLAG" = "--warm" ]; then
    # Warm: start from initialized, run prior phases live
    PROJECT_DIR=$(prepare_project "initialized" "$EXAMPLE")
    INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)
    export INIT_REF

    # Run prerequisite phases based on fixture level
    case "$PHASE_FIXTURE" in
      post-research)
        run_phase_test "research" "$EXAMPLE" "$PROJECT_DIR"
        check_gate
        ;;
      post-planning)
        run_phase_test "research" "$EXAMPLE" "$PROJECT_DIR"
        check_gate
        run_phase_test "plan" "$EXAMPLE" "$PROJECT_DIR"
        check_gate
        ;;
      post-implement)
        run_phase_test "research" "$EXAMPLE" "$PROJECT_DIR"
        check_gate
        run_phase_test "plan" "$EXAMPLE" "$PROJECT_DIR"
        check_gate
        run_phase_test "implement" "$EXAMPLE" "$PROJECT_DIR"
        check_gate
        ;;
    esac

    # Run the requested phase
    run_phase_test "$PHASE_ARG" "$EXAMPLE" "$PROJECT_DIR"
  else
    # Cold: use pre-baked fixtures for fast setup
    PROJECT_DIR=$(prepare_project "$PHASE_FIXTURE" "$EXAMPLE")
    INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)
    export INIT_REF
    run_phase_test "$PHASE_ARG" "$EXAMPLE" "$PROJECT_DIR"
  fi

  echo ""
  print_summary
  exit $?
fi

# --- Full pipeline mode ---
echo "=== Pipeline Test: Python API ==="
echo ""

PROJECT_DIR=$(prepare_project "initialized" "$EXAMPLE")
INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)
export INIT_REF

echo "Project: $PROJECT_DIR"
echo "Output:  $E2E_OUTPUT_DIR"
echo ""

run_phase_test "research"    "$EXAMPLE" "$PROJECT_DIR"
check_gate

run_phase_test "plan"        "$EXAMPLE" "$PROJECT_DIR"
check_gate

run_phase_test "plan-review" "$EXAMPLE" "$PROJECT_DIR"
check_gate

run_phase_test "pm-status"   "$EXAMPLE" "$PROJECT_DIR"
# pm-status failure is not a gate

run_phase_test "implement"   "$EXAMPLE" "$PROJECT_DIR"
check_gate

run_phase_test "review"      "$EXAMPLE" "$PROJECT_DIR"

echo ""
echo "================================================================"
echo "Pipeline Test Complete: Python API"
echo "================================================================"
print_summary
