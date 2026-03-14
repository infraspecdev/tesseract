# Shield Agent Consolidation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge 10 agents from 2 plugins into 7 multi-mode agents in `shield/agents/`. Each merged agent has a shared persona and mode-specific checklists (plan review, infra-code review, app-code review).

**Architecture:** For each domain (security, cost, architecture, operations), combine the dev-workflow plan-review agent with the infra-review code-review agent into a single markdown file with mode sections. The dispatching skill tells the agent which mode to use. Plan-only agents (agile-coach, dx-engineer) and code-only agents (well-architected) move as-is with minor updates to match the new format.

**Tech Stack:** Markdown agent definitions

---

## File Structure

| New Agent File | Sources | Modes |
|---------------|---------|-------|
| `shield/agents/security-reviewer.md` | `infra-review/agents/security-reviewer.md` + `dev-workflow/agents/security-engineer-reviewer.md` | plan, infra-code, app-code (deferred) |
| `shield/agents/cost-reviewer.md` | `infra-review/agents/cost-reviewer.md` + `dev-workflow/agents/cost-finops-reviewer.md` | plan, infra-code |
| `shield/agents/architecture-reviewer.md` | `infra-review/agents/architecture-reviewer.md` + `dev-workflow/agents/cloud-architect-reviewer.md` (CA1-CA8) | plan, infra-code, app-code (deferred) |
| `shield/agents/operations-reviewer.md` | `infra-review/agents/operations-reviewer.md` + `dev-workflow/agents/cloud-architect-reviewer.md` (CA9-CA15) | plan, infra-code, app-code (deferred) |
| `shield/agents/well-architected-reviewer.md` | `infra-review/agents/well-architected-reviewer.md` | infra-code only |
| `shield/agents/agile-coach-reviewer.md` | `dev-workflow/agents/agile-coach-reviewer.md` | plan only |
| `shield/agents/dx-engineer-reviewer.md` | `dev-workflow/agents/dx-engineer-reviewer.md` | plan only |

## Chunk 1: Merged Multi-Mode Agents

### Task 1: Create security-reviewer agent

**Files:**
- Create: `shield/agents/security-reviewer.md`
- Source: `infra-review/agents/security-reviewer.md` (S1-S29) + `dev-workflow/agents/security-engineer-reviewer.md` (SE1-SE14)

- [ ] **Step 1: Read both source agent files**

Read `infra-review/agents/security-reviewer.md` and `dev-workflow/agents/security-engineer-reviewer.md` to get the full content of both.

- [ ] **Step 2: Create the merged agent**

Create `shield/agents/security-reviewer.md` with this structure:

```markdown
---
name: security-reviewer
description: |
  Multi-mode security reviewer. Dispatched for plan review (lightweight, 14 checks),
  infra-code review (deep, 29 checks), or app-code review (deferred to v2).
  Triggers on: auth, IAM, encryption, network, secrets, compliance, access control,
  firewall, TLS, testing, validation, security groups, NACLs, policies.
model: inherit
---

# Security Reviewer

## Persona

You are a **Senior Cloud Security Engineer** with deep expertise in AWS security,
CIS AWS Foundations Benchmark, and infrastructure-as-code security scanning. You
think like an attacker reviewing defensive code and plans. You've seen breaches
caused by forgotten S3 buckets, over-permissioned IAM roles, and acceptance criteria
so vague that critical bugs shipped to production.

## Trigger Keywords

auth, IAM, encryption, network, secrets, compliance, access control, firewall, TLS,
testing, validation, acceptance, edge cases, regression, rollback

## Weight

1.0 (Core persona)

## Modes

This agent operates in one of three modes. The dispatching skill specifies the mode.

---

## Mode: Plan Review

Use this mode when reviewing plan documents, architecture docs, or execution plans.
Lightweight checks focused on whether security concerns are addressed in the design.

### Plan Review Checklist (SE1-SE14)

[Copy the full SE1-SE14 table from dev-workflow/agents/security-engineer-reviewer.md]

### Plan Review Process

1. Read the full plan document
2. Identify all security-sensitive components (auth, data stores, network boundaries, secrets)
3. Map the plan's testing/validation strategy
4. Evaluate each check against what the plan describes (or fails to describe)
5. Grade each evaluation point A-F
6. Write recommendations for anything graded C or below

### Plan Review Output Format

[Copy the output format from dev-workflow/agents/security-engineer-reviewer.md]

---

## Mode: Infra-Code Review

Use this mode when reviewing Terraform/HCL code, Atmos components, or infrastructure
configurations. Deep checks with 29 checklist items.

### Infra-Code Review Checklist

[Copy the full S1-S29 checklists from infra-review/agents/security-reviewer.md,
including all subsections: IAM, Network, Encryption, Detective Controls, Secrets
Management, Data Protection, Incident Response, Checkov]

### Plan-Aware Review

[Copy the Plan-Aware Review section from infra-review/agents/security-reviewer.md]

### Codebase-Specific Patterns

[Copy the Codebase-Specific Patterns section from infra-review/agents/security-reviewer.md]

### Infra-Code Review Process

1. Read all `.tf` files in the component
2. Run through the security checklist
3. Note any Checkov skip annotations and evaluate their justification
4. Produce findings report

### Infra-Code Review Output Format

[Copy the output format from infra-review/agents/security-reviewer.md]

---

## Mode: App-Code Review (Deferred to v2)

This mode will cover OWASP Top 10, authentication flows, data exposure risks,
and application-level security patterns. Not yet implemented.
```

