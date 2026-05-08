# Shield Backend Domain — Plan 2: Spring/JVM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Java/Kotlin Spring Boot framework-specific layer of the shield backend domain — 6 skills covering Spring web/data/config/security/test concerns plus JVM language idioms, conditional Spring sub-detection in the `backend-reviewer` agent, and Spring-specific fixture violations layered onto the existing `spring-boot-api` test fixture from Plan 1.

**Architecture:** Build on Plan 1's foundation. The skill files go under `shield/skills/backend/` alongside the 7 agnostic skills shipped in Plan 1. The agent's stack-detection logic gets extended with sub-marker checks (Spring Boot dependencies in `pom.xml`/`build.gradle*`) so that Spring skills load only when Spring Boot is detected. The Spring-Boot test fixture grows with new files (`SecurityConfig.java`, `OrderProcessingService.java`, `application-prod.yml`, etc.) and additional violations for the existing files where natural.

**Tech Stack:** Markdown skills/agents/commands. Spring Boot 3.2 (Java 17). Existing `spring-boot-api` Maven fixture from Plan 1.

---

## Scope of this plan (Plan 2)

**In scope:**
- 6 Spring/JVM skills:
  - `spring-web` — `@RestController` patterns, `@ExceptionHandler`/`@ControllerAdvice`, `@Valid`, `ResponseEntity`, request mapping clarity, content negotiation
  - `spring-data` — `@Transactional` placement and propagation, self-invocation, JPQL fetch strategies, `@Modifying`, repository patterns, equals/hashCode on entities
  - `spring-config` — `@ConfigurationProperties`, profiles (`application-{profile}.yml`), `@ConditionalOn*`, `@Bean` lifecycle, secrets-in-config
  - `spring-security` — `SecurityFilterChain`, password encoder (BCrypt vs NoOp), CSRF/CORS, method-level security (`@PreAuthorize`), session management
  - `spring-test` — Test slice selection (`@SpringBootTest` vs `@WebMvcTest` vs `@DataJpaTest`), `@MockBean` overuse, Testcontainers vs H2, `@DirtiesContext`
  - `jvm-language-review` — Java idioms (records, sealed types, immutability, var, Optional, exception design); Kotlin coverage in skill text only (Kotlin fixture deferred to follow-on)
- Conditional Spring sub-detection in `shield/agents/backend-reviewer.md` (sub-markers: `org.springframework.boot`, `spring-boot-starter-data-*`, `spring-boot-starter-security`, `spring-boot-starter-test`)
- Spring-specific fixture additions:
  - `SecurityConfig.java` (new) — Spring Security violations
  - `OrderProcessingService.java` (new) — `@Transactional` violations
  - `AppProperties.java` (new) — `@ConfigurationProperties` violations
  - `application-prod.yml` (new) — secrets-in-config + profile violations
  - `UserController.java` (extend) — Spring-web violations layered onto existing api-design fixture
  - `User.java`, `Order.java` (extend) — equals/hashCode missing, mutability
  - New `ControllerIntegrationTest.java` — Spring-test slice violations
- 28 new oracle rows expected (rough estimate: 5+5+5+5+4+4 across the 6 skills) — exact count locked at Task 8 validation
- Update agent's "v1 framework skills" section to reflect Plan 2 deliverables
- Bump shield to `2.11.0` in `.claude-plugin/marketplace.json`

**Out of scope (Plan 3):**
- `/plan`, `/plan-review`, `/implement` SDLC integrations
- Kotlin-specific RED-GREEN test fixture (skill body covers Kotlin conceptually; fixture-level Kotlin defers to a follow-on)

**Out of scope (post-v1):**
- Spring Cloud, Spring Actuator, Spring AOP, Spring Async — lower frequency, layer in incrementally as needs surface
- Python (v2 of stack rollout), Node/TS (v3), Go (v4)

After Plan 2 ships, `/review-backend` performs Java/Kotlin Spring Boot framework-aware review end-to-end. The agent detects Spring sub-markers in `pom.xml`/`build.gradle*` and loads the relevant Spring skills conditionally.

---

## File structure

**New files (this plan):**

```
shield/skills/backend/
  ├── spring-web/SKILL.md
  ├── spring-data/SKILL.md
  ├── spring-config/SKILL.md
  ├── spring-security/SKILL.md
  ├── spring-test/SKILL.md
  ├── jvm-language-review/SKILL.md
  └── EXTENDING-VERSIONS.md                       (new — extension contract for new SB versions)
shield/examples/spring-boot-api/src/main/java/com/example/api/
  ├── config/SecurityConfig.java                  (new — spring-security)
  ├── config/AppProperties.java                   (new — spring-config)
  └── service/OrderProcessingService.java         (new — spring-data @Transactional)
shield/examples/spring-boot-api/src/main/resources/
  └── application-prod.yml                        (new — spring-config profile + secrets)
shield/examples/spring-boot-api/src/test/java/com/example/api/
  └── controller/UserControllerIntegrationTest.java   (new — spring-test slice violations)
```

**Modified files (this plan):**

| File | Change | Why |
|---|---|---|
| `shield/agents/backend-reviewer.md` | Add conditional Spring sub-detection table; update Skill Loading section to reflect 6 new framework skills | Agent must know which Spring skills apply when Spring Boot deps detected |
| `shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java` | Add Spring-web specific violations alongside existing api-design ones (e.g., field injection, missing `@Valid`) | spring-web skill needs targets distinct from agnostic api-design |
| `shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java` | Add equals/hashCode + mutable getters issue | jvm-language + spring-data targets |
| `shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java` | Mark fields mutable / no equals/hashCode | jvm-language target |
| `shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java` | Add `@Value` usage instead of `@ConfigurationProperties` | spring-config target |
| `shield/examples/spring-boot-api/docs/expected-findings.md` | Append 27 new oracle rows | Spring/JVM skill RED-GREEN tests need entries |
| `.claude-plugin/marketplace.json` | Bump `shield` from `2.10.0` to `2.11.0` | Per `CLAUDE.md` versioning rules |

---

## Conventions used in this plan

