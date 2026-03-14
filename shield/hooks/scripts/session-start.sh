#!/usr/bin/env bash
set -euo pipefail

# Shield session-start hook
# Detects project config, loads settings, injects context into Claude

TESSERACT_HOME="${HOME}/.tesseract"
MARKER_FILE=".tesseract.json"
CONFIG_WARNINGS=""

find_marker() {
  local dir="$PWD"
  while [ "$dir" != "/" ]; do
    if [ -f "${dir}/${MARKER_FILE}" ]; then
      echo "${dir}/${MARKER_FILE}"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

# --- Detect project ---
MARKER_PATH=""
if MARKER_PATH=$(find_marker); then
  PROJECT_NAME=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['project'])" "$MARKER_PATH" 2>/dev/null || echo "unknown")
  DOMAINS=$(python3 -c "import json,sys; print(', '.join(json.load(open(sys.argv[1])).get('domains',[])))" "$MARKER_PATH" 2>/dev/null || echo "none")
else
  PROJECT_NAME=""
  DOMAINS=""
fi

# --- Load global config ---
PM_TOOL="none"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VALIDATE_SCRIPT="${PLUGIN_ROOT}/hooks/scripts/validate-config.sh"

if [ -f "${TESSERACT_HOME}/config.json" ]; then
  if [ -x "$VALIDATE_SCRIPT" ]; then
    CONFIG_ERRORS=$("$VALIDATE_SCRIPT" "${TESSERACT_HOME}/config.json" "${PLUGIN_ROOT}/schemas/config.schema.json" 2>&1 || true)
    if [ -n "$CONFIG_ERRORS" ]; then
      CONFIG_WARNINGS="Config validation warning: ${CONFIG_ERRORS}. Using defaults."
    fi
  fi
  PM_TOOL=$(python3 -c "import json; print(json.load(open('${TESSERACT_HOME}/config.json')).get('pm_tool','none'))" 2>/dev/null || echo "none")
fi

# --- Load project PM config ---
PM_STATUS="not configured"
if [ -n "$PROJECT_NAME" ] && [ -f "${TESSERACT_HOME}/projects/${PROJECT_NAME}/pm.json" ]; then
  PM_STATUS=$(python3 -c "
import json
pm = json.load(open('${TESSERACT_HOME}/projects/${PROJECT_NAME}/pm.json'))
adapter = pm.get('adapter', 'unknown')
ws = pm.get('workspace_id', 'not set')
print(f'{adapter} (workspace: {ws})')
" 2>/dev/null || echo "configured (details unreadable)")
fi

# --- Set up MCP server if PM tool configured ---
if [ "$PM_TOOL" != "none" ] && [ -f "${PLUGIN_ROOT}/adapters/${PM_TOOL}/.mcp.json" ]; then
  cp "${PLUGIN_ROOT}/adapters/${PM_TOOL}/.mcp.json" "${PLUGIN_ROOT}/.mcp.json"
fi

# --- Build context output ---
if [ -n "$PROJECT_NAME" ]; then
  CONTEXT="Shield project detected: **${PROJECT_NAME}**
- Domains: ${DOMAINS}
- PM tool: ${PM_TOOL} (${PM_STATUS})
- Config: ${TESSERACT_HOME}/projects/${PROJECT_NAME}/
${CONFIG_WARNINGS:+
⚠ ${CONFIG_WARNINGS}}

Available commands: /shield init, /research, /plan, /plan-review, /pm-sync, /pm-status, /implement, /review, /review-security, /review-cost, /review-well-architected, /analyze-plan"
else
  CONTEXT="No .tesseract.json found in this project. Run **/shield init** to set up Shield."
fi

CONTEXT_ESCAPED=$(echo "$CONTEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" | sed 's/^"//;s/"$//')

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "${CONTEXT_ESCAPED}"
  }
}
EOF
