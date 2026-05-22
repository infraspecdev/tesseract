---
name: plan-outputs
skill_under_test: shield:plan-docs
scenario: /plan writes plan.json, plan.md, and plan-architecture.md flat at feature root (plus rendered HTML under outputs/), not into legacy plan/{N}-{slug}/ subfolders
---

## Setup
```bash
mkdir -p docs/shield/plan-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/plan-test-20260522/prd.md <<'EOF'
# PRD: JWT migration

## 1. Problem
Legacy session tokens stored in Redis have inconsistent TTLs and cannot be
rotated independently per user.

## 8. Stories
- As an authenticated user, I can stay logged in across pod restarts.

## 15. Milestones
- M1: signing key rotation in place
EOF
cat > docs/shield/plan-test-20260522/prd.meta.json <<'EOF'
{
  "schema_version": "1.0",
  "type": "standard",
  "status": "Draft",
  "owner": "@test",
  "date_created": "2026-05-22",
  "last_updated": "2026-05-22",
  "rubric_version": "1.2",
  "sections_present": [1, 8, 15],
  "sections_missing_from_standard": [],
  "linked_research": null,
  "linked_design_spec": null,
  "linked_plans": []
}
EOF
```

## Prompt
> Use the shield:plan-docs skill to generate a plan for a feature named "plan-test-20260522". A PRD already exists at `docs/shield/plan-test-20260522/prd.md` — use it as authoritative context. Use placeholder content throughout — do not ask the user questions, synthesize reasonable placeholder answers (one milestone, one epic, one story with two acceptance criteria). Write all outputs using the path conventions defined in the skill's Output Paths section — do NOT create numbered-run subfolders or any `plan/{N}-{slug}/` directory. The plan.json sidecar goes at the feature root; plan.md and plan-architecture.md are the canonical markdown sources at feature root; rendered HTML goes under `outputs/`. If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the three source files (plan.json, plan.md, plan-architecture.md). Feature name is exactly "plan-test-20260522".

## Success criteria

### Structural
- plan-test-20260522/plan\.json
- plan-test-20260522/plan\.md
- plan-test-20260522/plan-architecture\.md

### Qualitative
- The agent wrote (or attempted to write) `plan.json`, `plan.md`, and `plan-architecture.md` flat at the feature root `docs/shield/plan-test-20260522/` — NOT under any `plan/{N}-<slug>/` numbered subfolder.
- No numbered-run folder pattern (e.g. `plan/1-foundation` or `plan/1-...`) appears in the agent-written file paths or output narration.

## Pass threshold
3 of 3 structural + 2 of 2 qualitative
