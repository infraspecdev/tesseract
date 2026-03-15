#!/usr/bin/env bash
set -euo pipefail

# E2E test: /research command
# Verifies the research skill is invoked when user asks to research a topic

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /research ==="

PROJECT_DIR=$(create_shield_test_project "test-research" "terraform")
trap 'cleanup_test_project "$PROJECT_DIR"' EXIT

echo "Project: $PROJECT_DIR"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:research' to investigate VPC IPAM best practices for multi-region deployment" \
  3 120)

echo "--- Assertions ---"
assert_skill_invoked "$OUTPUT" "research" "research skill invoked"
assert_no_premature_action "$OUTPUT" "no action before skill load"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
