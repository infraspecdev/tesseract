# Phase: research
# Fixture: initialized (just needs .shield.json)
# Produces: shield/docs/research-*.md

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

  assert_file_glob "$project_dir" "shield/docs/research-*.md" "research.md created in docs dir"
}
