# Terraform Plan Analyzer — Reference Tables

## Plan JSON Message Types

The `terraform plan -json` output is a stream of JSON lines. Each line has a `@level` and `type` field.

| Type | What It Contains |
|------|-----------------|
| `planned_change` | Resource address, action (create/update/delete/replace), reason |
| `change_summary` | Counts: add, change, remove |
| `diagnostic` | Warnings and errors from the plan |
| `resource_drift` | Changes detected outside Terraform |
| `outputs` | Output value changes |

For `terraform show -json plan.tfplan`, the structure is a single JSON object with:
- `resource_changes[]` — Array of planned resource changes
- `output_changes` — Map of output changes
- `prior_state` — Current state before changes

### Extracting Resource Changes

For each resource change, extract:
- `address` — Full resource address (e.g., `aws_iam_role.flow_log`)
- `type` — Resource type (e.g., `aws_iam_role`)
- `change.actions` — Array: `["create"]`, `["update"]`, `["delete"]`, `["delete", "create"]` (replace)
- `change.before` / `change.after` — Attribute values before and after

## Destructive Action Risk Levels

Flag any destroy or replace action on stateful resources:

| Resource Type | Risk Level | Why |
|---------------|-----------|-----|
| `aws_rds_instance`, `aws_rds_cluster` | CRITICAL | Data loss |
| `aws_dynamodb_table` | CRITICAL | Data loss |
| `aws_s3_bucket` | CRITICAL | Data loss (if not empty) |
| `aws_kms_key` | CRITICAL | Encryption key loss — dependent resources become inaccessible |
| `aws_efs_file_system` | HIGH | Data loss |
| `aws_elasticache_cluster` | HIGH | Cache data loss, connection disruption |
| `aws_vpc` | HIGH | All resources inside destroyed |
| `aws_subnet` | HIGH | Resources in subnet destroyed |
| `aws_db_subnet_group` | HIGH | Database connectivity impact |
| `aws_iam_role` | MEDIUM | Service disruption if role is in use |
| `aws_security_group` | MEDIUM | Network connectivity impact |
| `aws_route_table` | MEDIUM | Network routing disruption |
| `aws_nat_gateway` | MEDIUM | Outbound connectivity loss for private subnets |
| `aws_eip` | LOW | IP address change |

For replace actions (`["delete", "create"]`), also flag the reason — is it a force-new attribute change?

## Security-Sensitive Resource Changes

### IAM Changes
- `aws_iam_role` — Check trust policy changes (`assume_role_policy`)
- `aws_iam_policy` / `aws_iam_role_policy` — Check policy document for `*` actions or resources
- `aws_iam_policy_attachment` / `aws_iam_role_policy_attachment` — Who is getting new permissions?
- `aws_iam_user` — User creation or modification

### Network Changes
- `aws_security_group` / `aws_security_group_rule` — Check for `0.0.0.0/0` or `::/0` ingress
- `aws_network_acl` / `aws_network_acl_rule` — Check rule changes
- `aws_route` — New routes to internet gateway?
- `aws_vpc_endpoint` — Endpoint policy changes

### Encryption Changes
- `aws_kms_key` — Key policy changes, deletion scheduling
- Resources losing `kms_key_id` — Downgrade from CMK to AWS-managed
- `aws_s3_bucket_server_side_encryption_configuration` — Encryption config changes

### Public Access Changes
- `aws_s3_bucket_public_access_block` — Any block being set to `false`
- `aws_db_instance` with `publicly_accessible` changing to `true`
- `aws_lb` changing scheme to `internet-facing`

## Cost-Impacting Resources

| Resource Type | Approximate Cost | Direction |
|---------------|-----------------|-----------|
| `aws_nat_gateway` | $32/month + data transfer | Create = cost increase |
| `aws_vpc_endpoint` (Interface) | $7.30/month/AZ | Create = cost increase |
| `aws_eip` | $3.60/month | Create = cost increase |
| `aws_rds_instance` | Varies by instance type | Check `instance_class` in after |
| `aws_elasticache_cluster` | Varies by node type | Check `node_type` in after |
| `aws_instance` | Varies by instance type | Check `instance_type` in after |
| `aws_cloudwatch_log_group` | $0.50/GB ingestion | Check `retention_in_days` |
| `aws_kms_key` | $1/month | Create = cost increase |

For updates, compare before/after values of sizing attributes (`instance_type`, `instance_class`, `node_type`, `allocated_storage`).

## Drift Categories

If the plan shows `resource_drift` entries or unexpected update actions on resources not modified in code:

- **Configuration drift** — Someone changed the resource outside Terraform
- **Provider behavior change** — Provider upgrade changed default values
- **State inconsistency** — State file doesn't match reality

## Verdict Criteria

| Verdict | When |
|---------|------|
| **Safe to Apply** | No destructive actions, no security concerns, changes match expectations |
| **Review Required** | Has security-sensitive changes, cost increases, or replace actions that need human review |
| **Do Not Apply** | Destructive actions on stateful resources without `prevent_destroy`, security downgrades, or unexpected drift |
