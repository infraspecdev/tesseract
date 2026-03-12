# Test Coverage Assessment Output Template

Use this template when producing the final coverage assessment.

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
