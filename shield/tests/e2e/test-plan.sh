#!/usr/bin/env bash
set -euo pipefail

# E2E test: /plan command
# Verifies the plan-docs skill is invoked

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /plan ==="

PROJECT_DIR=$(create_test_project "test-plan" "terraform")

echo "Project: $PROJECT_DIR"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:plan-docs' to create an execution plan for a VPC module with IPAM integration. Write the plan sidecar JSON to plan-sidecar.json." \
  120)

echo "--- Assertions ---"
# Shield's plan-docs MUST be invoked (produces the sidecar JSON)
# Superpowers may also be invoked for design thinking — that's fine
assert_any_skill_invoked "$OUTPUT" "plan|plan-docs" "shield plan-docs invoked (sidecar generation)"
assert_no_premature_action "$OUTPUT" "no action before skill load"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
