# Team-Shared Dashboards for Analytics Product

## Header

| Field | Value |
|-------|-------|
| Owner | Marcus Chen, Senior PM, Analytics Platform |
| Engineering Lead | Fatima Al-Rashid |
| Status | In Review |
| Last Updated | 2026-04-28 |
| Target Release | Q3 2026 |

---

## Solution Overview

> **Note**: Anti-pattern intentional — solution appears before problem statement.

We will build a Team Dashboards feature that allows users to create, share, and collaboratively view analytics dashboards within their organization. The feature will use an intuitive UX with a simple flow for sharing — users select a dashboard, choose recipients from their org directory, and set permissions (view or edit). The backend will rely on a performant, scalable permission-check layer that evaluates access at render time.

Key solution components:
- A shared dashboard library accessible from the left nav
- A "Share Dashboard" modal with org-directory search
- Role-based permissions: Viewer and Editor
- A notification email when a dashboard is shared with a user
- Audit log for share/unshare events (Security requirement)

Technology choices:
- Extend existing `dashboards` DB table with an `owner_team_id` and a new `dashboard_shares` junction table
- Use existing org-directory API for member lookup
- Extend existing ACL middleware to enforce dashboard-level permissions

---

## Problem Statement

Analytics users want to share insights with teammates without resorting to exporting CSVs and attaching them to Slack messages. Currently, dashboards are personal and non-transferable. Teams working on shared KPIs (e.g., Growth, Customer Success) need a way to maintain a canonical dashboard that all stakeholders can view.

> **Gap**: No baseline data is provided here — no current ticket volume, no user research quotes, no churn signal. Reviewers should flag this as dim 1 weakness.

---

## Users and Personas

### Persona 1 — Anya Patel, Head of Growth

Anya manages a 12-person growth team. She builds weekly acquisition dashboards in the analytics product and screenshots them to share in Slack. She loses 30–45 minutes a week on this manual step and her screenshots go stale within hours. She wants a single source of truth her team can bookmark.

### Persona 2 — James Okafor, Customer Success Manager

James tracks NPS, CSAT, and retention metrics. He currently receives CSVs from the analytics team by email every Monday. He has no real-time visibility and can't drill down on anomalies. He wants view-only access to dashboards his colleagues own.

### Persona 3 — Devops Admin

Internal admin who manages user provisioning. Has no direct interest in dashboard content but must ensure that sharing respects org boundaries (no cross-org leakage).

---

## Goals and Non-Goals

### Goals

1. Enable users to share dashboards with individual teammates or entire teams within their org.
2. Reduce time spent on manual dashboard-screenshotting and CSV export workflows.
3. Maintain data access controls — shared dashboards respect the recipient's data permissions.

### Non-Goals

> **Gap**: No explicit Out of Scope section exists. This is a planted gap for dim 2. The section below is labeled "Non-Goals" which does not substitute for a formal Out of Scope section with rationale and scope-creep risk callouts.

- Cross-organization sharing (different tenant accounts)
- Public/anonymous sharing (no public links in v1)

---

## Success Metrics

> **Gap**: Single metric, no counter-metric. Planted gap for dim 3.

**Primary metric**: % of active dashboards that are shared with at least one other user, target ≥ 30% within 90 days of GA.

There is no counter-metric defined. No leading indicator (e.g., share button clicks, share modal opens) and no lagging indicator (e.g., 30-day retention of shared dashboard viewers) are specified. No dashboard plan or monitoring cadence described.

---

## User Stories

> **Gap**: ACs are written as prose paragraphs, not Given/When/Then. Only happy paths documented. Planted gaps for dim 4.

### Story 1 — Share a Dashboard

As Anya (Head of Growth), I want to share a dashboard with my team so that everyone sees the same real-time data instead of stale screenshots.

**Acceptance Criteria**: When Anya opens a dashboard she owns, she should see a Share button in the top-right corner. Clicking it opens a modal where she can search for users or teams. After selecting recipients and setting permissions (Viewer or Editor), she clicks Share and the recipients receive an email notification. The dashboard then appears in their Shared Dashboards library. The experience should feel simple and intuitive.

### Story 2 — View a Shared Dashboard

As James (Customer Success Manager), I want to view a dashboard shared with me so that I can monitor NPS and CSAT without requesting CSV exports.

**Acceptance Criteria**: James logs in and navigates to the Shared Dashboards section in the left nav. He can see all dashboards shared with him. Clicking a dashboard renders it with his data permissions applied (he only sees data his role allows). The dashboard loads quickly and feels performant.

