# Python API Example

A sample FastAPI application that demonstrates Shield's pipeline for application code.

## What This Shows

This example walks through Shield's pipeline using a FastAPI task management API with intentional issues:

- **Security issues**: Missing input validation, no auth on endpoints
- **Operations issues**: No error handling on external calls, missing logging
- **DX issues**: Vague acceptance criteria in the plan
- **Testing gaps**: No test coverage for edge cases

## Pipeline Walkthrough

### 1. Research (`/research`)
Research FastAPI best practices, API security patterns, and testing strategies.

### 2. Planning (`/plan`)
Generate a plan for the task management API with stories.

### 3. Plan Review (`/plan-review`)
Reviewers evaluate the plan:
- Security reviewer checks auth strategy and input validation
- DX engineer checks story clarity
- Agile coach checks sprint-readiness

### 4. Implementation (`/implement`)
TDD-based implementation with per-step review.

### 5. Code Review (`/review`)
Comprehensive review catches missing validation, auth gaps, and test coverage.

## Try It

1. Install Shield: `/plugin install shield@tesseract`
2. `cd` into this directory
3. Run `/research FastAPI best practices for task management APIs`
4. Follow the pipeline from there

## Source Files

- `src/main.py` — FastAPI app entry point
- `src/routes/tasks.py` — Task CRUD endpoints
- `src/models.py` — Pydantic models
- `tests/test_tasks.py` — Basic test (incomplete)
