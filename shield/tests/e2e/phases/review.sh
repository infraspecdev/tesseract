# Phase: review
# Fixture: post-implement (needs code changes to review)
# Produces: Claude output with findings (no persistent artifact required)

PHASE_FIXTURE="post-implement"
PHASE_TIMEOUT=1200

phase_prompt() {
  local example="$1"
  case "$example" in
    python-api)
      echo "Invoke the skill 'shield:review' to review the Python code in src/. Check for remaining security issues (missing auth), missing error handling, and test coverage gaps. Report findings with severity."
      ;;
    terraform-vpc)
      echo "Invoke the skill 'shield:review' to review the Terraform code in src/. Check for remaining security, cost, and architecture issues. Report specific findings with severity."
      ;;
  esac
}

phase_assertions() {
  local project_dir="$1"
  local output="$2"
  local example="$3"

  assert_skill_invoked "$output" "review" "review skill invoked"
  assert_output_contains "$output" "severity\|Severity\|critical\|Critical\|important\|Important" \
    "findings include severity levels"

  case "$example" in
    python-api)
      assert_output_contains "$output" "auth\|authentication\|Authorization" \
        "finds missing authentication"
      ;;
    terraform-vpc)
      assert_output_contains "$output" "NAT\|nat_gateway\|nat gateway" \
        "finds NAT gateway cost issue"
      assert_output_contains "$output" "0\.0\.0\.0/0\|SSH\|port 22\|open.*22" \
        "finds open SSH security issue"
      ;;
  esac
}
