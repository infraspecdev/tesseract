# Code Correctness Review — Detailed Findings

**Findings:** 3 CRITICAL, 4 HIGH, 6 MEDIUM, 4 LOW

---

## CRITICAL

### C1: Unhandled KeyError on GET, PUT, DELETE — causes 500
- **File:** `src/routes/tasks.py:29,35,42`
- **Fix:** Check `task_id in tasks`, raise `HTTPException(status_code=404)`

### C2: Race condition on _counter with concurrent requests
- **File:** `src/routes/tasks.py:8,14-15`
- **Fix:** Use `itertools.count()` or `uuid.uuid4()`

### C3: No input validation on create_task and update_task
- **File:** `src/routes/tasks.py:12,33`
- **Fix:** Replace `dict` params with Pydantic models from `models.py`

---

## HIGH

### H1: update_task allows overwriting the id field
- **File:** `src/routes/tasks.py:35`
- **Fix:** Use Pydantic model excluding `id`, use `model_dump(exclude_unset=True)`

### H2: POST /tasks/ returns 200 instead of 201
- **File:** `src/routes/tasks.py:11`
- **Fix:** Add `status_code=201` to decorator

### H3: DELETE /tasks/{id} returns 200 instead of 204
- **File:** `src/routes/tasks.py:39`
- **Fix:** Return `Response(status_code=204)`

### H4: No authentication or authorization
- **File:** `src/main.py:6`
- **Fix:** Add auth middleware or `Depends()` to mutation endpoints

---

## MEDIUM

### M1: Task model defined but never used
- **File:** `src/models.py:5-9`
- **Fix:** Import and use in route handlers

### M2: status field lacks enum validation
- **File:** `src/models.py:8`
- **Fix:** Use `Literal["open", "in_progress", "done"]` or `StrEnum`

### M3: title field has no length constraint
- **File:** `src/models.py:6`
- **Fix:** Use `Field(min_length=1, max_length=200)`

### M4: No global exception handler
- **File:** `src/main.py`
- **Fix:** Add `@app.exception_handler(Exception)` returning sanitized 500

### M5: Import placement violates PEP 8
- **File:** `src/main.py:15`
- **Fix:** Move router import to top of file

### M6: No response_model annotations
- **File:** `src/routes/tasks.py` (all endpoints)
- **Fix:** Add `response_model=TaskResponse` to decorators

---

## LOW

### L1: In-memory store not suitable for multi-worker deployment
- **File:** `src/routes/tasks.py:7`
- **Fix:** Document limitation; use database for production

### L2: Shared mutable state across tests
- **File:** `tests/test_tasks.py`
- **Fix:** Add fixture to reset `tasks` and `_counter` before each test

### L3: Very low test coverage (2 tests)
- **File:** `tests/test_tasks.py`
- **Fix:** Add tests for all endpoints, error paths, edge cases

### L4: test_create_task asserts 200 instead of 201
- **File:** `tests/test_tasks.py:15`
- **Fix:** Update assertion after fixing endpoint status code
