---
name: 02-json-sidecar-scope
skill_under_test: shield:writing-style
scenario: A doc that interleaves prose and a JSON sidecar — prose is tightened, JSON values stay byte-identical
---

## Setup
```bash
mkdir -p docs/shield/writing-style-test-02
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
# NOTE: BT3 is three literal backticks. We construct it via octal escapes so
# the eval parser does not see a nested triple-backtick fence in this block.
BT3=$'\140\140\140'
cat > docs/shield/writing-style-test-02/draft.md <<EOF
# Checkout SLO Update

It is basically the case that, due to the fact that the previous SLO was set in
a manner that was not aligned with current realities, we are of the opinion
that it is important to undertake an effort to revise the aforementioned SLO
in order to facilitate a more accurate target going forward. The Payments team
will be the team that owns this revision.

The new SLO definition is captured in the sidecar below.

${BT3}json
{
  "slo_name": "checkout_p95_latency_ms",
  "target_ms": 200,
  "previous_target_ms": 800,
  "owner_team": "Payments",
  "review_cadence_days": 30,
  "notes": "It is important to note that this is the agreed target."
}
${BT3}
EOF
```

## Prompt
> Apply the `shield:writing-style` skill to `docs/shield/writing-style-test-02/draft.md`. Write the tightened version to `docs/shield/writing-style-test-02/tightened.md`.
>
> **CRITICAL — code-block scope guard:** The draft contains a fenced ```json ... ``` code block. Your `tightened.md` MUST include that JSON block byte-for-byte identical to the input — same keys, values, quoting, indentation, and the same final fence. Copy it; do not rewrite, summarize, externalize, or drop it. Only the prose paragraphs around the JSON may be tightened. The JSON block is data, not prose. Preserve every fact exactly.

## Success criteria

### Structural (deterministic, bidirectional must-find)
- docs/shield/writing-style-test-02/tightened\.md
- "slo_name"\s*:\s*"checkout_p95_latency_ms"
- "target_ms"\s*:\s*200
- "previous_target_ms"\s*:\s*800
- "owner_team"\s*:\s*"Payments"
- "review_cadence_days"\s*:\s*30
- "notes"\s*:\s*"It is important to note that this is the agreed target."

### Qualitative (LLM-judged)
- The JSON code block is preserved byte-identical to the input — every key, value, quoting, and whitespace pattern. In particular, the `notes` field's "It is important to note" wording is intact.
- The author-written prose paragraphs OUTSIDE the JSON block are tightened — throat-clearing/filler removed (e.g. "basically", "due to the fact that", "aforementioned", "in order to facilitate").
- All facts are preserved across the doc: 200ms target, 800ms previous, Payments ownership, 30-day cadence.

## Pass threshold
7 of 7 structural + 2 of 3 qualitative.
