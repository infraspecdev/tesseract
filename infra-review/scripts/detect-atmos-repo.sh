#!/usr/bin/env bash
# Detect if the current directory is an Atmos component repository
# Exit 0 if yes, exit 1 if no

set -euo pipefail

# Check for single-component repo layout (template-based)
if [ -f "src/versions.tf" ] && [ -f "src/providers.tf" ]; then
    exit 0
fi

# Check for multi-component repo layout
if [ -d "components/terraform" ]; then
    # Verify at least one component has versions.tf
    if find components/terraform -maxdepth 2 -name "versions.tf" -print -quit 2>/dev/null | grep -q .; then
        exit 0
    fi
fi

# Not an Atmos component repo
exit 1
