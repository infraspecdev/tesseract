# Kubernetes Migration Guide

## Migration Ordering

### Recommended Order

1. **Non-breaking API updates first**: Resources where the old and new API versions coexist (deprecated but not removed). These can be updated in-place without risk.
2. **RBAC group updates**: Update any RBAC rules that reference old API groups (e.g., `extensions` → `networking.k8s.io` for Ingress).
3. **CRD updates**: If CustomResourceDefinitions need migration, do these before the resources that depend on them.
4. **Breaking changes last**: Resources with field restructuring or behavioral changes (e.g., Ingress with new `pathType`, PSP → PSA migration).

### Migration Strategy by Version Gap

| Gap | Strategy | Risk |
|-----|----------|------|
| 1 minor version (e.g., 1.27 → 1.28) | Update deprecated APIs, test, upgrade | Low |
| 2-3 minor versions (e.g., 1.25 → 1.28) | Update all removed APIs first, test extensively, then upgrade | Medium |
| 4+ minor versions (e.g., 1.22 → 1.28) | Step-by-step upgrade through each minor version, or update all APIs to latest and test against target | High — use Kind cluster validation |

### Pre-Migration Checklist

- [ ] Target K8s version confirmed with ops team
- [ ] All deprecated APIs identified (run this skill)
- [ ] Breaking changes documented and understood
- [ ] Upstream dependency compatibility verified (Helm charts, operators, CRDs)
- [ ] CI tools updated for target version (kubeconform schema, pluto config)
- [ ] Rollback plan documented
- [ ] Local Kind cluster tested (if available)

## Rollback Considerations

### One-Way Migrations

These API versions are **removed** and cannot be used after upgrading. Plan carefully:

- If upgrading from K8s <1.16 → 1.16+: `extensions/v1beta1` workloads must migrate to `apps/v1`
- If upgrading from K8s <1.22 → 1.22+: Many v1beta1 APIs removed (RBAC, storage, webhooks, CRDs)
- If upgrading from K8s <1.25 → 1.25+: PodSecurityPolicy removed entirely (no direct replacement)
- If upgrading from K8s <1.25 → 1.25+: `batch/v1beta1` CronJob removed
- If upgrading from K8s <1.26 → 1.26+: `autoscaling/v2beta1` and `v2beta2` HPA removed

### Rollback Safety

| Scenario | Safe to Rollback? | Notes |
|----------|-------------------|-------|
| Updated to new API version, old version still available | Yes | Both versions work on current cluster |
| Updated to new API version, old version removed in target | No | Can't roll back manifests on new cluster |
| Cluster upgraded, manifests using new-only features | No | Old cluster won't accept new-only fields |
| Cluster upgraded, manifests still on old (deprecated) API | Yes | Deprecated APIs work until removal |

### Recommended Rollback Strategy

1. **Keep a tagged copy** of pre-migration manifests in version control
2. **Test rollback** in a non-prod environment before upgrading prod
3. **For PSP → PSA migration**: keep PSP resources in place during transition, remove only after PSA is verified working
4. **For Helm charts**: maintain a rollback values file with the previous version's configuration

## Kind Cluster Validation Guide

### Setup

```bash
# Install Kind if not present
# Check https://kind.sigs.k8s.io/docs/user/quick-start/ for latest install

# Create cluster at target version
kind create cluster --name upgrade-test --image kindest/node:v<target-version>

# Verify version
kubectl version --short
```

### Validation Steps

```bash
# 1. Apply migrated manifests (dry-run first)
kubectl apply --dry-run=server -f <migrated-manifests-dir>/

# 2. Full apply
kubectl apply -f <migrated-manifests-dir>/

# 3. Check for errors
kubectl get events --field-selector type=Warning

# 4. Verify workloads are running
kubectl get pods --all-namespaces

# 5. Run schema validation
kubeconform -kubernetes-version <target-version> -strict <manifests-dir>/
```

### For Helm Charts

```bash
# Template and validate
helm template <release> <chart-dir> | kubeconform -kubernetes-version <target-version> -strict

# Lint
helm lint <chart-dir>

# Install in Kind cluster
helm install <release> <chart-dir> --namespace test --create-namespace
```

### For Kustomize

```bash
# Build and validate
kustomize build <overlay-dir> | kubeconform -kubernetes-version <target-version> -strict

# Apply to Kind cluster
kustomize build <overlay-dir> | kubectl apply -f -
```

### Teardown

```bash
kind delete cluster --name upgrade-test
```

### When Kind Is Not Available

Fall back to these lighter validation methods:

1. **kubeconform** — schema validation without a cluster
   ```bash
   kubeconform -kubernetes-version <target-version> -strict -summary <manifests>/
   ```

2. **pluto** — deprecation scanner
   ```bash
   pluto detect-files -d <manifests>/ --target-versions k8s=v<target-version>
   ```

3. **kubectl dry-run (client)** — basic YAML validation
   ```bash
   kubectl apply --dry-run=client -f <manifests>/
   ```

These methods catch API version issues but not runtime problems (webhook rejections, CRD conflicts). For full confidence, use Kind.
