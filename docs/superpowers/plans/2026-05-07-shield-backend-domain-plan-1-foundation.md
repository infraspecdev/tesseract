# Shield Backend Domain — Plan 1: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the foundation of shield's new backend domain — a Spring Boot test fixture, the `backend-reviewer` agent with stack detection, the `/review-backend` command, 7 language/framework-agnostic review skills, and `/review` command integration. This is one of three plans implementing the backend domain spec at `docs/superpowers/specs/2026-05-07-shield-backend-domain-design.md`.

**Architecture:** Mirror the existing `shield/skills/kubernetes/` pattern. Skills are flat under `shield/skills/backend/`. The new `backend-reviewer` agent walks the file tree, detects stacks via marker files, and dispatches to existing specialist agents (security, architecture, agile-coach, operations, dx-engineer, product-manager) for cross-cutting concerns. Each agnostic skill ships with a fixture violation, RED-GREEN test runs, and an entry in the fixture's `expected-findings.md` oracle.

**Tech Stack:** Markdown skills/agents/commands, Spring Boot 3.x test fixture (Maven, Java 17), JUnit 5. No runtime code — this is a Claude Code plugin.

---

## Scope of this plan (Plan 1)

**In scope:**
- 7 agnostic skills (`code-quality-review`, `api-design-review`, `testing-strategy-review`, `database-review`, `error-observability-review`, `deployment-safety-review`, `concurrency-review`)
- `backend-reviewer` agent with stack detection (all 4 stacks recognized; only Java/Kotlin path loads framework skills, but Plan 1 ships zero framework skills — that's Plan 2)
- `/review-backend` command
- Spring Boot fixture skeleton + violations for all 7 agnostic skills + `expected-findings.md` oracle
- Update `shield/commands/review.md` to register the backend domain
- Bump shield to `2.9.0` in `.claude-plugin/marketplace.json`

**Out of scope (Plan 2):**
- 6 Spring/JVM skills (`spring-web`, `spring-data`, `spring-config`, `spring-security`, `spring-test`, `jvm-language-review`)
- Conditional Spring sub-detection in the agent
- Spring-specific fixture violations

**Out of scope (Plan 3):**
- `/plan` domain-detection step (pre-existing gap)
- `/plan-review` reviewer auto-detect registration
- `/implement` per-step domain hook extension

After Plan 1 ships, `/review-backend` works end-to-end on any backend repo with agnostic checks. Java repos receive agnostic-only review until Plan 2 lands.

---

## File structure

**New files (this plan):**

```
shield/skills/backend/
  ├── code-quality-review/SKILL.md
  ├── api-design-review/SKILL.md
  ├── testing-strategy-review/SKILL.md
  ├── database-review/SKILL.md
  ├── error-observability-review/SKILL.md
  ├── deployment-safety-review/SKILL.md
  └── concurrency-review/SKILL.md
shield/agents/backend-reviewer.md
shield/commands/review-backend.md
shield/examples/spring-boot-api/
  ├── README.md
  ├── pom.xml
  ├── docs/expected-findings.md
  ├── src/main/java/com/example/api/
  │   ├── ApiApplication.java
  │   ├── controller/
  │   ├── service/
  │   ├── repository/
  │   ├── model/
  │   ├── config/
  │   └── exception/
  ├── src/main/resources/
  │   ├── application.yml
  │   └── db/migration/
  └── src/test/java/com/example/api/
```

**Modified files (this plan):**

| File | Change |
|---|---|
| `shield/commands/review.md` | Add `backend` to domain-skill list (line 38 area) |
| `.claude-plugin/marketplace.json` | Bump `shield` from `2.8.0` to `2.9.0` |

---

## Conventions used in this plan

- **Each skill is its own task** with a TDD cycle: add fixture violation → write expected-findings entry → RED test (subagent without skill) → write SKILL.md → GREEN test (subagent with skill) → refactor if needed → commit.
- **RED/GREEN test runs are dispatched via the `Agent` tool with `subagent_type: general-purpose`.** Each test prompt includes the full review instructions; the GREEN test additionally instructs the subagent to load the new skill.
- **All file paths are absolute from the repo root** of the worktree at `/Users/apple/projects/infraspecdev/tesseract/.worktrees/feat-backend-domain-exploration/`.
- **Commits are per task** unless a step explicitly says "commit at end of step". Use Conventional Commits per existing shield style (`feat(shield):`, `chore:`, etc.).
- **Oracle line numbers are approximate.** Exact line numbers in `expected-findings.md` depend on how the engineer formats each file. If the actual file's line numbers differ from the oracle by 1-2 lines, adjust the oracle row to match the file before running the GREEN test. The semantic content (what's wrong) is what the GREEN test compares — not exact lines.

---

### Task 1: Set up backend skill directory + Spring Boot fixture skeleton

**Files:**
- Create: `shield/skills/backend/.gitkeep`
- Create: `shield/examples/spring-boot-api/README.md`
- Create: `shield/examples/spring-boot-api/pom.xml`
- Create: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/ApiApplication.java`
- Create: `shield/examples/spring-boot-api/src/main/resources/application.yml`

- [ ] **Step 1: Create the backend skill directory**

```bash
mkdir -p shield/skills/backend
touch shield/skills/backend/.gitkeep
```

- [ ] **Step 2: Create the Spring Boot fixture README**

Write `shield/examples/spring-boot-api/README.md`:

```markdown
# spring-boot-api — Backend Review Test Fixture

A small Spring Boot 3.x service used to RED-GREEN test the skills under `shield/skills/backend/`. Every source file in this fixture contains intentional violations matched to specific skills. The contract between violations and skills lives in `docs/expected-findings.md`.

**This fixture is not a runnable application** — it is reference code with deliberate bugs. Do not deploy it.

## Layout

```
src/main/java/com/example/api/
  ├── ApiApplication.java        — Spring Boot entry point
  ├── controller/                — REST controllers (api-design, error-observability)
  ├── service/                   — Business logic (code-quality, concurrency)
  ├── repository/                — JPA repositories (database)
  ├── model/                     — Entities (database)
  ├── config/                    — App + Security config (deployment-safety)
  └── exception/                 — Exception handlers (error-observability)
src/main/resources/
  ├── application.yml            — Config (deployment-safety)
  └── db/migration/              — Flyway migrations (database, deployment-safety)
src/test/java/com/example/api/   — Tests (testing-strategy)
```

## Adding new violations

When adding a new violation:
1. Place it in the file most natural for that violation type.
2. Add a row to `docs/expected-findings.md` with the file path, line range, skill name, and expected severity.
3. Re-run the relevant skill's GREEN test to confirm it catches the new finding.

See `docs/expected-findings.md` for the full inventory of intentional bugs.
```

- [ ] **Step 3: Create a minimal valid pom.xml**

Write `shield/examples/spring-boot-api/pom.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>spring-boot-api</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>spring-boot-api</name>
    <description>Shield backend-review test fixture (intentional violations)</description>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-core</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 4: Create the empty expected-findings oracle**

Write `shield/examples/spring-boot-api/docs/expected-findings.md`:

```markdown
# Expected Findings

This file is the RED-GREEN oracle for the backend domain skills. Each row pairs an intentional violation in the fixture with the skill that should catch it.

When adding a new violation, append a row here. When deleting a violation, remove its row.

The table is established in Task 2 (the first skill task). Until then, this file has no rows.
```

- [ ] **Step 5: Create the Spring Boot main class**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/ApiApplication.java`:

```java
package com.example.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ApiApplication {
    public static void main(String[] args) {
        SpringApplication.run(ApiApplication.class, args);
    }
}
```

- [ ] **Step 6: Create a minimal application.yml**

Write `shield/examples/spring-boot-api/src/main/resources/application.yml`:

```yaml
spring:
  application:
    name: spring-boot-api
  datasource:
    url: jdbc:h2:mem:testdb
    username: sa
    password: ""
  jpa:
    hibernate:
      ddl-auto: validate
  flyway:
    enabled: true
    locations: classpath:db/migration
