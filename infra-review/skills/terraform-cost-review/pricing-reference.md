# AWS Pricing Reference

## Estimation Methodology

Use these approximate costs for common AWS resources (us-east-1):

| Resource | Approximate Cost |
|----------|-----------------|
| NAT Gateway | $32.40/month + $0.045/GB processed |
| Elastic IP (attached) | $3.60/month |
| VPC Interface Endpoint | $7.30/month/AZ |
| VPC Gateway Endpoint | Free |
| CloudWatch Log Ingestion | $0.50/GB |
| CloudWatch Log Storage | $0.03/GB/month |
| KMS CMK | $1.00/month + $0.03/10K requests |
| S3 Standard | $0.023/GB/month |
| EBS gp3 | $0.08/GB/month |

## Resource Inventory Categories

| Resource Category | Resources to Inventory | Key Cost Factors |
|-------------------|----------------------|-----------------|
| **Networking** | NAT Gateway, EIP, VPC Endpoint, Transit Gateway attachment | Per-hour + data transfer |
| **Compute** | EC2, Lambda, ECS tasks, EKS node groups | Instance type, runtime hours |
| **Storage** | S3 buckets, EBS volumes, EFS | Storage class, IOPS, throughput |
| **Database** | RDS, DynamoDB, ElastiCache | Instance type, storage, backups |
| **Monitoring** | CloudWatch log groups, metrics, alarms | Ingestion rate, retention, custom metrics |
| **Security** | KMS keys, WAF, Shield, GuardDuty | Per-key/month, per-rule evaluations |

## Environment-Specific Variable Patterns

| Variable Pattern | Dev | Staging | Production |
|-----------------|-----|---------|-----------|
| `enable_nat_gateway` | `false` | `true` | `true` |
| `nat_gateway_count` | `0` | `1` | AZ count |
| `az_count` | `1` | `2` | `3` |
| `instance_type` | Smallest viable | Medium | Production-sized |
| `flow_log_retention_days` | `7` | `14` | `90` |
| `enable_vpc_endpoints` | `false` | `false` | `true` |
