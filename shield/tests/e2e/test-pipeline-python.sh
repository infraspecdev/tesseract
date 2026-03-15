#!/usr/bin/env bash
set -euo pipefail

# E2E Pipeline Test: Python API
# Runs the full Shield SDLC pipeline in a SINGLE Claude session.
# All phases share context — artifacts from earlier phases are available to later ones.
#
# Timing: ~10-20 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== Pipeline Test: Python API (single session) ==="
echo ""

# Create project inside the output dir
PROJECT_DIR=$(create_test_project_from_example "$SHIELD_ROOT/examples/python-api")
INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)

echo "Project: $PROJECT_DIR"
echo "Output:  $E2E_OUTPUT_DIR"
echo ""

# Run the full pipeline in one session
OUTPUT=$(run_claude_in_project "$PROJECT_DIR" \
  "Run the full Shield SDLC pipeline on this project. Execute these phases IN ORDER, invoking each skill with the Skill tool:

Phase 1 — Research:
  Invoke the skill 'shield:research' to investigate FastAPI best practices for input validation and authentication.
  Write the findings to a file called research.md in the project root.

Phase 2 — Planning:
  Invoke the skill 'shield:plan-docs' to create an execution plan for improving the API in src/.
  Focus on: 1) adding input validation using the Task Pydantic model, 2) adding error handling for missing tasks (404).
  Write the plan sidecar JSON to plan-sidecar.json with at least 1 epic and 2 stories, each with acceptance_criteria.

Phase 3 — Plan Review:
  Invoke the skill 'shield:plan-review' to review the plan you just created. Produce a review with grades (A-F).

Phase 4 — PM Status:
  Invoke the skill 'shield:pm-status' to check sprint status.

Phase 5 — Implementation:
  Invoke the skill 'shield:implement' to add input validation to the create_task endpoint in src/routes/tasks.py.
  Change the parameter type from 'task: dict' to use the Task Pydantic model from src/models.py.
  Also add a 404 response to get_task when the task_id is not found.
  Make the changes and commit.

Phase 6 — Review:
  Invoke the skill 'shield:review' to review the Python code in src/.
  Check for remaining security issues (missing auth), missing error handling, and test coverage gaps.
  Report findings with severity.

IMPORTANT: You must invoke each skill using the Skill tool. Do not skip any phase." \
  30 600)

echo ""
echo "--- Assertions ---"
echo ""

# Phase 1: Research
echo "Phase 1: Research"
assert_skill_invoked "$OUTPUT" "research" "research skill invoked"
assert_output_contains "$OUTPUT" "validation\|FastAPI\|Pydantic\|auth" \
  "research mentions relevant concepts"
assert_file_exists "$PROJECT_DIR" "research.md" "research.md created"
echo ""

# Phase 2: Planning
echo "Phase 2: Planning"
assert_any_skill_invoked "$OUTPUT" "plan|plan-docs" "plan-docs skill invoked"
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
echo ""

# Phase 3: Plan Review
echo "Phase 3: Plan Review"
assert_skill_invoked "$OUTPUT" "plan-review" "plan-review skill invoked"
assert_output_contains "$OUTPUT" "Grade.*[A-F]\|grade.*[A-F]\|[A-F].*grade" \
  "review output contains grades"
echo ""

# Phase 4: PM Status
echo "Phase 4: PM Status"
assert_output_not_contains "$OUTPUT" "Traceback\|FATAL\|panic\|segfault" \
  "no crashes"
echo ""

# Phase 5: Implementation
echo "Phase 5: Implementation"
assert_any_skill_invoked "$OUTPUT" "implement|implement-feature" "implement skill invoked"
assert_git_commits_since "$PROJECT_DIR" "$INIT_REF" "new commits from implementation"

if grep -q "Task\|BaseModel" "$PROJECT_DIR/src/routes/tasks.py" 2>/dev/null && \
   ! grep -q "task: dict" "$PROJECT_DIR/src/routes/tasks.py" 2>/dev/null; then
  echo "  [PASS] create_task uses Pydantic model instead of dict"
  PASS=$((PASS + 1))
else
  echo "  [FAIL] create_task still accepts raw dict"
  FAIL=$((FAIL + 1))
fi

if grep -q "404\|HTTPException\|not found\|NotFound" "$PROJECT_DIR/src/routes/tasks.py" 2>/dev/null; then
  echo "  [PASS] 404 handling added to get_task"
  PASS=$((PASS + 1))
else
  echo "  [FAIL] no 404 handling in get_task"
  FAIL=$((FAIL + 1))
fi
echo ""

# Phase 6: Review
echo "Phase 6: Review"
assert_skill_invoked "$OUTPUT" "review" "review skill invoked"
assert_output_contains "$OUTPUT" "auth\|authentication\|Authorization" \
  "finds missing authentication"
assert_output_contains "$OUTPUT" "severity\|Severity\|critical\|Critical\|important\|Important" \
  "findings include severity levels"
echo ""

report_tokens "$OUTPUT" "pipeline"

# ================================================================
echo "================================================================"
echo "Pipeline Test Complete: Python API"
echo "================================================================"
print_summary
