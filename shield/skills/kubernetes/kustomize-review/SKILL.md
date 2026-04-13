---
name: kubernetes-kustomize-review
description: Use when reviewing Kustomize overlay structure, patch hygiene, and base/overlay separation. Only triggers when kustomization.yaml is detected.
---

# Kubernetes Kustomize Review

## Overview

Reviews Kustomize overlay structure and best practices. Covers base/overlay separation, patch strategy, resource references, naming conventions, generator options, and component reuse. Ensures Kustomize configurations are maintainable, DRY, and correctly structured.

Only triggers when `kustomization.yaml` is detected. Does not trigger for raw K8s manifests or Helm charts.

## When to Use

- When reviewing Kustomize base/overlay structure
- When auditing patch strategy (strategic merge vs JSON patch)
- When checking resource references and overlay consistency
- When evaluating component reuse and overlay sprawl

## When NOT to Use

- For raw K8s manifest review — use core K8s skills
- For Helm chart review — use `kubernetes-helm-review`
- When no `kustomization.yaml` is found
- For Kustomize runtime issues (build failures) — this is structural review only

## Workflow

1. **Detect Kustomize**: Confirm `kustomization.yaml` exists at the target path. If not found, do not proceed.
2. **Structure review**: Map the base/overlay directory tree, identify all kustomization.yaml files.
3. **Base review**: Check bases are generic and reusable, not environment-specific.
4. **Overlay review**: Check overlays are minimal, environment-specific, and reference valid bases.
5. **Patch review**: Evaluate patch strategy choices (strategic merge vs JSON patch).
6. **Resource reference check**: Verify all referenced files exist, no orphaned patches.
7. **Naming conventions**: Check namePrefix/nameSuffix consistency across overlays.
8. **Labels and annotations**: Verify commonLabels and commonAnnotations used correctly.
9. **Generators**: Check ConfigMap/Secret generators vs raw files.
10. **Component reuse**: Identify duplicated config that should be extracted into components.
11. **Deprecation flag**: If deprecated K8s API versions found in bases/overlays, flag and recommend `deprecation-check-and-upgrade`.
12. **Produce report**: Present findings with check pass/fail status.

See `check-tables.md` for detailed check definitions.

## Critical Checks

- Bases containing environment-specific values (should be in overlays)
- Overlays referencing non-existent bases or resources
- Patches targeting resources not in the base
- commonLabels that would break selector immutability on existing Deployments
- Secrets in plain text in generators without external secret references

## Common Mistakes

| Mistake | Why It Happens | Correct Approach |
|---------|---------------|-----------------|
| Flagging strategic merge patches as always wrong | JSON patches are more precise but harder to read | Strategic merge is fine for simple field overrides; JSON patch for complex operations |
| Requiring components for every shared config | Components add indirection | Use components only when 3+ overlays share the same patch |
| Flagging namePrefix as inconsistency | Different envs may need different prefixes | Verify prefixes are intentional and documented |
| Treating all overlay differences as sprawl | Each environment needs specific config | Sprawl is when overlays differ in only 1-2 trivial values that could be parameterized |
| Not checking the rendered output | Kustomize YAML looks correct in parts but renders incorrectly | Run `kustomize build` mentally — do patches apply to the right targets? |

## Supporting Files

- `check-tables.md` — Overlay structure and patch checks with pass/fail criteria