- **Each skill is its own task** with the same TDD cycle as Plan 1: add fixture violation → append oracle entries → RED test (subagent without skill) → write SKILL.md → GREEN test (subagent with skill) → refactor if needed → commit.
- **RED/GREEN test runs are dispatched via the `Agent` tool with `subagent_type: general-purpose`, `model: sonnet`.**
- **All file paths are absolute from the repo root** at `/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/` (or whichever worktree is active when execution begins).
- **Commits are per task** unless a step explicitly says "commit at end of step". Use Conventional Commits per existing shield style (`feat(shield):`, `chore:`).
- **Oracle line numbers are approximate.** If actual file lines differ from the oracle by 1-2, adjust the oracle row to match the file before running the GREEN test. Semantic content matches; exact lines do not.
- **Skill severity may grade stricter than oracle.** When the skill's Severity Guide elevates a finding (e.g., flaky tests are always High), prefer the skill's grading and align the oracle to match. Document the deviation in the implementer report.
- **Evaluation point counts are flexible.** Plan 1 found that some skills naturally needed 11 eval points (database-review's D11 for table naming). If during GREEN a finding has no clean home in the prescribed E1–E10 / etc., add an additional eval point rather than forcing a fit.
- **Fixture is intentionally bad code.** Code-quality reviewers should NOT propose fixing the violations — they're the test targets. If a reviewer suggests improvements, push back per `superpowers:receiving-code-review` skill.
- **Plan 1 must be merged or current.** This plan assumes the 7 agnostic skills, `backend-reviewer` agent, and `/review-backend` command from Plan 1 are present.
- **Spring version targeting.** All Spring skills target **Spring Boot 3.x** in v1 (uses `jakarta.*`, Java 17 baseline, lambda-style `SecurityFilterChain` DSL). Each Spring SKILL.md declares its supported versions in the `spring_boot_versions` frontmatter field and includes a "Version Compatibility" section listing version-sensitive checks for SB2.x. The agent detects the Spring Boot major version from `pom.xml`/`build.gradle*` and emits a compat warning when the detected version is outside a skill's declared range. Adding SB2 (or future SB4) coverage follows the contract documented in `shield/skills/backend/EXTENDING-VERSIONS.md` — see Task 1 below for that file's content.
- **Java version targeting (for `jvm-language-review`).** Targets Java 17+ in v1 (matches SB3 baseline). The skill includes a "Java Version Compatibility" section noting which checks (records, sealed types) require which Java level.

---

### Task 1: Update backend-reviewer agent for conditional Spring sub-detection + version detection + extension contract doc

**Files:**
- Modify: `shield/agents/backend-reviewer.md`
- Create: `shield/skills/backend/EXTENDING-VERSIONS.md`

- [ ] **Step 1: Read the current agent file**

Read `shield/agents/backend-reviewer.md`. Locate the "Skill Loading" section and the "Stack Detection" section.

- [ ] **Step 2: Add a "Spring sub-detection" subsection under "Stack Detection"**

After the existing "Greenfield prompt" subsection in `## Stack Detection`, ADD a new subsection. Find this line:

```
Treat the user's reply identically to a positive detection. Do NOT persist the choice — re-ask each greenfield run.
```

After it (before the `---` that ends the Stack Detection section), add:

```markdown

### Spring sub-detection (Java/Kotlin path)

When Java/Kotlin is detected (via `pom.xml`, `build.gradle`, `build.gradle.kts`, or `settings.gradle*`), inspect the dependency declarations to decide which Spring skills apply. Spring skills load only when their corresponding starter is present.

| Sub-marker (in pom.xml or build.gradle*) | Spring skill activated |
|---|---|
| `org.springframework.boot:spring-boot-starter` (or any `spring-boot-starter-*`) | `spring-config` (default for any Spring Boot app) |
| `spring-boot-starter-web` or `spring-boot-starter-webflux` | `spring-web` |
| `spring-boot-starter-data-jpa`, `spring-boot-starter-data-jdbc`, `spring-boot-starter-data-mongodb`, etc. | `spring-data` |
| `spring-boot-starter-security` | `spring-security` |
| `spring-boot-starter-test` (with test source files present) | `spring-test` |
| Any Java or Kotlin source file (`.java`, `.kt`) under the module | `jvm-language-review` |
| Java/Kotlin module with NO Spring Boot dependency (e.g., Quarkus, Micronaut, plain JVM) | `jvm-language-review` only; emit note "Spring skills do not apply" |

If `spring-boot-starter-test` is in `pom.xml` but no test source files exist, do not load `spring-test` (no targets to review).

For Gradle projects, parse the `dependencies { ... }` block in `build.gradle` or `build.gradle.kts` looking for the same artifact IDs.

### Spring Boot version detection

After detecting that a Spring skill applies, capture the Spring Boot **major version** (`2.x`, `3.x`, `4.x`):

- **Maven (`pom.xml`):** read `<parent><artifactId>spring-boot-starter-parent</artifactId><version>X.Y.Z</version>`. Extract major from `X`. Fallback: any `<dependency>` with `groupId=org.springframework.boot` and an explicit `<version>`.
- **Gradle (`build.gradle`/`build.gradle.kts`):** read `id 'org.springframework.boot' version 'X.Y.Z'` from the `plugins { ... }` block, OR an explicit `org.springframework.boot:spring-boot-starter` version in `dependencies { ... }`. Extract major.
- **No version found:** assume `3.x` (current default; v1 skill target).

Each Spring SKILL.md declares its supported versions in the frontmatter `spring_boot_versions` field (e.g., `spring_boot_versions: ["3.x"]`). After loading a skill, compare the detected version to the declared list:

| Detected version | Skill declares | Behavior |
|---|---|---|
| In declared list | `["3.x"]` matches `3.x` | Apply skill normally |
| Not in declared list | `["3.x"]` but detected `2.x` | Apply skill + emit one-line note: "skill `<name>` targets {declared}; detected SB {version} — see the skill's Version Compatibility section for which checks apply" |
| No spring_boot_versions field | (legacy / version-stable skill) | Apply normally; no note |

For each unsupported-version emission, list the skill name and the detected version in the agent's report header so reviewers don't miss it.

### Java version detection (for `jvm-language-review`)

Capture the Java **major version** from `pom.xml`/`build.gradle*`:

- **Maven:** `<properties><java.version>17</java.version></properties>` or `<maven.compiler.source>17</maven.compiler.source>`.
- **Gradle:** `sourceCompatibility = JavaVersion.VERSION_17` or `java { toolchain { languageVersion = JavaLanguageVersion.of(17) } }`.

Used by `jvm-language-review` to gate language-feature checks (records require Java 14+, sealed types require Java 17+, etc.). The skill's "Java Version Compatibility" section documents which checks apply at which Java level.
```

- [ ] **Step 3: Update the "Skill Loading" section**

Find the "Skill Loading" section. Replace its content with:

```markdown
## Skill Loading

**Always load (agnostic — apply to all backend stacks):**

- `backend/code-quality-review`
- `backend/api-design-review`
- `backend/testing-strategy-review`
- `backend/database-review`
- `backend/error-observability-review`
- `backend/deployment-safety-review`
- `backend/concurrency-review`

**Framework-specific (Java/Kotlin path, conditional on Spring sub-detection):**

- `backend/spring-web` — when `spring-boot-starter-web`/`webflux` detected
- `backend/spring-data` — when `spring-boot-starter-data-*` detected
- `backend/spring-config` — when any `spring-boot-starter` detected (default)
- `backend/spring-security` — when `spring-boot-starter-security` detected
- `backend/spring-test` — when `spring-boot-starter-test` detected and test source files exist
- `backend/jvm-language-review` — when any `.java` or `.kt` source file in the module

**Other stacks (Python, Node/TS, Go):** No framework skills in v1 — Plan 2 covers Java/Kotlin only. Python ships in v2, Node/TS in v3, Go in v4.
```

- [ ] **Step 4: Update the "Common Mistakes" section to remove the v1-stale entry**

Find this row in the Common Mistakes table:

```
| Running framework-specific Spring skills before Plan 2 lands | v1 ships zero framework skills. Java/Kotlin repos receive agnostic-only review until Plan 2 |
```

REPLACE it with:

```
| Loading all Spring skills regardless of detected starters | Sub-detect — `spring-security` only loads when `spring-boot-starter-security` is in the dependencies. Avoids false positives on Spring apps that don't use Security |
```

- [ ] **Step 5: Create the version extension contract doc**

Write `shield/skills/backend/EXTENDING-VERSIONS.md` with this EXACT content:

```markdown
# Extending Spring/JVM Skills to Other Versions

This doc is the contract for adding support for a Spring Boot major version (or Java major version) that the current skills don't fully cover.

v1 of the backend domain targets:
- **Spring Boot 3.x** — uses `jakarta.*` packages, lambda-style `SecurityFilterChain` DSL, Java 17+ baseline
- **Java 17** — records (since 14), sealed types (since 17), pattern matching, var (since 10)

Codebases on older versions (Spring Boot 2.x with `javax.*` and `WebSecurityConfigurerAdapter`, or Java 11 without sealed types) get useful-but-imperfect review with a per-skill compatibility note.

## When to extend

Add explicit support for a new version when:
- A meaningful share of target codebases run that version (e.g., still on Spring Boot 2.7 for Java-LTS reasons)
- The differences are large enough that "degrade gracefully" produces too many false positives or misses important issues

## Two extension patterns

For each Spring SKILL.md, decide between **broaden** and **sibling**:

### Pattern A — Broaden (recommended when most checks are version-stable)

Edit the existing SKILL.md to cover both versions in its rubric.

1. Add the new version to the frontmatter:
   ```yaml
   spring_boot_versions: ["3.x", "2.x"]
   ```
2. In the Evaluation Points table, mark version-sensitive checks with a note column or an extra column:
   ```
   | W3 | @Valid | (SB3) jakarta.validation, (SB2) javax.validation | High |
   ```
3. Update the Version Compatibility section to remove the "degrades gracefully" caveats — those checks now have explicit version-aware guidance.
4. Update the fixture (or add a parallel fixture if dialect differences are significant).
5. Run RED-GREEN against both versions. Add oracle entries for the new version's variants.

### Pattern B — Sibling skill (recommended when the API surface differs significantly)

Create a new SKILL.md alongside.

1. Decide naming. Two conventions, pick one:
   - **Suffix:** `shield/skills/backend/spring-security-sb2/SKILL.md` (sibling of `spring-security`)
   - **Subfolder:** `shield/skills/backend/spring-security/sb2/SKILL.md` (and rename the existing to `.../sb3/SKILL.md`)
   The suffix convention is less disruptive. The subfolder convention is cleaner once you have 3+ versions. Pick once and stay consistent.

2. Add the new skill name to the agent's Spring sub-detection routing. Update the routing table so the agent loads the right skill for the detected version:
   ```
   Detected SB version | spring-security skill loaded
   ---|---
   3.x                  | backend-spring-security
   2.x                  | backend-spring-security-sb2
   ```

3. Build a parallel fixture if the version's API surface is incompatible (e.g., `shield/examples/spring-boot-api-sb2/`). Reuse the existing fixture if you only need a few file additions.

4. RED-GREEN against the parallel fixture.

5. Update the original skill's Version Compatibility section to point to the sibling.

## Spring-specific guidance

- **`spring-security`** — recommend Pattern B (sibling). The DSL is fundamentally different between SS5 (SB2) and SS6 (SB3); a single rubric makes both bad.
- **`spring-data`, `spring-web`, `spring-test`, `spring-config`** — Pattern A (broaden) usually fits. Most checks are framework-stable; differences are package names and a few specific deprecations.
- **`jvm-language-review`** — version axis is Java, not Spring Boot. Pattern A. Add Java-version columns to the Evaluation Points table that gate language-feature checks (records → Java 14+, sealed → Java 17+).

## Process checklist

When adding a new version:

- [ ] Update frontmatter `spring_boot_versions` (or Java equivalent)
- [ ] Update or add a Version Compatibility section
- [ ] Update agent's version-detection routing (if Pattern B)
- [ ] Add or extend fixture
- [ ] RED test the new version
- [ ] Write or update SKILL.md (or sibling)
- [ ] GREEN test the new version
- [ ] Update CHANGELOG / release notes
- [ ] Bump shield version

## Anti-patterns

- **Don't** add version checks to the agent that test for version inside skill code. The agent does detection once; skills declare their support and emit notes via the agent's contract.
- **Don't** stuff multi-version support into a single SKILL.md when Pattern B applies — readers can't tell which checks apply to their version.
- **Don't** silently apply SB3 checks to SB2 code. Always emit the compat note when the version is outside the skill's declared range.
- **Don't** create a sibling skill "just in case" — broaden first; only split when the rubric becomes confusing.
```

- [ ] **Step 6: Verify with git diff**

```bash
git diff shield/agents/backend-reviewer.md
git status shield/skills/backend/EXTENDING-VERSIONS.md
```

Expected: agent diff shows new "Spring sub-detection", "Spring Boot version detection", "Java version detection" subsections, rewritten Skill Loading section, and one row swap in Common Mistakes. EXTENDING-VERSIONS.md exists as a new file.

- [ ] **Step 7: Commit**

```bash
git add shield/agents/backend-reviewer.md shield/skills/backend/EXTENDING-VERSIONS.md
git commit -m "feat(shield): add Spring sub-detection + version routing + extension contract"
```

---

### Task 2: spring-config skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppProperties.java`
- Create: `shield/examples/spring-boot-api/src/main/resources/application-prod.yml`
- Modify: `shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java` (add `@Value` violation)
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/spring-config/SKILL.md`

- [ ] **Step 1: Add a Spring-config-specific @ConfigurationProperties violation file**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppProperties.java`:

```java
package com.example.api.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

// VIOLATION: @Component + @ConfigurationProperties without prefix attribute. Properties
// won't bind correctly. Should use @ConfigurationProperties(prefix = "app").
// VIOLATION: Missing @Validated — invalid config (negative timeouts, empty URLs) won't
// fail at startup; will surface as runtime failures.
@Component
@ConfigurationProperties
public class AppProperties {

    // VIOLATION: Mutable field with public setter. @ConfigurationProperties beans should
    // be immutable (records or constructor binding via @ConfigurationPropertiesScan).
    private String apiUrl;
    private int timeoutSeconds;

    public String getApiUrl() { return apiUrl; }
    public void setApiUrl(String apiUrl) { this.apiUrl = apiUrl; }
    public int getTimeoutSeconds() { return timeoutSeconds; }
    public void setTimeoutSeconds(int timeoutSeconds) { this.timeoutSeconds = timeoutSeconds; }
}
```

- [ ] **Step 2: Add a prod profile with secret-in-config violation**

Write `shield/examples/spring-boot-api/src/main/resources/application-prod.yml`:

```yaml
# VIOLATION: Hardcoded secret in committed source. Should be sourced from env var,
# config server, or secret manager.
# VIOLATION: No @ConfigurationProperties type validation — these values will silently
# bind even if the type doesn't accept them.
spring:
  datasource:
    url: jdbc:postgresql://prod.example.com:5432/users
    username: app_user
    password: hardcoded-prod-password-2026

# VIOLATION: Profile-specific override that contradicts default behavior without
# explicit @ConditionalOnProperty gating.
app:
  api-url: https://api.prod.example.com
  timeout-seconds: 30
```

- [ ] **Step 3: Add a `@Value` violation to AppConfig.java**

Modify `shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java`. Find the existing class body (after `@Configuration`/`@Bean` declarations) and add a new field at the bottom of the class:

```java
    // VIOLATION: @Value for a typed config value. Should be in @ConfigurationProperties
    // for type safety, default handling, and validation.
    @org.springframework.beans.factory.annotation.Value("${app.timeout-seconds:30}")
    private int timeoutSeconds;
```

(Adjust based on the actual file structure — append before the closing `}`.)

- [ ] **Step 4: Append 5 oracle rows to `shield/examples/spring-boot-api/docs/expected-findings.md`**

```markdown
| spring-config | `config/AppProperties.java` | 8-10 | high | `@ConfigurationProperties` without `prefix` attribute — properties will not bind |
| spring-config | `config/AppProperties.java` | 8-10 | medium | Missing `@Validated` on `@ConfigurationProperties` — invalid config won't fail at startup |
| spring-config | `config/AppProperties.java` | 13-19 | medium | Mutable `@ConfigurationProperties` bean (setters); prefer immutable records |
| spring-config | `application-prod.yml` | 8-10 | high | Hardcoded secret (`spring.datasource.password`) in committed source |
| spring-config | `config/AppConfig.java` | (new line) | medium | `@Value` for typed config; should use `@ConfigurationProperties` |
```

- [ ] **Step 5: RED — dispatch a subagent without the skill**

Use `Agent` tool, `subagent_type: general-purpose`, `model: sonnet`. Send:

```
You are reviewing Spring Boot configuration code for Spring-config concerns.

Files:
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppProperties.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/resources/application-prod.yml

Read each file. List every Spring config issue: @ConfigurationProperties misuse, profile mishandling, @ConditionalOn* misuse, @Bean lifecycle, secrets in committed config, @Value vs @ConfigurationProperties.

For each: file, line range, severity (low/medium/high), one-sentence description. Markdown table.
```

Save the baseline.

- [ ] **Step 6: Write `shield/skills/backend/spring-config/SKILL.md` with this EXACT content:**

```markdown
---
name: backend-spring-config
description: Use when reviewing Spring Boot configuration code — `@ConfigurationProperties`, `application.yml`/profiles, `@Bean` lifecycle, `@ConditionalOn*`, externalized config, secrets management. Triggers when `application*.yml`/`.properties` files or Spring `@Configuration` beans are in scope and Spring Boot is detected.
spring_boot_versions: ["3.x"]
---

# Spring Config Review

## Overview

Review Spring Boot configuration for correct property binding, profile management, conditional bean wiring, lifecycle hygiene, and secrets externalization. Catches issues that are valid Java/Kotlin but invalid Spring patterns.

Triggers only when Spring Boot is detected (a `spring-boot-starter*` dependency in `pom.xml`/`build.gradle*`). Use `backend-deployment-safety-review` for the multi-instance / rollout angle on the same files.

## Version Compatibility

**Supported:** Spring Boot 3.x (declared via `spring_boot_versions: ["3.x"]` in frontmatter).

**Spring Boot 2.x — degraded coverage:**
- G1 (`@ConfigurationProperties` prefix): applies identically
- G3 (immutable config): SB2.2+ supports constructor binding via `@ConfigurationPropertiesScan`; SB2.0/2.1 require explicit `@ConstructorBinding`. SB3 makes constructor binding the default
- All other checks: framework-stable across SB2/SB3

To add full SB2 coverage, follow Pattern A (broaden the rubric) per `shield/skills/backend/EXTENDING-VERSIONS.md`.

## When to Use

- Reviewing `application.yml`, `application-{profile}.yml`, or `application.properties`
- Reviewing `@Configuration`/`@Bean`/`@ConfigurationProperties` classes
- Reviewing `@ConditionalOn*` usage
- Pre-implementation: shaping the config surface during planning

## When NOT to Use

- Pure runtime config (env vars, K8s ConfigMaps) — operational concern
- Build-time config (Maven/Gradle property substitution) — different phase
- Non-Spring frameworks (Quarkus `application.properties`, Micronaut config) — same concepts but different annotations

## Review Process

1. Inventory: `application*.yml`/`.properties` files, `@Configuration` classes, `@ConfigurationProperties` POJOs/records, `@Bean` methods
2. For each artifact, apply Evaluation Points G1–G10
3. Cross-cut: trace a property from `application.yml` to its consumer; flag any binding gap

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| G1 | `@ConfigurationProperties` prefix | Always set `prefix = "..."`. Without it, properties won't bind to nested keys correctly | High |
| G2 | Validation on config types | `@Validated` + JSR-303 annotations on `@ConfigurationProperties` so invalid config fails at startup, not runtime | Medium |
| G3 | Immutable config types | Prefer records or constructor binding (`@ConfigurationPropertiesScan` + immutable POJO) over getter/setter mutability | Medium |
| G4 | `@Value` vs `@ConfigurationProperties` | For typed groups of config, prefer `@ConfigurationProperties`. `@Value` is OK for one-off literals or SpEL | Medium |
| G5 | Profile correctness | `application-{profile}.yml` files exist for each declared profile. No profile-specific behavior baked into base config | Medium |
| G6 | Secrets in committed source | No passwords, API keys, or tokens in `application*.yml` / `application*.properties`. Use env vars, config server, or secret manager | High |
| G7 | `@ConditionalOn*` correctness | `@ConditionalOnProperty` etc. apply to the right bean and have correct `havingValue`/`matchIfMissing` semantics | High |
| G8 | `@Bean` lifecycle | No state in the `@Bean` method body that mutates a singleton context; no manual `new SomeBean()` outside `@Bean` for managed components | Medium |
| G9 | `@ComponentScan` boundaries | Default scan covers the right packages; no overly broad scans that pick up test classes in production | Medium |
| G10 | Default profile fallback | Sensible defaults in `application.yml`; profile files override only what changes | Low |

## Critical Checks

- A `@ConfigurationProperties` class with NO `prefix` attribute
- A committed `application*.yml` file containing what looks like a password, API key, or token
- A `@ConditionalOnProperty` annotation with no `name` attribute (always-evaluates-true bug)
- A `@Bean` method that calls `new` on another `@Component` instead of injecting it
- An `application-{profile}.yml` declared but never activated (no profile in deployment config)

## Severity Guide

| Severity | When |
|---|---|
| High | Properties don't bind (deployment will start with default values silently); secret leak |
| Medium | Friction or fragility — type errors at runtime, mutable config, suboptimal tools |
| Low | Stylistic — config layout, default-value placement |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding all config be in `@ConfigurationProperties` | Single literals (`@Value("${feature.enabled:false}")`) are fine for one-off use |
| Treating any `password` key as a leak | Test fixtures, dev profiles, and inline placeholder examples are acceptable. The smell is committed prod values |
| Flagging `@Value` with SpEL | SpEL has legitimate uses (computed defaults). Don't flag every `@Value` |
| Demanding records for all configs | Records are recommended; existing setter-based POJOs are fine if not actively touched |
| Insisting all profiles have files | Profiles activated via env vars or args don't need a file if defaults suffice |

## Related Skills

- For multi-instance config divergence and rollout safety → `backend-deployment-safety-review`
- For secrets at the infrastructure layer → `security-reviewer` agent (cross-cutting)
- For config-driven feature flags → `backend-deployment-safety-review` (S1)
```

- [ ] **Step 7: GREEN — dispatch a subagent with the skill loaded**

Use `Agent` tool, `subagent_type: general-purpose`, `model: sonnet`. Send:

```
You are reviewing Spring Boot configuration code for Spring-config concerns.

Read this skill in full and apply its rubric:
/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/skills/backend/spring-config/SKILL.md

Files (apply G1–G10):
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppProperties.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/resources/application-prod.yml

Markdown table: G#, file, line range, severity, one-sentence finding.
```

GREEN must catch all 5 oracle findings (high/medium/medium/high/medium). Refactor SKILL.md if any are missed.

- [ ] **Step 8: Refactor if needed.**

- [ ] **Step 9: Commit**

```bash
git add shield/skills/backend/spring-config/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppProperties.java \
        shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java \
        shield/examples/spring-boot-api/src/main/resources/application-prod.yml \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend spring-config skill"
```

---

### Task 3: spring-web skill (TDD)

**Files:**
- Modify: `shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java` (add Spring-web specific violations)
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/spring-web/SKILL.md`

- [ ] **Step 1: Add Spring-web specific violations to UserController.java**

Read the current `UserController.java` (from Plan 1, Task 3). Modify it to add Spring-web violations alongside the existing api-design ones. Add an import:

```java
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.RequestBody;
```

Inside the class, add new methods at the bottom of the class body (before the closing `}`):

```java
    // VIOLATION: Field injection (existing) is a spring-web smell — flagged again here.
    // The above @Autowired private UserService userService should be constructor injection.

    // VIOLATION: @RequestMapping with no method attribute — defaults to all methods.
    // Should be @PostMapping for clarity.
    // VIOLATION: Missing @Valid on @RequestBody — incoming payload not validated.
    @org.springframework.web.bind.annotation.RequestMapping("/v2/users")
    public Map<String, Object> createUserV2(@RequestBody Map<String, String> payload) {
        return Map.of("created", payload.getOrDefault("email", ""));
    }

    // VIOLATION: ResponseEntity not used where it should be — handler returns a Map but
    // the spec says return 201 Created with a Location header. Use ResponseEntity.
    // VIOLATION: @ResponseStatus on a method that also returns ResponseEntity-style map
    // (status comes from two sources, ambiguous).
    @org.springframework.web.bind.annotation.PostMapping("/v2/users/{id}/promote")
    @org.springframework.web.bind.annotation.ResponseStatus(HttpStatus.OK)
    public Map<String, Object> promote(@org.springframework.web.bind.annotation.PathVariable Long id) {
        return Map.of("promoted", id);
    }

    // VIOLATION: Mixed-case path segment — Spring is case-sensitive; inconsistent with
    // the kebab-case convention used elsewhere in this controller.
    @org.springframework.web.bind.annotation.GetMapping("/userProfile/{userId}")
    public Map<String, Object> getUserProfile(@org.springframework.web.bind.annotation.PathVariable Long userId) {
        return Map.of("userId", userId);
    }
