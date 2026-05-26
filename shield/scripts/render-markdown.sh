#!/usr/bin/env bash
# Render a markdown file into an HTML shell using a CommonMark-strict parser.
#
# Usage:
#   render-markdown.sh --md INPUT.md --shell SHELL.html --out OUTPUT.html
#
# The shell file must contain a literal `{{BODY}}` placeholder. Everything
# else in the shell (head, CSS, meta-banner, etc.) is the caller's
# responsibility — this script only substitutes the rendered body.
#
# Dependencies are fetched ephemerally via uv; no global pip install needed.

set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  cat >&2 <<'MSG'
render-markdown: uv is required but not installed.

To install uv (one-time, ~/.local/bin):
  curl -LsSf https://astral.sh/uv/install.sh | sh

Then re-run this command. uv handles markdown-it-py / mdit-py-plugins
ephemerally — no global pip install needed.
MSG
  exit 127
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec uv run --quiet \
  --with "markdown-it-py>=3,<4" \
  --with "mdit-py-plugins>=0.4,<1" \
  -- python "$SCRIPT_DIR/render-markdown.py" "$@"
