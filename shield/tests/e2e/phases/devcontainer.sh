# Phase: devcontainer
# Gated by RUN_DEVCONTAINER_E2E=1 (slow — requires Docker).
# Asserts: /shield init-devcontainer on a python-api fixture produces a
# buildable container, and `devcontainer up` + a no-op /implement-style
# command commits successfully on the bind-mounted workspace.
#
# This phase runs FROM the host (not from inside a devcontainer).

PHASE_FIXTURE="python-api"
PHASE_TIMEOUT=900

phase_prompt() {
  # Not used: this phase does its own setup + assertions.
  echo "<devcontainer e2e: see phase_assertions for the workflow>"
}

phase_skip() {
  [ "${RUN_DEVCONTAINER_E2E:-0}" != "1" ] && \
    echo "skipped: set RUN_DEVCONTAINER_E2E=1 to run this slow Docker-dependent phase"
}

phase_assertions() {
  local project_dir="$1"
  local _output="$2"
  local example="$3"

  if [ "${RUN_DEVCONTAINER_E2E:-0}" != "1" ]; then
    echo "  ⚠ skipping (set RUN_DEVCONTAINER_E2E=1 to enable)"
    return 0
  fi

  if ! command -v devcontainer >/dev/null 2>&1; then
    echo "  ✗ devcontainer CLI not installed (npm install -g @devcontainers/cli)"
    FAIL=$((FAIL + 1))
    return 0
  fi

  if ! docker info >/dev/null 2>&1; then
    echo "  ✗ Docker daemon not reachable"
    FAIL=$((FAIL + 1))
    return 0
  fi

  # 1. Scaffold .devcontainer/ in the fixture (replicates the skill flow)
  uv run python3 - <<PY
import json, shutil
from pathlib import Path
import sys
sys.path.insert(0, "$SHIELD_ROOT/scripts")
from compose_devcontainer import compose_devcontainer

target = Path("$project_dir")
target.joinpath(".devcontainer").mkdir(exist_ok=True)
cfg = compose_devcontainer(
    stacks=["python"],
    feature_map_path=Path("$SHIELD_ROOT/skills/devcontainer/feature-map.json"),
)
target.joinpath(".devcontainer/devcontainer.json").write_text(json.dumps(cfg, indent=2))
shutil.copy("$SHIELD_ROOT/skills/devcontainer/templates/shield-firewall.sh",
            target / ".devcontainer/shield-firewall.sh")
shutil.copy("$SHIELD_ROOT/skills/devcontainer/templates/Dockerfile.tmpl",
            target / ".devcontainer/Dockerfile")
fm = json.loads(Path("$SHIELD_ROOT/skills/devcontainer/feature-map.json").read_text())
tmpl = Path("$SHIELD_ROOT/skills/devcontainer/templates/postCreate.sh.tmpl").read_text()
target.joinpath(".devcontainer/postCreate.sh").write_text(
    tmpl.replace("# {{HINTS}}", fm["python"]["post_create_hint"])
)
PY

  chmod 0755 "$project_dir/.devcontainer/shield-firewall.sh" \
             "$project_dir/.devcontainer/postCreate.sh"

  # 2. Build + start the devcontainer
  if devcontainer up --workspace-folder "$project_dir" >/tmp/dc-up.log 2>&1; then
    echo "  [PASS] devcontainer up succeeds"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] devcontainer up failed (see /tmp/dc-up.log)"
    FAIL=$((FAIL + 1))
    return 0
  fi

  # 3. Verify claude is installed inside
  if devcontainer exec --workspace-folder "$project_dir" claude --version >/dev/null 2>&1; then
    echo "  [PASS] claude CLI works inside container"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] claude CLI not found / broken inside container"
    FAIL=$((FAIL + 1))
  fi

  # 4. Verify firewall behaves correctly (behavior probe, not iptables
  # introspection — the dev user can only sudo the firewall script, not
  # iptables directly, so we check OUTCOMES instead of state).
  # Behavior probe: 'connection establishes' = firewall allowed; 'http_code=000'
  # or curl error = firewall blocked. Don't use curl -f — endpoints like
  # api.anthropic.com return 401 to unauthenticated GET, which is still
  # proof the connection got through.
  http_allowed=$(devcontainer exec --workspace-folder "$project_dir" \
    bash -c 'curl -sS --max-time 8 --connect-timeout 5 https://api.anthropic.com/ -o /dev/null -w "%{http_code}" 2>/dev/null' \
    || true)
  if [ -n "$http_allowed" ] && [ "$http_allowed" != "000" ]; then
    echo "  [PASS] firewall allows api.anthropic.com (allowlisted, HTTP $http_allowed)"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] firewall blocked allowlisted host api.anthropic.com (no response)"
    FAIL=$((FAIL + 1))
  fi

  http_blocked=$(devcontainer exec --workspace-folder "$project_dir" \
    bash -c 'curl -sS --max-time 4 --connect-timeout 3 https://example.com/ -o /dev/null -w "%{http_code}" 2>/dev/null' \
    || true)
  if [ -z "$http_blocked" ] || [ "$http_blocked" = "000" ]; then
    echo "  [PASS] firewall blocks non-allowlisted host (example.com, no response)"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] firewall did NOT block non-allowlisted example.com (got HTTP $http_blocked)"
    FAIL=$((FAIL + 1))
  fi

  # 5. Verify a commit on the bind-mounted workspace works
  devcontainer exec --workspace-folder "$project_dir" bash -c \
    "cd /workspaces/* \
     && git config --global user.email dev@example.com \
     && git config --global user.name dev \
     && echo 'devcontainer-e2e' > .e2e-marker \
     && git add .e2e-marker \
     && git commit -m 'e2e: marker from devcontainer' --no-gpg-sign >/dev/null"
  if [ -f "$project_dir/.e2e-marker" ]; then
    echo "  [PASS] container commit lands on bind-mounted workspace"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] container commit did not appear on host"
    FAIL=$((FAIL + 1))
  fi

  # Cleanup: stop and remove the container (volume retained for next run)
  devcontainer exec --workspace-folder "$project_dir" \
    bash -c 'sudo docker stop $(hostname) 2>/dev/null' >/dev/null 2>&1 || true
}

