#!/bin/bash
# .devcontainer/postCreate.sh
# Project-specific install hints. Idempotent.
set -euo pipefail
cd /workspaces/* 2>/dev/null || cd "$(ls -d /workspaces/* | head -n1)"

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

# Top-level deps used by tests
python3 -m pip install --user --quiet jsonschema pyyaml 2>/dev/null \
  || python3 -m pip install --user --break-system-packages --quiet jsonschema pyyaml

echo "postCreate complete."
