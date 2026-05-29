# TRD Template — 14-section canonical structure

This document defines the unified Technical Requirements Document (TRD) template that
`/plan` emits to `{output_dir}/{feature}/trd.md`. It replaces the previous
`plan-architecture.md` deliverable.

**Slug allow-list source of truth:** `shield/schema/trd-sections.yaml` — the eval and
`/plan-review` import it. **Do not** drift this template from that file: when adding,
removing, or renaming a section, update the YAML in the same commit.

## How `/plan` selects the right authoring guidance

The emitter detects the dominant domain from repo markers (see `shield/commands/plan.md`
§Domain detection) and surfaces the matching authoring guidance for each of the 14
sections:

- **Backend-only** (`pom.xml`, `pyproject.toml`, `package.json`, `go.mod`, …): use the
  *backend interpretation* paragraph under each section below.
- **Infra-only** (`*.tf`, `atmos.yaml`, `Chart.yaml`, `kustomization.yaml`): use the
  *infra interpretation*.
- **Mixed** (both detected, or `.shield.json` `plan.template_override == "mixed"`):
  emit `[backend]` and `[infra]` labeled subsections within each domain-divergent
  section (§4, §5, §6, §7, §11, §14 per `trd-sections.yaml` `domain_divergent`).
- **Manual override**: `.shield.json` `plan.template_override` ∈ `{backend, infra, mixed}`
  bypasses repo-marker detection.

## The `n/a — <reason>` escape

Any section may declare `n/a — <reason>` on a single line when it genuinely does not
apply. Typical uses:

- §4 Product Journey on pure-infra plans: `n/a — declarative state change, no runtime path`
- §11 LLD-link rows on infra plans until `/lld <component>` lands

**Vague TBDs and silent omissions are not allowed.** The validator rejects:
- A section header present with empty body
- A section body containing only `TBD`, `TODO`, `???`, or whitespace
- An `n/a` line without a `—` separator and reason

Worked examples appear under the relevant sections below.

## Anchor convention

Every emitted section header carries an explicit kebab-case anchor:

```markdown
## §4 Product Journey {#product-journey}
```

The anchor token MUST match the slug from `shield/schema/trd-sections.yaml` exactly.
The validator rejects headers missing the `{#…}` anchor or carrying a non-canonical slug.

---

## §1 Document Overview {#document-overview}

**Purpose:** One-paragraph orientation — what this TRD covers, who reads it, how it
relates to the linked PRD and any prior research.

**Backend interpretation:** Name the service or feature, the team that owns it, and
the user-facing capability it enables. Link the PRD (`./prd.md#…`) and the
implementation plan (`./plan.md`). Date and author the document.

**Infra interpretation:** Name the cloud-resource topology, the environment(s) it
targets (e.g., `prod-eu-west-1`, `staging-us-east-1`), and the operational outcome.
Link the PRD and the plan. Date and author.

---

## §2 Problem Statement {#problem-statement}

**Purpose:** One to two paragraphs naming the concrete pain or constraint that
motivates this work. Reference the user need from the PRD without restating it
verbatim (the plan-review duplication rule will flag verbatim copies).

**Backend interpretation:** What user request can't be served today? What latency,
correctness, or scaling property is the current system missing? Quote a metric or
log line where possible.

**Infra interpretation:** What capacity, blast-radius, cost, or compliance constraint
does the current topology fail to satisfy? Quote a Terraform plan diff, a cost graph,
or an incident postmortem where possible.

---

## §3 Objective & Scope {#objective-scope}

**Purpose:** One paragraph stating the intended outcome. Two bullet lists: **In scope**
(what this TRD addresses) and **Out of scope** (what it explicitly defers). Scope must
be tight — anything not listed is implicitly deferred.

**Backend interpretation:** Name the endpoint(s) added/modified, the data model
changes, and the integrations touched. Out-of-scope examples: schema migrations,
client UI changes, partner-facing API changes.

**Infra interpretation:** Name the modules, the cloud accounts/regions, and the
state-management changes. Out-of-scope examples: cross-region replication, IAM
policy refactors not strictly required, observability changes.

---

## §4 Product Journey {#product-journey}

**Purpose:** End-to-end path through the system that exercises the change.

**Backend interpretation:** Trace a representative user request from entry point
(API gateway, queue consumer, scheduler) through the service to its persistence
and downstream effects. Include trigger, inputs, transformations, outputs, and
observable side effects. A small sequence diagram or numbered step list is fine.

**Infra interpretation:** Describe the operator's path: how is the change applied
(`terraform apply` in which workspace), what new resources come into existence in
what order, what state file is updated, and how does an existing workload start
using the new resources? If the change is a pure declarative state shift with no
runtime path (e.g., adding an output, importing existing resources), use
`n/a — declarative state change, no runtime path`.

