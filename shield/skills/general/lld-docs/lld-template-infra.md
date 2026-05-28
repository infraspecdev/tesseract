# Infra LLD Template

This document is the canonical template for infra LLDs (terraform / k8s / helm).
The `/lld` command (Path A) and `/plan` (Path B — M2) both generate documents
conforming to this shape via the lld-docs skill.

**Slug allow-list:** [`shield/schema/lld-sections-infra.yaml`](../../../schema/lld-sections-infra.yaml) — 14 sections in canonical order, 2 promote-on-demand (§7 Security posture, §11 Migration & cutover), 6 forced subsections under §12 Validation.

The infra template diverges from the backend template in §3 (Module topology
vs. Module layout), §4 (Variable interface vs. Data model), §5 (State model
vs. API contracts), §6 (Drift / destructive-change surface vs. Sequence flows),
§8 (Cost surface — infra-only), §9 (Reliability & blast radius), §11 (Migration
& cutover, promote-on-demand), and §12 (Validation, 6 forced subsections).
§§ 1, 2, 10, 13, 14 are identical in intent to the backend template.

---

## Header metadata (above §1)

Same as the backend template. See `lld-template-backend.md` § "Header metadata".

## Section template

### §1 Overview {#overview}

**Always on.** Same intent as backend. **Infra authoring guidance:** Name the
terraform module / k8s controller / helm chart. State its scope (e.g.
"workspace-wide VPC", "per-environment service mesh"). Link to the canonical
module directory.

### §2 Scope & non-goals {#scope-and-non-goals}

**Always on.** Same as backend.

### §3 Module topology {#module-topology}

**Always on.** Two artifacts:
1. **File tree** with `new` / `mod` / `unchanged` badges (which `.tf` files,
   k8s manifests, or helm templates belong to this module).
2. **Resource dependency graph** — which terraform resources (or k8s objects)
   this module creates, and how they reference each other. Mermaid diagram
   acceptable; ASCII tree also fine.

### §4 Variable interface {#variable-interface}

**Always on.** Per-variable sub-anchor: `{#var-<variable-name>}`. For each input
variable:

| Field | Notes |
|---|---|
| Name | Snake_case per terraform convention |
| Type | terraform type expression (string, number, map(string), object({…})) |
| Default | Value or `(none)` |
| Required | yes / no |
| Validation | terraform `validation {}` block summary or "none" |
| Description | One sentence; what the variable controls |

Also document outputs (the module's outward surface) in the same shape, minus
Default/Required/Validation.

### §5 State model & lifecycle {#state-model-and-lifecycle}

**Always on.** What state this module creates (terraform state entries, k8s
custom resources, helm release records). Lifecycle considerations:
- `lifecycle { ignore_changes = […] }` blocks and why.
- `lifecycle { create_before_destroy = true }` cases and why.
- `moved { … }` blocks (refactoring from a previous resource path).
- `depends_on` declarations that aren't auto-inferred.

For k8s: which CRDs are created; controller reconciliation semantics; finalizers.

### §6 Drift / idempotency / destructive-change surface {#drift-and-destructive-surface}

**Always on.** Explicit destructive-change table — what triggers in-place vs.
replacement:

| Attribute / config | In-place change | Triggers replacement | Notes |
|---|---|---|---|
| `instance_type` | no | yes | EC2 — recreate |
| `tags` | yes | no | no downtime |
| … | | | |

Idempotency: confirm that running `terraform plan` after `apply` shows no
changes when source is unchanged.

Drift detection: how this module surfaces post-apply drift (e.g. tag drift
sweep, conftest cron, k8s controller's `Status` field reconciliation).

### §7 Security posture {#security-posture}

**Promote-on-demand.** Default collapsed. Lift for modules that touch IAM,
network, secrets, or any user-data-handling surface. Subsections: IAM (which
principals get which permissions); network (ingress/egress rules); secrets
(where they're stored, how rotated); encryption (at rest, in transit).

### §8 Cost surface {#cost-surface}

**Always on.** Per-environment cost contributors. Subsections:
- **Always-on resources:** the ones that bill 24/7 (NAT gateway, RDS, etc.)
- **Tiering decisions:** what's different between dev/staging/prod (instance
  classes, replica counts, retention policies).
- **Expensive toggles:** named variables that 10× the cost when enabled.

### §9 Reliability & blast radius {#reliability-and-blast-radius}

**Always on.** Multi-AZ posture (yes/no). Backup strategy (what's backed up;
RPO/RTO). Failure modes ("what happens if an AZ goes away?"). Blast-radius
estimate — what user-facing functionality breaks if this module's resources fail.

### §10 Observability & tagging {#observability-and-tagging}

**Always on.** Tagging convention (`env`, `service`, `owner`, etc.). Metric
surfaces (CloudWatch namespaces, prometheus scrape config). Log destinations.

### §11 Migration & cutover {#migration-and-cutover}

**Promote-on-demand.** Default collapsed. Lift when this module replaces a
prior resource set or requires non-trivial cutover steps. Subsections:
- `moved` blocks and the source-path → target-path mapping.
- State imports (`terraform import`) needed; for which resources.
- Blue-green / canary cutover steps (if the module hosts user traffic).

### §12 Validation {#validation}

**Always on. 6 forced subsections — each MUST be non-empty or carry
`n/a — <reason>`.**

#### §12.1 Plan invariants {#plan-invariants}
What the rendered `terraform plan` MUST and MUST NOT show. Anti-rules:
"no resource replacement"; "no deletions"; positive rules: "exactly one new
VPC".

#### §12.2 Policy checks {#policy-checks}
OPA / conftest / sentinel rules that gate `terraform plan` output before
`apply`. Name the policy files and the rules they enforce.

#### §12.3 Apply checks {#apply-checks}
Post-apply sanity checks: are the expected resources present? Tags consistent?
Outputs non-empty?

#### §12.4 Drift detection {#drift-detection}
How drift is detected ongoing — scheduled `terraform plan -refresh-only`,
config-management agent, controller reconciliation status.

#### §12.5 Smoke test {#smoke-test}
End-to-end functional check after apply — e.g. "issue an HTTPS request via
the new ALB and assert 200".

#### §12.6 Rollback verify {#rollback-verify}
How rollback is verified — does the rollback path leave the previous state
intact and observable?

### §13 Open questions {#open-questions}

**Always on.** Same as backend template.

### §14 Changelog {#changelog}

**Always on.** Same as backend template.

## Escape pattern

Same `n/a — <reason>` escape as the backend template. Vague TBDs rejected.

## Anchor convention

Same as the backend template. Sub-anchors on §4 use the `var-` prefix:

```markdown
### §4 Variable interface {#variable-interface}

#### `vpc_cidr` {#var-vpc-cidr}
…

#### `private_subnet_count` {#var-private-subnet-count}
…
```