```

- [ ] **Step 2: Append 5 oracle rows to expected-findings.md**

```markdown
| spring-web | `controller/UserController.java` | 15-16 | high | Field injection via `@Autowired` — should be constructor injection |
| spring-web | `controller/UserController.java` | (createUserV2) | medium | `@RequestMapping` with no `method` attribute; use `@PostMapping` |
| spring-web | `controller/UserController.java` | (createUserV2) | high | Missing `@Valid` on `@RequestBody`; incoming payload unvalidated |
| spring-web | `controller/UserController.java` | (promote) | medium | `@ResponseStatus` + return value mix; status source is ambiguous |
| spring-web | `controller/UserController.java` | (getUserProfile) | low | Mixed-case path segment `/userProfile/`; inconsistent with kebab-case elsewhere |
```

(Replace `(createUserV2)` etc. with actual line ranges after writing the file.)

- [ ] **Step 3: RED — subagent without skill**

`Agent` tool, `subagent_type: general-purpose`, `model: sonnet`:

```
You are reviewing Spring Boot controller code for Spring-web concerns.

File: /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java

List every Spring-web issue: dependency injection style, @RequestMapping vs verb-specific annotations, @Valid usage, @ExceptionHandler wiring, ResponseEntity vs naked return, @ResponseStatus consistency, request mapping clarity.

