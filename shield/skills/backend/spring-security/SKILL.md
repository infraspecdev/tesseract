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
