---
name: terraform-test-coverage
description: Use when reviewing Terraform test files (.tftest.hcl), assessing test coverage, or designing new tests for components using mock_provider and plan-only assertions
---

# Terraform Test Coverage Assessment

## Overview

Test quality assessment for Terraform components using the native `terraform test` framework (`.tftest.hcl` files). Evaluates coverage across 6 dimensions and provides patterns for `mock_provider`, `override_resource`, and plan-only assertions.

## When to Use

- Reviewing existing `.tftest.hcl` files for coverage gaps
- Designing new tests for a Terraform component
- After adding new variables, resources, or feature flags
- Assessing whether a component is adequately tested before release

## When NOT to Use

- For non-native test frameworks (Terratest, kitchen-terraform)
- For syntax or formatting checks -- use `terraform validate` / `terraform fmt`
- For security auditing -- use the `terraform-security-audit` skill
- For module API design or variable naming reviews
- When the component has no `.tftest.hcl` files and you are not asked to create them

## Coverage Dimensions

Assess each component against these 6 dimensions (see `test-patterns.md` for HCL examples):

1. **Happy Path** -- `run` block with `command = plan`, valid inputs, assertions on key resource attributes
2. **Variable Validation** -- Every `validation` block has a test using `expect_failures`
3. **Feature Toggles** -- Every enable/disable flag tested in both states
4. **Edge Cases** -- Boundary values, empty collections, single-AZ, all features disabled
5. **CIDR Math** -- Subnet CIDRs do not overlap, fit within VPC CIDR, correct AZ distribution (N/A for non-networking)
6. **Naming Conventions** -- Name tags and environment/stage propagate consistently

## Workflow

1. **Discover tests**: Find all `.tftest.hcl` files in the component
2. **Inventory variables**: Read `variables.tf` to list all required variables, validation blocks, and feature toggle flags
3. **Map coverage**: For each `run` block, determine which dimension(s) it covers
4. **Identify gaps**: Cross-reference dimensions against existing tests. Flag missing coverage
5. **Assess quality**: Check assertion depth -- tests should verify specific attributes, not just "plan succeeds"
6. **Produce report**: Use the template from `templates.md`

## Critical Rules

- Every `validation` block MUST have a matching `expect_failures` test
- Every boolean feature flag MUST be tested in both states
- Happy path tests MUST assert on specific resource attributes, not just plan success
- `mock_provider` is required for plan-only tests -- do not rely on real AWS credentials
- IPAM components need `override_resource` to provide mock CIDR values since allocations happen at apply time

## Common Mistakes

| Mistake | Why It Happens | Correct Approach |
|---------|---------------|-----------------|
| Happy path test with zero assertions | Developer assumes "plan succeeds" is sufficient | Assert on specific resource attributes (count, CIDR, tags) |
| Missing `expect_failures` for validations | Validation blocks seem self-documenting | Every validation block needs an explicit negative test |
| Testing feature toggle in one state only | Enabled state is the default, so it "works" | Test both enabled and disabled; verify resource count is 0 when disabled |
| Hardcoding AZ names without mock | Tests fail in different regions | Use `override_data` on `data.aws_availability_zones` |
| Skipping CIDR overlap checks | Subnets "look right" in small configs | Use `distinct()` assertion to verify no CIDR overlap programmatically |
| No edge case for single AZ | Multi-AZ is the common path | Single-AZ is a valid deployment; test `az_count = 1` explicitly |

## Supporting Files

- `test-patterns.md` -- HCL code examples for each coverage dimension and mock_provider patterns
- `templates.md` -- Coverage assessment output template
