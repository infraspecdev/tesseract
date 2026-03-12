# infra-review Skills Evaluation (writing-skills checklist)

**Date:** 2026-03-12
**Evaluator:** writing-skills superpowers skill
**Skills evaluated:** 7

## Summary

| Skill | Words | Description CSO | Structure | Token Efficiency | Verdict |
|-------|-------|----------------|-----------|-----------------|---------|
| atmos-repo-review | 1700 | PASS | PASS | FAIL (3.4x over) | Needs extraction |
| github-actions-reviewer | 1603 | PASS | PASS | FAIL (3.2x over) | Needs extraction |
| terraform-plan-analyzer | 1518 | PASS | PASS | FAIL (3x over) | Needs extraction |
| terraform-security-audit | 1088 | PASS | PASS | FAIL (2.2x over) | Needs extraction |
| terraform-test-coverage | 1024 | PASS | PASS | FAIL (2x over) | Needs extraction |
| terraform-cost-review | 915 | PASS | PASS | FAIL (1.8x over) | Borderline |
| atmos-component-hygiene | 817 | PASS | PASS | FAIL (1.6x over) | Borderline |

---

## Per-Skill Evaluation

### 1. atmos-repo-review (1700 words)

**Frontmatter:**
- Name: `atmos-repo-review` — letters and hyphens only. PASS
- Description: `Use when reviewing Atmos infrastructure repositories...` — starts with "Use when", no workflow summary. PASS

**CSO:**
- Keywords: Atmos, IaC, Terraform, OpenTofu, stacks, components. PASS
- Naming: descriptive, active. PASS

**Structure:**
- Overview with core principle. PASS
- When to Use. PASS
- Flowchart for non-obvious workflow (8-phase). PASS
- Critical Rules section. PASS
- Grading Scale, Red Flags, Quick Reference. PASS
- When NOT to Use: MISSING

**Token Efficiency: FAIL**
- 1700 words — 3.4x over the 500-word target
- **Output templates** (analysis.md format, plan.md format): ~300 words. Should extract to `templates.md`
- **Red Flags section**: ~250 words of reference material. Should extract to `red-flags.md` or keep lean
- **Phase descriptions** are detailed but could reference supporting files for heavy content
- **Provider/backend file table**: 100+ words of reference. Could extract

**Missing:**
- When NOT to Use section
- Common Mistakes section (Red Flags is close but different)

---

### 2. github-actions-reviewer (1603 words)

**Frontmatter:**
- Name: `github-actions-reviewer` — PASS
- Description: `Use when reviewing, auditing, or improving GitHub Actions workflows...` — starts with "Use when", lists specific symptoms. PASS

**Structure:**
- Overview with core principle ("workflows form a system"). PASS
- When to Use. PASS
- Flowchart. PASS
- Critical Rules. PASS
- Grading Scale. PASS
- When NOT to Use: MISSING
- Common Mistakes: MISSING

**Token Efficiency: FAIL**
- 1603 words — 3.2x over target
- **Checklist sections** (8 checks with YAML examples): ~600 words. This is heavy reference — extract to `checklist.md`
- **Output templates**: ~250 words. Extract to `templates.md`
- **Concurrency YAML examples**: ~100 words inline. Could reference

---

### 3. terraform-plan-analyzer (1518 words)

**Frontmatter:**
- Name: `terraform-plan-analyzer` — PASS
- Description: `Use when analyzing Terraform plan output for security, cost, and operational impact...` — PASS, includes specific symptoms (destructive changes, IAM modifications, drift)

**Structure:**
- Overview with core principle ("Review the plan, not just the code"). PASS
- When to Use. PASS
- Prerequisites section. PASS
- Flowchart for plan source detection. PASS
- Critical Rules. PASS
- When NOT to Use: MISSING
- Common Mistakes: MISSING

**Token Efficiency: FAIL**
- 1518 words — 3x over target
- **Resource risk tables** (destructive actions, security-sensitive, cost-impacting): ~400 words. These are heavy reference — extract to `resource-tables.md`
- **Report template**: ~250 words. Extract to `templates.md`
- **JSON parsing reference** (Phase 2): ~150 words. Extract

---

### 4. terraform-security-audit (1088 words)

**Frontmatter:**
- Name: `terraform-security-audit` — PASS
- Description: `Use when auditing Terraform code for security vulnerabilities...` — PASS

