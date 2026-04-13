# Kubernetes Operational Checklist

## Health Probes (K1-K6)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| K1 | Readiness probe present | Every long-running workload has a readiness probe | Critical |
| K2 | Liveness probe present | Every long-running workload has a liveness probe | Important |
| K3 | Startup probe for slow apps | Applications taking >30s to start have startup probes | Important |
| K4 | Liveness != readiness | Liveness checks process health, readiness checks ability to serve (including dependencies) | Important |
| K5 | Probe timing appropriate | initialDelaySeconds, periodSeconds, failureThreshold tuned for the application | Warning |
| K6 | Probe endpoint lightweight | Probe endpoint doesn't call databases or external services (for liveness) | Warning |

## Disruption & Availability (K7-K11)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| K7 | PDB exists for multi-replica workloads | PodDisruptionBudget configured with appropriate minAvailable or maxUnavailable | Critical |
| K8 | PDB values reasonable | minAvailable not set to 100% (blocks all evictions), maxUnavailable not 0 | Important |
| K9 | Rolling update strategy configured | maxSurge and maxUnavailable tuned (not both 25% default for critical services) | Important |
| K10 | Topology spread constraints | Pods spread across nodes/zones for HA | Important |
| K11 | Pod anti-affinity | Critical workloads don't schedule on the same node | Important |

## Observability (K12-K17)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| K12 | Prometheus annotations | `prometheus.io/scrape`, `prometheus.io/port`, `prometheus.io/path` annotations | Important |
| K13 | Structured logging | Application outputs JSON logs (not unstructured text) | Important |
| K14 | Log volume bounded | No unbounded debug logging in production | Warning |
| K15 | Tracing configured | Trace context propagation headers, OpenTelemetry sidecar or SDK | Warning |
| K16 | Resource metrics | Metrics for request rate, error rate, duration (RED method) | Important |
| K17 | Health dashboard | Grafana dashboard or equivalent defined for the workload | Warning |

## Graceful Shutdown (K18-K22)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| K18 | preStop hook | Pods that need drain time have `lifecycle.preStop` (e.g., `sleep 5` for LB deregistration) | Important |
| K19 | terminationGracePeriodSeconds | Value matches actual shutdown time — default 30s may be insufficient | Important |
| K20 | SIGTERM handling | Application handles SIGTERM for graceful shutdown (stop accepting new requests, drain existing) | Important |
| K21 | Connection draining | For web services: preStop + terminationGracePeriod > expected drain time | Important |
| K22 | Resource cleanup | Long-running processes (consumers, watchers) clean up on shutdown | Warning |

## Dependency Management (K23-K27)

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| K23 | Init containers for dependencies | Workloads with external dependencies use init containers to wait for readiness | Important |
| K24 | ConfigMap/Secret reload | Changes to ConfigMaps/Secrets trigger pod rollout (hash annotation or Reloader) | Important |
| K25 | Service dependency ordering | Startup order documented for tightly coupled services | Warning |
| K26 | Circuit breaker / retry | Clients handle dependency failures gracefully (not just crash) | Warning |
| K27 | External dependency health | Readiness probes include checks for critical external dependencies | Warning |

## EKS-Specific Operational Checks (K28-K31)

Only apply when EKS is detected:

| # | Check | What to Look For | Severity |
|---|-------|-----------------|----------|
| K28 | ALB ingress health checks | `alb.ingress.kubernetes.io/healthcheck-path` configured, matches readiness probe | Important |
| K29 | Container Insights | CloudWatch Container Insights enabled for monitoring | Warning |
| K30 | EBS CSI driver | If using EBS PVCs, EBS CSI driver is configured (not in-tree) | Important |
| K31 | ExternalDNS annotations | Services/Ingresses that need DNS records have ExternalDNS annotations | Warning |
