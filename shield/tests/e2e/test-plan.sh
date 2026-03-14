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
# Shield's plan-docs skill or superpowers' writing-plans/brainstorming are all valid
# When superpowers is installed, it may handle planning instead of Shield's skill
if assert_skill_invoked "$OUTPUT" "plan-docs" "shield plan-docs skill invoked" 2>/dev/null; then
  true
elif assert_skill_invoked "$OUTPUT" "writing-plans" "superpowers writing-plans skill invoked (acceptable)" 2>/dev/null; then
  true
elif assert_skill_invoked "$OUTPUT" "brainstorming" "superpowers brainstorming skill invoked (acceptable)" 2>/dev/null; then
  true
else
  echo "  [FAIL] no planning skill invoked"
  FAIL=$((FAIL + 1))
fi
assert_no_premature_action "$OUTPUT" "no action before skill load"

print_summary
