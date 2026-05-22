---
name: init-devcontainer
description: Scaffold .devcontainer/ for running /implement in isolation (filesystem + network egress)
# No outputs declared: init-devcontainer writes .devcontainer/ files at the
# repo root and updates .shield.json — all outside the shield output_dir
# registry scope.
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