Note: this file also contains api-design violations (verb-in-URI, etc.) that are NOT Spring-web concerns — focus on Spring-specific issues only.

Markdown table: file, line range, severity, finding.
```

- [ ] **Step 4: Write `shield/skills/backend/spring-web/SKILL.md` with this EXACT content:**

```markdown
---
name: backend-spring-web
description: Use when reviewing Spring MVC / WebFlux controllers — `@RestController` patterns, dependency injection style, `@Valid`, `@ExceptionHandler`/`@ControllerAdvice`, `ResponseEntity`, request mapping clarity. Triggers when controllers are in scope and Spring Boot web/webflux is detected.
spring_boot_versions: ["3.x"]
---

# Spring Web Review

## Overview

Review Spring MVC and WebFlux controller code for idiomatic Spring patterns. Catches Spring-specific issues that the agnostic `api-design-review` skill doesn't flag (which is HTTP-conventions-focused).

Triggers when `spring-boot-starter-web` or `spring-boot-starter-webflux` is detected in `pom.xml`/`build.gradle*` and controller files are in scope. Pairs with `api-design-review` (HTTP layer) and `error-observability-review` (error response shape).

## Version Compatibility

**Supported:** Spring Boot 3.x (declared via `spring_boot_versions: ["3.x"]` in frontmatter).

**Spring Boot 2.x — degraded coverage:**
- W3 (`@Valid` on `@RequestBody`): applies, but examples use `jakarta.validation.*`; SB2 uses `javax.validation.*`. Findings still apply with the package name swapped
- W4 (`@ControllerAdvice`): applies identically across SB2/SB3
- Other checks: framework-stable

To add full SB2 coverage, follow Pattern A (broaden the rubric) per `shield/skills/backend/EXTENDING-VERSIONS.md`.

## When to Use

- Reviewing `@RestController` classes
- Reviewing `@ControllerAdvice` exception handlers
- Reviewing request validation (`@Valid` on `@RequestBody`)
- Pre-implementation: shaping a new controller during planning

## When NOT to Use

- HTTP/REST contract concerns (status codes, idempotency, URI design) — use `api-design-review`
- Pure error response shape — use `error-observability-review`
- Non-Spring web frameworks (FastAPI, Express) — different conventions

## Review Process

1. Inventory: `@RestController` and `@Controller` classes, `@ControllerAdvice` classes, request mapping methods
2. For each, apply Evaluation Points W1–W10
3. Cross-cut: confirm a single `@ControllerAdvice` handles the error shape consistently across handlers

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| W1 | Dependency injection style | Constructor injection (with `final` fields) over `@Autowired` field/setter injection. Also enables immutability and easier testing | High |
| W2 | Verb-specific mapping annotations | `@GetMapping` / `@PostMapping` / etc. over `@RequestMapping` (which defaults to all methods if `method` is omitted) | Medium |
| W3 | `@Valid` on `@RequestBody` | Every `@RequestBody` parameter has `@Valid` (and the body class has JSR-303 annotations). Validation errors return 400 with field details | High |
| W4 | `@ControllerAdvice` consistency | One `@ControllerAdvice` (or a small set) handles all exception → response mapping. Avoids ad-hoc `try/catch` in each controller method | High |
| W5 | `ResponseEntity` for status flexibility | Use `ResponseEntity.status(...).body(...)` when the handler needs to return varying status codes or set headers (e.g., `Location` for 201 Created) | Medium |
| W6 | `@ResponseStatus` vs `ResponseEntity` consistency | Don't mix — pick one source of status code per handler. `@ResponseStatus` fixes the status; `ResponseEntity` lets it vary | Medium |
| W7 | Path/query/body separation | Path variables for resource IDs, query params for filtering/sorting, body for the resource payload. Don't mix concerns | Medium |
| W8 | Content negotiation | `produces`/`consumes` attributes on controllers that serve multiple formats (JSON + XML, etc.) | Low |
| W9 | URI casing consistency | Kebab-case (or snake_case) consistently across endpoints; no `/userProfile` next to `/user-profile` | Low |
| W10 | Filter/interceptor placement | Cross-cutting concerns (auth, logging, request ID) live in filters/interceptors, not in every controller method | Medium |

## Critical Checks

- `@Autowired` on a field (not constructor) in any `@RestController` or `@Service`
- A `@RequestBody` parameter without `@Valid` on a controller that mutates state
- Two `@ControllerAdvice` classes handling overlapping exception types (last-wins is fragile)
- A handler with both `@ResponseStatus` AND a `ResponseEntity` return type
- A `@RequestMapping` annotation without an explicit `method` attribute on a state-changing endpoint

## Severity Guide

| Severity | When |
|---|---|
| High | Test/maintainability blocker (field injection), security/correctness blocker (no validation) |
| Medium | Style/consistency issues that impact maintainability |
| Low | Cosmetic — URI casing, content negotiation gaps |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding constructor injection on `@Autowired` setter | Setter injection is acceptable for circular dependency cases (rare). Default to constructor; setter only with explicit reason |
| Flagging `@RequestMapping` always | `@RequestMapping(value = "/foo", method = RequestMethod.POST)` is fine — the smell is omitting `method` |
| Insisting on `@Valid` on read endpoints | GET handlers don't need request body validation; the smell is missing `@Valid` on POST/PUT/PATCH bodies |
| Demanding ResponseEntity everywhere | Plain DTO returns are fine when the status is always 200 (default); use ResponseEntity only when status varies |
| Penalizing `@RestController` without explicit `@ResponseBody` on each method | `@RestController` implies `@ResponseBody` on every method — don't require explicit |

## Related Skills

- For HTTP contract concerns (methods, status codes, URI design) → `backend-api-design-review`
- For exception → response shape → `backend-error-observability-review`
- For test slices on controllers (`@WebMvcTest`) → `backend-spring-test`
```

- [ ] **Step 5: GREEN — subagent with skill**

`Agent` tool, `subagent_type: general-purpose`, `model: sonnet`:

```
You are reviewing Spring Boot controller code for Spring-web concerns.

Read this skill in full and apply its rubric:
/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/skills/backend/spring-web/SKILL.md

File (apply W1–W10): /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java

Focus on Spring-web issues only. The file also contains api-design violations (which are flagged by a different skill); do NOT include those.

Markdown table: W#, file, line range, severity, one-sentence finding.
```

GREEN must catch all 5 oracle findings (high/medium/high/medium/low).

- [ ] **Step 6: Refactor if needed.**

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/spring-web/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend spring-web skill"
```

---

### Task 4: spring-data skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderProcessingService.java`
- Modify: `shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java` (add `@Modifying` violation)
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/spring-data/SKILL.md`

- [ ] **Step 1: Create OrderProcessingService.java with @Transactional violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderProcessingService.java`:

