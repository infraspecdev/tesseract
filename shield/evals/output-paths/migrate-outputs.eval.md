---
name: migrate-outputs
skill_under_test: shield:migrate
scenario: /shield migrate writes manifest.json and lands migrated artifacts at the new flat paths, not legacy plan/{N}-{slug}/ or plan-review/{N}-{slug}/
---

## Setup
```bash
mkdir -p shield/docs/plans
cat > shield/docs/plans/legacy-feature.json <<'EOF'
{
  "version": "1.0",
  "project": "legacy",
  "phase": "Legacy Phase",
  "epics": [{
    "id": "P1",
    "name": "Legacy epic",
    "stories": [{
      "id": "P1-S1",
      "name": "Legacy story",
      "status": "ready",
      "description": "stub",
      "tasks": ["task A"],
      "acceptance_criteria": ["AC A"]
    }]
  }]
}
EOF
```

## Prompt
> Follow the /shield migrate command's path conventions to migrate a stub legacy Shield v2.x plan at `shield/docs/plans/legacy-feature.json` into the new flat layout. Use feature name "legacy-feature-20260522" and `output_dir` = `docs/shield`. Do NOT ask the user any questions. Migrate the plan as follows: write `docs/shield/legacy-feature-20260522/plan.json` (the new flat-path target — registry key `{plan_json}`), and write `docs/shield/manifest.json` (registry key `{manifest}`) with a single entry for this feature. Do NOT create numbered-run subfolders (no `plan/{N}-{slug}/`, no `plan-review/{N}-{slug}/`). Do NOT actually write HTML; markdown sources and JSON are enough.

## Success criteria

### Structural
- legacy-feature-20260522/plan\.json

## Pass threshold
1 of 1 structural
