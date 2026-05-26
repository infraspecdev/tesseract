# Add SSO to Admin Console

## Header

| Field | Value |
|-------|-------|
| Owner | Priya Sharma, Senior PM, IAM Platform |
| Engineering Lead | Tomás Reyes, Staff Engineer, IAM |
| Tech Lead | Olusegun Adeyemi, Senior Engineer, Auth Services |
| Legal Review | Claire Fontaine, Associate Counsel (sign-off confirmed 2026-03-15) |
| Security Review | Wei Zhang, Staff Security Engineer (sign-off confirmed 2026-03-20) |
| Status | Approved |
| Last Updated | 2026-04-30 |
| Target Release | Q3 2026 (compliance deadline: 2026-09-01) |
| Document Version | 1.4 |

---

## Problem Statement

Currently, 23% of admin console users reuse passwords across three or more applications, based on a credential hygiene audit completed by the Security team in January 2026. The security team flagged 4 confirmed account-compromise incidents in the last 90 days directly attributable to credential reuse on admin accounts. In each case, an attacker obtained a password from a third-party breach and successfully replayed it against the admin console.

In addition to security exposure, IT Operations teams at three of our largest Enterprise customers (TerraHealth, Apex Logistics, Cascade Retail) have filed support tickets requesting SSO integration so they can enforce their corporate MFA policies. Combined ARR at risk if not delivered before Q3: ~$1.2M.

Industry-standard expectation: Enterprise SaaS admin consoles are expected to support SAML 2.0 or OIDC. Absence of SSO is a recurring blocker in 7 of our last 12 Enterprise sales cycles per Sales data from Q1 2026.

---

## Users and Personas

### P1 — Admin Owner (e.g., "Rachel Kim, VP Engineering, TerraHealth")

Rachel manages 40+ admin users across her org. She must enforce her company's SSO policy (Okta-backed SAML 2.0) for all SaaS tools. She has already excluded our product from her corporate SSO catalog because we lack SAML support, meaning her admins authenticate with personal email/password. She is the primary buyer persona for this feature.

**Current pain**: Can't enforce MFA policy for our product; security audit findings because of it; manually provisions and deprovisions our product users outside her IdP.

### P2 — IT Operations Lead (e.g., "Daniel Osei, IT Ops Lead, Cascade Retail")

Daniel handles user lifecycle management. He provisions and deprovisions SaaS users through their IdP (Azure AD). He wants just-in-time provisioning so he doesn't have to separately manage user accounts in our product.

**Current pain**: Two systems of record for users; deprovisioning lag creates security risk; no SCIM means manual offboarding.

### P3 — Security Engineer (e.g., "Sunita Rao, Security Eng, Apex Logistics")

Sunita is responsible for ensuring all corporate applications comply with their SSO-required security baseline. Our product is currently on a monthly exception list she maintains, a process that costs her ~1 hour/month and creates audit findings.

**Current pain**: Monthly exception paperwork; no visibility into admin authentication events via their SIEM.

---

## Goals and Non-Goals

### Goals

1. Allow Enterprise admin console users to authenticate via SAML 2.0 IdP (Okta, Azure AD, Google Workspace).
2. Reduce credential-reuse-related incidents to zero for SSO-enrolled orgs within 60 days of GA.
3. Unblock ≥5 Enterprise sales cycles stalled on SSO requirement by Q3 2026.
4. Reduce admin provisioning time for IT Ops from manual account creation to automatic JIT provisioning.

### Non-Goals

1. SCIM provisioning — out of scope for this release; prioritized for Q4 2026. Reason: SCIM requires a separate API surface and security review; including it would push Q3 deadline.
2. OIDC support — SAML 2.0 covers 90%+ of our target accounts; OIDC will follow in Q4 based on demand.
3. End-user (non-admin) SSO — this feature targets admin console only; end-user SSO is a separate epic.
4. Social login (Google/GitHub OAuth) — different threat model, different target persona, deferred.

**Scope-creep risk**: It is likely that customers will request SCIM during beta. If scoped in, it will push delivery past the compliance deadline. Explicit decision: do not scope in SCIM mid-flight without EPD review and deadline adjustment.

---

## Solution Overview

