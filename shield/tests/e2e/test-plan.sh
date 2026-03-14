#!/usr/bin/env bash
set -euo pipefail

# E2E test: /plan command
# Verifies the plan-docs skill is invoked

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /plan ==="

PROJECT_DIR=$(create_shield_test_project "test-plan" "terraform")
trap 'cleanup_test_project "$PROJECT_DIR"' EXIT

echo "Project: $PROJECT_DIR"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /plan to create an execution plan for a VPC module with IPAM integration" \
  3 120)

echo "--- Assertions ---"
assert_any_skill_invoked "$OUTPUT" "plan|plan-docs|writing-plans|brainstorming" "planning invoked"
assert_no_premature_action "$OUTPUT" "no action before skill load"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
