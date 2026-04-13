# Kubernetes Resource Sizing Reference

## Sizing Guidelines by Workload Type

| Workload Type | CPU Request | CPU Limit | Memory Request | Memory Limit | Notes |
|--------------|-------------|-----------|---------------|-------------|-------|
| Web API (light) | 100m-250m | 500m-1000m | 128Mi-256Mi | 512Mi | Scale horizontally with HPA |
| Web API (heavy) | 250m-500m | 1000m-2000m | 256Mi-512Mi | 1Gi | Consider VPA for right-sizing |
| Background worker | 100m-250m | 500m | 128Mi-256Mi | 512Mi | Batch-oriented, scale on queue depth |
| Database (sidecar) | 50m-100m | 200m | 64Mi-128Mi | 256Mi | For sidecar proxies only |
| CronJob | 100m-500m | 1000m | 128Mi-512Mi | 1Gi | Size for actual job duration |
| Init container | 50m-100m | 500m | 64Mi-128Mi | 256Mi | Short-lived, don't over-provision |
| Monitoring agent | 50m-100m | 200m | 64Mi-128Mi | 256Mi | DaemonSet — multiplied by node count |

## Request vs Limit Strategy

| Strategy | When to Use | Trade-off |
|----------|-----------|-----------|
| Requests = Limits (Guaranteed QoS) | Latency-sensitive, database pods | No burst, may over-provision |
| Requests < Limits (Burstable QoS) | Typical web workloads | Can burst, risk of OOM kill under pressure |
| No Limits (BestEffort QoS) | Dev/test only, non-critical batch | Maximum flexibility, first to be evicted |

## Environment Sizing Patterns

| Resource | Dev | Staging | Production |
|----------|-----|---------|-----------|
| Replica count | 1 | 2 | 3+ (based on load) |
| CPU request | 50% of prod | 75% of prod | Based on P50 actual |
| Memory request | 50% of prod | 75% of prod | Based on P50 actual |
| HPA min replicas | 1 | 1-2 | 2-3 |
| HPA max replicas | 2 | 3-5 | Based on peak load |
| PVC size | Minimum viable | 50% of prod | Based on data growth projections |

## Common Over-Provisioning Patterns

| Pattern | Indicator | Right-Sizing Approach |
|---------|-----------|----------------------|
| 1 CPU request for a sidecar | Proxy/agent using <100m actual | Reduce to 50-100m request |
| 1Gi memory for a small API | Actual RSS <200Mi | Reduce to 256Mi request, 512Mi limit |
| 10 replicas in staging | Same as prod | Reduce to 2-3 with HPA |
| 100Gi PVC for small database | <5Gi actual usage | Start with 10Gi, use volume expansion |
| HPA targeting 50% CPU | Very aggressive scaling, frequent pod churn | Target 70-80% for most workloads |
