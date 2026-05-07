---
name: backend-error-observability-review
description: Use when reviewing code for error handling, exception flow, logging, metrics, and tracing concerns. Triggers when exception handlers, error responses, logging calls, or observability instrumentation are in scope.
---

# Backend Error & Observability Review

## Overview

Review backend code for proper error handling and observability instrumentation: exception type design, propagation patterns, logging discipline (level, structure, context), metric coverage, trace context propagation, and correlation ID hygiene.

Framework-agnostic: applies to Spring `@ControllerAdvice`, FastAPI exception handlers, Express error middleware, Go error wrapping, etc.

## When to Use

- Reviewing exception handlers, error response shapers
- Reviewing services that perform IO (DB, HTTP, queue)
- Auditing observability gaps in a critical path
- Pre-implementation: shaping error contract during planning

## When NOT to Use

- Pure infra-level monitoring config — different skill
- Frontend error handling — backend-specific patterns may not apply

## Review Process

1. Inventory: exception handlers, try/catch blocks, log calls, metric/trace instrumentation
2. For each, apply Evaluation Points E1–E10
3. Cross-cut: trace a request path and check that every IO point has structured logging + error path

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| E1 | Exception type design | Domain-specific exception types (e.g., `OrderNotFoundException`), not bare `RuntimeException` for everything | Medium |
| E2 | No catch-all that maps to 5xx | Catching `Throwable`/`Exception` and returning 500 hides client errors. Map by type | High |
| E3 | No silent swallows | Every `catch` either rethrows, logs at appropriate level, increments a metric, or transforms to a domain result. Empty catches are bugs | High |
| E4 | Exception-as-control-flow avoidance | Don't throw + catch within the same method to drive branching. Use return values or guard clauses | Medium |
| E5 | Log level discipline | DEBUG for trace, INFO for state transitions, WARN for recoverable issues, ERROR for true failures. Flag `println` or `System.err` | High |
| E6 | Structured logging | Logs use key-value/JSON, not string concatenation. Flag `log.info("user " + id + " did " + action)` | Medium |
| E7 | Correlation/trace context | Logs include request/trace ID. Distributed services propagate trace headers | High |
| E8 | Metric coverage on critical paths | Counter on errors per endpoint, latency histogram on external calls, business metrics on key flows | Medium |
| E9 | No internal details in error responses | Don't return stack traces, SQL fragments, or framework messages to clients | High |
| E10 | Idempotency on retried error paths | When retrying after a transient error, the operation must be safe to repeat | Medium |

## Critical Checks

- A `@ExceptionHandler(Throwable.class)` or `@ExceptionHandler(Exception.class)` that responds 500
- A `try { ... } catch (Exception e) {}` with empty body
- A `printStackTrace()` or `System.out.println` in production code paths
- An error response containing the raw exception message
- An external call (HTTP, DB, queue) without timeout, retry, or metric

## Severity Guide

| Severity | When |
|---|---|
| High | Operational impact: silent failures, leaked internals, missing critical observability |
| Medium | Friction: poor log structure, exception-as-control-flow, missing exception type design |
| Low | Style: log format nits, naming |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding metric on every method | Metrics belong on critical paths; over-instrumentation is its own anti-pattern |
| Flagging all RuntimeException as bad | RuntimeException is the right base for unchecked errors; the smell is using it without semantic meaning |
| Insisting all logs be JSON | Plaintext is fine for local dev; structured matters in aggregated systems |
| Treating catch-and-rethrow-with-context as redundant | Wrapping with context (`throw new OrderProcessingException("for order " + id, e)`) is good practice |
| Penalizing tests with println | Test code's logging discipline is laxer; this skill targets production paths |

## Related Skills

- For HTTP-level error response shape → `backend-api-design-review`
- For underlying code structure → `backend-code-quality-review`
- For Spring-specific exception handling (Plan 2) → `spring-web`
