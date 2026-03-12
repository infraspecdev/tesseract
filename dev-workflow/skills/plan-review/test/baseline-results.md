# Baseline Test Results (WITHOUT plan-review skill)

**Date:** 2026-03-12
**Test:** Ask agent to review a deliberately weak plan document under time pressure ("sprint starts tomorrow")
**Plan:** test-plan.md (API Gateway migration with vague criteria, missing security/cost/rollback)

## What the Agent Did Well (Natural Behavior)

1. Identified vague acceptance criteria ("works", "acceptable")
2. Called out missing rollback plan
3. Noticed missing load testing and WAF considerations
4. Flagged timeline risk
5. Provided actionable recommendations with priorities (High/Medium/Low)
6. Good depth on architecture gaps (TLS, custom domains, API type choice)

## What the Agent Did NOT Do (Failures Without Skill)

### F1: No structured evaluation framework
- Organized by ad-hoc categories ("Architecture Gaps", "Stories Too Vague", "Missing Stories")
- No consistent checklist or evaluation points — different review would produce different categories
- No repeatability — another agent reviewing the same plan would organize differently

### F2: No scoring or grading
- Used "High/Medium/Low" priority but no systematic grade per evaluation point
- No composite readiness score — no clear "is this plan ready or not?" verdict
- No numeric scoring that enables comparison across reviews

### F3: No multi-persona perspective
- Single generalist review — caught infra and story quality issues
- **Missed entirely:** cost analysis (Kong EC2 vs API Gateway pricing), FinOps concerns
- **Missed entirely:** sprint-readiness assessment (story sizing, dependency ordering, parallelism)
- **Missed entirely:** formal security threat model (JWT key management, token revocation attack surface)
- Security was mentioned briefly (WAF) but not systematically evaluated

### F4: No output artifacts
- Gave review inline as conversation text
- No `analysis.md` or `plan.md` written to disk
- No enhanced version of the plan with fixes applied
- Review is lost when conversation ends

### F5: No user review gate
- Delivered review and immediately suggested actions ("spend a few hours today")
- Did not ask user to review, edit, or approve before proceeding
- Would likely start implementing fixes if asked "go ahead"

### F6: No separation of concerns
- One monolithic review mixing infrastructure, story quality, security, and process concerns
- A specialist (e.g., security engineer) reading this review can't quickly find their section
- No per-persona breakdown enables delegation

### F7: Succumbed to time pressure
- Accepted "sprint starts tomorrow" framing without questioning it
- Suggested "spend a few hours today" as remediation — compressed timeline
- Did not flag that the plan needs fundamental rework, not polish

## Rationalizations Observed

| Rationalization | What Happened |
|----------------|---------------|
| "I'll cover everything in one pass" | Missed cost, sprint-readiness, and formal security |
| "High/Medium/Low is good enough" | No numeric scoring prevents comparison or threshold-based verdicts |
| "The review itself is the output" | No files written — review is ephemeral conversation text |
| "Time pressure means faster review" | Accepted urgency framing, didn't push back on timeline |

## Key Gaps the Skill Must Fix

1. **Structured multi-persona evaluation** — force different lenses (infra, security, DX, cost, agile)
2. **Systematic scoring** — grade per evaluation point, composite readiness verdict
3. **Output artifacts** — analysis.md + enhanced plan.md written to disk
4. **User review gate** — explicit confirmation before applying any changes
5. **Resist time pressure** — the skill's process runs regardless of stated urgency
