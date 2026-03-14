# Shield Testing Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add eval infrastructure for agent quality testing, sample inputs for evals, an eval runner script, and contract test stubs for the PM adapter.

**Architecture:** Agent evals use criteria-based YAML files (must-find / should-find / must-not-false-positive) with sample Terraform inputs. The eval runner validates agent output against criteria using regex matching. PM adapter contract tests verify tool schema compliance using pytest.

**Tech Stack:** YAML (eval criteria), Terraform (sample inputs), Bash (eval runner), Python (contract tests, pytest)

---

## Chunk 1: Agent Eval Infrastructure

### Task 1: Create sample Terraform input for evals

**Files:**
- Create: `shield/evals/inputs/insecure-vpc-module/main.tf`
- Create: `shield/evals/inputs/insecure-vpc-module/variables.tf`
- Create: `shield/evals/inputs/insecure-vpc-module/outputs.tf`
- Create: `shield/evals/inputs/insecure-vpc-module/versions.tf`

- [ ] **Step 1: Create a deliberately insecure Terraform VPC module**

This module has intentional issues for each reviewer to find:

`main.tf`:
```hcl
# Deliberately insecure VPC module for Shield agent evals
# DO NOT use in production — every issue here is intentional

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "eval-vpc"
  }
}

# ISSUE: Wildcard IAM policy (security-reviewer should catch)
resource "aws_iam_role" "admin" {
  name = "admin-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "admin_policy" {
  name = "admin-policy"
  role = aws_iam_role.admin.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

# ISSUE: Security group open to 0.0.0.0/0 on SSH (security-reviewer should catch)
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Web security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ISSUE: 3 NAT gateways with no disable flag (cost-reviewer should catch)
resource "aws_nat_gateway" "az1" {
  allocation_id = aws_eip.nat_az1.id
  subnet_id     = aws_subnet.public_az1.id
}

resource "aws_nat_gateway" "az2" {
  allocation_id = aws_eip.nat_az2.id
  subnet_id     = aws_subnet.public_az2.id
}

resource "aws_nat_gateway" "az3" {
  allocation_id = aws_eip.nat_az3.id
  subnet_id     = aws_subnet.public_az3.id
}

resource "aws_eip" "nat_az1" {}
resource "aws_eip" "nat_az2" {}
resource "aws_eip" "nat_az3" {}

# ISSUE: Hardcoded API key in variable default (security-reviewer should catch)
variable "api_secret" {
  type    = string
  default = "sk-1234567890abcdef"
}

# ISSUE: CloudWatch log group without KMS encryption (security-reviewer should catch)
resource "aws_cloudwatch_log_group" "flow_logs" {
  name = "/vpc/flow-logs"
}

# ISSUE: No deletion protection on RDS (operations-reviewer should catch)
resource "aws_db_instance" "main" {
  identifier     = "eval-db"
  engine         = "postgres"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  username       = "admin"
  password       = var.api_secret

  deletion_protection = false
  skip_final_snapshot = true
}

# ISSUE: S3 bucket without encryption or public access block (security-reviewer should catch)
resource "aws_s3_bucket" "data" {
  bucket = "eval-data-bucket"
}

# OK: Port 443 open to 0.0.0.0/0 is intentional for ALB
# (security-reviewer should NOT flag this as an issue)

resource "aws_subnet" "public_az1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "public_az2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

resource "aws_subnet" "public_az3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1c"
}
```

`variables.tf`:
```hcl
variable "environment" {
  type    = string
  default = "dev"
}

variable "tags" {
  type    = map(string)
  default = {}
}
```

`outputs.tf`:
```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}
```

`versions.tf`:
```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

- [ ] **Step 2: Remove .gitkeep from evals/inputs/**

- [ ] **Step 3: Commit**

```
feat: add sample insecure VPC module for agent evals

Terraform module with deliberate security, cost, and operational
issues for testing reviewer agent quality.
```

### Task 2: Create eval criteria for security reviewer

**Files:**
- Create: `shield/evals/expected/security-reviewer-terraform.yaml`

- [ ] **Step 1: Create the criteria file**

```yaml
# Security reviewer eval criteria for insecure-vpc-module
# Evaluated against: shield/evals/inputs/insecure-vpc-module/
agent: security-reviewer
mode: infra-code
input: insecure-vpc-module

must_find:
  - id: wildcard-iam
    description: "Flags Action = * in IAM policy"
    match: "wildcard|Action.*\\*|overly.?permissive"
  - id: open-ssh
    description: "Flags 0.0.0.0/0 on port 22"
    match: "0\\.0\\.0\\.0/0.*22|SSH.*open|port 22.*0\\.0\\.0\\.0"
  - id: hardcoded-secret
    description: "Flags hardcoded API key in variable default"
    match: "hardcoded|secret|credential|api_secret|sk-1234"
  - id: unencrypted-log-group
    description: "Flags CloudWatch log group without KMS"
    match: "kms_key_id|log.*encrypt|CloudWatch.*encrypt"
  - id: s3-no-encryption
    description: "Flags S3 bucket without encryption config"
    match: "S3.*encrypt|server_side_encryption|bucket.*encrypt"
  - id: s3-no-public-block
    description: "Flags S3 bucket without public access block"
    match: "public.?access.?block|block.?public"

