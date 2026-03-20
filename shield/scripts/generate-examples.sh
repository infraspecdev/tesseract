#!/usr/bin/env bash
set -euo pipefail

# Generate showcase examples by running Shield phases against example projects.
# This produces real artifacts (research, plans, reviews) that demonstrate
# what Shield does at each phase.
#
# Usage:
#   ./shield/scripts/generate-examples.sh [example_name]
#
# Examples:
#   ./shield/scripts/generate-examples.sh              # all examples
#   ./shield/scripts/generate-examples.sh python-api    # single example
#   ./shield/scripts/generate-examples.sh terraform-vpc
#
# Requirements:
#   - claude CLI installed and authenticated
#   - Shield plugin installed (plugin install shield@tesseract)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXAMPLES_DIR="${REPO_ROOT}/shield/examples"
PLUGIN_ROOT="${REPO_ROOT}/shield"

# --- Config ---
TIMEOUT=600  # seconds per phase
SELECTED_EXAMPLE="${1:-all}"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[generate-examples]${NC} $*"; }
ok()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn(){ echo -e "${YELLOW}[!]${NC} $*"; }
err() { echo -e "${RED}[✗]${NC} $*" >&2; }

# --- Phase definitions per example ---
# Each phase: prompt to send to claude CLI

python_api_phases() {
  local project_dir="$1"
  cat <<'PHASES'
research|Invoke the skill 'shield:research' to investigate FastAPI best practices for input validation and authentication. The feature name is 'input-validation-and-auth'.
plan|Invoke the skill 'shield:plan-docs' to create a plan for adding input validation, error handling, and JWT authentication to the FastAPI task API. The plan name is 'input-validation-and-auth'. Use findings from the research phase.
plan-review|Invoke the skill 'shield:plan-review' to review the plan 'input-validation-and-auth'.
review|Invoke the skill 'shield:review' to review the current codebase for security, code quality, and best practices.
PHASES
}

terraform_vpc_phases() {
  local project_dir="$1"
  cat <<'PHASES'
research|Invoke the skill 'shield:research' to investigate AWS VPC best practices for multi-AZ deployment with cost optimization. The feature name is 'vpc-hardening'.
plan|Invoke the skill 'shield:plan-docs' to create a plan for hardening the VPC module: toggleable NAT gateways, scoped IAM, KMS encryption for flow logs, log retention, and Terraform tests. The plan name is 'vpc-hardening'. Use findings from the research phase.
plan-review|Invoke the skill 'shield:plan-review' to review the plan 'vpc-hardening'.
review|Invoke the skill 'shield:review' to review the current Terraform code for security, cost, architecture, and operations.
PHASES
}

# --- GitHub Actions ---

add_github_actions() {
  local project_dir="$1"
  local example_name="$2"

  mkdir -p "${project_dir}/.github/workflows"

  case "$example_name" in
    python-api)
      cat > "${project_dir}/.github/workflows/ci.yml" <<'EOF'
name: CI

on:
  pull_request:
    branches: [main]
    paths: ["src/**", "tests/**", "pyproject.toml"]
  push:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check src/ tests/
      - run: uv run ruff format --check src/ tests/
      - run: uv run pytest tests/ -v --tb=short
EOF
      ;;
    terraform-vpc)
      cat > "${project_dir}/.github/workflows/ci.yml" <<'EOF'
name: CI

on:
  pull_request:
    branches: [main]
    paths: ["src/**", "tests/**"]
  push:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "~1.5"
      - run: terraform -chdir=src fmt -check
      - run: terraform -chdir=src init -backend=false
      - run: terraform -chdir=src validate

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: bridgecrewio/checkov-action@v12
        with:
          directory: src/
          quiet: true
          soft_fail: true

  test:
    runs-on: ubuntu-latest
    needs: [validate]
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "~1.5"
      - run: terraform -chdir=src init -backend=false
      - run: terraform -chdir=src test
EOF
      ;;
  esac
}

# --- Update .shield.json ---

