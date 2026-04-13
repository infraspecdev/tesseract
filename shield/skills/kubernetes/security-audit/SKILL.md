---
name: kubernetes-security-audit
description: Use when auditing Kubernetes manifests for security vulnerabilities, reviewing RBAC policies, checking pod security, or validating network policies. Only triggers when K8s manifests are detected.
---

# Kubernetes Security Audit

## Overview

Deep security audit for Kubernetes manifests, Helm templates, and Kustomize overlays. This skill catches security misconfigurations that general-purpose review cannot: overly permissive RBAC, containers running as root, missing network policies, secrets in environment variables, and images pulled without digest pinning.

Only triggers when there is clear evidence of Kubernetes usage (manifest files with K8s resource `kind:` fields, Helm charts, Kustomize overlays, or explicit user mention of K8s/EKS/GKE/AKS). When ambiguous (e.g., generic YAML without K8s resource kinds), ask the user before proceeding.

## When to Use

- When reviewing K8s manifests (Deployment, StatefulSet, DaemonSet, Pod, etc.) for security issues
- When auditing RBAC configuration (Role, ClusterRole, RoleBinding, ClusterRoleBinding)
- When checking network policies for ingress/egress restrictions
- When validating pod security contexts and security standards
- When reviewing secrets handling in K8s manifests
- During security review of EKS-specific configurations (IRSA, pod identity, aws-auth)

## When NOT to Use

- For Terraform security review — use `terraform-security-audit` instead
- For generic YAML files that are not K8s manifests — ask the user first
- For runtime cluster security (this is static manifest audit only)
- For application-level security (OWASP, auth flows) — use general security review
- When no K8s evidence is detected and user hasn't mentioned K8s

## Workflow

1. **Detect K8s presence**: Confirm K8s manifests exist (look for `apiVersion:` and `kind:` fields with K8s resource types). If ambiguous, ask user.
2. **Collect scope**: Identify all manifest files (`.yaml`, `.yml`) containing K8s resources, Helm templates, and Kustomize bases/overlays.
3. **RBAC audit**: Read every Role, ClusterRole, RoleBinding, and ClusterRoleBinding. Flag wildcard verbs/resources, unnecessary cluster-admin bindings, overly broad API group access.
4. **Pod security audit**: Check every Pod spec (in Deployments, StatefulSets, DaemonSets, Jobs, CronJobs, Pods) for security context, privilege escalation, capabilities, host namespace sharing.
5. **Network policy audit**: Verify network policies exist for namespaces with workloads. Flag missing policies, allow-all rules, and unrestricted egress.
6. **Secrets audit**: Check for secrets in environment variables (should use volume mounts), hardcoded values in manifests, and unencrypted Secret resources.
7. **Image security audit**: Flag `latest` tag, missing image digest, untrusted registries, missing `imagePullPolicy`.
8. **Service account audit**: Check for unnecessary auto-mounted service account tokens, default service account usage.
9. **Pod Security Standards**: Evaluate against PSS baseline and restricted profiles.
10. **EKS-specific checks** (if EKS detected): IRSA configuration, EKS pod identity, aws-auth ConfigMap, managed node group security.
11. **Deprecation flag**: If deprecated APIs are found (e.g., PodSecurityPolicy), flag them and recommend running `deprecation-check-and-upgrade` for full migration guidance.
12. **Produce report**: Use the template from `templates.md`.

See `audit-dimensions.md` for detailed check tables and verification steps for each dimension.

## Critical Checks

These are the highest-priority items to flag:

- ClusterRole with `verbs: ["*"]` or `resources: ["*"]` bound to non-system service accounts
- Containers running as root (`runAsNonRoot: false` or missing, `runAsUser: 0`)
- `privileged: true` or `allowPrivilegeEscalation: true` in security context
- Host namespace access (`hostPID`, `hostIPC`, `hostNetwork: true`)
- No NetworkPolicy in namespaces with internet-facing workloads
- Secrets passed via `env` instead of volume mounts
- Images using `latest` tag or no digest pinning
- Default service account used with auto-mounted token in production workloads

## Common Mistakes

| Mistake | Why It Happens | Correct Approach |
|---------|---------------|-----------------|
| Flagging `hostNetwork: true` on all DaemonSets | Some system DaemonSets legitimately need host networking (CNI plugins, node exporters) | Check if the workload is a system component before flagging |
| Treating all `cluster-admin` bindings as violations | System components and CI/CD bootstrap may need cluster-admin | Flag non-system cluster-admin bindings; verify system ones have justification |
| Ignoring init containers in security audit | Init containers can have different security contexts | Audit init containers alongside regular containers |
| Not checking CronJob pod templates | CronJobs wrap a Job template which wraps a Pod template | Traverse the full CronJob → Job → Pod spec chain |
| Flagging missing NetworkPolicy in kube-system | kube-system typically needs open internal communication | Skip kube-system namespace for NetworkPolicy checks unless explicitly requested |
| Treating `readOnlyRootFilesystem: false` as always critical | Some applications need writable tmp directories | Flag as Important, not Critical; suggest `emptyDir` volume mounts as alternative |

## Supporting Files

- `audit-dimensions.md` — Detailed check tables for RBAC, pod security, network policies, secrets, images, service accounts, PSS, and EKS-specific dimensions
- `templates.md` — Report output template with severity grading
