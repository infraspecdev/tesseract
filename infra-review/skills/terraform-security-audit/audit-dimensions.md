# Audit Dimensions Reference

## Dimension 1: IAM Policy Analysis

Analyze every `aws_iam_policy_document`, `aws_iam_policy`, and inline policy for:

| Check | What Automated Tools Miss | How to Verify |
|-------|--------------------------|---------------|
| Overly broad actions | `s3:Get*` passes Checkov but grants `s3:GetBucketPolicy` | Expand wildcards mentally, check if all expanded actions are needed |
| Resource scope gaps | `arn:aws:s3:::*` passes but should be `arn:aws:s3:::specific-bucket/*` | Verify Resource ARN patterns match intended scope |
| Missing conditions | Policy allows `sts:AssumeRole` without `aws:PrincipalOrgID` condition | Check sensitive actions have condition blocks |
| Cross-account exposure | Trust policy allows external account without external ID | Verify `sts:ExternalId` condition on cross-account trust |
| Service-linked confusion | Custom role when service-linked role exists | Check if AWS provides a service-linked role for the use case |
| Policy size risk | Many statements approaching 6,144 char managed policy limit | Count policy document size, suggest splitting if close to limits |

**How to audit:**
1. Read every `data "aws_iam_policy_document"` block
2. For each statement, list the actual permissions granted (expand wildcards)
3. Verify `Resource` is scoped to specific ARNs
4. Check `Condition` blocks exist on sensitive actions
5. Flag any `Effect = "Allow"` with `"*"` in actions or resources

## Dimension 2: Network Exposure Tracing

Trace network paths from public internet to private resources:

| Check | What Automated Tools Miss | How to Verify |
|-------|--------------------------|---------------|
| Ephemeral port gaps | NACLs allow 1024-65535 inbound but should only allow specific ranges | Trace which services listen on which ports |
| IPv6 blind spots | IPv4 security groups are tight but IPv6 (`::/0`) is wide open | Check every SG rule for both `cidr_blocks` AND `ipv6_cidr_blocks` |
| Transitive exposure | Public subnet to private subnet rules allow more than intended | Trace SG references: if SG-A allows SG-B, what can SG-B access? |
| NACL rule ordering | Higher-priority deny rules may be shadowed by lower-number allow rules | Read NACL rules in order (lowest number first) |
| Missing egress restrictions | Egress is default-allow, should be restricted for sensitive subnets | Check for explicit egress deny rules on private subnets |

**How to audit:**
1. Map all subnets (public, private, isolated) and their route tables
2. For each security group, list all inbound and outbound rules
3. Trace: Internet -> IGW -> public subnet -> SG -> resource -> SG -> private subnet
4. Verify no unintended path exists from public to private resources

## Dimension 3: Encryption Audit

| Check | What Automated Tools Miss | How to Verify |
|-------|--------------------------|---------------|
| AWS-managed vs CMK | `aws/s3` key passes checks but CMK provides rotation control and cross-account access | Check `kms_key_id` references a custom KMS key, not default |
| Missing key rotation | CMK exists but `enable_key_rotation = true` not set | Grep for `aws_kms_key` resources, verify rotation enabled |
| Encryption in transit | Resources encrypted at rest but connections allow non-TLS | Check for `ssl_mode`, `require_ssl`, security group port restrictions |
| Log encryption gap | Main resource encrypted but its CloudWatch log group is not | Verify every `aws_cloudwatch_log_group` has `kms_key_id` |
| Backup encryption | Source encrypted but backup/replica uses default encryption | Check replication and backup configurations for KMS settings |

**How to audit:**
1. List all resources that store data (S3, RDS, EBS, DynamoDB, CloudWatch)
2. For each, verify encryption at rest with CMK
3. For each, verify encryption in transit configuration
4. Cross-check: if resource A is encrypted, are its logs/backups also encrypted?

## Dimension 4: Checkov Configuration Review

| Check | What to Verify |
|-------|---------------|
| Skip justification quality | Every `#checkov:skip=CKV_*:reason` has a meaningful reason, not "not applicable" |
| Skip scope | Skips are on specific resources, not file-level or directory-level |
| Critical check coverage | CKV_AWS_144, CKV_AWS_145, CKV2_AWS_19 are NOT skipped without director-level justification |
| Custom policies | If `.checkov/` directory exists, review custom policies for gaps |
| CI integration | Checkov runs in CI with `--hard-fail-on CRITICAL` at minimum |
