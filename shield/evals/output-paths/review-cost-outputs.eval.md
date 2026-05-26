---
name: review-cost-outputs
skill_under_test: shield:review-cost
scenario: /review-cost writes summary.md and detailed/finops-analyst.md under reviews/code/{date}/, not legacy code-review/{N}-{slug}/
---

## Setup
```bash
mkdir -p docs/shield/review-cost-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p src
cat > src/main.tf <<'EOF'
resource "aws_instance" "example" { instance_type = "m5.xlarge" }
EOF
```

## Prompt
> Follow the /review-cost command's Output Path conventions to run a stub cost review for a feature named "review-cost-test-20260522". Do NOT actually dispatch any reviewer subagents — synthesize stub review content yourself (a placeholder summary noting one "B"-grade cost finding, plus one detailed/finops-analyst.md file with a brief stub finding). Do NOT ask the user any questions. Write all outputs to the new flat-path layout — do NOT create numbered-run subfolders or any `code-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter`. If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "review-cost-test-20260522".

## Success criteria

### Structural
- review-cost-test-20260522/reviews/code/2026-05-22(_\d+)?/summary\.md
- review-cost-test-20260522/reviews/code/2026-05-22(_\d+)?/detailed/finops-analyst\.md

## Pass threshold
2 of 2 structural
