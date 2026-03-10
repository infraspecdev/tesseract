#!/usr/bin/env bash
# SessionStart hook for infra-review plugin
# Detects if cwd is an Atmos component repo and injects context

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Use the detect script
DETECT_SCRIPT="${PLUGIN_ROOT}/scripts/detect-atmos-repo.sh"

# Check if we're in an Atmos component repo
if bash "${DETECT_SCRIPT}" 2>/dev/null; then
    # Determine repo type
    if [ -f "src/versions.tf" ]; then
        REPO_TYPE="single-component"
        COMPONENT_PATH="src/"
    else
        REPO_TYPE="multi-component"
        COMPONENT_PATH="components/terraform/*/"
    fi

    CONTEXT="Terraform component repository detected (${REPO_TYPE}, components at ${COMPONENT_PATH}).

Available review commands:
- /review-component — Full 4-perspective review (security, architecture, operations, cost)
- /review-security — Security-focused review (IAM, encryption, network, Checkov)
- /review-hygiene — Quick Atmos conventions check
- /review-cost — Cost optimization analysis
- /review-cicd — GitHub Actions workflow audit
- /review-well-architected — AWS Well-Architected Framework review (all 6 pillars)
- /analyze-plan — Analyze terraform plan output for security, cost, and destructive action impact

Available skills (auto-invoked when relevant):
- infra-review:atmos-component-hygiene
- infra-review:atmos-repo-review
- infra-review:terraform-security-audit
- infra-review:terraform-cost-review
- infra-review:terraform-test-coverage
- infra-review:terraform-plan-analyzer
- infra-review:github-actions-reviewer

Companion plugin: terraform-skill (antonbabenko/terraform-skill) provides general Terraform best practices for naming, module patterns, testing strategy, CI/CD, and code structure."

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

    ESCAPED=$(escape_for_json "$CONTEXT")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${ESCAPED}"
  }
}
EOF
else
    # Not a Terraform repo — output empty context (no noise)
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
fi

exit 0
