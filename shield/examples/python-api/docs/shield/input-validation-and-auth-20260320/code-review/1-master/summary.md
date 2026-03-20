# Code Review: Task Manager API (Baseline)

**Date:** 2026-03-20
**Branch:** `master`
**Scope:** Full codebase (`src/`, `tests/`)
**Reviewers:** Security Reviewer, Code Correctness Reviewer

---

## Finding Summary

| Severity | Security | Correctness | Total |
|----------|----------|-------------|-------|
| CRITICAL | 0 | 3 | 3 |
| HIGH | 3 | 4 | 7 |
| MEDIUM | 5 | 6 | 11 |
| LOW | 3 | 4 | 7 |
| **Total** | **11** | **17** | **28** |

**Overall Risk Rating: HIGH** — The API is not safe for any network-accessible deployment.

---

## CRITICAL Findings

| # | File | Line | Finding | Source |
|---|------|------|---------|--------|
| C1 | `src/routes/tasks.py` | 29, 35, 42 | **Unhandled KeyError** on GET/PUT/DELETE causes 500 with stack trace leak | Both |
| C2 | `src/routes/tasks.py` | 8, 14-15 | **Race condition on `_counter`** — non-atomic ID generation, duplicate IDs under concurrency | Correctness |
| C3 | `src/routes/tasks.py` | 12, 33 | **No input validation** — raw `dict` params bypass Pydantic, allow arbitrary key injection | Both |

## HIGH Findings

| # | File | Line | Finding | Source |
|---|------|------|---------|--------|
| H1 | `src/main.py` | 6 | **No authentication** — all endpoints including mutations are publicly accessible | Both |
| H2 | `src/routes/tasks.py` | 35 | **Mass assignment** — `dict.update()` allows overwriting `id` and internal fields | Both |
| H3 | `src/routes/tasks.py` | 11 | **Wrong status code** — POST returns 200 instead of 201 Created | Correctness |
| H4 | `src/routes/tasks.py` | 39 | **Wrong status code** — DELETE returns 200 instead of 204 No Content | Correctness |
| H5 | `src/routes/tasks.py` | 12 | **Unused Pydantic model** — Task model defined in models.py but never imported | Correctness |
| H6 | `src/main.py` | - | **No global exception handler** — unhandled exceptions leak raw tracebacks | Both |
| H7 | `src/models.py` | 8 | **No status enum** — `status: str` accepts any value | Both |

## MEDIUM Findings

| # | File | Line | Finding | Source |
|---|------|------|---------|--------|
| M1 | `src/models.py` | 6 | No `max_length` on title — allows multi-MB strings | Both |
| M2 | `src/routes/tasks.py` | 22-23 | No pagination on GET /tasks/ — unbounded response | Security |
| M3 | `src/main.py` | - | No rate limiting on any endpoint | Security |
| M4 | `src/main.py` | - | No CORS configuration | Security |
| M5 | `src/main.py` | - | No security headers (CSP, HSTS, X-Content-Type-Options) | Security |
| M6 | `src/main.py` | 15 | Import placement violates PEP 8 (after function definition) | Correctness |
| M7 | `src/routes/tasks.py` | - | No `response_model` annotations on endpoints | Correctness |

## LOW Findings

| # | File | Line | Finding | Source |
|---|------|------|---------|--------|
| L1 | `src/routes/tasks.py` | 7 | In-memory store not suitable for multi-worker deployment | Both |
| L2 | `tests/test_tasks.py` | - | Shared mutable state across tests (order-dependent) | Correctness |
| L3 | `tests/test_tasks.py` | - | Only 2 tests — no 404, validation, update, delete, or auth tests | Both |
| L4 | `tests/test_tasks.py` | 15 | Test asserts 200 (wrong) instead of 201 | Correctness |
| L5 | - | - | No `pyproject.toml` or `requirements.txt` — no dependency audit possible | Security |

---

## Top 3 Recommended Fixes

1. **Use Pydantic models** — Replace `dict` params with `TaskCreate`/`TaskUpdate` models (fixes C3, H2, H5, H7, M1)
2. **Add 404 handling** — Check key existence before access, raise `HTTPException(404)` (fixes C1)
3. **Add authentication** — JWT auth dependency on mutation endpoints (fixes H1)

These three changes address 3 CRITICAL and 3 HIGH findings.

---

## Next Steps

- Apply the `input-validation-and-auth` plan to systematically address all findings
- `/implement` — start TDD-based implementation
