---
name: 01-tighten-prose
skill_under_test: shield:writing-style
scenario: Bloated PRD prose is tightened, but a marker-wrapped rendered region inside the doc is preserved byte-identical (scope guard)
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

## Milestones

<!-- BEGIN rendered:milestones -->
| Milestone | Description |
|---|---|
| M1 | It is important to note that this milestone delivers the foundational data model and basically establishes the schema |
| M2 | Due to the fact that M1 is complete, this milestone facilitates downstream integration in order to enable rollout |
<!-- END rendered:milestones -->
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
- <!-- BEGIN rendered:milestones -->
- <!-- END rendered:milestones -->
- It is important to note that this milestone delivers the foundational data model and basically establishes the schema
- Due to the fact that M1 is complete, this milestone facilitates downstream integration in order to enable rollout

### Qualitative (LLM-judged)
- The prose OUTSIDE the `<!-- BEGIN rendered:milestones -->`/`<!-- END rendered:milestones -->` markers has been tightened — throat-clearing/filler removed (e.g. "It is important to note", "at the end of the day", "due to the fact that", "aforementioned") and phrasing made active/plain.
- The content INSIDE the `<!-- BEGIN rendered:milestones -->` / `<!-- END rendered:milestones -->` markers is preserved byte-identical to the input — including the stilted phrases "It is important to note", "basically", "Due to the fact that", "in order to". The markers themselves are unchanged.
- All facts are preserved across the doc: 800ms, 200ms, Payments team ownership, the M1 and M2 milestone descriptions.

## Pass threshold
8 of 8 structural + 2 of 3 qualitative.