update_shield_json() {
  local project_dir="$1"
  local example_name="$2"

  case "$example_name" in
    python-api)
      cat > "${project_dir}/.shield.json" <<'EOF'
{
  "project": "python-api-example",
  "domains": ["python", "github-actions"],
  "output_dir": "docs/shield"
}
EOF
      ;;
    terraform-vpc)
      cat > "${project_dir}/.shield.json" <<'EOF'
{
  "project": "terraform-vpc-example",
  "domains": ["terraform", "github-actions"],
  "output_dir": "docs/shield"
}
EOF
      ;;
  esac
}

# --- Run a single phase ---

run_phase() {
  local project_dir="$1"
  local phase_name="$2"
  local prompt="$3"

  log "Running phase: ${phase_name}"

  local output_file="${project_dir}/.shield-generate-${phase_name}.log"

  if (cd "$project_dir" && timeout "$TIMEOUT" claude --print \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash,Agent,Skill" \
    "$prompt") \
    > "$output_file" 2>&1; then
    ok "Phase ${phase_name} completed"
  else
    local exit_code=$?
    if [ "$exit_code" -eq 124 ]; then
      err "Phase ${phase_name} timed out after ${TIMEOUT}s"
    else
      err "Phase ${phase_name} failed (exit $exit_code)"
    fi
    warn "Log: ${output_file}"
    return 1
  fi

  # Clean up log on success
  rm -f "$output_file"
}

# --- Process one example ---

process_example() {
  local example_name="$1"
  local project_dir="${EXAMPLES_DIR}/${example_name}"

  if [ ! -d "$project_dir" ]; then
    err "Example not found: ${project_dir}"
    return 1
  fi

  log "Processing example: ${example_name}"
  log "Project dir: ${project_dir}"

  # Step 0: Clean up previous generated files
  log "Cleaning previous generated artifacts..."
  rm -rf "${project_dir}/docs/shield"
  rm -rf "${project_dir}/.github"
  rm -f "${project_dir}"/.shield-generate-*.log
  ok "Cleaned previous artifacts"

  # Step 1: Add GitHub Actions
  add_github_actions "$project_dir" "$example_name"
  ok "Added GitHub Actions"

  # Step 2: Update .shield.json
  update_shield_json "$project_dir" "$example_name"
  ok "Updated .shield.json"

  # Step 3: Init git in example (claude needs git context)
  rm -rf "${project_dir}/.git"
  git -C "$project_dir" init -q
  git -C "$project_dir" add .
  git -C "$project_dir" commit -q -m "init" --no-gpg-sign

  # Step 4: Run phases in sequence
  local phases_fn="${example_name//-/_}_phases"
  while IFS='|' read -r phase_name prompt; do
    run_phase "$project_dir" "$phase_name" "$prompt" || {
      err "Stopping ${example_name} at phase: ${phase_name}"
      return 1
    }
  done < <("$phases_fn" "$project_dir")

  # Step 5: Clean up temp git
  rm -rf "${project_dir}/.git"

  ok "Example ${example_name} complete"
  log "Artifacts in: ${project_dir}/docs/shield/"
}

# --- Main ---

main() {
  log "Shield Example Generator"
  log "========================"

  # Check prerequisites
  if ! command -v claude &>/dev/null; then
    err "claude CLI not found. Install: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
  fi

  local examples=()
  if [ "$SELECTED_EXAMPLE" = "all" ]; then
    for dir in "$EXAMPLES_DIR"/*/; do
      examples+=("$(basename "$dir")")
    done
  else
    examples+=("$SELECTED_EXAMPLE")
  fi

  log "Examples to process: ${examples[*]}"

  local failed=0
  for example in "${examples[@]}"; do
    if ! process_example "$example"; then
      ((failed++))
    fi
    echo
  done

  if [ "$failed" -eq 0 ]; then
    ok "All examples generated successfully"
    log ""
    log "Next steps:"
    log "  1. Review artifacts in shield/examples/*/docs/shield/"
    log "  2. git add shield/examples/ && git commit -m 'docs: generate Shield example showcase'"
  else
    err "${failed} example(s) failed"
    exit 1
  fi
}

main
