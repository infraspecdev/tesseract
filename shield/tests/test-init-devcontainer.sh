#!/usr/bin/env bash
# shield/tests/test-init-devcontainer.sh
# Integration test: simulate the skill steps against fixture repos.
# Tests the *mechanism* (composer + templates + .shield.json update),
# not the LLM execution of the skill.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0

assert() {
  if eval "$1" >/dev/null 2>&1; then
    echo "  ✓ $2"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $2"
    FAIL=$((FAIL + 1))
  fi
}

run_scaffolder() {
  local target="$1"
  shift
  local stacks=("$@")
  local stack_csv
  stack_csv=$(printf '"%s",' "${stacks[@]}")
  stack_csv="[${stack_csv%,}]"

  uv run python3 - <<PY
import json, sys
from pathlib import Path
sys.path.insert(0, "shield/scripts")
from compose_devcontainer import compose_devcontainer
from detect_stack import detect_stack

target = Path("$target")
target.mkdir(parents=True, exist_ok=True)
(target / ".devcontainer").mkdir(exist_ok=True)

cfg = compose_devcontainer(
    stacks=${stack_csv},
    feature_map_path=Path("shield/skills/devcontainer/feature-map.json"),
)
(target / ".devcontainer" / "devcontainer.json").write_text(
    json.dumps(cfg, indent=2) + "\n"
)

import shutil
shutil.copy("shield/skills/devcontainer/templates/shield-firewall.sh",
            target / ".devcontainer" / "shield-firewall.sh")
shutil.copy("shield/skills/devcontainer/templates/Dockerfile.tmpl",
            target / ".devcontainer" / "Dockerfile")

fm = json.loads(Path("shield/skills/devcontainer/feature-map.json").read_text())
hints = "\n".join(fm[s]["post_create_hint"] for s in ${stack_csv} if s in fm)
tmpl = Path("shield/skills/devcontainer/templates/postCreate.sh.tmpl").read_text()
(target / ".devcontainer" / "postCreate.sh").write_text(
    tmpl.replace("# {{HINTS}}", hints)
)

shield_json = target / ".shield.json"
data = json.loads(shield_json.read_text()) if shield_json.exists() else {}
data["devcontainer"] = {
    "version": 1,
    "stacks_detected": ${stack_csv},
    "required": "ask",
    "firewall_extra_allowlist": [],
}
shield_json.write_text(json.dumps(data, indent=2) + "\n")
PY
}

echo "=== Devcontainer Scaffolder Integration ==="

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Fixture 1: python-only
PY_FIX="$TMPDIR/python-only"
mkdir -p "$PY_FIX"
echo "[project]" > "$PY_FIX/pyproject.toml"
run_scaffolder "$PY_FIX" python

assert "[ -f '$PY_FIX/.devcontainer/devcontainer.json' ]" "python-only: devcontainer.json created"
assert "grep -q '/python@sha256:' '$PY_FIX/.devcontainer/devcontainer.json'" "python-only: includes python feature"
assert "grep -q 'pypi.org' '$PY_FIX/.devcontainer/devcontainer.json'" "python-only: EXTRA_HOSTS includes pypi.org"
assert "grep -q 'uv sync' '$PY_FIX/.devcontainer/postCreate.sh'" "python-only: postCreate has uv sync hint"
assert "grep -q 'anthropics/devcontainer-features/claude-code' '$PY_FIX/.devcontainer/devcontainer.json'" \
  "python-only: claude-code constant-layer feature present"

# Fixture 2: polyglot python + node
POLY="$TMPDIR/polyglot"
mkdir -p "$POLY"
echo "[project]" > "$POLY/pyproject.toml"
echo "{}" > "$POLY/package.json"
run_scaffolder "$POLY" python node

assert "grep -q '/python@sha256:' '$POLY/.devcontainer/devcontainer.json'" "polyglot: python feature present"
assert "grep -q '/node@sha256:' '$POLY/.devcontainer/devcontainer.json'" "polyglot: node feature present"
assert "grep -q 'registry.npmjs.org' '$POLY/.devcontainer/devcontainer.json'" "polyglot: EXTRA_HOSTS includes npm"
assert "grep -q 'anthropics/devcontainer-features/claude-code' '$POLY/.devcontainer/devcontainer.json'" \
  "polyglot: claude-code constant-layer feature present"

# Fixture 3: terraform-only
TF="$TMPDIR/terraform-only"
mkdir -p "$TF"
echo "resource \"aws_vpc\" \"x\" {}" > "$TF/main.tf"
run_scaffolder "$TF" terraform

assert "grep -q '/terraform@sha256:' '$TF/.devcontainer/devcontainer.json'" "terraform-only: tf feature present"
assert "grep -q 'registry.terraform.io' '$TF/.devcontainer/devcontainer.json'" "terraform-only: EXTRA_HOSTS includes tf registry"
assert "grep -q 'anthropics/devcontainer-features/claude-code' '$TF/.devcontainer/devcontainer.json'" \
  "terraform-only: claude-code constant-layer feature present"

# Idempotency: re-run on python fixture
run_scaffolder "$PY_FIX" python
assert "[ \"$(cat "$PY_FIX/.shield.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["devcontainer"]["required"])')\" = ask ]" \
  "idempotent: .shield.json required field preserved"

# Stack with no feature-map entry: skipped with warning
NOMAP="$TMPDIR/no-map"
mkdir -p "$NOMAP"
echo "x" > "$NOMAP/Gemfile"
warning=$(uv run python3 - <<'PY' 2>&1 1>/dev/null
import sys
from pathlib import Path
sys.path.insert(0, "shield/scripts")
from compose_devcontainer import compose_devcontainer
compose_devcontainer(stacks=["ruby"], feature_map_path=Path("shield/skills/devcontainer/feature-map.json"))
PY
)
assert "echo '$warning' | grep -qi 'ruby'" "unknown stack: warning emitted"

echo ""
echo "==========================="
TOTAL=$((PASS + FAIL))
echo "Results: $PASS/$TOTAL passed"
if [ "$FAIL" -gt 0 ]; then
  echo "FAILED: $FAIL test(s) failed"
  exit 1
fi
echo "ALL INIT-DEVCONTAINER TESTS PASSED"
