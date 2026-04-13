# Kustomize Check Tables

## Base Structure (KU1-KU5)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| KU1 | Base is environment-agnostic | No environment-specific values (replica counts, image tags, resource limits) in base | Critical |
| KU2 | Resources list complete | `kustomization.yaml` `resources` field lists all manifests in the directory | Important |
| KU3 | No hardcoded namespaces in base | Namespace set via overlay, not hardcoded in base manifests | Important |
| KU4 | Base is self-contained | `kustomize build base/` succeeds independently | Important |
| KU5 | Labels in base are generic | Base labels identify the app, not the environment | Warning |

## Overlay Structure (KU6-KU10)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| KU6 | Overlay references valid base | `resources` includes relative path to base that exists | Critical |
| KU7 | Minimal overlay | Overlay only contains environment-specific overrides, not full resource copies | Important |
| KU8 | Namespace set in overlay | `namespace` field set in overlay kustomization.yaml | Important |
| KU9 | Environment-specific values | Image tags, replica counts, resource limits set per environment | Important |
| KU10 | Overlay naming convention | Directories follow consistent pattern (e.g., `overlays/dev/`, `overlays/staging/`, `overlays/prod/`) | Warning |

## Patch Strategy (KU11-KU14)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| KU11 | Correct patch type | Strategic merge for field overrides, JSON patch for complex operations (add/remove/move) | Important |
| KU12 | Patch targets exist | Patches reference resources that exist in the base | Critical |
| KU13 | Patch selectors specific | Patches use `target` with kind, name, and optionally namespace | Important |
| KU14 | No patch duplication | Same patch not duplicated across overlays — extract to component | Warning |

## Generators & Resources (KU15-KU18)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| KU15 | ConfigMap generators | ConfigMaps generated from files/literals, not raw manifests (enables hash-based rollout) | Important |
| KU16 | Secret generators | Secrets use generators with external references, not hardcoded values | Critical |
| KU17 | Generator options | `generatorOptions` configured for label/annotation behavior | Warning |
| KU18 | No orphaned files | All files in directory are referenced by kustomization.yaml or a patch | Warning |

## Naming & Labels (KU19-KU22)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| KU19 | namePrefix/nameSuffix consistent | All overlays for same base use consistent naming patterns | Important |
| KU20 | commonLabels safe | No commonLabels that would modify Deployment selector (immutable after creation) | Critical |
| KU21 | commonAnnotations appropriate | Annotations applied at the right scope (not on all resources when only some need them) | Warning |
| KU22 | Var references resolved | If using `vars`, all referenced resources and fields exist | Important |

## Component Reuse (KU23-KU25)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| KU23 | Shared patches extracted | Config shared by 3+ overlays is a Kustomize component, not duplicated | Warning |
| KU24 | Component isolation | Components are self-contained and don't reference overlay-specific resources | Important |
| KU25 | No overlay sprawl | Overlays that differ in <3 values should be consolidated or parameterized | Warning |
