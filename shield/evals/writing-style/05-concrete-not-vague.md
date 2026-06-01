---
name: 05-concrete-not-vague
skill_under_test: shield:writing-style
scenario: A draft with vague claims AND a nearby data block — the tightened version replaces the vague claims with the concrete numbers from the data block
---

## Setup
```bash
mkdir -p docs/shield/writing-style-test-05
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/writing-style-test-05/draft.md <<'EOF'
# API Gateway Rollout

The new API gateway has improved performance significantly. Performance is now
much better than before. Users will have a faster experience going forward,
and the team believes this will deliver real cost savings.

The data behind these claims:

- p95 latency before: 2.1s
- p95 latency after: 380ms
- Cost per request before: $0.018
- Cost per request after: $0.004
- Owner: Platform team
EOF
```

## Prompt
> Apply the `shield:writing-style` skill to `docs/shield/writing-style-test-05/draft.md`. Write the tightened version to `docs/shield/writing-style-test-05/tightened.md`. The skill's principle #4 ("Concrete & specific") calls for replacing vague claims like "improved significantly" with the specific numbers/names available in the doc. Preserve every fact exactly.

## Success criteria

### Structural (deterministic, bidirectional must-find)
- docs/shield/writing-style-test-05/tightened\.md
- 2\.1 ?s
- 380 ?ms
- \$0\.018
- \$0\.004
- Platform team

### Qualitative (LLM-judged)
- The vague claims in the original ("improved performance significantly", "much better than before", "faster experience", "real cost savings") have been REPLACED in the tightened prose with the specific numbers and names from the data block — not merely paraphrased.
- The concrete numbers (2.1s → 380ms, $0.018 → $0.004) appear in the prose itself, not only in a separate list, so a reader sees them in context.
- All facts are preserved across the doc: 2.1s, 380ms, $0.018, $0.004, Platform team ownership.

## Pass threshold
5 of 5 structural + 2 of 3 qualitative.