```

- [ ] **Step 7: Commit the skeleton**

```bash
git add shield/skills/backend/.gitkeep shield/examples/spring-boot-api/
git commit -m "feat(shield): scaffold backend domain dir + spring-boot-api fixture skeleton"
```

---

### Task 2: code-quality-review skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/service/UserService.java` (intentional violations)
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/code-quality-review/SKILL.md`

- [ ] **Step 1: Add a UserService with SOLID/DRY/KISS violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/service/UserService.java`:

```java
package com.example.api.service;

import org.springframework.stereotype.Service;
import java.util.*;

// VIOLATION: God class — service handles users, orders, emails, payments, audit logs.
// Should be split into UserService, OrderService, NotificationService, PaymentService,
// AuditService. Each method below couples user logic to unrelated concerns.
@Service
public class UserService {

    private final Map<Long, Map<String, Object>> users = new HashMap<>();
    private final Map<Long, List<Map<String, Object>>> orders = new HashMap<>();

    // VIOLATION: Method does five things — validate, persist, send email, log audit, charge fee.
    // Single Responsibility violation. Should delegate to focused collaborators.
    public Map<String, Object> registerUser(String email, String password, String name, double signupFee) {
        if (email == null || !email.contains("@")) throw new RuntimeException("bad email");
        if (password == null || password.length() < 8) throw new RuntimeException("weak password");
        Long id = (long) (users.size() + 1);
        Map<String, Object> u = new HashMap<>();
        u.put("id", id);
        u.put("email", email);
        u.put("password", password); // plaintext — flagged elsewhere too
        u.put("name", name);
        users.put(id, u);
        // sends email (should be a NotificationService)
        System.out.println("Sending welcome email to " + email);
        // charges fee (should be a PaymentService)
        System.out.println("Charging $" + signupFee + " to " + email);
        // writes audit log (should be an AuditService)
        System.out.println("AUDIT: user " + id + " created");
        return u;
    }

    // VIOLATION: Copy-paste of registerUser logic with minor variation. DRY violation.
    public Map<String, Object> registerAdmin(String email, String password, String name, double signupFee) {
        if (email == null || !email.contains("@")) throw new RuntimeException("bad email");
        if (password == null || password.length() < 8) throw new RuntimeException("weak password");
        Long id = (long) (users.size() + 1);
        Map<String, Object> u = new HashMap<>();
        u.put("id", id);
        u.put("email", email);
        u.put("password", password);
        u.put("name", name);
        u.put("role", "ADMIN");
        users.put(id, u);
        System.out.println("Sending welcome email to " + email);
        System.out.println("Charging $" + signupFee + " to " + email);
        System.out.println("AUDIT: admin " + id + " created");
        return u;
    }

    // VIOLATION: Speculative generality / YAGNI — accepts a "strategy" param and a
    // "transformOptions" map that no caller uses. Premature flexibility.
    public List<Map<String, Object>> findUsers(String strategy, Map<String, Object> transformOptions) {
        return new ArrayList<>(users.values());
    }

    // VIOLATION: Deep nesting (5 levels), poor naming (`x`, `tmp`, `do2`), no early returns.
    public boolean doStuff(Long id, String x, boolean tmp, int do2) {
        if (id != null) {
            if (users.containsKey(id)) {
                Map<String, Object> u = users.get(id);
                if (u != null) {
                    if (x != null && !x.isEmpty()) {
                        if (tmp) {
                            u.put("flag", do2);
                            return true;
                        }
                    }
                }
            }
        }
        return false;
    }
}
```

- [ ] **Step 2: Add an oracle entry for code-quality-review**

Append to `shield/examples/spring-boot-api/docs/expected-findings.md` (this is the first skill task — it establishes the table):

```markdown
| Skill | File | Lines | Severity | What's wrong |
|---|---|---|---|---|
| code-quality-review | `service/UserService.java` | 9-15 | high | God class — handles users, orders, emails, payments, audit logs |
| code-quality-review | `service/UserService.java` | 18-32 | high | `registerUser` does five things (SRP violation) |
| code-quality-review | `service/UserService.java` | 36-50 | high | `registerAdmin` is a copy of `registerUser` (DRY violation) |
| code-quality-review | `service/UserService.java` | 54-56 | medium | `findUsers` accepts unused parameters (YAGNI / speculative generality) |
| code-quality-review | `service/UserService.java` | 59-71 | medium | `doStuff` has poor naming, deep nesting, no early returns |
```


- [ ] **Step 3: RED — dispatch a subagent without the skill**

Use the `Agent` tool with `subagent_type: general-purpose`. Send this prompt:

```
You are reviewing a Java/Spring Boot file for code quality concerns.

File path: shield/examples/spring-boot-api/src/main/java/com/example/api/service/UserService.java

Read the file. List every code-quality issue you find: SOLID violations, DRY/KISS/YAGNI smells, naming problems, deep nesting, single-responsibility issues, fat interfaces, leaky abstractions.

For each finding, provide: file path, line range, severity (low/medium/high), one-sentence description.

Format the output as a markdown table.
```

Read the subagent's response. Save it as a baseline note in your scratch (you do not need to commit this output). The expectation: the general-purpose agent without the skill will catch *some* of the issues but may miss SRP-vs-DRY framing, may grade severity inconsistently, and may not flag YAGNI on `findUsers`.

- [ ] **Step 4: Write the code-quality-review skill**

Write `shield/skills/backend/code-quality-review/SKILL.md`:

```markdown
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
- Security review — use the security-reviewer agent

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
```

- [ ] **Step 5: GREEN — dispatch a subagent with the skill**

Use the `Agent` tool with `subagent_type: general-purpose`. Send this prompt:

```
You are reviewing a Java/Spring Boot file for code quality concerns.

Before you start, read this skill in full and apply its rubric:
shield/skills/backend/code-quality-review/SKILL.md

File path: shield/examples/spring-boot-api/src/main/java/com/example/api/service/UserService.java

Read the file. Apply the skill's Evaluation Points (Q1–Q10) and produce the output in the format the skill specifies. For each finding, include: evaluation point ID (Q#), file path, line range, severity, one-sentence finding.

Format the output as a markdown table.
```

Compare the subagent's output to `shield/examples/spring-boot-api/docs/expected-findings.md`. The GREEN run must catch ALL 5 expected findings for `code-quality-review` and grade severity correctly.

- [ ] **Step 6: Refactor if GREEN reveals gaps**

If the GREEN run misses an expected finding or grades severity incorrectly:
1. Identify which Evaluation Point should have caught it
2. Refine the skill's "What to Look For" or "Critical Checks" section to make the signal more explicit
3. Re-run Step 5 until all 5 findings are caught with correct severity

If the skill needs no edits, skip this step.

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/code-quality-review/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/service/UserService.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend code-quality-review skill"
```

---

### Task 3: api-design-review skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/api-design-review/SKILL.md`

- [ ] **Step 1: Add a UserController with API design violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java`:

```java
package com.example.api.controller;

import com.example.api.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

// VIOLATION: No versioning prefix. URI exposes verbs, not resources.
@RestController
@RequestMapping("/api")
public class UserController {

    @Autowired
    private UserService userService;

    // VIOLATION: GET used for a state-changing operation. Should be POST.
    @GetMapping("/createUser")
    public Map<String, Object> createUser(@RequestParam String email,
                                          @RequestParam String password,
                                          @RequestParam String name) {
        return userService.registerUser(email, password, name, 0.0);
    }

    // VIOLATION: Verb in URI ("getAll"). Should be GET /users with pagination.
    // VIOLATION: No pagination — returns full collection.
    @GetMapping("/getAllUsers")
    public List<Map<String, Object>> getAllUsers() {
        return userService.findUsers(null, null);
    }

