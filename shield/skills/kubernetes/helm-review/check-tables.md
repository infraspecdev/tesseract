# Helm Chart Check Tables

## Chart Metadata (H1-H5)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| H1 | Chart.yaml completeness | `name`, `version`, `appVersion`, `description`, `type` all present | Important |
| H2 | Version follows semver | `version` field follows semver (X.Y.Z), `appVersion` matches application version | Important |
| H3 | Maintainers listed | At least one maintainer with name and email/url | Warning |
| H4 | Keywords and sources | `keywords`, `home`, `sources` help with chart discoverability | Warning |
| H5 | Chart type specified | `type: application` or `type: library` — defaults to application if missing | Warning |

## Values (H6-H11)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| H6 | Sensible defaults | `values.yaml` provides working defaults for basic deployment | Important |
| H7 | No hardcoded secrets | No passwords, tokens, API keys in default values | Critical |
| H8 | Values documented | Comments above each value section explaining purpose and valid options | Important |
| H9 | Image tag not `latest` | Default image tag is a specific version, not `latest` | Important |
| H10 | Resource requests/limits | Default resource values present (even if conservative) | Important |
| H11 | Configurable replicas | `replicaCount` exposed in values for environment-specific overrides | Warning |

## Templates (H12-H18)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| H12 | _helpers.tpl exists | Common labels, names, selectors defined as template helpers | Important |
| H13 | Consistent labels | All resources use `{{ include "chart.labels" . }}` from helpers | Important |
| H14 | Release-aware naming | Resource names include `{{ .Release.Name }}` to avoid collisions | Important |
| H15 | Selector labels match | Deployment `matchLabels` consistent with pod template labels | Critical |
| H16 | Service selector matches | Service `selector` matches pod labels | Critical |
| H17 | Conditional resources | Optional resources gated with `{{ if .Values.feature.enabled }}` | Important |
| H18 | Whitespace control | `{{-` and `-}}` used appropriately, no excessive blank lines in rendered output | Warning |

## Hooks & Tests (H19-H22)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| H19 | Hook weights ordered | Multiple hooks have `helm.sh/hook-weight` for deterministic ordering | Important |
| H20 | Hook cleanup policy | Hooks have `helm.sh/hook-delete-policy` to clean up completed resources | Important |
| H21 | Test templates exist | `templates/tests/` directory with at least one test (e.g., test-connection.yaml) | Warning |
| H22 | NOTES.txt present | `templates/NOTES.txt` provides useful post-install instructions | Warning |

## Dependencies (H23-H26)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| H23 | Chart.lock committed | Lock file ensures reproducible dependency versions | Important |
| H24 | Version ranges appropriate | Dependencies use `~X.Y.0` (minor pinning), not `*` or `>=X` | Important |
| H25 | Condition toggles | Subchart dependencies have `condition` field for enable/disable | Important |
| H26 | Values passthrough | Parent values correctly map to subchart values via alias or subchart name | Warning |
