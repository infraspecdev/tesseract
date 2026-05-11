# Add Cron Job to Purge Expired Session Tokens

## Header

| Field | Value |
|-------|-------|
| Owner | Diego Martinez, Senior Platform Engineer |
| Engineering Lead | Diego Martinez |
| Status | Approved |
| Last Updated | 2026-04-25 |
| Target Release | Q2 2026 |

---

## Problem Statement

Expired session tokens are currently retained indefinitely in the `sessions` table. As of 2026-04-01, the table contains approximately 14 million rows, of which a spot-audit confirmed 91% have an `expires_at` timestamp in the past. The table has grown by ~800K rows per month over the last 6 months.

Observed impact:
- Weekly maintenance query (`VACUUM ANALYZE sessions`) has degraded from a p95 of 4 minutes (baseline, 2025-09-01) to 17 minutes today — a 30% degradation after accounting for index growth.
- The `GET /session/:id` lookup query p95 has risen from 12ms (baseline) to 31ms over the same period due to index bloat.
- Backup window now 22% longer than provisioned; at current growth rate will breach backup SLA in ~8 weeks.

No user-facing data is affected. The `sessions` table stores server-side opaque token hashes and expiry timestamps only — no PII, no user content.

---

## Users

This is an internal-only feature. There are no external user personas.

### Internal Persona 1 — Platform Engineering Team

Owns the sessions infrastructure. Diego Martinez leads this area. Currently performs ad hoc `DELETE` queries during off-hours when bloat becomes critical. Manual intervention is unsustainable as growth continues.

### Internal Persona 2 — Database Operations (DB Ops)

Monitors table sizes and maintenance windows. DB Ops team (lead: Layla Hassan) flagged the backup window breach risk. They will verify the post-purge table size and maintenance window restoration.

### Internal Persona 3 — Security Engineering

Responsible for verifying that expired tokens are removed in a timely manner (part of credential hygiene controls). Security Eng (Wei Zhang) confirmed that indefinite retention of expired tokens is a finding in the internal security review ("Finding #SRF-2026-11").

---

## Goals

1. Reduce the `sessions` table to fewer than 2 million rows (active + recent) within 30 days of deploying the initial purge run.
2. Restore weekly `VACUUM ANALYZE sessions` p95 runtime to baseline (<5 minutes) within 30 days.
3. Restore `GET /session/:id` lookup p95 latency to baseline (<15ms) within 30 days.
4. Maintain table size below 3 million rows on an ongoing basis via weekly automated purge.

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| `sessions` table row count | ~14M | <2M (after initial purge) | Direct SQL: `SELECT COUNT(*) FROM sessions` |
| Ongoing table row count | — | <3M sustained | Checked weekly after cron run |
| `VACUUM ANALYZE` p95 runtime | 17 min | <5 min | DB Ops monitoring dashboard |
| `GET /session/:id` p95 latency | 31ms | <15ms | APM dashboard (Datadog) |
| Purge job completion time | N/A | <30 min per run | CloudWatch metrics on Lambda |
| Purge failure rate | N/A | 0% undetected failures | Alert on job failure + CloudWatch alarm |

---

## User Stories with Acceptance Criteria

### Story 1 — Platform Engineer Triggers Initial Purge (Manual)

**As** Diego (Platform Engineer), **I want** to run a one-time initial purge of all expired sessions **so that** the table is brought to a manageable size before handing off to the automated cron.

**Given** the purge job is deployed with `DRY_RUN=true`,
**When** Diego triggers it manually via the ops script `scripts/purge-sessions.sh --dry-run`,
**Then** the job logs the count of rows that would be deleted and exits without modifying any data.

**Given** Diego reviews dry-run output and approves the run,
**When** he triggers `scripts/purge-sessions.sh` (no dry-run flag) with `BATCH_SIZE=50000`,
**Then** the job deletes rows in batches of 50,000 where `expires_at < NOW() - INTERVAL '1 day'` (1-day grace period), sleeping 500ms between batches to avoid lock contention.

**Given** the job runs for >30 minutes or encounters a database error,
**When** the failure threshold is reached,
**Then** the job stops, logs the failure reason and last successfully deleted batch ID, and sends a PagerDuty alert to the platform-eng on-call.

### Story 2 — Weekly Cron Handles Ongoing Purge

**As** the Platform Engineering team, **I want** a cron job that runs weekly to purge newly-expired sessions **so that** the table stays below the 3M-row target without manual intervention.

**Given** the cron job is scheduled (every Sunday at 02:00 UTC behind a feature flag),
**When** the job runs,
**Then** it deletes all rows where `expires_at < NOW() - INTERVAL '1 day'` in batches of 10,000 with 200ms inter-batch sleep.

**Given** the cron job completes successfully,
**When** the run finishes,
**Then** it emits a CloudWatch metric `sessions.purge.rows_deleted` with the count, `sessions.purge.duration_ms`, and `sessions.purge.post_run_table_count`.

**Given** the post-run table count exceeds 3 million rows,
**When** the metric is emitted,
**Then** a CloudWatch alarm triggers a Slack notification to `#platform-eng-alerts`.

### Story 3 — On-Call Gets Paged on Purge Failure

**Given** the cron job encounters a fatal error (database unavailable, IAM permission denied, unhandled exception),
**When** the job exits with a non-zero status code,
**Then** the CloudWatch alarm `sessions-purge-job-failed` fires and creates a PagerDuty incident assigned to the platform-eng on-call rotation.

**And** the failure log (error type, last batch ID, elapsed time) is written to CloudWatch Logs group `/platform/sessions-purge`.

---

## Non-Functional Requirements

### Performance