    // VIOLATION: Returns 200 OK on a missing resource (should be 404).
    // VIOLATION: Inconsistent error shape — returns Map<String,String> on error,
    // Map<String,Object> on success.
    @GetMapping("/user/{id}")
    public Object getUser(@PathVariable Long id) {
        // simulating a not-found
        if (id < 0) return Map.of("error", "not found");
        return Map.of("id", id, "email", "stub@example.com");
    }

    // VIOLATION: Non-idempotent PUT. PUT must be idempotent; this appends.
    @PutMapping("/user/{id}/append-tag")
    public Map<String, Object> appendTag(@PathVariable Long id, @RequestParam String tag) {
        // appends each call — running twice gives different state
        return Map.of("id", id, "appended", tag);
    }

    // VIOLATION: DELETE returns the deleted resource body (200) instead of 204 No Content.
    @DeleteMapping("/user/{id}")
    public Map<String, Object> deleteUser(@PathVariable Long id) {
        return Map.of("deleted", id, "email", "stub@example.com");
    }
}
```

- [ ] **Step 2: Add oracle entries**

Modify `shield/examples/spring-boot-api/docs/expected-findings.md`. Append to the table:

```markdown
| api-design-review | `controller/UserController.java` | 11 | medium | No version prefix in `@RequestMapping` ("/api" alone) |
| api-design-review | `controller/UserController.java` | 18-22 | high | GET used for a state-changing operation (`/createUser`) |
| api-design-review | `controller/UserController.java` | 25-28 | medium | Verb in URI (`/getAllUsers`); resource modeling violation |
| api-design-review | `controller/UserController.java` | 25-28 | medium | No pagination on a list endpoint |
| api-design-review | `controller/UserController.java` | 32-37 | high | 200 OK returned for missing resource (should be 404) |
| api-design-review | `controller/UserController.java` | 32-37 | medium | Inconsistent error response shape vs success shape |
| api-design-review | `controller/UserController.java` | 40-43 | high | PUT used for non-idempotent operation (append) |
| api-design-review | `controller/UserController.java` | 46-49 | low | DELETE returns 200 with body (should be 204 No Content) |
```

- [ ] **Step 3: RED — subagent without skill**

`Agent` tool, `subagent_type: general-purpose`. Prompt:

```
You are reviewing a REST controller for API design quality.

File path: shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java

Read the file. List every API design issue: HTTP method misuse, URI design problems, status code issues, missing pagination, inconsistent error shapes, idempotency violations, versioning gaps.

For each finding: file path, line range, severity (low/medium/high), one-sentence description. Markdown table.
```

Save the baseline.

- [ ] **Step 4: Write the api-design-review skill**

Write `shield/skills/backend/api-design-review/SKILL.md`:

```markdown
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
| A1 | Resource-oriented URIs | Nouns, not verbs (`/users` not `/getUsers`/`/createUser`). Hierarchies via path segments | High |
| A2 | HTTP method semantics | GET = safe + idempotent; POST = create / non-idempotent; PUT = full replace + idempotent; PATCH = partial; DELETE = remove | High |
| A3 | Status code accuracy | 200 only on success with body; 201 on resource creation with `Location`; 204 on success with no body; 4xx for client error; 5xx for server error | High |
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
| High | Wrong HTTP method, wrong status code, missing idempotency on PUT/DELETE — these break clients |
| Medium | Inconsistent error shape, missing pagination, missing versioning — friction but not breakage |
| Low | URI casing inconsistencies, field-name style nits — surface-level |

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
- For Spring `@RestController` specifics (Plan 2) → `spring-web`
- For error handling shape → `backend-error-observability-review`
```

- [ ] **Step 5: GREEN — subagent with skill**

`Agent` tool, `subagent_type: general-purpose`. Prompt:

```
You are reviewing a REST controller for API design quality.

Read this skill in full and apply its rubric:
shield/skills/backend/api-design-review/SKILL.md

File path: shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java

Apply Evaluation Points A1–A10. For each finding, include the evaluation point ID. Markdown table with: A#, file path, line range, severity, one-sentence finding.
```

Compare against the 8 expected findings for `api-design-review`. All must be caught with correct severity.

- [ ] **Step 6: Refactor if needed**

Same pattern as Task 2 Step 6.

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/api-design-review/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/controller/UserController.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend api-design-review skill"
```

---

### Task 4: testing-strategy-review skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/test/java/com/example/api/UserServiceTest.java`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/testing-strategy-review/SKILL.md`

- [ ] **Step 1: Add a test class with strategy violations**

Write `shield/examples/spring-boot-api/src/test/java/com/example/api/UserServiceTest.java`:

```java
package com.example.api;

import com.example.api.service.UserService;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

// VIOLATION: @SpringBootTest pulls full context for every unit test — slow, broad scope.
// Should be a plain unit test (no Spring) or a focused @DataJpaTest / @WebMvcTest slice.
@SpringBootTest
class UserServiceTest {

    // VIOLATION: Mocking the class under test instead of its collaborators.
    // The mock returns a stubbed value, so the test asserts the stub, not the implementation.
    @Test
    void registerUser_returnsUser() {
        UserService mockedService = Mockito.mock(UserService.class);
        Map<String, Object> stub = new HashMap<>();
        stub.put("id", 1L);
        Mockito.when(mockedService.registerUser("a@b.c", "password123", "n", 0.0)).thenReturn(stub);

        Map<String, Object> result = mockedService.registerUser("a@b.c", "password123", "n", 0.0);

        assertEquals(1L, result.get("id"));
    }

    // VIOLATION: Sleep-based timing, flaky.
    @Test
    void waitsAndPasses() throws InterruptedException {
        long start = System.currentTimeMillis();
        Thread.sleep(100);
        long elapsed = System.currentTimeMillis() - start;
        assertTrue(elapsed >= 100); // flakes under load
    }

    // VIOLATION: Test relies on shared mutable state from a prior test run order.
    private static int counter = 0;
    @Test
    void incrementCounter() {
        counter++;
        assertEquals(1, counter); // breaks if any test increments first
    }

    // VIOLATION: Test asserts implementation, not behavior — checks a private map size
    // via reflection-style poke. Behavior assertion (the public contract) would be
    // "registering a user makes them findable".
    @Test
    void implementationDetail_internalMapGrows() {
        UserService svc = new UserService();
        svc.registerUser("a@b.c", "password123", "n", 0.0);
        // hypothetical reflective access — illustration only
        assertNotNull(svc); // weak/no-op assertion
    }

    // VIOLATION: No assertions — passes regardless of behavior.
    @Test
    void noAssertions() {
        UserService svc = new UserService();
        svc.registerUser("a@b.c", "password123", "n", 0.0);
    }
}
```

- [ ] **Step 2: Add oracle entries**

Append to `shield/examples/spring-boot-api/docs/expected-findings.md`:

```markdown
| testing-strategy-review | `test/.../UserServiceTest.java` | 14 | high | `@SpringBootTest` for unit-scope test (heavy slice + slow) |
| testing-strategy-review | `test/.../UserServiceTest.java` | 19-29 | high | Mocking the class under test — asserts the stub, not the implementation |
| testing-strategy-review | `test/.../UserServiceTest.java` | 32-37 | medium | Sleep-based timing assertion (flaky) |
| testing-strategy-review | `test/.../UserServiceTest.java` | 40-44 | medium | Shared mutable static state across tests |
| testing-strategy-review | `test/.../UserServiceTest.java` | 49-54 | medium | Asserts internal detail / weak assertion |
| testing-strategy-review | `test/.../UserServiceTest.java` | 57-60 | high | No assertions — test passes regardless |
```

- [ ] **Step 3: RED — subagent without skill**

`Agent` tool, `subagent_type: general-purpose`. Prompt:

