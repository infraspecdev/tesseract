---
name: backend-concurrency-review
description: Use when reviewing code for concurrency concerns — race conditions, lock granularity, async pitfalls, retry idempotency, shared mutable state. Triggers when threading, async patterns, or shared state are in scope.
---

# Backend Concurrency Review

## Overview

Review backend code for concurrency correctness: race conditions on shared mutable state, lock granularity and scope, async-pattern pitfalls (forgotten await, fire-and-forget exception loss, callback hell), idempotency for retried operations, and safe shared state across request threads.

Framework-agnostic but with examples in JVM threading, JS async/await, Python asyncio, Go goroutines.

## When to Use

- Reviewing services with shared state (singletons, statics, module globals)
- Reviewing async/await/CompletableFuture/goroutine code
- Auditing retry logic for idempotency
- Reviewing concurrent collections and locking patterns

## When NOT to Use

- Pure single-threaded logic — concurrency rubric does not apply
- Distributed coordination (consensus, leader election) — separate skill not in v1
- Database isolation level review — covered by `database-review`

## Review Process

1. Inventory: shared state (singletons, statics, beans with mutable fields), async call sites, locks
2. For each, apply Evaluation Points C1–C10
3. Cross-cut: trace a request path; flag every shared write that is not synchronized

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| C1 | Shared mutable state | Singleton beans, static fields, module-level vars holding mutable collections without synchronization | High |
| C2 | Read-modify-write atomicity | `x = x + 1` on a shared field. Use atomic types (`AtomicInteger`, `LongAdder`) or explicit locks | High |
| C3 | Concurrent collection choice | `HashMap` not safe for concurrent access; use `ConcurrentHashMap`. Same for lists and sets | High |
| C4 | Lock granularity | Fine-grained locks where contention matters; avoid `synchronized(this)` over wide methods | Medium |
| C5 | Async exception loss | `CompletableFuture.runAsync` / `setTimeout` / `goroutine` whose exceptions go nowhere | High |
| C6 | Forgotten `await` / `.get()` | Async result ignored; exception happens later in detached context | Medium |
| C7 | Idempotency on retry | Operations that may retry must be safe to repeat — no double-charge, double-create, double-send | High |
| C8 | Cancellation handling | Long async tasks honor cancellation tokens / `Thread.interrupted` / `ctx.Done()` | Medium |
| C9 | Deadlock risk | Two locks acquired in inconsistent order across paths. Resource hierarchy not enforced | Medium |
| C10 | Backpressure on async producers | Unbounded queues / unbounded fan-out can OOM. Bound the queue or rate-limit upstream | Medium |

## Critical Checks

- A `HashMap` or `ArrayList` field on a singleton accessed from multiple request threads
- `count++` or `total += x` on a shared field with no synchronization
- `CompletableFuture.runAsync(task)` with no `.exceptionally`/`whenComplete` handler
- Retried operation that performs an external write without an idempotency key
- Two locks acquired in different orders across two methods

## Severity Guide

| Severity | When |
|---|---|
| High | Data corruption risk, lost errors, double-side-effect on retry |
| Medium | Contention, deadlock potential, missing cancellation hygiene |
| Low | Stylistic threading nits |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Treating all `synchronized` as bad | Synchronization is the right tool when the cost (contention) is acceptable |
| Demanding atomic types everywhere | Single-threaded paths don't need atomics; the smell is shared mutable state, not the type itself |
| Flagging non-shared mutable fields | A field on a per-request object is fine; the smell is shared state across threads |
| Treating all async as risky | Async patterns are valuable; the smell is uncaught failures, not the technique |
| Demanding idempotency on read paths | Reads are naturally idempotent; the smell is non-idempotent writes/sends in retry-prone paths |

## Related Skills

- For deployment-time multi-instance concerns → `backend-deployment-safety-review`
- For database-level concurrent access (transactions, isolation) → `backend-database-review`
