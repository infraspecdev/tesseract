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
