---
name: kubernetes-cost-review
description: Use when reviewing Kubernetes manifests for cost optimization, resource right-sizing, or identifying over-provisioned workloads. Only triggers when K8s manifests are detected.
---

# Kubernetes Cost Review

## Overview

Cost analysis framework for Kubernetes workloads. Reviews resource requests and limits, scaling configuration, storage provisioning, and environment-specific sizing. Every workload should be right-sized for its actual needs, with scaling policies that prevent both waste and outages.

Only triggers when there is clear evidence of Kubernetes usage. When ambiguous, ask the user before proceeding.

## When to Use

- When reviewing K8s manifests for resource requests/limits optimization
- When auditing HPA/VPA configuration for scaling efficiency
- When checking storage provisioning (PVCs, storage classes)
- When evaluating workload sizing across environments (dev/staging/prod)
- When reviewing EKS-specific cost factors (Fargate, Spot, Karpenter)

## When NOT to Use

- For Terraform cost review — use `terraform-cost-review` instead
- For application performance tuning — this is resource cost, not performance
- When no K8s evidence is detected and user hasn't mentioned K8s
- For cluster-level cost (node sizing, reserved instances) without manifest context

## Cost Analysis Process

### Step 1: Resource Inventory

Scan all K8s manifests and inventory every workload. Categorize by:
- **Compute**: Deployments, StatefulSets, DaemonSets, Jobs, CronJobs
- **Storage**: PersistentVolumeClaims, StorageClasses
- **Scaling**: HPA, VPA, KEDA ScaledObjects
- **Networking**: Services (LoadBalancer type costs money), Ingress

See `sizing-reference.md` for workload sizing guidelines.

### Step 2: Configuration Analysis

For each workload, check:

- **Requests vs Limits** — Are requests set? Are limits set? Is the gap reasonable?
- **Over-provisioning** — Requests significantly higher than actual usage indicators
- **Under-provisioning** — Missing requests (scheduler can't bin-pack efficiently)
- **Scaling** — HPA/VPA configured for variable-load workloads?
- **Replica count** — Appropriate for the workload type and environment?
- **Storage sizing** — PVC sizes reasonable? Storage class appropriate?
- **Resource quotas** — Namespace quotas and limit ranges in place?

### Step 3: Environment-Specific Recommendations

For each workload, recommend resource values for dev, staging, and production. See `sizing-reference.md` for common sizing patterns.

## Common Cost Traps

| Trap | Typical Impact | Fix |
|------|---------------|-----|
| No resource requests set | Scheduler can't bin-pack, nodes under-utilized | Set requests based on actual usage patterns |
| Requests == Limits for all containers | No burst headroom, over-provisioned for steady state | Set requests to P50, limits to P99 of actual usage |
| No HPA on variable-load workloads | Paying for peak capacity 24/7 | Add HPA with CPU/memory or custom metrics |
| LoadBalancer Service per microservice | Cloud LB costs $15-25/month each | Use Ingress controller with single LB, or ClusterIP + Ingress |
| Over-sized PVCs | Paying for unused storage | Right-size PVCs, use volume expansion if supported |
| High replica count in dev/staging | Paying for prod-scale in non-prod | Use Kustomize overlays to reduce replicas per environment |
| CronJobs with large resource requests | Resources allocated for burst but idle most of the time | Right-size to actual job needs, consider spot/preemptible |

## Deprecated API Handling

If deprecated APIs with cost implications are found during the review (e.g., deprecated HPA autoscaling versions that affect scaling behavior), flag them in findings and recommend running `deprecation-check-and-upgrade` for full migration guidance.

## EKS-Specific Cost Checks

Only apply when EKS is detected:

| Check | Impact | Recommendation |
|-------|--------|---------------|
| Fargate vs managed nodes | Fargate premium ~20% over EC2 | Use Fargate for bursty/small workloads, managed nodes for steady-state |
| No Spot instances for fault-tolerant workloads | Paying full on-demand price | Add `karpenter.sh/capacity-type: spot` or node group Spot config |
| Karpenter consolidation not enabled | Nodes not bin-packed after scale-down | Enable consolidation policy in Karpenter provisioner |
| GP2 volumes instead of GP3 | GP2 is 20% more expensive with worse baseline | Use GP3 storage class |
| No cluster autoscaler or Karpenter | Nodes not scaling down when empty | Configure node scaling for non-prod environments |

## Supporting Files

- **`sizing-reference.md`** — Resource sizing guidelines by workload type, common patterns
- **`report-template.md`** — Full output format template for cost review reports
