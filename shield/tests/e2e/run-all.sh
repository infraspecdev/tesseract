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

# Shared output directory for token tracking
export E2E_OUTPUT_DIR="/tmp/shield-e2e-$(date +%s)"
mkdir -p "$E2E_OUTPUT_DIR"

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

# Token usage summary
echo ""
echo "--- Token Usage ---"
GRAND_INPUT=0
GRAND_OUTPUT=0
GRAND_CACHE_READ=0
for jsonl_file in "$E2E_OUTPUT_DIR"/*.jsonl; do
  [ -f "$jsonl_file" ] || continue
  test_name=$(basename "$jsonl_file" .jsonl)
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
  read -r inp out cache <<< "$tokens"
  GRAND_INPUT=$((GRAND_INPUT + inp))
  GRAND_OUTPUT=$((GRAND_OUTPUT + out))
  GRAND_CACHE_READ=$((GRAND_CACHE_READ + cache))
  if [ "$inp" -gt 0 ] || [ "$out" -gt 0 ]; then
    printf "  %-25s %6d in / %6d out (cache: %d)\n" "$test_name" "$inp" "$out" "$cache"
  fi
done
echo "  -----------------------------------------------"
printf "  %-25s %6d in / %6d out (cache: %d)\n" "TOTAL" "$GRAND_INPUT" "$GRAND_OUTPUT" "$GRAND_CACHE_READ"

# Estimate cost (Sonnet pricing: $3/M input, $15/M output)
COST=$(python3 -c "
inp = $GRAND_INPUT
out = $GRAND_OUTPUT
cost = (inp / 1_000_000) * 3 + (out / 1_000_000) * 15
print(f'\${cost:.4f}')
" 2>/dev/null || echo "unknown")
echo "  Estimated cost: $COST"
echo ""
echo "Output saved: $E2E_OUTPUT_DIR"

if [ "$TOTAL_FAIL" -gt 0 ]; then
  exit 1
fi