```
You are reviewing a Java JUnit test class for test-strategy quality.

File path: shield/examples/spring-boot-api/src/test/java/com/example/api/UserServiceTest.java

Read the file. List every test-strategy issue: wrong test scope (integration vs unit), mocking wrong things, flaky patterns, shared state between tests, weak assertions, missing assertions, asserting implementation over behavior.

For each: file path, line range, severity, one-sentence description. Markdown table.
```

Save the baseline.

- [ ] **Step 4: Write the testing-strategy-review skill**

Write `shield/skills/backend/testing-strategy-review/SKILL.md`:

```markdown
---
name: backend-testing-strategy-review
description: Use when reviewing test code for strategy quality — pyramid balance, mock boundaries, fixture/setup correctness, flaky patterns, behavior-vs-implementation tests, missing assertions. Triggers when test files (`*Test.java`, `test_*.py`, `*.test.ts`, `*_test.go`) are in scope.
---

# Backend Testing Strategy Review

## Overview

Review test code against principles of effective automated testing: appropriate test scope (unit vs integration vs e2e), mocking only at correct boundaries (collaborators not the class under test), avoidance of flaky patterns (timing, network, shared state), assertions that validate behavior over implementation, and meaningful coverage of critical paths.

## When to Use

- Reviewing PR diffs that include test code
- Auditing a test suite during onboarding
- Pre-implementation: planning the test strategy for a new feature

## When NOT to Use

- Production code review — use `code-quality-review`
- Coverage % evaluation — measure with tooling, this skill checks design
- Performance testing strategy — separate skill (not in v1)

## Review Process

1. Identify all test files in scope
2. For each test class/file, walk through Evaluation Points T1–T10
3. Cross-cut: assess pyramid balance (count of unit vs integration vs e2e)
4. Flag flaky patterns separately — even a passing flaky test is a finding

## Evaluation Points

| # | Check | What to Look For | Severity |
|---|-------|-------------------|----------|
| T1 | Test scope correctness | Unit tests use no framework context; integration tests use a focused slice; e2e uses full stack. Flag full-stack annotations on unit-shaped tests | High |
| T2 | Mock target | Mock collaborators, not the class under test. Mocking the SUT is a smell — the test exercises the mock, not the code | High |
| T3 | Assertion presence | Every test has at least one meaningful assertion. Flag tests with no asserts or `assertNotNull(obj)` on a constructed object | High |
| T4 | Behavior vs implementation | Assertions target the public contract. Flag tests that assert internal collaborators were called when the behavior is observable through the contract | Medium |
| T5 | Test isolation | No shared mutable state between tests. Flag static counters, file system state, database state without rollback | High |
| T6 | Flaky patterns | No sleeps, no time-of-day dependencies, no network to real services, no race-prone parallelism without sync | High |
| T7 | Setup/teardown clarity | Setup is per-test or per-class explicitly. Flag implicit ordering dependencies | Medium |
| T8 | Test naming | Names describe behavior under test (`registerUser_withDuplicateEmail_throws`). Flag `test1`, `testFoo`, `simpleTest` | Low |
| T9 | Pyramid balance (cross-cut) | Many unit, fewer integration, few e2e. Flag inverted pyramids — many slow tests, few fast ones | Medium |
| T10 | Edge case coverage | Critical paths have happy + at least one failure case. Flag tests that only cover the success path | Medium |

## Critical Checks

- A test that mocks the class under test and asserts the mock's stubbed return value
- A test with no assertions
- A test using `Thread.sleep` to coordinate with async work
- Static or instance state mutated across tests
- Heavy framework annotations (`@SpringBootTest`, `pytest fixtures` loading the world) on tests that could be plain units

## Severity Guide

| Severity | When |
|---|---|
| High | Test gives false confidence (no assertions, mocked SUT) or is flaky in CI |
| Medium | Test is correct but mis-scoped or has style issues that hurt maintainability |
| Low | Naming, formatting, minor structural nits |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Demanding only-unit tests | Integration and e2e tests are valuable; the smell is the wrong scope for the test's intent |
| Flagging all `@SpringBootTest` use | Legitimate when integration is the actual goal — flag when the test is shaped like a unit test |
| Penalizing fixtures and shared setup | Per-class `@BeforeAll` is fine for read-only setup; the smell is mutable state changed by each test |
| Treating golden-master / snapshot tests as anti-patterns | Snapshots are a valid technique for stable outputs; flag only if the snapshot is unreviewed or huge |
| Demanding 100% branch coverage | Coverage strategy is product-driven; the skill checks design, not coverage |

## Related Skills

- Spring-specific test slicing (`@WebMvcTest`, `@DataJpaTest`, Testcontainers) — Plan 2 `spring-test`
- For production code quality → `backend-code-quality-review`
```

- [ ] **Step 5: GREEN — subagent with skill**

`Agent` tool, `subagent_type: general-purpose`. Prompt:

```
You are reviewing a Java JUnit test class for test-strategy quality.

Read this skill in full and apply its rubric:
shield/skills/backend/testing-strategy-review/SKILL.md

File path: shield/examples/spring-boot-api/src/test/java/com/example/api/UserServiceTest.java

Apply Evaluation Points T1–T10. Markdown table with: T#, file path, line range, severity, one-sentence finding.
```

Compare to the 6 expected findings. All must be caught with correct severity.

- [ ] **Step 6: Refactor if needed.**

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/testing-strategy-review/ \
        shield/examples/spring-boot-api/src/test/java/com/example/api/UserServiceTest.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend testing-strategy-review skill"
```

---

### Task 5: database-review skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java`
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java`
- Create: `shield/examples/spring-boot-api/src/main/resources/db/migration/V1__create_users.sql`
- Create: `shield/examples/spring-boot-api/src/main/resources/db/migration/V2__create_orders.sql`
- Create: `shield/examples/spring-boot-api/src/main/resources/db/migration/V3__drop_email_column.sql`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/database-review/SKILL.md`

- [ ] **Step 1: Add an entity with intentional violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java`:

```java
package com.example.api.model;

import jakarta.persistence.*;
import java.util.List;

// VIOLATION: No explicit table name; relies on default lowercase-singular convention
// VIOLATION: No index on email despite frequent lookup
@Entity
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // VIOLATION: No @Column constraints — nullable=true, unique not enforced, length default
    private String email;
    private String passwordHash;

    // VIOLATION: Default LAZY would be safe, but EAGER on a 1-N relationship loads
    // every order whenever a User is fetched. N+1 risk.
    @OneToMany(mappedBy = "user", fetch = FetchType.EAGER)
    private List<Order> orders;

    public Long getId() { return id; }
    public String getEmail() { return email; }
    public String getPasswordHash() { return passwordHash; }
    public List<Order> getOrders() { return orders; }
}
```

- [ ] **Step 2: Add a placeholder Order entity (referenced by User)**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java`:

```java
package com.example.api.model;

import jakarta.persistence.*;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id")
    private User user;

    private double amount;

    public Long getId() { return id; }
    public User getUser() { return user; }
    public double getAmount() { return amount; }
}
```

- [ ] **Step 3: Add a repository with N+1 risk**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java`:

```java
package com.example.api.repository;

import com.example.api.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface UserRepository extends JpaRepository<User, Long> {

    // VIOLATION: SELECT N+1 — calling getOrders() on each User triggers an extra query.
    // Should use a fetch join or @EntityGraph.
    List<User> findAll();

    // VIOLATION: Custom JPQL with no pagination on potentially huge result.
    @Query("SELECT u FROM User u WHERE u.email LIKE :pattern")
    List<User> findByEmailPattern(String pattern);
}
```

- [ ] **Step 4: Add migrations including a destructive one**

Write `shield/examples/spring-boot-api/src/main/resources/db/migration/V1__create_users.sql`:

```sql
-- VIOLATION: No index on email column despite obvious lookup pattern
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);
```

Write `shield/examples/spring-boot-api/src/main/resources/db/migration/V2__create_orders.sql`:

```sql
CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DOUBLE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

