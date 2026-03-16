# Phase: pm-status
# Fixture: initialized (just needs .shield.json)
# Produces: Claude output (no persistent artifact)

PHASE_FIXTURE="initialized"
PHASE_TIMEOUT=1200

phase_prompt() {
  local example="$1"
  echo "Invoke the skill 'shield:pm-status' to check sprint status."
}

phase_assertions() {
  local project_dir="$1"
  local output="$2"
  local example="$3"

  assert_output_contains "$output" "init\|configure\|not configured\|no PM\|set up" \
    "suggests setup when PM not configured"
  assert_output_not_contains "$output" "Traceback\|FATAL\|panic\|segfault" \
    "no crashes"
}
