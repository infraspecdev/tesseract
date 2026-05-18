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
