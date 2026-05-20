#!/bin/bash
# .devcontainer/postCreate.sh
# Project-specific install hints. Idempotent.
set -euo pipefail
workspace=$(find /workspaces -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -n 1)
[ -n "$workspace" ] || { echo "postCreate: no workspace mounted at /workspaces" >&2; exit 1; }
cd "$workspace"

# Python (shield adapters use uv)
if [ -f shield/adapters/clickup/pyproject.toml ]; then
  (cd shield/adapters/clickup && uv sync)
fi
if [ -f shield/adapters/sast/sonarqube/pyproject.toml ]; then
  (cd shield/adapters/sast/sonarqube && uv sync)
fi
if [ -f shield/adapters/sast/semgrep/pyproject.toml ]; then
  (cd shield/adapters/sast/semgrep && uv sync)
fi

# Top-level test deps (uv-managed, system-Python target — no host pollution since we're in a container)
uv pip install --system --quiet jsonschema pyyaml

echo "postCreate complete."
