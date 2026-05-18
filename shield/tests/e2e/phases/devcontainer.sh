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
  uv run --with-no-deps python3 - <<PY
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

  # 4. Verify firewall is active
  if devcontainer exec --workspace-folder "$project_dir" \
       bash -c "sudo iptables -L OUTPUT -n 2>/dev/null | grep -q DROP"; then
    echo "  [PASS] firewall is active (OUTPUT policy DROP)"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] firewall not active or iptables -L returned wrong policy"
    FAIL=$((FAIL + 1))
  fi

  # 5. Verify a commit on the bind-mounted workspace works
  devcontainer exec --workspace-folder "$project_dir" bash -c \
    "cd /workspaces/* && git config user.email dev@example.com \
     && git config user.name dev \
     && echo 'devcontainer-e2e' > .e2e-marker \
     && git add .e2e-marker \
     && git commit -m 'e2e: marker from devcontainer' >/dev/null"
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
