# Kubernetes Security Audit Dimensions

## Dimension 1: RBAC Analysis

Analyze every Role, ClusterRole, RoleBinding, and ClusterRoleBinding:

| Check | What General Review Misses | How to Verify |
|-------|---------------------------|---------------|
| Wildcard verbs | `verbs: ["*"]` grants delete, escalate, impersonate | Expand wildcards, check if all verbs are needed |
| Wildcard resources | `resources: ["*"]` grants access to secrets, configmaps, pods/exec | Verify resource list is scoped to what's actually needed |
| Wildcard API groups | `apiGroups: ["*"]` grants access to all API groups including RBAC | Scope to specific API groups |
| Cluster-scope vs namespace-scope | ClusterRole used when Role would suffice | Check if the binding is ClusterRoleBinding or RoleBinding |
| Privilege escalation via bind | `verbs: ["bind"]` on roles allows self-escalation | Flag `bind`, `escalate`, `impersonate` verbs |
| Secrets access | Role allows `get`, `list`, `watch` on secrets | Verify the workload actually needs secrets access |
| Pod exec access | `pods/exec` resource allows remote code execution | Flag unless explicitly needed (debugging tools only) |
| Service account binding | RoleBinding binds to `default` service account | Should bind to purpose-specific service accounts |

**How to audit:**
1. List all ClusterRole and Role resources
2. For each, expand wildcard verbs and resources to understand actual permissions
3. Trace bindings: which service accounts or groups get these permissions?
4. Flag any non-system binding to cluster-admin
5. Verify namespace-scoped Roles are used instead of ClusterRoles where possible

## Dimension 2: Pod Security

Check every Pod spec (including embedded specs in Deployments, StatefulSets, DaemonSets, Jobs, CronJobs):

| Check | What General Review Misses | How to Verify |
|-------|---------------------------|---------------|
| runAsNonRoot missing | Container defaults to root if not explicitly set | Verify `securityContext.runAsNonRoot: true` at pod or container level |
| runAsUser: 0 | Explicitly running as root | Should be non-zero (e.g., 1000, 65534) |
| privileged mode | Full host access, bypasses all security | `securityContext.privileged` must be `false` or absent |
| allowPrivilegeEscalation | setuid binaries can escalate | `securityContext.allowPrivilegeEscalation: false` required |
| Dangerous capabilities | NET_ADMIN, SYS_ADMIN, ALL | `securityContext.capabilities.drop: ["ALL"]`, add only specific needed caps |
| Host namespaces | hostPID, hostIPC, hostNetwork bypass isolation | Must be `false` unless system component with justification |
| readOnlyRootFilesystem | Writable root allows malware persistence | `securityContext.readOnlyRootFilesystem: true`, use emptyDir for tmp |
| seccompProfile missing | No syscall filtering | Set `securityContext.seccompProfile.type: RuntimeDefault` minimum |
| appArmorProfile missing | No mandatory access control | Set appropriate AppArmor profile annotation |

**How to audit:**
1. Find every pod spec (including nested in Deployments, StatefulSets, etc.)
2. Check pod-level securityContext first, then container-level overrides
3. Both init containers and regular containers must be checked
4. For each container, verify all fields above

## Dimension 3: Network Policies

| Check | What General Review Misses | How to Verify |
|-------|---------------------------|---------------|
| Missing NetworkPolicy | Namespace allows all traffic by default | Every namespace with workloads should have at least one NetworkPolicy |
| Allow-all ingress | `ingress: [{}]` or `from: []` allows everything | Ingress rules should specify specific pod/namespace selectors or IP blocks |
| Missing egress restrictions | No egress policy means unrestricted outbound | Add egress rules, at minimum allowing DNS (port 53) and required endpoints |
| Overly broad selectors | `podSelector: {}` matches all pods in namespace | Use specific label selectors to target policies |
| Missing DNS egress | Egress policy blocks DNS, breaking service discovery | Always allow egress to port 53 UDP/TCP for kube-dns |
| Cross-namespace gaps | Policies don't account for cross-namespace traffic | Use `namespaceSelector` for legitimate cross-namespace communication |

