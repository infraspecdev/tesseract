# Shield — Backend Domain Design

**Status:** Draft
**Date:** 2026-05-07
**Marketplace:** Tesseract
**Plugin:** Shield
**Target version:** 2.9.0

## Context

Tesseract today is infrastructure-heavy. Shield's domain skills cover Terraform, Atmos, Kubernetes, and GitHub Actions — but there is no first-class support for backend application code. This spec adds a **backend domain** to Shield that delivers:

- Language- and framework-agnostic review skills covering common software-engineering practices (SOLID, API design, testing strategy, database, error/observability, deployment safety, concurrency).
- Framework-specific review skills for Java/Kotlin Spring Boot in v1, with Python, Node/TypeScript, and Go scoped as follow-on iterations.
- A new `backend-reviewer` agent that performs stack detection, loads the right skills, and dispatches cross-cutting concerns to existing specialist agents.
- Integration with the existing `/plan`, `/plan-review`, `/implement`, and `/review` commands so backend skills inform the full SDLC, not only post-hoc review.

## Goals

- Make Shield equally useful for backend repos as it is for infrastructure repos.
- Reuse existing patterns (kubernetes domain layout, agent specialization, skill structure) rather than introducing new conventions.
- Detect language/framework automatically from the repo; fall back to a user prompt only when the repo is greenfield.
- Ship v1 (foundations + Java/Kotlin) before adding Python/Node/Go to validate the pattern incrementally.

## Non-goals

- Cross-module/cross-service checks (version drift, shared API contract drift) — repo-level concerns, deferred to a follow-on after v1.
- Implementation help for new frameworks (scaffolding, code generation). The skills review existing or in-progress code; they do not generate new services.
- AWS- or cloud-specific operational review on backend code — that remains in `well-architected-reviewer` and infra skills.
- Persisted greenfield stack choice — the agent re-asks each run unless the user manually pins it via `.shield.json`.

## Pipeline integration

```
/plan          ─►  load relevant backend skills (NEW domain-detection step)
/plan-review   ─►  dispatch backend-reviewer (NEW reviewer in auto-detect list)
/implement     ─►  per-step domain hook runs backend skill checks (extended hook)
/review        ─►  domain-skill list now includes backend (extended list)
/review-backend─►  backend-only fast path (NEW command)
```

The backend domain is loaded by the same hooks that already load `terraform`, `atmos`, and `kubernetes` skills. The `/plan` change is broader than backend — it fixes a pre-existing gap where `/plan` does no domain-aware skill loading at all.

**Skills as context vs as checks.** The same skill body serves two roles depending on which command loads it:

- In `/plan` and `/implement`, skills are **context** — their principles inform what stories to write, what acceptance criteria to require, what tests to plan, and what code to produce. They are not run as gating checks.
- In `/plan-review` and `/review` (and `/review-backend`), skills are **checks** — agents evaluate the artifact (plan or code) against the skill's rubric and produce findings.
- In `/implement`'s per-step lightweight review (`implement-feature` Phase 5c), skills run as a quick check on the just-written diff. Not a full agent review — fast feedback during TDD.

Each `SKILL.md` should be written so the same body is usable in both modes; the loading command decides whether to apply it as guidance or as a rubric.

## Architecture & data flow

```
User runs: /review-backend [optional path]
       │
       ▼
┌────────────────────────────────────────┐
│   review-backend command               │
│   - Resolves target path / scope       │
│   - Invokes backend-reviewer agent     │
└────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│   backend-reviewer agent               │
│                                        │
│   1. Stack detection (per file)        │
│      ├── pom.xml | build.gradle*       │
│      │   → Java/Kotlin                 │
│      ├── pyproject.toml | reqs.txt     │
│      │   → Python (v2+, agnostic only) │
│      ├── package.json                  │
│      │   → Node/TS  (v3+, agnostic)    │
│      ├── go.mod                        │
│      │   → Go       (v4+, agnostic)    │
│      └── none → greenfield → ask user  │
│                                        │
│   2. Skill loading                     │
│      ├── ALWAYS load 7 agnostic skills │
│      └── IF Java/Kotlin: load Spring   │
│           skills conditionally on the  │
│           sub-markers in pom/gradle    │
│                                        │
│   3. Review execution                  │
│      ├── Apply skills to in-scope      │
│      │   files (diff or whole tree)    │
│      └── Dispatch to specialists for   │
│          cross-cutting concerns:       │
│           ├── security-reviewer        │
│           ├── architecture-reviewer    │
│           ├── agile-coach-reviewer     │
│           ├── operations-reviewer      │
│           ├── dx-engineer-reviewer     │
│           └── product-manager-reviewer │
│              (only when story context  │
│              available from plan.json) │
│                                        │
│   4. Aggregate findings                │
│      └── Group by module (monorepo)    │
│          + write per-agent detailed    │
│          findings + summary.md         │
└────────────────────────────────────────┘
```

