---
name: 03-bluf-restructure
skill_under_test: shield:writing-style
scenario: A paragraph that buries the conclusion at the end is restructured BLUF (bottom-line-up-front) style — the decision sentence moves to the front
---

## Setup
```bash
mkdir -p docs/shield/writing-style-test-03
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/writing-style-test-03/draft.md <<'EOF'
# Index Rebuild Decision

Back in 2024 we initially provisioned the search index on a single-node
Elasticsearch cluster, which at the time was sized for roughly 10 million
documents and was adequate for our needs. Over the past 18 months, the
document count has grown to approximately 90 million, and query latency
has degraded from a p95 of 120ms in early 2025 to a p95 of 1,400ms today.
The engineering team has explored several remediations — shard rebalancing,
hot-tier caching, and selective denormalization — none of which moved the
needle by more than 10–15%. After weighing the options and consulting with
the Platform team, we have decided that we will rebuild the index on a
3-node OpenSearch cluster next quarter, owned by the Search team.
EOF
```

## Prompt
> Apply the `shield:writing-style` skill to `docs/shield/writing-style-test-03/draft.md`. Write the tightened version to `docs/shield/writing-style-test-03/tightened.md`. Preserve every fact (numbers, team names, dates) exactly. The skill calls for BLUF — bottom line up front — so lead with the decision.

## Success criteria

### Structural (deterministic, bidirectional must-find)
- docs/shield/writing-style-test-03/tightened\.md
- 90 ?(million|M\b|,000,000)
- 1,?400 ?ms
- 120 ?ms
- [Ss]earch team
- OpenSearch
- 3.node

### Qualitative (LLM-judged)
- The first sentence (or first 1–2 sentences) of the tightened body states the decision — rebuild on a 3-node OpenSearch cluster, owned by the Search team — BEFORE recounting the history. The original buries this decision at the end of the paragraph.
- The tightened version is materially shorter than the original while preserving all factual content (10M→90M growth, 120ms→1,400ms p95, the failed remediations, Platform consult, Search team ownership, next-quarter timing).
- The tightened version uses plain language and active voice rather than the original's narrative drift.

## Pass threshold
7 of 7 structural + 2 of 3 qualitative.