```java
package com.example.api.service;

import com.example.api.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderProcessingService {

    private final UserRepository userRepository;

    public OrderProcessingService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    // VIOLATION: @Transactional on private method — Spring proxies are class-level;
    // private methods are NOT transactional.
    @Transactional
    private void persistOrder(Long userId) {
        userRepository.findById(userId);
    }

    // VIOLATION: Self-invocation problem — calling `persistOrder` from within the same
    // class bypasses the proxy, so @Transactional doesn't apply. Call from a separate
    // bean OR refactor.
    public void processOrder(Long userId) {
        persistOrder(userId);
    }

    // VIOLATION: Read method without `readOnly = true`. Skips JPA flush optimization
    // and signals intent incorrectly to other developers.
    @Transactional
    public Long countOrders(Long userId) {
        return userRepository.findById(userId).map(u -> 1L).orElse(0L);
    }

    // VIOLATION: REQUIRES_NEW propagation without explicit reason. Forks a new tx for
    // every call; almost always a mistake unless documenting why (e.g., "must commit
    // even if outer tx fails").
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordAuditEntry(Long userId, String action) {
        userRepository.findById(userId);
    }
}
```

- [ ] **Step 2: Add a @Modifying violation to UserRepository.java**

Modify `shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java`. Add this method to the interface (before the closing `}`):

```java
    // VIOLATION: Mutating JPQL query without @Modifying annotation. Spring will treat
    // it as a SELECT and the update will not execute. Must add @Modifying (and usually
    // @Transactional on the caller).
    @org.springframework.data.jpa.repository.Query("UPDATE User u SET u.email = :email WHERE u.id = :id")
    int updateEmail(@org.springframework.data.repository.query.Param("id") Long id,
                    @org.springframework.data.repository.query.Param("email") String email);
```

- [ ] **Step 3: Append 5 oracle rows**

```markdown
| spring-data | `service/OrderProcessingService.java` | 18-21 | high | `@Transactional` on private method — proxies don't intercept private |
| spring-data | `service/OrderProcessingService.java` | 26-28 | high | Self-invocation of `@Transactional` method bypasses the proxy |
| spring-data | `service/OrderProcessingService.java` | 32-35 | medium | Read method missing `readOnly = true` |
| spring-data | `service/OrderProcessingService.java` | 39-42 | medium | `REQUIRES_NEW` propagation without justification |
| spring-data | `repository/UserRepository.java` | (updateEmail) | high | Mutating JPQL `@Query` without `@Modifying` — update never runs |
```

- [ ] **Step 4: RED — subagent without skill**

`Agent` tool:

```
You are reviewing Spring Data JPA code for Spring-data concerns.

Files:
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderProcessingService.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java

List Spring-data specific issues: @Transactional placement (class vs method, private, propagation, readOnly), self-invocation problem, @Modifying for mutating queries, repository patterns. Exclude pure schema/N+1 issues (those are agnostic database-review).

Markdown table.
```

- [ ] **Step 5: Write `shield/skills/backend/spring-data/SKILL.md` with this EXACT content:**

```markdown
---
name: backend-spring-data
description: Use when reviewing Spring Data JPA code — `@Transactional` placement and propagation, self-invocation, JPQL fetch strategies, `@Modifying` queries, repository patterns, equals/hashCode on entities. Triggers when JPA repositories or `@Transactional` methods are in scope and Spring Boot Data is detected.
spring_boot_versions: ["3.x"]
---

# Spring Data Review

## Overview

Review Spring Data JPA code for transactional correctness, query patterns, and entity design. Catches Spring-specific issues that the agnostic `database-review` skill doesn't flag (which is schema/index/N+1-focused).

Triggers when `spring-boot-starter-data-*` is detected and JPA repositories or `@Transactional` methods are in scope.

## Version Compatibility

**Supported:** Spring Boot 3.x (declared via `spring_boot_versions: ["3.x"]` in frontmatter).

**Spring Boot 2.x — degraded coverage:**
- All checks (P1–P10) apply identically; package names differ (`jakarta.persistence.*` in SB3 vs `javax.persistence.*` in SB2)
- `@Transactional` annotations live in `org.springframework.transaction.annotation` in both versions — no change

To add full SB2 coverage, follow Pattern A (broaden the rubric) per `shield/skills/backend/EXTENDING-VERSIONS.md`.

## When to Use

- Reviewing `@Repository` interfaces (Spring Data, custom)
- Reviewing `@Transactional` placement and propagation
- Reviewing JPA entities for equals/hashCode and lifecycle annotations
- Reviewing JPQL/native queries with `@Query`/`@Modifying`

## When NOT to Use

- Pure schema design (FKs, indexes, normalization) — use `database-review`
- N+1 query detection at the schema level — use `database-review` (D6)
- Non-JPA persistence (Spring Data MongoDB, JDBC, R2DBC) — patterns differ; this skill is JPA-focused

## Review Process

1. Inventory: `@Transactional` annotations, `@Repository` interfaces, JPA entity classes, `@Query` methods
2. For each, apply Evaluation Points P1–P10
3. Cross-cut: trace a write path; flag every transactional boundary that is silently missing or misplaced

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| P1 | `@Transactional` on private method | Spring AOP proxies don't intercept private methods. `@Transactional` on `private` is a no-op | High |
| P2 | Self-invocation problem | Calling a `@Transactional` method from within the same bean bypasses the proxy. Refactor to separate bean OR use `AopContext.currentProxy()` (rarely the right answer) | High |
| P3 | `readOnly = true` on read methods | Read methods marked `@Transactional(readOnly = true)` — enables JPA flush optimization, signals intent | Medium |
| P4 | Propagation correctness | `REQUIRES_NEW` requires explicit justification (e.g., audit log that commits independently). Default `REQUIRED` is correct most of the time | Medium |
| P5 | `@Modifying` for mutating `@Query` | UPDATE/DELETE in `@Query` requires `@Modifying`. Without it, Spring treats it as SELECT and silently ignores the change | High |
| P6 | Mutating queries also need `@Transactional` | `@Modifying` queries fail without an active transaction. Annotate the caller (or use `@Transactional` on the repo method) | High |
| P7 | `equals`/`hashCode` on entities | Auto-generated ID-based equals breaks before persistence (HashSet bugs). Use natural keys or business identifier; document the choice | Medium |
| P8 | Fetch strategy via `@EntityGraph` | When `findAll`/custom queries need to load children, use `@EntityGraph(attributePaths=...)` rather than EAGER on the entity | Medium |
| P9 | `@Repository` annotation | Optional on `Spring Data` interfaces extending `JpaRepository` (auto-detected), but harmless. Required for plain JPA repos with `@PersistenceContext` | Low |
| P10 | Cascade types | `CascadeType.ALL` on `@OneToMany` cascades deletes — usually wrong. Be explicit about which operations cascade | Medium |

## Critical Checks

- `@Transactional` annotation on a `private` method (always a bug)
- A method calling another `@Transactional` method on `this` (self-invocation)
- A `@Query` containing `UPDATE` or `DELETE` without `@Modifying`
- A `@Modifying` query on a method outside any `@Transactional` boundary
- An entity with default Object-identity `equals`/`hashCode` used in a HashSet/HashMap

## Severity Guide

| Severity | When |
|---|---|
| High | Silent bug — code looks like it works but doesn't (no-op `@Transactional`, ignored update, lost data) |
| Medium | Performance/correctness friction (missing readOnly, wrong propagation, equals bugs in collections) |
| Low | Style — annotation hygiene |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding `@Transactional` on every public method | Many service methods are read-only and don't need explicit `@Transactional` (auto-tx in Spring Data repos handles reads) |
| Flagging `Propagation.REQUIRES_NEW` always | Legitimate when the caller's tx must not affect the inner work (audit log, retry logic). The smell is REQUIRES_NEW WITHOUT a comment justifying it |
| Insisting on `@Repository` on Spring Data interfaces | Spring Data auto-detects them. Adding `@Repository` is harmless but not required |
| Penalizing all Cascade.ALL | Acceptable on parent-owned children where deleting the parent SHOULD delete children (e.g., line items of an invoice) |
| Treating ID-based equals as always wrong | OK when entities are always persisted before going into collections. The smell is using them in HashSet pre-persistence |

## Related Skills

- For schema design (FKs, indexes, migrations) → `backend-database-review`
- For underlying code structure → `backend-code-quality-review`
- For multi-instance state safety on shared caches → `backend-deployment-safety-review`
```

- [ ] **Step 6: GREEN — subagent with skill**

`Agent` tool:

```
You are reviewing Spring Data JPA code for Spring-data concerns.

Read this skill in full and apply its rubric:
/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/skills/backend/spring-data/SKILL.md

Files (apply P1–P10):
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderProcessingService.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java

Markdown table: P#, file, line range, severity, one-sentence finding.
```

GREEN must catch all 5 oracle findings (high/high/medium/medium/high).

- [ ] **Step 7: Refactor if needed.**

- [ ] **Step 8: Commit**

```bash
git add shield/skills/backend/spring-data/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderProcessingService.java \
        shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend spring-data skill"
```

---

### Task 5: spring-security skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/spring-security/SKILL.md`

- [ ] **Step 1: Create SecurityConfig.java with Spring Security violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java`:

```java
package com.example.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.password.NoOpPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    // VIOLATION: NoOpPasswordEncoder stores plaintext. Use BCrypt/Argon2/PBKDF2.
    @Bean
    @SuppressWarnings("deprecation")
    public PasswordEncoder passwordEncoder() {
        return NoOpPasswordEncoder.getInstance();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // VIOLATION: CSRF disabled without explicit reason or compensating control.
            // For browser-facing APIs that use cookies, CSRF must be enabled.
            .csrf(csrf -> csrf.disable())
            // VIOLATION: All endpoints permitted — no authentication required anywhere.
            // Effectively turns off security.
            .authorizeHttpRequests(auth -> auth
                .anyRequest().permitAll()
            )
            // VIOLATION: HTTP Basic configured without HTTPS enforcement. Credentials
            // sent in cleartext if HTTPS not terminated upstream.
            .httpBasic(httpBasic -> {})
            // VIOLATION: Session creation policy not set. Defaults to IF_REQUIRED, which
            // creates sessions for stateless APIs unnecessarily.
            ;
        return http.build();
    }
}
```

- [ ] **Step 2: Append 4 oracle rows**

```markdown
| spring-security | `config/SecurityConfig.java` | 17-21 | high | `NoOpPasswordEncoder` stores passwords in plaintext |
| spring-security | `config/SecurityConfig.java` | 27-29 | high | CSRF disabled with no compensating control or explicit reason |
| spring-security | `config/SecurityConfig.java` | 31-34 | high | All endpoints `permitAll()` — authentication effectively disabled |
| spring-security | `config/SecurityConfig.java` | 36-37 | medium | HTTP Basic configured without HTTPS enforcement |
```

- [ ] **Step 3: RED — subagent without skill**

```
You are reviewing Spring Security configuration for security concerns.

