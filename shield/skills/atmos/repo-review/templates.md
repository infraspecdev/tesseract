# Output Templates

All outputs are written to the **target repository** (not the skill directory):

```
<repo-root>/
  claude/
    atmos-repo-review/
      analysis.md    # Review findings and grade (ALWAYS created)
      plan.md        # Implementation plan (ALWAYS created)
```

## analysis.md Template

```markdown
# Atmos Repository Analysis

**Repository:** [repo name]
**Date:** [date]
**Repo Type:** [components-only | stacks-only | monorepo]

## Context
[User-provided context from clarifying questions]

## Findings

### The Good
- [What's well-structured and why]

### The Bad
- [Structural issues, risks, anti-patterns]

### Improvements

**P0 (Critical):**
- [Must fix - blocks safe operation]

**P1 (Important):**
- [Should fix soon - affects scale/maintenance]

**P2 (Nice to have):**
- [Improvements for polish/optimization]

## Scores

| Criterion | Score | Notes |
|-----------|-------|-------|
| Atmos-native structure | X/5 | ... |
| Environment strategy | X/5 | ... |
| ... | | |

## Grade: [A-F]

**Justification:**
- [3-6 bullets tied to evaluation criteria]

**What would move to next grade:**
1. [Top change]
2. [Second change]
3. [Third change]
```

## plan.md Template

If no improvements needed:

```markdown
# Implementation Plan

**Based on:** analysis.md
**Current Grade:** A

## Status

No improvements required. Repository meets all best practices.

## Optional Enhancements
- [Any nice-to-have items]
```

Otherwise, write actionable steps:

```markdown
# Implementation Plan

**Based on:** analysis.md
**Target Grade:** [current] -> [target]

## Steps

### Step 1: [Title]
**Priority:** P0/P1/P2
**Files affected:**
- `path/to/file1`
- `path/to/file2`

**Actions:**
1. [Specific action]
2. [Specific action]

**Verification:**
- [ ] [How to verify this step is complete]

---

### Step 2: [Title]
...

## Execution Order
[Any dependencies between steps]

## Notes for Review
[Questions or alternatives for user consideration]
```

## Clarifying Questions (Phase 2)

**On first review:** Ask 10-15 questions grouped by category.
**On re-review:** Skip if context already known from conversation.

| Category | Example Questions |
|----------|------------------|
| **Architecture** | Consumer repo count, repo type intent, multi-repo strategy |
| **Scale** | AWS accounts, account strategy, multi-region needs |
| **Operations** | State backend, secrets management, version pinning |
| **Development** | Local testing, breaking change communication, target component count |
| **Governance** | Approval process, compliance requirements |

## User Confirmation Prompt

After writing both files, ask:

> "I've written the analysis (Grade: X) and plan (Y steps) to `claude/atmos-repo-review/`.
>
> Would you like me to:
> 1. **Proceed** with executing the plan
> 2. **Stop here** (you can review/edit files and resume later)
> 3. **Wait** while you edit plan.md, then continue"
