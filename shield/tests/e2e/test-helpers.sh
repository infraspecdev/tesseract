#!/usr/bin/env bash
# Shield E2E test helpers — runs Claude Code headless against test projects
# Requires: claude CLI installed locally

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TESTS_OUTPUT_DIR="${SHIELD_ROOT}/tests/output"

# Build output dir: tests/output/<datetime>-<testname>/
# Individual tests derive name from their filename; run-all.sh overrides E2E_OUTPUT_DIR.
if [ -z "${E2E_OUTPUT_DIR:-}" ]; then
  _CALLER_BASENAME="$(basename "${BASH_SOURCE[1]:-unknown}" .sh)"
  _RUN_TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
  E2E_OUTPUT_DIR="${TESTS_OUTPUT_DIR}/${_RUN_TIMESTAMP}-${_CALLER_BASENAME}"
fi
mkdir -p "$E2E_OUTPUT_DIR"

PASS=0
FAIL=0
SKIP=0
LAST_OUTPUT=""
TOTAL_INPUT_TOKENS=0
TOTAL_OUTPUT_TOKENS=0
TOTAL_CACHE_READ=0
TOTAL_CACHE_WRITE=0

# Check Claude CLI is available and API is reachable
check_claude() {
  if ! command -v claude &>/dev/null; then
    echo "ERROR: claude CLI not found. Install Claude Code first."
    exit 1
  fi

  # Pre-flight: verify API is reachable with a minimal prompt
  echo "Pre-flight check..."
  local preflight_file="${E2E_OUTPUT_DIR}/.preflight"
  timeout 30 claude -p "reply OK" --output-format json --dangerously-skip-permissions \
    < /dev/null > "$preflight_file" 2>&1 || true
  if ! grep -qi "OK" "$preflight_file" 2>/dev/null; then
    echo "WARNING: Pre-flight check failed — API may be rate-limited or unreachable"
    echo "  Output: $(head -5 "$preflight_file" 2>/dev/null)"
    echo "  Continuing anyway..."
  else
    echo "Pre-flight check passed."
  fi
}

# Run Claude in headless mode against a project directory
# Usage: run_claude_in_project "project_dir" "prompt" [max_turns] [timeout_seconds]
# Output file is saved to $E2E_OUTPUT_DIR for post-run analysis
# Uses a file-based counter because $() subshells don't preserve variable state.
_COUNTER_FILE="${E2E_OUTPUT_DIR}/.run-counter"
echo "0" > "$_COUNTER_FILE"

run_claude_in_project() {
  local project_dir="$1"
  local prompt="$2"
  local timeout_secs="${3:-180}"

  # Derive a unique name from the calling test script + file-based counter
  local caller_name
  caller_name=$(basename "${BASH_SOURCE[1]:-unknown}" .sh)
  local count
  count=$(cat "$_COUNTER_FILE")
  count=$((count + 1))
  echo "$count" > "$_COUNTER_FILE"
  local output_file="${E2E_OUTPUT_DIR}/${caller_name}-${count}.jsonl"

  cd "$project_dir" || return 1

  local exit_code=0
  local stderr_file="${output_file%.jsonl}.stderr"
  timeout "$timeout_secs" claude -p "$prompt" \
    --plugin-dir "$SHIELD_ROOT" \
    --dangerously-skip-permissions \
    --output-format stream-json \
    --model "${CLAUDE_MODEL:-sonnet}" \
    < /dev/null > "$output_file" 2>"$stderr_file" || exit_code=$?

  cd - >/dev/null || true

  # Warn if output is empty (usually means CLI error or rate limit)
  if [ ! -s "$output_file" ]; then
    echo "  [WARN] Claude session produced no output (exit code: $exit_code)" >&2
    echo "         Output file: $output_file" >&2
    if [ "$exit_code" -eq 124 ]; then
      echo "         Cause: timeout after ${timeout_secs}s" >&2
    elif [ "$exit_code" -ne 0 ]; then
      echo "         Cause: claude exited with code $exit_code" >&2
    fi
    if [ -s "$stderr_file" ]; then
      echo "         Stderr:" >&2
      head -20 "$stderr_file" | sed 's/^/           /' >&2
    fi
  fi

  # Extract readable text output alongside the JSONL
  _extract_readable "$output_file"

  LAST_OUTPUT="$output_file"
}

