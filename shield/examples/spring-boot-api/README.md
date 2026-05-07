# spring-boot-api — Backend Review Test Fixture

A small Spring Boot 3.x service used to RED-GREEN test the skills under `shield/skills/backend/`. Every source file in this fixture contains intentional violations matched to specific skills. The contract between violations and skills lives in `docs/expected-findings.md`.

**This fixture is not a runnable application** — it is reference code with deliberate bugs. Do not deploy it.

## Layout

```
src/main/java/com/example/api/
  ├── ApiApplication.java        — Spring Boot entry point
  ├── controller/                — REST controllers (api-design, error-observability)
  ├── service/                   — Business logic (code-quality, concurrency)
  ├── repository/                — JPA repositories (database)
  ├── model/                     — Entities (database)
  ├── config/                    — App + Security config (deployment-safety)
  └── exception/                 — Exception handlers (error-observability)
src/main/resources/
  ├── application.yml            — Config (deployment-safety)
  └── db/migration/              — Flyway migrations (database, deployment-safety)
src/test/java/com/example/api/   — Tests (testing-strategy)
```

## Adding new violations

When adding a new violation:
1. Place it in the file most natural for that violation type.
2. Add a row to `docs/expected-findings.md` with the file path, line range, skill name, and expected severity.
3. Re-run the relevant skill's GREEN test to confirm it catches the new finding.

See `docs/expected-findings.md` for the full inventory of intentional bugs.