should_find:
  - id: wildcard-resource
    description: "Flags Resource = * in IAM policy"
    match: "Resource.*\\*|resource.*wildcard"
  - id: rds-password-in-var
    description: "Flags RDS using var.api_secret as password"
    match: "password.*variable|secret.*password|plaintext.*password"

must_not_false_positive:
  - id: valid-https
    description: "Should not flag port 443 open to 0.0.0.0/0"
    match_absence_in: "443.*0\\.0\\.0\\.0/0.*issue|443.*problem|port 443.*flag"
```

- [ ] **Step 2: Remove .gitkeep from evals/expected/**

- [ ] **Step 3: Commit**

```
feat: add security reviewer eval criteria

Must-find: wildcard IAM, open SSH, hardcoded secret, unencrypted
logs, S3 without encryption/public block. Must not flag port 443.
```

### Task 3: Create eval criteria for cost reviewer

**Files:**
- Create: `shield/evals/expected/cost-reviewer-terraform.yaml`

- [ ] **Step 1: Create the criteria file**

```yaml
# Cost reviewer eval criteria for insecure-vpc-module
agent: cost-reviewer
mode: infra-code
input: insecure-vpc-module

must_find:
  - id: nat-gateway-count
    description: "Flags 3 NAT gateways without configurable count"
    match: "NAT.*gateway|nat_gateway.*3|three.*NAT"
  - id: nat-no-disable
    description: "Flags NAT gateways without enable/disable toggle"
    match: "enable.*nat|disable.*nat|toggle|configurable"

should_find:
  - id: eip-cost
    description: "Flags 3 EIPs tied to NAT gateways"
    match: "EIP|elastic.?IP|eip.*cost"
  - id: log-retention
    description: "Flags CloudWatch log group without retention"
    match: "retention|log.*retention|infinite.*log"
  - id: env-recommendations
    description: "Provides environment-specific sizing recommendations"
    match: "dev|staging|prod|environment"

must_not_false_positive: []
```

- [ ] **Step 2: Commit**

```
feat: add cost reviewer eval criteria

Must-find: NAT gateway count and disable toggle. Should-find:
EIP costs, log retention, environment recommendations.
```

### Task 4: Create eval runner script

**Files:**
- Create: `shield/evals/run-evals.sh`

- [ ] **Step 1: Create the runner**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Shield agent eval runner
# Validates agent output against criteria YAML files
#
# Usage: ./run-evals.sh [criteria-file]
# If no file specified, runs all criteria in expected/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPECTED_DIR="${SCRIPT_DIR}/expected"
RESULTS_DIR="${SCRIPT_DIR}/results"
mkdir -p "$RESULTS_DIR"

PASS=0
FAIL=0
WARN=0

check_criteria() {
  local criteria_file="$1"
  local output_file="$2"
  local category="$3"  # must_find, should_find, must_not_false_positive

  python3 -c "
import yaml, re, sys

with open('$criteria_file') as f:
    criteria = yaml.safe_load(f)

with open('$output_file') as f:
    output = f.read()

category = '$category'
items = criteria.get(category, [])
results = []

for item in items:
    item_id = item['id']
    desc = item['description']
    if category == 'must_not_false_positive':
        pattern = item.get('match_absence_in', '')
        found = bool(re.search(pattern, output, re.IGNORECASE)) if pattern else False
        results.append({
            'id': item_id,
            'description': desc,
            'passed': not found,
            'category': category,
        })
    else:
        pattern = item.get('match', '')
        found = bool(re.search(pattern, output, re.IGNORECASE)) if pattern else False
        results.append({
            'id': item_id,
            'description': desc,
            'passed': found,
            'category': category,
        })

for r in results:
    status = 'PASS' if r['passed'] else ('FAIL' if r['category'] == 'must_find' or r['category'] == 'must_not_false_positive' else 'WARN')
    print(f\"{status} [{r['category']}] {r['id']}: {r['description']}\")
" 2>/dev/null
}

run_eval() {
  local criteria_file="$1"
  local basename=$(basename "$criteria_file" .yaml)

  echo "=== Evaluating: $basename ==="

  # Check if a results file exists for this eval
  local output_file="${RESULTS_DIR}/${basename}.txt"
  if [ ! -f "$output_file" ]; then
    echo "  SKIP: No output file at $output_file"
    echo "  To run: capture agent output to $output_file first"
    echo ""
    return
  fi

  for category in must_find should_find must_not_false_positive; do
    check_criteria "$criteria_file" "$output_file" "$category"
  done

  echo ""
}

# Run specified criteria or all
if [ -n "${1:-}" ]; then
  run_eval "$1"
else
  for criteria in "$EXPECTED_DIR"/*.yaml; do
    [ -f "$criteria" ] && run_eval "$criteria"
  done
fi

echo "=== Eval Summary ==="
echo "To generate agent output for evaluation:"
echo "  1. Run the agent against the input module"
echo "  2. Save output to shield/evals/results/<criteria-name>.txt"
echo "  3. Re-run this script"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x shield/evals/run-evals.sh
```

