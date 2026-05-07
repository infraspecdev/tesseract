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
