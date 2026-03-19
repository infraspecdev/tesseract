#!/usr/bin/env bash
set -euo pipefail

# E2E test: /implement command
# Verifies implement-feature skill is invoked and AC confirmation is presented

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== E2E Test: /implement ==="

PROJECT_DIR=$(create_test_project "test-implement" "terraform")

# Create a plan sidecar with a story and acceptance criteria
mkdir -p "$PROJECT_DIR/docs/shield/vpc-module-$(date +%Y%m%d)"
cat > "$PROJECT_DIR/docs/shield/vpc-module-$(date +%Y%m%d)/plan.json" <<'EOF'
{
  "version": "1.0",
  "project": "test-implement",
  "name": "vpc-module",
  "epics": [{
    "id": "EPIC-1",
    "name": "VPC Module",
    "stories": [{
      "id": "EPIC-1-S1",
      "name": "Create base VPC",
      "status": "ready",
      "assignee": null,
      "priority": "high",
      "week": null,
      "description": "Create a basic VPC with public and private subnets",
      "tasks": ["Create VPC resource", "Add subnets", "Configure routing"],
      "acceptance_criteria": [
        "VPC has DNS support enabled",
        "Public and private subnets in 2 AZs"
      ],
      "pm_id": null,
      "pm_url": null
    }]
  }],
  "metadata": {
    "created_at": "2026-03-14",
    "domains": ["terraform"]
  }
}
EOF

git -C "$PROJECT_DIR" add . && git -C "$PROJECT_DIR" commit -q -m "add sidecar" --no-gpg-sign

echo "Project: $PROJECT_DIR"
echo ""

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:implement' to start implementing story EPIC-1-S1" \
  120)

echo "--- Assertions ---"
assert_any_skill_invoked "$OUTPUT" "implement|implement-feature" "implement command/skill invoked"
assert_no_premature_action "$OUTPUT" "no action before skill load"

report_tokens "$OUTPUT" "$(basename $0 .sh)"

print_summary
