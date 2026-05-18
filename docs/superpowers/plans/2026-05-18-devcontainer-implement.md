# Devcontainer `/implement` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Shield-scaffolded devcontainer that runs `/implement` in filesystem + network egress isolation, per the design spec at `docs/superpowers/specs/2026-05-18-devcontainer-implement-design.md`.

**Architecture:** Three composition layers (Dockerfile / Dev Container Features pinned by digest / postCreate). Two security boundaries (workspace-only filesystem bind, default-deny iptables egress with allowlist). Credentials in a named Docker volume keyed by `${devcontainerId}`. Path B order: **Story 1 first hand-writes `.devcontainer/` for this very repo** so we dogfood the design before building the scaffolder.

**Tech Stack:** Python (uv for runtime + pytest), bash + shellcheck, Dev Containers spec, iptables/ipset, Claude Code plugin (markdown + JSON Schema).

**Prerequisites:** Docker Desktop / Colima / Podman running on the host for any task that exercises a real container (Stories 1.7, 9). All other tasks are pure file edits + pytest, runnable without Docker.

---

## File Plan

### New files

| Path | Responsibility |
|---|---|
| `.devcontainer/devcontainer.json` | Hand-written instance of Shield's scaffolder output, for this repo (Story 1). |
| `.devcontainer/Dockerfile` | Constant layer for this repo (Story 1). |
| `.devcontainer/shield-firewall.sh` | Firewall script copy for this repo (Story 1). |
| `.devcontainer/postCreate.sh` | Project install steps for this repo (Story 1). |
| `shield/scripts/detect_stack.py` | Stack detection from repo markers (Story 2). |
| `shield/scripts/test_detect_stack.py` | Pytest for stack detection (Story 2). |
| `shield/skills/devcontainer/feature-map.json` | Map: stack tag → Feature OCI ref (digest-pinned), postCreate hint, allowlist (Story 3). |
| `shield/skills/devcontainer/test_feature_map.py` | Schema validation for feature-map (Story 3). |
| `shield/skills/devcontainer/feature-map.schema.json` | JSON Schema for feature-map entries (Story 3). |
| `shield/scripts/compose_devcontainer.py` | Pure function: stack tags + feature-map → devcontainer.json dict (Story 4). |
| `shield/scripts/test_compose_devcontainer.py` | Pytest for the composer (Story 4). |
| `shield/skills/devcontainer/templates/shield-firewall.sh` | Source-of-truth firewall script (Story 5). |
| `shield/skills/devcontainer/templates/Dockerfile.tmpl` | Source-of-truth Dockerfile template (Story 5). |
| `shield/skills/devcontainer/templates/postCreate.sh.tmpl` | Source-of-truth postCreate template (Story 5). |
| `shield/scripts/devcontainer_gate.py` | Pre-flight decision for `/implement` (Story 6). |
| `shield/scripts/test_devcontainer_gate.py` | Pytest for the gate (Story 6). |
| `shield/commands/init-devcontainer.md` | `/shield init-devcontainer` command (Story 7). |
| `shield/skills/devcontainer/SKILL.md` | Devcontainer skill (auto-invoked) (Story 7). |
| `shield/tests/test-init-devcontainer.sh` | Integration test: run scaffolder against fixture repos (Story 7). |
| `shield/tests/e2e/phases/devcontainer.sh` | E2E phase test, gated by `RUN_DEVCONTAINER_E2E=1` (Story 9). |

### Modified files

| Path | What changes |
|---|---|
| `shield/skills/general/implement-feature/SKILL.md` | Insert Step 0 calling the gate (Story 8). |
| `shield/tests/run-all.sh` | Add sections for feature-map validation + detect_stack + compose_devcontainer + devcontainer_gate pytests + init-devcontainer integration test (Stories 2, 3, 4, 6, 7). |
| `shield/schemas/shield.schema.json` | Add `devcontainer` block (Story 11). |
| `shield/README.md` | New devcontainer section: setup, security model, escape hatches (Story 11). |
| `.claude-plugin/marketplace.json` | Bump `shield` version from 2.16.0 → 2.17.0 (Story 11). |

---

## Story 1: Dogfood — hand-write `.devcontainer/` for this repo

**Why first:** Path B. Before building the scaffolder, apply the spec to this very repo by hand. The hand-written files become the canonical reference the scaffolder must reproduce in later stories. After this story lands, the user can reopen this worktree in VS Code's devcontainer and continue from inside.

### Task 1.1: Create `.devcontainer/Dockerfile`

**Files:**
- Create: `.devcontainer/Dockerfile`

- [ ] **Step 1: Write the file**

```dockerfile
# .devcontainer/Dockerfile
# Constant layer for the Shield devcontainer. Hand-written instance of the
# template at shield/skills/devcontainer/templates/Dockerfile.tmpl (which
# Story 5 will create as the source of truth).
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates iptables ipset dnsutils jq sudo \
    && rm -rf /var/lib/apt/lists/*

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid "$USER_GID" "$USERNAME" \
    && useradd -m -s /bin/bash --uid "$USER_UID" --gid "$USER_GID" "$USERNAME" \
    && echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/bin/shield-firewall.sh" \
       > /etc/sudoers.d/shield-firewall \
    && chmod 0440 /etc/sudoers.d/shield-firewall

# Pin Claude Code to a concrete version. Bump deliberately.
ARG CLAUDE_CODE_VERSION=2.0.0
RUN curl -fsSL https://claude.ai/install.sh \
      | CLAUDE_VERSION="${CLAUDE_CODE_VERSION}" bash

# Install uv globally so /implement's Python steps work.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && chmod 0755 /usr/local/bin/uv

COPY shield-firewall.sh /usr/local/bin/shield-firewall.sh
RUN chmod 0755 /usr/local/bin/shield-firewall.sh

USER dev
WORKDIR /workspaces
```

- [ ] **Step 2: Commit**

```bash
git add .devcontainer/Dockerfile
git commit -m "feat(shield): add Dockerfile for /implement devcontainer

Constant layer per spec §Architecture. Non-root 'dev' user, sudoers
scoped to firewall script only, Claude Code + uv pinned."
```

### Task 1.2: Create `.devcontainer/shield-firewall.sh`

**Files:**
- Create: `.devcontainer/shield-firewall.sh`

- [ ] **Step 1: Write the file**

```bash
#!/bin/bash
# .devcontainer/shield-firewall.sh
# Default-deny outbound + per-stack allowlist.
# Hand-written instance of the template at
# shield/skills/devcontainer/templates/shield-firewall.sh (Story 5 source).
# Named shield-firewall.sh (not init-firewall.sh) to avoid silent overwrite
# by upstream Feature ghcr.io/anthropics/devcontainer-features/claude-code
# (claude-code#32113).
set -euo pipefail

# Default-deny
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Loopback always
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Established / related return traffic
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# DNS only to Docker's embedded resolver (claude-code#36907 mitigation)
iptables -A OUTPUT -p udp --dport 53 -d 127.0.0.11 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -d 127.0.0.11 -j ACCEPT

# Resolve & allowlist Anthropic + extra hosts
ipset create allowlist hash:ip -exist
DEFAULT_HOSTS="api.anthropic.com statsig.anthropic.com claude.ai console.anthropic.com"
HOSTS="${DEFAULT_HOSTS} ${EXTRA_HOSTS:-}"
for host in $HOSTS; do
  for ip in $(dig +short A "$host"); do
    ipset add allowlist "$ip" -exist
  done
done

# GitHub meta CIDRs
ipset create allowlist_cidr hash:net -exist
curl -fsSL https://api.github.com/meta \
  | jq -r '.git[]' \
  | while read -r cidr; do
      ipset add allowlist_cidr "$cidr" -exist
    done

iptables -A OUTPUT -m set --match-set allowlist      dst -j ACCEPT
iptables -A OUTPUT -m set --match-set allowlist_cidr dst -j ACCEPT
```

- [ ] **Step 2: Make executable**

```bash
chmod 0755 .devcontainer/shield-firewall.sh
```

- [ ] **Step 3: Verify shellcheck passes**

```bash
shellcheck .devcontainer/shield-firewall.sh
```

Expected: no output (clean pass). If shellcheck is not installed locally, skip — CI will catch.

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/shield-firewall.sh
git commit -m "feat(shield): add shield-firewall.sh for devcontainer

