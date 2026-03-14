#!/usr/bin/env bash
set -euo pipefail

# E2E Pipeline Test: Terraform VPC
# Runs the full Shield pipeline sequentially against the terraform-vpc example.
# Verifies artifacts produced by each phase, not just skill invocation.
#
# Timing: ~15-25 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== Pipeline Test: Terraform VPC ==="
echo ""

# Copy example to temp dir
EXAMPLE_DIR="$SHIELD_ROOT/examples/terraform-vpc"
PROJECT_DIR=$(mktemp -d)
cp -r "$EXAMPLE_DIR"/* "$EXAMPLE_DIR"/.tesseract.json "$PROJECT_DIR/"
git -C "$PROJECT_DIR" init -q
git -C "$PROJECT_DIR" add .
git -C "$PROJECT_DIR" commit -q -m "init terraform-vpc example" --no-gpg-sign
INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)
trap 'rm -rf "$PROJECT_DIR"' EXIT

echo "Project: $PROJECT_DIR"
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

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /research to investigate AWS VPC best practices for multi-AZ deployment with IPAM. Write findings to a file called research.md in the project root." \
  5 180)

# Skill invocation
assert_skill_invoked "$OUTPUT" "research" "research skill invoked"

# Artifact: research output contains substance
assert_output_contains "$OUTPUT" "VPC\|vpc\|subnet\|CIDR\|availability.zone" \
  "research output mentions VPC concepts"

report_tokens "$OUTPUT" "1-research"
check_phase
echo ""

# ================================================================
# Phase 2: Planning
# ================================================================
echo "================================================================"
echo "Phase 2: Planning"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /plan to create an execution plan for improving the VPC module in src/. Focus on fixing security issues (wildcard IAM, open SSH) and cost issues (NAT gateways). Write the plan sidecar to plan-sidecar.json in the project root. The sidecar must have at least 1 epic with 2 stories, each with acceptance_criteria. Also create a plan.html file." \
  8 300)

# Skill invocation (accept Shield or superpowers planning skills)
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

# Artifact: sidecar JSON created and valid
if [ -f "$PROJECT_DIR/plan-sidecar.json" ]; then
  assert_json_valid "$PROJECT_DIR/plan-sidecar.json" \
    "$SHIELD_ROOT/schemas/plan-sidecar.schema.json" \
    "sidecar validates against schema"

  assert_json_field "$PROJECT_DIR/plan-sidecar.json" \
    "len(data.get('epics', [])) > 0" \
    "sidecar has at least 1 epic"

  assert_json_field "$PROJECT_DIR/plan-sidecar.json" \
    "any(len(e.get('stories',[])) > 0 for e in data.get('epics',[]))" \
    "sidecar has stories"

  assert_json_field "$PROJECT_DIR/plan-sidecar.json" \
    "any(len(s.get('acceptance_criteria',[])) > 0 for e in data.get('epics',[]) for s in e.get('stories',[]))" \
    "stories have acceptance criteria"
else
  echo "  [FAIL] plan-sidecar.json not created"
  FAIL=$((FAIL + 1))
fi

report_tokens "$OUTPUT" "2-plan"
check_phase
echo ""

# ================================================================
# Phase 3: Plan Review
# ================================================================
echo "================================================================"
echo "Phase 3: Plan Review"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /plan-review to review the plan. Look for any plan files in the project. Produce a review with grades (A-F) for each reviewer." \
  8 240)

assert_skill_invoked "$OUTPUT" "plan-review" "plan-review skill invoked"

# Artifact: review contains grades
assert_output_contains "$OUTPUT" "Grade.*[A-F]\|grade.*[A-F]\|[A-F].*grade" \
  "review output contains grades"

report_tokens "$OUTPUT" "3-plan-review"
check_phase
echo ""

# ================================================================
# Phase 4: PM Status (no PM configured)
# ================================================================
echo "================================================================"
echo "Phase 4: PM Status (graceful no-PM)"
echo "================================================================"

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /pm-status to check sprint status" \
  3 60)

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

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /implement to fix the security issue in src/main.tf: the flow log IAM policy (aws_iam_role_policy.flow_log) has Resource = \"*\" — scope it to the specific CloudWatch log group ARN using aws_cloudwatch_log_group.flow_logs.arn. Make the change and commit it." \
  8 240)

assert_skill_invoked "$OUTPUT" "implement-feature" "implement-feature skill invoked"

# Artifact: code was changed and committed
assert_git_commits_since "$PROJECT_DIR" "$INIT_REF" "new commits from implementation"

# Artifact: the specific fix was applied
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

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /review to review the Terraform code in src/. Check for remaining security, cost, and architecture issues. Report specific findings with severity." \
  8 300)

assert_skill_invoked "$OUTPUT" "review" "review skill invoked"

# Artifact: specific findings from the intentionally insecure module
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
