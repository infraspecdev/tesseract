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
