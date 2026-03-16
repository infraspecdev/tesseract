#!/usr/bin/env bash
set -euo pipefail

# Shield test runner — runs all tests locally
# Used by pre-commit hook and CI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SHIELD_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SHIELD_ROOT/.." && pwd)"
PASS=0
FAIL=0

run_test() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  ✓ $name"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $name"
    FAIL=$((FAIL + 1))
  fi
}

run_test_verbose() {
  local name="$1"
  shift
  local output
  if output=$("$@" 2>&1); then
    echo "  ✓ $name"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $name"
    echo "$output" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Shield Test Suite ==="
echo ""

# --- 1. JSON Schema Validation ---
echo "1. JSON Schema Validation"
for schema in "$SHIELD_ROOT"/schemas/*.schema.json; do
  basename=$(basename "$schema")
  run_test "$basename is valid JSON" python3 -c "import json; json.load(open('$schema'))"
done
echo ""

# --- 2. Config Examples vs Schemas ---
echo "2. Config Examples vs Schemas"
run_test_verbose "shield.example.json validates" python3 -c "
import json, jsonschema
schema = json.load(open('$SHIELD_ROOT/schemas/shield.schema.json'))
example = json.load(open('$SHIELD_ROOT/config-examples/shield.example.json'))
jsonschema.validate(example, schema)
"
run_test_verbose "pm-clickup.example.json validates" python3 -c "
import json, jsonschema
schema = json.load(open('$SHIELD_ROOT/schemas/pm.schema.json'))
example = json.load(open('$SHIELD_ROOT/config-examples/pm-clickup.example.json'))
jsonschema.validate(example, schema)
"
echo ""

# --- 3. Plugin Structure ---
echo "3. Plugin Structure"
run_test_verbose "plugin.json valid" python3 -c "
import json
p = json.load(open('$SHIELD_ROOT/.claude-plugin/plugin.json'))
assert p['name'] == 'shield', f'name is {p[\"name\"]}'
assert 'permissions' in p, 'missing permissions'
"
run_test_verbose "hooks.json valid" python3 -c "
import json
h = json.load(open('$SHIELD_ROOT/hooks/hooks.json'))
for e in ['SessionStart', 'PostToolUse']:
    assert e in h['hooks'], f'missing {e}'
"
run_test_verbose "marketplace.json valid" python3 -c "
import json
m = json.load(open('$REPO_ROOT/.claude-plugin/marketplace.json'))
names = [p['name'] for p in m['plugins']]
assert 'shield' in names, f'shield not in plugins: {names}'
"
echo ""

# --- 4. Hook Scripts ---
echo "4. Hook Scripts"
for script in "$SHIELD_ROOT"/hooks/scripts/*.sh; do
  basename=$(basename "$script")
  run_test "$basename is executable" test -x "$script"
done
if command -v shellcheck &>/dev/null; then
  for script in "$SHIELD_ROOT"/hooks/scripts/*.sh; do
    basename=$(basename "$script")
    run_test_verbose "$basename passes shellcheck" shellcheck "$script"
  done
else
  echo "  ⚠ shellcheck not installed, skipping"
fi
echo ""

# --- 5. Reference Integrity ---
echo "5. Reference Integrity"

# Check that all agent names referenced in commands/skills exist
run_test_verbose "agent references resolve" python3 -c "
import glob, re, os

# Get actual agent names from filenames
agent_dir = '$SHIELD_ROOT/agents'
actual_agents = set()
for f in glob.glob(os.path.join(agent_dir, '*.md')):
    name = os.path.basename(f).replace('.md', '')
    actual_agents.add(name)

# Scan commands and skills for agent references like shield:<name>
referenced = set()
patterns = [
    r'shield:([a-z]+-[a-z]+-?[a-z]*)',  # shield:security-reviewer
    r'dispatch.*\x60([a-z]+-[a-z]+-?[a-z]*)\x60',  # dispatch \`security-reviewer\`
]
for md_file in glob.glob('$SHIELD_ROOT/**/*.md', recursive=True):
    if '/agents/' in md_file:
        continue
    with open(md_file) as f:
        content = f.read()
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            name = match.group(1)
            # Filter to likely agent names (contain 'reviewer')
            if 'reviewer' in name:
                referenced.add(name)

missing = referenced - actual_agents
if missing:
    print(f'Referenced agents not found: {missing}')
    raise AssertionError(f'Missing agents: {missing}')
"

# Check that all skill SKILL.md files have valid frontmatter
run_test_verbose "skill frontmatter valid" python3 -c "
import glob, os

for skill_file in glob.glob('$SHIELD_ROOT/skills/**/SKILL.md', recursive=True):
    with open(skill_file) as f:
        content = f.read()
    if not content.startswith('---'):
        raise AssertionError(f'{skill_file}: missing frontmatter')
    # Check frontmatter has name and description
    end = content.index('---', 3)
    frontmatter = content[3:end]
    if 'name:' not in frontmatter:
        raise AssertionError(f'{skill_file}: missing name in frontmatter')
    if 'description:' not in frontmatter:
        raise AssertionError(f'{skill_file}: missing description in frontmatter')
"

# Check all commands have valid frontmatter
run_test_verbose "command frontmatter valid" python3 -c "
import glob

for cmd_file in glob.glob('$SHIELD_ROOT/commands/*.md'):
    with open(cmd_file) as f:
        content = f.read()
    if not content.startswith('---'):
        raise AssertionError(f'{cmd_file}: missing frontmatter')
    end = content.index('---', 3)
    frontmatter = content[3:end]
    if 'name:' not in frontmatter:
        raise AssertionError(f'{cmd_file}: missing name in frontmatter')
    if 'description:' not in frontmatter:
        raise AssertionError(f'{cmd_file}: missing description in frontmatter')
"
echo ""

# --- 6. Eval Criteria ---
echo "6. Eval Criteria"
run_test_verbose "eval criteria YAML valid" python3 -c "
import yaml, glob
for f in glob.glob('$SHIELD_ROOT/evals/expected/*.yaml'):
    with open(f) as fh:
        data = yaml.safe_load(fh)
    assert 'agent' in data, f'{f}: missing agent'
    assert 'mode' in data, f'{f}: missing mode'
    assert 'must_find' in data, f'{f}: missing must_find'
    for item in data['must_find']:
        assert 'id' in item, f'{f}: must_find missing id'
        assert 'match' in item, f'{f}: must_find missing match'
"
echo ""

# --- 7. Example Project Validation ---
echo "7. Example Projects"

# Validate example .shield.json files against schema
for example_dir in "$SHIELD_ROOT"/examples/*/; do
  example_name=$(basename "$example_dir")
  marker="$example_dir/.shield.json"
  if [ -f "$marker" ]; then
    run_test_verbose "$example_name: .shield.json validates" python3 -c "
import json, jsonschema
schema = json.load(open('$SHIELD_ROOT/schemas/shield.schema.json'))
marker = json.load(open('$marker'))
jsonschema.validate(marker, schema)
"
  else
    echo "  ⚠ $example_name: no .shield.json found"
  fi
done

# Session-start hook against each example project
for example_dir in "$SHIELD_ROOT"/examples/*/; do
  example_name=$(basename "$example_dir")
  if [ -f "$example_dir/.shield.json" ]; then
    PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$example_dir/.shield.json'))['project'])")
    run_test_verbose "$example_name: session-start detects project" bash -c "
cd '$example_dir'
OUTPUT=\$(CLAUDE_PLUGIN_ROOT='$SHIELD_ROOT' bash '$SHIELD_ROOT/hooks/scripts/session-start.sh' 2>/dev/null || true)
echo \"\$OUTPUT\" | python3 -c '
import json, sys
data = json.load(sys.stdin)
ctx = data[\"hookSpecificOutput\"][\"additionalContext\"]
assert \"$PROJECT_NAME\" in ctx, f\"project name not in context: {ctx}\"
'
"
  fi
done

# Verify example Terraform files are syntactically valid HCL (if terraform available)
if command -v terraform &>/dev/null; then
  for tf_dir in "$SHIELD_ROOT"/examples/*/src/; do
    if ls "$tf_dir"/*.tf &>/dev/null 2>&1; then
      example_name=$(basename "$(dirname "$tf_dir")")
      run_test_verbose "$example_name: terraform validates" bash -c "cd '$tf_dir' && terraform validate -no-color 2>&1 || terraform fmt -check -diff '$tf_dir' 2>&1"
    fi
  done
else
  echo "  ⚠ terraform not installed, skipping HCL validation"
fi
echo ""

# --- 8. Session-Start Hook E2E ---
echo "8. Session-Start Hook E2E"

# Create a temp project directory with .shield.json and run the hook
run_test_verbose "session-start produces valid JSON" bash -c "
TMPDIR=\$(mktemp -d)
trap 'rm -rf \$TMPDIR' EXIT

# Create test project marker
cat > \"\$TMPDIR/.shield.json\" <<'MARKER'
{\"project\": \"test-project\", \"domains\": [\"terraform\"]}
MARKER

# Run session-start hook from the test directory
cd \"\$TMPDIR\"
OUTPUT=\$(CLAUDE_PLUGIN_ROOT='$SHIELD_ROOT' bash '$SHIELD_ROOT/hooks/scripts/session-start.sh' 2>/dev/null || true)

# Verify output is valid JSON with expected structure
echo \"\$OUTPUT\" | python3 -c '
import json, sys
data = json.load(sys.stdin)
assert \"hookSpecificOutput\" in data, \"missing hookSpecificOutput\"
assert \"additionalContext\" in data[\"hookSpecificOutput\"], \"missing additionalContext\"
ctx = data[\"hookSpecificOutput\"][\"additionalContext\"]
assert \"test-project\" in ctx, f\"project name not in context: {ctx}\"
assert \"terraform\" in ctx, f\"domain not in context: {ctx}\"
'
"

# Test session-start when no marker exists
run_test_verbose "session-start handles missing marker" bash -c "
TMPDIR=\$(mktemp -d)
trap 'rm -rf \$TMPDIR' EXIT
cd \"\$TMPDIR\"
OUTPUT=\$(CLAUDE_PLUGIN_ROOT='$SHIELD_ROOT' bash '$SHIELD_ROOT/hooks/scripts/session-start.sh' 2>/dev/null || true)
echo \"\$OUTPUT\" | python3 -c '
import json, sys
data = json.load(sys.stdin)
ctx = data[\"hookSpecificOutput\"][\"additionalContext\"]
assert \"shield init\" in ctx.lower(), f\"init suggestion not in context: {ctx}\"
'
"
echo ""

# --- 9. Contract Tests ---
echo "9. PM Adapter Contract Tests"
if command -v uv &>/dev/null; then
  ADAPTER_DIR="$SHIELD_ROOT/adapters/clickup"
  run_test_verbose "contract tests pass" bash -c "cd '$ADAPTER_DIR' && uv run --extra test pytest tests/ -q 2>&1"
else
  echo "  ⚠ uv not installed, skipping adapter tests"
fi
echo ""

# --- Summary ---
echo "==========================="
TOTAL=$((PASS + FAIL))
echo "Results: $PASS/$TOTAL passed"
if [ "$FAIL" -gt 0 ]; then
  echo "FAILED: $FAIL test(s) failed"
  exit 1
else
  echo "ALL TESTS PASSED"
  exit 0
fi
