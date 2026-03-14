#!/usr/bin/env bash
set -euo pipefail

# E2E test: /shield init command
# Verifies init command is triggered and handles a fresh project

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /shield init ==="

# Create a bare project with NO .tesseract.json
PROJECT_DIR=$(mktemp -d)
git -C "$PROJECT_DIR" init -q
echo "# Test" > "$PROJECT_DIR/README.md"
git -C "$PROJECT_DIR" add . && git -C "$PROJECT_DIR" commit -q -m "init" --no-gpg-sign
trap 'rm -rf "$PROJECT_DIR"' EXIT

echo "Project: $PROJECT_DIR (no .tesseract.json)"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /shield init to set up this project. Project name: e2e-test. Domains: terraform. PM tool: none." \
  5 120)

echo "--- Assertions ---"
assert_output_contains "$OUTPUT" "init\|initialized\|created\|tesseract.json" \
  "init process mentioned"
assert_output_not_contains "$OUTPUT" "Error\|Traceback\|exception" \
  "no errors during init"

print_summary
