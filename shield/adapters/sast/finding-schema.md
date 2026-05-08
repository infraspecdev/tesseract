# Normalized Finding Schema

Every SAST adapter normalizes its tool's output to this schema before returning it. Definitions live in `common.py` as Python dataclasses.

## Finding

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | yes | Adapter name, e.g. `"semgrep"`, `"sonarqube"` |
| `rule_id` | string | yes | Tool-native rule ID (e.g. `"java.spring.security.csrf-disabled"`, `"java:S5547"`) |
| `file` | string | yes | Path relative to repo root |
| `lines` | string | yes | Single line `"27"` or range `"27-29"` |
| `severity` | enum | yes | `"high"` \| `"medium"` \| `"low"` (see `severity-mapping.md`) |
| `category` | enum | yes | `"security"` \| `"code-quality"` \| `"performance"` \| `"reliability"` \| `"style"` |
| `message` | string | yes | One-line description from the tool |
| `fix_hint` | string | no | Recommended fix, when the tool provides one |

## AdapterResult

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | yes | Adapter name |
| `mode` | enum | yes | `"consumed"` \| `"invoked"` \| `"unavailable"` |
| `runtime_seconds` | float | yes | How long the adapter took |
| `findings` | list[Finding] | yes | May be empty |
| `note` | string | no | Used for best-effort skip messages, invocation errors |

## Dedup

Findings dedupe at aggregation by:

- `file` (exact match)
- `lines` (overlapping range within ±2)

Two findings on the same file/line area collapse to a single entry citing all `source` fields. No skill↔rule mapping is required — location overlap is sufficient.

SAST findings whose location does not overlap any skill finding surface in a dedicated "Repo-wide SAST findings" section in the report.
