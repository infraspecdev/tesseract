# Shield

Unified SDLC plugin for Claude Code — research, planning, PM integration, implementation, and continuous review with multi-domain support and specialist agents.

## Installation

```bash
/plugin install shield@tesseract
/shield init
```

## Commands

| Command | Description |
|---|---|
| `/shield init` | Initialise `.shield.json` for a new project |
| `/shield research` | Capture product + tech context for a new feature |
| `/shield prd` | Author a new PRD |
| `/shield plan` | Generate architecture / ADR docs and an execution plan |
| `/shield implement` | Start TDD-based feature implementation with progress tracking |
| `/shield review` | Run comprehensive code review |
| `/shield pm-sync` | Sync plan stories to your PM tool |

## Devcontainer for `/implement`

`/implement` runs autonomously — it writes tests, runs builds, makes commits. To contain that blast radius and protect your Claude credentials, scaffold a project-local devcontainer.

### Prerequisites

You need two things on your host machine: a container runtime and a launcher.

**1. Container runtime (one of):**

| Platform | Runtime | Install |
|---|---|---|
| macOS | Docker Desktop | https://www.docker.com/products/docker-desktop — or `brew install --cask docker` |
| macOS (alternative, lighter) | Colima + Docker CLI | `brew install colima docker` then `colima start` |
| Linux | Docker Engine | https://docs.docker.com/engine/install/ |
| Linux (rootless alternative) | Podman | `apt install podman` / `dnf install podman` |
| Windows | Docker Desktop (WSL2 backend) | https://www.docker.com/products/docker-desktop |

Verify it's running: `docker info` should print engine info without errors.

**2. Launcher (one of):**

| Launcher | Best for | Install |
|---|---|---|
| **VS Code + Dev Containers extension** | Daily use; "Reopen in Container" UI flow | Install [VS Code](https://code.visualstudio.com/), then add the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) (`ms-vscode-remote.remote-containers`). No separate CLI needed — the extension bundles its own. |
| **`@devcontainers/cli`** | Headless / scripted / CI use | Requires Node.js. Install: `npm install -g @devcontainers/cli`. Verify: `devcontainer --version`. |

You can install both — they coexist.

### First run

```bash
# 1. Scaffold .devcontainer/ for this repo
/shield init-devcontainer
```

Shield detects your stack (Python, Node, Go, Java, Terraform — polyglot is fine) and writes four files: `.devcontainer/devcontainer.json`, `.devcontainer/Dockerfile`, `.devcontainer/shield-firewall.sh`, `.devcontainer/postCreate.sh`. It also adds a `devcontainer` block to `.shield.json`.

```bash
# 2. Open the project in the container
```

- **VS Code:** Command Palette (Cmd/Ctrl + Shift + P) → "Dev Containers: Reopen in Container". First build takes ~3–5 minutes (image build + Features install + project deps). Subsequent opens are fast.
- **CLI:** `devcontainer up --workspace-folder .` then `devcontainer exec --workspace-folder . bash` to enter.

```bash
# 3. Inside the container, log into Claude (one-time per project)
claude /login
```

This stores OAuth credentials in a named Docker volume (`claude-config-${devcontainerId}`) that's scoped to this project. The host's `~/.claude/` is never touched. The volume persists across container rebuilds — you won't be asked to log in again unless the volume is deleted.

```bash
# 4. Run /implement as usual
/implement EPIC-1-S1   # or any story / feature description
```

The container's firewall is active (default-deny outbound + allowlist), `claude` is installed via the Anthropic Dev Container Feature, and the workspace is bind-mounted so commits land on your host repo.

### Troubleshooting first run

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Runtime not started | Start Docker Desktop / Colima / Podman service. Verify with `docker info`. |
| `Path '<owner>/<feature>:1' ... failed validation` / `Could not resolve Feature manifest` | Feature ref uses `name:tag@sha256:digest` (rejected by Dev Containers CLI) | Use the digest alone — `name@sha256:digest`, no `:tag`. Shield's scaffolder emits this format; if you've hand-edited `.devcontainer/devcontainer.json`, strip the `:1` (or other tag) from each `features` key. |
| `devcontainer: command not found` | CLI not installed (only matters if you're using the CLI flow) | `npm install -g @devcontainers/cli`. VS Code users don't need this. |
| Build fails on Anthropic Feature pull | GHCR rate-limit or network issue | Retry. If persistent, log into ghcr.io: `docker login ghcr.io`. |
| `groupadd: GID '1000' already exists` | Base image changed and the `userdel vscode` mitigation regressed | Rebuild image from scratch: VS Code → "Rebuild Container Without Cache"; CLI → `devcontainer up --remove-existing-container`. |
| `claude --version` fails inside container | The Anthropic Feature didn't install; check `postStartCommand` logs in VS Code's "Dev Containers" output panel |
| Firewall blocks a legitimate hostname (e.g., a private package mirror) | Hostname not in the allowlist | See [Customizing the allowlist](#customizing-the-allowlist) below. |
| `fatal: not a git repository: .../.git/worktrees/<name>` inside the container | You scaffolded the devcontainer **inside a git worktree** (not a normal checkout). The worktree's `.git` file points to metadata at a host path that isn't bind-mounted. | Use VS Code's "Reopen in Container" — its Dev Containers extension passes `--mount-workspace-git-root` automatically, which handles this. With the bare CLI, pass the flag yourself: `devcontainer up --workspace-folder . --mount-workspace-git-root`. Or, simplest: scaffold the devcontainer in the main repo checkout, not inside a worktree — devcontainers and worktrees serve overlapping isolation goals and rarely need to be combined. |

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

Then re-run `/shield init-devcontainer` to regenerate `.devcontainer/devcontainer.json` with the new host in `EXTRA_HOSTS`, and **rebuild** the container (VS Code: "Rebuild Container"; CLI: `devcontainer up --remove-existing-container`). The new hostname is read from `.shield.json` only at scaffold time — a plain rebuild reuses the existing `EXTRA_HOSTS` value.

### Disabling the gate

If you want `/implement` to run on the host this time:
- One-shot: answer `n` at the gate prompt.
- Persistent: answer `never` (writes `devcontainer.required: "false"` to `.shield.json`), or set it manually.

### Footguns mitigated

| Issue | Mitigation |
|---|---|
| [claude-code#36907](https://github.com/anthropics/claude-code/issues/36907) (DNS exfiltration via port 53) | Firewall locks port 53 to Docker's `127.0.0.11` resolver |
| [claude-code#32113](https://github.com/anthropics/claude-code/issues/32113) (Feature overwrites `init-firewall.sh`) | Shield names its script `shield-firewall.sh` |
