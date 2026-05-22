---
name: review-well-architected-outputs
skill_under_test: shield:review-well-architected
scenario: /review-well-architected writes summary.md and detailed/cloud-architect.md under reviews/code/{date}/, not legacy code-review/{N}-{slug}/
---

## Setup
```bash
mkdir -p docs/shield/review-wa-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p infra
cat > infra/main.tf <<'EOF'
resource "aws_lambda_function" "example" {
  function_name = "test"
  runtime       = "python3.11"
}
EOF
```

## Prompt
> Follow the /review-well-architected command's Output Path conventions to run a stub Well-Architected review for a feature named "review-wa-test-20260522". Do NOT actually dispatch the cloud-architect agent — synthesize stub review content yourself (a placeholder summary with all 6 pillar scores set to "B", plus one detailed/cloud-architect.md file with a brief stub). Do NOT ask the user any questions. Write all outputs to the new flat-path layout — do NOT create numbered-run subfolders or any `code-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter`. If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "review-wa-test-20260522".

## Success criteria

### Structural
- review-wa-test-20260522/reviews/code/2026-05-22
- summary\.md
- detailed/cloud-architect\.md

### Qualitative
- The agent wrote (or attempted to write) `summary.md` and `detailed/cloud-architect.md` under a path ending in `reviews/code/2026-05-22/` inside the `review-wa-test-20260522` feature folder.
- No legacy `code-review/{N}-<slug>/` folder pattern appears anywhere in the agent-written file paths or output narration.

## Pass threshold
3 of 3 structural + 2 of 2 qualitative
