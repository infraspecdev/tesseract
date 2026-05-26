---
name: backend-code-quality-review
description: Use when reviewing backend code for SOLID/DRY/KISS/YAGNI violations, naming, cohesion, and coupling. Triggers when source files in a backend stack (Java, Kotlin, Python, Node/TS, Go) are in scope. Skip for infrastructure code (Terraform, K8s manifests).
---

# Backend Code Quality Review

## Overview

Review backend source code against language- and framework-agnostic software-engineering principles: SOLID, DRY, KISS, YAGNI, naming clarity, cohesion at the type level, and coupling between modules. The skill flags structural smells that make code hard to evolve, not surface-level style issues.

Triggers on backend stacks (file paths under `services/`, `src/`, `backend/`, presence of `pom.xml`, `package.json`, `pyproject.toml`, `go.mod`). Does not apply to infra code.

## When to Use

- Reviewing changes to service classes, domain models, controllers, repositories
- Auditing a new module before merge
- Pre-implementation: shaping the design while writing a plan

## When NOT to Use

- Pure infrastructure code — use the relevant infra skill
- Trivial changes (one-line fixes, comment-only edits, generated code)
- Performance review — separate concern
- Security review — use the security-engineer agent

## Review Process

1. Identify all source files in scope
2. For each file, walk through the Evaluation Points below and grade
3. Where a check fails, write a finding with file path, line range, severity, and a one-sentence recommendation
4. Group findings by file in the output

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| Q1 | Single Responsibility | Each class/module has one reason to change. Flag god classes (services that handle multiple unrelated domains), fat methods doing 4+ things, mixing transport/business/persistence concerns | High |
| Q2 | Open/Closed | Extension points where they make sense; no `if-else` chains that grow with each new type. Strategy/polymorphism over type checks | Medium |
| Q3 | Interface segregation | Interfaces are small and role-specific. Flag fat interfaces clients implement only partially | Medium |
| Q4 | Dependency direction | High-level modules don't depend on low-level details. Flag domain code reaching into framework specifics | Medium |
| Q5 | DRY | Duplicated logic across methods/classes. Flag copy-paste with minor variation; suggest extraction | High |
| Q6 | KISS | Simple solutions for the actual requirement. Flag over-engineering, unnecessary abstraction layers, "framework-y" indirection | Medium |
| Q7 | YAGNI / speculative generality | Unused parameters, configuration knobs nothing reads, abstract base classes with one subclass, "future-proof" interfaces | Medium |
| Q8 | Naming | Names match what the code does. Flag `x`, `tmp`, `data`, `do2`, `helper` (without context), inconsistent casing for the same concept | Low to Medium |
| Q9 | Function/method size | Functions short enough to hold in mind. Flag methods over ~30 lines or with nesting depth >3 | Medium |
| Q10 | Coupling | Modules depend on abstractions, not concretions. Flag direct instantiation across module boundaries (`new ConcreteService()` in a domain class) | Medium |

## Critical Checks

- A service class with method names spanning multiple business domains (god class)
- A method that performs side effects in 3+ unrelated systems (DB write + external call + email + audit log)
- Two methods whose bodies are 80%+ identical
- A class with `@Configuration` + `@Service` + `@RestController` annotations on the same type

## Severity Guide

| Severity | When |
|---|---|
| High | The code will be expensive to change. SRP/DRY violations that block evolution |
| Medium | Friction during normal feature work. Naming/coupling/KISS issues |
| Low | Stylistic. Naming nits, minor nesting, single-letter variables in narrow scopes |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Flagging short controller methods as "too short" | Controllers are thin by design; the smell is logic-in-controllers, not size |
| Calling all duplication a DRY violation | Two similar lines is fine; three or more across distant call sites is worth flagging |
| Demanding interfaces for every class | Premature interfaces are themselves YAGNI — only add when there are 2+ real implementations or a stable seam exists |
| Treating "magic numbers" as code-quality issues | Constants are a different concern; this skill focuses on structure, not literals |
| Penalizing test code with the same rubric | Tests have different shape (Arrange/Act/Assert) — don't apply SRP to test methods the same way |

## Related Skills

- For API contract concerns → `backend-api-design-review`
- For framework-specific issues (Spring annotations, etc.) → relevant Spring skill (Plan 2)
- For test-code design → `backend-testing-strategy-review`
