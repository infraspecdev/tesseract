---
name: analyze-plan-outputs
skill_under_test: shield:analyze-plan
scenario: /analyze-plan writes summary.md under reviews/code/{date}/, not into a legacy or improvised subfolder
---

## Setup
```bash
mkdir -p docs/shield/analyze-plan-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p infra
cat > infra/tfplan.json <<'EOF'
{
  "resource_changes": [
    {
      "address": "aws_instance.example",
      "type": "aws_instance",
      "change": { "actions": ["create"] }
    }
  ]
}
EOF
```

## Prompt
> Follow the /analyze-plan command's Paths conventions to analyze the Terraform plan at `infra/tfplan.json` for a feature named "analyze-plan-test-20260522". Do NOT actually invoke the terraform plan-analysis skill — synthesize stub analysis content yourself (a placeholder summary noting one resource being created, no destructive actions). Do NOT ask the user any questions. Write `summary.md` to the new flat-path layout under `reviews/code/{date}/` — do NOT create numbered-run or improvised subfolders. Use today's date (2026-05-22) and an empty `_counter`. If `uv` or HTML rendering is unavailable, skip the `.html` file — just write `summary.md`. Feature name is exactly "analyze-plan-test-20260522".

## Success criteria

### Structural
- analyze-plan-test-20260522/reviews/code/2026-05-22/summary\.md

## Pass threshold
1 of 1 structural