**Structure:**
- Overview explaining what it catches beyond Checkov. PASS
- When to Use. PASS
- 4 audit dimensions with tables. PASS
- Output format template. PASS
- Common False Negatives table. PASS (this IS a Common Mistakes equivalent)
- When NOT to Use: MISSING
- Flowchart: MISSING (could benefit from one showing audit order)

**Token Efficiency: FAIL**
- 1088 words — 2.2x over target
- **Audit dimension tables**: ~400 words of reference. Extract to `audit-dimensions.md`
- **Report template**: ~150 words. Extract

---

### 5. terraform-test-coverage (1024 words)

**Frontmatter:**
- Name: `terraform-test-coverage` — PASS
- Description: `Use when reviewing Terraform test files (.tftest.hcl)...` — PASS, technology-specific trigger

**Structure:**
- Overview. PASS
- When to Use. PASS
- 6 coverage dimensions with code patterns. PASS
- Coverage assessment output. PASS
- When NOT to Use: MISSING
- Common Mistakes: MISSING
- Flowchart: MISSING

**Token Efficiency: FAIL**
- 1024 words — 2x over target
- **HCL code examples**: ~400 words (6 patterns). These are the skill's core value but could extract to `test-patterns.hcl` as a reference file
- **Output template**: ~100 words. Could extract

---

### 6. terraform-cost-review (915 words)

**Frontmatter:**
- Name: `terraform-cost-review` — PASS
- Description: `Use when reviewing Terraform components for AWS cost optimization...` — PASS

**Structure:**
- Overview. PASS
- When to Use. PASS
- 3-step analysis process. PASS
- Common Cost Traps table. PASS (serves as Common Mistakes)
- Output format. PASS
- Estimation methodology with pricing table. PASS
- When NOT to Use: MISSING
- Flowchart: MISSING

**Token Efficiency: FAIL (borderline)**
- 915 words — 1.8x over target
- **Report template**: ~150 words. Extract
- **Pricing table**: ~100 words of reference. Could extract
- This skill is close to acceptable if templates are extracted

---

### 7. atmos-component-hygiene (817 words)

**Frontmatter:**
- Name: `atmos-component-hygiene` — PASS
- Description: `Use when adding, modifying, or reviewing Terraform components...` — PASS, includes specific symptoms (committed provider.tf, missing terraform-docs)

**Structure:**
- Overview. PASS
- When to Use. PASS
- Check tables (R1-R8, C1-C10) with severity. PASS
- Flowchart for check flow. PASS
- Output format. PASS
- Common Mistakes table. PASS
- When NOT to Use: MISSING

**Token Efficiency: FAIL (borderline)**
- 817 words — 1.6x over target
- **Output format example**: ~50 words. Acceptable inline
- This is the closest to target and mostly acceptable

---

## Cross-Cutting Issues

### 1. All skills exceed 500-word target
Every skill is 1.6x-3.4x over. The main offenders are:
- **Output/report templates** (analysis.md, plan.md formats) — present in 5/7 skills
- **Reference tables** (resource lists, cost tables, check tables) — present in all skills
- **Code examples** (YAML, HCL) — present in 4/7 skills

**Fix:** Extract templates and heavy reference to supporting files. Keep SKILL.md focused on decision-making and process.

### 2. No "When NOT to Use" section in any skill
All 7 skills are missing this. This matters for persona dispatch — agents need to know when to skip.

### 3. No Iron Law testing
None of the skills have documented baseline or GREEN test results. Per writing-skills Iron Law: "No skill without a failing test first."

### 4. Consistent good patterns across all skills
- All descriptions start with "Use when..." — CSO compliant
- All descriptions avoid workflow summary — CSO compliant
- All have clear overview with core principle
- All use structured tables for checklists
- Consistent grading scales (A-F) across review skills
- All have user confirmation gates before execution

---

## Priority Recommendations

### P0 — Must Fix
1. **Extract templates/reference to supporting files** for all skills exceeding 1000 words. Target: SKILL.md under 500 words, heavy reference in separate files.

### P1 — Should Fix
2. **Add "When NOT to Use" section** to all 7 skills
3. **Run Iron Law baseline tests** on at least the 3 most-used skills (atmos-repo-review, atmos-component-hygiene, terraform-plan-analyzer)

### P2 — Nice to Have
4. **Add Common Mistakes section** to skills missing it (terraform-plan-analyzer, github-actions-reviewer, terraform-test-coverage)
5. **Add flowcharts** to skills with non-obvious decision points (terraform-security-audit audit order, terraform-test-coverage dimension selection)