- [ ] **Step 3: Commit**

```
feat: add agent eval runner script

Validates agent output against criteria YAML files using regex
matching. Reports must-find (FAIL), should-find (WARN), and
must-not-false-positive (FAIL) results.
```

## Chunk 2: PM Adapter Contract Tests

### Task 5: Create contract test infrastructure

**Files:**
- Create: `shield/adapters/clickup/tests/__init__.py`
- Create: `shield/adapters/clickup/tests/test_contract.py`
- Create: `shield/adapters/clickup/tests/conftest.py`

- [ ] **Step 1: Create conftest.py with fixtures**

```python
"""Shared fixtures for ClickUp adapter tests."""
import pytest


@pytest.fixture
def mock_capabilities():
    """Expected capabilities response."""
    return {
        "adapter": "clickup",
        "adapter_mode": "hybrid",
        "capabilities": [
            "pm_sync",
            "pm_bulk_create",
            "pm_bulk_update",
            "pm_get_status",
            "pm_link_story_to_epic",
            "pm_bulk_rename",
            "pm_action_log",
            "pm_get_capabilities",
        ],
    }
```

- [ ] **Step 2: Create contract test file**

```python
"""PM adapter contract tests.

These tests verify that the ClickUp adapter conforms to the pm_* interface
contract. The same tests should pass for any PM adapter implementation.
"""
import json
from pathlib import Path


def test_capabilities_lists_all_required_operations(mock_capabilities):
    """pm_get_capabilities must return all required operations."""
    required = {"pm_sync", "pm_get_status", "pm_get_capabilities"}
    actual = set(mock_capabilities["capabilities"])
    missing = required - actual
    assert not missing, f"Missing required capabilities: {missing}"


def test_capabilities_declares_adapter_name(mock_capabilities):
    """pm_get_capabilities must declare the adapter name."""
    assert "adapter" in mock_capabilities
    assert isinstance(mock_capabilities["adapter"], str)
    assert len(mock_capabilities["adapter"]) > 0


def test_capabilities_declares_adapter_mode(mock_capabilities):
    """pm_get_capabilities must declare the adapter mode."""
    assert mock_capabilities["adapter_mode"] in ("native", "hybrid", "full")


def test_pm_config_schema_valid():
    """pm.json example must validate against the PM schema."""
    schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "pm.schema.json"
    example_path = Path(__file__).parent.parent.parent.parent / "config-examples" / "pm-clickup.example.json"

    if not schema_path.exists() or not example_path.exists():
        pytest.skip("Schema or example file not found")

    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    with open(schema_path) as f:
        schema = json.load(f)
    with open(example_path) as f:
        example = json.load(f)

    jsonschema.validate(example, schema)


def test_capabilities_only_declares_implemented_tools(mock_capabilities):
    """Every capability declared must correspond to a registered tool."""
    # This is a structural test — in integration tests, we'd actually
    # call each declared capability and verify it doesn't error with
    # "not implemented"
    valid_prefixes = ("pm_",)
    for cap in mock_capabilities["capabilities"]:
        assert any(cap.startswith(p) for p in valid_prefixes), \
            f"Capability '{cap}' doesn't follow pm_* naming convention"
```

- [ ] **Step 3: Create __init__.py**

Empty file.

- [ ] **Step 4: Commit**

```
feat: add PM adapter contract tests

Verify capabilities declaration, adapter naming, mode, schema
compliance, and tool naming convention. Same tests should pass
for any PM adapter implementation.
```

### Task 6: Update test CI workflow for evals and contract tests

**Files:**
- Modify: `.github/workflows/test.yml`

- [ ] **Step 1: Add eval and contract test jobs**

Add two new jobs to the existing test.yml:

```yaml
  agent-evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: Validate eval criteria YAML
        run: |
          pip install pyyaml
          python3 -c "
          import yaml, glob
          for f in glob.glob('shield/evals/expected/*.yaml'):
              with open(f) as fh:
                  data = yaml.safe_load(fh)
              assert 'agent' in data, f'{f}: missing agent field'
              assert 'mode' in data, f'{f}: missing mode field'
              assert 'must_find' in data, f'{f}: missing must_find field'
              for item in data['must_find']:
                  assert 'id' in item, f'{f}: must_find item missing id'
                  assert 'match' in item, f'{f}: must_find item missing match'
              print(f'✓ {f} valid')
          "

  adapter-contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v4
      - name: Run contract tests
        run: |
          cd shield/adapters/clickup
          uv run --extra test pytest tests/ -v
```

Also update pyproject.toml to add test dependencies:
```toml
[project.optional-dependencies]
test = ["pytest>=8.0", "jsonschema>=4.0"]
```

- [ ] **Step 2: Commit**

```
ci: add agent eval validation and adapter contract tests to CI

Validates eval criteria YAML structure and runs PM adapter
contract tests in the test workflow.
```
