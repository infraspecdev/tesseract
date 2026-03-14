# Test Patterns Reference

HCL code examples for each coverage dimension using `terraform test` with `mock_provider` and plan-only assertions.

## Happy Path Pattern

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

## Variable Validation Pattern

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

## Feature Toggle Pattern

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

## Edge Cases Pattern

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

  assert {
    condition     = aws_vpc.main.cidr_block != ""
    error_message = "VPC should still be created with all options disabled"
  }
}
```

## CIDR Math Verification Pattern

```hcl
run "subnet_cidr_distribution" {
  command = plan

  variables {
    vpc_cidr = "10.0.0.0/16"
    az_count = 3
  }

  assert {
    condition     = length(aws_subnet.private) == 3
    error_message = "Should have one private subnet per AZ"
  }

  assert {
    condition     = length(distinct([for s in aws_subnet.private : s.cidr_block])) == length(aws_subnet.private)
    error_message = "Subnet CIDRs must not overlap"
  }
}
```

## Naming Convention Pattern

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
