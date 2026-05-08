# SonarQube Community SAST Adapter

LLM-readable contract for the SonarQube adapter. The Python runtime that executes this contract lives at `adapter.py`.

## What this adapter does

Consumes findings from a SonarQube Community Edition server. By default the adapter does NOT invoke `sonar-scanner` locally (full scans take minutes); it expects the user to run scans in CI and reads the results via REST API.

## Configuration

In `.shield.json`:

```json
{
  "sast": {
    "adapters": ["sonarqube"],
    "sonarqube": {
      "consume_path": "target/sonarqube-issues.json"
    }
  }
}
```

| Key | Required | Default | Description |
|---|---|---|---|
| `consume_path` | no | (none) | Path to a pre-fetched SonarQube REST API response. Mtime-checked against HEAD commit. |

In `~/.shield/credentials.json`:

```json
{
  "sonarqube": {
    "url": "https://sonar.example.com",
    "token": "...",
    "project_key": "my-project"
  }
}
```

Env var fallback (used if any credential is missing in the file): `SHIELD_SONAR_URL`, `SHIELD_SONAR_TOKEN`, `SHIELD_SONAR_PROJECT_KEY`.

## Layered fallback

1. **Consume `consume_path` file** if its mtime is newer than HEAD commit time.
2. **Fetch via REST API** at `{url}/api/issues/search?componentKeys={project_key}&statuses=OPEN,REOPENED,CONFIRMED` using credentials.
3. **Invoke `sonar-scanner`** locally if credentials are configured AND `sonar-scanner` is on PATH (slow, last resort). After scan, fetch via API.
4. **Best-effort skip** if no path forward (no consumable file, no working API, no scanner).

## Severity mapping

| SonarQube | shield |
|---|---|
| BLOCKER | high |
| CRITICAL | high |
| MAJOR | medium |
| MINOR | low |
| INFO | low |

## Category derivation

SonarQube issue `type` field:
- `VULNERABILITY`, `SECURITY_HOTSPOT` → `security`
- `BUG` → `reliability`
- `CODE_SMELL` → `code-quality`
- Any other → `code-quality` (default)

## Stale output handling

`consume_path` mtime older than HEAD commit time → treat as missing, fall through to API fetch. The user's CI scan was older than their latest commit; trust live API over stale report.

## Branch analysis

SonarQube Community Edition does NOT support branch analysis (Developer Edition feature). All findings cover the whole project regardless of which branch the user is reviewing. The aggregator surfaces SAST findings in a "Repo-wide SAST findings" section to make this clear.

## Authentication notes

SonarQube uses HTTP Basic auth with the token as the username (and an empty password): `Authorization: Basic base64(token + ":")`. The adapter handles this; users only provide the raw token.

## Behavior on unreachable server

If the API is unreachable (network error, server down, 401), the adapter logs the error in its `note` field and returns zero findings. Doesn't fail the review.

## Sample sonar-project.properties

`examples/sonar-project.properties` is a reasonable baseline for a Spring Boot 3 project. Copy to your project root and adjust the `sonar.projectKey` etc.

## Testing

Parser tests at `tests/test_adapter.py` use captured fixtures (`tests/fixtures/*.json`). To regenerate fixtures, hit the API with curl:

```bash
curl -u "$SHIELD_SONAR_TOKEN:" \
  "$SHIELD_SONAR_URL/api/issues/search?componentKeys=$SHIELD_SONAR_PROJECT_KEY&ps=10" > \
  shield/adapters/sast/sonarqube/tests/fixtures/sample-issues.json
```

## Related

- See `../README.md` for the framework overview
- See `../finding-schema.md` for the normalized finding shape
- See `examples/sonar-project.properties` for a recommended scanner config