# Extract human-readable text from a stream-json JSONL file
# Writes a .txt file alongside the .jsonl with assistant messages and tool summaries
_extract_readable() {
  local jsonl_file="$1"
  local txt_file="${jsonl_file%.jsonl}.txt"

  [ -s "$jsonl_file" ] || return 0

  python3 -c "
import json, sys, textwrap

for line in open('$jsonl_file'):
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
    except:
        continue

    msg_type = data.get('type', '')

    # Assistant text output
    if msg_type == 'assistant' and 'message' in data:
        for block in data['message'].get('content', []):
            if block.get('type') == 'text':
                print(block['text'])
                print()
            elif block.get('type') == 'tool_use':
                name = block.get('name', '?')
                inp = block.get('input', {})
                if name == 'Skill':
                    print(f'[Skill: {inp.get(\"skill\", \"?\")}]')
                elif name == 'Write':
                    print(f'[Write: {inp.get(\"file_path\", \"?\")}]')
                elif name == 'Edit':
                    print(f'[Edit: {inp.get(\"file_path\", \"?\")}]')
                elif name == 'Read':
                    print(f'[Read: {inp.get(\"file_path\", \"?\")}]')
                elif name == 'Bash':
                    cmd = inp.get('command', '?')
                    if len(cmd) > 100:
                        cmd = cmd[:100] + '...'
                    print(f'[Bash: {cmd}]')
                elif name == 'Agent':
                    print(f'[Agent: {inp.get(\"description\", \"?\")}]')
                else:
                    print(f'[{name}]')
                print()

    # Tool results (abbreviated)
    elif msg_type == 'tool_result':
        pass  # Skip — too verbose
" > "$txt_file" 2>/dev/null || true
}

# resume_claude_session is deprecated — use run_claude_in_project with artifact-based context instead.
# Each phase reads artifacts from shield/ on disk rather than resuming conversation history.
resume_claude_session() {
  local project_dir="$1"
  local _session_id="$2"  # ignored — kept for backward compat
  local prompt="$3"
  local timeout_secs="${4:-180}"
  run_claude_in_project "$project_dir" "$prompt" "$timeout_secs"
}

# Extract token usage from a stream-json output file
# Usage: extract_tokens "output_file"
# Prints: input_tokens output_tokens cache_read cache_creation
extract_tokens() {
  local output_file="$1"
  python3 -c "
import json, sys

input_tokens = 0
output_tokens = 0
cache_read = 0
cache_creation = 0

for line in open('$output_file'):
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        continue
    usage = data.get('usage', {})
    if usage:
        input_tokens += usage.get('input_tokens', 0)
        output_tokens += usage.get('output_tokens', 0)
        cache_read += usage.get('cache_read_input_tokens', usage.get('cache_read', 0))
        cache_creation += usage.get('cache_creation_input_tokens', usage.get('cache_creation', 0))

print(f'{input_tokens} {output_tokens} {cache_read} {cache_creation}')
" 2>/dev/null || echo "0 0 0 0"
}