**Worked `n/a` example (infra):** `n/a — module adds an output value; no runtime path exists.`

---

## §5 Functional Requirements {#functional-requirements}

**Purpose:** Numbered list of testable behavior statements. Each item is a verifiable
fact, not an aspiration.

**Backend interpretation:** Behaviors of the service — request/response shapes,
validation rules, error semantics, business rules, idempotency guarantees. Example:
`F1. POST /users with a duplicate email returns 409 and does not create a record.`

**Infra interpretation:** Declared resource set and topology invariants. Example:
`F1. The eks_cluster module provisions one cluster per region with 3 control-plane
ENIs across distinct AZs.` State-shape facts count; pure procedural recipes don't.

---

## §6 Non-Functional Requirements {#non-functional-requirements}

**Purpose:** Performance, reliability, security, and operability targets — each one
measurable.

**Backend interpretation:** Latency (p50/p99), throughput, error budget, RPO/RTO for
stateful subsystems, authentication/authorization properties, audit-log shape. Avoid
unmeasurable adjectives ("fast", "secure", "scalable"); name a number.

**Infra interpretation:** Blast radius (which workloads share fate), RTO/RPO for
state restoration, IAM least-privilege properties, cost ceiling, compliance frame
(SOC2 control IDs, PCI scope), upgrade cadence (e.g., "patch within 30 days of CVE").

---

## §7 High-Level Design {#high-level-design}

**Purpose:** The shape of the solution — components, data flow, key contracts.
Detail belongs in `/lld` (when it lands); §7 stays at the "what fits where" level.

**Diagrams are mandatory and MUST be Mermaid** (rendered client-side by the HTML
shell), not ASCII art. Emit one fenced `mermaid` block per diagram. At minimum:

1. **Component / topology** (a `mermaid` `flowchart`): which service/module owns
   which responsibility, the ports/interfaces between them, and the persistence
   boundary.
2. **Core flow sequence** (a `mermaid` `sequenceDiagram`): the primary
   request/lifecycle path end-to-end, including failure/recovery transitions.
3. **Boundary diagram** (a `mermaid` `flowchart` with `subgraph` per zone): the
   region / network / residency / account boundaries and what crosses them.

A single richer topology diagram is the floor; prefer all three when the system
spans regions, async flows, or trust boundaries.

**Backend interpretation:** services, ports, sync-vs-async edges, event backbone,
canonical data store. **Infra interpretation:** module graph, provider composition,
VPC/account/region subgraphs, IAM/network boundaries.

**Anti-patterns:** Do NOT paste ASCII box-art (it renders as monospace text, not a
diagram). Do NOT paste >20-line code blocks (the plan-review implementation-manual
rule flags code blocks >20 lines unless §8 carries a rationale for why this exact
code shape was chosen). Mermaid source is not counted as a code block for that rule.

---

## §8 Alternatives Considered {#alternatives-considered}

**Purpose:** Numbered list of options that were weighed, with the reason each was
not chosen. At least one alternative must be a real option that almost won — pure
"do nothing" entries don't count.

**Backend interpretation:** Alternate architectures (eventing vs. polling, sync vs.
async, library vs. service, vendor X vs. Y, monolith vs. decomposed). Reason
addresses the §6 NFR targets explicitly.

**Infra interpretation:** Alternate topologies (single-VPC vs. multi-VPC, hub-and-spoke
vs. mesh, managed service vs. self-hosted, region pinning vs. multi-region). Reason
addresses cost, blast radius, compliance.

---

## §9 Cross-Cutting Concerns {#cross-cutting-concerns}

**Purpose:** Concerns that touch most of the system regardless of which domain leads:
security, observability, compliance, error handling, configuration, secrets, feature
flags.

**Backend interpretation:** AuthN/AuthZ flow, secret rotation, structured logging,
metrics emitted, traces, request IDs, feature flags, runtime config.

**Infra interpretation:** IAM policy ownership, KMS/secret manager wiring, audit log
shipping, drift detection, state-file encryption, change-window/maintenance posture.

---

## §10 Milestones {#milestones}

**Purpose:** The ship plan — milestones, exit criteria, DAG.

**Source of truth:** `plan.json` `milestones[]` is the **structured upstream**
and §10's body is **rendered** from it, not hand-written. The skill emits the
section by calling:

```bash
uv run shield/scripts/render_trd_section.py milestones <plan.json>
```

