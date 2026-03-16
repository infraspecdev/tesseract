#!/usr/bin/env bash
# Fixture engine — builds a project directory at a requested state level
#
# Fixture levels:
#   initialized     — .shield.json + source code (from example)
#   post-research   — above + shield/docs/research-*.md
#   post-planning   — above + shield/docs/plans/<name>.json + shield/docs/architecture-*.html + plan-*.html
#   post-implement  — above + code changes committed
#
# Usage: setup_fixture "post-planning" "python-api" "/path/to/project"

FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Level name → integer
fixture_level() {
  case "$1" in
    bare)              echo 0 ;;
    initialized)       echo 1 ;;
    post-research)     echo 2 ;;
    post-planning)     echo 3 ;;
    post-implement)    echo 5 ;;
    *) echo "Unknown fixture level: $1" >&2; return 1 ;;
  esac
}

# Build a project directory at the given fixture level using pre-baked files
# Usage: setup_fixture_cold "post-planning" "python-api" "/path/to/project"
setup_fixture_cold() {
  local level_name="$1"
  local example="$2"
  local project_dir="$3"
  local level
  level=$(fixture_level "$level_name")

  local example_dir="${FIXTURES_DIR}/../../../examples/${example}"
  local fixture_dir="${FIXTURES_DIR}/${example}"

  if [ ! -d "$example_dir" ]; then
    echo "ERROR: Example not found: $example_dir" >&2
    return 1
  fi
  if [ ! -d "$fixture_dir" ] && [ "$level" -ge 2 ]; then
    echo "ERROR: Fixtures not found: $fixture_dir" >&2
    return 1
  fi

  # Level 1: initialized — copy example project
  if [ "$level" -ge 1 ]; then
    mkdir -p "$project_dir"
    cp -r "$example_dir"/* "$project_dir/"
    for dotfile in "$example_dir"/.*; do
      [ -f "$dotfile" ] && cp "$dotfile" "$project_dir/"
    done
    git -C "$project_dir" init -q
    git -C "$project_dir" add .
    git -C "$project_dir" commit -q -m "init example" --no-gpg-sign
  fi

  # Level 2: post-research — add research doc
  if [ "$level" -ge 2 ]; then
    local ts
    ts=$(date +%Y%m%d-%H%M%S)
    mkdir -p "$project_dir/shield/docs"
    cp "$fixture_dir/research.md" "$project_dir/shield/docs/research-${ts}.md"
    git -C "$project_dir" add .
    git -C "$project_dir" commit -q -m "fixture: research" --no-gpg-sign
  fi

  # Level 3: post-planning — add plan artifacts
  if [ "$level" -ge 3 ]; then
    local ts
    ts=$(date +%Y%m%d-%H%M%S)
    mkdir -p "$project_dir/shield/docs/plans"
    cp "$fixture_dir/plan.json" "$project_dir/shield/docs/plans/${example}.json"
    cp "$fixture_dir/architecture.html" "$project_dir/shield/docs/architecture-${ts}.html"
    cp "$fixture_dir/plan.html" "$project_dir/shield/docs/plan-${ts}.html"
    git -C "$project_dir" add .
    git -C "$project_dir" commit -q -m "fixture: planning" --no-gpg-sign
  fi

  # Level 5: post-implement — apply code patch
  if [ "$level" -ge 5 ]; then
    if [ -f "$fixture_dir/implement.patch" ]; then
      git -C "$project_dir" apply "$fixture_dir/implement.patch"
      git -C "$project_dir" add .
      git -C "$project_dir" commit -q -m "fixture: implementation" --no-gpg-sign
    fi
  fi

  echo "$project_dir"
}