`cost-reviewer`, `well-architected-reviewer`, and `kubernetes-reviewer` are intentionally excluded from the dispatch list — they are infra-flavored.

## Component inventory

### New files

```
shield/skills/backend/
  ├── code-quality-review/SKILL.md
  ├── api-design-review/SKILL.md
  ├── testing-strategy-review/SKILL.md
  ├── database-review/SKILL.md
  ├── error-observability-review/SKILL.md
  ├── deployment-safety-review/SKILL.md
  ├── concurrency-review/SKILL.md
  ├── spring-web/SKILL.md
  ├── spring-data/SKILL.md
  ├── spring-config/SKILL.md
  ├── spring-security/SKILL.md
  ├── spring-test/SKILL.md
  └── jvm-language-review/SKILL.md
shield/agents/backend-reviewer.md
shield/commands/review-backend.md
shield/examples/spring-boot-api/         (test fixture; intentional violations)
  ├── pom.xml
  ├── src/main/java/...
  ├── src/test/java/...
  └── docs/expected-findings.md          (RED-GREEN oracle)
```

### Modified files

| File | Change | Why |
|---|---|---|
| `shield/commands/review.md` | Add `backend` to the domain-skill list | `/review` auto-loads backend skills |
| `shield/skills/general/implement-feature/SKILL.md` | Extend per-step domain hook to include `backend` | `/implement` runs backend checks during TDD |
| `shield/commands/plan.md` | Add domain-detection step + skill-loading guidance | Fixes pre-existing gap; `/plan` becomes domain-aware |
| `shield/commands/plan-review.md` | Register `backend-reviewer` in auto-detect reviewer list | `/plan-review` picks up backend plans |
| `.claude-plugin/marketplace.json` | Bump shield to `2.9.0` | Per CLAUDE.md versioning rules |

## Skill scopes

### Agnostic skills

| Skill | Checks |
|---|---|
| `code-quality-review` | SOLID violations (god objects, fat interfaces, leaky abstractions); DRY/KISS/YAGNI smells; naming clarity; cohesion/coupling at the type level |
| `api-design-review` | REST/GraphQL contracts: resource modeling, idempotency of mutations, versioning strategy, error response shape, status code semantics, pagination/filtering |
| `testing-strategy-review` | Test pyramid balance, fixture/mock placement, contract-vs-implementation tests, flaky-test patterns, coverage focus on critical paths |
| `database-review` | Schema design (normalization, FKs, index strategy), migration safety (zero-downtime, additive-only), N+1 detection, transaction boundary placement |
| `error-observability-review` | Error type hierarchy/propagation, exception-as-control-flow anti-patterns, log structure/levels, metric instrumentation gaps, trace context, correlation IDs |
| `deployment-safety-review` | Feature-flag readiness for risky changes, backwards-compatible API/schema evolution, rollback paths, blast-radius scoping, multi-instance safety |
| `concurrency-review` | Race conditions, lock granularity/scope, async/await pitfalls (missed await, fire-and-forget exception loss), retry idempotency, shared state without sync |

### Spring/JVM skills

