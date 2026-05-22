---
name: review-outputs
skill_under_test: shield:review
scenario: /review writes summary.md and detailed/<agent>.md to the new reviews/code/{date}/ path, not legacy code-review/{N}-{slug}/ subfolders
---

## Setup
```bash
mkdir -p docs/shield/review-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
# Create a tiny stub source file so /review has something to review
mkdir -p src
cat > src/example.py <<'EOF'
def add(a, b):
    return a + b
EOF
```

## Prompt
> Use the shield:review skill (or follow the /review command's behavior) to run a stub code review for a feature named "review-test-20260522". Do NOT actually dispatch any reviewer subagents — synthesize stub review content yourself (a placeholder summary noting one "B"-grade finding, and one detailed/backend-engineer.md file with a brief stub finding). Do NOT ask the user any questions. Write all outputs using the path conventions defined in the /review command's Output Path section — do NOT create numbered-run subfolders or any `code-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter` (assume no prior same-day run). If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "review-test-20260522".

## Success criteria

### Structural
- review-test-20260522/reviews/code/2026-05-22
- summary\.md
- detailed/.*\.md

### Qualitative
- The agent wrote (or attempted to write) `summary.md` and at least one `detailed/<agent>.md` file under a path ending in `reviews/code/2026-05-22/` (or `reviews/code/2026-05-22_2/` if same-day collision detected) inside the `review-test-20260522` feature folder.
- No legacy `code-review/{N}-<slug>/` folder pattern (e.g. `code-review/1-branch` or `code-review/1-...`) appears anywhere in the agent-written file paths or output narration.

## Pass threshold
3 of 3 structural + 2 of 2 qualitative
