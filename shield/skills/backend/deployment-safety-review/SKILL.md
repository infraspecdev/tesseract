---
name: backend-deployment-safety-review
description: Use when reviewing code for deployment safety — feature flags on risky changes, backwards-compatible API/schema evolution, rollback paths, blast-radius scoping, multi-instance safety, expand/contract migration patterns. Triggers when migration files, config beans, or production-critical paths are in scope.
---

# Backend Deployment Safety Review

## Overview

Review backend changes for safe deployment in production: feature flag readiness for risky behavior changes, backwards-compatible evolution of public APIs and database schemas, rollback paths, blast-radius scoping, and correctness across multiple application instances.

Framework-agnostic: applies to any service that ships through a CD pipeline with rolling deploys, blue/green, or canary rollouts.

## When to Use

- Reviewing changes that affect public API contracts
- Reviewing migration files (Flyway, Liquibase, Alembic)
- Reviewing config files / config beans / static toggles
- Pre-implementation: planning rollout strategy

## When NOT to Use

- Internal scripts run once on a developer machine — different concerns
- Pure documentation / comment-only changes
- Operational deploy mechanics (Helm chart, K8s rollout strategy) — use kubernetes domain skills

## Review Process

1. Inventory: API contract changes, migration files, config files, beans with state
2. For each, apply Evaluation Points S1–S10
3. Cross-cut: ensure the change can roll back in <5 minutes; ensure two consecutive versions can run side-by-side

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| S1 | Feature flag for risky changes | Behavior changes that affect business logic gated behind a runtime flag with default-off | High |
| S2 | API backwards compatibility | Existing endpoints unchanged, OR new endpoints added alongside, OR Sunset/Deprecation headers + transition window | High |
| S3 | Schema migration safety | Adds are safe; column drops/renames use expand/contract pattern across two deploys; no data loss without explicit migration | High |
| S4 | Rollback path | Code change is reversible. If the migration is not reversible, the application code must tolerate the old schema for the rollback window | High |
| S5 | Blast radius | Change is scoped to a small set of users/tenants/endpoints first (canary, percentage rollout) when impact is uncertain | Medium |
| S6 | Multi-instance state safety | No process-local mutable state shared across requests in a multi-instance deploy. In-memory caches must be acknowledged and bounded; sticky sessions must be deliberate | High |
| S7 | Configuration externalization | Config that varies per environment lives in env vars / config server, not committed source | Medium |
| S8 | Migration ordering | Code that reads new schema deploys after migration; code that writes old schema deploys before drop migrations | High |
| S9 | Idempotent deploy hooks | Startup hooks, init containers, schema bootstrap can run multiple times safely | Medium |
| S10 | No global side effects on import | Importing a module / loading a class doesn't mutate the world (e.g., no DB writes in a static initializer) | Medium |

## Critical Checks

- A migration that DROPs a column whose old name is still read by the deployed application
- An in-memory cache or session store in a singleton bean (or process global) without explicit single-instance constraint
- A risky feature change merged without a flag that allows runtime kill
- Removing a public endpoint or response field without a deprecation window
- Code that requires a specific deploy order with no enforcement

## Severity Guide

| Severity | When |
|---|---|
| High | Outage risk on next deploy, data loss potential, breaking change without compat path |
| Medium | Friction during rollout, no kill switch on a moderately risky change |
| Low | Stylistic config externalization preferences |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding flags on every change | Only behavior changes with uncertain impact need flags. Refactors and bug fixes don't |
| Treating all in-memory data as a violation | Bounded caches with eviction are fine on a single-instance service or stateless tier with sticky sessions; the smell is unbounded shared state |
| Flagging all migrations as risky | Pure adds are safe; the smell is destructive ops on hot paths during rolling deploys |
| Forcing all configs into env vars | Build-time constants and feature defaults are fine in source; secrets and environment-varying values aren't |

## Related Skills

- For migration data-design specifics → `backend-database-review`
- For multi-instance concurrency → `backend-concurrency-review`
- For API contract evolution → `backend-api-design-review`
