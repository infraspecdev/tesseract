# Design — `/implement` in a devcontainer

**Status:** Draft (pending user review)
**Date:** 2026-05-18
**Author:** brainstorm session with @ashwinimanoj
**Related:** [Research findings](../../shield/devcontainer-implement-20260518/research/1-claude-implement-isolation/findings.md)

## Context

Shield's `/implement` command runs TDD-style feature implementation: it loads a story, confirms acceptance criteria, then loops — write failing test, implement, per-step review, commit, update `plan.json`. The agent executes real shell commands: `pytest`, `npm test`, `terraform apply`, `git commit`, package installs, postCreate scripts. Today it runs on the host as the developer's user, with full filesystem and credential access.

This design moves `/implement` into a devcontainer so it can run autonomously without endangering the host machine or the developer's Claude credentials.

### Goals

1. **Filesystem isolation** — `/implement` cannot touch any host path outside the workspace.
2. **Credential isolation** — host's `~/.claude/` is unreachable from inside the container.
3. **Network egress isolation** — default-deny outbound; only allowlisted endpoints reachable.
4. **Reproducibility** — same behavior on every developer's machine (macOS / Linux / WSL2).
5. **Polyglot support** — repo with Python + Node + Terraform composes correctly.
6. **Opt-in, not forced** — users who don't want the devcontainer path keep working as before.

### Non-goals (v1)

- Cloud / Codespaces / CI launchers. Local laptop only.
- A Shield-published container image. Recipe portability (Dockerfile in repo) instead.
- microVM tier (Firecracker / gVisor / Edera). Documented as future upgrade path.
- Adversarial-code containment. Container reduces blast radius for mistakes and prompt injection; not a defense against deliberately malicious repo content.
- Cross-container parallel `/implement` orchestration. Each devcontainer is its own session.

### Evidence base

Industry has converged on the pattern this design adopts: filesystem + network egress isolation, non-root user, credentials in a named volume keyed by `${devcontainerId}`, default-deny iptables firewall. Adopted by Anthropic's own `anthropics/claude-code/.devcontainer/` reference, Cursor, OpenAI Codex CLI, Google Gemini CLI, GitHub Copilot Coding Agent, and the community sandbox-wrapper ecosystem. Full sources in the findings.md (linked above).

