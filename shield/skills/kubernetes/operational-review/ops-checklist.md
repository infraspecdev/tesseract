# Kubernetes Operational Checklist

## Assessability Guide

Each check has a **Source** column:
- **Manifest** — Assessable from K8s YAML alone. Always check these.
- **Context** — Requires application knowledge. Ask the user if unclear, but flag the absence as a finding.

When a check is marked **Context**, don't skip it silently — note it as "Not verifiable from manifests; confirm with team" rather than omitting it from the report.

## Health Probes (K1-K6)

| # | Check | What to Look For | Severity | Source |
|---|-------|-----------------|----------|--------|
| K1 | Readiness probe present | Every long-running workload has a readiness probe | Critical | Manifest |
| K2 | Liveness probe present | Every long-running workload has a liveness probe | Important | Manifest |
| K3 | Startup probe for slow apps | Applications taking >30s to start have startup probes | Important | Manifest |
| K4 | Liveness != readiness | Liveness checks process health, readiness checks ability to serve (including dependencies) | Important | Manifest |
| K5 | Probe timing appropriate | initialDelaySeconds, periodSeconds, failureThreshold tuned for the application | Warning | Context |
| K6 | Probe endpoint lightweight | Probe endpoint doesn't call databases or external services (for liveness) | Warning | Context |

## Disruption & Availability (K7-K11)

| # | Check | What to Look For | Severity | Source |
|---|-------|-----------------|----------|--------|
| K7 | PDB exists for multi-replica workloads | PodDisruptionBudget configured with appropriate minAvailable or maxUnavailable | Critical | Manifest |
| K8 | PDB values reasonable | minAvailable not set to 100% (blocks all evictions), maxUnavailable not 0 | Important | Manifest |
| K9 | Rolling update strategy configured | maxSurge and maxUnavailable tuned (not both 25% default for critical services) | Important | Manifest |
| K10 | Topology spread constraints | Pods spread across nodes/zones for HA | Important | Manifest |
| K11 | Pod anti-affinity | Critical workloads don't schedule on the same node | Important | Manifest |

## Observability (K12-K17)

| # | Check | What to Look For | Severity | Source |
|---|-------|-----------------|----------|--------|
| K12 | Prometheus annotations | `prometheus.io/scrape`, `prometheus.io/port`, `prometheus.io/path` annotations | Important | Manifest |
| K13 | Structured logging | Application outputs JSON logs (not unstructured text) | Important | Context |
| K14 | Log volume bounded | No unbounded debug logging in production | Warning | Context |
| K15 | Tracing configured | Trace context propagation headers, OpenTelemetry sidecar or SDK | Warning | Manifest |
| K16 | Resource metrics | Metrics for request rate, error rate, duration (RED method) | Important | Context |
| K17 | Health dashboard | Grafana dashboard or equivalent defined for the workload | Warning | Context |

## Graceful Shutdown (K18-K22)

| # | Check | What to Look For | Severity | Source |
|---|-------|-----------------|----------|--------|
| K18 | preStop hook | Pods that need drain time have `lifecycle.preStop` (e.g., `sleep 5` for LB deregistration) | Important | Manifest |
| K19 | terminationGracePeriodSeconds | Value matches actual shutdown time — default 30s may be insufficient | Important | Manifest |
| K20 | SIGTERM handling | Application handles SIGTERM for graceful shutdown (stop accepting new requests, drain existing) | Important | Context |
| K21 | Connection draining | For web services: preStop + terminationGracePeriod > expected drain time | Important | Manifest |
| K22 | Resource cleanup | Long-running processes (consumers, watchers) clean up on shutdown | Warning | Context |

## Dependency Management (K23-K27)

| # | Check | What to Look For | Severity | Source |
|---|-------|-----------------|----------|--------|
| K23 | Init containers for dependencies | Workloads with external dependencies use init containers to wait for readiness | Important | Manifest |
| K24 | ConfigMap/Secret reload | Changes to ConfigMaps/Secrets trigger pod rollout (hash annotation or Reloader) | Important | Manifest |
| K25 | Service dependency ordering | Startup order documented for tightly coupled services | Warning | Context |
| K26 | Circuit breaker / retry | Clients handle dependency failures gracefully (not just crash) | Warning | Context |
| K27 | External dependency health | Readiness probes include checks for critical external dependencies | Warning | Context |

## EKS-Specific Operational Checks (K28-K31)

Only apply when EKS is detected:

| # | Check | What to Look For | Severity | Source |
|---|-------|-----------------|----------|--------|
| K28 | ALB ingress health checks | `alb.ingress.kubernetes.io/healthcheck-path` configured, matches readiness probe | Important | Manifest |
| K29 | Container Insights | CloudWatch Container Insights enabled for monitoring | Warning | Context |
| K30 | EBS CSI driver | If using EBS PVCs, EBS CSI driver is configured (not in-tree) | Important | Manifest |
| K31 | ExternalDNS annotations | Services/Ingresses that need DNS records have ExternalDNS annotations | Warning | Manifest |
