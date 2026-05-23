---
name: pm-sync-outputs
skill_under_test: shield:pm-sync
scenario: /pm-sync mutates {plan_json} in place; does not create new files under legacy plan/{N}-{slug}/ paths
---

## Setup
```bash
mkdir -p docs/shield/pm-sync-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/pm-sync-test-20260522/plan.json <<'EOF'
{
  "schema_version": "1.0",
  "feature": "pm-sync-test-20260522",
  "milestones": [],
  "epics": [
    {
      "id": "E1",
      "name": "Stub epic",
      "stories": [
        {
          "id": "E1-S1",
          "name": "Stub story",
          "status": "ready",
          "milestone_id": null,
          "tasks": ["Trivial task"],
          "acceptance_criteria": ["Trivial AC"]
        }
      ]
    }
  ]
}
EOF
```

## Prompt
> Follow the /pm-sync command's path conventions for a feature named "pm-sync-test-20260522". Do NOT actually call any PM adapter MCP tools (no pm_get_capabilities, no pm_sync, no pm_bulk_*) — synthesize a stub sync result (add a placeholder `pm_id: "FAKE-001"` and `pm_url: "https://example.invalid/FAKE-001"` to story E1-S1 in `docs/shield/pm-sync-test-20260522/plan.json`). Do NOT ask the user any questions. Do NOT create any new files outside of the existing `plan.json`. Do NOT create numbered-run subfolders or any `plan/{N}-{slug}/` directory. Feature name is exactly "pm-sync-test-20260522".

## Success criteria

### Structural
- pm-sync-test-20260522/plan\.json

## Pass threshold
1 of 1 structural
