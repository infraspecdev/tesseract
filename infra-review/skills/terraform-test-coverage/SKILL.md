---
name: terraform-test-coverage
description: Use when reviewing Terraform test files (.tftest.hcl), assessing test coverage, or designing new tests for components using mock_provider and plan-only assertions
---

# Terraform Test Coverage Assessment

## Overview

Test quality assessment for Terraform components using the native `terraform test` framework (`.tftest.hcl` files). Evaluates coverage across 6 dimensions and provides test patterns for `mock_provider`, `override_resource`, and plan-only assertions.

## When to Use

- Reviewing existing `.tftest.hcl` files for coverage gaps
- Designing new tests for a Terraform component
- After adding new variables, resources, or feature flags
- Assessing whether a component is adequately tested before release

## Coverage Dimensions

### Dimension 1: Happy Path

Does a basic test exist that provisions the component with valid inputs?

**What to check:**
- At least one `run` block that uses `command = plan` with `mock_provider`
- Valid values for all required variables
- Assertions on key resource attributes (not just "plan succeeds")

**Pattern:**
```hcl
mock_provider "aws" {}

variables {
  aws_region   = "us-east-1"
  environment  = "test"
  stage        = "test"
  tags         = { ManagedBy = "terraform-test" }
  # ... component-specific required variables
}

run "happy_path" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block != ""
    error_message = "VPC CIDR block should be set"
  }

  assert {
    condition     = length(aws_subnet.private) > 0
    error_message = "At least one private subnet should be created"
  }
}
```

### Dimension 2: Variable Validation

Are validation rules on variables actually tested?

**What to check:**
- For every `validation` block in `variables.tf`, there should be a test that triggers it
- Tests use `expect_failures` to verify validation catches bad input

**Pattern:**
```hcl
run "invalid_environment_rejected" {
  command = plan

  variables {
    environment = "INVALID"
  }

  expect_failures = [
    var.environment,
  ]
}

run "empty_tags_rejected" {
  command = plan

  variables {
    tags = {}
  }

  expect_failures = [
    var.tags,
  ]
}
```

### Dimension 3: Feature Toggles

Are enable/disable flags tested in both states?

**What to check:**
- If component has `enable_nat_gateway`, test both `true` and `false`
- When disabled, verify dependent resources are NOT created
- When enabled, verify resources ARE created with expected attributes

**Pattern:**
```hcl
run "nat_gateway_disabled" {
  command = plan

  variables {
    enable_nat_gateway = false
  }

  assert {
    condition     = length(aws_nat_gateway.main) == 0
    error_message = "NAT gateways should not be created when disabled"
  }

  assert {
    condition     = length(aws_eip.nat) == 0
    error_message = "EIPs should not be created when NAT is disabled"
  }
}

run "nat_gateway_enabled" {
  command = plan

  variables {
    enable_nat_gateway = true
    nat_gateway_count  = 2
  }

  assert {
    condition     = length(aws_nat_gateway.main) == 2
    error_message = "Expected 2 NAT gateways"
  }
}
```

### Dimension 4: Edge Cases

Are boundary values and unusual inputs tested?

**What to check:**
- Minimum and maximum values for numeric variables (e.g., `az_count = 1`)
- Empty lists/maps where allowed
- Single-AZ deployment
- All optional features disabled simultaneously

**Pattern:**
```hcl
run "single_az_deployment" {
  command = plan

  variables {
    az_count = 1
  }

  assert {
    condition     = length(aws_subnet.private) == 1
    error_message = "Single AZ should create exactly 1 private subnet"
  }
}

run "all_optional_features_disabled" {
  command = plan

  variables {
    enable_nat_gateway    = false
    enable_vpc_endpoints  = false
    enable_flow_logs      = false
  }

  # Should still create base VPC and subnets
  assert {
    condition     = aws_vpc.main.cidr_block != ""
    error_message = "VPC should still be created with all options disabled"
  }
}
```

### Dimension 5: CIDR Math Verification

For networking components, are CIDR calculations tested?

**What to check:**
- Subnet CIDR blocks don't overlap
- Subnet sizes match expected netmask
- Subnets fit within VPC CIDR
- AZ distribution is correct

**Pattern:**
```hcl
run "subnet_cidr_distribution" {
  command = plan

  variables {
    vpc_cidr = "10.0.0.0/16"
    az_count = 3
  }

  # Verify subnets are created per AZ
  assert {
    condition     = length(aws_subnet.private) == 3
    error_message = "Should have one private subnet per AZ"
  }

  # Verify no CIDR overlap (subnet CIDRs are distinct)
  assert {
    condition     = length(distinct([for s in aws_subnet.private : s.cidr_block])) == length(aws_subnet.private)
    error_message = "Subnet CIDRs must not overlap"
  }
}
```

### Dimension 6: Naming Convention Tests

Are resource names and tags consistent?

**What to check:**
- Resources have expected Name tags
- Naming follows component conventions
- Environment and stage propagate to names/tags

**Pattern:**
```hcl
run "naming_conventions" {
  command = plan

  variables {
    environment = "dev"
    stage       = "use1"
  }

  assert {
    condition     = aws_vpc.main.tags["Environment"] == "dev"
    error_message = "VPC should be tagged with environment"
  }

  assert {
    condition     = can(regex("dev", aws_vpc.main.tags["Name"]))
    error_message = "VPC Name tag should contain environment"
  }
}
```

## Test Infrastructure Patterns

### mock_provider (plan-only testing)

```hcl
mock_provider "aws" {
  # Optionally override specific resources or data sources
  override_resource {
    target = aws_vpc_ipam_pool_cidr_allocation.main
    values = {
      cidr = "10.0.0.0/16"
    }
  }

  override_data {
    target = data.aws_availability_zones.available
    values = {
      names = ["us-east-1a", "us-east-1b", "us-east-1c"]
    }
  }
}
```

### override_resource for IPAM components

Components using IPAM need mock values since IPAM allocations happen at apply time:

```hcl
override_resource {
  target = aws_vpc_ipam_pool_cidr_allocation.vpc
  values = {
    cidr = "10.0.0.0/16"
    id   = "ipam-cidr-alloc-mock"
  }
}
```

### Test file organization

```
src/
  main.tf
  variables.tf
  outputs.tf
  versions.tf
  providers.tf
  main.tftest.hcl        # Happy path + feature toggle tests
  validation.tftest.hcl   # Variable validation tests
  edge_cases.tftest.hcl   # Edge cases + CIDR math
```

## Coverage Assessment Output

```markdown
## Test Coverage Assessment

**Component:** [name]
**Test files found:** [count]
**Total test runs:** [count]

### Coverage Matrix

| Dimension | Coverage | Tests | Status |
|-----------|----------|-------|--------|
| Happy Path | X/Y scenarios | [list] | Full/Partial/None |
| Variable Validation | X/Y validations tested | [list] | Full/Partial/None |
| Feature Toggles | X/Y flags tested both states | [list] | Full/Partial/None |
| Edge Cases | X scenarios | [list] | Full/Partial/None |
| CIDR Math | X scenarios | [list] | Full/Partial/None (N/A if not networking) |
| Naming Conventions | X scenarios | [list] | Full/Partial/None |

### Missing Coverage

| Gap | Priority | Suggested Test |
|-----|----------|---------------|
| ... | High/Medium/Low | Brief description of what to test |

### Test Quality Notes

- [Observations about test quality, mock patterns, assertion depth]

## Coverage Score: X/10

## Verdict: [Well Tested / Adequately Tested / Under Tested / Untested]
```
