#!/usr/bin/env bash
# Build the full Shield HTML site from committed Markdown.
#
# Step 1: render every source .md to its outputs/*.html (rerender_all.py)
# Step 2: write the dashboard + shared assets (write_shield_assets.py)
#
# HTML is a build artifact: it is gitignored and regenerated on demand.
# Markdown + JSON sidecars are the committed source of truth.
#
# Usage:
#   render-output.sh [OUTPUT_DIR]
#     OUTPUT_DIR defaults to <repo-root>/docs/shield
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OUTPUT_DIR="${1:-}"
if [[ -z "$OUTPUT_DIR" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  OUTPUT_DIR="$ROOT/docs/shield"
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
  echo "render-output: not a dir: $OUTPUT_DIR" >&2
  exit 2
fi

python3 "$SCRIPT_DIR/rerender_all.py" --output-dir "$OUTPUT_DIR"
python3 "$SCRIPT_DIR/write_shield_assets.py" --output-dir "$OUTPUT_DIR"
echo "render-output: site built at $OUTPUT_DIR"
