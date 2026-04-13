# Kubernetes API Deprecation Tables

## How to Use This Reference

For each entry: check if your manifests use the **Deprecated API**. If the **Removed In** version is <= your target K8s version, migration is **mandatory** (Critical). If it's a future version, migration is **recommended** (Warning).

## Core API Deprecations

### Networking

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| Ingress | `extensions/v1beta1` | `networking.k8s.io/v1` | 1.14 | 1.22 | `pathType` required, `backend` structure changed to `service.name`/`service.port` |
| Ingress | `networking.k8s.io/v1beta1` | `networking.k8s.io/v1` | 1.19 | 1.22 | Same as above |
| IngressClass | `networking.k8s.io/v1beta1` | `networking.k8s.io/v1` | 1.19 | 1.22 | No major field changes |
| NetworkPolicy | `extensions/v1beta1` | `networking.k8s.io/v1` | 1.9 | 1.16 | No major field changes |

### Workloads

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| Deployment | `extensions/v1beta1` | `apps/v1` | 1.9 | 1.16 | `spec.selector` required and immutable |
| Deployment | `apps/v1beta1` | `apps/v1` | 1.9 | 1.16 | Same |
| Deployment | `apps/v1beta2` | `apps/v1` | 1.9 | 1.16 | Same |
| StatefulSet | `apps/v1beta1` | `apps/v1` | 1.9 | 1.16 | `spec.selector` required and immutable |
| StatefulSet | `apps/v1beta2` | `apps/v1` | 1.9 | 1.16 | Same |
| DaemonSet | `extensions/v1beta1` | `apps/v1` | 1.9 | 1.16 | `spec.selector` required and immutable |
| DaemonSet | `apps/v1beta2` | `apps/v1` | 1.9 | 1.16 | Same |
| ReplicaSet | `extensions/v1beta1` | `apps/v1` | 1.9 | 1.16 | `spec.selector` required and immutable |
| ReplicaSet | `apps/v1beta2` | `apps/v1` | 1.9 | 1.16 | Same |
| CronJob | `batch/v1beta1` | `batch/v1` | 1.21 | 1.25 | No major field changes |
| HorizontalPodAutoscaler | `autoscaling/v2beta1` | `autoscaling/v2` | 1.23 | 1.26 | `metrics` field restructured |
| HorizontalPodAutoscaler | `autoscaling/v2beta2` | `autoscaling/v2` | 1.23 | 1.26 | Minor field naming changes |

### Security & Policy

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| PodSecurityPolicy | `policy/v1beta1` | Pod Security Admission (built-in) | 1.21 | 1.25 | **No direct replacement resource** — migrate to PSA namespace labels + policy engine (OPA/Kyverno) |
| PodDisruptionBudget | `policy/v1beta1` | `policy/v1` | 1.21 | 1.25 | `spec.unhealthyPodEvictionPolicy` added |

### RBAC

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| ClusterRole | `rbac.authorization.k8s.io/v1beta1` | `rbac.authorization.k8s.io/v1` | 1.17 | 1.22 | No major field changes |
| ClusterRoleBinding | `rbac.authorization.k8s.io/v1beta1` | `rbac.authorization.k8s.io/v1` | 1.17 | 1.22 | No major field changes |
| Role | `rbac.authorization.k8s.io/v1beta1` | `rbac.authorization.k8s.io/v1` | 1.17 | 1.22 | No major field changes |
| RoleBinding | `rbac.authorization.k8s.io/v1beta1` | `rbac.authorization.k8s.io/v1` | 1.17 | 1.22 | No major field changes |

### Storage

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| CSIDriver | `storage.k8s.io/v1beta1` | `storage.k8s.io/v1` | 1.19 | 1.22 | No major field changes |
| CSINode | `storage.k8s.io/v1beta1` | `storage.k8s.io/v1` | 1.17 | 1.22 | No major field changes |
| StorageClass | `storage.k8s.io/v1beta1` | `storage.k8s.io/v1` | 1.6 | 1.22 | No major field changes |
| VolumeAttachment | `storage.k8s.io/v1beta1` | `storage.k8s.io/v1` | 1.13 | 1.22 | No major field changes |

### API Extensions

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| CustomResourceDefinition | `apiextensions.k8s.io/v1beta1` | `apiextensions.k8s.io/v1` | 1.16 | 1.22 | `spec.versions` required (not `spec.version`), structural schemas required, `spec.preserveUnknownFields` must be false |
| MutatingWebhookConfiguration | `admissionregistration.k8s.io/v1beta1` | `admissionregistration.k8s.io/v1` | 1.16 | 1.22 | `sideEffects` required, `admissionReviewVersions` required |
| ValidatingWebhookConfiguration | `admissionregistration.k8s.io/v1beta1` | `admissionregistration.k8s.io/v1` | 1.16 | 1.22 | Same as MutatingWebhookConfiguration |

### Scheduling

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| PriorityClass | `scheduling.k8s.io/v1beta1` | `scheduling.k8s.io/v1` | 1.14 | 1.22 | No major field changes |

### Certificates

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| CertificateSigningRequest | `certificates.k8s.io/v1beta1` | `certificates.k8s.io/v1` | 1.19 | 1.22 | `spec.signerName` required, `status.certificate` must be PEM |

### Recent Deprecations (1.25+)

| Resource | Deprecated API | Replacement API | Deprecated In | Removed In | Key Changes |
|----------|---------------|----------------|--------------|-----------|-------------|
| FlowSchema | `flowcontrol.apiserver.k8s.io/v1beta1` | `flowcontrol.apiserver.k8s.io/v1beta3` | 1.26 | 1.29 | Field renames |
| FlowSchema | `flowcontrol.apiserver.k8s.io/v1beta2` | `flowcontrol.apiserver.k8s.io/v1beta3` | 1.26 | 1.29 | Field renames |
| FlowSchema | `flowcontrol.apiserver.k8s.io/v1beta3` | `flowcontrol.apiserver.k8s.io/v1` | 1.29 | 1.32 | No major changes |

## Third-Party CRD Deprecation Notes

These are not K8s core APIs but commonly encountered:

| Component | Version Change | Notes |
|-----------|---------------|-------|
| cert-manager | v1alpha2/v1alpha3 → v1 | CRDs changed significantly; check cert-manager upgrade docs |
| Istio | networking.istio.io/v1alpha3 → v1beta1/v1 | VirtualService and DestinationRule field changes |
| Traefik | traefik.containo.us/v1alpha1 → traefik.io/v1alpha1 | API group changed |
| Prometheus Operator | monitoring.coreos.com/v1alpha1 → v1 | Some CRDs stable, others still alpha |

Always check the specific component's compatibility matrix for your target K8s version.
