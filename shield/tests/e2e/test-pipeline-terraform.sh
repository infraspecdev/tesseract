#!/usr/bin/env bash
set -euo pipefail
trap 'trap - INT TERM; kill -- -$$ 2>/dev/null; wait; exit 1' INT TERM

# E2E Pipeline Test: Terraform VPC
# Runs all phases sequentially against a shared project.
#
# Usage:
#   ./test-pipeline-terraform.sh                    # Full pipeline
#   ./test-pipeline-terraform.sh research           # Single phase (cold fixture)
#   ./test-pipeline-terraform.sh plan --warm        # Single phase (run prior phases first)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/framework.sh"
check_claude

EXAMPLE="terraform-vpc"
PHASE_ARG="${1:-}"
WARM_FLAG="${2:-}"

# --- Single phase mode ---
if [ -n "$PHASE_ARG" ] && [ "$PHASE_ARG" != "all" ]; then
  echo "=== Phase Test: $PHASE_ARG ($EXAMPLE) ==="
  echo ""

  source "$PHASES_DIR/${PHASE_ARG}.sh"

  if [ "$WARM_FLAG" = "--warm" ]; then
    PROJECT_DIR=$(prepare_project "initialized" "$EXAMPLE")
    INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)
    export INIT_REF

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

    run_phase_test "$PHASE_ARG" "$EXAMPLE" "$PROJECT_DIR"
  else
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
echo "=== Pipeline Test: Terraform VPC ==="
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

run_phase_test "implement"   "$EXAMPLE" "$PROJECT_DIR"
check_gate

run_phase_test "review"      "$EXAMPLE" "$PROJECT_DIR"

echo ""
echo "================================================================"
echo "Pipeline Test Complete: Terraform VPC"
echo "================================================================"
print_summary