We will implement SAML 2.0 Service Provider (SP) support in the admin console, enabling IdP-initiated and SP-initiated SSO flows. The admin console acts as the SAML SP; customer IdPs (Okta, Azure AD, Google Workspace) act as SAML IdPs.

A new SSO Configuration page in the admin console allows the Org Owner to upload the IdP metadata XML, configure attribute mappings (email, name, role), and enable the `sso_login_enabled` feature flag per org. Once enabled, login attempts are redirected to the IdP flow. Existing email/password login is retained as fallback (configurable per org by Org Owner).

OIDC support is explicitly deferred to Q4 2026 (see Non-Goals).

---

## User Stories with Acceptance Criteria

### Story 1 — SP-Initiated SSO Login (Happy Path)

**As** Rachel (Admin Owner), **I want** to log in to the admin console via Okta SSO **so that** I am authenticated under my corporate identity without a separate password.

**Given** Rachel's org has SSO configured and `sso_login_enabled = true`,
**When** she navigates to the admin console login page and clicks "Sign in with SSO",
**Then** she is redirected to her IdP (Okta), authenticates there, and is returned to the admin console as an authenticated session with her org-level role.

**Given** the SSO session is established,
**When** Rachel's session token expires after the configured timeout (8 hours),
**Then** she is redirected to the IdP re-authentication flow, not the email/password form.

### Story 2 — IdP-Initiated SSO Login

**Given** Daniel's org uses Azure AD and has JIT provisioning enabled,
**When** Daniel clicks the admin console tile in his Azure AD app catalog,
**Then** he is redirected to the admin console with a valid SSO session, and if his account does not exist, it is created automatically with the `viewer` default role.

### Story 3 — IdP Timeout / Unreachable (Error Path)

**Given** Rachel's org has SSO enabled,
**When** she initiates SSO login and the IdP does not respond within 10 seconds,
**Then** the admin console displays an error: "Your identity provider is not responding. Contact your IT admin." with a support article link.

**And** the system logs the failure event `sso.login.idp_timeout` with org_id, timestamp, and elapsed time for debugging.

**And** if `sso_fallback_enabled = true` for the org, a "Sign in with email instead" fallback link is shown.

### Story 4 — Deprovisioned User Attempts Login (Error Path)

**Given** a user has been deprovisioned in the IdP but their admin console account still exists,
**When** they attempt SSO login,
**Then** the IdP denies the SAML assertion and the admin console displays: "Access denied by your identity provider."

**And** the admin console logs `sso.login.assertion_rejected` with the SP-provided name ID for audit purposes.

**And** the user's admin console session (if any) is invalidated.

### Story 5 — SSO Configuration (Admin Owner)

**Given** Rachel is an Org Owner in the admin console,
**When** she navigates to Settings → Security → SSO Configuration,
**Then** she sees fields for: IdP Metadata URL or XML upload, Attribute mappings (email, display name, role claim), SSO enabled toggle, Fallback enabled toggle.

**Given** she uploads a valid Okta metadata XML and saves,
**When** she clicks "Test SSO Configuration",
**Then** the system validates the SAML metadata (certificate present, ACS URL matches, entity ID valid) and shows a success indicator with the parsed IdP name.

**Given** the metadata XML is malformed or the certificate has expired,
**When** she saves the configuration,
**Then** validation fails with a specific error message identifying the problem field.

### Story 6 — Session Conflict (Edge Case)

**Given** a user has both an active email/password session and initiates an SSO login in another tab,
**When** the SSO flow completes,
**Then** the SSO session supersedes the email/password session; the email/password session token is invalidated.

**And** the user is shown a banner: "You are now signed in via SSO."

### Story 7 — Org Owner Disables SSO Mid-Flight (Edge Case)

**Given** SSO is enabled for an org and users have active SSO sessions,
**When** an Org Owner disables SSO (`sso_login_enabled = false`),
**Then** existing SSO sessions remain valid until natural expiry,
**And** new login attempts are routed to email/password,
**And** any users without a password set see a "Reset your password to continue" prompt on next login.

---

## State Transitions

Admin console authentication state machine (prose description for implementation reference):