### Story 3 — Manage Sharing Permissions

As Anya, I want to change a teammate's permission from Editor back to Viewer so that I can control who can modify my dashboard.

**Acceptance Criteria**: Anya opens the Share modal on a dashboard she owns. She sees a list of current shares with their permission levels. She can change any share's permission from a dropdown. The change takes effect immediately and the affected user sees updated permissions on their next page load. This should be an intuitive UX.

### Story 4 — Unshare a Dashboard

As Anya, I want to revoke access to a dashboard I previously shared so that former team members lose access after they leave my team.

**Acceptance Criteria**: Anya opens the Share modal, finds the user she wants to remove, and clicks Remove. The user loses access immediately. The dashboard disappears from their Shared Dashboards library on next page refresh.

> **Gap**: No error stories. No timeout/network failure scenarios. No scenario where sharing fails (e.g., recipient not found, permission denied). No abandon/cancel-mid-flow story. No edge case for sharing with a deactivated user. All 4 stories are pure happy paths.

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | A "Share" button MUST appear on dashboards owned by the current user. |
| FR2 | The Share modal MUST support searching by name or email within the user's org. |
| FR3 | Sharing MUST support two permission levels: Viewer and Editor. |
| FR4 | Shared dashboards MUST appear in a "Shared with Me" section of the dashboard library. |
| FR5 | The system MUST send an email notification to recipients when a dashboard is shared. |
| FR6 | Data access rules MUST be applied at render time based on the viewer's role, not the owner's. |
| FR7 | The dashboard owner MUST be able to modify or revoke any share at any time. |
| FR8 | All share/unshare events MUST be logged to the audit log with actor, target, timestamp. |
| FR9 | Shared dashboards MUST reflect the latest data (no stale snapshots). |
| FR10 | An org admin MUST be able to view all sharing activity within their org from the admin panel. |

---

## Non-Functional Requirements

### Performance
- Dashboard render time for shared dashboards: no specific budget defined (placeholder: "should feel performant").
- API response time for share modal search: should be scalable to org sizes up to 10,000 users.

### Security
- All permission checks enforced server-side.
- No cross-org data leakage.
- Audit log entries non-repudiable.

> **Gap**: No threat model. No RBAC matrix. No specific latency budget (p95, p99). Accessibility (WCAG), privacy impact, telemetry taxonomy, and i18n requirements absent.

### Observability
- Emit events for: `dashboard.shared`, `dashboard.unshared`, `dashboard.viewed` (shared context).

---

## Rollout Plan

### Phase 1 — Internal Beta (Week 1–2)
Deploy to internal employees only behind feature flag `team_dashboards_enabled`. Gather feedback via survey.

### Phase 2 — Limited GA (Week 3–5)
Enable for 10% of Enterprise tier accounts. Monitor error rates and support tickets.

### Phase 3 — Full GA (Week 6+)
Roll out to all Enterprise accounts.

> **Gap**: No kill-switch criteria defined. No abort thresholds. No data migration plan for existing dashboards. No backward compatibility commitments stated. "We'll monitor and decide" is the implied strategy. Planted gap for dim 6.

---

## Risks and Assumptions

| Risk / Assumption | Status |
|-------------------|--------|
| Org-directory API may be slow under load from share-modal search | Unvalidated |
| Email notification deliverability could be blocked by corporate spam filters | Unvalidated |
| Users may share sensitive financial dashboards with unauthorized viewers | Unvalidated |
| PM assumes 30% share adoption is achievable within 90 days | Unvalidated assumption |
| Data permission enforcement at render time adds latency | Unvalidated |

> **Gap**: No mitigations listed for any risk. Planted gap for dim 12.

---

## RACI

| Role | Person |
|------|--------|
| PM / Owner | Marcus Chen |
| Engineering Lead | Fatima Al-Rashid |
| Design | TBD |
| Legal / Privacy | TBD |
| Security Review | TBD |
| Sign-off | TBD |

---

<!--
Expected review outcomes for this fixture are captured empirically in
shield/evals/baselines/prd-review-pm-postchange.json (per-dim finding counts) and in
shield/evals/expected/*.yaml (per-dim grade + severity assertions). Do not restate them
inline here — they will drift. Gap annotations on individual sections above are
authoring intent, kept for human readers; the merge gate ignores them.
-->
