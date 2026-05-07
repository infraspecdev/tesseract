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
