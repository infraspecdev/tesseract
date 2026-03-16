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
else
  PROJECT_NAME=""
  DOMAINS=""
fi

# --- Load global config ---
PM_TOOL="none"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VALIDATE_SCRIPT="${PLUGIN_ROOT}/hooks/scripts/validate-config.sh"

if [ -f "${SHIELD_HOME}/config.json" ]; then
  if [ -x "$VALIDATE_SCRIPT" ]; then
    CONFIG_ERRORS=$("$VALIDATE_SCRIPT" "${SHIELD_HOME}/config.json" "${PLUGIN_ROOT}/schemas/config.schema.json" 2>&1 || true)
    if [ -n "$CONFIG_ERRORS" ]; then
      CONFIG_WARNINGS="Config validation warning: ${CONFIG_ERRORS}. Using defaults."
    fi
  fi
  PM_TOOL=$(python3 -c "import json; print(json.load(open('${SHIELD_HOME}/config.json')).get('pm_tool','none'))" 2>/dev/null || echo "none")
fi

# --- Load project PM config ---
PM_STATUS="not configured"
if [ -n "$PROJECT_NAME" ] && [ -f "${SHIELD_HOME}/projects/${PROJECT_NAME}/pm.json" ]; then
  PM_STATUS=$(python3 -c "
import json
pm = json.load(open('${SHIELD_HOME}/projects/${PROJECT_NAME}/pm.json'))
adapter = pm.get('adapter', 'unknown')
ws = pm.get('workspace_id', 'not set')
print(f'{adapter} (workspace: {ws})')
" 2>/dev/null || echo "configured (details unreadable)")
fi

# --- Set up MCP server if PM tool configured ---
if [ "$PM_TOOL" != "none" ] && [ -f "${PLUGIN_ROOT}/adapters/${PM_TOOL}/.mcp.json" ]; then
  cp "${PLUGIN_ROOT}/adapters/${PM_TOOL}/.mcp.json" "${PLUGIN_ROOT}/.mcp.json"
fi

# --- Artifact directory ---
# Skills write directly to shield/ with timestamps in filenames.
# The Write tool creates the directory automatically — no pre-creation needed.
SHIELD_DIR=""
if [ -n "$PROJECT_NAME" ]; then
  SHIELD_DIR="${PROJECT_ROOT}/shield"
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
- Config: ${SHIELD_HOME}/projects/${PROJECT_NAME}/
- Artifact directory: ${SHIELD_DIR}/
${CONFIG_WARNINGS:+
⚠ ${CONFIG_WARNINGS}}

**Artifact output:** Documents go to \`shield/docs/\` with timestamps in filenames (e.g. \`shield/docs/research-20260315-170930.md\`). The \`shield/plan.json\` sidecar is updated in place (no timestamp).

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