and injecting the marker-wrapped output verbatim under this heading. The bytes
between `<!-- BEGIN rendered:milestones … -->` and `<!-- END rendered:milestones -->`
are re-rendered every time `/plan` runs; `validate_trd.py` emits a
**`milestone_drift`** Critical error if the live region diverges from what the
renderer would produce now (mirrors gate 0c's stale-anchor strictness).

**Do not hand-edit the rendered region.** To change a milestone — its name,
outcome, exit criteria, or `depends_on` — edit `plan.json` `milestones[]` and
re-run `/plan`; the §10 body refreshes on the next emit.

**Per-milestone fields rendered (from `plan.json` `milestones[]`):** `outcome`
(headline), optional `description` (2–3 sentences of additional context — populate
it when the outcome alone is thin), `exit_criteria`, and a **Detailed design:** line
auto-built from `touches_lld[]` linking each component to its co-located
`lld-<component>.md` draft. You do not write these by hand — they render from the
sidecar; you control them by editing `plan.json`.

**Backend interpretation:** Phases like "service compiles", "feature flag default
off ships", "feature flag enabled in prod", "old code path removed". Exit criteria
tie back to §5 + §6.

**Infra interpretation:** Phases like "module compiles", "applied to staging",
"applied to one prod region", "applied to all regions", "old resources destroyed".
Exit criteria tie back to §5 + §6.

---

## §11 APIs Involved {#apis-involved}

**Purpose:** The external + internal interface surface.

**Backend interpretation:** HTTP/RPC contracts (path, method, request/response
schema), event payloads (topic, schema, key, ordering), database/cache interface
changes. One subsection per surface.

**Infra interpretation:** Cloud-provider API surface (which Terraform providers and
which resource types), inter-module interfaces (which module exports what to which
consumer), backend storage (S3 keys, DynamoDB table shapes for state).

**Mixed-domain example:** Emit `### [backend] HTTP API contracts` AND
`### [infra] Module interfaces & cloud-API surface` as two labeled subsections.

**Worked `n/a` example (infra w/o module exports):** `n/a — module is a root invocation; no exports.`

---

## §12 Open Questions {#open-questions}

**Purpose:** Numbered list of decisions that are deliberately deferred or genuinely
unknown. Each entry has a question and a target resolution checkpoint (a milestone
ID, a date, or "blocked on …").

**Backend interpretation:** Examples: choice of cache eviction policy pending load
test, retry budget pending downstream SLO confirmation.

**Infra interpretation:** Examples: choice of NAT gateway count pending egress
volume baseline, IAM boundary pending security-review sign-off.

**Worked `n/a` example:** A small, well-scoped TRD with no genuine unknowns may
write `n/a — no open questions at this scope`.

---

## §13 References {#references}

**Purpose:** Links to the PRD, prior research, related TRDs/LLDs, external standards,
ADRs.

**Backend interpretation:** Link the PRD (`./prd.md`), the research transcript
(`./research.md`), upstream API docs, RFC numbers.

**Infra interpretation:** Link the PRD, the research transcript, Terraform module
registry pages, AWS/GCP service-quota docs, ADRs for prior topology decisions.

**LLD references (derive from `plan.json`, do not hand-curate):** list every entry
in `lld_components[]`, each linked to its co-located draft `./lld-<name>.md`, with a
one-line lifecycle note: *"drafted by `/plan`; promoted to `docs/lld/<name>.md` by
`/implement` at milestone close."* When `lld_components[]` is empty, write
`n/a — no component LLDs at this scope`. This is what makes the TRD→LLD relationship
visible instead of a hand-written "to be authored" stub.

---

## §14 Rollback Strategy {#rollback-strategy}

**Purpose:** Concrete steps to undo the change, with a trigger statement.

**Backend interpretation:** Steps to revert the deploy (feature-flag flip, version
pin, DB migration reverse). Triggers are observable: error-rate over threshold for
N minutes, p99 latency over X, error-budget burn, data-quality alert.

**Infra interpretation:** Steps to undo the apply (`terraform destroy` of the new
module, or `terraform state rm` followed by deletion, or revert-PR + re-apply).
Triggers are observable: drift alert, cost overshoot, compliance scan failure,
oncall incident.

---

## Provenance stamp

The emitter writes a top-of-file HTML comment as the first line after frontmatter:

```html
<!-- generated by /plan v{shield-plugin-version} on {YYYY-MM-DD} -->
```

`{shield-plugin-version}` is read from `.claude-plugin/marketplace.json` (the shield
plugin entry's `version` field). The validator checks for this stamp's presence but
does not version-pin (older valid stamps from prior plugin versions are accepted).

## Atomic write

The emitter writes `trd.md.tmp` first, then renames to `trd.md` once the full
document is on disk. On any failure mid-write, it removes the `.tmp` file and
surfaces the error — never leaves a partial `trd.md` behind.

## Re-run behavior

When `/plan` is re-run in a folder that already contains `trd.md`, the new file
overwrites the old one. **Existing `plan-architecture.md` files are never modified
or deleted** — the cutover is forward-only; old folders remain readable. The
plan.json `last_aligned_with` field (when present per schema 1.3) is also
preserved/updated by `/implement`, not by `/plan` itself.
