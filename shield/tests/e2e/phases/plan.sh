# Phase: plan
# Fixture: post-research (optionally reads research docs)
# Produces: shield/plan.json, shield/docs/architecture-*.html, shield/docs/plan-*.html

PHASE_FIXTURE="post-research"
PHASE_TIMEOUT=1200

phase_prompt() {
  local example="$1"
  case "$example" in
    python-api)
      echo "Invoke the skill 'shield:plan-docs' to create an execution plan for improving the API in src/. Focus on: 1) adding input validation using the Task Pydantic model, 2) adding error handling for missing tasks (404)."
      ;;
    terraform-vpc)
      echo "Invoke the skill 'shield:plan-docs' to create an execution plan for improving the VPC module in src/. Focus on fixing security issues (wildcard IAM, open SSH) and cost issues (NAT gateways)."
      ;;
  esac
}

phase_assertions() {
  local project_dir="$1"
  local output="$2"
  local example="$3"

  assert_any_skill_invoked "$output" "plan|plan-docs" "plan-docs skill invoked"

  local sidecar
  sidecar=$(find "$project_dir/shield" -name "plan.json" -type f 2>/dev/null | head -1)
  if [ -n "$sidecar" ]; then
    assert_json_field "$sidecar" \
      "len(data.get('epics', [])) > 0" \
      "sidecar has at least 1 epic"
    assert_json_field "$sidecar" \
      "any(len(s.get('acceptance_criteria',[])) > 0 for e in data.get('epics',[]) for s in e.get('stories',[]))" \
      "stories have acceptance criteria"

    # Terraform-specific: validate against schema
    if [ "$example" = "terraform-vpc" ] && [ -f "$SHIELD_ROOT/schemas/plan.schema.json" ]; then
      assert_json_valid "$sidecar" \
        "$SHIELD_ROOT/schemas/plan.schema.json" \
        "sidecar validates against schema"
    fi
  else
    echo "  [FAIL] plan.json not created"
    FAIL=$((FAIL + 1))
  fi

  assert_file_glob "$project_dir" "shield/docs/architecture-*.html" "architecture.html created"
  assert_file_glob "$project_dir" "shield/docs/plan-*.html" "plan.html created"
}
