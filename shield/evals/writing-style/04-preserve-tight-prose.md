---
name: 04-preserve-tight-prose
skill_under_test: shield:writing-style
scenario: Already-tight prose is not over-compressed into cryptic shorthand — the skill leaves good writing alone
---

## Setup
```bash
mkdir -p docs/shield/writing-style-test-04
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/writing-style-test-04/draft.md <<'EOF'
# Webhook Retry Policy

The Payments team owns webhook delivery. We retry failed deliveries up to
5 times with exponential backoff starting at 2 seconds. After the 5th
failure, the event is moved to a dead-letter queue and an alert fires to
the on-call channel. Successful deliveries are logged with a 7-day
retention window.
EOF
```

## Prompt
> Apply the `shield:writing-style` skill to `docs/shield/writing-style-test-04/draft.md`. Write the tightened version to `docs/shield/writing-style-test-04/tightened.md`. Preserve every fact exactly. Note: the source is already concise — the skill warns against over-compressing into cryptic shorthand, so leave well-written prose alone.

## Success criteria

### Structural (deterministic, bidirectional must-find)
- docs/shield/writing-style-test-04/tightened\.md
- [Pp]ayments
- 5 times
- exponential backoff
- 2 seconds
- dead-letter queue
- on-call
- 7-day

### Qualitative (LLM-judged)
- Every fact from the original is present in the tightened version: Payments ownership, 5 retries, exponential backoff starting at 2 seconds, dead-letter queue, on-call alert, 7-day retention. No information was dropped in the name of brevity.
- The tightened version is NOT materially shorter than the input, and it does NOT collapse into telegraphic shorthand like "5x retry, exp backoff 2s, DLQ + page" — the skill explicitly warns that "Concise ≠ terse-to-the-point-of-unclear."
- Sentences remain readable as full English (subject + verb + object). The prose is recognizable as a paragraph, not a bullet list of fragments.

## Pass threshold
8 of 8 structural + 2 of 3 qualitative.
