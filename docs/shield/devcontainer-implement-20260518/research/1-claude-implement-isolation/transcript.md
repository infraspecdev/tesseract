# Research Transcript — Isolation for `/implement` (Claude Code)

**Date:** 2026-05-18
**Topic:** Recommended practice for isolating Claude Code's `/implement` work
**Mode:** Phase 1 auto-filled from active brainstorm; Phase 2 ran 3 parallel agents.

## Detected Context

### Stack
- Multi-plugin Claude Code marketplace (Python via `uv`, markdown plugin definitions, shell hooks) (confirmed) — *from CLAUDE.md + repo root*
- Shield plugin under `shield/` is the target of this design (confirmed) — *from brainstorm scope*

### Integrations
- Claude Code CLI (host today) (confirmed) — *from `/implement` skill definition*
- Project Management adapters (ClickUp/Jira, optional) (detected) — *from `shield/adapters/`*

### Compliance markers
- None detected in repo. The user surfaced regulated-environments as a downstream user concern, not as an active constraint. (manual)

### Deployment / rollout pattern
- N/A — this is a developer-tooling plugin marketplace; not a deployed service.

### Recent activity
- shield/ — active development of PRDs and PM integration (last several commits) (detected) — *git log*

### Past decisions / ADRs
- `docs/adr/0001-introduce-prd-layer.md` (detected) — *globbed from docs/adr/*

### Prior Shield artifacts
- None prior to this run.

## Product Context

### Problem
Run Shield's `/implement` (TDD-based feature work that executes tests, builds, package installs, and `git commit`s) inside an isolated environment so the agent cannot:
- Damage the host filesystem ("`rm -rf ~/`"-class incidents)
- Exfiltrate Anthropic OAuth/API credentials
- Run unsafe operations from a tampered repo (postCreate, malicious tests, supply-chain via Dev Container Features)

### Users
Developers using Shield's `/implement` on their own machines (local-only scope, per user decision).

### Evidence
Multiple public incidents (Replit prod DB wipe; Cursor+Claude Opus PocketOS 9-second wipe; recurring Claude Code `rm -rf ~/` reports; Prisma `--accept-data-loss`) — see findings.md.

### Success criteria
1. `/implement` runs end-to-end inside a devcontainer on a clean laptop.
2. Same behavior on macOS, Linux, (and Windows/WSL2 if free).
3. No host bind-mount of `~/.claude/.credentials.json` (revised after research).
4. Default-deny outbound; allowlist limited to what `/implement` actually needs.
5. First-run cost ≤ a few minutes; warm-rebuild ≤ 30s.

### Why now
Industry has converged on the pattern in late 2025–early 2026. Anthropic, Cursor, OpenAI Codex, Gemini CLI, and GitHub Copilot all ship sandbox guidance. Shield can adopt the canonical pattern rather than invent.

### Alternatives considered (from brainstorm)
- (A) Claude inside container — chosen
- (B) Host orchestrates, routes commands via `docker exec` — rejected (doesn't isolate the agent itself)
- (C) Hybrid — rejected for scope

## Technical Context

### Existing systems
- `/implement` command at `shield/commands/implement.md` invokes `shield:implement-feature` skill (`shield/skills/general/implement-feature/SKILL.md`), which does: load plan story → confirm AC → TDD loop (write failing test → implement → per-step review → commit → update `plan.json`) → final AC verification.
- Plan sidecar lives at `{output_dir}/{feature}/plan.json`.

### Constraints
- Local laptop only (no cloud / CI / Codespaces for this phase).
- Recipe portability — Dockerfile checked into the repo; no Shield-published image (yet).
- Keep simple — single config; minimize Shield-owned templates.

### Integration points
- VS Code Dev Containers extension (primary launcher).
- `devcontainer` CLI (secondary launcher).
- Git inside the container.
- `gh` CLI for PR opening.
- Project's own toolchain (uv, npm, go, etc.) via Dev Container Features + postCreate.

### Technical risks (pre-research)
- Credential exfiltration from a tampered `postCreateCommand` or compromised Dev Container Feature.
- Container escape.
- Drift across machines if image not pinned.

### Open Technical Questions (going into Phase 2)
1. What's the recommended pattern industry-wide for isolating AI coding agents?
2. How should credentials be delivered to an agent inside a container — host bind-mount, named volume, env, or short-lived broker?
3. What egress controls are realistic for `/implement` (what services does the agent actually need to reach)?
4. Are there documented incidents that should shape the threat model?
5. Is the devcontainer enough, or do we need a microVM tier for true adversarial isolation?

## External Findings (Phase 2)

See `findings.md` in this same folder. Three parallel agents (official sources, industry voices, community experience) returned consistent results.

### Top-line implications for the brainstorm

1. **Industry consensus on the "two-boundary model":** filesystem isolation AND network egress allowlisting are both required. Either alone is insufficient (Anthropic, Cursor, OpenAI all state this).
2. **Credentials go in a named Docker volume keyed by `${devcontainerId}`, not bind-mounted from host.** This contradicts the earlier brainstorm conclusion (which was leaning toward read-only mount of host `~/.claude/.credentials.json`). Anthropic's own reference devcontainer uses a per-project named volume; the agent logs in once inside the container, and creds never sit on the host as a mountable file readable by the agent.
3. **Anthropic publishes a canonical reference** at `anthropics/claude-code/.devcontainer/` — Dockerfile, `devcontainer.json`, and `init-firewall.sh` (iptables + ipset, default-deny OUTPUT, allowlist anthropic.com / npmjs / github CIDRs). Shield should diff against this rather than design from scratch.
4. **Run as non-root** (`remoteUser`). `--dangerously-skip-permissions` is gated to non-root precisely because the container is the safety net.
5. **Known footguns** in the reference: DNS port-53 unrestricted (#36907 — closed "not planned"), and the official Dev Container Feature silently overwrites `init-firewall.sh` (#32113). Shield should mitigate both.
6. **Trusted-code assumption** is universal. Containers reduce blast radius for mistakes and prompt injection. They are not a defense against deliberately malicious code (e.g., a PR that modifies `postCreateCommand`). Document this honestly.
7. **Per-task ephemerality + git worktrees** is the pattern emerging for parallel runs. Each `/implement` invocation gets its own worktree + container; state in `plan.json` is the persistence point. Defer this to a Phase 2 iteration of Shield.

## Decisions arising from research

| Decision | Pre-research | Post-research | Reason |
|---|---|---|---|
| Where do Claude creds live? | Bind-mount `~/.claude/.credentials.json` read-only from host | Named Docker volume per `${devcontainerId}` | Anthropic reference + Solberg + sbox all converge here; eliminates host-cred reach |
| Network policy | "defer to Phase 2" | Ship a default-deny iptables firewall from day 1 (allowlist: anthropic API, github, npm, pypi) | Egress is the highest-leverage control per Willison + Anthropic Engineering |
| Runtime user | non-root (assumed) | non-root, confirmed (`remoteUser: dev`) + don't run `claude --dangerously-skip-permissions` as root | Anthropic refuses to run YOLO mode as root |
| Constant layer (Layer 1) contents | Claude Code + shield + git | Same + a Shield-owned firewall script (avoid naming collision with Feature's `init-firewall.sh`) | Issue #32113 — Feature silently overwrites |
| Dev Container Feature pinning | Reference by name | Pin Features by OCI digest, not tag | Supply-chain risk + drift |
| Microvm tier | Not in scope | Not in scope, but document the upgrade path (gVisor / Firecracker / Edera) for adversarial threat models | Frazelle's "containers were never a top-level security boundary" still applies |

## Sources
See `findings.md` References section.
