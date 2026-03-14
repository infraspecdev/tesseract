#!/usr/bin/env bash
set -euo pipefail

# Shield E2E test runner
# Runs all E2E tests using headless Claude Code sessions
#
# Usage:
#   ./run-all.sh                    # Run all tests (stops on first failure)
#   ./run-all.sh test-review        # Run a single test
#   ./run-all.sh --no-fail-fast     # Run all tests even if some fail
#
# Requirements:
#   - claude CLI installed and authenticated
#   - Runs locally only (uses --dangerously-skip-permissions)
#
# Timing: ~2-5 minutes per test, ~15-30 minutes total

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse flags
FAIL_FAST=true
SPECIFIC_TEST=""
for arg in "$@"; do
  case "$arg" in
    --no-fail-fast) FAIL_FAST=false ;;
    *) SPECIFIC_TEST="$arg" ;;
  esac
done

# Check prerequisites
if ! command -v claude &>/dev/null; then
  echo "ERROR: claude CLI not found. Install Claude Code first."
  echo "These tests require a local Claude Code installation."
  exit 1
fi

# Shared output directory for token tracking
export E2E_OUTPUT_DIR="/tmp/shield-e2e-$(date +%s)"
mkdir -p "$E2E_OUTPUT_DIR"

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0
RESULTS=()

print_token_summary() {
  echo ""
  echo "--- Token Usage ---"
  local grand_input=0
  local grand_output=0
  local grand_cache=0
  for jsonl_file in "$E2E_OUTPUT_DIR"/*.jsonl; do
    [ -f "$jsonl_file" ] || continue
    local test_name
    test_name=$(basename "$jsonl_file" .jsonl)
    local tokens
    tokens=$(python3 -c "
import json
input_t = output_t = cache_r = 0
for line in open('$jsonl_file'):
    line = line.strip()
    if not line: continue
    try:
        data = json.loads(line)
    except: continue
    u = data.get('usage', {})
    if u:
        input_t += u.get('input_tokens', 0)
        output_t += u.get('output_tokens', 0)
        cache_r += u.get('cache_read_input_tokens', u.get('cache_read', 0))
print(f'{input_t} {output_t} {cache_r}')
" 2>/dev/null || echo "0 0 0")
    local inp out cache
    read -r inp out cache <<< "$tokens"
    grand_input=$((grand_input + inp))
    grand_output=$((grand_output + out))
    grand_cache=$((grand_cache + cache))
    if [ "$inp" -gt 0 ] || [ "$out" -gt 0 ]; then
      printf "  %-35s %6d in / %6d out (cache: %d)\n" "$test_name" "$inp" "$out" "$cache"
    fi
  done
  echo "  ---------------------------------------------------"
  printf "  %-35s %6d in / %6d out (cache: %d)\n" "TOTAL" "$grand_input" "$grand_output" "$grand_cache"

  local cost
  cost=$(python3 -c "
inp = $grand_input
out = $grand_output
cost = (inp / 1_000_000) * 3 + (out / 1_000_000) * 15
print(f'\${cost:.4f}')
" 2>/dev/null || echo "unknown")
  echo "  Estimated cost: $cost"
  echo ""
  echo "Output saved: $E2E_OUTPUT_DIR"
}

print_summary() {
  echo ""
  echo "================================================================"
  echo "E2E Test Summary"
  echo "================================================================"
  for result in "${RESULTS[@]}"; do
    echo "  $result"
  done
  echo ""
  echo "Total: $TOTAL_PASS passed, $TOTAL_FAIL failed"
  print_token_summary
}

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

    if [ "$FAIL_FAST" = "true" ]; then
      echo ""
      echo "STOPPING: test failed (fail-fast mode)"
      echo "  Use --no-fail-fast to continue after failures"
      print_summary
      exit 1
    fi
  fi
}

echo "=== Shield E2E Test Suite ==="
echo "Plugin: $(cd "$SCRIPT_DIR/../.." && pwd)"
echo "Claude: $(claude --version 2>/dev/null || echo 'unknown')"
echo "Fail-fast: $FAIL_FAST"
echo ""

if [ -n "$SPECIFIC_TEST" ]; then
  # Run specific test
  TEST_FILE="$SCRIPT_DIR/${SPECIFIC_TEST}.sh"
  if [ ! -f "$TEST_FILE" ]; then
    TEST_FILE="$SCRIPT_DIR/test-${SPECIFIC_TEST}.sh"
  fi
  if [ ! -f "$TEST_FILE" ]; then
    echo "Test not found: $SPECIFIC_TEST"
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

print_summary

if [ "$TOTAL_FAIL" -gt 0 ]; then
  exit 1
fi