Write `shield/examples/spring-boot-api/src/main/resources/db/migration/V3__drop_email_column.sql`:

```sql
-- VIOLATION: Destructive migration without expand/contract pattern.
-- During rolling deploy: old code reads users.email, new code does not. The DROP
-- happens before old code is fully drained, causing runtime errors.
-- Should be split: V3 stop reading email, V4 drop column once all instances upgraded.
ALTER TABLE users DROP COLUMN email;
```

- [ ] **Step 5: Add oracle entries**

Append to `shield/examples/spring-boot-api/docs/expected-findings.md`:

```markdown
| database-review | `model/User.java` | 8 | medium | No `@Table` with explicit name |
| database-review | `model/User.java` | 13-14 | medium | No `@Column` constraints (nullable, unique, length) on email/password |
| database-review | `model/User.java` | 18-20 | high | EAGER fetch on `@OneToMany` causes load-everything; risks N+1 and memory blowups |
| database-review | `repository/UserRepository.java` | 12 | high | `findAll` with EAGER child loads triggers SELECT N+1 |
| database-review | `repository/UserRepository.java` | 14-15 | medium | LIKE query without pagination; full table scan on production-sized data |
| database-review | `db/migration/V1__create_users.sql` | 2-6 | medium | No index on `email` column |
| database-review | `db/migration/V3__drop_email_column.sql` | 5 | high | Destructive migration without expand/contract; breaks rolling deploys |
```

- [ ] **Step 6: RED — subagent without skill**

`Agent` tool, `subagent_type: general-purpose`. Prompt:

```
You are reviewing JPA entities, repositories, and SQL migrations for database-design quality.

Files:
- shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java
- shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java
- shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java
- shield/examples/spring-boot-api/src/main/resources/db/migration/V1__create_users.sql
- shield/examples/spring-boot-api/src/main/resources/db/migration/V2__create_orders.sql
- shield/examples/spring-boot-api/src/main/resources/db/migration/V3__drop_email_column.sql

Read each file. List every database design issue: missing indexes, N+1 queries, eager-load smells, missing constraints, transaction boundary issues, migration safety problems.

For each: file path, line range, severity, one-sentence description. Markdown table.
```

Save the baseline.

- [ ] **Step 7: Write the database-review skill**

Write `shield/skills/backend/database-review/SKILL.md`:

```markdown
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

- For Spring-specific transactional boundary issues (Plan 2) → `spring-data`
- For deployment ordering of migrations → `backend-deployment-safety-review`
- For underlying code structure → `backend-code-quality-review`
```

- [ ] **Step 8: GREEN — subagent with skill**

`Agent` tool, `subagent_type: general-purpose`. Prompt:

```
You are reviewing JPA entities, repositories, and SQL migrations for database-design quality.

Read this skill in full and apply its rubric:
shield/skills/backend/database-review/SKILL.md

Files (apply D1–D10 to each):
- shield/examples/spring-boot-api/src/main/java/com/example/api/model/User.java
- shield/examples/spring-boot-api/src/main/java/com/example/api/model/Order.java
- shield/examples/spring-boot-api/src/main/java/com/example/api/repository/UserRepository.java
- shield/examples/spring-boot-api/src/main/resources/db/migration/V1__create_users.sql
- shield/examples/spring-boot-api/src/main/resources/db/migration/V2__create_orders.sql
- shield/examples/spring-boot-api/src/main/resources/db/migration/V3__drop_email_column.sql

Markdown table with: D#, file path, line range, severity, one-sentence finding.
```

Compare to the 7 expected findings.

- [ ] **Step 9: Refactor if needed.**

- [ ] **Step 10: Commit**

```bash
git add shield/skills/backend/database-review/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/model/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/repository/ \
        shield/examples/spring-boot-api/src/main/resources/db/ \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend database-review skill"
```

---

### Task 6: error-observability-review skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/exception/GlobalExceptionHandler.java`
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderService.java`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/error-observability-review/SKILL.md`

- [ ] **Step 1: Add a global exception handler with violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/exception/GlobalExceptionHandler.java`:

```java
package com.example.api.exception;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class GlobalExceptionHandler {

    // VIOLATION: Catch-all that maps every Throwable to 500. Hides 4xx-shaped client
    // errors as 5xx server errors, breaks alerting and client-side handling.
    @ExceptionHandler(Throwable.class)
    public ResponseEntity<String> handleAll(Throwable t) {
        // VIOLATION: Logging via println — no level, no structure, no MDC/correlation ID.
        System.out.println("error: " + t.getMessage());
        // VIOLATION: Returns the raw exception message to clients — leaks internals.
        return ResponseEntity.status(500).body(t.getMessage());
    }
}
```

- [ ] **Step 2: Add a service that uses exceptions as control flow**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderService.java`:

```java
package com.example.api.service;

import org.springframework.stereotype.Service;

@Service
public class OrderService {

    // VIOLATION: Throws and catches its own exception to control branching.
    // Exception-as-control-flow — should be a return value or a normal conditional.
    public boolean isValid(double amount) {
        try {
            if (amount <= 0) {
                throw new IllegalArgumentException("non-positive");
            }
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

    // VIOLATION: Swallows exception silently — no log, no rethrow, no metric.
    // The caller has no visibility into a failure.
    public void chargeCustomer(Long customerId, double amount) {
        try {
            // simulate external call
            if (Math.random() < 0.1) {
                throw new RuntimeException("payment gateway unreachable");
            }
        } catch (Exception ignored) {
            // silently swallow
        }
    }
}
```

- [ ] **Step 3: Add oracle entries**

Append to `shield/examples/spring-boot-api/docs/expected-findings.md`:

```markdown
| error-observability-review | `exception/GlobalExceptionHandler.java` | 11-15 | high | Catch-all `Throwable` handler maps every exception to 500 |
| error-observability-review | `exception/GlobalExceptionHandler.java` | 13 | high | `System.out.println` for error logging — no level, no structure, no correlation ID |
| error-observability-review | `exception/GlobalExceptionHandler.java` | 14 | medium | Returns raw exception message to client — leaks internals |
| error-observability-review | `service/OrderService.java` | 9-17 | medium | Exception-as-control-flow in `isValid` |
| error-observability-review | `service/OrderService.java` | 21-29 | high | `chargeCustomer` swallows exception silently with no log/metric/rethrow |
```

- [ ] **Step 4: RED — subagent without skill**

```
You are reviewing Java code for error handling and observability.

Files:
- shield/examples/spring-boot-api/src/main/java/com/example/api/exception/GlobalExceptionHandler.java
- shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderService.java

List every error-handling and observability issue: catch-alls, leaking internal details, exception-as-control-flow, silent swallows, missing logs, missing metrics, missing trace context.

Markdown table: file, lines, severity, finding.
```

- [ ] **Step 5: Write the error-observability-review skill**

Write `shield/skills/backend/error-observability-review/SKILL.md`:

```markdown
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
```

- [ ] **Step 6: GREEN — subagent with skill**

```
You are reviewing Java code for error handling and observability.

Read this skill in full and apply its rubric:
shield/skills/backend/error-observability-review/SKILL.md

Files (apply E1–E10):
- shield/examples/spring-boot-api/src/main/java/com/example/api/exception/GlobalExceptionHandler.java
- shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderService.java

Markdown table: E#, file path, line range, severity, one-sentence finding.
```

Compare to the 5 expected findings.

- [ ] **Step 7: Refactor if needed.**

- [ ] **Step 8: Commit**

```bash
git add shield/skills/backend/error-observability-review/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/exception/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/service/OrderService.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend error-observability-review skill"
```

---

### Task 7: deployment-safety-review skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/deployment-safety-review/SKILL.md`

