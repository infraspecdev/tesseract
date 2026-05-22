---
name: plan-review-outputs
skill_under_test: shield:plan-review
scenario: /plan-review writes summary.md, enhanced-plan.md, and detailed/<agent>.md to the new reviews/plan/{date}/ path, not legacy plan-review/{N}-{slug}/ subfolders
---

## Setup
```bash
mkdir -p docs/shield/plan-review-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/plan-review-test-20260522/plan.md <<'EOF'
# Plan: JWT migration

## Epic: Signing-key rotation
Goal: introduce JWTs signed with a rotating key.

### Story: Stand up KMS-backed signing key store
Tasks:
- [ ] Provision KMS key
- [ ] Wire signing path

Acceptance criteria:
- [ ] All tokens carry kid claim
EOF
cat > docs/shield/plan-review-test-20260522/plan.json <<'EOF'
{
  "schema_version": "1.0",
  "feature": "plan-review-test-20260522",
  "milestones": [],
  "epics": [
    {
      "id": "E1",
      "name": "Signing-key rotation",
      "stories": [
        {
          "id": "S1",
          "name": "Stand up KMS-backed signing key store",
          "milestone_id": null,
          "tasks": ["Provision KMS key", "Wire signing path"],
          "acceptance_criteria": ["All tokens carry kid claim"]
        }
      ]
    }
  ]
}
EOF
```

## Prompt
> Use the shield:plan-review skill to review the plan at `docs/shield/plan-review-test-20260522/plan.md` (sidecar at `plan.json`). Feature name is exactly "plan-review-test-20260522". Do NOT actually dispatch any reviewer subagents — synthesize stub review content yourself (a placeholder summary scoring everything "B", an enhanced-plan with one inline `<!-- [from: shield:architect] -->` comment, and one detailed/architect.md file with a brief stub). Do NOT ask the user any questions. Write all outputs using the path conventions defined in the skill's Output Path section — do NOT create numbered-run subfolders or any `plan-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter` (assume no prior same-day run). If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "plan-review-test-20260522".

## Success criteria

### Structural
- plan-review-test-20260522/reviews/plan/2026-05-22
- enhanced-plan\.md
- detailed/.*\.md

### Qualitative
- The agent wrote (or attempted to write) `summary.md`, `enhanced-plan.md`, and at least one `detailed/<agent>.md` file under a path ending in `reviews/plan/2026-05-22/` (or `reviews/plan/2026-05-22_2/` if same-day collision detected) inside the `plan-review-test-20260522` feature folder.
- No legacy `plan-review/{N}-<slug>/` folder pattern (e.g. `plan-review/1-jwt` or `plan-review/1-...`) appears anywhere in the agent-written file paths or output narration.

## Pass threshold
3 of 3 structural + 2 of 2 qualitative
