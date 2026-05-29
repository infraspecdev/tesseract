# Backend LLD Template

This document is the canonical template for backend LLDs. The `/lld` command
(Path A — human invocation) and `/plan` (Path B — TRD-driven, M2 plan) both
generate documents conforming to this shape via the lld-docs skill.

**Slug allow-list:** [`shield/schema/lld-sections-backend.yaml`](../../../schema/lld-sections-backend.yaml) — 14 sections in canonical order, 2 promote-on-demand (§9 Configuration, §11 Security & privacy), 8 forced subsections under §12 Performance & scaling.

**Source sample:** The shape is pinned to [tesseract PR #43](https://github.com/infraspecdev/tesseract/pull/43) — `docs/superpowers/specs/2026-05-18-lld-sample.html` (Bytebite user-signup LLD).

---

## Header metadata (above §1)

Every backend LLD MUST carry this header block, immediately after the provenance
comment and before §1:

```markdown
**Feature:** `<feature-folder slug or "manual">`
**Owner:** `<git user.email>`
**Status:** `draft | review | promoted`
**Linked PRD:** `<relative path or "n/a">`
**Linked plans:** `[<relative path>, …]` (plural — one LLD ↔ many plans)
**Version:** `<semver, default 0.1.0>`
**Last updated:** `<YYYY-MM-DD>`
```

`Linked plans` is plural by design — the same LLD doc is referenced by multiple
milestones across one or more plans. §14 Changelog records each touch.

## Section template

### §1 Overview {#overview}

**Always on.** 1–3 paragraphs naming which epics / PRD milestones / plan
milestones this LLD serves. Bidirectional with TRD §10 Milestones. Establishes
the *what* and *which-plan-touched-this* — concrete, not vague.

**Backend authoring guidance:** Name the C4 Container or Component. State its
runtime shape (HTTP service, library, daemon). Link to the canonical service
directory in the repo.

`n/a — <reason>` is allowed only if the component is being introduced and its
runtime shape isn't yet defined; vague TBDs are rejected.

### §2 Scope & non-goals {#scope-and-non-goals}

**Always on.** Two lists: in-scope (what this LLD covers) and out-of-scope
(what intentionally isn't covered, with a one-line reason each).

### §3 Module layout {#module-layout}

**Always on.** File tree with `new` / `mod` / `unchanged` badges. Identifies
which directories and files belong to this component.

### §4 Data model {#data-model}

**Always on.** Tables (with column-level detail: name, type, nullable,
default, indices) + cache namespaces (Redis key patterns, TTL). For pure
stateless services, declare `n/a — stateless service, no persistent data model`.

### §5 API contracts {#api-contracts}

**Always on.** Per-endpoint sub-anchor: `{#api-<endpoint-slug>}`. For each
endpoint: HTTP verb + path, request shape, response shape, error responses.

### §6 Sequence flows {#sequence-flows}

**Always on.** Per-flow sub-anchor: `{#flow-<flow-name>}`. Mermaid sequence
diagrams covering the component's interactions with callers and downstream
services. One flow per significant user / system journey.

### §7 Error handling {#error-handling}

**Always on.** Error-code table + behavior matrix. Each error has a stable
identifier, an HTTP status (if applicable), and the documented behavior (retry?
surface to user? log-only?).

### §8 Concurrency & state {#concurrency-and-state}

**Always on.** Named race conditions and their resolutions. State transitions
(if the component owns state). For stateless components, declare
`n/a — stateless component, no concurrency-sensitive state` and list any
externalised state (e.g. distributed locks, idempotency keys).

### §9 Configuration {#configuration}

**Promote-on-demand.** Default render: collapsed `<details>` block. Lift (open
the block) when the component has user-tunable configuration. Document every
config value with: name, type, default, range, secret/non-secret, hot-reloadable.

### §10 Observability {#observability}

**Always on.** Three subsections: logs (structured fields), metrics (named
gauges / counters / histograms with units), traces (span names + meaningful
attributes).

### §11 Security & privacy {#security-and-privacy}

**Promote-on-demand.** Default render: collapsed. Lift when the component
handles user data, authentication, authorization, or PII. Subsections: AuthN
(how callers identify), AuthZ (what they can do), data classification, threat
model.

### §12 Performance & scaling {#performance-and-scaling}

**Always on. 8 forced subsections — each MUST be non-empty or carry
`n/a — <reason>`.** This is the strongest anti-format-drift mechanism in the
template: a fixture-based eval mechanically verifies all 8 are present.

#### §12.1 Load {#load}
Expected request rate, payload sizes, distribution (steady vs. spiky).

#### §12.2 SLO {#slo}
Target p50/p99 latency, availability target, error-rate budget.

#### §12.3 Bottleneck {#bottleneck}
Where the component is expected to be CPU-bound, IO-bound, memory-bound, or
network-bound. Justified, not guessed.

#### §12.4 Latency breakdown {#latency-breakdown}
Per-flow latency contributors: network RTT, DB query time, downstream RPC
time, internal CPU time. Numbers or `n/a — measured post-ship`.

#### §12.5 Capacity {#capacity}
Estimated headroom at peak load. CPU cores, memory, connection-pool sizing.

#### §12.6 Scale-out lever {#scale-out-lever}
How the component scales horizontally. Stateless replication vs. partition-by-X.
Any constraints on max-replicas.

#### §12.7 Caches {#caches}
Where caching exists (or doesn't); cache invalidation strategy; TTLs.

#### §12.8 Degradation {#degradation}
What graceful degradation looks like when an upstream / downstream fails:
which features turn off, what user sees, what the alert says.

### §13 Open questions {#open-questions}

**Always on.** Table: `Q# | Question | Options | Owner | Resolve-by`.
Empty table is acceptable when no open questions exist.

### §14 Changelog {#changelog}

**Always on.** Every edit ties to a story ID (or `"manual"` for Path A edits)
and the date. Format:

```markdown
| Touch | Date | Summary | Story IDs |
|---|---|---|---|
| M1 | 2026-05-30 | Initial draft via /plan | EPIC-1-S1 EPIC-1-S2 |
| manual | 2026-06-01 | Reverse-doc fill-in by ashwini | n/a |
```

## Escape pattern

Any section may carry `n/a — <reason>` when the section genuinely doesn't
apply to this component. Examples:

- §4 Data model on a pure stateless transformation library → `n/a — stateless library, no persistent state`
- §8 Concurrency on a CLI tool that exits before any reentrancy → `n/a — single-shot CLI, no concurrency surface`
- §12.4 Latency breakdown when first-version measurements aren't available → `n/a — measured post-ship; targets in §12.2 SLO`

**Vague TBDs are not allowed.** `TBD`, `TODO`, `to be determined`, etc. in
always-on sections cause the eval to fail.

## Anchor convention

Every section header carries an explicit `{#kebab-case-slug}` anchor matching
the `id` field in `shield/schema/lld-sections-backend.yaml`. Sub-anchors on §5
use the `api-` prefix; sub-anchors on §6 use the `flow-` prefix. Example:

```markdown
### §5 API contracts {#api-contracts}

#### POST /signup {#api-signup}
…

#### GET /users/:id {#api-get-user}
…
```
