---
name: implement-outputs
skill_under_test: shield:implement-feature
scenario: /implement mutates {plan_json} in place; does not create new files under legacy plan/{N}-{slug}/ paths
---

## Setup
```bash
mkdir -p docs/shield/implement-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/implement-test-20260522/plan.json <<'EOF'
{
  "schema_version": "1.0",
  "feature": "implement-test-20260522",
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
> Follow the /implement command's path conventions for a feature named "implement-test-20260522". Do NOT actually execute any TDD workflow — synthesize a stub completion (mark story E1-S1 status as "done" in `docs/shield/implement-test-20260522/plan.json` and report that you would have written tests + implementation but skipped per instruction). Do NOT ask the user any questions. Do NOT create any new files outside of the existing `plan.json`. Do NOT create numbered-run subfolders or any `plan/{N}-{slug}/` directory. Feature name is exactly "implement-test-20260522".

## Success criteria

### Structural
- implement-test-20260522/plan\.json

### Qualitative
- The agent updated (or attempted to update) the existing `plan.json` at `docs/shield/implement-test-20260522/plan.json` — story status changed to "done" or similar.
- No legacy `plan/{N}-<slug>/` folder pattern appears anywhere in the agent-written file paths or output narration. The agent did not create any new files outside `plan.json`.

## Pass threshold
1 of 1 structural + 2 of 2 qualitative