1. **Unauthenticated** — user has no valid session cookie.
2. **SSO Redirect Pending** — SP-initiated: SAML AuthnRequest sent to IdP; 10-second timeout starts.
3. **IdP Authenticated** — IdP has returned a signed SAML assertion; assertion validation in progress on SP side.
4. **Assertion Valid** — SAML signature verified, not-before/not-after window respected, audience restriction matches our SP entity ID.
5. **Session Established** — session token issued; user logged in; `sso.login.success` event emitted.
6. **Session Expired** — session token TTL elapsed; user returned to step 1.

Error states:
- **IdP Timeout**: reached from step 2 after 10 seconds without response → `sso.login.idp_timeout`
- **Assertion Rejected**: reached from step 3 when IdP assertion is invalid or user deprovisioned → `sso.login.assertion_rejected`
- **Replay Attack Detected**: reached from step 4 when assertion ID has been used before (InResponseTo already seen in assertion cache) → `sso.login.replay_detected`
- **Signature Validation Failure**: reached from step 4 when SAML signature does not match registered IdP certificate → `sso.login.signature_invalid`

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | The system MUST support SAML 2.0 SP-initiated and IdP-initiated flows. |
| FR2 | SAML assertions MUST be validated: signature, certificate chain, not-before/not-after window, audience restriction. |
| FR3 | The system MUST detect and reject replayed assertions using an assertion ID cache (TTL: 5 minutes). |
| FR4 | SAML metadata (IdP cert, ACS URL, entity ID) MUST be configurable per org by Org Owner via admin console UI. |
| FR5 | The system MUST support JIT user provisioning on first SSO login with configurable default role (default: viewer). |
| FR6 | A feature flag `sso_login_enabled` MUST gate the SSO login path per org; disabling it MUST restore email/password flow. |
| FR7 | A feature flag `sso_fallback_enabled` MUST allow orgs to optionally retain email/password as fallback alongside SSO. |
| FR8 | All SSO login events (success, failure, timeout, assertion reject, replay) MUST be written to the audit log. |
| FR9 | The admin console MUST display a "Test SSO Configuration" flow that validates metadata without completing a full login. |
| FR10 | On SSO disable, users with no password MUST be prompted to set one before next login. |
| FR11 | Session tokens issued via SSO MUST carry a `auth_method: sso` claim for audit differentiation. |
| FR12 | The SAML SP metadata endpoint MUST be publicly accessible (for IdP-side configuration) at a stable URL. |

---

## Non-Functional Requirements

### Performance

- p95 SSO login latency (from ACS callback receipt to session token issued, excluding IdP round-trip): < 800ms.
- JIT provisioning MUST complete within the same 800ms budget.
- SAML assertion ID cache lookups: < 5ms p99 (Redis-backed).

### Security

**Threat model (key threats and mitigations):**

| Threat | Mitigation |
|--------|------------|
| Session hijack (stolen session token) | Short-lived tokens (8h); HTTPS-only; Secure + HttpOnly + SameSite=Strict cookie attributes. |
| Assertion replay | Assertion ID cache with 5-minute TTL; replay attempts logged and alerted. |
| IdP spoofing (unsigned/forged assertion) | SAML signature validation required; unsigned assertions rejected; certificate pinned per org. |
| Metadata tampering (attacker replaces IdP cert) | Only Org Owner can update SSO config; all config changes logged; cert change triggers re-test requirement. |
| Privilege escalation via role claim | Role attribute mapping validated against allowed-roles allowlist; unknown roles default to viewer with alert. |

**RBAC matrix:**

| Action | Unauthenticated | Viewer | Editor | Admin | Org Owner |
|--------|----------------|--------|--------|-------|-----------|
| Initiate SSO login | Yes | — | — | — | — |
| Configure SSO settings | No | No | No | No | Yes |
| View SSO audit log | No | No | No | Yes | Yes |
| Disable SSO | No | No | No | No | Yes |
| View SAML SP metadata | Yes | — | — | — | — |

### Accessibility

All new UI components (SSO login button, SSO configuration form, error messages) MUST meet WCAG 2.1 AA. Specifically:
- Error messages MUST be associated with form fields via `aria-describedby`.
- SSO status indicators MUST not rely on color alone.
- Focus management after SSO redirect return MUST place focus on the first interactive element.
- Tested against screen reader (VoiceOver on macOS, NVDA on Windows) before release.

