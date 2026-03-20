# Security Engineer Review — Plan Review Mode

**Score:** 38/100 | **Grade:** D+

## Check Results

| # | Check | Grade | Rationale |
|---|-------|-------|-----------|
| 1 | Authentication mechanism | WARN | JWT/HS256 via PyJWT is reasonable for single-service. No mention of RS256 for multi-service. |
| 2 | Authorization model | WARN | Role-based for delete, user-level for create/update. No resource ownership (any user can update any task). |
| 3 | Input validation | PASS | Pydantic models with max_length, status enum, required fields. Specific testable AC. |
| 4 | Secret management | FAIL | JWT_SECRET from env var only. No rotation, no minimum entropy, no secrets manager guidance. |
| 5 | Token lifecycle | FAIL | No token revocation, no blocklist, no logout endpoint, no refresh tokens. |
| 6 | Error information leakage | PASS | Stack traces logged server-side, not exposed. Consistent JSON error bodies. |
| 7 | Dependency security | WARN | PyJWT added but no version pinning, no pip-audit, no PyJWT vs jwt package clarification. |
| 8 | OWASP Top 10 | WARN | Injection mitigated. Broken auth partial. No CORS, no HTTPS, possible mass assignment via TaskUpdate. |
| 9 | Data protection | FAIL | No TLS/HTTPS mention. No password hashing in user store. |
| 10 | API security headers | FAIL | No X-Content-Type-Options, HSTS, X-Frame-Options, CSP, or CORS. |
| 11 | Rate limiting | FAIL | No rate limiting on login endpoint. Textbook brute-force target. |
| 12 | Session management | WARN | Stateless JWT is fine. No token storage guidance, no concurrent session handling, no logout. |
| 13 | Security event logging | WARN | General exception logging exists. No security-specific events (failed logins, invalid tokens, 403s). |
| 14 | Threat model | FAIL | No threat model anywhere in the plan. |

## Key Finding

The plan delivers solid input validation and error handling but treats authentication as a feature checkbox rather than a security boundary.

## P0 Recommendations

1. Add token revocation mechanism (blocklist + logout endpoint)
2. Hash passwords in user store (passlib[bcrypt])
3. Add rate limiting to login endpoint (slowapi)
4. Write minimal threat model before E3

## P1 Recommendations

1. JWT_SECRET minimum entropy (32 bytes) + rotation guidance
2. Resource-level authorization (created_by field)
3. Mass assignment guard (exclude id from TaskUpdate)
4. Security response headers middleware
5. Security event logging
6. Pin PyJWT version + pip-audit
