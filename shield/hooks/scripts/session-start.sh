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

# --- Create run directory for artifacts ---
RUN_DIR=""
DOCS_DIR=""
if [ -n "$PROJECT_NAME" ]; then
  RUN_TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
  RUN_DIR="${PROJECT_ROOT}/shield/${RUN_TIMESTAMP}"
  DOCS_DIR="${RUN_DIR}/docs"
  mkdir -p "$DOCS_DIR"

  # Write run metadata
  python3 -c "
import json, datetime
metadata = {
    'run_id': '${RUN_TIMESTAMP}',
    'project': '${PROJECT_NAME}',
    'domains': '${DOMAINS}'.split(', '),
    'pm_tool': '${PM_TOOL}',
    'started_at': datetime.datetime.now().isoformat()
}
json.dump(metadata, open('${RUN_DIR}/metadata.json', 'w'), indent=2)
" 2>/dev/null || true

  # Update latest symlink
  ln -sfn "${RUN_TIMESTAMP}" "${PROJECT_ROOT}/shield/latest"
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
- Config: ${TESSERACT_HOME}/projects/${PROJECT_NAME}/
- Run directory: ${RUN_DIR}/
- Docs directory: ${DOCS_DIR}/
${CONFIG_WARNINGS:+
⚠ ${CONFIG_WARNINGS}}

**Artifact output:** Write user-facing docs (research.md, plan.md, analysis.md, review reports, summaries) to \`${DOCS_DIR}/\`. Write non-docs artifacts (plan.json, metadata.json) to \`${RUN_DIR}/\`. The \`shield/latest\` symlink always points to the current run.

**Skill domains:** ${DOMAIN_SKILLS}
${DOMAIN_SKIP:+**Skip skills from:** ${DOMAIN_SKIP} (not relevant to this project)}

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
