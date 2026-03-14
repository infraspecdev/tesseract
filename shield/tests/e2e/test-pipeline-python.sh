#!/usr/bin/env bash
set -euo pipefail

# E2E Pipeline Test: Python API
# Runs the full Shield pipeline sequentially against the python-api example:
#   research → plan → plan-review → pm-status → implement → review
#
# Tests the application domain flow (non-infrastructure).
#
# Timing: ~10-20 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== Pipeline Test: Python API ==="
echo ""

# Copy example to temp dir
EXAMPLE_DIR="$SHIELD_ROOT/examples/python-api"
PROJECT_DIR=$(mktemp -d)
cp -r "$EXAMPLE_DIR"/* "$EXAMPLE_DIR"/.tesseract.json "$PROJECT_DIR/"
git -C "$PROJECT_DIR" init -q
git -C "$PROJECT_DIR" add .
git -C "$PROJECT_DIR" commit -q -m "init python-api example" --no-gpg-sign
trap 'rm -rf "$PROJECT_DIR"' EXIT

echo "Project: $PROJECT_DIR"
echo ""

# --- Phase 1: Research ---
echo "================================================================"
echo "Phase 1: Research"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /research to investigate FastAPI best practices for input validation and authentication. Keep it brief." \
  3 120)

assert_skill_invoked "$OUTPUT" "research" "research skill invoked"
report_tokens "$OUTPUT" "1-research"
echo ""

# --- Phase 2: Plan ---
echo "================================================================"
echo "Phase 2: Planning"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /plan to create an execution plan for improving the API in src/. Focus on adding input validation and error handling. Generate stories with acceptance criteria." \
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
  "Use /plan-review to review the plan. If no plan file found, review the code in src/ for improvement opportunities." \
  5 180)

assert_skill_invoked "$OUTPUT" "plan-review" "plan-review skill invoked"
report_tokens "$OUTPUT" "3-plan-review"
echo ""

# --- Phase 4: PM Status ---
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
  "Use /implement to add input validation to the create_task endpoint in src/routes/tasks.py. Use the Task Pydantic model from src/models.py instead of accepting raw dict. Just fix this one endpoint and commit." \
  5 180)

assert_skill_invoked "$OUTPUT" "implement-feature" "implement-feature skill invoked"
report_tokens "$OUTPUT" "5-implement"
echo ""

# --- Phase 6: Review ---
echo "================================================================"
echo "Phase 6: Review"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /review to review the Python code in src/. Check for security issues like missing validation, auth gaps, and error handling." \
  5 180)

assert_skill_invoked "$OUTPUT" "review" "review skill invoked"
assert_output_contains "$OUTPUT" "validation\|auth\|security\|input" "security/validation findings present"
report_tokens "$OUTPUT" "6-review"
echo ""

# --- Summary ---
echo "================================================================"
echo "Pipeline Test Complete: Python API"
echo "================================================================"
print_summary
