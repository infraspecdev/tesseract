#!/usr/bin/env bash
set -euo pipefail

# E2E test: /review command
# Verifies the review orchestrator skill is invoked against the terraform-vpc example

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /review ==="

# Use the terraform-vpc example project
EXAMPLE_DIR="$SHIELD_ROOT/examples/terraform-vpc"

if [ ! -d "$EXAMPLE_DIR" ]; then
  echo "ERROR: terraform-vpc example not found at $EXAMPLE_DIR"
  exit 1
fi

PROJECT_DIR=$(create_test_project_from_example "$EXAMPLE_DIR")

echo "Project: $PROJECT_DIR (copied from terraform-vpc example)"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:review' to review the Terraform code in src/" \
  5 180)

echo "--- Assertions ---"
assert_skill_invoked "$OUTPUT" "review" "review skill invoked"
assert_output_contains "$OUTPUT" "security\|Security" "security concerns mentioned"
assert_output_contains "$OUTPUT" "cost\|Cost\|NAT" "cost concerns mentioned"
assert_no_premature_action "$OUTPUT" "no action before skill load"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
