#!/usr/bin/env bash
# Shield E2E test helpers — runs Claude Code headless against test projects
# Requires: claude CLI installed locally

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PASS=0
FAIL=0
SKIP=0

# Check Claude CLI is available
check_claude() {
  if ! command -v claude &>/dev/null; then
    echo "ERROR: claude CLI not found. Install Claude Code first."
    exit 1
  fi
}

# Run Claude in headless mode against a project directory
# Usage: run_claude_in_project "project_dir" "prompt" [max_turns] [timeout_seconds]
run_claude_in_project() {
  local project_dir="$1"
  local prompt="$2"
  local max_turns="${3:-3}"
  local timeout_secs="${4:-120}"
  local output_file
  output_file=$(mktemp)

  cd "$project_dir" || return 1

  timeout "$timeout_secs" claude -p "$prompt" \
    --plugin-dir "$SHIELD_ROOT" \
    --dangerously-skip-permissions \
    --max-turns "$max_turns" \
    --output-format stream-json \
    > "$output_file" 2>&1 || true

  cd - >/dev/null || true
  echo "$output_file"
}

# Check if a specific skill was invoked in the output
# Usage: assert_skill_invoked "output_file" "skill_name" "test_name"
assert_skill_invoked() {
  local output_file="$1"
  local skill_name="$2"
  local test_name="${3:-skill invoked}"

  local skill_pattern="\"skill\":\"([^\"]*:)?${skill_name}\""
  if grep -q '"name":"Skill"' "$output_file" && grep -qE "$skill_pattern" "$output_file"; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    Expected skill '$skill_name' to be invoked"
    local triggered
    triggered=$(grep -o '"skill":"[^"]*"' "$output_file" 2>/dev/null | sort -u || echo "(none)")
    echo "    Skills triggered: $triggered"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check if a specific agent was dispatched
# Usage: assert_agent_dispatched "output_file" "agent_name" "test_name"
assert_agent_dispatched() {
  local output_file="$1"
  local agent_name="$2"
  local test_name="${3:-agent dispatched}"

  if grep -q "$agent_name" "$output_file"; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    Expected agent '$agent_name' to be dispatched"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check if output contains a pattern
# Usage: assert_output_contains "output_file" "pattern" "test_name"
assert_output_contains() {
  local output_file="$1"
  local pattern="$2"
  local test_name="${3:-contains pattern}"

  if grep -qi "$pattern" "$output_file"; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    Expected to find: $pattern"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check output does NOT contain a pattern
# Usage: assert_output_not_contains "output_file" "pattern" "test_name"
assert_output_not_contains() {
  local output_file="$1"
  local pattern="$2"
  local test_name="${3:-not contains pattern}"

  if grep -qi "$pattern" "$output_file"; then
    echo "  [FAIL] $test_name"
    echo "    Did not expect to find: $pattern"
    FAIL=$((FAIL + 1))
    return 1
  else
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  fi
}

# Check that no tools were invoked before the Skill tool (premature action)
# Usage: assert_no_premature_action "output_file" "test_name"
assert_no_premature_action() {
  local output_file="$1"
  local test_name="${2:-no premature action}"

  local first_skill_line
  first_skill_line=$(grep -n '"name":"Skill"' "$output_file" | head -1 | cut -d: -f1)

  if [ -z "$first_skill_line" ]; then
    echo "  [SKIP] $test_name (no Skill invocation found)"
    SKIP=$((SKIP + 1))
    return 0
  fi

  local premature
  premature=$(head -n "$first_skill_line" "$output_file" | \
    grep '"type":"tool_use"' | \
    grep -v '"name":"Skill"' | \
    grep -v '"name":"TaskCreate"' | \
    grep -v '"name":"TaskUpdate"' | \
    grep -v '"name":"TaskList"' || true)

  if [ -n "$premature" ]; then
    echo "  [FAIL] $test_name"
    echo "    Tools invoked before Skill:"
    echo "$premature" | head -3 | sed 's/^/    /'
    FAIL=$((FAIL + 1))
    return 1
  else
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  fi
}

# Create a temporary test project with .tesseract.json
# Usage: project_dir=$(create_shield_test_project "project_name" "domain1,domain2")
create_shield_test_project() {
  local name="${1:-test-project}"
  local domains="${2:-terraform}"
  local tmpdir
  tmpdir=$(mktemp -d)

  # Create .tesseract.json
  local domains_json
  domains_json=$(echo "$domains" | python3 -c "
import sys
domains = sys.stdin.read().strip().split(',')
print('[' + ', '.join('\"' + d.strip() + '\"' for d in domains) + ']')
")

  cat > "$tmpdir/.tesseract.json" <<EOF
{
  "project": "$name",
  "domains": $domains_json
}
EOF

  # Init git repo (Claude Code expects one)
  git -C "$tmpdir" init -q
  git -C "$tmpdir" add .
  git -C "$tmpdir" commit -q -m "init" --no-gpg-sign

  echo "$tmpdir"
}

# Cleanup test project
cleanup_test_project() {
  local project_dir="$1"
  if [ -d "$project_dir" ] && [[ "$project_dir" == /tmp/* ]]; then
    rm -rf "$project_dir"
  fi
}

# Print test summary
print_summary() {
  local total=$((PASS + FAIL + SKIP))
  echo ""
  echo "==========================="
  echo "Results: $PASS passed, $FAIL failed, $SKIP skipped (${total} total)"
  if [ "$FAIL" -gt 0 ]; then
    echo "FAILED"
    return 1
  else
    echo "ALL TESTS PASSED"
    return 0
  fi
}

export -f run_claude_in_project
export -f assert_skill_invoked
export -f assert_agent_dispatched
export -f assert_output_contains
export -f assert_output_not_contains
export -f assert_no_premature_action
export -f create_shield_test_project
export -f cleanup_test_project
export -f print_summary
