# User Authentication v2

## 1. Header
| Field | Value |
|---|---|
| Owner | @anika.dev |
| Status | Draft |
| PRD type | Standard |
| Date created | 2026-05-13 |
| Last updated | 2026-05-13 |
| Linked design spec | null |
| Linked research | null |
| Decision-maker | @eng-lead |
| Sign-off contacts | Legal: @legal, Security: @sec-review, Support: @cx-lead |
| Linked plans | _(auto-populated by /plan)_ |

## 2. Problem & context
Users cannot log in with email + password via the legacy `/auth/login` route without hitting frequent session-loss bugs. The endpoint has no rate limiting, allowing credential-stuffing attacks that have triggered 3 security incidents in the last 90 days. Support handles ~200 "locked out" tickets/week because there is no self-serve password-reset flow. Cost of inaction: continued reputational risk and ~40 eng-hours/month spent on manual account unlocks.

## 3. Target users / personas
| ID | Persona | Goals | Frictions today |
|---|---|---|---|
| P1 | Anika — security-conscious user | Sign in quickly and recover access without contacting support | Session drops after a few hours; no self-serve reset; receives no warning before lockout |

## 4. Goals & non-goals
### Goals
1. Replace the legacy login endpoint with a hardened v2 endpoint that enforces rate limiting.
2. Provide a fully self-serve password-reset flow via email.
3. Emit structured telemetry for all authentication events.

### Non-goals
- SSO / SAML integration (separate workstream).
- Social login (OAuth with Google/GitHub) — out of scope this cycle.
- Admin-side forced password reset for enterprise accounts.

## 5. Success metrics
| Metric | Type | Target | Counter |
|---|---|---|---|
| Support tickets tagged "locked out" | Lagging | < 50/week within 4 weeks of full rollout | — |
| Login success rate | Leading | ≥ 98% of valid-credential attempts succeed | Login error rate |
| Credential-stuffing incidents | Lagging | 0 within 30 days of rate-limiting being active | — |

**Dashboard plan:** DataDog dashboard `auth-v2-health` — login success rate, 401 rate, 429 rate, recovery email latency p99.

## 6. User stories & scenarios

### Story US-1: Happy-path login
- **Persona:** P1
- **Goal:** Sign in with email + password and land on the dashboard within 3 seconds.
- **Happy path:**
  1. P1 navigates to `/login`.
  2. P1 enters valid email and password, submits.
  3. `POST /v2/auth/login` returns 200 + JWT session token.
  4. Client stores token; P1 is redirected to `/dashboard`.
- **Error / timeout / abandon paths:** Invalid credentials → 401 with "Incorrect email or password" message; server timeout → 504 with retry guidance.
- **Edge cases:** Account with no `user_credentials` row (migrated legacy user) → treated as invalid credentials.
- **State transitions:** unauthenticated → authenticated.
- **Cross-functional handoffs:** Security review before endpoint ships.
- **Acceptance criteria (Given/When/Then):**
  - Given a registered user with valid credentials, When they POST to `/v2/auth/login`, Then the response is 200 with a JWT.
  - Given a registered user with an incorrect password, When they POST to `/v2/auth/login`, Then the response is 401.

### Story US-2: Password reset
- **Persona:** P1
- **Goal:** Regain access to the account without calling support.
- **Happy path:**
  1. P1 clicks "Forgot password" on the login page.
  2. P1 enters their email; `POST /v2/auth/recover` is called.
  3. Recovery email arrives within 60 seconds with a reset link.
  4. P1 clicks the link; it is valid (single-use, 15-min TTL).
  5. P1 enters a new password; `POST /v2/auth/reset` returns 200.
  6. All existing sessions are invalidated; P1 is redirected to login.
- **Error / timeout / abandon paths:** Unknown email → 200 (no-enumeration); expired link → 410; re-used link → 410.
- **Edge cases:** P1 requests reset twice — only the second link should be valid.
- **State transitions:** unauthenticated (with reset token) → unauthenticated (token spent) → authenticated after new login.
- **Cross-functional handoffs:** Transactional email provider config; Legal review of reset email copy.
- **Acceptance criteria (Given/When/Then):**
  - Given a registered user, When they POST to `/v2/auth/recover` with their email, Then a recovery email arrives within 60 seconds.
  - Given a valid single-use reset token, When used once, Then the password is updated and the token is invalidated.
  - Given a used reset token, When submitted again, Then the response is 410.

### Story US-3: Rate limiting on login
- **Persona:** P1 (and malicious actors as negative case)
- **Goal:** Ensure brute-force attempts are blocked while P1 is not disrupted.
- **Happy path:** P1 makes up to 10 login attempts/min without hitting rate limit.
- **Error / timeout / abandon paths:** 11th attempt within 60 s from same IP → 429 with `Retry-After` header.
- **Edge cases:** Legitimate user on a shared corporate IP that has been rate-limited — retry guidance in 429 body.
- **State transitions:** none.
- **Cross-functional handoffs:** Security team sign-off on limit thresholds.
- **Acceptance criteria (Given/When/Then):**
  - Given 10 consecutive login attempts from the same IP within 60 s, When the 11th attempt is made, Then the response is 429 with a `Retry-After` header.