The actual file should contain the FULL checklist tables copied from both source files — not placeholders. Copy verbatim.

- [ ] **Step 3: Remove .gitkeep from agents/**

```bash
rm -f shield/agents/.gitkeep
```

- [ ] **Step 4: Commit**

```
feat: add multi-mode security reviewer agent

Merge infra-review security-reviewer (29 checks) and dev-workflow
security-engineer-reviewer (14 checks) into a single agent with
plan-review and infra-code-review modes.
```

### Task 2: Create cost-reviewer agent

**Files:**
- Create: `shield/agents/cost-reviewer.md`
- Source: `infra-review/agents/cost-reviewer.md` (C1-C24) + `dev-workflow/agents/cost-finops-reviewer.md` (CF1-CF10)

- [ ] **Step 1: Read both source agent files**

- [ ] **Step 2: Create the merged agent**

Same structure as Task 1 but for cost:
- Persona: Senior FinOps Engineer (merge both personas — they're nearly identical)
- Plan Review mode: CF1-CF10 from dev-workflow
- Infra-Code Review mode: C1-C24 from infra-review (including VPC Costs, General Patterns, Cost-Aware Design, Storage Lifecycle, Compute Efficiency, Data Transfer, Plan-Aware Review, Common Cost Traps)
- No App-Code Review mode (cost is infrastructure-focused)
- Weight: 0.7 for plan review, always for infra-code review
- Trigger keywords: cost, budget, scaling, resources, NAT, storage, compute, pricing, reserved, spot

Copy the FULL checklist tables from both source files.

- [ ] **Step 3: Commit**

```
feat: add multi-mode cost reviewer agent

Merge infra-review cost-reviewer (24 checks) and dev-workflow
cost-finops-reviewer (10 checks) into a single agent with
plan-review and infra-code-review modes.
```

### Task 3: Create architecture-reviewer agent

**Files:**
- Create: `shield/agents/architecture-reviewer.md`
- Source: `infra-review/agents/architecture-reviewer.md` (A1-A42) + `dev-workflow/agents/cloud-architect-reviewer.md` (CA1-CA8 only)

- [ ] **Step 1: Read both source agent files**

- [ ] **Step 2: Create the merged agent**

Important: the cloud-architect-reviewer has 15 checks (CA1-CA15), but CA9-CA15 (observability, monitoring, failure modes, backup, capacity, change management, on-call) belong in the operations-reviewer. Only CA1-CA8 go here.

- Persona: Senior Infrastructure Architect / Cloud Architect (merge both)
- Plan Review mode: CA1-CA8 from dev-workflow (service topology, scalability, HA, multi-region, network design, blast radius, service selection, environment parity)
- Infra-Code Review mode: A1-A42 from infra-review (including the full AWS Service Topology section with Context7 research guidance)
- App-Code Review: deferred to v2
- Weight: 1.0 (core)
- Trigger keywords: infrastructure, cloud, AWS, VPC, networking, multi-AZ, terraform, architecture, component, module, topology

Copy the FULL checklist tables from both source files. Include the entire AWS Service Topology reference table and research guidance from A26-A29.

- [ ] **Step 3: Commit**

```
feat: add multi-mode architecture reviewer agent

Merge infra-review architecture-reviewer (42 checks) and dev-workflow
cloud-architect-reviewer (CA1-CA8) into a single agent with
plan-review and infra-code-review modes.
```

### Task 4: Create operations-reviewer agent

**Files:**
- Create: `shield/agents/operations-reviewer.md`
- Source: `infra-review/agents/operations-reviewer.md` (O1-O31) + `dev-workflow/agents/cloud-architect-reviewer.md` (CA9-CA15 only)

- [ ] **Step 1: Read both source agent files**

- [ ] **Step 2: Create the merged agent**

CA9-CA15 from cloud-architect-reviewer map to operations:
- CA9 → Observability plan
- CA10 → Monitoring & alerting
- CA11 → Failure mode analysis
- CA12 → Backup & recovery
- CA13 → Capacity planning
- CA14 → Change management
- CA15 → On-call readiness

- Persona: Senior SRE focused on day-2 operations and production readiness
- Plan Review mode: CA9-CA15 (renumbered as OP1-OP7 for clarity)
- Infra-Code Review mode: O1-O31 from infra-review
- App-Code Review: deferred to v2
- Weight: 0.7 for plan review, always for infra-code review
- Trigger keywords: monitoring, observability, logging, alerting, SLA, runbook, on-call, backup, recovery, operations, production readiness

Copy the FULL checklist tables from both source files.

- [ ] **Step 3: Commit**

```
feat: add multi-mode operations reviewer agent

Merge infra-review operations-reviewer (31 checks) and dev-workflow
cloud-architect-reviewer (CA9-CA15) into a single agent with
plan-review and infra-code-review modes.
```

## Chunk 2: Single-Mode Agents

### Task 5: Create well-architected-reviewer agent

**Files:**
- Create: `shield/agents/well-architected-reviewer.md`
- Source: `infra-review/agents/well-architected-reviewer.md`

- [ ] **Step 1: Read source agent file**

- [ ] **Step 2: Create the agent**

Copy as-is from infra-review with minor updates:
- Update the frontmatter description to note it's infra-code only
- Add a `## Modes` section noting this agent only operates in infra-code review mode
- Keep all 6 pillar checklists and cross-pillar analysis intact

- [ ] **Step 3: Commit**

```
feat: add well-architected reviewer agent

Port from infra-review. Infra-code review only — covers all 6 AWS
Well-Architected Framework pillars with cross-pillar trade-off analysis.
```

### Task 6: Create agile-coach-reviewer agent

**Files:**
- Create: `shield/agents/agile-coach-reviewer.md`
- Source: `dev-workflow/agents/agile-coach-reviewer.md`

- [ ] **Step 1: Read source agent file**

- [ ] **Step 2: Create the agent**

Copy as-is from dev-workflow with minor updates:
- Update frontmatter description to note it's plan review only
- Add a `## Modes` section noting this agent only operates in plan review mode
- Keep all 10 evaluation points (AC1-AC10) and the mandatory story sections

- [ ] **Step 3: Commit**

```
feat: add agile coach reviewer agent

Port from dev-workflow. Plan review only — evaluates sprint-readiness,
story quality, sizing, dependency ordering, and AC testability.
```

### Task 7: Create dx-engineer-reviewer agent

**Files:**
- Create: `shield/agents/dx-engineer-reviewer.md`
- Source: `dev-workflow/agents/dx-engineer-reviewer.md`

- [ ] **Step 1: Read source agent file**

- [ ] **Step 2: Create the agent**

Copy as-is from dev-workflow with minor updates:
- Update frontmatter description to note it's plan review only
- Add a `## Modes` section noting this agent only operates in plan review mode
- Keep all 15 evaluation points (DX1-DX15)

- [ ] **Step 3: Commit**

```
feat: add DX engineer reviewer agent

Port from dev-workflow. Plan review only — evaluates plan clarity,
actionability, software architecture quality, and developer experience.
```
