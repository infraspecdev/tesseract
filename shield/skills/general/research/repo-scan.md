# Research Phase 1 — Repo Scan

Silent scan of the current repository to detect technical context before asking the user any questions. Findings surfaced for user confirmation/correction.

## Confidence tags

Each detected entry is tagged with a marker:

| Tag | Meaning |
|---|---|
| `(detected)` | Shield inferred from the repo; user has not confirmed or corrected |
| `(confirmed)` | Shield detected AND user said "yes" during confirmation step |
| `(corrected by user)` | Shield's initial guess was wrong; this is the user's correction |
| `(manual)` | User added during the confirmation step; Shield did not detect |

## Categories scanned

### Stack

Detection by file presence in the repo root or `src/` directory:

| File | Inferred stack |
|---|---|
| `package.json` (no Python markers nearby) | Node + JavaScript or TypeScript |
| `tsconfig.json` alongside `package.json` | Node + TypeScript |
| `pom.xml` | Java + Maven |
| `build.gradle` or `build.gradle.kts` | Java/Kotlin + Gradle |
| `pyproject.toml` | Python (poetry / hatch / similar) |
| `requirements.txt` (no pyproject) | Python (pip) |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `*.csproj` or `*.fsproj` | .NET |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `mix.exs` | Elixir |

Report each as: `<Stack> (detected) — *from <file>*`.

### Integrations

Detection by package dependencies + config files:

| Source | Inferred integration |
|---|---|
| `node_modules` or `package.json` deps containing `passport-*`, `auth0`, `firebase-admin` | Auth provider |
| Deps containing `@stripe/*`, `paypal-*` | Payment provider |
| Deps containing `pg`, `mysql2`, `mongodb`, `redis` | Datastore |
| Deps containing `bull`, `kafkajs`, `amqplib` | Message queue |
| Deps containing `@aws-sdk/*`, `gcp-*`, `azure-*` | Cloud provider |
| `docker-compose.yml` services | Runtime services (Postgres, Redis, etc.) |
| `helm/values.yaml` or `kustomization.yaml` | K8s deployment |
| `.env.example` keys mentioning auth/secret names | Inferred auth integrations |

Report as: `<Integration name> (detected) — *from <source>*`.

### Compliance markers

Search `CLAUDE.md`, `README.md`, `SECURITY.md`, `docs/` for these terms (case-insensitive):

| Keyword | Inferred compliance |
|---|---|
| `SOC2` | SOC 2 |
| `GDPR` | GDPR |
| `CCPA` | CCPA |
| `HIPAA` | HIPAA |
| `PCI-DSS` or `PCI DSS` | PCI-DSS |
| `RBI` | RBI (India payment regulation) |
| `DPDP` | DPDP (India data protection) |
| `PDPL` | PDPL (UAE / Saudi data protection) |

Report each as: `<Compliance> (detected) — *mentioned in <file>*`.

### Deployment / rollout pattern

| Source | Inferred pattern |
|---|---|
| `.github/workflows/deploy.yml` containing `canary`, `blue-green`, `rolling` | Inferred deployment strategy |
| `helm/values.yaml` containing canary stanza | Canary rollout |
| `argo-cd-app.yaml` or `Application.yaml` | ArgoCD |
| `.github/workflows/*.yml` with `terraform plan` | Terraform / Atmos |
| `CLAUDE.md` or `README.md` mentioning `helm`, `ArgoCD`, `canary`, `blue-green`, `kubernetes`, `k8s` | Deployment context noted in project docs |

Report as: `<Pattern> (detected) — *from <workflow file or doc>*`.

### Recent activity

```bash
# Last 20 commits in touched paths
git log --oneline -20 --name-only | head -50
```

From this output, surface:
- Most recently touched directories
- Most active contributors (by commit count) in the inferred feature area

Report as: `<dir>: <N> commits last 30 days, mostly @<user> (confirmed) — *git log*`.

### Past decisions / ADRs

Glob `docs/decisions/*.md`, `docs/adr/*.md`, `**/ADR-*.md`. For each, surface:
- ADR number
- Title
- One-line summary

Report as: `ADR-001: <title> — <one-line>`.

### Prior Shield artifacts

Glob `{output_dir}/{feature}/research/*/transcript.md` and `{output_dir}/{feature}/research/*/findings.md`. If any exist:
- Note that prior research has been done
- Read the most recent transcript to carry forward context

## Output format in transcript.md

Render as a `## Detected Context` section at the top of `transcript.md`:

```markdown
## Detected Context

### Stack
- Node.js + TypeScript (confirmed) — *from package.json + tsconfig.json*
- PostgreSQL (confirmed) — *from docker-compose.yml services*

### Integrations
- passport-google-oauth20 (confirmed) — *existing OAuth provider in package.json*
- Redis (detected) — *Redis service in docker-compose.yml*

### Compliance markers
- SOC2 (confirmed) — *mentioned in CLAUDE.md*
- GDPR (corrected by user) — *Shield missed; user added "EU users in scope"*

### Deployment pattern
- Helm + ArgoCD (confirmed) — *helm/ + .github/workflows/argo-sync.yml*
- Canary rollout (confirmed) — *helm/values.yaml has canary stanza*

### Recent activity
- src/auth/: 8 commits last 30 days, mostly @ashwinimanoj (confirmed) — *git log*

### Past decisions / ADRs
- ADR-001: Use Postgres for transactional data (2025-09-12)
- ADR-002: Adopt strangler pattern for v2 migration (2026-01-15)

### Prior Shield artifacts
- Prior research transcript at research/1-platform-foundations/transcript.md (2026-04-30)
```

## Performance budget

Scan must complete in ≤ 30 seconds for a typical repo. If scan exceeds 30s, skip lower-priority categories (Past decisions, Prior artifacts) and proceed with confirmed Stack + Integrations only.

## Failure modes

- **Empty repo / no manifests** — emit `## Detected Context` with the note "No technical context detected; proceeding with manual Q&A only."
- **Permission errors reading files** — skip that file silently; continue with others
- **Git not available** — skip Recent activity category