## 7. Functional requirements
- FR-1 (US-1): `POST /v2/auth/login` validates credentials against `user_credentials` table and returns a signed JWT on success.
- FR-2 (US-3): Rate limiter rejects requests exceeding 10/min per source IP on the login endpoint.
- FR-3 (US-2): `POST /v2/auth/recover` sends a reset email; token is stored with 15-min TTL and single-use flag.
- FR-4 (US-2): `POST /v2/auth/reset` validates token, hashes new password, updates `user_credentials`, and invalidates all existing sessions.
- FR-5: Legacy `/auth/login` returns 301 to `/v2/auth/login` for 90 days.

## 8. Non-functional requirements
| NFR | Requirement |
|---|---|
| Performance | `POST /v2/auth/login` p99 < 200 ms at 500 req/s |
| Security | Passwords stored as bcrypt (cost 12); tokens signed HS256 with 24-h expiry; HTTPS only |
| Accessibility | Login form meets WCAG 2.1 AA; error messages not communicated by colour alone |
| Privacy | No PII logged; auth events contain only hashed user ID; 90-day log retention |
| Telemetry / event taxonomy | `auth.login.success`, `auth.login.failure`, `auth.recover.requested`, `auth.reset.completed` |
| i18n / l10n | N/A for v2 (en-only); string externalisation deferred |

## 9. RBAC & permissions matrix
| Role | Can do |
|---|---|
| Unauthenticated user | POST /v2/auth/login, POST /v2/auth/recover, POST /v2/auth/reset |
| Authenticated user | Access protected routes; cannot call /recover or /reset while logged in |
| Admin | No special auth endpoints; admin console uses separate SAML flow |

## 10. Dependencies
- **user_credentials table** — must be backfilled from `users.password_hash` before M1 ships.
- **Transactional email provider** (SendGrid) — existing contract; need template approval for reset email.
- **Rate-limit middleware** — already in the service; needs to be wired to the new endpoint.
- **DataDog** — existing APM; new dashboard to be created.

## 11. Risks & mitigations
| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Backfill of `user_credentials` misses some legacy rows | M | H | Dry-run backfill in staging; add reconciliation query in post-deploy runbook | @db-team |
| R2 | Rate limiting too aggressive for shared-IP corporate users | L | M | Monitor 429 rate; raise threshold or add IP-allowlist if needed | @sec-review |

## 12. Assumptions
| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | SendGrid can deliver transactional email within 60 s under normal load | Validated | Evaluate Postmark as fallback |
| A2 | All legacy users have a password hash in `users.password_hash` | Unvalidated | Extend backfill script to handle nulls; surface to user at first login |

## 13. Rollout plan

### Milestones
| ID | Name | Outcome | Exit criteria | Depends on |
|---|---|---|---|---|
| M1 | Login core | Users can log in with email + password | Login endpoint returns 200 + JWT session token on valid credentials; 401 on invalid; 11th login attempt within 60s from the same IP returns 429 with Retry-After header; failed-login telemetry emitted | — |
| M2 | Password recovery | Users can reset a forgotten password without contacting support | Recovery email delivered within 60s; reset link single-use and 15-min TTL; password-reset telemetry emitted | M1 |

### Rollout mechanics
- Flag plan: `auth_v2` LaunchDarkly flag
- Canary: 1% → 10% → 50% → 100% over 2 weeks
- Kill-switch: revert flag to 0%
- Abort thresholds: login error rate > 2% sustained 5 min
- Data migration: backfill user_credentials table from legacy `users.password_hash`
- Backward compatibility: legacy `/auth/login` route 301s to `/v2/auth/login` for 90 days

## 14. Cost & resource impact
| Component | Cost dimension | Estimate |
|---|---|---|
| Build cost | Engineering time | 3 engineers × 4 weeks |
| Run cost | Compute (no LLM) | < $50/month at current user volume |
| Counter-metric | Cost per login | Should not exceed $0.001 per request |

## 15. GTM & customer-comms
- Pricing / packaging implications: none — auth is not billable.
- In-app messaging plan: toast notification on first login via new endpoint ("We've upgraded your sign-in for better security").
- Release notes: changelog entry on general availability.
- CS / sales enablement: one-pager for CS explaining rate-limiting to handle "I got locked out" tickets.
- Beta / early-access plan: internal dogfood for 2 weeks, then canary rollout.

## 16. Support / CX impact
- Day-1 ticket owner: @cx-lead
- Runbook: `docs/runbooks/auth-v2.md` — covers 401 spikes, 429 spikes, backfill verification.
- Escalation path: CX → @eng-on-call → @anika.dev.
- Sales enablement: N/A.
- Training plan: CX team briefed via Loom before GA.

## 17. Open questions
| # | Question | Owner | Target resolution |
|---|---|---|---|
| OQ-1 | Should rate limiting be per-IP, per-account, or both? | @sec-review | 2026-05-20 |
| OQ-2 | Do we need account-lockout (vs. just rate-limiting)? | @eng-lead | 2026-05-20 |

## 18. Out of scope / Non-goals
- SSO / SAML integration — separate quarter.
- OAuth social login (Google, GitHub) — not in this cycle.
- Admin-initiated password reset — requires admin console work outside this scope.
- MFA / 2FA — follow-on PRD once v2 is stable.
