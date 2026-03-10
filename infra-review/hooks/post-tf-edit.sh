#!/usr/bin/env bash
# PostToolUse hook for infra-review plugin
# Fires after Write/Edit tool use — reminds about hygiene if .tf file was modified

set -euo pipefail

# Check if any .tf files in src/ were recently modified (last 30 seconds)
REMINDER=""

# Look for recently modified .tf files
if [ -d "src" ]; then
    RECENT_TF=$(find src -name "*.tf" -newer /tmp/.infra-review-last-check 2>/dev/null || true)
    if [ -z "$RECENT_TF" ]; then
        # Fallback: check if any .tf files exist and were modified in last 30 seconds
        RECENT_TF=$(find src -name "*.tf" -mmin -0.5 2>/dev/null || true)
    fi

    if [ -n "$RECENT_TF" ]; then
        REMINDER="Terraform files modified. Remember to run: terraform fmt, terraform validate. For IAM or security group changes, consider /review-security. Run /analyze-plan to preview impact before applying."
    fi
fi

# Also check components/terraform/ layout
if [ -d "components/terraform" ]; then
    RECENT_TF=$(find components/terraform -name "*.tf" -mmin -0.5 2>/dev/null || true)
    if [ -n "$RECENT_TF" ]; then
        REMINDER="Terraform files modified. Remember to run: terraform fmt, terraform validate. For IAM or security group changes, consider /review-security. Run /analyze-plan to preview impact before applying."
    fi
fi

if [ -n "$REMINDER" ]; then
    # Escape for JSON
    escape_for_json() {
        local input="$1"
        local output=""
        local i char
        for (( i=0; i<${#input}; i++ )); do
            char="${input:$i:1}"
            case "$char" in
                $'\\') output+='\\\\';;
                '"') output+='\\"';;
                $'\n') output+='\\n';;
                $'\r') output+='\\r';;
                $'\t') output+='\\t';;
                *) output+="$char";;
            esac
        done
        printf '%s' "$output"
    }

    ESCAPED=$(escape_for_json "$REMINDER")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "${ESCAPED}"
  }
}
EOF
else
    # No .tf files modified — silent
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": ""
  }
}
EOF
fi

# Touch timestamp file for next comparison
touch /tmp/.infra-review-last-check 2>/dev/null || true

exit 0
