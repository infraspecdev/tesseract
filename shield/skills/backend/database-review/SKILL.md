---
name: backend-database-review
description: Use when reviewing database schema design, migrations, ORM entity definitions, or query patterns. Triggers when SQL files (`*.sql`), migration directories (`db/migration/`, `migrations/`, `alembic/`), JPA entities, or ORM model files are in scope.
---

# Backend Database Review

## Overview

Review database-related code for schema design (normalization, foreign keys, indexes), migration safety (zero-downtime, additive-only on hot paths), ORM entity correctness (fetch strategy, equals/hashCode, cascades), and query patterns (N+1, full table scans, missing pagination).

Framework-agnostic: applies to JPA/Hibernate, SQLAlchemy, ActiveRecord, Sequelize, GORM, raw SQL.

## When to Use

- Reviewing changes to entity/model classes
- Reviewing repository/DAO methods
- Auditing migration files (Flyway, Liquibase, Alembic, Rails migrations)
- Pre-implementation: shaping schema during planning

## When NOT to Use

- Pure runtime DB tuning (query plans, vacuum, replication) — operational concern
- NoSQL document modeling (separate skill not in v1)
- Reviewing application logic that uses DB results without DB code itself

## Review Process

1. Inventory: entities, repositories/DAOs, migration files, query strings
2. For each artifact, apply Evaluation Points D1–D10
3. Cross-cut: detect N+1 risk by reading entity fetch type alongside repo methods
4. Group findings by file and migration version

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| D1 | Schema normalization | 3NF for OLTP unless explicit denormalization for read perf. Flag obvious anti-normalization (CSV in a column, repeating groups) | Medium |
| D2 | Foreign key integrity | FKs declared on every reference. Flag soft references via `_id` columns without FK | High |
| D3 | Index coverage | Indexes on lookup columns, FK columns, columns used in WHERE/ORDER BY. Flag obvious missing indexes | High |
| D4 | Column constraints | NOT NULL where appropriate, UNIQUE where business rules require, length limits for VARCHAR | Medium |
| D5 | ORM fetch strategy | LAZY by default for relationships; EAGER only with explicit justification. Flag EAGER on collections | High |
| D6 | N+1 query risk | Repository methods that load parents and lazy-load children one-by-one. Suggest fetch join or `@EntityGraph` | High |
| D7 | Pagination on list queries | List endpoints support pagination. Flag `findAll`-style on tables that grow unbounded | Medium |
| D8 | Migration safety (additive vs destructive) | Adds are safe; drops/renames need expand/contract pattern across two deploys | High |
| D9 | Transaction boundaries | Read methods marked readOnly where applicable; write methods scope tx narrowly. Flag ambient/no-tx writes | Medium |
| D10 | equals/hashCode on entities | Use natural keys or business identifiers; avoid using auto-generated ID before persistence (HashSet bugs) | Medium |
| D11 | Explicit table/column naming | Entities should declare `@Table(name=...)` and key `@Column(name=...)` to prevent schema drift when class names change | Medium |

## Critical Checks

- A migration that DROPs a column or RENAMEs a column without an expand/contract sequence
- A `@OneToMany`/`@OneToMany` with `fetch = EAGER`
- A repository `findAll()` returning all rows on a table with no row-count cap
- An `@ManyToMany` join without an explicit join entity (cascading delete surprises)
- Indexes only on PK; lookup columns un-indexed

## Severity Guide

| Severity | When |
|---|---|
| High | Production outage risk: destructive migration, N+1 at scale, missing indexes on hot paths |
| Medium | Performance friction or correctness risk under future growth |
| Low | Stylistic: column naming, comment density |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding indexes on every column | Indexes have write cost — only index columns used in WHERE/ORDER BY/JOIN |
| Flagging EAGER on `@ManyToOne` | Single-row eager fetch is usually fine; the smell is EAGER on collections |
| Treating all migration drops as bad | Drops are fine in green-field or pre-launch; the smell is drops on hot tables in production deploys |
| Calling `findAll` an anti-pattern | Fine for small reference tables (countries, currencies); the smell is `findAll` on growing tables |
| Demanding compound indexes everywhere | Compound indexes have query-shape constraints; only suggest when the query pattern justifies it |

## Related Skills

- For Spring-specific transactional boundary issues → `spring-data`
- For deployment ordering of migrations → `backend-deployment-safety-review`
- For underlying code structure → `backend-code-quality-review`
