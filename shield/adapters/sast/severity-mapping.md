# Severity Mapping Reference

Each SAST tool has its own severity scale. Adapters map tool-native severities to shield's normalized `high` / `medium` / `low` when emitting findings.

## Semgrep

| Tool-native | Normalized |
|---|---|
| `ERROR` | high |
| `WARNING` | medium |
| `INFO` | low |

## SonarQube

| Tool-native | Normalized |
|---|---|
| `BLOCKER` | high |
| `CRITICAL` | high |
| `MAJOR` | medium |
| `MINOR` | low |
| `INFO` | low |

## Edge cases

- Tool-native severity not in the table → default to `medium`. The adapter logs a one-line warning to stderr so operators notice.
- Tool emits no severity at all → default to `medium`.
- New severity levels added by tool upstream → add a row here when adding the adapter version that uses them.

## Why this mapping

Shield's normalization is deliberately coarse (3 levels). Reasons:
- Cross-tool aggregation needs a common scale; finer granularity is tool-specific
- Reports are read by humans who scan for "is this a problem now?" — a binary-ish severity is more useful than a 5-point scale
- Severity calibration is the user's responsibility per their codebase; shield doesn't try to be authoritative
