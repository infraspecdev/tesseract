#!/usr/bin/env bash
set -euo pipefail

# Shield post-edit hook
# Runs lightweight lint checks on edited files that match active domains

MARKER_FILE=".shield.json"

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

# Claude Code PostToolUse hooks receive tool input via stdin as JSON.
INPUT=$(cat)
EDITED_FILE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$EDITED_FILE" ] || [ ! -f "$EDITED_FILE" ]; then
  exit 0
fi

# Only process if we have a project marker
if ! find_marker >/dev/null; then
  exit 0
fi

REMINDERS=""
case "$EDITED_FILE" in
  *.tf)
    if command -v terraform &>/dev/null; then
      FMT_CHECK=$(terraform fmt -check -diff "$EDITED_FILE" 2>/dev/null || true)
      if [ -n "$FMT_CHECK" ]; then
        REMINDERS="File needs formatting: run \`terraform fmt ${EDITED_FILE}\`"
      fi
    fi
    ;;
  *.yaml|*.yml)
    if command -v python3 &>/dev/null; then
      YAML_CHECK=$(python3 -c "import yaml; yaml.safe_load(open('${EDITED_FILE}'))" 2>&1 || true)
      if echo "$YAML_CHECK" | grep -qi "error\|exception"; then
        REMINDERS="YAML syntax issue in ${EDITED_FILE}"
      fi
    fi
    ;;
esac

if [ -z "$REMINDERS" ]; then
  exit 0
fi

REMINDERS_ESCAPED=$(echo "$REMINDERS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" | sed 's/^"//;s/"$//')

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "${REMINDERS_ESCAPED}"
  }
}
EOF
