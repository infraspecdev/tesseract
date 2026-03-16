# Phase: implement
# Fixture: post-planning (needs plan.json for story context)
# Produces: code changes committed to git

PHASE_FIXTURE="post-planning"
PHASE_TIMEOUT=1200

phase_prompt() {
  local example="$1"
  case "$example" in
    python-api)
      echo "Invoke the skill 'shield:implement' to add input validation to the create_task endpoint in src/routes/tasks.py. Change the parameter type from 'task: dict' to use the Task Pydantic model from src/models.py. Also add a 404 response to get_task when the task_id is not found. Make the changes and commit."
      ;;
    terraform-vpc)
      echo "Invoke the skill 'shield:implement' to fix the security issue in src/main.tf: the flow log IAM policy (aws_iam_role_policy.flow_log) has Resource = \"*\" — scope it to the specific CloudWatch log group ARN using aws_cloudwatch_log_group.flow_logs.arn. Make the change and commit it."
      ;;
  esac
}

phase_assertions() {
  local project_dir="$1"
  local output="$2"
  local example="$3"

  assert_any_skill_invoked "$output" "implement|implement-feature" "implement skill invoked"
  assert_git_commits_since "$project_dir" "${INIT_REF:-HEAD~1}" "new commits from implementation"

  case "$example" in
    python-api)
      if grep -q "Task\|BaseModel" "$project_dir/src/routes/tasks.py" 2>/dev/null && \
         ! grep -q "task: dict" "$project_dir/src/routes/tasks.py" 2>/dev/null; then
        echo "  [PASS] create_task uses Pydantic model instead of dict"
        PASS=$((PASS + 1))
      else
        echo "  [FAIL] create_task still accepts raw dict"
        FAIL=$((FAIL + 1))
      fi

      if grep -q "404\|HTTPException\|not found\|NotFound" "$project_dir/src/routes/tasks.py" 2>/dev/null; then
        echo "  [PASS] 404 handling added to get_task"
        PASS=$((PASS + 1))
      else
        echo "  [FAIL] no 404 handling in get_task"
        FAIL=$((FAIL + 1))
      fi
      ;;
    terraform-vpc)
      if grep -q 'aws_cloudwatch_log_group.flow_logs.arn\|flow_logs\.arn' "$project_dir/src/main.tf" 2>/dev/null; then
        echo "  [PASS] IAM policy scoped to log group ARN"
        PASS=$((PASS + 1))
      else
        echo "  [FAIL] IAM policy still has Resource = *"
        FAIL=$((FAIL + 1))
      fi
      ;;
  esac
}
