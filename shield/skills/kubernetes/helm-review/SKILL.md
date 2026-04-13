---
name: kubernetes-helm-review
description: Use when reviewing Helm chart structure, values, templates, and best practices. Only triggers when Chart.yaml is detected.
---

# Kubernetes Helm Review

## Overview

Reviews Helm chart structure and best practices. Covers chart metadata, values defaults, template patterns, dependency management, hooks, and tests. Complements the K8s security/cost/operational skills by focusing on Helm-specific concerns like template hygiene and chart packaging.

Only triggers when `Chart.yaml` is detected. Does not trigger for raw K8s manifests — use the core K8s skills for those.

## When to Use

- When reviewing a Helm chart for structural best practices
- When auditing `values.yaml` defaults and documentation
- When checking template helpers and naming conventions
- When reviewing Helm hooks, tests, and dependency management

## When NOT to Use

- For raw K8s manifest review — use core K8s skills (security-audit, cost-review, operational-review)
- For Kustomize overlays — use `kubernetes-kustomize-review`
- When no `Chart.yaml` is found
- For Helm chart deployment/release issues — this is static chart review only

## Workflow

1. **Detect Helm chart**: Confirm `Chart.yaml` exists at the target path. If not found, do not proceed.
2. **Chart metadata**: Review `Chart.yaml` for completeness, version constraints, maintainer info.
3. **Values review**: Check `values.yaml` for sensible defaults, documentation, no hardcoded secrets.
4. **Template review**: Check templates for helper usage, consistent labeling, resource naming patterns.
5. **NOTES.txt**: Verify post-install instructions exist and are useful.
6. **Hooks review**: Check hook annotations for proper weight ordering and cleanup policy.
7. **Tests review**: Verify test templates exist (e.g., `test-connection.yaml`).
8. **Dependencies**: Check `Chart.lock` committed, version ranges appropriate, subchart value passthrough.
9. **Deprecation flag**: If deprecated K8s API versions are found in templates, flag them and recommend `deprecation-check-and-upgrade`.
10. **Produce report**: Present findings with check pass/fail status.

See `check-tables.md` for detailed check definitions.

## Critical Checks

- `Chart.yaml` missing `appVersion` or `version`
- Hardcoded secrets or passwords in `values.yaml`
- Templates not using `_helpers.tpl` for common labels and names
- Missing `NOTES.txt` (users get no post-install guidance)
- Subchart dependencies without version pinning
- Missing `Chart.lock` (dependency versions not reproducible)

## Common Mistakes

| Mistake | Why It Happens | Correct Approach |
|---------|---------------|-----------------|
| Flagging missing tests on library charts | Library charts have no installable templates | Tests only apply to application charts (`type: application`) |
| Requiring NOTES.txt on subcharts | Subcharts don't display NOTES independently | NOTES.txt is for the parent chart only |
| Flagging `{{ .Release.Namespace }}` usage | Some see this as hardcoding namespace | This is correct — it uses the release namespace dynamically |
| Treating all `default` values as problems | `default` template function is normal Helm pattern | Only flag `default` when it masks missing required values |
| Requiring version pinning to patch level | Overly strict pinning blocks security patches | Minor version pinning (`~1.2.0`) is appropriate for most deps |

## Supporting Files

- `check-tables.md` — Chart structure and template checks with pass/fail criteria