### Privacy

No new PII is collected. Existing user identifiers (email, display name) are extended with an `sso_subject_claim` field mapped from the IdP's `NameID`. This field is treated as PII under our existing data classification policy (internal classification: "user identity data", retention: aligned to user record retention at 3 years post-account-deletion). No cross-org data sharing. GDPR/CCPA: data subject deletion request flow extended to clear `sso_subject_claim`.

### Telemetry Taxonomy

Events emitted:

| Event Name | Trigger | Key Properties |
|------------|---------|----------------|
| `sso.login.success` | Successful SSO session established | org_id, user_id, idp_type, latency_ms |
| `sso.login.failure` | Any SSO login failure | org_id, failure_reason, step_at_failure |
| `sso.login.idp_timeout` | IdP did not respond in 10s | org_id, elapsed_ms |
| `sso.login.assertion_rejected` | Assertion invalid or user deprovisioned | org_id, rejection_reason |
| `sso.login.replay_detected` | Assertion ID reuse detected | org_id, assertion_id_hash |
| `sso.config.updated` | Org Owner saves SSO config | org_id, actor_user_id, change_summary |
| `sso.config.tested` | Org Owner runs "Test SSO" | org_id, result (pass/fail) |
| `sso.provisioned_user` | JIT user created on first SSO login | org_id, assigned_role |

Dashboard plan: All SSO events feed into the existing observability dashboard (Datadog). A dedicated SSO Health panel will be created showing: daily SSO login success rate, IdP timeout rate, failure reason breakdown, p95 login latency by org_id. Reviewed weekly by EM during first 30 days post-GA.

### i18n

SSO login button text, error messages, and configuration UI labels will be added to the existing i18n translation pipeline (React-i18next). Initial supported locales: en, fr, de, es, ja (matching existing admin console locale coverage). No new locale infrastructure required.

---

## Rollout Plan

### Feature Flags

- `sso_login_enabled` (per-org boolean): gates the SSO login path. Default off. Set to true per org by Ops when org is onboarded.
- `sso_fallback_enabled` (per-org boolean): retains email/password alongside SSO. Default true. Org Owner can set to false to enforce SSO-only.

### Canary Rollout

| Phase | Scope | Duration | Monitoring |
|-------|-------|----------|------------|
| Internal beta | Infraspec internal org only | Days 1–7 | Manual review; daily check-in with Priya + Tomás |
| Canary | 5% of Enterprise orgs (opt-in whitelist) | Days 8–14 | Automated: error rate, timeout rate, latency |
| Expanded canary | 25% of Enterprise orgs | Days 15–21 | Same automated monitors; support ticket review |
| GA | 100% of Enterprise orgs | Day 22+ | Standard production monitoring |

### Kill-Switch Criteria

Rollback the `sso_login_enabled` flag (disable globally or per affected org) if ANY of the following conditions are met and sustained:

- SSO login failure rate > 0.5% of login attempts for 10 consecutive minutes (measured over 5-minute rolling window).
- p95 SSO login latency (ACS callback to session issued) > 2 seconds for 5 consecutive minutes.
- Assertion replay detection rate > 0% sustained over 5 minutes (indicates active attack or cache failure).
- More than 3 Severity-1 tickets related to SSO in any 24-hour window during rollout.

Owner for kill-switch decision: Tomás Reyes (EM on-call) or Olusegun Adeyemi (TL on-call). Kill-switch can be executed without PM approval if conditions are met.

### Abort Thresholds

If canary phase (5% or 25%) triggers kill-switch criteria, rollout is halted. Retrospective required before resuming. If abort occurs during GA rollout, email/password fallback (`sso_fallback_enabled`) is force-enabled for all affected orgs while investigation proceeds.

### Data Migration

No destructive migration. New columns (`sso_subject_claim`, `sso_configured_at`) added to `users` and `orgs` tables respectively via backward-compatible migrations (nullable, default null). No backfill required. Existing user records unaffected until they first log in via SSO (at which point `sso_subject_claim` is populated from IdP NameID).

### Backward Compatibility

Email/password login is preserved unless the Org Owner explicitly sets `sso_fallback_enabled = false`. Users with no active SSO configuration see no change. All existing API tokens and session tokens issued before SSO enablement remain valid until their natural expiry.