| Skill | Checks |
|---|---|
| `spring-web` | `@RestController` patterns, validation (`@Valid`, JSR-303), `@ExceptionHandler`/`@ControllerAdvice` consistency, `ResponseEntity` shape, content negotiation, request mapping clarity |
| `spring-data` | JPA entity design (lazy-vs-eager, fetch joins, equals/hashCode), `@Transactional` placement and propagation, N+1 in JPQL, cascading |
| `spring-config` | `application.yml` profiles and overrides, `@Configuration`/`@Bean` lifecycle, `@ConditionalOn*` correctness, `@ConfigurationProperties` binding, secrets-in-config |
| `spring-security` | `SecurityFilterChain` configuration, authentication providers, JWT/OAuth2 wiring, method-level security (`@PreAuthorize`), CSRF/CORS, password encoder selection |
| `spring-test` | Test slice selection (`@SpringBootTest` vs `@WebMvcTest` vs `@DataJpaTest`), `@MockBean` overuse, Testcontainers vs H2 trade-offs, `@DirtiesContext` hygiene, parallel test safety |
| `jvm-language-review` | Java idioms (records, sealed types, immutability, exception design); Kotlin idioms (null safety, `data class`, sealed classes, scope functions, coroutine launching/cancellation) |

Full check details and severity rubrics are written into each `SKILL.md` during implementation.

## Stack detection

### Marker files (priority order)

| Marker | Stack | v1 framework skills |
|---|---|---|
| `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle*` | Java/Kotlin | Spring/JVM skills (conditional sub-detection) |
| `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile` | Python | none (agnostic only; v2 ships framework skills) |
| `package.json` | Node/TS | none (agnostic only; v3 ships framework skills) |
| `go.mod` | Go | none (agnostic only; v4 ships framework skills) |
| None + non-empty repo | Unknown stack | agnostic only + warn |
| None + near-empty repo (≤5 source files, configurable) | Greenfield | ask user |

### Conditional Spring skill loading

Within Java/Kotlin detection, sub-markers in `pom.xml`/`build.gradle*` decide which Spring skills load:

| Sub-marker | Skill activated |
|---|---|
| `org.springframework.boot` | `spring-web`, `spring-config` (default for any Spring Boot app) |
| `spring-boot-starter-data-*` | `spring-data` |
| `spring-boot-starter-security` | `spring-security` |
| Test code present + Spring Boot test starter | `spring-test` |
| Kotlin source files (`.kt`) | `jvm-language-review` weighted toward Kotlin |
| Pure Java | `jvm-language-review` weighted toward Java |
| Non-Spring JVM (Quarkus, Micronaut, plain JVM) | `jvm-language-review` only; emit note |

### Greenfield prompt

```
This looks like a greenfield repo. Which stack are you targeting?

  [a] Java/Kotlin (Spring Boot)
  [b] Python — framework-specific review not yet available; agnostic only
  [c] Node.js / TypeScript — framework-specific review not yet available; agnostic only
  [d] Go — framework-specific review not yet available; agnostic only
  [e] Other / not yet decided — agnostic only

Or skip stack-specific review for this run: type "skip"
```

The user's choice is treated identically to a positive detection. It is **not** persisted by default; the agent re-asks on each greenfield run unless the user manually pins it via `.shield.json`.

## Monorepo handling

### Scope resolution (priority order)

| Invocation | Scope |
|---|---|
| `/review-backend services/api/` | Subtree at the given path |
| `/review-backend` (no arg, on a branch) | Changed files vs `main` (git diff) — default for PR review |
| `/review-backend --full` or `/review-backend .` | Whole repo — periodic audit / onboarding |

### Per-file marker resolution

For each in-scope file, walk **up** the directory tree to the first stack-marker. That marker determines which framework skills apply. Agnostic skills apply to every file. If the walk reaches the repo root with no marker, the file is "unknown stack" → agnostic only + per-file warning.

This matches Maven/Gradle/Yarn-workspace inheritance semantics: a file inherits its owning module's config.

### Excluded paths (default, configurable in `.shield.json`)

```
node_modules/  target/  build/  dist/  out/  .gradle/  .mvn/
__pycache__/  .venv/  vendor/  .git/  .worktrees/  .superpowers/
```

### Output grouped by module

Findings are organized by module so users can see which service produced what:

```
backend-reviewer findings (3 modules detected)

services/api/ (Java/Kotlin · Spring Boot · Spring Security · Spring Data)
  ├── api-design-review:        2 findings (1 high, 1 medium)
  ├── spring-web:               1 finding  (medium)
  └── testing-strategy-review:  1 finding  (low)

services/worker/ (Java/Kotlin · Spring Boot, no Spring Data)
  ├── concurrency-review:       3 findings (2 high, 1 medium)
  └── error-observability-review: 1 finding (medium)

frontend/ (Node/TS — framework-specific review ships in v3)
  └── code-quality-review:      1 finding (low)
```

