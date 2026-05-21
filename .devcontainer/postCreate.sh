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

# Install Shield plugin from this workspace's local marketplace.
# Runs idempotently — adding the same marketplace twice or installing an
# already-installed plugin should not fail the postCreate step. Wrapped in
# `|| true` so any transient hiccup (e.g., claude not yet authed) doesn't
# block container startup; user can re-run manually after `claude /login`.
if command -v claude >/dev/null 2>&1; then
  echo "Adding workspace as Claude Code marketplace + installing shield plugin..."
  claude /plugin marketplace add "$workspace" 2>&1 | sed 's/^/  /' || true
  claude /plugin install shield@tesseract 2>&1 | sed 's/^/  /' || true
  echo "Shield plugin install attempt complete."
  echo "If install failed because Claude isn't logged in yet:"
  echo "  1. Run: claude /login"
  echo "  2. Then re-run: claude /plugin install shield@tesseract"
else
  echo "claude CLI not found on PATH; skipping Shield plugin install."
  echo "After 'claude /login', run: claude /plugin install shield@tesseract"
fi

echo "postCreate complete."