Default-deny outbound + allowlist Anthropic API, GitHub CIDRs, and
EXTRA_HOSTS env var. Locks port 53 to 127.0.0.11 (claude-code#36907).
Named shield-firewall.sh to avoid Feature overwrite (claude-code#32113)."
```

### Task 1.3: Create `.devcontainer/devcontainer.json`

**Files:**
- Create: `.devcontainer/devcontainer.json`

This repo is polyglot — Python (shield's adapters use uv) + shell + markdown. The Feature for Python is included; node is not (no `package.json` at root). Digests below MUST be filled in with actual values fetched at implementation time; placeholders are flagged.

- [ ] **Step 1: Fetch current digests for the Features we use**

```bash
# Fetch digest for python:1 and github-cli:1
crane digest ghcr.io/devcontainers/features/python:1
crane digest ghcr.io/devcontainers/features/github-cli:1
```

If `crane` is not installed:

```bash
# Fallback: docker manifest inspect
docker manifest inspect ghcr.io/devcontainers/features/python:1 \
  --verbose 2>/dev/null \
  | jq -r 'if type=="array" then .[0].Descriptor.digest else .Descriptor.digest // .descriptor.digest end' \
  || echo "fetch manually from https://github.com/devcontainers/features"
```

Record both digests; you'll use them in Step 2.

- [ ] **Step 2: Write the file**

Replace `<PYTHON_DIGEST>` and `<GH_DIGEST>` with values from Step 1.

```json
{
  "$schema": "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json",
  "name": "shield-implement",
  "build": { "dockerfile": "Dockerfile" },
  "features": {
    "ghcr.io/devcontainers/features/python:1@sha256:<PYTHON_DIGEST>": {
      "version": "3.12"
    },
    "ghcr.io/devcontainers/features/github-cli:1@sha256:<GH_DIGEST>": {}
  },
  "remoteUser": "dev",
  "capAdd": ["NET_ADMIN", "NET_RAW"],
  "mounts": [
    "source=claude-config-${devcontainerId},target=/home/dev/.claude,type=volume"
  ],
  "containerEnv": {
    "SHIELD_IN_DEVCONTAINER": "true",
    "EXTRA_HOSTS": "pypi.org files.pythonhosted.org astral.sh"
  },
  "postCreateCommand": "bash .devcontainer/postCreate.sh",
  "postStartCommand": "sudo /usr/local/bin/shield-firewall.sh",
  "customizations": {
    "vscode": {
      "extensions": ["anthropic.claude-code"]
    }
  }
}
```

- [ ] **Step 3: Verify JSON is parseable**

```bash
python3 -c "import json; json.load(open('.devcontainer/devcontainer.json'))"
```

Expected: no output (success).

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/devcontainer.json
git commit -m "feat(shield): add devcontainer.json for /implement isolation

Polyglot: python (3.12) + github-cli. Features pinned by @sha256.
Named volume claude-config-\${devcontainerId} for credentials.
Firewall via postStartCommand with NET_ADMIN/NET_RAW caps."
```

### Task 1.4: Create `.devcontainer/postCreate.sh`

**Files:**
- Create: `.devcontainer/postCreate.sh`

- [ ] **Step 1: Write the file**

```bash
#!/bin/bash
# .devcontainer/postCreate.sh
# Project-specific install hints. Idempotent.
set -euo pipefail
cd /workspaces/* 2>/dev/null || cd "$(ls -d /workspaces/* | head -n1)"

# Python (shield adapters use uv)
if [ -f shield/adapters/clickup/pyproject.toml ]; then
  (cd shield/adapters/clickup && uv sync)
fi
if [ -f shield/adapters/sast/sonarqube/pyproject.toml ]; then
  (cd shield/adapters/sast/sonarqube && uv sync)
fi
if [ -f shield/adapters/sast/semgrep/pyproject.toml ]; then
  (cd shield/adapters/sast/semgrep && uv sync)
fi

# Top-level deps used by tests
python3 -m pip install --user --quiet jsonschema pyyaml 2>/dev/null \
  || python3 -m pip install --user --break-system-packages --quiet jsonschema pyyaml

echo "postCreate complete."
```

- [ ] **Step 2: Make executable**

```bash
chmod 0755 .devcontainer/postCreate.sh
```

- [ ] **Step 3: Verify shellcheck**

```bash
shellcheck .devcontainer/postCreate.sh
```

Expected: clean pass.

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/postCreate.sh
git commit -m "feat(shield): add postCreate.sh for devcontainer

Idempotent install hints: shield adapters (uv sync) + top-level
test deps (jsonschema, pyyaml)."
```

### Task 1.5: Verify the build (manual, requires Docker)

- [ ] **Step 1: Build the container**

```bash
devcontainer up --workspace-folder .
```

Expected: build succeeds; ends with `outcome=success`. If `devcontainer` CLI is not installed: `npm install -g @devcontainers/cli`.

- [ ] **Step 2: Exec into the container**

```bash
devcontainer exec --workspace-folder . bash -lc 'whoami && claude --version && uv --version && which iptables && which ipset'
```

Expected:
- `whoami` → `dev`
- `claude --version` → a Claude Code version string
- `uv --version` → a uv version
- `iptables`/`ipset` → paths under `/usr/sbin/` or `/usr/local/sbin/`

- [ ] **Step 3: Verify firewall ran**

```bash
devcontainer exec --workspace-folder . bash -lc 'sudo iptables -L OUTPUT -n | head -20'
```

Expected: policy is `DROP`, with ACCEPT rules for loopback, ESTABLISHED, port 53 to 127.0.0.11, and ipset matches.

- [ ] **Step 4: Verify network policy works (allow + deny)**

```bash
# Allowed (should succeed)
devcontainer exec --workspace-folder . bash -lc 'curl -fsSL --max-time 10 https://api.anthropic.com/ 2>&1 | head -3'

# Blocked (should fail to connect)
devcontainer exec --workspace-folder . bash -lc 'curl -fsSL --max-time 5 https://example.com/ 2>&1 || echo "BLOCKED as expected"'
```

Expected: first curl gets a response (likely 401 or similar — it connected). Second curl times out or fails with "BLOCKED as expected".

- [ ] **Step 5: No commit needed — this task is verification only**

If the smoke test fails, file the failure as part of Task 1.5 work; iterate on Tasks 1.1–1.4 until smoke passes, then proceed.

### Task 1.6: Add a static-check test for the .devcontainer/ files

**Files:**
- Create: `shield/tests/test-devcontainer-files.sh`
- Modify: `shield/tests/run-all.sh` (add new section)

- [ ] **Step 1: Write the failing test**

Write a test that asserts the four `.devcontainer/` files exist and have valid syntax. This is a regression guard: any future change that breaks one of them gets caught.

```bash
#!/usr/bin/env bash
# shield/tests/test-devcontainer-files.sh
# Static checks for the .devcontainer/ files.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

fail=0

assert() {
  if eval "$1" >/dev/null 2>&1; then
    echo "  ✓ $2"
  else
    echo "  ✗ $2"
    fail=$((fail + 1))
  fi
}

assert "[ -f .devcontainer/Dockerfile ]" "Dockerfile exists"
assert "[ -f .devcontainer/devcontainer.json ]" "devcontainer.json exists"
assert "[ -f .devcontainer/shield-firewall.sh ]" "shield-firewall.sh exists"
assert "[ -f .devcontainer/postCreate.sh ]" "postCreate.sh exists"

assert "python3 -c 'import json; json.load(open(\".devcontainer/devcontainer.json\"))'" \
  "devcontainer.json is valid JSON"

assert "grep -q 'remoteUser.*dev' .devcontainer/devcontainer.json" \
  "devcontainer.json sets remoteUser=dev"

assert "grep -q 'NET_ADMIN' .devcontainer/devcontainer.json" \
  "devcontainer.json declares NET_ADMIN capability"

assert "grep -q 'claude-config-' .devcontainer/devcontainer.json" \
  "devcontainer.json mounts named claude-config volume"

assert "grep -q '^#!/bin/bash' .devcontainer/shield-firewall.sh" \
  "shield-firewall.sh has bash shebang"

assert "grep -q '127.0.0.11' .devcontainer/shield-firewall.sh" \
  "shield-firewall.sh locks DNS to Docker's resolver (#36907)"

if [ $fail -gt 0 ]; then
  echo "FAILED: $fail check(s)"
  exit 1
fi
echo "ALL DEVCONTAINER STATIC CHECKS PASSED"
```

- [ ] **Step 2: Make executable and run**

```bash
chmod 0755 shield/tests/test-devcontainer-files.sh
shield/tests/test-devcontainer-files.sh
```

Expected: `ALL DEVCONTAINER STATIC CHECKS PASSED`.

- [ ] **Step 3: Wire into `shield/tests/run-all.sh`**

Insert a new section between section 10 (Markdown Renderer) and the Summary. Edit `shield/tests/run-all.sh`, find the line that reads `# --- Summary ---` and insert directly above it:

```bash
# --- 11. Devcontainer Static Checks ---
echo "11. Devcontainer Static Checks"
run_test_verbose "devcontainer files valid" "$SHIELD_ROOT/tests/test-devcontainer-files.sh"
echo ""
```

- [ ] **Step 4: Run the full suite**

```bash
make test
```

Expected: previous 24 tests still pass, plus the new "devcontainer files valid" test passes. New total: 25/25.

- [ ] **Step 5: Commit**

```bash
git add shield/tests/test-devcontainer-files.sh shield/tests/run-all.sh
git commit -m "test(shield): add static checks for .devcontainer/ files

Asserts presence, validity, and key spec invariants (remoteUser=dev,
NET_ADMIN, named volume mount, DNS pinning) of the .devcontainer/
files. Wired into run-all.sh as section 11."
```

---

**STORY 1 EXIT GATE.** At this point the user should reopen this worktree in VS Code's devcontainer (or `devcontainer up && devcontainer exec bash`), then continue with Story 2+ from inside the container. Stories 2 onward are pure file-edit + pytest work, so they don't require Docker.

---

## Story 2: Stack detection

### Task 2.1: Write failing test for stack detection

**Files:**
- Create: `shield/scripts/test_detect_stack.py`

- [ ] **Step 1: Write the test file**

```python
# shield/scripts/test_detect_stack.py
"""Tests for detect_stack.py.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_detect_stack.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from detect_stack import detect_stack  # type: ignore[import-not-found]


def _make(tmp_path: Path, files: dict[str, str]) -> Path:
    for relpath, content in files.items():
        target = tmp_path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    return tmp_path


@pytest.mark.parametrize(
    "files,expected",
    [
        ({"pyproject.toml": "[project]\nname='x'\n"}, {"python"}),
        ({"requirements.txt": "requests==2.0\n"}, {"python"}),
        ({"package.json": "{}"}, {"node"}),
        ({"package.json": "{}", "tsconfig.json": "{}"}, {"node", "node-ts"}),
        ({"go.mod": "module x\n"}, {"go"}),
        ({"pom.xml": "<project/>"}, {"java"}),
        ({"build.gradle": ""}, {"java"}),
        ({"build.gradle.kts": ""}, {"java"}),
        ({"main.tf": "resource {}\n"}, {"terraform"}),
        ({"infra/sub/aws.tf": "resource {}\n"}, {"terraform"}),
        ({"Cargo.toml": "[package]\n"}, {"rust"}),
        ({"Gemfile": ""}, {"ruby"}),
        ({"Dockerfile": "FROM scratch\n"}, {"docker-in-docker"}),
        ({"docker-compose.yml": "services: {}\n"}, {"docker-in-docker"}),
        ({"helm/values.yaml": ""}, {"kubernetes"}),
        ({"kustomization.yaml": ""}, {"kubernetes"}),
        ({"pyproject.toml": "", "package.json": "{}"}, {"python", "node"}),
        ({}, set()),
    ],
)
def test_detect_stack(tmp_path: Path, files: dict[str, str], expected: set[str]) -> None:
    repo = _make(tmp_path, files)
    assert set(detect_stack(repo)) == expected


def test_detect_stack_returns_sorted_list(tmp_path: Path) -> None:
    """Output is deterministic — caller can use it in a stable composition."""
    _make(tmp_path, {"pyproject.toml": "", "package.json": "{}", "go.mod": "module x"})
    assert detect_stack(tmp_path) == sorted(detect_stack(tmp_path))
```

- [ ] **Step 2: Run the test — confirm it fails**

```bash
cd shield/scripts && uv run --with pytest pytest test_detect_stack.py -v
```

Expected: ImportError / ModuleNotFoundError on `from detect_stack import detect_stack`.

### Task 2.2: Implement stack detection

**Files:**
- Create: `shield/scripts/detect_stack.py`

- [ ] **Step 1: Write the minimal implementation**

```python
# shield/scripts/detect_stack.py
"""Detect a project's tech stack from filesystem markers.

Mirrors the marker rules in shield/skills/general/research/repo-scan.md so
the devcontainer scaffolder and the research repo-scan stay in sync.

Public API:
    detect_stack(root: Path) -> list[str]

Returns a sorted list of stack tags. Multiple tags are returned for polyglot
repos. Unknown markers are silently ignored; absent markers produce an empty
list.
"""
from __future__ import annotations

from pathlib import Path


def detect_stack(root: Path) -> list[str]:
    root = Path(root)
    tags: set[str] = set()

    # Python
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        tags.add("python")

    # Node (+ node-ts if tsconfig.json is present)
    if (root / "package.json").exists():
        tags.add("node")
        if (root / "tsconfig.json").exists():
            tags.add("node-ts")

    # Go
    if (root / "go.mod").exists():
        tags.add("go")

    # Java
    if (root / "pom.xml").exists() \
       or (root / "build.gradle").exists() \
       or (root / "build.gradle.kts").exists():
        tags.add("java")

    # Terraform — recursive
    if _has_recursive(root, "*.tf"):
        tags.add("terraform")

    # Rust
    if (root / "Cargo.toml").exists():
        tags.add("rust")

    # Ruby
    if (root / "Gemfile").exists():
        tags.add("ruby")

    # Docker (flag)
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        tags.add("docker-in-docker")

    # Kubernetes (flag)
    if (root / "helm").is_dir() or (root / "kustomization.yaml").exists():
        tags.add("kubernetes")

    return sorted(tags)


def _has_recursive(root: Path, pattern: str) -> bool:
    """True if any file matching pattern exists at or below root.

    Skips hidden dirs (.git, .venv, etc.) and node_modules to stay fast.
    """
    SKIP = {".git", ".venv", "node_modules", "__pycache__", ".worktrees"}
    for p in root.rglob(pattern):
        parts = set(p.relative_to(root).parts)
        if parts & SKIP:
            continue
        return True
    return False
```

- [ ] **Step 2: Run the test — confirm pass**

```bash
cd shield/scripts && uv run --with pytest pytest test_detect_stack.py -v
```

Expected: all parametrized cases plus `test_detect_stack_returns_sorted_list` pass.

### Task 2.3: Wire into `run-all.sh` and commit

**Files:**
- Modify: `shield/tests/run-all.sh`

- [ ] **Step 1: Add a section to run-all.sh**

Insert between sections 10 and 11 (or wherever fits in the existing numbering):

```bash
# --- 12. Stack Detection ---
echo "12. Stack Detection"
if command -v uv &>/dev/null; then
  run_test_verbose "detect_stack tests pass" bash -c \
    "cd '$SHIELD_ROOT/scripts' && uv run --with pytest pytest test_detect_stack.py -q 2>&1"
else
  echo "  ⚠ uv not installed, skipping detect_stack tests"
fi
echo ""
```

- [ ] **Step 2: Run full suite**

```bash
make test
```

Expected: 25 → 26 tests passing.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/detect_stack.py shield/scripts/test_detect_stack.py shield/tests/run-all.sh
git commit -m "feat(shield): stack detection for devcontainer scaffolder

Detects python / node / go / java / terraform / rust / ruby and flags
docker-in-docker + kubernetes. Sorted output for deterministic
composition. Wired into run-all.sh."
```

---

## Story 3: Feature map data + schema

### Task 3.1: Create the feature-map JSON Schema

**Files:**
- Create: `shield/skills/devcontainer/feature-map.schema.json`

- [ ] **Step 1: Write the schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Shield devcontainer feature map",
  "type": "object",
  "patternProperties": {
    "^[a-z][a-z0-9-]*$": {
      "type": "object",
      "required": ["feature", "default_options", "post_create_hint", "firewall_allowlist"],
      "additionalProperties": false,
      "properties": {
        "feature": {
          "type": "string",
          "pattern": "^ghcr\\.io/[a-z0-9-/]+:[a-z0-9.]+@sha256:[a-f0-9]{64}$",
          "description": "Dev Container Feature OCI ref, pinned by @sha256 digest."
        },
        "default_options": { "type": "object" },
        "post_create_hint": {
          "type": "string",
          "description": "Bash snippet appended to postCreate.sh when this stack is detected."
        },
        "firewall_allowlist": {
          "type": "array",
          "items": { "type": "string", "format": "hostname" },
          "uniqueItems": true,
          "description": "Hostnames added to EXTRA_HOSTS when this stack is detected."
        }
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Verify the schema itself parses**

```bash
python3 -c "import json; json.load(open('shield/skills/devcontainer/feature-map.schema.json'))"
```

### Task 3.2: Write the failing test for feature-map validation

**Files:**
- Create: `shield/skills/devcontainer/test_feature_map.py`

- [ ] **Step 1: Write the test**

```python
# shield/skills/devcontainer/test_feature_map.py
"""Validates feature-map.json against feature-map.schema.json.

Runnable: `cd shield/skills/devcontainer && uv run --with jsonschema --with pytest pytest -v`
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

DIR = Path(__file__).resolve().parent
MAP_PATH = DIR / "feature-map.json"
SCHEMA_PATH = DIR / "feature-map.schema.json"


def test_feature_map_validates() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    data = json.loads(MAP_PATH.read_text())
    jsonschema.validate(data, schema)


def test_feature_map_has_required_stacks() -> None:
    """Spec §Components.2 lists the stacks Shield supports out of the box."""
    data = json.loads(MAP_PATH.read_text())
    required = {"python", "node", "go", "java", "terraform"}
    missing = required - set(data.keys())
    assert not missing, f"feature-map missing entries: {missing}"


@pytest.mark.parametrize("stack,allowlist_must_include", [
    ("python", "pypi.org"),
    ("node", "registry.npmjs.org"),
    ("go", "proxy.golang.org"),
    ("terraform", "registry.terraform.io"),
])
def test_feature_map_firewall_allowlist_sane(stack: str, allowlist_must_include: str) -> None:
    data = json.loads(MAP_PATH.read_text())
    assert allowlist_must_include in data[stack]["firewall_allowlist"]
```

- [ ] **Step 2: Run — confirm it fails**

```bash
cd shield/skills/devcontainer && uv run --with jsonschema --with pytest pytest -v
```

Expected: FileNotFoundError for `feature-map.json`.

### Task 3.3: Create feature-map.json with real digests

**Files:**
- Create: `shield/skills/devcontainer/feature-map.json`

- [ ] **Step 1: Fetch current digests for each Feature**

```bash
for f in python node go java terraform rust ruby github-cli; do
  digest=$(crane digest ghcr.io/devcontainers/features/$f:1 2>/dev/null \
           || echo "FETCH_MANUALLY")
  echo "$f -> $digest"
done
```

If `crane` is unavailable, fetch manually from each Feature's GitHub release at https://github.com/devcontainers/features/releases or:

```bash
docker pull ghcr.io/devcontainers/features/python:1
docker image inspect --format='{{index .RepoDigests 0}}' ghcr.io/devcontainers/features/python:1
```

Record the digests; you'll use them in Step 2.

- [ ] **Step 2: Write the file**

Substitute `<PYTHON_DIGEST>` etc. with values from Step 1.

```json
{
  "python": {
    "feature": "ghcr.io/devcontainers/features/python:1@sha256:<PYTHON_DIGEST>",
    "default_options": { "version": "3.12" },
    "post_create_hint": "if [ -f pyproject.toml ]; then uv sync; elif [ -f requirements.txt ]; then pip install -r requirements.txt; fi",
    "firewall_allowlist": ["pypi.org", "files.pythonhosted.org", "astral.sh"]
  },
  "node": {
    "feature": "ghcr.io/devcontainers/features/node:1@sha256:<NODE_DIGEST>",
    "default_options": { "version": "lts" },
    "post_create_hint": "if [ -f pnpm-lock.yaml ]; then pnpm install; elif [ -f yarn.lock ]; then yarn install; else npm install; fi",
    "firewall_allowlist": ["registry.npmjs.org"]
  },
  "go": {
    "feature": "ghcr.io/devcontainers/features/go:1@sha256:<GO_DIGEST>",
    "default_options": { "version": "1.22" },
    "post_create_hint": "if [ -f go.mod ]; then go mod download; fi",
    "firewall_allowlist": ["proxy.golang.org", "sum.golang.org"]
  },
  "java": {
    "feature": "ghcr.io/devcontainers/features/java:1@sha256:<JAVA_DIGEST>",
    "default_options": { "version": "21" },
    "post_create_hint": "if [ -f pom.xml ]; then mvn -q dependency:resolve; elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then gradle --no-daemon dependencies; fi",
    "firewall_allowlist": ["repo.maven.apache.org", "plugins.gradle.org", "services.gradle.org"]
  },
  "terraform": {
    "feature": "ghcr.io/devcontainers/features/terraform:1@sha256:<TF_DIGEST>",
    "default_options": {},
    "post_create_hint": "terraform -chdir=$(dirname $(find . -name '*.tf' -not -path '*/.terraform/*' | head -n1)) init -input=false || true",
    "firewall_allowlist": ["registry.terraform.io", "releases.hashicorp.com"]
  }
}
```

`rust`, `ruby`, `github-cli` deferred — add later if a user-repo needs them. Story 11 documents this extension point.

- [ ] **Step 3: Run the test — confirm pass**

```bash
cd shield/skills/devcontainer && uv run --with jsonschema --with pytest pytest -v
```

Expected: all three test functions pass.

- [ ] **Step 4: Wire into `run-all.sh`**

Add a section to `shield/tests/run-all.sh`:

```bash
# --- 13. Devcontainer Feature Map ---
echo "13. Devcontainer Feature Map"
if command -v uv &>/dev/null; then
  run_test_verbose "feature-map.json validates" bash -c \
    "cd '$SHIELD_ROOT/skills/devcontainer' && uv run --with jsonschema --with pytest pytest -q 2>&1"
else
  echo "  ⚠ uv not installed, skipping feature-map tests"
fi
echo ""
```

- [ ] **Step 5: Run full suite**

```bash
make test
```

Expected: 26 → 27 passing.

- [ ] **Step 6: Commit**

```bash
git add shield/skills/devcontainer/feature-map.json \
        shield/skills/devcontainer/feature-map.schema.json \
        shield/skills/devcontainer/test_feature_map.py \
        shield/tests/run-all.sh
git commit -m "feat(shield): feature-map.json for devcontainer scaffolder

Maps detected stacks (python/node/go/java/terraform) to digest-pinned
Dev Container Features, postCreate hints, and per-stack firewall
allowlist entries. JSON Schema validates each entry; pytest enforces
required stacks and sane allowlists."
```

---

## Story 4: Devcontainer compose

### Task 4.1: Write failing test for the composer

**Files:**
- Create: `shield/scripts/test_compose_devcontainer.py`

- [ ] **Step 1: Write the test**

```python
# shield/scripts/test_compose_devcontainer.py
"""Tests for compose_devcontainer.py.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_compose_devcontainer.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from compose_devcontainer import compose_devcontainer  # type: ignore[import-not-found]

FEATURE_MAP_PATH = SCRIPT_DIR.parent / "skills" / "devcontainer" / "feature-map.json"


def test_python_only_compose() -> None:
    cfg = compose_devcontainer(stacks=["python"], feature_map_path=FEATURE_MAP_PATH)
    assert cfg["remoteUser"] == "dev"
    assert "NET_ADMIN" in cfg["capAdd"]
    assert "NET_RAW" in cfg["capAdd"]
    # exactly one python feature, digest-pinned
    py_features = [k for k in cfg["features"] if "/python:" in k]
    assert len(py_features) == 1
    assert "@sha256:" in py_features[0]
    # EXTRA_HOSTS contains python's allowlist
    extra = cfg["containerEnv"]["EXTRA_HOSTS"].split()
    assert "pypi.org" in extra
    assert "files.pythonhosted.org" in extra


def test_polyglot_compose_python_node() -> None:
    cfg = compose_devcontainer(stacks=["python", "node"], feature_map_path=FEATURE_MAP_PATH)
    feature_keys = list(cfg["features"].keys())
    assert any("/python:" in k for k in feature_keys)
    assert any("/node:" in k for k in feature_keys)
    extra = cfg["containerEnv"]["EXTRA_HOSTS"].split()
    assert "pypi.org" in extra
    assert "registry.npmjs.org" in extra


def test_named_volume_mount_present() -> None:
    cfg = compose_devcontainer(stacks=["python"], feature_map_path=FEATURE_MAP_PATH)
    assert any("claude-config-" in m and "type=volume" in m for m in cfg["mounts"])


def test_shield_env_var_set() -> None:
    cfg = compose_devcontainer(stacks=["python"], feature_map_path=FEATURE_MAP_PATH)
    assert cfg["containerEnv"]["SHIELD_IN_DEVCONTAINER"] == "true"


def test_unknown_stack_silently_skipped_with_warning(capsys: pytest.CaptureFixture[str]) -> None:
    cfg = compose_devcontainer(stacks=["python", "lisp"], feature_map_path=FEATURE_MAP_PATH)
    # Lisp not in feature-map → no lisp Feature, no Crash, warning to stderr.
    assert all("/lisp" not in k for k in cfg["features"])
    captured = capsys.readouterr()
    assert "lisp" in captured.err.lower()


def test_extra_hosts_user_allowlist_appended() -> None:
    cfg = compose_devcontainer(
        stacks=["python"],
        feature_map_path=FEATURE_MAP_PATH,
        user_extra_allowlist=["internal.example.com", "mirror.corp.local"],
    )
    extra = cfg["containerEnv"]["EXTRA_HOSTS"].split()
    assert "internal.example.com" in extra
    assert "mirror.corp.local" in extra
```

- [ ] **Step 2: Run — confirm fail**

```bash
cd shield/scripts && uv run --with pytest pytest test_compose_devcontainer.py -v
```

Expected: ModuleNotFoundError for `compose_devcontainer`.

### Task 4.2: Implement the composer

**Files:**
- Create: `shield/scripts/compose_devcontainer.py`

- [ ] **Step 1: Write the implementation**

```python
# shield/scripts/compose_devcontainer.py
"""Compose a devcontainer.json dict from detected stacks + feature-map.

Public API:
    compose_devcontainer(stacks, feature_map_path, user_extra_allowlist=None) -> dict

Pure function. No filesystem writes. The caller serializes the returned dict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable


def compose_devcontainer(
    stacks: Iterable[str],
    feature_map_path: Path,
    user_extra_allowlist: list[str] | None = None,
) -> dict:
    feature_map = json.loads(Path(feature_map_path).read_text())

    features: dict[str, dict] = {}
    extra_hosts: list[str] = []
    skipped: list[str] = []

    for stack in stacks:
        entry = feature_map.get(stack)
        if entry is None:
            skipped.append(stack)
            continue
        features[entry["feature"]] = entry.get("default_options", {})
        extra_hosts.extend(entry.get("firewall_allowlist", []))

    if user_extra_allowlist:
        extra_hosts.extend(user_extra_allowlist)

    for stack in skipped:
        print(
            f"warning: stack '{stack}' has no feature-map entry; "
            f"its Feature and postCreate hint will be omitted.",
            file=sys.stderr,
        )

    return {
        "$schema": "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json",
        "name": "shield-implement",
        "build": {"dockerfile": "Dockerfile"},
        "features": features,
        "remoteUser": "dev",
        "capAdd": ["NET_ADMIN", "NET_RAW"],
        "mounts": [
            "source=claude-config-${devcontainerId},target=/home/dev/.claude,type=volume",
        ],
        "containerEnv": {
            "SHIELD_IN_DEVCONTAINER": "true",
            "EXTRA_HOSTS": " ".join(extra_hosts),
        },
        "postCreateCommand": "bash .devcontainer/postCreate.sh",
        "postStartCommand": "sudo /usr/local/bin/shield-firewall.sh",
        "customizations": {
            "vscode": {"extensions": ["anthropic.claude-code"]},
        },
    }
```

- [ ] **Step 2: Run — confirm pass**

```bash
cd shield/scripts && uv run --with pytest pytest test_compose_devcontainer.py -v
```

Expected: all 6 tests pass.

### Task 4.3: Wire into `run-all.sh` and commit

- [ ] **Step 1: Add to run-all.sh**

```bash
# --- 14. Devcontainer Composer ---
echo "14. Devcontainer Composer"
if command -v uv &>/dev/null; then
  run_test_verbose "compose_devcontainer tests pass" bash -c \
    "cd '$SHIELD_ROOT/scripts' && uv run --with pytest pytest test_compose_devcontainer.py -q 2>&1"
else
  echo "  ⚠ uv not installed, skipping composer tests"
fi
echo ""
```

- [ ] **Step 2: Run full suite**

```bash
make test
```

Expected: 27 → 28.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/compose_devcontainer.py shield/scripts/test_compose_devcontainer.py shield/tests/run-all.sh
git commit -m "feat(shield): devcontainer.json composer

Pure function: stacks + feature-map -> devcontainer.json dict.
Skips unknown stacks with stderr warning. Merges per-stack +
user-provided allowlist entries into EXTRA_HOSTS."
```

---

## Story 5: Templates for the scaffolder

This story creates the **source-of-truth** templates that the scaffolder (Story 7) copies into user repos. Story 1 already hand-wrote instances of these for *this* repo; here we extract them as templates so they can be reused.

### Task 5.1: Create the firewall template

**Files:**
- Create: `shield/skills/devcontainer/templates/shield-firewall.sh`

- [ ] **Step 1: Copy the working script from Story 1**

```bash
mkdir -p shield/skills/devcontainer/templates
cp .devcontainer/shield-firewall.sh shield/skills/devcontainer/templates/shield-firewall.sh
chmod 0755 shield/skills/devcontainer/templates/shield-firewall.sh
```

- [ ] **Step 2: Verify shellcheck**

```bash
shellcheck shield/skills/devcontainer/templates/shield-firewall.sh
```

Expected: clean.

### Task 5.2: Create the Dockerfile template

**Files:**
- Create: `shield/skills/devcontainer/templates/Dockerfile.tmpl`

- [ ] **Step 1: Copy from Story 1**

```bash
cp .devcontainer/Dockerfile shield/skills/devcontainer/templates/Dockerfile.tmpl
```

The template is byte-identical to Story 1's Dockerfile. The scaffolder (Story 7) copies it verbatim.

### Task 5.3: Create the postCreate.sh template

**Files:**
- Create: `shield/skills/devcontainer/templates/postCreate.sh.tmpl`

- [ ] **Step 1: Write the template**

The template is a skeleton; the scaffolder fills in stack-specific snippets from `feature-map.json`'s `post_create_hint` values.

```bash
#!/bin/bash
# postCreate.sh — generated by /shield init-devcontainer
# Project-specific install hints. Idempotent.
set -euo pipefail
cd /workspaces/* 2>/dev/null || cd "$(ls -d /workspaces/* | head -n1)"

# === SCAFFOLDER FILLS THESE LINES PER DETECTED STACK ===
# (each line below is one stack's post_create_hint from feature-map.json)
# {{HINTS}}
# === END SCAFFOLDER-FILLED ===

echo "postCreate complete."
```

- [ ] **Step 2: Make executable**

```bash
chmod 0755 shield/skills/devcontainer/templates/postCreate.sh.tmpl
```

### Task 5.4: Add static check for templates and commit

**Files:**
- Modify: `shield/tests/test-devcontainer-files.sh` (extend)

- [ ] **Step 1: Append template checks**

Add these lines to the bottom of `assert ...` blocks in `shield/tests/test-devcontainer-files.sh` (before the `if [ $fail -gt 0 ]` block):

```bash
assert "[ -f shield/skills/devcontainer/templates/shield-firewall.sh ]" "template: shield-firewall.sh exists"
assert "[ -f shield/skills/devcontainer/templates/Dockerfile.tmpl ]" "template: Dockerfile.tmpl exists"
assert "[ -f shield/skills/devcontainer/templates/postCreate.sh.tmpl ]" "template: postCreate.sh.tmpl exists"
assert "diff -q .devcontainer/shield-firewall.sh shield/skills/devcontainer/templates/shield-firewall.sh" \
  "template: shield-firewall.sh matches .devcontainer/ instance"
assert "diff -q .devcontainer/Dockerfile shield/skills/devcontainer/templates/Dockerfile.tmpl" \
  "template: Dockerfile.tmpl matches .devcontainer/ instance"
```

- [ ] **Step 2: Run the static check**

```bash
shield/tests/test-devcontainer-files.sh
```

Expected: all checks pass (including the new template-vs-instance diff checks).

- [ ] **Step 3: Run full suite**

```bash
make test
```

Expected: still 28/28 (existing test now has more sub-assertions).

- [ ] **Step 4: Commit**

```bash
git add shield/skills/devcontainer/templates/ shield/tests/test-devcontainer-files.sh
git commit -m "feat(shield): templates for devcontainer scaffolder

Source-of-truth shield-firewall.sh, Dockerfile.tmpl, postCreate.sh.tmpl.
Static check enforces they stay in sync with this repo's hand-written
.devcontainer/ instance (the dogfood)."
```

---

## Story 6: Devcontainer pre-flight gate

### Task 6.1: Write failing tests for the gate

**Files:**
- Create: `shield/scripts/test_devcontainer_gate.py`

- [ ] **Step 1: Write the test**

```python
# shield/scripts/test_devcontainer_gate.py
"""Tests for devcontainer_gate.py.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_devcontainer_gate.py -v`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from devcontainer_gate import Decision, decide  # type: ignore[import-not-found]


def _write_shield_json(repo: Path, required: str | None) -> None:
    payload: dict = {}
    if required is not None:
        payload["devcontainer"] = {"required": required}
    (repo / ".shield.json").write_text(json.dumps(payload))


def _mk_devcontainer(repo: Path) -> None:
    (repo / ".devcontainer").mkdir()
    (repo / ".devcontainer" / "devcontainer.json").write_text("{}")


def test_in_container_proceeds(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "ask")
    d = decide(repo=tmp_path, in_container=True, user_input=None)
    assert d == Decision.PROCEED


def test_no_devcontainer_dir_proceeds(tmp_path: Path) -> None:
    _write_shield_json(tmp_path, "ask")
    d = decide(repo=tmp_path, in_container=False, user_input=None)
    assert d == Decision.PROCEED


def test_required_false_proceeds(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "false")
    d = decide(repo=tmp_path, in_container=False, user_input=None)
    assert d == Decision.PROCEED


def test_required_true_refuses(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "true")
    d = decide(repo=tmp_path, in_container=False, user_input=None)
    assert d == Decision.REFUSE


@pytest.mark.parametrize("answer,expected_decision,expected_required_after", [
    ("y", Decision.REFUSE, "ask"),
    ("n", Decision.PROCEED, "ask"),
    ("always", Decision.REFUSE, "true"),
    ("never", Decision.PROCEED, "false"),
])
def test_ask_branch(tmp_path: Path, answer: str, expected_decision: Decision, expected_required_after: str) -> None:
    _mk_devcontainer(tmp_path)
    _write_shield_json(tmp_path, "ask")
    d = decide(repo=tmp_path, in_container=False, user_input=answer)
    assert d == expected_decision
    after = json.loads((tmp_path / ".shield.json").read_text())
    assert after["devcontainer"]["required"] == expected_required_after


def test_missing_shield_json_treated_as_ask(tmp_path: Path) -> None:
    _mk_devcontainer(tmp_path)
    # no .shield.json at all
    d = decide(repo=tmp_path, in_container=False, user_input="n")
    assert d == Decision.PROCEED
```

- [ ] **Step 2: Run — confirm fail**

```bash
cd shield/scripts && uv run --with pytest pytest test_devcontainer_gate.py -v
```

Expected: ModuleNotFoundError.

### Task 6.2: Implement the gate

**Files:**
- Create: `shield/scripts/devcontainer_gate.py`

- [ ] **Step 1: Write the implementation**

```python
# shield/scripts/devcontainer_gate.py
"""Pre-flight decision for /implement: should it run in this repo's devcontainer?

Public API:
    decide(repo, in_container, user_input) -> Decision

CLI entry point at the bottom: invoked from /implement's first step.

Read .shield.json -> devcontainer.required (default 'ask'). Compose decision
with SHIELD_IN_DEVCONTAINER env var (passed in as `in_container`) and an
optional user answer when the gate has to prompt.
"""
from __future__ import annotations

import enum
import json
import sys
from pathlib import Path


class Decision(enum.Enum):
    PROCEED = "proceed"
    REFUSE = "refuse"


def _read_required(repo: Path) -> str:
    cfg_path = repo / ".shield.json"
    if not cfg_path.exists():
        return "ask"
    try:
        data = json.loads(cfg_path.read_text())
    except json.JSONDecodeError:
        return "ask"
    return str(data.get("devcontainer", {}).get("required", "ask"))


def _set_required(repo: Path, value: str) -> None:
    cfg_path = repo / ".shield.json"
    data: dict = {}
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text())
        except json.JSONDecodeError:
            data = {}
    data.setdefault("devcontainer", {})["required"] = value
    cfg_path.write_text(json.dumps(data, indent=2) + "\n")


def decide(repo: Path, in_container: bool, user_input: str | None) -> Decision:
    repo = Path(repo)

    if in_container:
        return Decision.PROCEED

    if not (repo / ".devcontainer").is_dir():
        return Decision.PROCEED

    required = _read_required(repo)

    if required == "false":
        return Decision.PROCEED
    if required == "true":
        return Decision.REFUSE

    # required == 'ask'
    if user_input is None:
        # Caller is responsible for prompting; if they didn't, default to REFUSE
        # to be safe. Tests always supply a value.
        return Decision.REFUSE

    answer = user_input.strip().lower()
    if answer == "y":
        return Decision.REFUSE
    if answer == "n":
        return Decision.PROCEED
    if answer == "always":
        _set_required(repo, "true")
        return Decision.REFUSE
    if answer == "never":
        _set_required(repo, "false")
        return Decision.PROCEED
    # Unrecognized: default safe = refuse
    return Decision.REFUSE


def _cli() -> int:
    """Invoked from /implement's first step. Reads SHIELD_IN_DEVCONTAINER.

    Prompts interactively in the 'ask' branch when stdin is a TTY.
    Exits 0 on PROCEED, 1 on REFUSE.
    """
    import os

    repo = Path(os.environ.get("SHIELD_REPO", "."))
    in_container = os.environ.get("SHIELD_IN_DEVCONTAINER") == "true"
    required = _read_required(repo)

    user_input: str | None = None
    if (not in_container
            and (repo / ".devcontainer").is_dir()
            and required == "ask"):
        sys.stderr.write(
            "This repo has a Shield devcontainer.\n"
            "Run /implement inside it? [y / n / always / never]: "
        )
        sys.stderr.flush()
        user_input = sys.stdin.readline().strip()

    decision = decide(repo, in_container, user_input)

    if decision == Decision.REFUSE:
        sys.stderr.write(
            "Refusing to /implement on host.\n"
            "  VS Code:  reopen folder in container ('Reopen in Container').\n"
            "  CLI:      devcontainer up --workspace-folder . \\\n"
            "            && devcontainer exec --workspace-folder . bash\n"
            "            then run /implement inside.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
```

- [ ] **Step 2: Run — confirm pass**

```bash
cd shield/scripts && uv run --with pytest pytest test_devcontainer_gate.py -v
```

Expected: all 9 tests pass (5 parametrized + 4 standalone).

### Task 6.3: Wire into run-all.sh and commit

- [ ] **Step 1: Add to run-all.sh**

```bash
# --- 15. Devcontainer Gate ---
echo "15. Devcontainer Gate"
if command -v uv &>/dev/null; then
  run_test_verbose "devcontainer_gate tests pass" bash -c \
    "cd '$SHIELD_ROOT/scripts' && uv run --with pytest pytest test_devcontainer_gate.py -q 2>&1"
else
  echo "  ⚠ uv not installed, skipping gate tests"
fi
echo ""
```

- [ ] **Step 2: Run full suite**

```bash
make test
```

Expected: 28 → 29.

- [ ] **Step 3: Commit**

```bash
git add shield/scripts/devcontainer_gate.py shield/scripts/test_devcontainer_gate.py shield/tests/run-all.sh
git commit -m "feat(shield): /implement devcontainer pre-flight gate

Decides PROCEED vs REFUSE based on SHIELD_IN_DEVCONTAINER env var,
.devcontainer/ presence, and .shield.json devcontainer.required
(ask | true | false). 'ask' branch persists 'always'/'never' choices
to .shield.json. CLI entry point invoked from implement-feature
skill's Step 0."
```

---

## Story 7: `/shield init-devcontainer` command + SKILL

### Task 7.1: Create the command file

**Files:**
- Create: `shield/commands/init-devcontainer.md`

- [ ] **Step 1: Write the command**

```markdown
---
name: init-devcontainer
description: Scaffold .devcontainer/ for running /implement in isolation (filesystem + network egress)
---

# Init Devcontainer

Generate a Shield-managed devcontainer for this repo so `/implement` and other agent-driven commands run in a sandboxed environment.

## Usage

`/shield init-devcontainer`

## Behavior

Invoke the `shield:devcontainer-init` skill (see `shield/skills/devcontainer/SKILL.md`). The skill:

1. Detects the project's stack via `shield/scripts/detect_stack.py`.
2. Confirms the detected stacks with the user (add / correct / drop).
3. Composes `.devcontainer/devcontainer.json` from `shield/skills/devcontainer/feature-map.json` using `shield/scripts/compose_devcontainer.py`.
4. Copies `shield-firewall.sh`, `Dockerfile`, and a stack-filled `postCreate.sh` from `shield/skills/devcontainer/templates/`.
5. Updates `.shield.json` with a `devcontainer` block (`stacks_detected`, `required: "ask"`, `firewall_extra_allowlist: []`).
6. Prints next-step instructions: VS Code "Reopen in Container", or CLI `devcontainer up --workspace-folder .` followed by `claude /login` inside.

Idempotent: re-running diffs against existing `.devcontainer/` and asks before overwriting any file.

## See also

- Design spec: `docs/superpowers/specs/2026-05-18-devcontainer-implement-design.md`
- Threat model + security caveats: `shield/README.md` § Devcontainer
```

### Task 7.2: Create the SKILL

**Files:**
- Create: `shield/skills/devcontainer/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: devcontainer-init
description: Use when scaffolding a .devcontainer/ for Shield. Triggers on /shield init-devcontainer, "set up devcontainer", "isolate /implement".
---

# Devcontainer Init

Scaffold a per-repo `.devcontainer/` that runs `/implement` and other agent commands in filesystem + network egress isolation. Follows the design at `docs/superpowers/specs/2026-05-18-devcontainer-implement-design.md`.

## When to Use

- User runs `/shield init-devcontainer`.
- User asks to "set up a devcontainer" or "isolate /implement".

## When NOT to Use

- `.devcontainer/` already exists and matches what we'd produce → tell the user it's already set up.
- User wants cloud / Codespaces / CI launchers → out of scope for v1; suggest local devcontainer first.

## Step Skeleton

| Step | Action | Mandatory |
|------|--------|-----------|
| 1 | Detect stacks via `shield/scripts/detect_stack.py` | Yes |
| 2 | Confirm with user (add / drop / correct) | Yes |
| 3 | Compose `devcontainer.json` via `shield/scripts/compose_devcontainer.py` | Yes |
| 4 | Copy templates: `shield-firewall.sh`, `Dockerfile.tmpl`, fill `postCreate.sh.tmpl` | Yes |
| 5 | Diff against existing `.devcontainer/` if present; prompt before overwrite | Yes |
| 6 | Update `.shield.json` with `devcontainer` block | Yes |
| 7 | Print next-step instructions (VS Code / CLI) | Yes |

## Workflow

### 1. Detect

```bash
uv run --with-no-deps python3 -c \
  "from pathlib import Path; \
   import sys; sys.path.insert(0, 'shield/scripts'); \
   from detect_stack import detect_stack; \
   print(' '.join(detect_stack(Path('.'))))"
```

Output is a space-separated list of stack tags (e.g., `python node`).

### 2. Confirm with user

Show the detected stacks. Ask:

```
Detected: python, node
  [a] proceed with these
  [b] drop one or more
  [c] add a stack not detected
```

### 3. Compose devcontainer.json

```bash
uv run --with-no-deps python3 -c \
  "from pathlib import Path; \
   import sys, json; \
   sys.path.insert(0, 'shield/scripts'); \
   from compose_devcontainer import compose_devcontainer; \
   fm = Path('shield/skills/devcontainer/feature-map.json'); \
   cfg = compose_devcontainer(stacks=['python', 'node'], feature_map_path=fm); \
   print(json.dumps(cfg, indent=2))" > .devcontainer/devcontainer.json
```

Replace `['python', 'node']` with the confirmed-stack list.

### 4. Copy templates

```bash
mkdir -p .devcontainer
cp shield/skills/devcontainer/templates/shield-firewall.sh .devcontainer/shield-firewall.sh
cp shield/skills/devcontainer/templates/Dockerfile.tmpl    .devcontainer/Dockerfile
```

Fill `postCreate.sh` from `postCreate.sh.tmpl` by substituting `# {{HINTS}}` with each confirmed-stack's `post_create_hint` from `feature-map.json`:

```python
import json
from pathlib import Path

stacks = ["python", "node"]  # confirmed list
fm = json.loads(Path("shield/skills/devcontainer/feature-map.json").read_text())
hints = "\n".join(fm[s]["post_create_hint"] for s in stacks if s in fm)
tmpl = Path("shield/skills/devcontainer/templates/postCreate.sh.tmpl").read_text()
Path(".devcontainer/postCreate.sh").write_text(tmpl.replace("# {{HINTS}}", hints))
```

`chmod 0755 .devcontainer/postCreate.sh .devcontainer/shield-firewall.sh`.

### 5. Diff against existing

Before overwriting any file, `diff` the proposed new content against the existing file. If different, show the user the diff and ask: `[o]verwrite / [k]eep existing / [s]how diff again`.

### 6. Update .shield.json

```python
import json
from pathlib import Path

path = Path(".shield.json")
data = json.loads(path.read_text()) if path.exists() else {}
data["devcontainer"] = {
    "version": 1,
    "stacks_detected": stacks,
    "required": "ask",
    "firewall_extra_allowlist": [],
}
path.write_text(json.dumps(data, indent=2) + "\n")
```

### 7. Print next-step instructions

```
Devcontainer scaffolded.

Next:
  VS Code:  Cmd+Shift+P → "Dev Containers: Reopen in Container"
  CLI:      devcontainer up --workspace-folder .
            devcontainer exec --workspace-folder . bash

Then inside the container:
  claude /login    # one-time per project; creds persist in named volume

Security caveats — see shield/README.md § Devcontainer.
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping the diff before overwrite | Always diff and confirm; users will lose customizations otherwise |
| Naming the firewall script `init-firewall.sh` | Use `shield-firewall.sh` — claude-code#32113 will silently overwrite the upstream name |
| Hard-coding Feature versions instead of digests | Always use `@sha256:...` from `feature-map.json`; tag-only pins drift |
| Forgetting to update `.shield.json` | Without the `devcontainer` block, the gate (Story 8) defaults to "ask" forever |
```

### Task 7.3: Write the integration test

**Files:**
- Create: `shield/tests/test-init-devcontainer.sh`

- [ ] **Step 1: Write the test**

```bash
#!/usr/bin/env bash
# shield/tests/test-init-devcontainer.sh
# Integration test: simulate the skill steps against fixture repos.
# Tests the *mechanism* (composer + templates + .shield.json update),
# not the LLM execution of the skill.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0

assert() {
  if eval "$1" >/dev/null 2>&1; then
    echo "  ✓ $2"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $2"
    FAIL=$((FAIL + 1))
  fi
}

run_scaffolder() {
  local target="$1"
  shift
  local stacks=("$@")
  local stack_csv
  stack_csv=$(printf '"%s",' "${stacks[@]}")
  stack_csv="[${stack_csv%,}]"

  uv run --with-no-deps python3 - <<PY
import json, sys
from pathlib import Path
sys.path.insert(0, "shield/scripts")
from compose_devcontainer import compose_devcontainer
from detect_stack import detect_stack

target = Path("$target")
target.mkdir(parents=True, exist_ok=True)
(target / ".devcontainer").mkdir(exist_ok=True)

cfg = compose_devcontainer(
    stacks=${stack_csv},
    feature_map_path=Path("shield/skills/devcontainer/feature-map.json"),
)
(target / ".devcontainer" / "devcontainer.json").write_text(
    json.dumps(cfg, indent=2) + "\n"
)

import shutil
shutil.copy("shield/skills/devcontainer/templates/shield-firewall.sh",
            target / ".devcontainer" / "shield-firewall.sh")
shutil.copy("shield/skills/devcontainer/templates/Dockerfile.tmpl",
            target / ".devcontainer" / "Dockerfile")

fm = json.loads(Path("shield/skills/devcontainer/feature-map.json").read_text())
hints = "\n".join(fm[s]["post_create_hint"] for s in ${stack_csv} if s in fm)
tmpl = Path("shield/skills/devcontainer/templates/postCreate.sh.tmpl").read_text()
(target / ".devcontainer" / "postCreate.sh").write_text(
    tmpl.replace("# {{HINTS}}", hints)
)

shield_json = target / ".shield.json"
data = json.loads(shield_json.read_text()) if shield_json.exists() else {}
data["devcontainer"] = {
    "version": 1,
    "stacks_detected": ${stack_csv},
    "required": "ask",
    "firewall_extra_allowlist": [],
}
shield_json.write_text(json.dumps(data, indent=2) + "\n")
PY
}

echo "=== Devcontainer Scaffolder Integration ==="

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Fixture 1: python-only
PY_FIX="$TMPDIR/python-only"
mkdir -p "$PY_FIX"
echo "[project]" > "$PY_FIX/pyproject.toml"
run_scaffolder "$PY_FIX" python

assert "[ -f '$PY_FIX/.devcontainer/devcontainer.json' ]" "python-only: devcontainer.json created"
assert "grep -q '/python:' '$PY_FIX/.devcontainer/devcontainer.json'" "python-only: includes python feature"
assert "grep -q 'pypi.org' '$PY_FIX/.devcontainer/devcontainer.json'" "python-only: EXTRA_HOSTS includes pypi.org"
assert "grep -q 'uv sync' '$PY_FIX/.devcontainer/postCreate.sh'" "python-only: postCreate has uv sync hint"

# Fixture 2: polyglot python + node
POLY="$TMPDIR/polyglot"
mkdir -p "$POLY"
echo "[project]" > "$POLY/pyproject.toml"
echo "{}" > "$POLY/package.json"
run_scaffolder "$POLY" python node

assert "grep -q '/python:' '$POLY/.devcontainer/devcontainer.json'" "polyglot: python feature present"
assert "grep -q '/node:' '$POLY/.devcontainer/devcontainer.json'" "polyglot: node feature present"
assert "grep -q 'registry.npmjs.org' '$POLY/.devcontainer/devcontainer.json'" "polyglot: EXTRA_HOSTS includes npm"

# Fixture 3: terraform-only
TF="$TMPDIR/terraform-only"
mkdir -p "$TF"
echo "resource \"aws_vpc\" \"x\" {}" > "$TF/main.tf"
run_scaffolder "$TF" terraform

assert "grep -q '/terraform:' '$TF/.devcontainer/devcontainer.json'" "terraform-only: tf feature present"
assert "grep -q 'registry.terraform.io' '$TF/.devcontainer/devcontainer.json'" "terraform-only: EXTRA_HOSTS includes tf registry"

# Idempotency: re-run on python fixture
run_scaffolder "$PY_FIX" python
assert "[ \"$(cat "$PY_FIX/.shield.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["devcontainer"]["required"])')\" = ask ]" \
  "idempotent: .shield.json required field preserved"

# Stack with no feature-map entry: skipped with warning
NOMAP="$TMPDIR/no-map"
mkdir -p "$NOMAP"
echo "x" > "$NOMAP/Gemfile"
warning=$(uv run --with-no-deps python3 - <<'PY' 2>&1 1>/dev/null
import sys
from pathlib import Path
sys.path.insert(0, "shield/scripts")
from compose_devcontainer import compose_devcontainer
compose_devcontainer(stacks=["ruby"], feature_map_path=Path("shield/skills/devcontainer/feature-map.json"))
PY
)
assert "echo '$warning' | grep -qi 'ruby'" "unknown stack: warning emitted"

echo ""
echo "==========================="
TOTAL=$((PASS + FAIL))
echo "Results: $PASS/$TOTAL passed"
if [ "$FAIL" -gt 0 ]; then
  echo "FAILED: $FAIL test(s) failed"
  exit 1
fi
echo "ALL INIT-DEVCONTAINER TESTS PASSED"
```

- [ ] **Step 2: Make executable and run**

```bash
chmod 0755 shield/tests/test-init-devcontainer.sh
shield/tests/test-init-devcontainer.sh
```

Expected: all assertions pass.

### Task 7.4: Wire into run-all.sh and commit

- [ ] **Step 1: Add to run-all.sh**

```bash
# --- 16. Init Devcontainer Integration ---
echo "16. Init Devcontainer Integration"
if command -v uv &>/dev/null; then
  run_test_verbose "init-devcontainer scaffolds fixtures correctly" \
    "$SHIELD_ROOT/tests/test-init-devcontainer.sh"
else
  echo "  ⚠ uv not installed, skipping init-devcontainer integration"
fi
echo ""
```

- [ ] **Step 2: Run full suite**

```bash
make test
```

Expected: 29 → 30.

- [ ] **Step 3: Commit**

```bash
git add shield/commands/init-devcontainer.md \
        shield/skills/devcontainer/SKILL.md \
        shield/tests/test-init-devcontainer.sh \
        shield/tests/run-all.sh
git commit -m "feat(shield): /shield init-devcontainer command + skill

New command + skill that scaffolds .devcontainer/ from detected stacks.
Integration test asserts python-only, polyglot, terraform-only fixtures
produce correct devcontainer.json + postCreate.sh + .shield.json, that
re-runs are idempotent, and that unmapped stacks warn instead of crash."
```

---

## Story 8: Wire the gate into `implement-feature`

### Task 8.1: Modify implement-feature SKILL.md

**Files:**
- Modify: `shield/skills/general/implement-feature/SKILL.md`

- [ ] **Step 1: Insert a new Step 0 at the top of the workflow**

Open `shield/skills/general/implement-feature/SKILL.md`. Find the section starting `## Step Skeleton` (around line 33). Replace the line `| 1 | Load story from plan.json | skip if no plan context | No |` and the rows that follow up to step 8 with:

```markdown
| 0 | Devcontainer gate (skip if not in repo with `.devcontainer/`) | always | Yes |
| 1 | Load story from plan.json | skip if no plan context | No |
| 2 | Confirm acceptance criteria | always | Yes |
| 3 | Write failing test | always (TDD) | Yes |
| 4 | Implement to pass test | always | Yes |
| 5 | Per-step review | always | Yes |
| 6 | Commit + update AC status in plan.json | always | Yes |
| 7 | Repeat 3-6 for next AC | loop until all AC done | Yes |
| 8 | Update story status in plan.json | always | Yes |
```

Add a new sub-section directly after the Step Skeleton table:

```markdown
## Phase 0: Devcontainer Gate

Before any other work, run the pre-flight gate to ensure `/implement` runs in the right place:

```bash
SHIELD_REPO=. python3 shield/scripts/devcontainer_gate.py
```

Behavior:
- Inside a devcontainer (`SHIELD_IN_DEVCONTAINER=true`): proceeds silently.
- Outside, but no `.devcontainer/` in the repo: proceeds silently (no devcontainer set up).
- Outside, with `.devcontainer/` present:
  - If `.shield.json` `devcontainer.required = true`: refuses to start; prints reopen instructions; exits.
  - If `false`: proceeds.
  - If `ask` (default): prompts `[y/n/always/never]`. `y`/`always` refuses + instructs reopen; `n`/`never` proceeds.
- Exit code 1 means refuse — `/implement` must not continue.

This is the same logic implemented in `shield/scripts/devcontainer_gate.py` (covered by `test_devcontainer_gate.py`).
```

- [ ] **Step 2: Run the existing implement-feature e2e phase**

```bash
shield/tests/e2e/phases/implement.sh
```

Expected: still passes — the gate has no effect on a project without `.devcontainer/`.

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/implement-feature/SKILL.md
git commit -m "feat(shield): wire devcontainer gate into implement-feature

Adds Step 0 to the skill: invoke devcontainer_gate.py before loading
story. Backwards-compatible — gate is a no-op for repos without
.devcontainer/."
```

---

## Story 9: E2E phase test

### Task 9.1: Create the E2E phase

**Files:**
- Create: `shield/tests/e2e/phases/devcontainer.sh`

- [ ] **Step 1: Write the phase**

```bash
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
sys.path.insert(0, "$REPO_ROOT/shield/scripts")
from compose_devcontainer import compose_devcontainer

target = Path("$project_dir")
target.joinpath(".devcontainer").mkdir(exist_ok=True)
cfg = compose_devcontainer(
    stacks=["python"],
    feature_map_path=Path("$REPO_ROOT/shield/skills/devcontainer/feature-map.json"),
)
target.joinpath(".devcontainer/devcontainer.json").write_text(json.dumps(cfg, indent=2))
shutil.copy("$REPO_ROOT/shield/skills/devcontainer/templates/shield-firewall.sh",
            target / ".devcontainer/shield-firewall.sh")
shutil.copy("$REPO_ROOT/shield/skills/devcontainer/templates/Dockerfile.tmpl",
            target / ".devcontainer/Dockerfile")
fm = json.loads(Path("$REPO_ROOT/shield/skills/devcontainer/feature-map.json").read_text())
tmpl = Path("$REPO_ROOT/shield/skills/devcontainer/templates/postCreate.sh.tmpl").read_text()
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
```

- [ ] **Step 2: Smoke-test it locally (opt-in)**

```bash
# Without env var: phase should skip
shield/tests/e2e/phases/devcontainer.sh

# With env var: phase runs (slow — multiple minutes)
RUN_DEVCONTAINER_E2E=1 shield/tests/e2e/phases/devcontainer.sh
```

Both should complete without errors. The skipped run reports the skip; the enabled run reports PASS counts.

- [ ] **Step 3: Commit**

```bash
git add shield/tests/e2e/phases/devcontainer.sh
git commit -m "test(shield): E2E phase for devcontainer scaffolder

Gated by RUN_DEVCONTAINER_E2E=1. Builds + runs the scaffolded
.devcontainer/ on a python-api fixture, asserts claude works inside,
firewall is active, and a container-side commit reaches the host
bind-mount. CI default: skipped."
```

---

## Story 10: RED-GREEN skill verification

CLAUDE.md mandates RED-GREEN testing for new skills. Run this once; if gaps are found, fix them.

### Task 10.1: RED — baseline without the skill

- [ ] **Step 1: Dispatch a subagent without the new skill loaded**

Open a NEW Claude Code session (or run a subagent with a clean working directory not containing `shield/skills/devcontainer/`). Give it the prompt:

> "Set up isolated execution of `/implement` in this repo. Tell me exactly what files you'd create and what they'd contain."

Document the baseline output. Likely outcome: it produces a generic devcontainer (no firewall script, no named-volume, no #36907/#32113 mitigations). Save this output as `/tmp/red-baseline.md`.

### Task 10.2: GREEN — same task with the skill

- [ ] **Step 1: Dispatch a subagent WITH `shield/skills/devcontainer/SKILL.md` loaded**

Same prompt as RED. Document the output. Compare with `/tmp/red-baseline.md`.

Assertions to verify in the GREEN output:
- Mentions `shield-firewall.sh` (NOT `init-firewall.sh`)
- Mentions named volume `claude-config-${devcontainerId}` (NOT host bind-mount of `~/.claude`)
- Mentions `cap_add: NET_ADMIN/NET_RAW`
- References stacks detected from feature-map
- Mentions port 53 lock to 127.0.0.11

### Task 10.3: REFACTOR if needed

- [ ] **Step 1: If any assertion fails, update the skill**

Edit `shield/skills/devcontainer/SKILL.md` to make the missing point more salient. Re-run GREEN; iterate until all assertions pass.

No commit needed if no skill change is required. If the skill is updated, commit with:

```bash
git add shield/skills/devcontainer/SKILL.md
git commit -m "fix(shield): tighten devcontainer skill prose after RED-GREEN"
```

---

## Story 11: Docs + version bump

### Task 11.1: Extend `.shield.json` schema

**Files:**
- Modify: `shield/schemas/shield.schema.json`

- [ ] **Step 1: Find the top-level `properties` block and add a `devcontainer` entry**

Locate the `"properties": {` section of `shield/schemas/shield.schema.json`. Add (alphabetical position works fine):

```json
"devcontainer": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "version": { "type": "integer", "minimum": 1 },
    "stacks_detected": {
      "type": "array",
      "items": { "type": "string" }
    },
    "required": {
      "enum": ["ask", "true", "false"]
    },
    "firewall_extra_allowlist": {
      "type": "array",
      "items": { "type": "string", "format": "hostname" },
      "uniqueItems": true
    }
  }
}
```

- [ ] **Step 2: Verify the schema is valid JSON**

```bash
python3 -c "import json; json.load(open('shield/schemas/shield.schema.json'))"
```

### Task 11.2: Update README

**Files:**
- Modify: `shield/README.md`

- [ ] **Step 1: Add a "Devcontainer for /implement" section**

Append (or insert at the appropriate location) the following section to `shield/README.md`:

```markdown
## Devcontainer for `/implement`

`/implement` runs autonomously — it writes tests, runs builds, makes commits. To contain that blast radius and protect your Claude credentials, scaffold a project-local devcontainer:

```bash
/shield init-devcontainer
```

This produces `.devcontainer/{devcontainer.json,Dockerfile,shield-firewall.sh,postCreate.sh}` tuned to your detected stack. Reopen in VS Code ("Reopen in Container") or `devcontainer up --workspace-folder .` from the CLI. Run `claude /login` once inside the container — credentials persist in a named Docker volume keyed by `${devcontainerId}` and never touch your host's `~/.claude/`.

### What's contained

| Boundary | Mechanism |
|---|---|
| Filesystem | Bind-mount workspace only; no host `~/.claude`, `~/.ssh`, or cloud creds |
| Network egress | Default-deny outbound; allowlist for Anthropic API, GitHub CIDRs, your stack's package registries; DNS locked to Docker's resolver |
| Credentials | Per-project named Docker volume; host's `~/.claude` is unreachable |
| Privileges | Non-root `dev` user; sudoers scoped to the firewall script only |

### What's NOT contained

- **Tampered repo content.** The container limits damage from prompt injection and agent mistakes, not from a deliberately malicious `postCreateCommand` or test fixture. Treat checked-out PRs from untrusted contributors the same as any other untrusted code.
- **Container escape via kernel bug.** For threat models that require it, see the microVM upgrade path (gVisor / Firecracker / Edera) in the design spec.

### Customizing the allowlist

If your project needs an additional hostname (private mirror, internal API), add it to `.shield.json`:

```json
{
  "devcontainer": {
    "firewall_extra_allowlist": ["mirror.corp.example.com"]
  }
}
```

Then **rebuild** the container (VS Code: "Rebuild Container"; CLI: `devcontainer up --remove-existing-container`). Changes don't take effect until the container is rebuilt.

### Disabling the gate

If you want `/implement` to run on the host this time:
- One-shot: answer `n` at the gate prompt.
- Persistent: answer `never` (writes `devcontainer.required: "false"` to `.shield.json`), or set it manually.

### Footguns mitigated

| Issue | Mitigation |
|---|---|
| [claude-code#36907](https://github.com/anthropics/claude-code/issues/36907) (DNS exfiltration via port 53) | Firewall locks port 53 to Docker's `127.0.0.11` resolver |
| [claude-code#32113](https://github.com/anthropics/claude-code/issues/32113) (Feature overwrites `init-firewall.sh`) | Shield names its script `shield-firewall.sh` |
```

### Task 11.3: Bump marketplace version

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump shield version from 2.16.0 to 2.17.0**

```bash
python3 - <<'PY'
import json
from pathlib import Path
mp = Path(".claude-plugin/marketplace.json")
data = json.loads(mp.read_text())
for plug in data["plugins"]:
    if plug["name"] == "shield":
        plug["version"] = "2.17.0"
mp.write_text(json.dumps(data, indent=2) + "\n")
PY
```

- [ ] **Step 2: Verify**

```bash
python3 -c "import json; assert json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'] == '2.17.0'"
```

### Task 11.4: Run full suite and commit

- [ ] **Step 1: Run the full suite**

```bash
make test
```

Expected: 30/30 still passing.

- [ ] **Step 2: Commit**

```bash
git add shield/schemas/shield.schema.json shield/README.md .claude-plugin/marketplace.json
git commit -m "docs(shield): devcontainer section + schema + v2.17.0

- README: usage, threat model (contained / not contained), allowlist
  extension, mitigated footguns
- .shield.json schema: add 'devcontainer' block
- marketplace: bump shield to 2.17.0"
```

---

## Self-review checklist (post-write)

1. **Spec coverage.** Each spec section/requirement should have a task:
   - Goals 1-4 (isolation, egress, reproducibility, polyglot): Stories 1 (dogfood), 3 (feature map per-stack), 4 (composer), 5 (templates), 7 (scaffolder), 9 (E2E) ✓
   - Components 1-5 (init-devcontainer, detect_stack, feature-map, firewall, gate): Stories 7, 2, 3, 5, 6 respectively ✓
   - File layout (4 files in `.devcontainer/`): Stories 1, 5, 7 ✓
   - `.shield.json` block: Stories 7 (gain block), 11 (schema) ✓
   - Error handling table (Docker missing, build fail, no-login, firewall block, parallel, opt-out, no-feature-map, allowlist edits): Story 7 (warning + diff prompts), Story 11 (README troubleshooting) ✓
   - Testing (unit + integration + E2E + RED-GREEN): Stories 2/3/4/6 (unit), 7 (integration), 9 (E2E), 10 (RED-GREEN) ✓
2. **Placeholder scan.** Two tolerable placeholders: `<*_DIGEST>` in Tasks 1.3 and 3.3, with explicit instructions on how to fetch each — these are intentional (digest values change) and have a recipe. No "TODO" / "TBD" / vague "add error handling".
3. **Type consistency.** `detect_stack` returns `list[str]` in tests and implementation. `compose_devcontainer` parameter `stacks` consumes an iterable; tests use lists. `Decision` enum members (`PROCEED`, `REFUSE`) consistent across `decide()` and tests.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-18-devcontainer-implement.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints.

Which approach?