- [ ] **Step 1: Add a config bean with deployment-safety violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java`:

```java
package com.example.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class AppConfig {

    // VIOLATION: In-memory cache held in a singleton bean.
    // Multi-instance deployments diverge — instance A caches X, instance B does not.
    // Should use a distributed cache (Redis, etc.) or scope explicitly per-instance.
    @Bean
    public Map<String, Object> sharedCache() {
        return new HashMap<>();
    }

    // VIOLATION: Feature is launched fully on/off via this static toggle.
    // No feature flag, no gradual rollout, no kill switch.
    // Risky changes should be behind a runtime flag.
    public static final boolean NEW_PRICING_ENABLED = true;
}
```

- [ ] **Step 2: Add oracle entries**

Note: V3 destructive migration is also a deployment-safety concern. Add a row pointing the same file to deployment-safety-review.

Append to `shield/examples/spring-boot-api/docs/expected-findings.md`:

```markdown
| deployment-safety-review | `config/AppConfig.java` | 14-17 | high | In-memory cache in a singleton bean — diverges across multi-instance deploys |
| deployment-safety-review | `config/AppConfig.java` | 21 | medium | Risky pricing change rolled in via static constant — no feature flag |
| deployment-safety-review | `db/migration/V3__drop_email_column.sql` | 5 | high | Destructive migration without feature-flag gating; cannot roll back without restoring data |
```

- [ ] **Step 3: RED — subagent without skill**

```
You are reviewing Java/Spring Boot code and SQL for deployment-safety concerns.

Files:
- shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java
- shield/examples/spring-boot-api/src/main/resources/db/migration/V3__drop_email_column.sql

List every deployment-safety issue: feature flag readiness for risky changes, backwards-compatible API/schema evolution, rollback paths, blast-radius scoping, multi-instance state safety.

Markdown table: file, lines, severity, finding.
```

- [ ] **Step 4: Write the deployment-safety-review skill**

Write `shield/skills/backend/deployment-safety-review/SKILL.md`:

```markdown
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
```

- [ ] **Step 5: GREEN — subagent with skill**

```
You are reviewing Java/Spring Boot code and SQL for deployment-safety concerns.

Read this skill in full and apply its rubric:
shield/skills/backend/deployment-safety-review/SKILL.md

Files (apply S1–S10):
- shield/examples/spring-boot-api/src/main/java/com/example/api/config/AppConfig.java
- shield/examples/spring-boot-api/src/main/resources/db/migration/V3__drop_email_column.sql

Markdown table: S#, file, line range, severity, finding.
```

Compare to the 3 expected findings.

- [ ] **Step 6: Refactor if needed.**

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/deployment-safety-review/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/config/ \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend deployment-safety-review skill"
```

---

### Task 8: concurrency-review skill (TDD)

**Files:**
- Create: `shield/examples/spring-boot-api/src/main/java/com/example/api/service/CounterService.java`
- Modify: `shield/examples/spring-boot-api/docs/expected-findings.md`
- Create: `shield/skills/backend/concurrency-review/SKILL.md`

- [ ] **Step 1: Add a service with concurrency violations**

Write `shield/examples/spring-boot-api/src/main/java/com/example/api/service/CounterService.java`:

```java
package com.example.api.service;

import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@Service
public class CounterService {

    // VIOLATION: Shared mutable state in a singleton bean accessed without synchronization.
    // Multiple request threads race on these reads/writes.
    private final Map<String, Integer> counters = new HashMap<>();
    private int totalRequests = 0;

    // VIOLATION: Read-modify-write race on totalRequests.
    public int increment(String key) {
        totalRequests++;
        Integer cur = counters.get(key);
        if (cur == null) cur = 0;
        counters.put(key, cur + 1);
        return cur + 1;
    }

    // VIOLATION: Fire-and-forget — exceptions are silently dropped.
    // No tracking of failure, no metric, no retry policy.
    public void chargeAsync(Long userId, double amount) {
        CompletableFuture.runAsync(() -> {
            if (Math.random() < 0.1) {
                throw new RuntimeException("payment failed");
            }
            // success path; result discarded
        });
    }

    // VIOLATION: Retried operation is not idempotent — appends a row each retry.
    // If caller retries on transient failure, side effects multiply.
    public void recordEvent(String key, String event) {
        counters.merge(key + ":" + event, 1, Integer::sum);
    }
}
```

- [ ] **Step 2: Add oracle entries**

Append to `shield/examples/spring-boot-api/docs/expected-findings.md`:

```markdown
| concurrency-review | `service/CounterService.java` | 14-15 | high | Shared mutable state (`HashMap`, `int`) in singleton without synchronization |
| concurrency-review | `service/CounterService.java` | 18-23 | high | Read-modify-write race on `totalRequests` and counter map |
| concurrency-review | `service/CounterService.java` | 27-33 | high | Fire-and-forget `CompletableFuture.runAsync` — exceptions silently lost |
| concurrency-review | `service/CounterService.java` | 37-39 | medium | Operation not idempotent — retry causes duplicate side effects |
```

- [ ] **Step 3: RED — subagent without skill**

```
You are reviewing Java code for concurrency concerns.

File: shield/examples/spring-boot-api/src/main/java/com/example/api/service/CounterService.java

List every concurrency issue: race conditions, lock granularity issues, async pitfalls (lost exceptions, missed await), retry-idempotency, shared mutable state without synchronization.

Markdown table: file, lines, severity, finding.
```

- [ ] **Step 4: Write the concurrency-review skill**

Write `shield/skills/backend/concurrency-review/SKILL.md`:

```markdown
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
```

- [ ] **Step 5: GREEN — subagent with skill**

```
You are reviewing Java code for concurrency concerns.

Read this skill in full and apply its rubric:
shield/skills/backend/concurrency-review/SKILL.md

File (apply C1–C10): shield/examples/spring-boot-api/src/main/java/com/example/api/service/CounterService.java

Markdown table: C#, file, line range, severity, finding.
```

Compare to the 4 expected findings.

- [ ] **Step 6: Refactor if needed.**

- [ ] **Step 7: Commit**

```bash
git add shield/skills/backend/concurrency-review/ \
        shield/examples/spring-boot-api/src/main/java/com/example/api/service/CounterService.java \
        shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "feat(shield): add backend concurrency-review skill"
```

---

### Task 9: backend-reviewer agent

**Files:**
- Create: `shield/agents/backend-reviewer.md`

- [ ] **Step 1: Write the agent file**

Write `shield/agents/backend-reviewer.md`:

