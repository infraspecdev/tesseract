---
name: backend-api-design-review
description: Use when reviewing REST/HTTP or GraphQL APIs for resource modeling, HTTP method semantics, status codes, idempotency, versioning, error response shape, and pagination. Triggers when controllers/handlers/resolvers are in scope.
---

# Backend API Design Review

## Overview

Review HTTP/REST and GraphQL APIs against established conventions: resource-oriented URIs, correct HTTP method semantics, accurate status codes, idempotency where required, consistent error response shape, versioning strategy, and pagination on list endpoints.

The skill is framework-agnostic — applies equally to Spring `@RestController`, Express routes, FastAPI path operations, Gin handlers, etc.

## When to Use

- Reviewing controllers, route handlers, GraphQL resolvers
- Designing a new endpoint during planning
- Auditing API contract changes for backwards compatibility

## When NOT to Use

- Internal RPC between services using non-HTTP transports — different conventions
- Async messaging (Kafka, SQS) — separate review concern
- Static asset serving — no API design surface

## Review Process

1. Inventory all endpoints in scope (HTTP method + path + handler)
2. For each endpoint, walk through Evaluation Points A1–A10
3. Group findings by endpoint in the output
4. Note cross-endpoint inconsistencies (e.g., error shape varies between handlers)

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| A1 | Resource-oriented URIs | Nouns, not verbs (`/users` not `/getUsers`/`/createUser`). Hierarchies via path segments | Medium |
| A2 | HTTP method semantics | GET = safe + idempotent; POST = create / non-idempotent; PUT = full replace + idempotent; PATCH = partial; DELETE = remove | High |
| A3 | Status code accuracy | 200 only on success with body; 201 on resource creation with `Location`; 204 on success with no body; 4xx for client error; 5xx for server error. Wrong 2xx family (e.g. 200 vs 204) is Low; masking errors with 200 (e.g. returning 200 for a not-found) is High | High / Low |
| A4 | Idempotency | PUT and DELETE must be idempotent. POST may use idempotency keys for retried clients | High |
| A5 | Error response consistency | Single shape across all handlers (e.g., `{ "error": { "code", "message", "details" } }`). No mixing `{ error: "..." }` and structured shapes | Medium |
| A6 | Versioning strategy | URI version (`/v1/...`), header version, or content negotiation. No unversioned public APIs | Medium |
| A7 | Pagination | List endpoints support pagination (offset/limit, cursor, page tokens). Documented limits | Medium |
| A8 | Filtering & sorting | Standard query parameter conventions; no exposing DB query syntax raw | Low |
| A9 | Validation surface | Input validated at the boundary (annotations, schema validators); validation errors return 4xx with field details | Medium |
| A10 | Resource representation consistency | Same resource has same fields across endpoints. No selective field hiding without explicit projection params | Medium |

## Critical Checks

- A GET endpoint that mutates state
- A PUT or DELETE that produces different state on repeated calls
- A 200 OK returned on a 404-shaped condition (resource not found)
- An endpoint returning two different error shapes for two different errors
- A list endpoint with no pagination on a table that grows unbounded

## Severity Guide

| Severity | When |
|---|---|
| High | Wrong HTTP method, masking errors with 2xx (e.g. returning 200 for a not-found), missing idempotency on PUT/DELETE — these break clients |
| Medium | Inconsistent error shape, missing pagination, missing versioning, wrong 2xx subcode that hides intent (e.g. 200 vs 201 on create) — friction but not breakage |
| Low | 200 vs 204 on successful DELETE (body vs no-body), URI casing inconsistencies, field-name style nits — surface-level |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding pagination on every endpoint | Pagination matters for unbounded collections; a `/me` or `/health` is fine returning a single resource |
| Flagging POST as wrong for non-creation actions | "Action" endpoints (login, search complex queries) often use POST legitimately when no idempotency key is feasible |
| Insisting on 201 for every create | 200 with body is acceptable when there's no canonical resource location to return |
| Treating internal admin APIs the same as public | Public APIs need versioning + stable error shapes; internal APIs may be looser |
| Calling all GraphQL "anti-REST" | GraphQL has its own conventions — apply A1/A4/A7 differently (single endpoint, fragments, connections) |

## Related Skills

- For underlying code structure → `backend-code-quality-review`
- For test design around endpoints → `backend-testing-strategy-review`
- For Spring `@RestController` specifics → `spring-web`
- For error handling shape → `backend-error-observability-review`