**How to audit:**
1. List all namespaces that contain workloads
2. For each namespace, check if NetworkPolicies exist
3. For each NetworkPolicy, verify ingress and egress rules are specific
4. Trace allowed traffic paths: can a compromised pod reach sensitive services?

## Dimension 4: Secrets Management

| Check | What General Review Misses | How to Verify |
|-------|---------------------------|---------------|
| Secrets in env vars | Env vars appear in process listings and crash dumps | Use volume mounts with `secretKeyRef` volumes instead of `env.valueFrom.secretKeyRef` |
| Hardcoded values | Secret data in plain text in manifests | Values should reference external secret stores or be encrypted (SealedSecrets, SOPS, External Secrets) |
| Unencrypted Secrets | K8s Secrets are base64-encoded, not encrypted | Use EncryptionConfiguration for etcd encryption at rest, or external secret operators |
| Secret sprawl | Same secret duplicated across namespaces | Use external secret management (External Secrets Operator, Vault) |
| Overly broad secret access | Multiple workloads sharing the same secret | Each workload should have its own secret with only the keys it needs |

## Dimension 5: Image Security

| Check | What General Review Misses | How to Verify |
|-------|---------------------------|---------------|
| `latest` tag | Deployments become non-reproducible | Use specific version tags (e.g., `nginx:1.25.3`) |
| No image digest | Tags are mutable, can be overwritten | Pin critical images with digest (`image@sha256:...`) |
| Untrusted registries | Public registries may serve compromised images | Use private registry or verified publishers |
| Missing imagePullPolicy | Defaults vary by tag (Always for latest, IfNotPresent otherwise) | Set explicitly: `imagePullPolicy: Always` for mutable tags, `IfNotPresent` for immutable |
| No image pull secrets | Private registry images fail silently | Configure `imagePullSecrets` in pod spec or service account |

## Dimension 6: Service Accounts

| Check | What General Review Misses | How to Verify |
|-------|---------------------------|---------------|
| Default service account | Pods use `default` SA which may have accumulated permissions | Create dedicated service accounts per workload |
| Auto-mounted tokens | Token mounted even when pod doesn't call K8s API | Set `automountServiceAccountToken: false` on pods that don't need it |
| Shared service accounts | Multiple workloads sharing one SA | Each workload should have its own SA with minimal RBAC |

## Dimension 7: Pod Security Standards (PSS)

Evaluate manifests against the Kubernetes Pod Security Standards:

| Level | Key Requirements |
|-------|-----------------|
| **Privileged** | Unrestricted — only for system components |
| **Baseline** | No privileged, no hostNamespaces, no hostPorts (ranges), restricted volume types, no procMount, restricted seccomp/AppArmor |
| **Restricted** | Baseline + must run as non-root, drop ALL capabilities, restricted volume types, no privilege escalation, seccomp RuntimeDefault or Localhost |

**How to audit:**
1. Determine the target PSS level (default: restricted for application workloads, baseline for system components)
2. Check each pod spec against the target level requirements
3. Flag violations with specific field and required value

## Dimension 8: EKS-Specific Checks

Only apply when EKS is detected (user mentions EKS, AWS annotations present, or Terraform EKS modules found alongside K8s manifests):

| Check | What General Review Misses | How to Verify |
|-------|---------------------------|---------------|
| IRSA not used | Static AWS credentials in secrets instead of IAM Roles for Service Accounts | Service accounts should have `eks.amazonaws.com/role-arn` annotation |
| EKS Pod Identity | Newer alternative to IRSA for cross-account | Check for EKS Pod Identity Association resources |
| aws-auth ConfigMap | Over-permissioned IAM → K8s group mappings | Review `kube-system/aws-auth` for unnecessary admin/cluster-admin mappings |
| Security groups for pods | Missing ENI-based security groups | Check for `SecurityGroupPolicy` resources in EKS clusters using VPC CNI |
| Managed node group AMI | Custom AMI may miss security patches | Prefer EKS-optimized AMI or verify custom AMI update process |
