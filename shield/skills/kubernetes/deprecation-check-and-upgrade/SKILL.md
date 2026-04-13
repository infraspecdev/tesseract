---
name: kubernetes-deprecation-check-and-upgrade
description: Use when checking Kubernetes manifests for deprecated or removed APIs, planning K8s version upgrades, or migrating manifests to newer API versions. Also use when another K8s review skill flags deprecated APIs.
---

# Kubernetes Deprecation Check and Upgrade

## Overview

Comprehensive API deprecation audit with migration guidance, testing requirements, and local validation paths. Scans manifests, Helm templates, and Kustomize bases for deprecated or removed Kubernetes API versions, provides concrete migration steps, calls out breaking changes, and recommends validation approaches including local Kind cluster testing.

Triggered by direct user request for upgrade/version checks, or as a cascading recommendation from other K8s review skills (security-audit, operational-review, helm-review, kustomize-review) when they detect deprecated APIs.

## When to Use

- When planning a Kubernetes version upgrade
- When other K8s review skills flag deprecated APIs and recommend this skill
- When checking manifests for API compatibility with a target K8s version
- When migrating manifests from deprecated to current API versions
- When auditing Helm charts or Kustomize bases for API version currency

## When NOT to Use

- For general K8s security/cost/ops review — use the dedicated skills
- For Terraform provider version upgrades — use Terraform-specific skills
- When manifests are already on current API versions with no upgrade planned

## Workflow

### Phase 1: Check

1. **Determine target version**: Ask the user for the target K8s version if not detectable from cluster config, Helm chart constraints, or context. This is required — do not assume a version.
2. **Scan manifests**: Read all K8s manifest files (.yaml, .yml), Helm templates, and Kustomize bases. Extract `apiVersion` and `kind` from each resource.
3. **Cross-reference deprecation tables**: For each resource, check against `deprecation-tables.md` to determine if the API version is deprecated or removed in the target version.
4. **Report findings**: For each deprecated/removed API, report: current API version → deprecated in → removed in → replacement API → severity (Warning if deprecated, Critical if removed in target).

### Phase 2: Breaking Changes

5. **Field mapping analysis**: For each migration, identify field changes between old and new API versions (additions, removals, renames, behavioral changes).
6. **Behavioral changes**: Call out semantic differences — e.g., PSA replacing PSP has different enforcement model, Ingress `pathType` is required in networking.k8s.io/v1.
7. **Webhook compatibility**: Flag custom admission webhooks that may reject new API versions.
8. **CRD version changes**: If operators/CRDs are involved, check their compatibility with the target K8s version.
9. **RBAC impact**: Flag RBAC rules referencing old API groups that need updating (e.g., `extensions` → `networking.k8s.io`).
10. **Dependency check**: Review upstream Helm chart dependencies and third-party operators for target version compatibility. Check infrastructure component version matrices (ingress controller, cert-manager, external-dns, etc.).

### Phase 3: Upgrade

11. **Generate migration plan**: For each deprecated resource, provide the concrete migration: old YAML → new YAML with field mappings.
12. **Migration ordering**: Recommend order of operations (see `migration-guide.md`).

### Phase 4: Testing

13. **Schema validation**: Recommend `kubeconform` or `kubeval` against the target K8s version schema.
14. **Dry-run validation**: Recommend `kubectl apply --dry-run=server` against a cluster running the target version. For Helm charts, also `helm template` + `helm lint`. For Kustomize, also `kustomize build`.
15. **CI tool check**: Verify existing CI tools (kubeconform, pluto, kubeval) are configured for the target version.
16. **Local Kind cluster validation**: Recommend a Kind cluster at the target version for full validation — user opts in. See `migration-guide.md` for exact commands and fallback options when Kind is unavailable.

### Phase 5: Rollback Assessment

17. **One-way migrations**: Flag APIs where the old version is removed in the target K8s version — no rollback to old manifests possible.
18. **Rollback strategy**: Recommend migration ordering based on version gap and risk. See `migration-guide.md`.

## Critical Checks

- Resources using API versions removed in the target K8s version (deployment will fail)
- PodSecurityPolicy resources (removed in K8s 1.25, no in-place migration)
- Ingress resources using `extensions/v1beta1` or `networking.k8s.io/v1beta1`
- Custom resources whose CRD apiextensions version has changed
- Helm charts with hardcoded deprecated API versions in templates

## Common Mistakes

| Mistake | Why It Happens | Correct Approach |
|---------|---------------|-----------------|
| Scanning only top-level manifests | Helm templates and Kustomize bases are missed | Scan rendered templates (`helm template`), Kustomize bases, and raw manifests |
| Not checking CRD compatibility | Focus on core K8s APIs only | Third-party CRDs (cert-manager, Istio) have their own deprecation cycles |
| Recommending Kind cluster without checking target version availability | Not all K8s versions have Kind node images | Check `kindest/node` tags for available versions |
| Ignoring RBAC group changes | API group changes affect RBAC rules too | If `extensions` → `networking.k8s.io` for Ingress, update RBAC rules referencing `extensions` |
| Migrating all at once | Big-bang migration is risky | Recommend incremental migration: non-breaking changes first, then breaking ones |
| Not flagging webhook compatibility | Admission webhooks may reject new API versions | Check ValidatingWebhookConfiguration and MutatingWebhookConfiguration for API version filters |

## Supporting Files

- `deprecation-tables.md` — API deprecation matrix by Kubernetes version (1.22 through 1.32)
- `migration-guide.md` — Rollback strategies, migration ordering, dependency checklists, Kind cluster validation guide
