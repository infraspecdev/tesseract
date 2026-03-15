#!/usr/bin/env bash
set -euo pipefail

# E2E Pipeline Test: Python API
# Runs the full Shield pipeline sequentially against the python-api example.
# Verifies artifacts produced by each phase, not just skill invocation.
#
# Timing: ~15-25 minutes

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
  "Invoke the skill 'shield:research' to investigate FastAPI best practices for input validation and authentication. Write findings to research.md." \
  5 180)

assert_skill_invoked "$OUTPUT" "research" "research skill invoked"
assert_output_contains "$OUTPUT" "validation\|FastAPI\|Pydantic\|auth" \
  "research mentions relevant concepts"

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
  "Invoke the skill 'shield:plan-docs' to create an execution plan for improving the API in src/. Focus on: 1) adding input validation using the Task Pydantic model, 2) adding error handling for missing tasks (404). The plan sidecar JSON must be written to plan-sidecar.json with at least 1 epic and 2 stories, each with acceptance_criteria." \
  10 300)

# Shield's plan-docs MUST run to produce the sidecar
assert_any_skill_invoked "$OUTPUT" "plan|plan-docs" "shield plan-docs invoked (sidecar generation)"

# Artifact: sidecar created with stories
if [ -f "$PROJECT_DIR/plan-sidecar.json" ]; then
  assert_json_field "$PROJECT_DIR/plan-sidecar.json" \
    "len(data.get('epics', [])) > 0" \
    "sidecar has at least 1 epic"

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
  "Invoke the skill 'shield:plan-review' to review the plan. Produce a review with grades (A-F)." \
  8 240)

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

OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Invoke the skill 'shield:pm-status' to check sprint status" \
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
  "Invoke the skill 'shield:implement' to add input validation to the create_task endpoint in src/routes/tasks.py. Change the parameter type from 'task: dict' to use the Task Pydantic model from src/models.py. Also add a 404 response to get_task when the task_id is not found. Make the changes and commit." \
  15 360)

assert_any_skill_invoked "$OUTPUT" "implement|implement-feature" "implement command/skill invoked"

# Artifact: code was changed and committed
assert_git_commits_since "$PROJECT_DIR" "$INIT_REF" "new commits from implementation"

# Artifact: input validation was added (Task model used instead of dict)
if grep -q "Task\|BaseModel" "$PROJECT_DIR/src/routes/tasks.py" 2>/dev/null && \
   ! grep -q "task: dict" "$PROJECT_DIR/src/routes/tasks.py" 2>/dev/null; then
  echo "  [PASS] create_task uses Pydantic model instead of dict"
  PASS=$((PASS + 1))
else
  echo "  [FAIL] create_task still accepts raw dict"
  FAIL=$((FAIL + 1))
fi

# Artifact: 404 handling added
if grep -q "404\|HTTPException\|not found\|NotFound" "$PROJECT_DIR/src/routes/tasks.py" 2>/dev/null; then
  echo "  [PASS] 404 handling added to get_task"
  PASS=$((PASS + 1))
else
  echo "  [FAIL] no 404 handling in get_task"
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
  "Invoke the skill 'shield:review' to review the Python code in src/. Check for remaining security issues (missing auth), missing error handling, and test coverage gaps. Report findings with severity." \
  8 300)

assert_skill_invoked "$OUTPUT" "review" "review skill invoked"

# Artifact: review finds remaining issues
assert_output_contains "$OUTPUT" "auth\|authentication\|Authorization" \
  "finds missing authentication"
assert_output_contains "$OUTPUT" "severity\|Severity\|critical\|Critical\|important\|Important" \
  "findings include severity levels"

report_tokens "$OUTPUT" "6-review"
echo ""

# ================================================================
echo "================================================================"
echo "Pipeline Test Complete: Python API"
echo "================================================================"
print_summary
