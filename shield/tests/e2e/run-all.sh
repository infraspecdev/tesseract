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
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
_RUN_TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
if [ -n "$SPECIFIC_TEST" ]; then
  export E2E_OUTPUT_DIR="${SHIELD_ROOT}/tests/output/${_RUN_TIMESTAMP}-${SPECIFIC_TEST}"
else
  export E2E_OUTPUT_DIR="${SHIELD_ROOT}/tests/output/${_RUN_TIMESTAMP}-all"
fi
mkdir -p "$E2E_OUTPUT_DIR"

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0
RESULTS=()

print_suite_summary() {
  local summary_file="${E2E_OUTPUT_DIR}/summary.txt"

  {
    echo "================================================================"
    echo "Shield E2E Test Suite Summary"
    echo "================================================================"
    echo "Date:    $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Output:  ${E2E_OUTPUT_DIR}"
    echo ""

    echo "--- Test Results ---"
    for result in "${RESULTS[@]}"; do
      echo "  $result"
    done
    echo ""
    echo "Total: $TOTAL_PASS passed, $TOTAL_FAIL failed"
    echo ""

    echo "--- Token Usage ---"
    local grand_input=0 grand_output=0 grand_cache_read=0 grand_cache_write=0

    for jsonl_file in "$E2E_OUTPUT_DIR"/*.jsonl; do
      [ -f "$jsonl_file" ] || continue
      local fname
      fname=$(basename "$jsonl_file" .jsonl)
      local tokens
      tokens=$(python3 -c "
import json
i=o=cr=cw=0
for line in open('$jsonl_file'):
    line = line.strip()
    if not line: continue
    try: data = json.loads(line)
    except: continue
    u = data.get('usage', {})
    if u:
        i += u.get('input_tokens', 0)
        o += u.get('output_tokens', 0)
        cr += u.get('cache_read_input_tokens', u.get('cache_read', 0))
        cw += u.get('cache_creation_input_tokens', u.get('cache_creation', 0))
print(f'{i} {o} {cr} {cw}')
" 2>/dev/null || echo "0 0 0 0")
      local inp out cr cw
      read -r inp out cr cw <<< "$tokens"
      grand_input=$((grand_input + inp))
      grand_output=$((grand_output + out))
      grand_cache_read=$((grand_cache_read + cr))
      grand_cache_write=$((grand_cache_write + cw))
      if [ "$inp" -gt 0 ] || [ "$out" -gt 0 ]; then
        printf "  %-40s %7s in / %7s out  (cache read: %s, write: %s)\n" \
          "$fname" "$inp" "$out" "$cr" "$cw"
      fi
    done

    echo "  ----------------------------------------"
    printf "  %-40s %7s in / %7s out  (cache read: %s, write: %s)\n" \
      "TOTAL" "$grand_input" "$grand_output" "$grand_cache_read" "$grand_cache_write"

    local cost
    cost=$(python3 -c "
i=$grand_input; o=$grand_output; cr=$grand_cache_read; cw=$grand_cache_write
cost = (i*3 + o*15 + cr*0.30 + cw*3.75) / 1_000_000
print(f'\${cost:.4f}')
" 2>/dev/null || echo "unknown")
    echo "  Estimated cost (Sonnet pricing): $cost"

    local total_ctx=$((grand_input + grand_cache_read + grand_cache_write))
    if [ "$total_ctx" -gt 0 ]; then
      local hit_rate
      hit_rate=$(python3 -c "print(f'{$grand_cache_read / $total_ctx * 100:.1f}%')" 2>/dev/null || echo "n/a")
      echo "  Cache hit rate: $hit_rate"
    fi
    echo ""

    if [ "$TOTAL_FAIL" -gt 0 ]; then
      echo "FAILED"
    else
      echo "ALL TESTS PASSED"
    fi
  } | tee "$summary_file"

  echo ""
  echo "Summary written to: $summary_file"
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
      print_suite_summary
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

print_suite_summary

if [ "$TOTAL_FAIL" -gt 0 ]; then
  exit 1
fi