- Batch size MUST be configurable (default: 10,000 rows per batch for cron; up to 50,000 for initial one-time run).
- Inter-batch sleep MUST be configurable (default: 200ms for cron; 500ms for initial run) to avoid saturating the DB write path.
- The cron job MUST not hold a single DELETE transaction open for more than 10 seconds; batch commit after each batch.
- Total cron run time target: <30 minutes per weekly run at steady-state (<3M rows purged per run).

### Security

- The purge job MUST run under the `platform-eng-purge` IAM role (AWS), which has ONLY `rds:ExecuteStatement` on the `sessions` table with a `WHERE expires_at < NOW()` condition enforced by an IAM condition key.
- No other IAM permissions granted. The role MUST NOT have read access to `users`, `dashboards`, or any other table.
- Dry-run mode MUST be gated by the same IAM role (no elevated privileges needed for dry-run).

### Observability

Custom CloudWatch metrics emitted per run:

| Metric | Description |
|--------|-------------|
| `sessions.purge.rows_deleted` | Total rows deleted in this run |
| `sessions.purge.duration_ms` | Total wall-clock time of the job |
| `sessions.purge.post_run_table_count` | Table row count after purge (sampled via `SELECT COUNT(*)`) |
| `sessions.purge.batch_count` | Number of batches executed |
| `sessions.purge.error` | 1 if job exited with error, 0 otherwise |

CloudWatch Alarms:
- `sessions-purge-job-failed`: triggers if `sessions.purge.error = 1`; PagerDuty P2.
- `sessions-post-purge-count-high`: triggers if `sessions.purge.post_run_table_count > 3000000`; Slack notification.

---

## Legal / Privacy

**N/A** — no user-facing data. The `sessions` table contains only opaque token hashes and server-side expiry timestamps. No PII, no user content, no regulated data. Legal and privacy review not required; confirmed with Wei Zhang (Security Eng) and Diego Martinez (Platform Eng) on 2026-04-20.

---

## GTM

**N/A** — internal-only infrastructure change. No customer-facing behavior modified. No release notes, CS enablement, or external communications required.

---

## Support / CX

**N/A** — no external surface. On-call runbook added to `[internal wiki]/runbooks/sessions-purge-job` covering: how to check job status, how to manually trigger a run, how to abort a running job safely, how to interpret the post-run CloudWatch metrics. On-call escalation: platform-eng PagerDuty rotation.

---

## Rollout Plan

### Feature Flag

`sessions_purge_cron_enabled` (boolean, default: false): gates the weekly cron schedule. The initial manual purge is run independently of this flag (manual trigger by Diego).

### Staging Dry-Run

1. Deploy job to staging with `DRY_RUN=true`.
2. Verify dry-run logs show expected row count (~14M in staging replica).
3. Run with `DRY_RUN=false` in staging; verify staging table count drops to <500K rows and staging DB performance metrics improve.
4. Verify CloudWatch metrics emit correctly.

### Production Rollout

1. Run initial manual purge in production (off-peak: Sunday 01:00 UTC). Dry-run first, then live with `BATCH_SIZE=50000`.
2. Verify table count <2M after initial run. Verify `VACUUM ANALYZE` and query latency metrics recover.
3. Enable `sessions_purge_cron_enabled = true` to activate weekly cron.
4. Monitor for 4 weeks; review CloudWatch alarms and metrics in weekly DB Ops sync.

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Initial purge causes lock contention, slowing production traffic | Medium | High | Run during off-peak (01:00 UTC Sunday); batch size 50K with 500ms sleep; monitor `pg_locks` and abort if contention detected. | Diego Martinez |
| Job deletes non-expired tokens due to clock skew | Low | High | 1-day grace period on `expires_at` (delete only if `expires_at < NOW() - INTERVAL '1 day'`). Dry-run validation step required before live run. | Diego Martinez |
| Database unavailable mid-run leaves partial deletion | Low | Medium | Idempotent batch design — re-run picks up where it left off (cursor-based: `WHERE expires_at < X AND id > last_id`). | Diego Martinez |
| CloudWatch metric emission fails silently | Low | Low | Alarm on missing metric: if no `sessions.purge.rows_deleted` datapoint within 8 hours of expected run window, fire `sessions-purge-job-missing` alarm. | Layla Hassan (DB Ops) |

---

## Cost and Resource Impact

**Build cost**: ~2 eng-weeks (Diego Martinez). No additional engineers required. No design work needed.

**Run cost**: Negligible. Lambda invocation for weekly 30-minute run: <$0.10/month. CloudWatch metrics and alarms: <$5/month. No new infrastructure — existing RDS, Lambda, and CloudWatch infrastructure used.

**Cost counter-metric**: Not applicable at this cost level. Tracked informally in monthly infra cost review as "sessions purge job" line item.

**Alternatives considered**:
1. PostgreSQL `pg_cron` extension in-database: rejected — not available in our current RDS parameter group; enabling requires parameter group change with DB restart.
2. Partition the `sessions` table by `expires_at` month and drop old partitions: rejected — table partitioning requires a migration that is higher-risk and longer-lead than the cron approach; viable as a future optimization if cron proves insufficient.

---

<!--
EXPECTED REVIEW OUTCOMES (used by RED-GREEN tests, do not delete):
  P0 expected on dims: none
  P1 expected on dims: none
  N/A expected on dims: 8 (Legal/privacy - no PII), 9 (GTM - internal), 10 (Support - no external)
  N/A expected on eval points: 5g (i18n - English-only internal)
  All graded dims expected: A or B
  Composite expected: 3.0+ (computed over GRADED dims only)
  Verdict expected: Ready
-->
