#!/usr/bin/env bash
set -euo pipefail

# E2E test: /shield init command
# Verifies init command is triggered and handles a fresh project

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /shield init ==="

# Create a bare project with NO .shield.json
PROJECT_DIR="${E2E_OUTPUT_DIR}/project"
mkdir -p "$PROJECT_DIR"
git -C "$PROJECT_DIR" init -q
echo "# Test" > "$PROJECT_DIR/README.md"
git -C "$PROJECT_DIR" add . && git -C "$PROJECT_DIR" commit -q -m "init" --no-gpg-sign

echo "Project: $PROJECT_DIR (no .shield.json)"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:init' to set up this project. Project name: e2e-test. Domains: terraform. PM tool: none." \
  120)

echo "--- Assertions ---"
assert_output_contains "$OUTPUT" "init\|initialized\|created\|shield.json" \
  "init process mentioned"
assert_output_not_contains "$OUTPUT" "Traceback\|FATAL\|panic\|segfault" \
  "no crashes during init"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
