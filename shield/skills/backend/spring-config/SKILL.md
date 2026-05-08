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
