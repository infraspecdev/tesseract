# Getting Started with Shield SAST Adapters

This guide walks you from "shield works skill-only" to "shield runs SAST tools alongside skills."

## TL;DR

```bash
# 1. Install Semgrep (lightest tool to start)
pip install semgrep

# 2. Edit your repo's .shield.json to opt in
echo '{
  "project": "my-project",
  "sast": { "adapters": ["semgrep"] }
}' > .shield.json

# 3. Run shield review
/review-backend
```

That's it. SAST runs automatically on the next `/review-backend` invocation.

## Adding SonarQube

SonarQube Community is heavier — it requires a self-hosted server. If your team already runs SonarQube in CI, configure shield to consume the existing scans:

### One-time setup

1. Get a token: in SonarQube, Account → Security → Generate Token
2. Configure credentials at `~/.shield/credentials.json`:
   ```json
   {
     "clickup":   { "api_token": "..." },
     "sonarqube": {
       "url": "https://sonar.your-company.com",
       "token": "<token from step 1>",
       "project_key": "<your project's sonar key>"
     }
   }
   ```
   (Permissions: `chmod 600 ~/.shield/credentials.json`)

3. Add `sonarqube` to your repo's `.shield.json`:
   ```json
   {
     "project": "my-project",
     "sast": {
       "adapters": ["semgrep", "sonarqube"]
     }
   }
   ```

### Verifying

```bash
# Quick sanity check the credentials work
curl -u "$SHIELD_SONAR_TOKEN:" \
     "$SHIELD_SONAR_URL/api/projects/search?projects=$SHIELD_SONAR_PROJECT_KEY"
```

Should return a JSON object with your project metadata. If 401, the token is wrong; if 404, the project_key is wrong; if connection refused, the URL is wrong.

## Configuration reference

`.shield.json` `sast` block:

```json
{
  "sast": {
    "adapters": ["semgrep", "sonarqube"],
    "semgrep": {
      "config": "p/spring-boot-best-practices",
      "output_path": "target/semgrep-output.json"
    },
    "sonarqube": {
      "consume_path": "target/sonarqube-issues.json"
    }
  }
}
```

All keys under each adapter are optional. Defaults:
- Semgrep `config`: shield's bundled rule pack at `shield/adapters/sast/semgrep/rules/`
- Semgrep `output_path`: none (always invoke locally)
- SonarQube `consume_path`: none (fetch via API)

## Suppression

Use the tool's native suppression:

- **Semgrep:** `// nosemgrep: <rule_id>` on the offending line
- **SonarQube:** `@SuppressWarnings("java:S1234")` on the method/class, or mark the issue "Won't Fix" in the SonarQube UI

shield does not provide its own suppression mechanism in v1. If SAST output becomes too noisy, consider:
1. Disabling specific rules at the tool level (Semgrep: edit your rule pack; SonarQube: adjust your Quality Profile)
2. Removing the adapter from `sast.adapters` if the noise outweighs the value

## What if a tool isn't installed?

The adapter emits a one-line "best-effort" note in the report header and continues. The review still completes; you just don't get that adapter's findings.

Example output header when only Semgrep is installed:

```
**SAST adapters:** semgrep (invoked, 8 findings) · sonarqube (unavailable: credentials missing)
```

## Reading the output

Findings appear in two places:

1. **Inside module sections** — when SAST and skills both flag the same file:line area, the entry shows `source: "skill+semgrep"` (or whichever combination). Both sources caught it; treat as a confirmed issue.
2. **"Repo-wide SAST findings" section** — SAST-only findings (no skill overlap). These cover the whole repo, not just changed files, since SonarQube Community doesn't do branch analysis.

The summary at the bottom shows a breakdown:
```
- Total findings: 73 (skill: 38, SAST-skill-overlap: 8, SAST-only: 27)
```
"SAST-only" tells you how much value SAST added beyond what skills caught.

## Adding a new adapter

See `shield/adapters/sast/README.md`. Implement the `adapter.run(target_path, config, head_commit_time)` contract defined in `finding-schema.md`, write parser tests against captured fixtures, and add the adapter name to your `.shield.json`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `semgrep adapter — tool not available` | Semgrep not in PATH | `pip install semgrep` |
| `sonarqube adapter — credentials missing` | No `~/.shield/credentials.json` and no env vars | Set up credentials per "One-time setup" above |
| `sonarqube adapter — API fetch failed: 401` | Wrong token | Regenerate the token in SonarQube and update credentials.json |
| `sonarqube adapter — API fetch failed: 404` | Wrong project_key | Find the project's actual key in the SonarQube UI under Project Settings |
| `mtime stale → re-fetched` in header | Existing output is older than HEAD commit | This is expected behavior; adapter automatically refetched |
| SAST finds 200+ noisy CODE_SMELL findings | Quality profile too broad | Tune your SonarQube Quality Profile to focus on Bugs + Vulnerabilities |
| Same finding appears twice in report | Dedup edge case | Check that the file paths match exactly; SonarQube prefixes paths with `project_key:` and our adapter strips this — file a bug if dedup misses |
