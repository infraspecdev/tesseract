#!/usr/bin/env bash
set -euo pipefail

# E2E test: /pm-status command
# Verifies graceful handling when no PM tool is configured

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /pm-status (no PM configured) ==="

PROJECT_DIR=$(create_test_project "test-pm-status" "terraform")

echo "Project: $PROJECT_DIR"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:pm-status' to check sprint status" \
  3 60)

echo "--- Assertions ---"
# Should gracefully handle missing PM config — not crash
assert_output_contains "$OUTPUT" "init\|configure\|not configured\|no PM\|set up" \
  "suggests setup when PM not configured"
assert_output_not_contains "$OUTPUT" "Traceback\|FATAL\|panic\|segfault" \
  "no crashes when PM missing"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
