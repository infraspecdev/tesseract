#!/usr/bin/env bash
set -euo pipefail

# Shield pre-commit review hook
# Runs lightweight code review on staged changes before commit
# Disabled by default — enable via review_on_commit.enabled in config
#
# NOTE: Claude Code hooks communicate via JSON output (additionalContext),
# not via exit codes. This hook provides context and thresholds to Claude,
# which then performs the review and decides whether to proceed with the
# commit or ask the user to fix issues first. The blocking is enforced by
# Claude's behavior, not by this script's exit code.

SHIELD_HOME="${HOME}/.shield"

ENABLED="false"
if [ -f "${SHIELD_HOME}/config.json" ]; then
  ENABLED=$(python3 -c "
import json
cfg = json.load(open('${SHIELD_HOME}/config.json'))
print(str(cfg.get('review_on_commit', {}).get('enabled', False)).lower())
" 2>/dev/null || echo "false")
fi

if [ "$ENABLED" != "true" ]; then
  exit 0
fi

BLOCK_THRESHOLD=$(python3 -c "
import json
cfg = json.load(open('${SHIELD_HOME}/config.json'))
print(cfg.get('review_on_commit', {}).get('block_threshold', 'critical'))
" 2>/dev/null || echo "critical")

WARN_THRESHOLD=$(python3 -c "
import json
cfg = json.load(open('${SHIELD_HOME}/config.json'))
print(cfg.get('review_on_commit', {}).get('warn_threshold', 'important'))
" 2>/dev/null || echo "important")

STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)
if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

CONTEXT="Pre-commit review triggered. Staged files:
${STAGED_FILES}

Review thresholds — block: ${BLOCK_THRESHOLD}, warn: ${WARN_THRESHOLD}
Review these changes and report findings at or above the warn threshold.
Block the commit (exit non-zero) if any findings are at or above the block threshold."

CONTEXT_ESCAPED=$(echo "$CONTEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" | sed 's/^"//;s/"$//')

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "${CONTEXT_ESCAPED}"
  }
}
EOF
