# Story Coverage — Archetypes Library

Common flow patterns per feature domain. Used by `story-coverage` skill Rule 2 to identify archetypal flows missing from a PRD.

Each archetype: name, description, severity if missing, typical persona, typical state transitions.

## Domain: auth

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| signup | New user creates account | P0 | None → Unverified → Verified |
| login | Returning user authenticates | P0 | Logged out → Logging in → Logged in |
| logout | User ends session | P1 | Logged in → Logged out |
| password-reset | User recovers forgotten password | P1 | None → Reset requested → Reset link clicked → New password set |
| email-change | User updates email | P2 | Email confirmed → Email change requested → Email reconfirmed |
| mfa-enrollment | User adds MFA | P2 | MFA off → MFA setup pending → MFA on |
| account-deletion | User deletes account (GDPR / compliance) | P0 | Active → Deletion requested → Soft-deleted → Hard-deleted |
| account-recovery | Recover deleted/disabled account | P2 | Disabled → Recovery requested → Active |

## Domain: payment

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| charge-happy | Customer pays successfully | P0 | Created → Authorized → Captured → Settled |
| charge-decline | Card declined | P0 | Created → Authorized failed |
| charge-partial-success | Some line items succeed, others fail | P1 | Created → Partial settlement |
| refund-full | Customer requests full refund | P1 | Settled → Refund requested → Refunded |
| refund-partial | Customer refunded for some line items | P2 | Settled → Partial refund |
| dispute / chargeback | Bank-initiated dispute | P1 | Settled → Disputed → Won / Lost |
| recurring-renewal | Subscription auto-renews | P1 (if recurring) | Active → Renewal attempting → Active OR Past due |
| recurring-failure | Renewal fails | P1 (if recurring) | Active → Renewal failed → Past due → Cancelled |

## Domain: content

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| create | User creates content | P0 | None → Draft → Published |
| read / view | User views content | P0 (depends — implied if create exists) | — |
| update / edit | User edits existing | P1 | Published → Draft → Published (v2) |
| delete | User deletes | P1 | Published → Deleted (soft) → Hard-deleted |
| share | User shares with others | P2 | Published → Shared (with permission set) |
| search | User finds content | P2 | — |
| archive / unarchive | User archives | P2 | Published → Archived → Published |

## Domain: lifecycle (user account / subscription / feature flag rollout)

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| activation | Newly created → fully active | P1 | Pending → Activating → Active |
| dormancy | User stops engaging | P2 | Active → Dormant |
| churn | User cancels | P1 | Active → Cancelling → Cancelled |
| win-back | Re-engage churned user | P2 | Cancelled → Win-back offered → Active |

## Domain: multi-region / residency

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| region-pinned-write | User write goes to pinned region | P0 (if regulatory) | — |
| cross-region-read | User reads from non-home region | P1 | — |
| residency-conflict | User crosses borders | P1 | — |
| data-purge | Compliance-driven data deletion | P0 (if regulatory) | Resident → Purge scheduled → Purged |

## Domain: billing (separate from payment — invoice + revenue ops)

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| invoice-issued | Customer is billed | P0 | None → Issued |
| invoice-paid | Customer pays invoice | P0 | Issued → Paid |
| invoice-overdue | Customer misses payment | P1 | Issued → Overdue → (Past due actions) |
| credit-issued | Customer receives credit | P2 | None → Credited |

## Domain: observability / ops (internal tooling features)

| Archetype | Description | If missing | Typical state transitions |
|---|---|---|---|
| metric-emitted | Feature emits a measured event | P1 | — |
| alert-fired | Threshold breached | P1 | OK → Alerting → Acknowledged → Resolved |
| runbook-followed | On-call resolves alert | P2 | Alerting → Investigating → Resolved |
| capacity-scaling | System scales under load | P2 | At capacity → Scaling up → Scaled |

## Domain: internal-tool

No archetypal flows — internal tools have feature-specific flows. Rule 2 returns empty for this domain. Rule 1 (persona-goal cross-product) and Rule 3 (orphan-reference) still apply.

## How to extend

To add a new domain or archetype:
1. Add the domain section above with archetype rows
2. Update the `feature_domain` inference list in `SKILL.md` if a new keyword should map
3. No code changes needed — this is reference data
