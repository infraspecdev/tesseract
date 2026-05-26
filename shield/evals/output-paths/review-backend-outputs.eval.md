---
name: review-backend-outputs
skill_under_test: shield:review-backend
scenario: /review-backend writes summary.md and detailed/backend-engineer.md under reviews/code/{date}/, not legacy code-review/{N}-{slug}/
---

## Setup
```bash
mkdir -p docs/shield/review-backend-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p src
cat > src/example.py <<'EOF'
def add(a, b): return a + b
EOF
```

## Prompt
> Follow the /review-backend command's Output Path conventions to run a stub backend code review for a feature named "review-backend-test-20260522". Do NOT actually dispatch the backend-engineer agent — synthesize stub review content yourself (a placeholder summary noting one "B"-grade finding, plus one detailed/backend-engineer.md file with a brief stub). Do NOT ask the user any questions. Write all outputs to the new flat-path layout — do NOT create numbered-run subfolders or any `code-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter`. If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "review-backend-test-20260522".

## Success criteria

### Structural
- review-backend-test-20260522/reviews/code/2026-05-22(_\d+)?/summary\.md
- review-backend-test-20260522/reviews/code/2026-05-22(_\d+)?/detailed/backend-engineer\.md

## Pass threshold
2 of 2 structural
