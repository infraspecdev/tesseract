# GitHub Actions Reviewer — Output Templates

## Output Location

All outputs written to **target repository** (not skill directory):

```
<repo-root>/
  claude/
    github-actions-review/
      analysis.md    # Review findings and grade (ALWAYS created)
      plan.md        # Implementation plan (ALWAYS created)
```

## analysis.md Template

```markdown
# GitHub Actions Review

**Repository:** [repo name]
**Date:** [date]
**Workflows reviewed:** [count]

## Workflow Inventory

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `name.yaml` | PR / push / workflow_call | Brief description |

## Findings

### Must Fix
- [Issues causing incorrect behavior, security risks, or CI failures]

### Should Fix
- [Inconsistencies that increase maintenance burden]

### Nice to Have
- [Polish items for developer experience]

## Checklist Results

| Check | Status | Notes |
|-------|--------|-------|
| Version consistency | Pass/Fail | ... |
| Plugin alignment | Pass/Fail | ... |
| Permissions | Pass/Fail | ... |
| Concurrency control | Pass/Fail | ... |
| Path filters | Pass/Fail | ... |
| Reusable workflows | Pass/Fail | ... |
| Action pinning | Pass/Fail | ... |
| Secrets handling | Pass/Fail | ... |

## Grade: [A-F]

**Justification:**
- [Bullets tied to checklist results]

**What would move to next grade:**
1. [Top improvement]
2. [Second improvement]
```

## plan.md Template

**If no improvements needed:**

```markdown
# Implementation Plan

**Based on:** analysis.md
**Current Grade:** A

## Status

No improvements required. All workflows pass review checklist.

## Optional Enhancements
- [Any nice-to-have items]
```

**If improvements exist:**

```markdown
# Implementation Plan

**Based on:** analysis.md
**Target Grade:** [current] -> [target]

## Steps

### Step 1: [Title]
**Severity:** Must Fix / Should Fix / Nice to Have
**Files affected:**
- `.github/workflows/file.yaml`

**Actions:**
1. [Specific action]
2. [Specific action]

**Verification:**
- [ ] [How to verify this step is complete]

---

### Step 2: [Title]
...

## Notes
[Context for user, questions, or alternatives]
```
