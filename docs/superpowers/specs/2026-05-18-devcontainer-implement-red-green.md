# RED-GREEN — `shield/skills/devcontainer/SKILL.md`

**Status:** GREEN — skill produces output a generic agent cannot.
**Date:** 2026-05-18
**Mandated by:** `CLAUDE.md` § "Skill Quality" — RED-GREEN testing required for new skills.

## Setup

Two subagents, same goal ("set up isolated execution of `/implement` for this repo"), different access:

- **RED** — forbidden from reading any devcontainer-related Shield files (SKILL.md, templates, scripts, spec, plan, `.devcontainer/`). Allowed to consult `CLAUDE.md`, `shield/skills/general/implement-feature/SKILL.md`, and the public Dev Containers spec.
- **GREEN** — read `shield/skills/devcontainer/SKILL.md`, `feature-map.json`, the three templates, and `detect_stack.py`/`compose_devcontainer.py`. Forbidden from reading `.devcontainer/*` directly (the result we're independently reproducing).

Both produced markdown design documents (no code execution).

## Grading rubric (from the plan, Story 10)

GREEN must mention:
1. `shield-firewall.sh` (NOT `init-firewall.sh`)
2. Named volume `claude-config-${devcontainerId}` (NOT host bind-mount of `~/.claude`)
3. `cap_add: NET_ADMIN/NET_RAW`
4. Stacks detected from `feature-map.json`
5. Port 53 lock to `127.0.0.11`

## Results

| Invariant | RED | GREEN |
|---|---|---|
| Named volume for `~/.claude` | ✗ — bind-mounts host `~/.claude` read-write | ✓ — `source=claude-config-${devcontainerId},...,type=volume` |
| Firewall script | ✗ — design has no firewall ("acknowledged gap") | ✓ — `shield-firewall.sh` (not `init-firewall.sh`) |
| `NET_ADMIN`/`NET_RAW` capability | ✗ — not declared | ✓ — `capAdd: ["NET_ADMIN", "NET_RAW"]` |
| Stack detection driving the Feature list | ✗ — generic, picks one base image per language | ✓ — `detect_stack` → `feature-map.json` lookup; this repo: `python`, `terraform` |
| Port 53 locked to `127.0.0.11` | ✗ — no DNS policy | ✓ — both UDP/TCP 53 only to `127.0.0.11` (cites claude-code#36907) |
| Feature digest pinning | ✗ — floating tag `python:3.12` | ✓ — all Features pinned `@sha256:...` from `feature-map.json` |
| `userdel vscode` UID-1000 mitigation | ✗ — not mentioned | ✓ — explicit, cited as Linux bind-mount fix |
| Claude Code as a Feature (not curl install) | ✗ — uses `postCreateCommand` with `pip install uv` etc.; doesn't address Claude Code install | ✓ — Anthropic `claude-code` Feature; cites the OOM rationale |
| Issue references | ✗ — none | ✓ — both #36907 (DNS tunneling) and #32113 (Feature overwrite naming) |

**5/5 plan-mandated invariants present in GREEN. 0/5 in RED.**

## What RED got partially right (and where it stopped)

- Recognized that Dev Containers is the right primitive.
- Used a non-root user (but `vscode`, not `dev`).
- Suggested an allowlist *if it could enforce it* — but admitted Docker bridge default-allow defeats this without a Compose-level network policy.
- Acknowledged its design left network exfiltration unblocked.

These concessions are honest and useful. They show the floor an agent reaches without Shield's skill: a basic Dev Containers setup with no defense-in-depth around the credential or network surface.

## What the skill contributes (above the RED floor)

1. **Per-stack composition** — GREEN correctly identified that this polyglot repo needs python + terraform Features, and assembled the firewall allowlist (`pypi.org`, `files.pythonhosted.org`, `astral.sh`, `registry.terraform.io`, `releases.hashicorp.com`) by union over those stacks. RED would have either picked one base image or installed everything inline.
2. **Concrete, current footgun mitigations** — Both #36907 and #32113 surfaced verbatim in GREEN's output. RED, working from public Dev Containers docs only, has no path to know about these.
3. **Threat-model coherence** — GREEN's design has no host bind-mount of credentials (the explicit policy from the design spec); RED defaulted to bind-mounting `~/.claude` because that's the natural Dev Containers idiom.
4. **Composer + templates as one design** — GREEN cited `compose_devcontainer.py:ANTHROPIC_CLAUDE_CODE_FEATURE` for the constant layer; RED would not have made the Anthropic Feature unconditional.

## Refactor needed?

**No.** GREEN's output is sound on all rubric points and on adjacent quality (stack-specific allowlist assembly, Common-Mistakes references, idempotency / diff-before-overwrite). The SKILL.md as it stands at commit `f39cedc` (the `--with-no-deps` fix) produces correct, defensible output.

## Reproducing

Two `Agent` dispatches (general-purpose, sonnet), same working directory (`.claude/worktrees/shield-devcontainer-implement`), the prompts above. ~45s for RED, ~85s for GREEN. Full transcripts in the session log preceding this file.