File: /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java

List Spring Security issues: SecurityFilterChain config, password encoder choice, CSRF/CORS, method-level security, session management, authentication on sensitive endpoints.

Markdown table.
```

- [ ] **Step 4: Write `shield/skills/backend/spring-security/SKILL.md` with this EXACT content:**

```markdown
---
name: backend-spring-security
description: Use when reviewing Spring Security configuration — `SecurityFilterChain`, password encoding, CSRF/CORS, method-level security (`@PreAuthorize`), session management, authentication providers, JWT/OAuth2 wiring. Triggers when Spring Security config is in scope.
spring_boot_versions: ["3.x"]
---

# Spring Security Review

## Overview

Review Spring Security configuration for safe defaults: strong password hashing, CSRF protection on browser flows, deliberate authorization rules, appropriate session policy, and explicit choices on every relaxation.

Triggers when `spring-boot-starter-security` is detected and Spring Security config classes are in scope. Pairs with the `security-reviewer` agent for cross-cutting security concerns beyond Spring Security framework wiring.

## Version Compatibility

**Supported:** Spring Boot 3.x with Spring Security 6 (declared via `spring_boot_versions: ["3.x"]` in frontmatter).

**Spring Boot 2.x with Spring Security 5 — LIMITED coverage. This is the most version-sensitive Spring skill.**

Spring Security 5 uses `WebSecurityConfigurerAdapter` and a different DSL. The SB3 examples in this skill DO NOT translate directly. On SB2 codebases:
- SS1 (password encoder strength): applies identically — trust this finding
- SS5 (method-level `@PreAuthorize`): applies identically — trust this finding
- SS2 (CSRF), SS3 (authorization rules), SS4 (CORS), SS6 (session policy): the SB3 lambda DSL examples DO NOT match SB2's `WebSecurityConfigurerAdapter` style. Findings on SB2 code may be incorrect — verify manually
- SS7 (JWT/OAuth2): applies but config class shape differs
- SS8 (HTTPS), SS9 (auth provider), SS10 (logout): concept identical, syntax differs

**Recommendation:** For thorough SB2 coverage, follow Pattern B (sibling skill `spring-security-sb2`) per `shield/skills/backend/EXTENDING-VERSIONS.md`. Until then: trust SS1 and SS5 findings on SB2 code, treat SS2–SS4 findings as candidates to verify manually.

## When to Use

- Reviewing `@EnableWebSecurity` configuration classes
- Reviewing `SecurityFilterChain` beans and their authorization rules
- Reviewing `@PreAuthorize`/`@PostAuthorize` on service methods
- Reviewing JWT/OAuth2 resource server configuration

## When NOT to Use

- Application-layer authorization without Spring Security — different patterns
- Infrastructure-level network security (security groups, ACLs) — operational concern
- Generic input validation — use `api-design-review` (A9)

## Review Process

1. Inventory: `@EnableWebSecurity` classes, `SecurityFilterChain` beans, `@PreAuthorize`/`@PostAuthorize` annotations, password encoder beans
2. For each, apply Evaluation Points SS1–SS10
3. Cross-cut: trace authorization for a critical endpoint; confirm one rule covers it explicitly

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| SS1 | Password encoder strength | BCrypt, Argon2, or PBKDF2. NoOp / plaintext / MD5 / SHA-1 are unacceptable | High |
| SS2 | CSRF protection | Enabled by default. Disabled only with explicit reason (stateless API + no cookies) and compensating control | High |
| SS3 | Authorization rules deliberate | No blanket `permitAll()` on `anyRequest()`. Rules enumerate which endpoints are public | High |
| SS4 | CORS configuration | If browsers call the API across origins, CORS is configured explicitly with allowed origins (no wildcard `*` in prod) | High |
| SS5 | Method-level security on sensitive operations | `@PreAuthorize("hasRole('ADMIN')")` etc. on admin/sensitive service methods. Don't rely solely on URL-based rules | Medium |
| SS6 | Session creation policy | Stateless APIs use `STATELESS`. Browser flows use `IF_REQUIRED`. Don't accept the default if it's wrong for the app | Medium |
| SS7 | JWT/OAuth2 token validation | Issuer, audience, signature algorithm, and clock skew are configured explicitly. No wildcard issuer accept | High |
| SS8 | HTTPS enforcement | `requiresChannel().anyRequest().requiresSecure()` for browser flows OR ensure deployment terminates HTTPS upstream and cookies are `Secure` | Medium |
| SS9 | Authentication provider correctness | One clear chain. No mixing in-memory + database providers without intent. `UserDetailsService` returns enabled+credentials-non-expired users | Medium |
| SS10 | Logout configuration | If sessions are used, logout invalidates the session and clears authentication. Don't rely on default for production | Low |

## Critical Checks

- `NoOpPasswordEncoder` (or any plaintext password mechanism)
- `csrf().disable()` without an explanatory comment AND without a stateless/no-cookies justification
- `anyRequest().permitAll()` on a SecurityFilterChain
- HTTP Basic without HTTPS enforcement
- JWT validation that doesn't check issuer or signature algorithm

## Severity Guide

| Severity | When |
|---|---|
| High | Direct security exposure — broken auth, plaintext passwords, missing CSRF on cookie flows |
| Medium | Defensive gap — missing method-level security, wrong session policy |
| Low | Hygiene — logout config, deprecation warnings |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding CSRF on stateless JSON APIs | If the API uses Bearer tokens (no cookies), CSRF is not needed. Disabling is correct, but should be explicit |
| Flagging `permitAll()` on health/metrics endpoints | `/actuator/health`, public docs, etc. legitimately permit all — flag only when applied to `anyRequest()` |
| Insisting on `@PreAuthorize` everywhere | URL-based rules in `SecurityFilterChain` are sufficient for many flows. Method security is a defense-in-depth tool |
| Demanding HTTPS enforcement at the app | If a load balancer/ingress terminates HTTPS and forwards plaintext internally, app-level enforcement is redundant |
| Penalizing in-memory user details | Acceptable for tests, demos, internal admin tools. Production should use a real user store |

## Related Skills

- For cross-cutting security beyond Spring Security wiring → `security-reviewer` agent
- For input validation as a defensive layer → `backend-api-design-review` (A9)
- For secrets handling in config → `backend-spring-config` (G6)
```

- [ ] **Step 5: GREEN — subagent with skill**

```
You are reviewing Spring Security configuration.

Read this skill in full:
/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/skills/backend/spring-security/SKILL.md

File (apply SS1–SS10): /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java

Markdown table: SS#, file, line range, severity, finding.
```

GREEN must catch all 4 oracle findings (high/high/high/medium).

- [ ] **Step 6: Refactor if needed.**

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/spring-security/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend spring-security skill"
```

---

### Task 6: spring-test skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/test/java/com/example/api/controller/UserControllerIntegrationTest.java`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/spring-test/SKILL.md`

- [ ] **Step 1: Create UserControllerIntegrationTest.java with Spring-test slice violations**

Write `shield/examples/spring-boot-api/src/test/java/com/example/api/controller/UserControllerIntegrationTest.java`:

```java
package com.example.api.controller;

import com.example.api.repository.UserRepository;
import com.example.api.service.UserService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

// VIOLATION: Full @SpringBootTest for a controller-only test. @WebMvcTest(UserController.class)
// would load only the web layer — much faster, focused.
// VIOLATION: @DirtiesContext per-method causes context recreation between tests; very slow.
// Use only when state mutation requires it AND no test-isolation alternative exists.
@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.BEFORE_EACH_TEST_METHOD)
class UserControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    // VIOLATION: @MockBean on a class that the controller doesn't directly call.
    // The test mocks the entire layer instead of using the slice's auto-config.
    @MockBean
    private UserService userService;

    @MockBean
    private UserRepository userRepository;

    // VIOLATION: Test relies on H2 schema state from prior tests (no @BeforeEach reset,
    // no @Sql to seed). Order-dependent.
    @Test
    void getUser_returns200() throws Exception {
        mockMvc.perform(get("/api/user/1"));
        // No assertions chained on the result — test passes regardless.
    }
}
```

- [ ] **Step 2: Append 4 oracle rows**

```markdown
| spring-test | `test/.../UserControllerIntegrationTest.java` | 17 | high | `@SpringBootTest` for controller-only test; should be `@WebMvcTest(UserController.class)` |
| spring-test | `test/.../UserControllerIntegrationTest.java` | 19-20 | high | `@DirtiesContext(BEFORE_EACH_TEST_METHOD)` — context recreation per test is very slow |
| spring-test | `test/.../UserControllerIntegrationTest.java` | 27-31 | medium | `@MockBean` overuse — slice annotation handles auto-config; MockBean only for true external collaborators |
| spring-test | `test/.../UserControllerIntegrationTest.java` | 36-39 | high | Test relies on shared H2 state and has no assertions on the response |
```

- [ ] **Step 3: RED — subagent without skill**

```
You are reviewing Spring Boot test code for test-slice and test-strategy concerns.

File: /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/test/java/com/example/api/controller/UserControllerIntegrationTest.java

List Spring-test specific issues: test slice annotation choice (@SpringBootTest vs @WebMvcTest vs @DataJpaTest), @MockBean overuse, @DirtiesContext misuse, Testcontainers vs H2, parallel test safety.

Markdown table.
```