```markdown
---
name: backend-reviewer
description: |
  Use this agent when reviewing backend application code (Java, Kotlin, Python, Node/TypeScript, Go).
  Detects the stack from repo markers (pom.xml, build.gradle*, pyproject.toml, package.json, go.mod),
  loads relevant agnostic and framework-specific skills, and dispatches cross-cutting concerns to
  specialist agents. Only activate when there is clear evidence of backend application code.
model: inherit
---

# Backend Reviewer

## Persona

You are a **Senior Staff Backend Engineer** with 12+ years of production experience across Java/Kotlin (Spring Boot), Python (FastAPI/Django), Node.js (Express/NestJS), and Go services. You've seen p99 latency spikes traced back to N+1 queries, cascading failures from missing circuit breakers, multi-million-dollar incidents from racy in-memory caches, and migrations that took down production for six hours because someone dropped a column the rollback target still read from.

You think in terms of: blast radius, idempotency, contracts, observability gaps, and deployment safety. You apply the SOLID/DRY/KISS/YAGNI principles pragmatically — never religiously. You know the difference between code that's "wrong" and code that's "fine for this stage of the codebase."

You are the orchestrator of the backend domain. You don't do every check yourself — you detect the stack, load the right skills as your rubric, and dispatch cross-cutting concerns (security, architecture at codebase level, agile-coach for story shape, operations) to specialist agents who go deeper than you in their lane.

## Trigger Keywords

backend, api, service, controller, endpoint, repository, jpa, orm, sql, migration, spring, fastapi, django, express, nestjs, gin, go-http, java, kotlin, python, node, typescript, golang

## Weight

1.0 (Core persona — dispatched whenever backend code is in review scope)

## Modes

This agent operates in **review mode** in v1. Future modes (planning, implementation guidance) ship with later iterations.

---

## Stack Detection

Walk the file tree (or the changed-files set on a branch) looking for marker files. For each in-scope file, walk **up** the directory tree to the nearest marker.

| Marker | Stack | v1 framework skills |
|---|---|---|
| `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle*` | Java/Kotlin | (Plan 2 will add Spring/JVM skills; v1 = agnostic only) |
| `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile` | Python | none in v1; emit "framework-specific Python review ships in v2" |
| `package.json` | Node/TS | none in v1; emit "framework-specific Node/TS review ships in v3" |
| `go.mod` | Go | none in v1; emit "framework-specific Go review ships in v4" |
| None + non-empty repo | Unknown stack | agnostic only + warn |
| None + ≤5 source files (configurable) | Greenfield | ask user |

### Excluded paths (default)

```
node_modules/  target/  build/  dist/  out/  .gradle/  .mvn/
__pycache__/  .venv/  vendor/  .git/  .worktrees/  .superpowers/
```

### Greenfield prompt

If detection finds no markers AND the repo is near-empty (default ≤5 source files), ask:

```
This looks like a greenfield repo. Which stack are you targeting?

  [a] Java/Kotlin (Spring Boot)
  [b] Python — framework-specific review not yet available; agnostic only
  [c] Node.js / TypeScript — framework-specific review not yet available; agnostic only
  [d] Go — framework-specific review not yet available; agnostic only
  [e] Other / not yet decided — agnostic only

Or skip stack-specific review for this run: type "skip"
```

Treat the user's reply identically to a positive detection. Do NOT persist the choice — re-ask each greenfield run.

---

## Skill Loading

**Always load (agnostic):**

- `backend/code-quality-review`
- `backend/api-design-review`
- `backend/testing-strategy-review`
- `backend/database-review`
- `backend/error-observability-review`
- `backend/deployment-safety-review`
- `backend/concurrency-review`

**Framework-specific (per detected stack):** None in v1. Plan 2 adds Java/Kotlin Spring skills with conditional sub-detection.

---

## Specialist Dispatch

For cross-cutting concerns, dispatch to existing specialist agents in parallel (they are independent — no shared state).

| Specialist | When to dispatch | Notes |
|---|---|---|
| `security-reviewer` | Always when backend code is in scope | Cross-cutting security beyond any framework-specific skill |
| `architecture-reviewer` | Always | Codebase-level architecture (boundaries, module design); skills handle per-file concerns |
| `agile-coach-reviewer` | When the review is tied to a story (plan.json or PM card present) | Story sizing, AC testability |
| `operations-reviewer` | Always | Operational concerns at the code level |
| `dx-engineer-reviewer` | Always | DX, code clarity, maintainability |
| `product-manager-reviewer` | Only when story context (plan.json) is present | AC verification |

**Do NOT dispatch:** `cost-reviewer` (infra-flavored), `well-architected-reviewer` (AWS-specific), `kubernetes-reviewer` (different domain).

---

## Review Process

1. **Resolve scope.**
   - If a path argument is provided → that subtree
   - Else if on a branch → changed files vs `main` (git diff)
   - Else if `--full` → whole repo (excluding the default exclude list)
2. **Detect stacks per file.** Walk up to the nearest marker. Track which stacks are present and group files by their owning module.
3. **Greenfield/unknown.** If no markers and the repo is near-empty, run the greenfield prompt. If markers but the stack has no v1 framework skills, emit a one-line note and proceed with agnostic-only.
4. **Load skills.** Always-load agnostic; framework-specific based on detected stacks (none in v1).
5. **Apply skills to in-scope files.** For each file, run the relevant skills' Evaluation Points and produce findings (file path, line range, severity, evaluation-point ID).
6. **Dispatch specialists in parallel.** Hand each specialist the in-scope changes, story context (if any), and your initial findings list. Specialists return their own findings.
7. **Aggregate findings.** Merge, deduplicate (same file/line/check from multiple sources collapses to one entry citing all sources), sort by severity (high → medium → low).
8. **Group by module.** In monorepos, group findings under their owning module path so users can see which service produced what.

---

## Output Format

```
## Backend Review

**Scope:** {N files in M modules}
**Stacks detected:** {Java/Kotlin: 2 modules; Python: 1 module}
**Skills applied:** {agnostic: 7; framework: 0 (Plan 2 ships Java)}
**Specialists consulted:** {security, architecture, agile-coach, operations, dx-engineer, product-manager}

### Module: services/api/ (Java/Kotlin)

| Severity | Skill / Source | File | Lines | Finding |
|---|---|---|---|---|
| High | code-quality-review:Q1 | service/UserService.java | 9-15 | God class — handles unrelated domains |
| High | api-design-review:A2 | controller/UserController.java | 18-22 | GET used for state change |
...

### Module: services/worker/ (Java/Kotlin)
...

### Module: frontend/ (Node/TS — framework review pending v3)

(Agnostic-only findings)
| Severity | Skill / Source | File | Lines | Finding |
...

### Specialist Findings

#### security-reviewer
...

#### architecture-reviewer
...

### Summary

- Total findings: {N}
- High: {n}; Medium: {n}; Low: {n}
- Modules with no findings: {list}
```

---

## Edge Cases

| Case | Behavior |
|---|---|
| Multiple markers walking up (nested Maven) | Use the nearest (deepest) marker |
| Multiple stacks at same dir level (e.g., `pom.xml` + `package.json`) | Multi-stack module — load skills from all detected stacks |
| Path arg outside any module | Scope to the path; treat as unknown-stack (agnostic only) |
| Git submodules | Treat as normal directories; no special handling in v1 |
| Empty diff | Print "no changes to review" and exit; do not fall through to whole-repo |
| Specialist dispatch fails | Continue review; note the dispatch failure in the report |
| Skill produces zero findings | Skip in output (no empty sections) |

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Treating any YAML as a backend marker | Backend markers are language/dependency files. Generic YAML (CI configs, K8s manifests) does NOT activate this agent |
| Dispatching `cost-reviewer` on backend code | `cost-reviewer` is infra-flavored — backend cost concerns (connection pools, executor sizing) are deferred |
| Failing to scope monorepo output by module | Findings without module grouping are unreadable in a 5-service repo. Always group |
| Persisting greenfield stack choice | The user re-confirms each greenfield run unless they manually pin via `.shield.json` |
| Running framework-specific Spring skills before Plan 2 lands | v1 ships zero framework skills. Java/Kotlin repos receive agnostic-only review until Plan 2 |
```

- [ ] **Step 2: Verify the agent file is well-formed**

Read the file back and confirm:
- Frontmatter has `name`, `description`, `model: inherit`
- Persona, Trigger Keywords, Weight sections present
- Stack detection table covers all 4 stacks
- Specialist dispatch list excludes cost/well-architected/kubernetes
- Output Format section shows monorepo grouping

- [ ] **Step 3: Commit**

```bash
git add shield/agents/backend-reviewer.md
git commit -m "feat(shield): add backend-reviewer agent"
```

---

### Task 10: /review-backend command

**Files:**
- Create: `shield/commands/review-backend.md`

- [ ] **Step 1: Write the command file**

Write `shield/commands/review-backend.md`:

