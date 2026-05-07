# Expected Findings

This file is the RED-GREEN oracle for the backend domain skills. Each row pairs an intentional violation in the fixture with the skill that should catch it.

When adding a new violation, append a row here. When deleting a violation, remove its row.

The table is established in Task 2 (the first skill task). Until then, this file has no rows.

| Skill | File | Lines | Severity | What's wrong |
|---|---|---|---|---|
| code-quality-review | `service/UserService.java` | 9-13 | high | God class — handles users, orders, emails, payments, audit logs |
| code-quality-review | `service/UserService.java` | 17-34 | high | `registerUser` does five things (SRP violation) |
| code-quality-review | `service/UserService.java` | 37-52 | high | `registerAdmin` is a copy of `registerUser` (DRY violation) |
| code-quality-review | `service/UserService.java` | 56-58 | medium | `findUsers` accepts unused parameters (YAGNI / speculative generality) |
| code-quality-review | `service/UserService.java` | 61-76 | medium | `doStuff` has poor naming, deep nesting, no early returns |
| api-design-review | `controller/UserController.java` | 12 | medium | No version prefix in `@RequestMapping` ("/api" alone) |
| api-design-review | `controller/UserController.java` | 19-24 | high | GET used for a state-changing operation (`/createUser`) |
| api-design-review | `controller/UserController.java` | 28-31 | medium | Verb in URI (`/getAllUsers`); resource modeling violation |
| api-design-review | `controller/UserController.java` | 28-31 | medium | No pagination on a list endpoint |
| api-design-review | `controller/UserController.java` | 36-41 | high | 200 OK returned for missing resource (should be 404) |
| api-design-review | `controller/UserController.java` | 36-41 | medium | Inconsistent error response shape vs success shape |
| api-design-review | `controller/UserController.java` | 44-48 | high | PUT used for non-idempotent operation (append) |
| api-design-review | `controller/UserController.java` | 51-54 | low | DELETE returns 200 with body (should be 204 No Content) |
| testing-strategy-review | `test/.../UserServiceTest.java` | 15 | high | `@SpringBootTest` for unit-scope test (heavy slice + slow) |
| testing-strategy-review | `test/.../UserServiceTest.java` | 20-30 | high | Mocking the class under test — asserts the stub, not the implementation |
| testing-strategy-review | `test/.../UserServiceTest.java` | 33-39 | medium | Sleep-based timing assertion (flaky) |
| testing-strategy-review | `test/.../UserServiceTest.java` | 42-47 | medium | Shared mutable static state across tests |
| testing-strategy-review | `test/.../UserServiceTest.java` | 52-58 | medium | Asserts internal detail / weak assertion |
| testing-strategy-review | `test/.../UserServiceTest.java` | 61-65 | high | No assertions — test passes regardless |
| database-review | `model/User.java` | 8 | medium | No `@Table` with explicit name |
| database-review | `model/User.java` | 13-14 | medium | No `@Column` constraints (nullable, unique, length) on email/password |
| database-review | `model/User.java` | 18-20 | high | EAGER fetch on `@OneToMany` causes load-everything; risks N+1 and memory blowups |
| database-review | `repository/UserRepository.java` | 12 | high | `findAll` with EAGER child loads triggers SELECT N+1 |
| database-review | `repository/UserRepository.java` | 14-15 | medium | LIKE query without pagination; full table scan on production-sized data |
| database-review | `db/migration/V1__create_users.sql` | 2-6 | medium | No index on `email` column |
| database-review | `db/migration/V3__drop_email_column.sql` | 5 | high | Destructive migration without expand/contract; breaks rolling deploys |
| error-observability-review | `exception/GlobalExceptionHandler.java` | 12-16 | high | Catch-all `Throwable` handler maps every exception to 500 |
| error-observability-review | `exception/GlobalExceptionHandler.java` | 14 | high | `System.out.println` for error logging — no level, no structure, no correlation ID |
| error-observability-review | `exception/GlobalExceptionHandler.java` | 16 | medium | Returns raw exception message to client — leaks internals |
| error-observability-review | `service/OrderService.java` | 10-18 | medium | Exception-as-control-flow in `isValid` |
| error-observability-review | `service/OrderService.java` | 22-30 | high | `chargeCustomer` swallows exception silently with no log/metric/rethrow |
| deployment-safety-review | `config/AppConfig.java` | 14-17 | high | In-memory cache in a singleton bean — diverges across multi-instance deploys |
| deployment-safety-review | `config/AppConfig.java` | 21 | medium | Risky pricing change rolled in via static constant — no feature flag |
| deployment-safety-review | `db/migration/V3__drop_email_column.sql` | 5 | high | Destructive migration without feature-flag gating; cannot roll back without restoring data |
| concurrency-review | `service/CounterService.java` | 14-15 | high | Shared mutable state (`HashMap`, `int`) in singleton without synchronization |
| concurrency-review | `service/CounterService.java` | 18-23 | high | Read-modify-write race on `totalRequests` and counter map |
| concurrency-review | `service/CounterService.java` | 27-33 | high | Fire-and-forget `CompletableFuture.runAsync` — exceptions silently lost |
| concurrency-review | `service/CounterService.java` | 37-39 | medium | Operation not idempotent — retry causes duplicate side effects |
| spring-config | `config/AppProperties.java` | 8-11 | high | `@ConfigurationProperties` without `prefix` attribute — properties will not bind |
| spring-config | `config/AppProperties.java` | 8-11 | medium | Missing `@Validated` on `@ConfigurationProperties` — invalid config won't fail at startup |
| spring-config | `config/AppProperties.java` | 13-22 | medium | Mutable `@ConfigurationProperties` bean (setters); prefer immutable records |
| spring-config | `application-prod.yml` | 8-9 | high | Hardcoded secret (`spring.datasource.password`) in committed source |
| spring-config | `config/AppConfig.java` | 27-28 | medium | `@Value` for typed config; should use `@ConfigurationProperties` |
| spring-web | `controller/UserController.java` | 18-19 | high | Field injection via `@Autowired` — should be constructor injection |
| spring-web | `controller/UserController.java` | 62-65 | medium | `@RequestMapping` with no `method` attribute; use `@PostMapping` |
| spring-web | `controller/UserController.java` | 62-65 | high | Missing `@Valid` on `@RequestBody`; incoming payload unvalidated |
| spring-web | `controller/UserController.java` | 71-75 | medium | `@ResponseStatus` + return value mix; status source is ambiguous |
| spring-web | `controller/UserController.java` | 79-82 | low | Mixed-case path segment `/userProfile/`; inconsistent with kebab-case elsewhere |
| spring-data | `service/OrderProcessingService.java` | 18-21 | high | `@Transactional` on private method — proxies don't intercept private |
| spring-data | `service/OrderProcessingService.java` | 26-28 | high | Self-invocation of `@Transactional` method bypasses the proxy |
| spring-data | `service/OrderProcessingService.java` | 32-35 | medium | Read method missing `readOnly = true` |
| spring-data | `service/OrderProcessingService.java` | 39-42 | medium | `REQUIRES_NEW` propagation without justification |
| spring-data | `repository/UserRepository.java` | (updateEmail) | high | Mutating JPQL `@Query` without `@Modifying` — update never runs |
