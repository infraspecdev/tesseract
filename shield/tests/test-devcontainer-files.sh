#!/usr/bin/env bash
# shield/tests/test-devcontainer-files.sh
# Static checks for the .devcontainer/ files.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

fail=0

assert() {
  if eval "$1" >/dev/null 2>&1; then
    echo "  ✓ $2"
  else
    echo "  ✗ $2"
    fail=$((fail + 1))
  fi
}

assert "[ -f .devcontainer/Dockerfile ]" "Dockerfile exists"
assert "[ -f .devcontainer/devcontainer.json ]" "devcontainer.json exists"
assert "[ -f .devcontainer/shield-firewall.sh ]" "shield-firewall.sh exists"
assert "[ -f .devcontainer/postCreate.sh ]" "postCreate.sh exists"

assert "python3 -c 'import json; json.load(open(\".devcontainer/devcontainer.json\"))'" \
  "devcontainer.json is valid JSON"

assert "grep -q 'remoteUser.*dev' .devcontainer/devcontainer.json" \
  "devcontainer.json sets remoteUser=dev"

assert "grep -q 'NET_ADMIN' .devcontainer/devcontainer.json" \
  "devcontainer.json declares NET_ADMIN capability"

assert "grep -q 'claude-config-' .devcontainer/devcontainer.json" \
  "devcontainer.json mounts named claude-config volume"

assert "grep -q '^#!/bin/bash' .devcontainer/shield-firewall.sh" \
  "shield-firewall.sh has bash shebang"

assert "grep -q '127.0.0.11' .devcontainer/shield-firewall.sh" \
  "shield-firewall.sh locks DNS to Docker's resolver (#36907)"

assert "[ -f shield/skills/devcontainer/templates/shield-firewall.sh ]" "template: shield-firewall.sh exists"
assert "[ -f shield/skills/devcontainer/templates/Dockerfile.tmpl ]" "template: Dockerfile.tmpl exists"
assert "[ -f shield/skills/devcontainer/templates/postCreate.sh.tmpl ]" "template: postCreate.sh.tmpl exists"
assert "diff -q .devcontainer/shield-firewall.sh shield/skills/devcontainer/templates/shield-firewall.sh" \
  "template: shield-firewall.sh matches .devcontainer/ instance"
assert "diff -q .devcontainer/Dockerfile shield/skills/devcontainer/templates/Dockerfile.tmpl" \
  "template: Dockerfile.tmpl matches .devcontainer/ instance"

if [ $fail -gt 0 ]; then
  echo "FAILED: $fail check(s)"
  exit 1
fi
echo "ALL DEVCONTAINER STATIC CHECKS PASSED"
