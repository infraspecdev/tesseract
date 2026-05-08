# Semgrep SAST Adapter

LLM-readable contract for the Semgrep adapter. The Python runtime that executes this contract lives at `adapter.py`.

## What this adapter does

Runs Semgrep against the target codebase using shield's bundled Spring 3.x rule pack (or a user-overridden config), parses the `--json` output, and returns normalized findings to `backend-reviewer`.

## Configuration

In `.shield.json`:

```json
{
  "sast": {
    "adapters": ["semgrep"],
    "semgrep": {
      "config": "p/spring-boot-best-practices",
      "output_path": "target/semgrep-output.json"
    }
  }
}
```

| Key | Required | Default | Description |
|---|---|---|---|
| `config` | no | `shield/adapters/sast/semgrep/rules/` | Path or registry pack ID for Semgrep rules |
| `output_path` | no | (none) | Path to a pre-existing `semgrep --json` output file. Adapter will consume this if mtime is newer than HEAD commit. |

No credentials required. Optional `SEMGREP_APP_TOKEN` env var (for Semgrep Cloud) is honored by Semgrep itself; shield's adapter doesn't reference it.

## Layered fallback

1. **Consume existing output.** If `config.output_path` is set and the file's mtime is newer than HEAD commit time, parse it.
2. **Invoke locally.** If `semgrep` is on PATH, run `semgrep --config <rules> --json --quiet <target_path>` with a 120-second timeout.
3. **Best-effort skip.** If neither is possible, return zero findings with note: `"semgrep adapter — tool not available; SAST coverage best-effort. Install with `pip install semgrep` to enable."`

## Severity mapping

| Semgrep | shield |
|---|---|
| ERROR | high |
| WARNING | medium |
| INFO | low |

## v1 limitation: Spring Boot 3.x only

Bundled rules at `rules/spring-*.yml` target Spring Boot 3.x patterns:
- `csrf(csrf -> csrf.disable())` lambda DSL (SS6); will not match SB2's `csrf().disable()` chained DSL
- `@RequestMapping` with `jakarta.*` imports

Spring Boot 2.x patterns will not be flagged by these rules. To add SB2 coverage, follow Pattern A (broaden) per `EXTENDING-VERSIONS.md` — add a parallel set of patterns to each rule's `pattern-either` block, OR ship a sibling `spring-*-sb2.yml` rule pack.

## Behavior on unparseable output

If `semgrep --json` returns malformed JSON (rare but possible during interrupted runs), the adapter logs the error to its `note` field and returns zero findings. Don't fail the review.

## Testing

Parser tests at `tests/test_adapter.py` use captured fixtures (`tests/fixtures/*.json`). To regenerate fixtures, run Semgrep against the spring-boot-api fixture:

```bash
semgrep --config shield/adapters/sast/semgrep/rules \
        --json --quiet \
        shield/examples/spring-boot-api > \
        shield/adapters/sast/semgrep/tests/fixtures/spring-boot-api-output.json
```

The bundled rule packs themselves can be self-tested via `semgrep --test rules/`. Each rule pack ships with a `<name>.test.java` example that triggers the rule (and a `<name>.test.java` no-trigger negative case if needed).

## Related

- See `../README.md` for the framework overview
- See `../finding-schema.md` for the normalized finding shape
- See `../severity-mapping.md` for the full severity table