Two specific footguns in the upstream Anthropic reference are mitigated explicitly: the DNS-tunnel bypass via unrestricted port 53 (issue #36907) and the Dev Container Feature that silently overwrites `init-firewall.sh` (issue #32113).

## Architecture

Three composition layers with one owner each, mapped to Dev Containers spec primitives:

| Layer | Owner | Mechanism | Contents |
|---|---|---|---|
| **1 — Constant** | Shield | `Dockerfile` | Claude Code CLI, git, gh, iptables, ipset, dnsutils, jq, sudo, `shield-firewall.sh`, non-root `dev` user |
| **2 — Stack** | Upstream (Microsoft/community) | Dev Container Features pinned by digest | Python, Node, Go, Terraform, JDK, etc. — only what the detected stack needs |
| **3 — Project** | The repo | `postCreate.sh` | `uv sync`, `npm install`, `go mod download`, etc. |

Two security boundaries (per the consensus in findings.md):

1. **Filesystem:** bind-mount only the workspace. No `~/.claude`, no `~/.ssh`, no cloud creds.
2. **Network:** default-deny outbound; allowlist Anthropic API + project's package registries + GitHub meta CIDRs; port 53 locked to Docker's internal resolver (127.0.0.11).

```
┌─────────────────────────────────────────────────────────────────┐
│  HOST                                                           │
│  - Repo workspace (bind-mounted rw into container)              │
│  - VS Code Dev Containers extension OR `devcontainer` CLI       │
│  - ~/.claude  ←─ never touched, never mounted                   │
└────┬────────────────────────────────────────────────────────────┘
     │ bind: workspace
     │ named volume: claude-config-${devcontainerId}
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  DEVCONTAINER  (non-root user `dev`, cap_add NET_ADMIN/NET_RAW) │
│  Layer 1 — Dockerfile:  claude, shield, git, gh,                │
│                         shield-firewall.sh                      │
│  Layer 2 — Features:    python | node | go | tf | jdk           │
│                         (all digest-pinned)                     │
│  Layer 3 — postCreate:  uv sync / npm install / ...             │
│                                                                 │
│  postStart: sudo /usr/local/bin/shield-firewall.sh              │
│             → default-deny OUTPUT                               │
│             → allowlist via ipset (per-stack)                   │
│             → port 53 only to 127.0.0.11                        │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. `/shield init-devcontainer` (new command)

Standalone command, separate from `/shield init`. Composable: a repo can run either, both, or neither.

Behavior:

1. Run stack detection (component 2).
2. Show detected stacks; ask confirm / correct / add.
3. Look up each confirmed stack in `feature-map.json` (component 3).
4. Compose four files in `.devcontainer/`. Idempotent — diff and prompt before overwrite.
5. Update `.shield.json` with a `devcontainer` block.
6. Print next-step instructions: "Reopen in container" (VS Code) or `devcontainer up && devcontainer exec bash` (CLI), then `claude /login`.

Re-runs are non-destructive: if `.devcontainer/` exists, show the diff and ask before any file is changed.

### 2. Stack detection — `shield/scripts/detect_stack.py`

Reuses the same markers as `shield/skills/general/research/repo-scan.md`.

| Marker | Stack tag |
|---|---|
| `pyproject.toml` or `requirements.txt` | `python` |
| `package.json` (+ `tsconfig.json` → `node-ts`) | `node` |
| `go.mod` | `go` |
| `pom.xml` or `build.gradle*` | `java` |
| `*.tf` files (recursive) | `terraform` |
| `Cargo.toml` | `rust` |
| `Gemfile` | `ruby` |
| `Dockerfile` or `docker-compose.yml` | `docker-in-docker` (flag) |
| `helm/` or `kustomization.yaml` | `kubernetes` (flag) |

Multi-stack repos return multiple tags by design.

### 3. Feature map — `shield/skills/devcontainer/feature-map.json`

Shield-owned data file. Maps each stack tag to its Dev Container Feature reference (pinned by `@sha256:` digest), default options, `postCreate` hint, and firewall allowlist entries.

```json
{
  "python": {
    "feature": "ghcr.io/devcontainers/features/python:1@sha256:<digest>",
    "default_options": { "version": "3.12" },
    "post_create_hint": "if [ -f pyproject.toml ]; then uv sync; elif [ -f requirements.txt ]; then pip install -r requirements.txt; fi",
    "firewall_allowlist": ["pypi.org", "files.pythonhosted.org"]
  },
  "node": {
    "feature": "ghcr.io/devcontainers/features/node:1@sha256:<digest>",
    "default_options": { "version": "lts" },
    "post_create_hint": "if [ -f pnpm-lock.yaml ]; then pnpm install; elif [ -f yarn.lock ]; then yarn install; else npm install; fi",
    "firewall_allowlist": ["registry.npmjs.org"]
  },
  "terraform": {
    "feature": "ghcr.io/devcontainers/features/terraform:1@sha256:<digest>",
    "default_options": {},
    "post_create_hint": "terraform init -input=false || true",
    "firewall_allowlist": ["registry.terraform.io", "releases.hashicorp.com"]
  }
}
```

**Strict digest pinning** is the rule, not the exception. Shield maintains digest updates (manually for v1; dependabot-style automation deferred).

### 4. Firewall script — `shield-firewall.sh`

Lives at `shield/skills/devcontainer/templates/shield-firewall.sh`. **Copied** into each user's `.devcontainer/` at scaffold time (not referenced as a Shield-shipped script). This makes the script auditable per repo, survives Shield uninstall, and follows the supply-chain hygiene the research recommends.

Named `shield-firewall.sh` deliberately (not `init-firewall.sh`) to avoid silent overwrite by the upstream `ghcr.io/anthropics/devcontainer-features/claude-code` Feature (issue #32113).

Outline:

```bash
#!/bin/bash
set -euo pipefail

# Default-deny
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Loopback always
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Established / related
iptables -A INPUT  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# DNS: only to Docker's embedded resolver (mitigates #36907)
iptables -A OUTPUT -p udp --dport 53 -d 127.0.0.11 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -d 127.0.0.11 -j ACCEPT

# Allowlist via ipset
ipset create allowlist hash:ip -exist
HOSTS="api.anthropic.com statsig.anthropic.com claude.ai console.anthropic.com ${EXTRA_HOSTS:-}"
for host in $HOSTS; do
  for ip in $(dig +short A "$host"); do
    ipset add allowlist "$ip" -exist
  done
done

# GitHub meta CIDRs
ipset create allowlist_cidr hash:net -exist
curl -s https://api.github.com/meta | jq -r '.git[]' | while read cidr; do
  ipset add allowlist_cidr "$cidr" -exist
done

iptables -A OUTPUT -m set --match-set allowlist     dst -j ACCEPT
iptables -A OUTPUT -m set --match-set allowlist_cidr dst -j ACCEPT
```

`$EXTRA_HOSTS` is composed in `devcontainer.json`'s `containerEnv` from the union of each detected stack's `firewall_allowlist` in `feature-map.json` and the user's `.shield.json` `devcontainer.firewall_extra_allowlist`.

### 5. `/implement` pre-flight gate — `shield/scripts/devcontainer_gate.py`

A Python helper (uv-runnable) called from the first step of `shield/skills/general/implement-feature/SKILL.md`. Single responsibility: decide whether `/implement` proceeds, exits, or prompts.

Decision logic:

```
Read .shield.json → devcontainer.required (default: "ask")
Read $SHIELD_IN_DEVCONTAINER (env var set by containerEnv)

if SHIELD_IN_DEVCONTAINER == "true":
    print "Running in Shield devcontainer."
    proceed

elif .devcontainer/ absent:
    proceed  # no devcontainer set up; nothing to gate

elif required == "false":
    proceed  # user persistently opted out

elif required == "true":
    refuse to start.
    print: "This repo requires /implement in a devcontainer.
            Reopen in VS Code via 'Reopen in Container', or run:
              devcontainer up && devcontainer exec bash
            then /implement."
    exit 1

else:  # required == "ask"
    prompt: "This repo has a Shield devcontainer.
             Run /implement inside it? [y / n / always / never]"
    y      → print reopen instructions; exit 1
    n      → proceed on host this run
    always → write required=true to .shield.json; exit 1
    never  → write required=false to .shield.json; proceed
```

Testable in isolation: feed in synthetic `.shield.json` + env-var combinations; assert the decision and any `.shield.json` mutation.

## File layout produced in the user's repo

```
<user-repo>/
├── .devcontainer/
│   ├── devcontainer.json   # composed from feature-map.json + detected stacks
│   ├── Dockerfile          # Layer 1 (constant) — see below
│   ├── shield-firewall.sh  # copied verbatim from Shield templates
│   └── postCreate.sh       # Layer 3 (project install hints)
├── .shield.json            # gains a `devcontainer` block (does not replace anything)
└── ...
```

### `devcontainer.json`

```json
{
  "name": "shield-implement",
  "build": { "dockerfile": "Dockerfile" },
  "features": {
    "ghcr.io/devcontainers/features/python:1@sha256:<digest>": { "version": "3.12" },
    "ghcr.io/devcontainers/features/github-cli:1@sha256:<digest>": {}
  },
  "remoteUser": "dev",
  "capAdd": ["NET_ADMIN", "NET_RAW"],
  "mounts": [
    "source=claude-config-${devcontainerId},target=/home/dev/.claude,type=volume"
  ],
  "containerEnv": {
    "SHIELD_IN_DEVCONTAINER": "true",
    "EXTRA_HOSTS": "pypi.org files.pythonhosted.org registry.npmjs.org"
  },
  "postCreateCommand": "bash .devcontainer/postCreate.sh",
  "postStartCommand": "sudo /usr/local/bin/shield-firewall.sh",
  "customizations": {
    "vscode": { "extensions": ["anthropic.claude-code"] }
  }
}
```

- Workspace bind-mount is the Dev Containers default — not overridden.
- No host `~/.claude` mount. Named volume keyed by `${devcontainerId}` keeps credentials inside the container's lifecycle.
- No secrets in the file. `claude /login` runs inside the container on first use and writes into the named volume.

### `Dockerfile`

```dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates iptables ipset dnsutils jq sudo \
    && rm -rf /var/lib/apt/lists/*

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -m -s /bin/bash --uid $USER_UID --gid $USER_GID $USERNAME \
    && echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/bin/shield-firewall.sh" \
       > /etc/sudoers.d/shield-firewall

# Pin to a concrete Claude Code version at implementation time (replace 2.x.x).
ARG CLAUDE_CODE_VERSION=2.x.x
RUN curl -fsSL https://claude.ai/install.sh | CLAUDE_VERSION=${CLAUDE_CODE_VERSION} bash

COPY shield-firewall.sh /usr/local/bin/shield-firewall.sh
RUN chmod 755 /usr/local/bin/shield-firewall.sh

USER dev
WORKDIR /workspaces
```

- `sudoers` scoped to only the firewall script. `dev` cannot escalate for anything else.
- Claude Code version pinned via build-arg.
- Firewall script copied at build time, not by a Feature (issue #32113 mitigation).

### `postCreate.sh`

Composed from the `post_create_hint` of each detected stack in `feature-map.json`. Idempotent — safe to re-run.

```bash
#!/bin/bash
set -euo pipefail
cd /workspaces/*

# python
if [ -f pyproject.toml ]; then
  uv sync
elif [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

# node
if [ -f package.json ]; then
  if [ -f pnpm-lock.yaml ]; then pnpm install
  elif [ -f yarn.lock ]; then yarn install
  else npm install; fi
fi

# (etc., per detected stacks)
```

### `.shield.json` update

```json
{
  "devcontainer": {
    "version": 1,
    "stacks_detected": ["python", "node"],
    "required": "ask",
    "firewall_extra_allowlist": []
  }
}
```

`firewall_extra_allowlist` is the user-controlled escape hatch — add a hostname here (e.g., a private package mirror) and re-running the firewall script picks it up.

## Error handling & edge cases

| Scenario | Behavior |
|---|---|
| Docker not running | Native Dev Containers extension / CLI surfaces the error. Scaffolder's next-step output mentions Docker Desktop / Colima / Podman as the runtime requirement. |
| Build fails (digest 404, apt mirror down) | User-surfaced build error. README troubleshooting documents the top failures and fixes. |
| No prior `claude /login` inside the container | First `claude` invocation prompts OAuth in a browser. One-time per project (volume keyed by `${devcontainerId}`). |
| Firewall blocks a legitimate endpoint | User edits `.shield.json` `devcontainer.firewall_extra_allowlist`, runs `sudo /usr/local/bin/shield-firewall.sh` (or rebuilds container) to re-apply. |
| Multiple parallel `/implement` in same repo | Each launcher (VS Code window, CLI invocation) has its own `${devcontainerId}` and its own credential volume. Workspace bind-mount is shared, so concurrent commits could race — pre-existing concern, not new. README note. |
| User explicitly opted out (`required: false`) | Pre-flight proceeds on host without prompt. |
| Detected stack has no entry in `feature-map.json` (e.g., new language) | Scaffolder prints a warning, skips that stack's Feature and `postCreate` hint, and continues with the others. Sets a TODO note in the generated `postCreate.sh` so the user knows. |
| User edits `firewall_extra_allowlist` after scaffold | The new hostnames don't take effect until the container is rebuilt (rebuilds re-render `EXTRA_HOSTS` from `.shield.json`). README documents: VS Code → "Rebuild Container", CLI → `devcontainer up --remove-existing-container`. |

### Explicitly out of scope

- Tampered `postCreateCommand` or Dockerfile in a checked-out PR. Container is blast-radius reduction, not adversarial containment. README states this plainly.
- Container escape via kernel bug. Future microVM upgrade path documented; v1 accepts container-grade isolation.

## Testing approach

### Unit (`shield/tests/unit/`)

- `test_detect_stack.py` — fixture directories exercising every marker combination; assert detected stack tags.
- `test_feature_map.py` — schema validation; every entry has feature + digest + post_create_hint + firewall_allowlist; digest format check.
- `test_devcontainer_compose.py` — given a stack list, assert the produced `devcontainer.json` references the right Features (with digests) and the right `EXTRA_HOSTS` value.
- `test_devcontainer_gate.py` — synthetic `.shield.json` + env-var combinations; assert decision and any `.shield.json` mutation.

### Integration (`shield/tests/integration/`)

- `test_init_devcontainer.sh` — run `/shield init-devcontainer` against fixture repos (python-only, polyglot python+node, terraform-only). Assert: four files appear with expected content, `.shield.json` gains the `devcontainer` block, re-run is idempotent.

### E2E (`shield/tests/e2e/phases/`)

- `devcontainer.sh` — gated behind `RUN_DEVCONTAINER_E2E=1` (slow; requires Docker). Runs `devcontainer up` on the python-api fixture with scaffolded `.devcontainer/`, execs `claude --version` inside to confirm install, runs a minimal `/implement`-equivalent, asserts a commit lands on the bind-mounted workspace.

### RED-GREEN skill test

Per the project's CLAUDE.md ("RED-GREEN testing is mandatory when creating or modifying any skill"):
- **RED:** dispatch a subagent without the new `shield/skills/devcontainer/SKILL.md` loaded; ask it to set up isolated execution for `/implement`. Document baseline.
- **GREEN:** dispatch with the skill loaded; assert it produces the file layout in this design.
- **REFACTOR:** any gaps → update the skill prose.

## Open questions / deferred

| Item | Status | Notes |
|---|---|---|
| Cloud / Codespaces / CI launchers | Deferred | Spec uses Dev Containers spec, which is portable; CI add-on can be a v2 |
| Published Shield base image | Deferred | Recipe portability sufficient for v1; if first-build time becomes painful, revisit |
| microVM tier (gVisor / Firecracker / Edera) | Deferred | Document upgrade path in README; no v1 work |
| Feature digest auto-update | Deferred | Manual digest bumps for v1; consider dependabot-style automation later |
| Cross-container parallel orchestration | Deferred | Each devcontainer is its own session; worktree-per-task pattern is a future iteration |

## Migration / reversibility

- **Roll forward:** `/shield init-devcontainer` is idempotent; safe to re-run.
- **Roll back:** delete `.devcontainer/`, run `docker volume rm claude-config-<devcontainerId>`, remove the `devcontainer` block from `.shield.json`. Repo is otherwise unchanged.
- **Upgrade to microVM:** swap the Dockerfile's `FROM` for a gVisor-runtime base, or move launch to Firecracker (Edera / Kata). Out of scope for v1 but the design's three-layer structure accommodates it cleanly.

## Summary

A Shield-scaffolded devcontainer that adopts the industry-standard two-boundary pattern (filesystem + network egress isolation), with strict digest pinning, a Shield-owned firewall script that fixes two known upstream footguns, and a non-disruptive opt-in path for `/implement`. Shield's surface stays small: one new command, one detection helper, one feature map, one firewall template, one pre-flight gate. Upstream Features own stack composition; the project owns its install steps.
