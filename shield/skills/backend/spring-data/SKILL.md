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