```markdown
---
name: review-backend
description: Run backend-only code review with stack detection, agnostic + framework skills, and specialist agent dispatch
args: "[path or scope] [--full]"
---

# Review Backend

Run a focused backend code review. Detects the stack (Java/Kotlin, Python, Node/TS, Go) from repo markers, loads agnostic and framework-specific skills under `shield/skills/backend/`, and dispatches cross-cutting concerns to specialist agents.

## Usage

`/review-backend [path or scope] [--full]`

- `/review-backend` (no arg, on a branch) — review changed files vs `main`
- `/review-backend services/api/` — review a specific subtree
- `/review-backend --full` or `/review-backend .` — review the whole repo (excluding the default exclude list)

## Output Path — MANDATORY

First, find the project root by locating `.shield.json` (check current directory, then parent directories). Read `.shield.json` to get `output_dir` (default: `docs/shield`). Then determine the feature folder name and run number:

- **Feature folder** (`{feature}`): Use the current feature directory name (e.g., `auth-feature-20260319`). If none exists yet, derive from the current branch name or story context and append `-YYYYMMDD`.
- **Run number** (`{N}`): Count existing folders inside `{output_dir}/{feature}/code-review/` and add 1.
- **Slug** (`{slug}`): Use the story ID if available from plan context, otherwise use the current git branch name.

Write the review summary using the Write tool to:

```
{project_root}/{output_dir}/{feature}/code-review/{N}-{slug}/summary.md
```

Replace `{project_root}` with the absolute path to the directory containing `.shield.json`.

**Do NOT** use a relative path. **Do NOT** use the plugin directory. **Do NOT** invent custom filenames. The Write tool creates directories automatically.

## Behavior

1. Resolve scope per the usage rules above
2. Invoke the `backend-reviewer` agent with the resolved scope
3. The agent runs stack detection, loads skills, dispatches specialists, and aggregates findings — see `shield/agents/backend-reviewer.md` for full agent behavior
4. Per-agent detailed findings written to `{output_dir}/{feature}/code-review/{N}-{slug}/detailed/<agent>.md`
5. Applied fixes logged to `{output_dir}/{feature}/code-review/{N}-{slug}/changes.md`
6. **Write review summary, detailed findings, and changes log to the paths above**
7. After writing, update `{output_dir}/manifest.json` with the new review entry and regenerate `{output_dir}/index.html`
8. Present to user with options: apply all, select specific, skip, post to PM
9. Apply selected fixes

## Relationship to /review

`/review` is comprehensive — it includes backend, terraform, kubernetes, atmos, and any other detected domain in one pass. Use `/review-backend` when you want backend-only feedback (faster) or when running against a backend-only repo. The two commands share the same output writer; they differ only in which domain skills/agents are loaded.

## Single-Agent Shortcuts

Within a backend review, individual specialists can also be dispatched directly:

- `/review-security` — security reviewer only
- `/review-cost` — cost reviewer only (note: not dispatched from `/review-backend` because cost is infra-flavored)
- `/review-well-architected` — AWS Well-Architected Framework review (not dispatched from `/review-backend`)
```

- [ ] **Step 2: Commit**

```bash
git add shield/commands/review-backend.md
git commit -m "feat(shield): add /review-backend command"
```

---

### Task 11: Register backend domain in /review

**Files:**
- Modify: `shield/commands/review.md`

- [ ] **Step 1: Inspect the current /review behavior section**

Read `shield/commands/review.md`. Locate the line that currently says:

```
   - Domain-specific review skills (terraform, atmos, etc.)
```

Locate the line in the agent reviews list:

```
   - Agent reviews (security, cost, architecture, operations)
```

- [ ] **Step 2: Update the domain list to include backend**

Replace `Domain-specific review skills (terraform, atmos, etc.)` with `Domain-specific review skills (terraform, atmos, kubernetes, backend, etc.)`.

This is the only required change — the existing dispatcher logic already auto-loads any domain found in `shield/skills/<domain>/`.

- [ ] **Step 3: Verify the file with git diff**

```bash
git diff shield/commands/review.md
```

Expected diff: a single line change adding `kubernetes, backend` to the domain list.

- [ ] **Step 4: Commit**

```bash
git add shield/commands/review.md
git commit -m "feat(shield): register backend domain in /review command"
```

---

### Task 12: End-to-end validation against the fixture

**Files:**
- (No file changes — validation step)

- [ ] **Step 1: Dispatch backend-reviewer against the full fixture**

Use the `Agent` tool with `subagent_type: general-purpose`. Send this prompt:

```
You are the backend-reviewer agent.

Read in full: shield/agents/backend-reviewer.md

Apply the agent's behavior end-to-end against the fixture at: shield/examples/spring-boot-api/

Detect the stack, load agnostic skills (read each SKILL.md under shield/skills/backend/), apply each skill's Evaluation Points to the relevant files in the fixture, and produce the agent's standard output format.

Do NOT dispatch specialists for this validation run — focus on the skill output.

Output the full Backend Review report.
```

- [ ] **Step 2: Compare output against the oracle**

Read `shield/examples/spring-boot-api/docs/expected-findings.md`. The agent's output must include every row in the oracle, with matching severity. Count: there should be 38 expected findings across the 7 agnostic skills:

- code-quality-review: 5
- api-design-review: 8
- testing-strategy-review: 6
- database-review: 7
- error-observability-review: 5
- deployment-safety-review: 3
- concurrency-review: 4

Total: 38

- [ ] **Step 3: Document any gaps**

If the end-to-end run misses any oracle finding, identify which skill should have caught it and adjust that skill's "What to Look For" / "Critical Checks" section. Re-run Step 1 until all 38 findings appear.

If a finding appears that's NOT in the oracle, decide:
- Is it a real issue we should add to the oracle? (Update `expected-findings.md`)
- Is it a false positive? (Adjust the skill's rubric or "Common Mistakes" section)

- [ ] **Step 4: Commit any skill refinements from the validation run**

If skills were edited:

```bash
git add shield/skills/backend/ shield/examples/spring-boot-api/docs/expected-findings.md
git commit -m "fix(shield): refine backend skills based on end-to-end validation"
```

If no edits were needed, skip this step.

---

### Task 13: Bump shield to 2.9.0

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read the current marketplace registry**

Read `.claude-plugin/marketplace.json`. Locate the shield entry's `version` field (currently `"2.8.0"`).

- [ ] **Step 2: Bump to 2.9.0**

Change the shield entry's `version` from `"2.8.0"` to `"2.9.0"`.

Per `CLAUDE.md`, the version lives **only** in the marketplace.json — do not add a `version` field to `shield/.claude-plugin/plugin.json`.

- [ ] **Step 3: Verify the diff**

```bash
git diff .claude-plugin/marketplace.json
```

Expected: a single-line change in the shield entry's version.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(shield): bump to 2.9.0 — backend domain foundation (Plan 1)"
```

---

## Self-review checklist (run at end of plan execution)

Before declaring Plan 1 complete:

- [ ] All 7 agnostic skills exist under `shield/skills/backend/`
- [ ] Each skill has a corresponding entry in `shield/examples/spring-boot-api/docs/expected-findings.md`
- [ ] `shield/agents/backend-reviewer.md` exists and includes stack detection, skill loading, specialist dispatch, output format
- [ ] `shield/commands/review-backend.md` exists and follows the shield output-path convention
- [ ] `shield/commands/review.md` mentions `backend` in the domain-skill list
- [ ] `.claude-plugin/marketplace.json` shows shield at `2.9.0`
- [ ] End-to-end validation (Task 12) passes — all 38 oracle findings caught
- [ ] No SKILL.md contains a TBD/TODO
- [ ] All commits are on the `feat/backend-domain-exploration` branch

## After Plan 1 ships

Plan 2 picks up: 6 Spring/JVM skills, conditional Spring sub-detection in the agent, Spring-specific fixture violations, oracle entries for all 6 Spring skills.

Plan 3 picks up: `/plan` domain-detection step, `/plan-review` reviewer auto-detect registration, `/implement` per-step domain hook extension.
