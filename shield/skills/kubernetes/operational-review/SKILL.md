---
name: kubernetes-operational-review
description: Use when reviewing Kubernetes workloads for production readiness, checking probes, PDBs, rollout strategy, or observability. Only triggers when K8s manifests are detected.
---

# Kubernetes Operational Review

## Overview

Production readiness review for Kubernetes workloads. Checks that deployments are resilient, observable, and operable — covering health probes, disruption budgets, rollout strategy, observability, and graceful shutdown. A workload that passes security and cost review can still cause outages if it lacks proper probes or PDBs.

Only triggers when there is clear evidence of Kubernetes usage. When ambiguous, ask the user before proceeding.

## When to Use

- When reviewing K8s workloads for production readiness
- When auditing health probe configuration (liveness, readiness, startup)
- When checking PodDisruptionBudgets and rollout strategy
- When evaluating observability setup (logging, metrics, tracing)
- When reviewing graceful shutdown and dependency management

## When NOT to Use

- For Terraform operational review — use the operations-reviewer agent in infra-code mode
- For security concerns — use `kubernetes-security-audit`
- For cost concerns — use `kubernetes-cost-review`
- When no K8s evidence is detected and user hasn't mentioned K8s

## Workflow

1. **Detect K8s presence**: Confirm K8s manifests exist. If ambiguous, ask user.
2. **Collect scope**: Identify all workloads (Deployments, StatefulSets, DaemonSets, Jobs, CronJobs).
3. **Probe audit**: Check every workload for liveness, readiness, and startup probes. See `ops-checklist.md` for detailed checks.
4. **Disruption audit**: Verify PDBs exist for production workloads, check minAvailable/maxUnavailable values.
5. **Rollout audit**: Check rolling update strategy, maxSurge, maxUnavailable configuration.
6. **Topology audit**: Review topology spread constraints, pod anti-affinity for HA.
7. **Observability audit**: Check for monitoring annotations, logging sidecars, tracing config.
8. **Shutdown audit**: Verify preStop hooks, terminationGracePeriodSeconds, SIGTERM handling.
9. **Dependency audit**: Check init containers, dependency ordering, ConfigMap/Secret reload strategy.
10. **EKS-specific checks** (if EKS detected): ALB ingress annotations, CloudWatch Container Insights, EBS CSI driver, ExternalDNS.
11. **Deprecation flag**: If deprecated APIs are found, flag them and recommend `deprecation-check-and-upgrade`.
12. **Produce report**: Use the template from `templates.md`.

See `ops-checklist.md` for detailed check tables.

## Critical Checks

- Deployments/StatefulSets without readiness probes (traffic sent to unready pods)
- Identical liveness and readiness probes (liveness should be simpler, checking process health, not dependencies)
- No PodDisruptionBudget for multi-replica workloads
- `terminationGracePeriodSeconds` shorter than actual shutdown time
- Missing topology spread or anti-affinity for HA workloads
- No preStop hook when the application needs graceful drain time

## Common Mistakes

| Mistake | Why It Happens | Correct Approach |
|---------|---------------|-----------------|
| Requiring probes on CronJobs | CronJobs are short-lived batch | Probes are for long-running workloads; CronJobs use `activeDeadlineSeconds` |
| Flagging missing PDB on single-replica deployments | PDBs need multiple replicas to be useful | PDB is relevant for workloads with >1 replica |
| Setting liveness probe = readiness probe | Copy-paste convenience | Liveness should check process health; readiness should check ability to serve |
| Ignoring startup probes for slow-starting apps | Liveness probe kills the pod before it's ready | Use startup probe with generous timeout for apps that take >30s to start |
| Not checking terminationGracePeriodSeconds | Default 30s assumed sufficient | Must match actual graceful shutdown time (e.g., connection draining) |
| Flagging missing anti-affinity on dev | Dev typically runs 1 replica | Anti-affinity is for multi-replica production workloads |

## Supporting Files

- `ops-checklist.md` — Detailed check tables for probes, PDBs, rollout, topology, observability, shutdown, and dependencies
- `templates.md` — Report output template with readiness scoring
