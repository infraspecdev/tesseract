#!/usr/bin/env bash
set -euo pipefail

# E2E test: /plan-review command
# Verifies the plan-review skill is invoked and agents are dispatched

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /plan-review ==="

PROJECT_DIR=$(create_shield_test_project "test-plan-review" "terraform")
trap 'cleanup_test_project "$PROJECT_DIR"' EXIT

# Create a sample plan doc for the review to operate on
mkdir -p "$PROJECT_DIR/docs"
cat > "$PROJECT_DIR/docs/plan.md" <<'EOF'
# VPC Module Plan

## Epic 1: Base VPC

### Story 1: IPAM Pool Hierarchy
Set up 3-tier IPAM pool hierarchy with regional sub-pools.

**Tasks:**
- Create top-level pool
- Create regional sub-pools

**Acceptance Criteria:**
- Regional pools allocate /20 CIDRs
- No CIDR overlap across regions

### Story 2: VPC with Subnets
Create VPC with public/private subnet tiers.

**Tasks:**
- Create VPC resource
- Create subnet tiers
- Configure route tables

**Acceptance Criteria:**
- Multi-AZ deployment
- Private subnets have NAT gateway access
EOF

git -C "$PROJECT_DIR" add . && git -C "$PROJECT_DIR" commit -q -m "add plan" --no-gpg-sign

echo "Project: $PROJECT_DIR"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Use /plan-review to review the plan at docs/plan.md" \
  5 180)

echo "--- Assertions ---"
assert_skill_invoked "$OUTPUT" "plan-review" "plan-review skill invoked"
assert_no_premature_action "$OUTPUT" "no action before skill load"

print_summary