---

## RACI

| Responsibility | Who |
|----------------|-----|
| PM / Feature Owner | Priya Sharma (priya.sharma@company.com) |
| Engineering Lead | Tomás Reyes |
| Tech Lead / Architecture | Olusegun Adeyemi |
| Security Review & Sign-off | Wei Zhang (confirmed 2026-03-20) |
| Legal / Privacy Sign-off | Claire Fontaine (confirmed 2026-03-15) |
| Design | Aarav Mehta |
| Support Readiness | Jess Thornton, Head of Support Engineering |
| Sales Enablement | Carlos Vega, Solutions Engineering |
| Decision Maker | Priya Sharma (feature scope); CTO sign-off required for GA |
| Status Updates | Weekly in IAM Platform review (Mondays 10am PT) |

---

## Legal and Privacy

**Data classification**: IdP subject claims (`sso_subject_claim`) are classified as "user identity data" — internal classification level 2 (PII). Governed by existing user data retention policy (3 years post-account-deletion). No new data categories introduced.

**PII handling**: No new PII collected beyond what is already stored in `users` table. IdP `NameID` mapped to existing email identifier. Display name sourced from IdP attribute if provided; falls back to existing stored name.

**Regulated industry**: Not applicable for this release (admin console is not HIPAA or PCI-scoped). Confirmed by Claire Fontaine (Legal) on 2026-03-15.

**GDPR/CCPA compliance**: Data subject deletion request (right to erasure) flow extended to clear `sso_subject_claim`. No data exported to new third-party processors — IdP communication is direct SAML over HTTPS with customer-controlled IdP.

**Data retention**: SSO audit log events retained for 12 months (aligned to existing audit log retention policy), then archived to cold storage for 5 additional years per compliance requirement confirmed with Legal.

---

## Go-To-Market

**Pricing**: SSO is an Enterprise tier feature. No price change for existing Enterprise customers. Included in Enterprise tier as of Q3 2026 release. Growth tier: SSO will not be available in this release cycle (GTM decision: limiting to Enterprise reduces support surface and allows controlled onboarding).

**Release notes**: Draft release notes prepared by Priya; review by Marketing by 2026-07-15. Key message: "Enterprise-grade SSO now available for admin console — configure SAML 2.0 with Okta, Azure AD, or Google Workspace in minutes."

**In-app messaging**: Banner in admin console for Org Owners of Enterprise orgs at GA launch: "New: Set up SSO for your organization." Links to setup guide. Dismissible; shown for 14 days post-GA.

**CS enablement**: CS runbook published in CS wiki (link: `[internal wiki]/cs/sso-setup-guide`) covering: how to identify customers who should onboard, common IdP configuration issues (Okta vs Azure AD differences), escalation path (TL on-call).

**Beta plan**: 3 design-partner customers (TerraHealth, Apex Logistics, Cascade Retail) enrolled in internal beta (Days 1–7). Dedicated Slack channel `#sso-beta-partners` with EM and PM monitoring. Beta feedback incorporated before expanded canary.

**Sales enablement**: One-pager ("SSO in Admin Console — Frequently Asked Questions") prepared by Carlos Vega and reviewed by Priya by 2026-07-01. Delivered to Sales in pre-GA enablement session.

---

## Support and CX