This integrates with the existing `/review` output writer at `{output_dir}/{feature}/code-review/{N}-{slug}/summary.md`. Module grouping becomes a section structure in the markdown.

### Edge cases

| Case | Behavior |
|---|---|
| Multiple markers walking up (nested Maven projects) | Use the nearest (deepest) marker |
| Multiple stacks at same directory level (e.g., `pom.xml` AND `package.json`) | Multi-stack module — apply skills from both stacks |
| Path arg points outside any module | Scope to the path; treat as unknown-stack (agnostic only) |
| Git submodules | Out of scope for v1 explicit handling; treated as normal directories |
| Empty diff (no changed files) | Print "no changes to review" and exit; no fall-through to whole-repo |

## Error handling

| Failure mode | Behavior |
|---|---|
| Detection finds no markers in non-empty repo | Agnostic only; emit "unknown stack — framework review unavailable" |
| User declines greenfield prompt (`skip`) | Run agnostic only, no further prompts |
| Specialist agent dispatch fails | Continue review; note dispatch failure in report; don't block other findings |
| Skill produces zero findings | Skip in output (no empty sections) |
| Scope reduces to zero files (excluded paths cover everything) | Print "no reviewable files in scope" and exit cleanly |
| Java detected but no Spring deps | Load `jvm-language-review` only; emit note that Spring skills do not apply |

## Test strategy (RED-GREEN)

CLAUDE.md mandates RED-GREEN testing for every new skill. The plan:

- **Single shared fixture.** `shield/examples/spring-boot-api/` is one Spring Boot service with intentional violations spanning all 13 skills. Each skill exercises the bugs it cares about.
- **RED phase** — subagent reviews the fixture *without* the skill loaded. Document what gets caught anyway by general agents — that is the baseline.
- **GREEN phase** — subagent reviews the fixture *with* the skill loaded. Must catch all skill-specific findings and grade severity correctly.
- **REFACTOR** — gaps in GREEN trigger skill edits + re-test.
- **Total runs:** 13 skills × (RED + GREEN) = 26 minimum.
- **Oracle:** `shield/examples/spring-boot-api/docs/expected-findings.md` lists every intentional violation, the skill that should catch it, and expected severity.

## v1 deliverable summary

- 13 new skills (7 agnostic + 6 Spring/JVM)
- 1 new agent (`backend-reviewer`)
- 1 new command (`/review-backend`)
- 1 new fixture (`spring-boot-api`)
- 4 modified files (`/review`, `/plan`, `/plan-review`, `implement-feature`)
- 1 marketplace bump (shield 2.8.0 → 2.9.0)
- 26 RED-GREEN test runs

## Out of scope (deferred to follow-on iterations)

- **v2** — Python framework skills (FastAPI, Django, Flask) on top of the agnostic core. Reuse `examples/python-api/` as fixture.
- **v3** — Node/TS framework skills (Express, NestJS, Next.js API). New fixture required.
- **v4** — Go framework skills (net/http, Gin, Echo). New fixture required.
- **Cross-module checks** — version drift across multiple `pom.xml`, shared API contract drift, dependency-hygiene rollups. Different skill shape (repo-level not file-level); deferred.
- **Persisted greenfield choice** — auto-write user's stack pick to `.shield.json`. Manual pin only in v1.
- **Other Spring concerns** — `spring-actuator`, `spring-async`, `spring-aop`, `spring-cloud`. Lower frequency; layer in incrementally as needs surface.
- **Cost review for backend code** — Spring/Java cost concerns (connection pools, executor sizing, etc.) deferred; current `cost-reviewer` agent stays infra-flavored.

## Versioning notes

Per `CLAUDE.md`:

- Bump `shield` version to `2.9.0` in `.claude-plugin/marketplace.json`.
- Do **not** add a `version` field to `shield/.claude-plugin/plugin.json` — the marketplace value wins for relative-path plugins.
- Shield has no `pyproject.toml` at the plugin root, so no pyproject bump is needed for shield itself.
