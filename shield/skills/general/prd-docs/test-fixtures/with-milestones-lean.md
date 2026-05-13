# User Authentication v2 (Lean)

## 1. Header
| Field | Value |
|---|---|
| Owner | @anika.dev |
| Status | Draft |
| PRD type | Lean |
| Date created | 2026-05-13 |
| Last updated | 2026-05-13 |
| Linked design spec | null |
| Linked research | null |
| Decision-maker | @eng-lead |
| Sign-off contacts | Security: @sec-review |
| Linked plans | _(auto-populated by /plan)_ |

## 2. Problem & context
The legacy `/auth/login` endpoint has no rate limiting and no self-serve password reset. This has caused 3 credential-stuffing incidents in 90 days and ~200 support tickets/week from locked-out users.

## 3. Target users / personas
| ID | Persona | Goals | Frictions today |
|---|---|---|---|
| P1 | Anika — security-conscious user | Sign in quickly; recover access without support | Session drops; no self-serve reset |

## 4. Goals & non-goals
### Goals
1. Replace the legacy login endpoint with a rate-limited v2 endpoint.
2. Provide a self-serve email-based password-reset flow.

### Non-goals
- SSO / SAML, OAuth social login, MFA — separate workstreams.

## 5. Success metrics
| Metric | Type | Target | Counter |
|---|---|---|---|
| "Locked out" support tickets | Lagging | < 50/week within 4 weeks of GA | — |
| Login success rate | Leading | ≥ 98% of valid-credential attempts | Login error rate |

## 6. Milestones
| ID | Name | Outcome | Exit criteria | Depends on |
|---|---|---|---|---|
| M1 | Login core | Users can log in with email + password | Login endpoint returns 200 + JWT session token on valid credentials; 401 on invalid; 11th login attempt within 60s from the same IP returns 429 with Retry-After header; failed-login telemetry emitted | — |
| M2 | Password recovery | Users can reset a forgotten password without contacting support | Recovery email delivered within 60s; reset link single-use and 15-min TTL; password-reset telemetry emitted | M1 |

## 7. Open questions
| # | Question | Owner | Target resolution |
|---|---|---|---|
| OQ-1 | Rate limiting per-IP, per-account, or both? | @sec-review | 2026-05-20 |

## 8. Out of scope / Non-goals
- SSO / SAML integration.
- OAuth social login.
- MFA / 2FA.

---

> **This is a lean PRD.** It intentionally omits the following standard sections:
> - Section 6 — User stories & scenarios
> - Section 7 — Functional requirements
> - Section 8 — Non-functional requirements
> - Section 9 — RBAC & permissions matrix
> - Section 10 — Dependencies
> - Section 11 — Risks & mitigations
> - Section 12 — Assumptions
> - Section 13 — Rollout plan (rollout mechanics; lean keeps only the Milestones half)
> - Section 14 — Cost & resource impact
> - Section 15 — GTM & customer-comms
> - Section 16 — Support / CX impact
>
> If scope grows or stakeholders need more detail, run `/prd` again — Shield
> will offer to add specific sections or upgrade to `standard`.
