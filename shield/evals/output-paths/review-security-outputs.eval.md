---
name: review-security-outputs
skill_under_test: shield:review-security
scenario: /review-security writes summary.md and detailed/security-engineer.md under reviews/code/{date}/, not legacy code-review/{N}-{slug}/
---

## Setup
```bash
mkdir -p docs/shield/review-security-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p src
cat > src/main.tf <<'EOF'
resource "aws_s3_bucket" "example" { bucket = "test" }
EOF
```

## Prompt
> Follow the /review-security command's Output Path conventions to run a stub security review for a feature named "review-security-test-20260522". Do NOT actually dispatch the security-engineer agent — synthesize stub review content yourself (a placeholder summary noting one "B"-grade finding, plus one detailed/security-engineer.md file with a brief stub finding). Do NOT ask the user any questions. Write all outputs to the new flat-path layout — do NOT create numbered-run subfolders or any `code-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter`. If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "review-security-test-20260522".

## Success criteria

### Structural
- review-security-test-20260522/reviews/code/2026-05-22(_\d+)?/summary\.md
- review-security-test-20260522/reviews/code/2026-05-22(_\d+)?/detailed/security-engineer\.md

## Pass threshold
2 of 2 structural