**Day-1 ticket owner**: Support Engineering queue `support-iam` (monitored by Jess Thornton's team). Triage SLA: P1 within 1 hour, P2 within 4 hours.

**Escalation path**: Jess Thornton (Support Lead) → Olusegun Adeyemi (TL on-call) for technical escalations. Tomás Reyes for engineering-level escalation.

**Runbook**: `[internal wiki]/runbooks/sso-admin-console` covers: how to diagnose IdP timeout failures, how to force-disable SSO for an org, how to reset a user stuck in SSO-only mode with no password, how to check assertion ID cache health.

**Talking points for sales**: Included in sales one-pager (Carlos Vega; see GTM section). Covers: supported IdPs, JIT provisioning behavior, fallback options, timeline for SCIM (Q4 2026).

**Customer-facing documentation**: Setup guide in help center covering Okta, Azure AD, and Google Workspace configuration steps. Published by 2026-07-20. Reviewed by Design Partner contacts before GA.

---

## Why Now and Cost of Inaction

**Why now**: Enterprise compliance deadline — our three largest design-partner customers have SSO requirements in their vendor assessment due by 2026-09-01. Missing this date risks $1.2M ARR in combined renewals and $850K in in-flight expansions per Sales data as of 2026-04-01.

**Cost of inaction**:
- Continued audit findings for TerraHealth, Apex Logistics, Cascade Retail (~$0.3M in penalty risk at TerraHealth per their contract SLA).
- SSO remains a blocking criterion in approximately 7 active Enterprise sales cycles (Sales Q1 2026 data), estimated $2.1M TCV.
- Security team incurs ~4 eng-days/quarter managing credential-reuse incident response; continuing this costs ~$60K/year in eng time.
- Each quarter of delay pushes OIDC (Q4 goal) further out, compounding demand.

---

## Risks and Assumptions

| Risk / Assumption | Likelihood | Impact | Mitigation | Owner |
|-------------------|------------|--------|------------|-------|
| IdP outage causes admin console login failure for SSO-only orgs | Medium | High | `sso_fallback_enabled` toggle allows Org Owner to retain email/password. TL on-call can force-enable fallback within 5 minutes. | Olusegun Adeyemi |
| IdP configuration errors (wrong ACS URL, cert mismatch) generate high support volume | High | Medium | "Test SSO Configuration" flow in admin UI catches most errors before go-live. CS runbook covers common mistakes. | Jess Thornton |
| SAML library (python3-saml) has undisclosed vulnerability | Low | High | Library pinned to current audited version; Security team runs automated CVE scans weekly; upgrade path confirmed in threat model. | Wei Zhang |
| Customers request SCIM during beta (scope creep) | High | Medium | Explicit non-goal in this PRD. Committed Q4 2026. If pressure is extreme, EPD review required before any scope change. Decision authority: Priya Sharma. | Priya Sharma |
| JIT provisioning assigns wrong default role if IdP sends unexpected attribute | Medium | Medium | Role mapping validated against allowlist; unknown values default to `viewer` with alert email to Org Owner and audit log entry. | Olusegun Adeyemi |
| Assumption: >80% of target Enterprise orgs use Okta or Azure AD | Assumed validated | Low | Sales confirmed Okta: 62%, Azure AD: 24%, Google Workspace: 8%, Other: 6% based on Q1 2026 survey of 47 Enterprise accounts. |  |

---

## Cost and Resource Impact

**Build cost**:
- Engineering: 6 eng-weeks total (Olusegun 3 weeks, 2 additional engineers 1.5 weeks each).
- Design: 1 designer, 1.5 weeks.
- PM/EM overhead: ~0.5 weeks.
- Total estimated: ~$85K all-in at blended rate.

**Run cost** (incremental):
- Redis assertion ID cache: ~$30/month at projected 10K logins/day (p50 cache entry size: 128 bytes, TTL 5 minutes).
- No new compute required — SSO validation added to existing auth service pods; CPU impact < 5% projected.
- Audit log storage: ~$5/month incremental at projected SSO event volume.
- Estimated incremental run cost: **~$35/month** at GA scale.

**Cost counter-metric**: Cost per SSO login event (total incremental run cost / SSO login count per month). Tracked in monthly infra cost review. Alert if cost per login event exceeds $0.001 (would indicate cache inefficiency or unexpectedly high retry storms).

**Design alternatives considered**:
1. Third-party auth provider (Auth0, Okta CIC): rejected — would require migrating existing session infrastructure ($200K+ migration cost, 3-quarter timeline); run cost ~$2,500/month at scale vs. $35/month.
2. OIDC-first instead of SAML-first: rejected — SAML covers 86% of target orgs today vs. OIDC 40%; both would be needed eventually; SAML first by demand.
3. Delay until Q4 2026: rejected — compliance deadline forces Q3; cost of inaction ~$1.2M ARR at risk.

---

<!--
Expected review outcomes for this fixture are captured empirically in
shield/evals/baselines/prd-review-pm-postchange.json (per-dim finding counts) and in
shield/evals/expected/*.yaml (per-dim grade + severity assertions). Do not restate them
inline here — they will drift.
-->
