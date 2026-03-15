#!/usr/bin/env bash
set -euo pipefail

# E2E test: /review command
# Verifies the review orchestrator skill is invoked against the terraform-vpc example

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /review ==="

# Use the terraform-vpc example project directly
EXAMPLE_DIR="$SHIELD_ROOT/examples/terraform-vpc"

if [ ! -d "$EXAMPLE_DIR" ]; then
  echo "ERROR: terraform-vpc example not found at $EXAMPLE_DIR"
  exit 1
fi

# Copy to temp dir so we don't pollute the example
PROJECT_DIR=$(mktemp -d)
cp -r "$EXAMPLE_DIR"/* "$EXAMPLE_DIR"/.tesseract.json "$PROJECT_DIR/"
git -C "$PROJECT_DIR" init -q
git -C "$PROJECT_DIR" add .
git -C "$PROJECT_DIR" commit -q -m "init" --no-gpg-sign
trap 'rm -rf "$PROJECT_DIR"' EXIT

echo "Project: $PROJECT_DIR (copied from terraform-vpc example)"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:review' to review the Terraform code in src/" \
  5 180)

echo "--- Assertions ---"
assert_skill_invoked "$OUTPUT" "review" "review skill invoked"
assert_output_contains "$OUTPUT" "security\|Security" "security concerns mentioned"
assert_output_contains "$OUTPUT" "cost\|Cost\|NAT" "cost concerns mentioned"
assert_no_premature_action "$OUTPUT" "no action before skill load"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
