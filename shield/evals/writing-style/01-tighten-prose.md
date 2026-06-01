---
name: 01-tighten-prose
skill_under_test: shield:writing-style
scenario: Bloated PRD prose is tightened — filler cut, facts preserved, output written to a file
---

## Setup
```bash
mkdir -p docs/shield/writing-style-test
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/writing-style-test/draft.md <<'EOF'
# Checkout Latency Problem

It is important to note that, at the end of the day, the checkout flow is
currently experiencing what can only be described as a situation where the
performance is not where we would ideally like it to be. Basically, due to the
fact that the p95 latency is currently sitting at around 800ms, there is a real
and genuine possibility that users may potentially decide to abandon their carts.
We are of the firm belief that we should endeavour to undertake an initiative in
order to facilitate the reduction of the aforementioned p95 latency down to a
target of 200ms. The team responsible for this, which is the Payments team, will
be the ones who are going to be owning this particular piece of work going forward.
EOF
```

## Prompt
> Apply the `shield:writing-style` skill to `docs/shield/writing-style-test/draft.md`. Write the tightened version to `docs/shield/writing-style-test/tightened.md`. Preserve every fact (numbers, team names, targets) exactly; only improve the writing.

## Success criteria

### Structural (deterministic, bidirectional must-find)
- docs/shield/writing-style-test/tightened\.md
- 800ms
- 200ms
- [Pp]ayments

### Qualitative (LLM-judged)
- The tightened version removes throat-clearing/filler present in the original (e.g. "It is important to note", "at the end of the day", "due to the fact that", "aforementioned").
- The tightened version is materially shorter than the original while preserving all factual content (the 800ms→200ms p95 target and Payments ownership).
- The tightened version uses plain language and active voice rather than the original's hedged, passive phrasing.

## Pass threshold
4 of 4 structural + 2 of 3 qualitative.
