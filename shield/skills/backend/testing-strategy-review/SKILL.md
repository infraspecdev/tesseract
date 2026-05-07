---
name: backend-testing-strategy-review
description: Use when reviewing test code for strategy quality — pyramid balance, mock boundaries, fixture/setup correctness, flaky patterns, behavior-vs-implementation tests, missing assertions. Triggers when test files (`*Test.java`, `test_*.py`, `*.test.ts`, `*_test.go`) are in scope.
---

# Backend Testing Strategy Review

## Overview

Review test code against principles of effective automated testing: appropriate test scope (unit vs integration vs e2e), mocking only at correct boundaries (collaborators not the class under test), avoidance of flaky patterns (timing, network, shared state), assertions that validate behavior over implementation, and meaningful coverage of critical paths.

## When to Use

- Reviewing PR diffs that include test code
- Auditing a test suite during onboarding
- Pre-implementation: planning the test strategy for a new feature

## When NOT to Use

- Production code review — use `code-quality-review`
- Coverage % evaluation — measure with tooling, this skill checks design
- Performance testing strategy — separate skill (not in v1)

## Review Process

1. Identify all test files in scope
2. For each test class/file, walk through Evaluation Points T1–T10
3. Cross-cut: assess pyramid balance (count of unit vs integration vs e2e)
4. Flag flaky patterns separately — even a passing flaky test is a finding

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| T1 | Test scope correctness | Unit tests use no framework context; integration tests use a focused slice; e2e uses full stack. Flag full-stack annotations on unit-shaped tests | High |
| T2 | Mock target | Mock collaborators, not the class under test. Mocking the SUT is a smell — the test exercises the mock, not the code | High |
| T3 | Assertion presence | Every test has at least one meaningful assertion. Flag tests with no asserts or `assertNotNull(obj)` on a constructed object | High |
| T4 | Behavior vs implementation | Assertions target the public contract. Flag tests that assert internal collaborators were called when the behavior is observable through the contract | Medium |
| T5 | Test isolation | No shared mutable state between tests. Flag static counters, file system state, database state without rollback | High |
| T6 | Flaky patterns | No sleeps, no time-of-day dependencies, no network to real services, no race-prone parallelism without sync | High |
| T7 | Setup/teardown clarity | Setup is per-test or per-class explicitly. Flag implicit ordering dependencies | Medium |
| T8 | Test naming | Names describe behavior under test (`registerUser_withDuplicateEmail_throws`). Flag `test1`, `testFoo`, `simpleTest` | Low |
| T9 | Pyramid balance (cross-cut) | Many unit, fewer integration, few e2e. Flag inverted pyramids — many slow tests, few fast ones | Medium |
| T10 | Edge case coverage | Critical paths have happy + at least one failure case. Flag tests that only cover the success path | Medium |

## Critical Checks

- A test that mocks the class under test and asserts the mock's stubbed return value
- A test with no assertions
- A test using `Thread.sleep` to coordinate with async work
- Static or instance state mutated across tests
- Heavy framework annotations (`@SpringBootTest`, `pytest fixtures` loading the world) on tests that could be plain units

## Severity Guide

| Severity | When |
|---|---|
| High | Test gives false confidence (no assertions, mocked SUT) or is flaky in CI |
| Medium | Test is correct but mis-scoped or has style issues that hurt maintainability |
| Low | Naming, formatting, minor structural nits |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding only-unit tests | Integration and e2e tests are valuable; the smell is the wrong scope for the test's intent |
| Flagging all `@SpringBootTest` use | Legitimate when integration is the actual goal — flag when the test is shaped like a unit test |
| Penalizing fixtures and shared setup | Per-class `@BeforeAll` is fine for read-only setup; the smell is mutable state changed by each test |
| Treating golden-master / snapshot tests as anti-patterns | Snapshots are a valid technique for stable outputs; flag only if the snapshot is unreviewed or huge |
| Demanding 100% branch coverage | Coverage strategy is product-driven; the skill checks design, not coverage |

## Related Skills

- Spring-specific test slicing (`@WebMvcTest`, `@DataJpaTest`, Testcontainers) — Plan 2 `spring-test`
- For production code quality → `backend-code-quality-review`
