# Phase: research
# Fixture: initialized (just needs .shield.json)
# Produces: {output_dir}/{feature}/research/{N}-{slug}/findings.md

PHASE_FIXTURE="initialized"
PHASE_TIMEOUT=1200

phase_prompt() {
  local example="$1"
  case "$example" in
    python-api)
      echo "Invoke the skill 'shield:research' to investigate FastAPI best practices for input validation and authentication."
      ;;
    terraform-vpc)
      echo "Invoke the skill 'shield:research' to investigate AWS VPC best practices for multi-AZ deployment with IPAM."
      ;;
  esac
}

phase_assertions() {
  local project_dir="$1"
  local output="$2"
  local example="$3"

  assert_skill_invoked "$output" "research" "research skill invoked"

  # PM agent must be dispatched for both framing and review
  assert_agent_dispatched "$output" "product-manager-reviewer" "PM agent dispatched during research"
  assert_output_contains "$output" "research-framing\|research.framing\|PM.*[Ff]raming\|framing.*mode" \
    "PM framing mode invoked before research agents"
  assert_output_contains "$output" "research-review\|research.review\|PM.*[Rr]eview\|Product Lens" \
    "PM review mode invoked after synthesis"

  case "$example" in
    python-api)
      assert_output_contains "$output" "validation\|FastAPI\|Pydantic\|auth" \
        "research mentions relevant concepts"
      ;;
    terraform-vpc)
      assert_output_contains "$output" "VPC\|vpc\|subnet\|CIDR\|availability.zone" \
        "research mentions VPC concepts"
      ;;
  esac

  assert_file_glob "$project_dir" "docs/shield/*/research/*/findings.md" "research findings.md created in feature dir"

  # Verify Product Lens section in findings
  local findings
  findings=$(find "$project_dir" -path "*/research/*/findings.md" -print -quit 2>/dev/null)
  if [ -n "$findings" ]; then
    assert_output_contains "$findings" "Product Lens" "findings.md contains Product Lens section from PM review"
  fi
}