# When invoked directly (`bash devcontainer.sh`), set up a temp python-api
# project and run the assertions. The framework runner sources this file
# and calls phase_assertions itself, so this main block only fires for
# ad-hoc invocations like `RUN_DEVCONTAINER_E2E=1 ./devcontainer.sh`.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  set -euo pipefail

  if [ "${RUN_DEVCONTAINER_E2E:-0}" != "1" ]; then
    echo "skipped: set RUN_DEVCONTAINER_E2E=1 to run this slow Docker-dependent phase"
    exit 0
  fi

  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SHIELD_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
  PASS=0
  FAIL=0

  # Use $HOME-based tmpdir, not /var/folders/. Podman's macOS VM doesn't
  # share /var/folders by default, so a bind mount points at an empty
  # directory inside the container. $HOME is shared on every supported
  # macOS container runtime (Docker Desktop, Colima, Podman machine).
  E2E_CACHE_DIR="${E2E_CACHE_DIR:-$HOME/.cache/shield/devcontainer-e2e}"
  mkdir -p "$E2E_CACHE_DIR"
  TMPDIR="$(mktemp -d -p "$E2E_CACHE_DIR" run.XXXXXX)"
  trap 'rm -rf "$TMPDIR"' EXIT

  PROJECT_DIR="$TMPDIR/python-api"
  if [ -d "$SHIELD_ROOT/examples/python-api" ]; then
    cp -R "$SHIELD_ROOT/examples/python-api" "$PROJECT_DIR"
  else
    mkdir -p "$PROJECT_DIR"
    printf '[project]\nname = "shield-devcontainer-e2e"\nversion = "0.0.1"\n' \
      > "$PROJECT_DIR/pyproject.toml"
  fi
  (
    cd "$PROJECT_DIR"
    git init -q
    git add -A
    git -c user.email=e2e@example.com -c user.name=e2e \
      commit -q -m "init" --allow-empty --no-gpg-sign
  )

  echo "=== devcontainer e2e (project=$PROJECT_DIR) ==="
  phase_assertions "$PROJECT_DIR" "" "python-api"
  echo ""
  TOTAL=$((PASS + FAIL))
  echo "Results: $PASS/$TOTAL passed"
  [ "$FAIL" -gt 0 ] && exit 1 || exit 0
fi
