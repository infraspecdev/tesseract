#!/usr/bin/env bash
set -euo pipefail

# E2E Pipeline Test: Terraform VPC
# Runs the full Shield pipeline sequentially against the terraform-vpc example:
#   research → plan → plan-review → pm-status → implement → review
#
# Each phase builds on the previous one's output. This tests the real-world
# flow where sidecar JSON, summaries, and review findings chain together.
#
# Timing: ~10-20 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== Pipeline Test: Terraform VPC ==="
echo ""

# Copy example to temp dir so we don't pollute the repo
EXAMPLE_DIR="$SHIELD_ROOT/examples/terraform-vpc"
PROJECT_DIR=$(mktemp -d)
cp -r "$EXAMPLE_DIR"/* "$EXAMPLE_DIR"/.tesseract.json "$PROJECT_DIR/"
git -C "$PROJECT_DIR" init -q
git -C "$PROJECT_DIR" add .
git -C "$PROJECT_DIR" commit -q -m "init terraform-vpc example" --no-gpg-sign
trap 'rm -rf "$PROJECT_DIR"' EXIT

echo "Project: $PROJECT_DIR"
echo ""

# --- Phase 1: Research ---
echo "================================================================"
echo "Phase 1: Research"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /research to investigate AWS VPC best practices for multi-AZ deployment with IPAM. Keep it brief — just key findings, no full document." \
  3 120)

assert_skill_invoked "$OUTPUT" "research" "research skill invoked"
report_tokens "$OUTPUT" "1-research"
echo ""

# --- Phase 2: Plan ---
echo "================================================================"
echo "Phase 2: Planning"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /plan to create an execution plan for improving the VPC module in src/. Focus on fixing the security and cost issues. Generate a plan sidecar JSON file at plan-sidecar.json with at least 2 stories with acceptance criteria." \
  5 180)

PLAN_SKILL_FOUND=false
for skill_name in plan-docs writing-plans brainstorming; do
  SKILL_PATTERN="\"skill\":\"([^\"]*:)?${skill_name}\""
  if grep -q '"name":"Skill"' "$OUTPUT" && grep -qE "$SKILL_PATTERN" "$OUTPUT"; then
    echo "  [PASS] planning skill invoked ($skill_name)"
    PASS=$((PASS + 1))
    PLAN_SKILL_FOUND=true
    break
  fi
done
if [ "$PLAN_SKILL_FOUND" = "false" ]; then
  echo "  [FAIL] no planning skill invoked"
  FAIL=$((FAIL + 1))
fi
report_tokens "$OUTPUT" "2-plan"
echo ""

# --- Phase 3: Plan Review ---
echo "================================================================"
echo "Phase 3: Plan Review"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /plan-review to review the plan that was just created. If no plan file is found, review the Terraform code in src/ as a plan for improvement." \
  5 180)

assert_skill_invoked "$OUTPUT" "plan-review" "plan-review skill invoked"
report_tokens "$OUTPUT" "3-plan-review"
echo ""

# --- Phase 4: PM Status (no PM configured — should handle gracefully) ---
echo "================================================================"
echo "Phase 4: PM Status (graceful no-PM)"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /pm-status to check sprint status" \
  3 60)

assert_output_contains "$OUTPUT" "init\|configure\|not configured\|no PM\|set up" \
  "suggests setup when PM not configured"
report_tokens "$OUTPUT" "4-pm-status"
echo ""

# --- Phase 5: Implementation ---
echo "================================================================"
echo "Phase 5: Implementation"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /implement to fix the security issue: the flow log IAM policy has Resource = * — scope it to the specific log group ARN. Just fix this one issue and commit." \
  5 180)

assert_skill_invoked "$OUTPUT" "implement-feature" "implement-feature skill invoked"
report_tokens "$OUTPUT" "5-implement"
echo ""

# --- Phase 6: Review ---
echo "================================================================"
echo "Phase 6: Review"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /review to review the Terraform code in src/. Check for security, cost, and architecture issues." \
  5 180)

assert_skill_invoked "$OUTPUT" "review" "review skill invoked"
assert_output_contains "$OUTPUT" "security\|Security\|IAM\|wildcard" "security findings present"
assert_output_contains "$OUTPUT" "cost\|Cost\|NAT" "cost findings present"
report_tokens "$OUTPUT" "6-review"
echo ""

# --- Summary ---
echo "================================================================"
echo "Pipeline Test Complete: Terraform VPC"
echo "================================================================"
print_summary
