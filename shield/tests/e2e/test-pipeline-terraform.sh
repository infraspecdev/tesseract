#!/usr/bin/env bash
set -euo pipefail
trap 'trap - INT TERM; kill -- -$$ 2>/dev/null; wait; exit 1' INT TERM

# E2E Pipeline Test: Terraform VPC
# Runs the full Shield SDLC pipeline as independent phases.
# Each phase is a fresh Claude session that reads artifacts from disk.
# No session resumption — keeps context small for Sonnet compatibility.
#
# Timing: ~10-20 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== Pipeline Test: Terraform VPC ==="
echo ""

# Create project inside the output dir
PROJECT_DIR=$(create_test_project_from_example "$SHIELD_ROOT/examples/terraform-vpc")
INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)

echo "Project: $PROJECT_DIR"
echo "Output:  $E2E_OUTPUT_DIR"
echo ""

check_phase() {
  if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "STOPPING: phase failed — subsequent phases depend on this output"
    print_summary
    exit 1
  fi
}

# ================================================================
# Phase 1: Research
# ================================================================
echo "================================================================"
echo "Phase 1: Research"
echo "================================================================"

run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:research' to investigate AWS VPC best practices for multi-AZ deployment with IPAM." \
  1200
OUTPUT="$LAST_OUTPUT"

assert_skill_invoked "$OUTPUT" "research" "research skill invoked"
assert_output_contains "$OUTPUT" "VPC\|vpc\|subnet\|CIDR\|availability.zone" \
  "research mentions VPC concepts"
assert_file_glob "$PROJECT_DIR" "shield/*/docs/research.md" "research.md created in docs dir"

report_tokens "$OUTPUT" "1-research"
check_phase
echo ""

# ================================================================
# Phase 2: Planning
# ================================================================
echo "================================================================"
echo "Phase 2: Planning"
echo "================================================================"

run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:plan-docs' to create an execution plan for improving the VPC module in src/. Focus on fixing security issues (wildcard IAM, open SSH) and cost issues (NAT gateways)." \
  1200
OUTPUT="$LAST_OUTPUT"

assert_any_skill_invoked "$OUTPUT" "plan|plan-docs" "plan-docs skill invoked"

SIDECAR=$(find "$PROJECT_DIR/shield" -name "plan-sidecar.json" -type f 2>/dev/null | head -1)
if [ -n "$SIDECAR" ]; then
  assert_json_valid "$SIDECAR" \
    "$SHIELD_ROOT/schemas/plan-sidecar.schema.json" \
    "sidecar validates against schema"
  assert_json_field "$SIDECAR" \
    "len(data.get('epics', [])) > 0" \
    "sidecar has at least 1 epic"
  assert_json_field "$SIDECAR" \
    "any(len(e.get('stories',[])) > 0 for e in data.get('epics',[]))" \
    "sidecar has stories"
  assert_json_field "$SIDECAR" \
    "any(len(s.get('acceptance_criteria',[])) > 0 for e in data.get('epics',[]) for s in e.get('stories',[]))" \
    "stories have acceptance criteria"
else
  echo "  [FAIL] plan-sidecar.json not created in run dir"
  FAIL=$((FAIL + 1))
fi

assert_file_glob "$PROJECT_DIR" "shield/*/architecture.html" "architecture.html created"
assert_file_glob "$PROJECT_DIR" "shield/*/plan.html" "plan.html created"

report_tokens "$OUTPUT" "2-plan"
check_phase
echo ""

# ================================================================
# Phase 3: Plan Review
# ================================================================
echo "================================================================"
echo "Phase 3: Plan Review"
echo "================================================================"

run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:plan-review' to review the plan. Produce a review with grades (A-F) for each reviewer." \
  1200
OUTPUT="$LAST_OUTPUT"

assert_skill_invoked "$OUTPUT" "plan-review" "plan-review skill invoked"
assert_output_contains "$OUTPUT" "Grade.*[A-F]\|grade.*[A-F]\|[A-F].*grade" \
  "review output contains grades"

report_tokens "$OUTPUT" "3-plan-review"
check_phase
echo ""

# ================================================================
# Phase 4: PM Status
# ================================================================
echo "================================================================"
echo "Phase 4: PM Status (graceful no-PM)"
echo "================================================================"

run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:pm-status' to check sprint status." \
  1200
OUTPUT="$LAST_OUTPUT"

assert_output_contains "$OUTPUT" "init\|configure\|not configured\|no PM\|set up" \
  "suggests setup when PM not configured"
assert_output_not_contains "$OUTPUT" "Traceback\|FATAL\|panic\|segfault" \
  "no crashes"

report_tokens "$OUTPUT" "4-pm-status"
check_phase
echo ""

# ================================================================
# Phase 5: Implementation
# ================================================================
echo "================================================================"
echo "Phase 5: Implementation"
echo "================================================================"

run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:implement' to fix the security issue in src/main.tf: the flow log IAM policy (aws_iam_role_policy.flow_log) has Resource = \"*\" — scope it to the specific CloudWatch log group ARN using aws_cloudwatch_log_group.flow_logs.arn. Make the change and commit it." \
  1200
OUTPUT="$LAST_OUTPUT"

assert_any_skill_invoked "$OUTPUT" "implement|implement-feature" "implement skill invoked"
assert_git_commits_since "$PROJECT_DIR" "$INIT_REF" "new commits from implementation"

if grep -q 'aws_cloudwatch_log_group.flow_logs.arn\|flow_logs\.arn' "$PROJECT_DIR/src/main.tf" 2>/dev/null; then
  echo "  [PASS] IAM policy scoped to log group ARN"
  PASS=$((PASS + 1))
else
  echo "  [FAIL] IAM policy still has Resource = *"
  FAIL=$((FAIL + 1))
fi

report_tokens "$OUTPUT" "5-implement"
check_phase
echo ""

# ================================================================
# Phase 6: Review
# ================================================================
echo "================================================================"
echo "Phase 6: Review"
echo "================================================================"

run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:review' to review the Terraform code in src/. Check for remaining security, cost, and architecture issues. Report specific findings with severity." \
  1200
OUTPUT="$LAST_OUTPUT"

assert_skill_invoked "$OUTPUT" "review" "review skill invoked"
assert_output_contains "$OUTPUT" "NAT\|nat_gateway\|nat gateway" \
  "finds NAT gateway cost issue"
assert_output_contains "$OUTPUT" "0\.0\.0\.0/0\|SSH\|port 22\|open.*22" \
  "finds open SSH security issue"
assert_output_contains "$OUTPUT" "severity\|Severity\|critical\|Critical\|important\|Important" \
  "findings include severity levels"

report_tokens "$OUTPUT" "6-review"
echo ""

# ================================================================
echo "================================================================"
echo "Pipeline Test Complete: Terraform VPC"
echo "================================================================"
print_summary
