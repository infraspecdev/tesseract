# Plan Review: Input Validation & JWT Auth

**Date:** 2026-03-20
**Plan:** `input-validation-and-auth`
**Reviewers:** Security Engineer, DX Engineer, Agile Coach, Architecture, Product Manager

---

## Composite Score

| Reviewer | Score | Grade |
|----------|-------|-------|
| Security Engineer | 38/100 | D+ |
| Architecture | 52/100 | B- |
| DX Engineer | 68/100 | B |
| Agile Coach | 72/100 | B+ |
| Product Manager | 78/100 | B |
| **Weighted Average** | **61/100** | **C+** |

---

## Verdict

The plan is **well-structured** with clear epics, correct dependency ordering, consistent story sizing, and testable acceptance criteria. However, it has **critical security gaps** (no token revocation, no password hashing, no rate limiting, no threat model) and **missing developer foundations** (no dependency manifest, no setup instructions, no configuration strategy). The plan treats authentication as a feature rather than a security boundary.

---

## P0 Recommendations (Must Fix Before Implementation)

| # | Source | Recommendation |
|---|--------|---------------|
| 1 | Security | **Add token revocation mechanism.** Implement a server-side blocklist and `POST /auth/logout` endpoint. Without revocation, a leaked token is valid until expiry with no mitigation. |
| 2 | Security | **Hash passwords in the user store.** Even for a demo, use `passlib[bcrypt]`. Storing plaintext passwords teaches the wrong pattern. |
| 3 | Security | **Add rate limiting to the login endpoint.** Use `slowapi` or similar. Without this, `/auth/token` is trivially brute-forceable. |
| 4 | Security | **Write a minimal threat model.** Document assets, threat actors, attack vectors, and mitigations before starting E3. |
| 5 | DX | **Add a prerequisites & setup story (Story 0).** Create `pyproject.toml`, specify Python version, dependencies, and commands to install/run/test. No story can begin without this. |
| 6 | DX | **Define a configuration strategy.** Specify whether to use `pydantic-settings`, `os.environ`, or `.env` files. Document defaults for JWT_ALGORITHM and ACCESS_TOKEN_EXPIRE_MINUTES. |
| 7 | Agile | **Reorder E3-S4 (login) before E3-S3 (protect endpoints).** Developers need the login endpoint to generate tokens for testing protected endpoints. |
| 8 | Agile | **Add an explicit Definition of Done.** State: code reviewed, tests passing, linting clean, OpenAPI docs updated. |
| 9 | PM | **Add plan-level success metrics.** Define measurable "done" criteria: target test coverage, zero unhandled exceptions, all endpoints documented. |
| 10 | Architecture | **Explicitly scope as demo-only or add persistence.** Adding JWT auth to an in-memory dict creates a false security posture. |

---

## P1 Recommendations (Should Fix During Implementation)

| # | Source | Recommendation |
|---|--------|---------------|
| 1 | Security | Specify JWT_SECRET minimum entropy (32 bytes). Document secret rotation. |
| 2 | Security | Add resource-level authorization (users can only modify their own tasks). Store `created_by` from JWT `sub`. |
| 3 | Security | Guard against mass assignment — exclude `id` from TaskUpdate, use `model_dump(exclude_unset=True)`. |
| 4 | Security | Add security response headers middleware (X-Content-Type-Options, X-Frame-Options, HSTS). |
| 5 | Security | Log security events: failed logins, invalid tokens, 403s, admin actions. |
| 6 | Security | Pin PyJWT version, verify correct package, add `pip-audit` to test suite. |
| 7 | Architecture | Add CORS middleware configuration with explicit allow-list. |
| 8 | Architecture | Address `_counter` race condition — use `uuid4()` or `itertools.count()`. |
| 9 | Agile | Add business context ("why") to each story. |
| 10 | Agile | Add explicit dependency from E2-S1 to E1-S2 (both modify `routes/tasks.py`). |
| 11 | Agile | Tighten E3-S3 AC: add "DELETE with valid non-admin token returns 403." |
| 12 | Agile | Specify logging requirements for E2-S2 (level, format, logger name). |
| 13 | DX | Define the in-memory user store (exact demo users, roles, password handling). |
| 14 | DX | Define error response schemas for all error types (404, 422, 500). |
| 15 | DX | Add CI story or extend E4-S1 with GitHub Actions workflow. |
| 16 | PM | Document the breaking change and migration path for adding auth. |
| 17 | PM | Add an outcome-oriented executive summary for non-technical stakeholders. |

---

## P2 Recommendations (Nice to Have)

| # | Source | Recommendation |
|---|--------|---------------|
| 1 | Security | Add refresh token support for short-lived access tokens. |
| 2 | Security | Document token expiry default and add config validation. |
| 3 | Security | Add TLS enforcement note. |
| 4 | Architecture | Define environment-specific configuration via `pydantic-settings`. |
| 5 | Architecture | Bound the in-memory store to prevent OOM. |
| 6 | Agile | Add coverage target to E4-S1 (e.g., >= 85% line coverage). |
| 7 | Agile | Consider splitting E4-S1 into CRUD tests and auth flow tests. |
| 8 | DX | Add code snippets for non-obvious FastAPI patterns. |
| 9 | PM | Call out explicit non-goals (token refresh, CORS, API versioning). |
| 10 | PM | Fold E4-S1 tests into each story as AC rather than standalone epic. |

---

## Next Steps

- **Apply P0 fixes** to the plan before implementation
- `/pm-sync` — sync updated stories to project management tool
- `/implement` — start TDD-based implementation
