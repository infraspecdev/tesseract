# Phase: plan-review
# Fixture: post-planning (needs plan.json + HTML docs)
# Produces: Claude output with grades (no persistent artifact required)

PHASE_FIXTURE="post-planning"
PHASE_TIMEOUT=1200

phase_prompt() {
  local example="$1"
  echo "Invoke the skill 'shield:plan-review' to review the plan. Produce a review with grades (A-F) for each reviewer."
}

phase_assertions() {
  local project_dir="$1"
  local output="$2"
  local example="$3"

  assert_skill_invoked "$output" "plan-review" "plan-review skill invoked"
  assert_output_contains "$output" "Grade.*[A-F]\|grade.*[A-F]\|[A-F].*grade" \
    "review output contains grades"
}