- [ ] **Step 4: Write `shield/skills/backend/spring-test/SKILL.md` with this EXACT content:**

```markdown
---
name: backend-spring-test
description: Use when reviewing Spring Boot test code — test slice selection (`@SpringBootTest` vs `@WebMvcTest` vs `@DataJpaTest`), `@MockBean` overuse, Testcontainers vs H2, `@DirtiesContext` hygiene, security context in tests. Triggers when Spring Boot test files are in scope.
spring_boot_versions: ["3.x"]
---

# Spring Test Review

## Overview

Review Spring Boot tests for appropriate slice scope, mock placement, and context isolation. Pairs with the agnostic `testing-strategy-review` (which covers test pyramid, mocking SUT, flaky patterns).

Triggers when `spring-boot-starter-test` is detected and test source files are in scope. The agnostic skill flags WHAT is wrong with a test; this skill flags HOW Spring's test annotations should be used.

## Version Compatibility

**Supported:** Spring Boot 3.x (declared via `spring_boot_versions: ["3.x"]` in frontmatter).

**Spring Boot 2.x — degraded coverage:**
- All checks (ST1–ST10) apply identically across SB2/SB3
- Package paths differ slightly (`jakarta.servlet.*` in SB3 vs `javax.servlet.*` in SB2 for MockMvc/WebMvcTest internals)

**Spring Boot 3.4+:** `@MockBean` was deprecated in Spring Framework 6.2 in favor of `@MockitoBean` / `@MockitoSpyBean`. ST2/ST3 examples in this skill use `@MockBean`; on SB3.4+ codebases prefer `@MockitoBean`. The semantic checks (mock necessity, slice scope) are unchanged.

To extend coverage for SB2 or SB3.4+, follow Pattern A (broaden the rubric) per `shield/skills/backend/EXTENDING-VERSIONS.md`.

## When to Use

- Reviewing `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`, etc.
- Reviewing `@MockBean` and `@SpyBean` usage
- Reviewing Testcontainers vs H2 in-memory choices
- Reviewing test security context (`@WithMockUser`, etc.)

## When NOT to Use

- Pure JUnit assertion patterns — use `testing-strategy-review`
- Non-Spring test frameworks (pytest, jest) — different conventions
- Performance test design — separate skill not in v1

## Review Process

1. Inventory: test classes by their primary slice annotation
2. For each, apply Evaluation Points ST1–ST10
3. Cross-cut: confirm `@SpringBootTest` is reserved for full integration, not unit tests in disguise

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| ST1 | Test slice selection | Use `@WebMvcTest` for controllers, `@DataJpaTest` for repos, `@JsonTest` for serialization, `@SpringBootTest` only when truly integration-shaped | High |
| ST2 | `@MockBean` necessity | Mock collaborators that aren't part of the slice. Don't mock everything — slice annotations auto-configure the layer | Medium |
| ST3 | `@SpringBootTest` scope | Full context boot is slow. Justify when a smaller slice would work | High |
| ST4 | `@DirtiesContext` minimization | Recreating the context per test is very slow. Use only when absolutely required (rare); prefer test-data isolation via transactions or `@Sql` | High |
| ST5 | Testcontainers vs H2 | Testcontainers gives a real database (catches dialect issues). H2 is faster but masks production differences. Choose deliberately | Medium |
| ST6 | Test security context | `@WithMockUser`, `@WithUserDetails`, or custom security context. Don't disable security in tests | Medium |
| ST7 | `@Transactional` in tests | Tests marked `@Transactional` roll back automatically — good for isolation. Avoid in tests that span multiple transactions | Medium |
| ST8 | MockMvc vs WebTestClient | MockMvc for MVC; WebTestClient for WebFlux. Don't mix layers | Low |
| ST9 | Parallel test safety | If tests run in parallel, no shared mutable state across classes. `@Execution(SAME_THREAD)` for legacy tests | Medium |
| ST10 | Test data setup | `@Sql` for repo tests, `TestEntityManager.persist` in `@DataJpaTest`. Don't rely on schema state from prior tests | Medium |

## Critical Checks

- `@SpringBootTest` on a test that exercises one controller (slice annotation would be faster)
- `@DirtiesContext(classMode = BEFORE_EACH_TEST_METHOD)` (extremely slow)
- A test class with 5+ `@MockBean`s (smell — the slice is wrong)
- A test that asserts on database state without resetting between methods

## Severity Guide

| Severity | When |
|---|---|
| High | CI slowness or false confidence (heavy slice for unit-shaped test, no assertions, dirties-context per method) |
| Medium | Friction during normal feature work (wrong mock placement, missing isolation) |
| Low | Style — slice consistency, minor naming |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding `@WebMvcTest` for every controller test | Some controllers genuinely need the full context (e.g., to verify security filters interact). The smell is when `@WebMvcTest` would clearly suffice |
| Flagging all `@MockBean` usage | `@MockBean` is the right tool for external dependencies. The smell is mocking domain services already in the slice |
| Insisting on Testcontainers always | H2 is fine for repo tests that don't exercise dialect-specific SQL. Testcontainers is required when SQL features differ |
| Treating `@Transactional` tests as anti-pattern | Tx-rollback tests give clean isolation. The smell is using them when the test must span transactions (e.g., testing a saga) |
| Demanding security context in every test | Pure unit tests don't need it. The smell is integration tests bypassing security to "make tests pass" |

## Related Skills

- For test pyramid balance, mock SUT, flaky patterns → `backend-testing-strategy-review`
- For JPA repository test patterns → `backend-spring-data` (P5–P8)
- For controller test patterns alongside `@WebMvcTest` → `backend-spring-web` (W4)
```

- [ ] **Step 5: GREEN — subagent with skill**

```
You are reviewing Spring Boot test code.

Read this skill in full:
/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/skills/backend/spring-test/SKILL.md

File (apply ST1–ST10): /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/test/java/com/example/api/controller/UserControllerIntegrationTest.java

Markdown table: ST#, file, line range, severity, finding.
```

GREEN must catch all 4 oracle findings (high/high/medium/high).

- [ ] **Step 6: Refactor if needed.**

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/spring-test/ \
        shield/examples/spring-boot-api/src/test/java/com/example/api/controller/UserControllerIntegrationTest.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend spring-test skill"
```

---

### Task 7: jvm-language-review skill (TDD)

**Files:**
- Modify: `shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java` (add immutability/equals violations)
- Modify: `shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java` (add mutability violation)
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/jvm-language-review/SKILL.md`

- [ ] **Step 1: Modify User.java to add a leaky-getter violation**

Read `User.java`. After the existing `getOrders()` getter, add:

```java
    // VIOLATION: Returns the internal mutable List directly. Callers can mutate the
    // entity's state through the returned reference. Should return an unmodifiable view
    // or a defensive copy.
    public List<Order> getOrdersMutable() { return orders; }

    // VIOLATION: No equals/hashCode override on entity. Default Object identity breaks
    // HashSet semantics and Hibernate session-cache lookups in some cases.
    // (Already partially in database-review D10; jvm-language flags it as immutability/
    // value-equality concern.)
```

- [ ] **Step 2: Modify Order.java to add a mutability violation**

Read `Order.java`. Add the following at the bottom of the class (before the closing `}`):

```java
    // VIOLATION: Public mutable setter on entity field — entity is mutable across the
    // codebase. Prefer constructor + Hibernate-managed state changes via methods that
    // express intent (e.g., `applyDiscount(...)`).
    public void setAmount(double amount) { this.amount = amount; }
```

- [ ] **Step 3: Append 4 oracle rows**

```markdown
| jvm-language-review | `model/User.java` | (getOrdersMutable) | medium | Returns internal mutable list — callers can mutate entity state |
| jvm-language-review | `model/User.java` | (class level) | medium | Missing `equals`/`hashCode` on entity used in collections |
| jvm-language-review | `model/Order.java` | (setAmount) | low | Public setter on entity field — prefer intent-revealing methods |
| jvm-language-review | `model/Order.java` | (class level) | medium | Entity has mutable fields and no `equals`/`hashCode` |
```

- [ ] **Step 4: RED — subagent without skill**

```
You are reviewing Java code for JVM-language idiom concerns.

Files:
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java

List JVM/Java idiom issues: records vs manual value classes, sealed types, immutability (final fields, defensive copies, unmodifiable views), exception design, var usage, Optional usage, equals/hashCode/toString.

Markdown table.
```

- [ ] **Step 5: Write `shield/skills/backend/jvm-language-review/SKILL.md` with this EXACT content:**

