#!/usr/bin/env bash
set -euo pipefail

# Shield session-start hook
# Detects project config, loads settings, injects context into Claude

SHIELD_HOME="${HOME}/.shield"
MARKER_FILE=".shield.json"
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
PROJECT_ROOT=""
if MARKER_PATH=$(find_marker); then
  PROJECT_ROOT="$(dirname "$MARKER_PATH")"
  PROJECT_NAME=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['project'])" "$MARKER_PATH" 2>/dev/null || echo "unknown")
  DOMAINS=$(python3 -c "import json,sys; print(', '.join(json.load(open(sys.argv[1])).get('domains',[])))" "$MARKER_PATH" 2>/dev/null || echo "none")
  OUTPUT_DIR=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('output_dir', 'docs/shield'))" "$MARKER_PATH" 2>/dev/null || echo "docs/shield")
else
  PROJECT_NAME=""
  DOMAINS=""
  OUTPUT_DIR="docs/shield"
fi

# --- Load PM config from per-project pm.json ---
PM_TOOL="none"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# --- Load project PM config ---
PM_STATUS="not configured"
if [ -n "$PROJECT_NAME" ] && [ -f "${SHIELD_HOME}/projects/${PROJECT_NAME}/pm.json" ]; then
  PM_TOOL=$(python3 -c "
import json
pm = json.load(open('${SHIELD_HOME}/projects/${PROJECT_NAME}/pm.json'))
print(pm.get('adapter', 'none'))
" 2>/dev/null || echo "none")
  PM_STATUS=$(python3 -c "
import json
pm = json.load(open('${SHIELD_HOME}/projects/${PROJECT_NAME}/pm.json'))
adapter = pm.get('adapter', 'unknown')
ws = pm.get('workspace_id', 'not set')
print(f'{adapter} (workspace: {ws})')
" 2>/dev/null || echo "configured (details unreadable)")
fi

# --- Check if PM adapter MCP is registered ---
PM_MCP_WARNING=""
if [ "$PM_TOOL" != "none" ]; then
  HAS_ADAPTER=$(python3 -c "
import json
mcp = json.load(open('${PLUGIN_ROOT}/.mcp.json'))
print('yes' if mcp.get('mcpServers', {}) else 'no')
" 2>/dev/null || echo "no")
  if [ "$HAS_ADAPTER" = "no" ]; then
    PM_MCP_WARNING="PM tool is configured but the adapter MCP server is not registered. Run /shield init to set it up, then reload the Shield plugin."
  fi
fi

# --- Output directory ---
# Skills write to {output_dir}/ inside feature folders.
# The Write tool creates directories automatically — no pre-creation needed.
SHIELD_DIR=""
if [ -n "$PROJECT_NAME" ]; then
  SHIELD_DIR="${PROJECT_ROOT}/${OUTPUT_DIR}"
fi

# --- Build context output ---
if [ -n "$PROJECT_NAME" ]; then
  # Build domain-specific skill guidance
  DOMAIN_SKILLS="Use skills from: general/"
  DOMAIN_SKIP=""
  ALL_DOMAINS="terraform atmos github-actions"

  IFS=',' read -ra ACTIVE_DOMAINS <<< "$(echo "$DOMAINS" | tr -d ' ')"
  for d in "${ACTIVE_DOMAINS[@]}"; do
    DOMAIN_SKILLS="${DOMAIN_SKILLS}, ${d}/"
  done

  for d in $ALL_DOMAINS; do
    is_active=false
    for a in "${ACTIVE_DOMAINS[@]}"; do
      [ "$d" = "$a" ] && is_active=true
    done
    if [ "$is_active" = "false" ]; then
      DOMAIN_SKIP="${DOMAIN_SKIP:+${DOMAIN_SKIP}, }${d}/"
    fi
  done

  CONTEXT="Shield project detected: **${PROJECT_NAME}**
- Domains: ${DOMAINS}
- PM tool: ${PM_TOOL} (${PM_STATUS})
- Project config: ${SHIELD_HOME}/projects/${PROJECT_NAME}/
- Output directory: \`${OUTPUT_DIR}\` (${SHIELD_DIR}/)
${CONFIG_WARNINGS:+
⚠ ${CONFIG_WARNINGS}}
${PM_MCP_WARNING:+
⚠ ${PM_MCP_WARNING}}

**Artifact output:** Documents go to \`${OUTPUT_DIR}/\` inside feature folders (e.g. \`${OUTPUT_DIR}/vpc-module-20260319/research/1-topic/findings.md\`). Plan sidecars live at \`${OUTPUT_DIR}/{feature}/plan.json\`. Manifest at \`${OUTPUT_DIR}/manifest.json\`.

**Skill domains:** ${DOMAIN_SKILLS}
${DOMAIN_SKIP:+**Skip skills from:** ${DOMAIN_SKIP} (not relevant to this project)}

Available commands: /shield init, /research, /plan, /plan-review, /pm-sync, /pm-status, /implement, /review, /review-security, /review-cost, /review-well-architected, /analyze-plan"
else
  CONTEXT="No .shield.json found in this project. Run **/shield init** to set up Shield."
fi

CONTEXT_ESCAPED=$(echo "$CONTEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" | sed 's/^"//;s/"$//')

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "${CONTEXT_ESCAPED}"
  }
}
EOF