# Report token usage for the current test
# Usage: report_tokens "output_file" "test_name"
report_tokens() {
  local output_file="$1"
  local test_name="${2:-test}"

  local tokens
  tokens=$(extract_tokens "$output_file")
  local input output cache_read cache_creation
  read -r input output cache_read cache_creation <<< "$tokens"

  TOTAL_INPUT_TOKENS=$((TOTAL_INPUT_TOKENS + input))
  TOTAL_OUTPUT_TOKENS=$((TOTAL_OUTPUT_TOKENS + output))
  TOTAL_CACHE_READ=$((TOTAL_CACHE_READ + cache_read))
  TOTAL_CACHE_WRITE=$((TOTAL_CACHE_WRITE + cache_creation))

  if [ "$input" -gt 0 ] || [ "$output" -gt 0 ]; then
    echo "  Tokens: ${input} in / ${output} out (cache read: ${cache_read}, cache write: ${cache_creation})"
  fi
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

# Check if any of multiple skill names was invoked
# Usage: assert_any_skill_invoked "output_file" "name1|name2|name3" "test_name"
assert_any_skill_invoked() {
  local output_file="$1"
  local names="$2"
  local test_name="${3:-skill invoked}"

  IFS='|' read -ra NAME_ARRAY <<< "$names"
  for skill_name in "${NAME_ARRAY[@]}"; do
    local skill_pattern="\"skill\":\"([^\"]*:)?${skill_name}\""
    if grep -q '"name":"Skill"' "$output_file" && grep -qE "$skill_pattern" "$output_file"; then
      echo "  [PASS] $test_name ($skill_name)"
      PASS=$((PASS + 1))
      return 0
    fi
  done

  echo "  [FAIL] $test_name"
  echo "    Expected one of: $names"
  local triggered
  triggered=$(grep -o '"skill":"[^"]*"' "$output_file" 2>/dev/null | sort -u || echo "(none)")
  echo "    Skills triggered: $triggered"
  FAIL=$((FAIL + 1))
  return 1
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

# Create a test project inside the output directory
# Usage: project_dir=$(create_test_project "project_name" "domain1,domain2")
# The project lives at $E2E_OUTPUT_DIR/project/ — no cleanup needed.
create_test_project() {
  local name="${1:-test-project}"
  local domains="${2:-terraform}"
  local project_dir="${E2E_OUTPUT_DIR}/project"
  mkdir -p "$project_dir"

  # Create .shield.json
  local domains_json
  domains_json=$(echo "$domains" | python3 -c "
import sys
domains = sys.stdin.read().strip().split(',')
print('[' + ', '.join('\"' + d.strip() + '\"' for d in domains) + ']')
")

  cat > "$project_dir/.shield.json" <<EOF
{
  "project": "$name",
  "domains": $domains_json
}
EOF

  # Init git repo (Claude Code expects one)
  git -C "$project_dir" init -q
  git -C "$project_dir" add .
  git -C "$project_dir" commit -q -m "init" --no-gpg-sign

  echo "$project_dir"
}

# Create a test project from an example directory
# Usage: project_dir=$(create_test_project_from_example "example_dir")
# Copies the example into $E2E_OUTPUT_DIR/project/ and inits git.
create_test_project_from_example() {
  local example_dir="$1"
  local project_dir="${E2E_OUTPUT_DIR}/project"
  mkdir -p "$project_dir"

  cp -r "$example_dir"/* "$project_dir/"
  # Copy dotfiles separately (cp * doesn't match them)
  for dotfile in "$example_dir"/.*; do
    [ -f "$dotfile" ] && cp "$dotfile" "$project_dir/"
  done

  git -C "$project_dir" init -q
  git -C "$project_dir" add .
  git -C "$project_dir" commit -q -m "init example" --no-gpg-sign

  echo "$project_dir"
}

# Print test summary to stdout and write summary.txt to output dir
print_summary() {
  local total=$((PASS + FAIL + SKIP))
  local summary_file="${E2E_OUTPUT_DIR}/summary.txt"

  {
    echo "==========================="
    echo "Shield E2E Test Summary"
    echo "==========================="
    echo "Date:    $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Output:  ${E2E_OUTPUT_DIR}"
    echo ""
    echo "Results: $PASS passed, $FAIL failed, $SKIP skipped (${total} total)"
    echo ""

    if [ "$TOTAL_INPUT_TOKENS" -gt 0 ] || [ "$TOTAL_OUTPUT_TOKENS" -gt 0 ]; then
      echo "--- Token Usage ---"
      # Per-file breakdown
      for jsonl_file in "$E2E_OUTPUT_DIR"/*.jsonl; do
        [ -f "$jsonl_file" ] || continue
        local fname
        fname=$(basename "$jsonl_file" .jsonl)
        local tokens
        tokens=$(extract_tokens "$jsonl_file")
        local inp out cr cw
        read -r inp out cr cw <<< "$tokens"
        if [ "$inp" -gt 0 ] || [ "$out" -gt 0 ]; then
          printf "  %-40s %7s in / %7s out  (cache read: %s, write: %s)\n" \
            "$fname" "$inp" "$out" "$cr" "$cw"
        fi
      done

      echo "  ----------------------------------------"
      printf "  %-40s %7s in / %7s out  (cache read: %s, write: %s)\n" \
        "TOTAL" "$TOTAL_INPUT_TOKENS" "$TOTAL_OUTPUT_TOKENS" "$TOTAL_CACHE_READ" "$TOTAL_CACHE_WRITE"

      # Cost estimate (Sonnet pricing)
      local cost
      cost=$(python3 -c "
i=$TOTAL_INPUT_TOKENS; o=$TOTAL_OUTPUT_TOKENS; cr=$TOTAL_CACHE_READ; cw=$TOTAL_CACHE_WRITE
cost = (i*3 + o*15 + cr*0.30 + cw*3.75) / 1_000_000
print(f'\${cost:.4f}')
" 2>/dev/null || echo "unknown")
      echo "  Estimated cost (Sonnet pricing): $cost"

      # Cache hit rate
      local total_context=$((TOTAL_INPUT_TOKENS + TOTAL_CACHE_READ + TOTAL_CACHE_WRITE))
      if [ "$total_context" -gt 0 ]; then
        local hit_rate
        hit_rate=$(python3 -c "print(f'{$TOTAL_CACHE_READ / $total_context * 100:.1f}%')" 2>/dev/null || echo "n/a")
        echo "  Cache hit rate: $hit_rate"
      fi
      echo ""
    fi

    if [ "$FAIL" -gt 0 ]; then
      echo "FAILED"
    else
      echo "ALL TESTS PASSED"
    fi
  } | tee "$summary_file"

  echo ""
  echo "Summary written to: $summary_file"

  if [ "$FAIL" -gt 0 ]; then
    return 1
  else
    return 0
  fi
}

# --- Artifact Assertions ---

# Check that a file exists in the project directory
# Usage: assert_file_exists "project_dir" "relative_path" "test_name"
assert_file_exists() {
  local project_dir="$1"
  local rel_path="$2"
  local test_name="${3:-file exists: $rel_path}"

  if [ -f "$project_dir/$rel_path" ]; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    File not found: $project_dir/$rel_path"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check that a file matches a glob pattern exists
# Usage: assert_file_glob "project_dir" "glob_pattern" "test_name"
assert_file_glob() {
  local project_dir="$1"
  local pattern="$2"
  local test_name="${3:-file matching $pattern exists}"

  local found
  found=$(find "$project_dir" -path "$project_dir/$pattern" -type f 2>/dev/null | head -1)
  if [ -n "$found" ]; then
    echo "  [PASS] $test_name ($(basename "$found"))"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    No file matching: $pattern"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check that a JSON file validates against a schema
# Usage: assert_json_valid "json_file" "schema_file" "test_name"
assert_json_valid() {
  local json_file="$1"
  local schema_file="$2"
  local test_name="${3:-JSON validates against schema}"

  if [ ! -f "$json_file" ]; then
    echo "  [FAIL] $test_name (file not found: $json_file)"
    FAIL=$((FAIL + 1))
    return 1
  fi

  local result
  result=$(python3 -c "
import json, jsonschema, sys
try:
    data = json.load(open('$json_file'))
    schema = json.load(open('$schema_file'))
    jsonschema.validate(data, schema)
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

  if [ "$result" = "OK" ]; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    $result"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check that a JSON file contains a field with a non-empty value
# Usage: assert_json_field "json_file" "jsonpath_expr" "test_name"
# jsonpath_expr is a Python expression applied to the loaded JSON (variable: data)
assert_json_field() {
  local json_file="$1"
  local expr="$2"
  local test_name="${3:-JSON field check}"

  if [ ! -f "$json_file" ]; then
    echo "  [FAIL] $test_name (file not found)"
    FAIL=$((FAIL + 1))
    return 1
  fi

  local result
  result=$(python3 -c "
import json
data = json.load(open('$json_file'))
result = $expr
if result:
    print('OK')
else:
    print('EMPTY')
" 2>&1)

  if [ "$result" = "OK" ]; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    Expression '$expr' returned empty/false"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check that git has new commits since a given ref
# Usage: assert_git_commits_since "project_dir" "ref" "test_name"
assert_git_commits_since() {
  local project_dir="$1"
  local ref="$2"
  local test_name="${3:-new commits since $ref}"

  local count
  count=$(git -C "$project_dir" rev-list --count "$ref..HEAD" 2>/dev/null || echo "0")

  if [ "$count" -gt 0 ]; then
    echo "  [PASS] $test_name ($count new commits)"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name (no new commits)"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# Check that git diff shows changes in specific files
# Usage: assert_git_files_changed "project_dir" "pattern" "test_name"
assert_git_files_changed() {
  local project_dir="$1"
  local pattern="$2"
  local test_name="${3:-files matching $pattern changed}"

  local changed
  changed=$(git -C "$project_dir" diff --name-only HEAD~1 2>/dev/null | grep "$pattern" || true)

  if [ -n "$changed" ]; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    No changed files matching: $pattern"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# --- PM Mock Server ---

# Start a mock PM server that records calls and returns canned responses
# Usage: start_pm_mock "port"
# Returns the PID. Stop with: kill $PID
start_pm_mock() {
  local port="${1:-9876}"
  local mock_log="${E2E_OUTPUT_DIR}/pm-mock.log"

  python3 -c "
import http.server, json, sys, os

PORT = $port
LOG = '$mock_log'

class MockPMHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode() if length else ''

        # Log the request
        with open(LOG, 'a') as f:
            f.write(json.dumps({
                'method': 'POST',
                'path': self.path,
                'body': body
            }) + '\n')

        # Return canned responses based on path
        if 'capabilities' in self.path:
            response = {
                'adapter': 'mock',
                'adapter_mode': 'hybrid',
                'capabilities': ['pm_sync', 'pm_bulk_create', 'pm_get_status', 'pm_get_capabilities']
            }
        elif 'sync' in self.path:
            response = {'status': 'synced', 'created': 0, 'updated': 0, 'matched': 2}
        elif 'status' in self.path:
            response = {'epics': [{'id': 'EPIC-1', 'name': 'Test', 'total': 2, 'done': 0}]}
        elif 'bulk_create' in self.path:
            response = {'created': [{'id': 'task-1', 'name': 'Test Story'}], 'failed': []}
        else:
            response = {'ok': True}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, fmt, *args):
        pass  # Suppress request logging to stderr

server = http.server.HTTPServer(('127.0.0.1', PORT), MockPMHandler)
print(f'Mock PM server on port {PORT}', file=sys.stderr)
server.serve_forever()
" &
  local pid=$!
  sleep 1  # Wait for server to start

  # Verify it's running
  if kill -0 "$pid" 2>/dev/null; then
    echo "$pid"
    return 0
  else
    echo ""
    return 1
  fi
}

# Check that the mock PM server received a specific call
# Usage: assert_pm_mock_called "pattern" "test_name"
assert_pm_mock_called() {
  local pattern="$1"
  local test_name="${2:-PM mock received call}"
  local mock_log="${E2E_OUTPUT_DIR}/pm-mock.log"

  if [ ! -f "$mock_log" ]; then
    echo "  [FAIL] $test_name (no PM mock calls recorded)"
    FAIL=$((FAIL + 1))
    return 1
  fi

  if grep -qi "$pattern" "$mock_log"; then
    echo "  [PASS] $test_name"
    PASS=$((PASS + 1))
    return 0
  else
    echo "  [FAIL] $test_name"
    echo "    Expected call matching: $pattern"
    echo "    Calls recorded:"
    cat "$mock_log" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
    return 1
  fi
}

export -f run_claude_in_project
export -f resume_claude_session
export -f extract_tokens
export -f report_tokens
export -f assert_skill_invoked
export -f assert_any_skill_invoked
export -f assert_agent_dispatched
export -f assert_output_contains
export -f assert_output_not_contains
export -f assert_no_premature_action
export -f assert_file_exists
export -f assert_file_glob
export -f assert_json_valid
export -f assert_json_field
export -f assert_git_commits_since
export -f assert_git_files_changed
export -f start_pm_mock
export -f assert_pm_mock_called
export -f create_test_project
export -f create_test_project_from_example
export -f print_summary
export E2E_OUTPUT_DIR
export TESTS_OUTPUT_DIR
export TOTAL_INPUT_TOKENS
export TOTAL_OUTPUT_TOKENS
export TOTAL_CACHE_READ
export TOTAL_CACHE_WRITE