```markdown
---
name: backend-jvm-language-review
description: Use when reviewing Java/Kotlin source for language-idiom concerns — records, sealed types, immutability, var, Optional, exception design, Kotlin null safety, data classes, sealed classes, scope functions, coroutines. Triggers when Java/Kotlin source files are in scope and Spring or other JVM stack is detected.
java_versions: ["17"]
kotlin_versions: ["1.9", "2.0"]
---

# JVM Language Review

## Overview

Review Java and Kotlin source for idiomatic language usage independent of framework concerns. Catches issues that compile but don't match modern idioms or that risk subtle bugs (mutability, ID-based equals, missed Optional checks, etc.).

Triggers when Java (`.java`) or Kotlin (`.kt`) source files are in scope. Pairs with `code-quality-review` (which is language-agnostic SOLID/DRY/KISS) and `spring-data` (which covers entity-specific equals/hashCode).

## Java Version Compatibility

**Supported:** Java 17 (declared via `java_versions: ["17"]` in frontmatter — matches Spring Boot 3 baseline).

**Java 11 (older LTS) — degraded coverage:**
- J1 (records): NOT AVAILABLE before Java 14 — DON'T flag missing record usage; suggest plain final-field POJO
- J2 (sealed types): NOT AVAILABLE before Java 17 — DON'T flag closed hierarchies as needing `sealed`; suggest enum or class hierarchy with package-private constructors
- J3–J10: all apply

**Java 8 (legacy) — degraded coverage:**
- J1, J2: not available (see Java 11 above)
- J5 (var): NOT AVAILABLE before Java 10 — DON'T flag missing var; explicit types are required
- J7 (try-with-resources): applies, but final-effectively-final var-in-resource is Java 9+
- Other checks apply

The agent passes the detected Java major version to this skill; the skill gates language-feature checks accordingly. For new Java versions (e.g., Java 21 with virtual threads, sequenced collections), follow Pattern A (broaden the rubric) per `shield/skills/backend/EXTENDING-VERSIONS.md`.

**Kotlin coverage:** The skill body covers Kotlin (K1–K5) conceptually. Fixture-level RED-GREEN testing for Kotlin is deferred to a follow-on (no `.kt` files in the v1 fixture).

## When to Use

- Reviewing Java domain classes for records / sealed types / immutability
- Reviewing Kotlin classes for null safety and data class patterns
- Auditing exception design choices
- Pre-implementation: shaping a new model or value class

## When NOT to Use

- Cross-cutting structure concerns (SOLID, DRY) — use `code-quality-review`
- Spring annotations on the same class — use the relevant Spring skill
- Pure performance — separate skill not in v1

## Review Process

1. Inventory: Java/Kotlin source files in scope (excluding test files unless test code is the target)
2. For each, apply Evaluation Points J1–J10
3. Cross-cut: trace value types through the system; flag mutable surface where immutability would be safer

## Evaluation Points

### Java

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| J1 | Records over manual value classes | Java 14+: prefer `record` for immutable data carriers (DTOs, value objects, tuple-like types) over hand-written final-field POJOs | Medium |
| J2 | Sealed types for closed hierarchies | When a base type has a known set of subclasses, `sealed` + `permits` makes the contract explicit and enables exhaustive `switch` | Medium |
| J3 | Immutability by default | `final` fields where mutation isn't required. Returning unmodifiable collection views from getters. Defensive copies on input | High |
| J4 | Exception design | Domain-specific `RuntimeException` subtypes (e.g., `OrderNotFoundException`); don't throw bare `RuntimeException` for everything. Avoid checked exceptions for control flow | Medium |
| J5 | `var` usage clarity | `var` is fine when the type is obvious from context; avoid when it hides a long generic or unfamiliar return type | Low |
| J6 | Optional discipline | Don't use `Optional` for fields or method parameters. `.get()` only after `.isPresent()` (or use `.orElse`/`.orElseThrow`/`.map`) | Medium |
| J7 | try-with-resources | Use `try (var r = ...)` for `AutoCloseable`. Don't manage `close()` manually | Medium |
| J8 | equals/hashCode/toString consistency | Override all three together (or none for identity-based). For records, you get them for free | Medium |
| J9 | Stream API readability | Avoid nested streams, side-effects in `forEach`, and unreadable `collect`. Extract complex pipelines into named methods | Low |
| J10 | Enum vs constants | Prefer `enum` over `public static final int` constants for closed sets of named values | Low |

### Kotlin (skill text only — fixture-level Kotlin RED-GREEN deferred to follow-on)

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| K1 | Null safety | Don't use `!!` to assert non-null without certainty. Prefer `?.let` / `?: ...` chains | High |
| K2 | `data class` for value carriers | Use `data class` for DTOs and value objects — get equals/hashCode/toString/copy automatically | Medium |
| K3 | Sealed classes for closed hierarchies | `sealed class` / `sealed interface` with `when` exhaustiveness | Medium |
| K4 | Scope functions | `let`, `also`, `apply`, `with`, `run` — pick the one whose semantics match. Don't nest deeply | Low |
| K5 | Coroutine launching | `viewModelScope.launch` / `coroutineScope { ... }` — don't use `GlobalScope.launch` for app code | High |

## Critical Checks

- A getter that returns the internal mutable collection directly (`return list;` instead of `Collections.unmodifiableList(list)`)
- An exception design that catches `Throwable` and rethrows as `RuntimeException` (loses type info)
- A class meant to be a value type with mutable fields and no equals/hashCode
- Use of `Optional` as a field type
- (Kotlin) `!!` operator on a value that could legitimately be null

## Severity Guide

| Severity | When |
|---|---|
| High | Mutability that breaks invariants, null assertions that crash at runtime |
| Medium | Idiom drift that obscures intent or makes evolution harder |
| Low | Style — naming, var, stream readability |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding records on every value class | Records are a strong default but don't fit when JPA proxying is needed (entities) or when frameworks reflect on getters/setters |
| Flagging all mutable fields as wrong | Domain entities often need controlled mutability via methods. The smell is fields exposed via setters |
| Insisting on Optional for return types | Optional is for return types of "find X — may not exist". Don't use as method parameters or fields |
| Treating `var` as always bad | `var` improves readability when the RHS is clearly typed. The smell is `var x = service.compute(...)` where the type is non-obvious |
| (Kotlin) Demanding `?` nullable types everywhere | Defensive nullability is the default in Kotlin; the smell is overuse of `!!` to bypass it |

## Related Skills

- For SOLID/DRY/KISS structural concerns → `backend-code-quality-review`
- For entity-specific equals/hashCode and lifecycle → `backend-spring-data` (P7)
- For Spring `@Configuration` annotation correctness on Java/Kotlin classes → `backend-spring-config`
```

- [ ] **Step 6: GREEN — subagent with skill**

```
You are reviewing Java code for JVM-language idiom concerns.

Read this skill in full:
/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/skills/backend/jvm-language-review/SKILL.md

Files (apply J1–J10):
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java
- /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java

Skip Kotlin checks (K1–K5) for this run — no Kotlin files present.

Markdown table: J#, file, line range, severity, finding.
```

GREEN must catch all 4 oracle findings (medium/medium/low/medium).

- [ ] **Step 7: Refactor if needed.**

- [ ] **Step 8: Commit**

```bash
git add shield/skills/backend/jvm-language-review/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java \
        shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend jvm-language-review skill"
```

---

### Task 8: End-to-end validation against the extended fixture

**Files:**
- (No file changes — validation step; if gaps found, refine skill files and recommit)

- [ ] **Step 1: Dispatch backend-reviewer end-to-end**

Use `Agent` tool, `subagent_type: general-purpose`, `model: opus` (orchestration). Send:

```
You are the backend-reviewer agent.

Read in full: /Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/agents/backend-reviewer.md

Apply the agent's behavior end-to-end against the fixture at:
/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/shield/examples/spring-boot-api/

Detect the stack via pom.xml (expected: Java/Kotlin Spring Boot — should detect web, data, config, security, test starters and load all 6 Spring skills + jvm-language-review + 7 agnostic skills).

Read each SKILL.md under shield/skills/backend/ (13 skills total now: 7 agnostic + 6 framework). Apply each skill's Evaluation Points to the relevant fixture files, and produce the agent's standard output format with module grouping.

Do NOT dispatch specialists for this validation — focus on skill output.

Output the full Backend Review report.
```

- [ ] **Step 2: Compare against the oracle**

Read `shield/examples/spring-boot-api/docs/expected-findings.md`. The agent's output must include every row in the oracle. After Plan 2:

- Plan 1 oracle: 38 findings (7 agnostic skills)
- Plan 2 additions: ~27 findings (6 framework skills × 4-5 each)
- **Expected total: ~65 oracle entries**

Confirm the actual oracle row count matches the running total of skill TDD additions across Tasks 2–7.

- [ ] **Step 3: Document gaps**

If any oracle entry is missed, identify the responsible skill and refine its Evaluation Points / Critical Checks. Re-run the e2e dispatch until all oracle entries are caught.

If skills produce findings NOT in the oracle, note them as bonus findings (candidates for adding to the oracle in a follow-up).

- [ ] **Step 4: Commit any skill refinements**

```bash
git add shield/skills/backend/ shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "fix(shield): refine backend Spring/JVM skills based on end-to-end validation"
```

If no refinements were needed, skip this step.

---

### Task 9: Bump shield to 2.11.0

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read the current shield version**

Read `.claude-plugin/marketplace.json`. Confirm the shield entry's `version` is currently `"2.10.0"` (set by Plan 1).

- [ ] **Step 2: Bump to 2.11.0**

Change `"2.10.0"` to `"2.11.0"`. Per `CLAUDE.md`, version stays only in `marketplace.json` — do not add a `version` field to `shield/.claude-plugin/plugin.json`. Shield has no `pyproject.toml` at the plugin root, so no pyproject bump.

- [ ] **Step 3: Verify**

```bash
git diff .claude-plugin/marketplace.json
```

Expected: a single-line change in the shield entry's version (`2.10.0` → `2.11.0`).

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.11.0 — Spring/JVM skills (Plan 2)"
```

---

## Self-review checklist (run at end of plan execution)

Before declaring Plan 2 complete:

- [ ] All 6 Spring/JVM skills exist under `shield/skills/backend/`
- [ ] Each skill has corresponding fixture violations and oracle rows in `shield/examples/spring-boot-api/docs/expected-findings.md`
- [ ] `shield/agents/backend-reviewer.md` includes the conditional Spring sub-detection table and updated Skill Loading section
- [ ] `.claude-plugin/marketplace.json` shows shield at `2.11.0`
- [ ] End-to-end validation (Task 8) passes — all oracle findings caught
- [ ] No SKILL.md contains a TBD/TODO
- [ ] All commits on the feature branch (whichever branch is being used for Plan 2 — could be the same as Plan 1 if user opted for a single PR)

## After Plan 2 ships

Plan 3 picks up the SDLC integration work: `/plan` domain-detection step (pre-existing gap — not backend-specific), `/plan-review` reviewer auto-detect registration, `/implement` per-step domain hook extension. With Plan 3 done, backend skills inform the full SDLC, not only post-hoc review.

A future iteration adds Kotlin RED-GREEN coverage for `jvm-language-review` (skill body already covers Kotlin conceptually; needs a Kotlin file in the fixture to validate the K1–K5 checks).
