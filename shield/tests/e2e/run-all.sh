#!/usr/bin/env bash
set -euo pipefail

# Shield E2E test runner
# Runs all E2E tests using headless Claude Code sessions
#
# Usage:
#   ./run-all.sh              # Run all tests
#   ./run-all.sh test-review  # Run a single test
#
# Requirements:
#   - claude CLI installed and authenticated
#   - Runs locally only (uses --dangerously-skip-permissions)
#
# Timing: ~2-5 minutes per test, ~15-30 minutes total

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check prerequisites
if ! command -v claude &>/dev/null; then
  echo "ERROR: claude CLI not found. Install Claude Code first."
  echo "These tests require a local Claude Code installation."
  exit 1
fi

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0
RESULTS=()

run_test_file() {
  local test_file="$1"
  local test_name
  test_name=$(basename "$test_file" .sh)

  echo ""
  echo "================================================================"
  echo "Running: $test_name"
  echo "================================================================"

  local output
  if output=$(bash "$test_file" 2>&1); then
    echo "$output"
    RESULTS+=("PASS: $test_name")
    TOTAL_PASS=$((TOTAL_PASS + 1))
  else
    echo "$output"
    RESULTS+=("FAIL: $test_name")
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
  fi
}

echo "=== Shield E2E Test Suite ==="
echo "Plugin: $SCRIPT_DIR/../.."
echo "Claude: $(claude --version 2>/dev/null || echo 'unknown')"
echo ""

if [ -n "${1:-}" ]; then
  # Run specific test
  TEST_FILE="$SCRIPT_DIR/${1}.sh"
  if [ ! -f "$TEST_FILE" ]; then
    TEST_FILE="$SCRIPT_DIR/test-${1}.sh"
  fi
  if [ ! -f "$TEST_FILE" ]; then
    echo "Test not found: $1"
    echo "Available tests:"
    ls "$SCRIPT_DIR"/test-*.sh | xargs -I{} basename {} .sh | sed 's/^/  /'
    exit 1
  fi
  run_test_file "$TEST_FILE"
else
  # Run all tests
  for test_file in "$SCRIPT_DIR"/test-*.sh; do
    [ -f "$test_file" ] && run_test_file "$test_file"
  done
fi

echo ""
echo "================================================================"
echo "E2E Test Summary"
echo "================================================================"
for result in "${RESULTS[@]}"; do
  echo "  $result"
done
echo ""
echo "Total: $TOTAL_PASS passed, $TOTAL_FAIL failed"

if [ "$TOTAL_FAIL" -gt 0 ]; then
  exit 1
fi
