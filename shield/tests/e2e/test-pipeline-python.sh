#!/usr/bin/env bash
set -euo pipefail

# E2E Pipeline Test: Python API
# Runs the full Shield SDLC pipeline in a single resumed session.
# Each phase is a separate prompt that resumes the same session,
# so artifacts and context carry across phases naturally.
#
# Timing: ~10-20 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
check_claude

echo "=== Pipeline Test: Python API ==="
echo ""

# Create project inside the output dir
PROJECT_DIR=$(create_test_project_from_example "$SHIELD_ROOT/examples/python-api")
INIT_REF=$(git -C "$PROJECT_DIR" rev-parse HEAD)
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "Project: $PROJECT_DIR"
echo "Output:  $E2E_OUTPUT_DIR"
echo "Session: $SESSION_ID"
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
  "Invoke the skill 'shield:research' to investigate FastAPI best practices for input validation and authentication. Write the research findings to the Shield run directory." \
  600 "$SESSION_ID")

assert_skill_invoked "$OUTPUT" "research" "research skill invoked"
assert_output_contains "$OUTPUT" "validation\|FastAPI\|Pydantic\|auth" \
  "research mentions relevant concepts"
assert_file_glob "$PROJECT_DIR" ".shield/*/docs/research.md" "research.md created in docs dir"

report_tokens "$OUTPUT" "1-research"
check_phase
echo ""

# ================================================================
# Phase 2: Planning (resumes session — has research context)
# ================================================================
echo "================================================================"
echo "Phase 2: Planning"
echo "================================================================"

OUTPUT=$(resume_claude_session "$PROJECT_DIR" "$SESSION_ID" \
  "Now invoke the skill 'shield:plan-docs' to create an execution plan for improving the API in src/. Focus on: 1) adding input validation using the Task Pydantic model, 2) adding error handling for missing tasks (404). Write plan-sidecar.json to the Shield run directory with at least 1 epic and 2 stories, each with acceptance_criteria." \
  300)

assert_any_skill_invoked "$OUTPUT" "plan|plan-docs" "plan-docs skill invoked"

SIDECAR=$(find "$PROJECT_DIR/.shield" -name "plan-sidecar.json" -type f 2>/dev/null | head -1)
if [ -n "$SIDECAR" ]; then
  assert_json_field "$SIDECAR" \
    "len(data.get('epics', [])) > 0" \
    "sidecar has at least 1 epic"
  assert_json_field "$SIDECAR" \
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
# Phase 3: Plan Review (resumes — has research + plan context)
# ================================================================
echo "================================================================"
echo "Phase 3: Plan Review"
echo "================================================================"

OUTPUT=$(resume_claude_session "$PROJECT_DIR" "$SESSION_ID" \
  "Now invoke the skill 'shield:plan-review' to review the plan. Produce a review with grades (A-F)." \
  240)

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

OUTPUT=$(resume_claude_session "$PROJECT_DIR" "$SESSION_ID" \
  "Now invoke the skill 'shield:pm-status' to check sprint status." \
  60)

assert_output_contains "$OUTPUT" "init\|configure\|not configured\|no PM\|set up" \
  "suggests setup when PM not configured"
assert_output_not_contains "$OUTPUT" "Traceback\|FATAL\|panic\|segfault" \
  "no crashes"

report_tokens "$OUTPUT" "4-pm-status"
check_phase
echo ""

# ================================================================
# Phase 5: Implementation (resumes — has full plan context)
# ================================================================
echo "================================================================"
echo "Phase 5: Implementation"
echo "================================================================"

OUTPUT=$(resume_claude_session "$PROJECT_DIR" "$SESSION_ID" \
  "Now invoke the skill 'shield:implement' to add input validation to the create_task endpoint in src/routes/tasks.py. Change the parameter type from 'task: dict' to use the Task Pydantic model from src/models.py. Also add a 404 response to get_task when the task_id is not found. Make the changes and commit." \
  360)

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

report_tokens "$OUTPUT" "5-implement"
check_phase
echo ""

# ================================================================
# Phase 6: Review (resumes — sees implementation changes)
# ================================================================
echo "================================================================"
echo "Phase 6: Review"
echo "================================================================"

OUTPUT=$(resume_claude_session "$PROJECT_DIR" "$SESSION_ID" \
  "Now invoke the skill 'shield:review' to review the Python code in src/. Check for remaining security issues (missing auth), missing error handling, and test coverage gaps. Report findings with severity." \
  300)

assert_skill_invoked "$OUTPUT" "review" "review skill invoked"
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
