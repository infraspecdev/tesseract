---
name: prd-review-outputs
skill_under_test: shield:prd-review
scenario: /prd-review writes summary.md and enhanced-prd.md to the new reviews/prd/{date}/ path, not legacy prd-review/{N}-{slug}/ subfolders
---

## Setup
```bash
mkdir -p docs/shield/prd-review-test-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/prd-review-test-20260522/prd.md <<'EOF'
# PRD: JWT migration

## 1. Problem
Legacy session tokens stored in Redis have inconsistent TTLs and cannot be
rotated independently per user.

## 2. Goal
Move to JWTs signed with a rotating key.

## 3. Stories
- As an authenticated user, I can stay logged in across pod restarts.
EOF
```

## Prompt
> Use the shield:prd-review skill to review the PRD at `docs/shield/prd-review-test-20260522/prd.md`. Feature name is exactly "prd-review-test-20260522". Do NOT actually dispatch the 13 reviewer agents — synthesize stub review content yourself (a placeholder summary scoring everything "B" and an enhanced PRD identical to the source with one `<!-- [from: pm-reviewer] -->` comment). Do NOT ask the user any questions; treat the PRD as standard type. Write all outputs using the path conventions defined in the skill's Output Path section — do NOT create numbered-run subfolders or any `prd-review/{N}-{slug}/` directory. Use today's date (2026-05-22) and an empty `_counter` (assume no prior same-day run). If `uv` or HTML rendering is unavailable, skip the `.html` files — just write the `.md` files. Feature name is exactly "prd-review-test-20260522".

## Success criteria

### Structural
- prd-review-test-20260522/reviews/prd/2026-05-22
- enhanced-prd\.md

### Qualitative
- The agent wrote (or attempted to write) `summary.md` and `enhanced-prd.md` under a path ending in `reviews/prd/2026-05-22/` (or `reviews/prd/2026-05-22_2/` if it detected a same-day collision) inside the `prd-review-test-20260522` feature folder.
- No legacy `prd-review/{N}-<slug>/` folder pattern (e.g. `prd-review/1-jwt` or `prd-review/1-...`) appears anywhere in the agent-written file paths or the output narration.

## Pass threshold
2 of 2 structural + 2 of 2 qualitative
