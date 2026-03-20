# Security Code Review — Detailed Findings

**Risk Rating:** HIGH
**Findings:** 3 HIGH, 5 MEDIUM, 3 LOW

---

## HIGH

### H1: No authentication or authorization on any endpoint
- **File:** `src/main.py:6`
- **OWASP:** A01:2021 — Broken Access Control
- **Risk:** Any unauthenticated user can create, modify, or delete any task
- **Fix:** Add OAuth2PasswordBearer dependency to mutation endpoints

### H2: No input validation on POST /tasks/ — accepts arbitrary dict
- **File:** `src/routes/tasks.py:12`
- **OWASP:** A08:2021 — Software and Data Integrity Failures
- **Risk:** Mass assignment, parameter pollution, memory exhaustion
- **Fix:** Use `Task` Pydantic model as parameter type

### H3: No input validation on PUT /tasks/{id} — mass assignment
- **File:** `src/routes/tasks.py:33-36`
- **Risk:** Attacker can overwrite `id` field or inject arbitrary keys
- **Fix:** Define `TaskUpdate` model, use `model_dump(exclude_unset=True)`

---

## MEDIUM

### M1: Unhandled KeyError leaks internal details
- **File:** `src/routes/tasks.py:29,35,42`
- **OWASP:** A05:2021 — Security Misconfiguration
- **Risk:** Stack traces reveal file paths, library versions
- **Fix:** Check key existence, raise HTTPException(404)

### M2: No pagination on GET /tasks/
- **File:** `src/routes/tasks.py:22-23`
- **Risk:** DoS via unbounded response serialization
- **Fix:** Add `skip`/`limit` query parameters

### M3: No rate limiting
- **File:** `src/main.py` (global)
- **Risk:** DoS, brute-force, resource exhaustion
- **Fix:** Add `slowapi` middleware

### M4: No CORS configuration
- **File:** `src/main.py` (global)
- **Risk:** Blocks legitimate cross-origin clients or enables CSRF if wildcard added later
- **Fix:** Add `CORSMiddleware` with explicit allow-list

### M5: No security headers
- **File:** `src/main.py` (global)
- **Risk:** MIME sniffing, clickjacking, downgrade attacks
- **Fix:** Add middleware for X-Content-Type-Options, X-Frame-Options, HSTS

---

## LOW

### L1: Race condition on global _counter
- **File:** `src/routes/tasks.py:8,14-16`
- **Risk:** Duplicate task IDs under concurrency
- **Fix:** Use `uuid4()` or `itertools.count()`

### L2: No dependency manifest
- **Risk:** Cannot audit for CVEs or ensure reproducible builds
- **Fix:** Add `pyproject.toml` with pinned versions, integrate `pip-audit`

### L3: No security tests
- **File:** `tests/test_tasks.py`
- **Risk:** Security regressions go undetected
- **Fix:** Add tests for 404, 422, auth enforcement
