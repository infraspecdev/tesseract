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
uv pip install --system --quiet jsonschema pyyaml pre-commit

# Install repo pre-commit git hooks so commits run the configured checks
# (whitespace hygiene, YAML/JSON validity, bash syntax, eval-format check, etc.
# — see .pre-commit-config.yaml). Skipped silently if the config is absent.
if [ -f .pre-commit-config.yaml ]; then
  pre-commit install --install-hooks 2>/dev/null || echo "postCreate: pre-commit install skipped (will run on first commit instead)"
fi

echo "postCreate complete."
echo ""
echo "=========================================================="
echo "Next steps (inside an interactive Claude Code session):"
echo ""
echo "  1. claude /login                                    # one-time per container volume"
echo "  2. /plugin marketplace add $workspace               # inside claude REPL"
echo "  3. /plugin install shield@tesseract                 # inside claude REPL"
echo ""
echo "After step 3, /shield commands resolve. Try:"
echo "  /shield implement EPIC-1-S1"
echo ""
echo "Note: /plugin is a Claude Code REPL slash command and is NOT"
echo "available from 'claude' invoked as a shell command — these"
echo "must be run inside an interactive Claude session."
echo "=========================================================="
