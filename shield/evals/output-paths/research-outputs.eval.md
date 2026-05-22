---
name: research-outputs
skill_under_test: shield:research
scenario: /research writes findings to the new flat {research} path, not legacy numbered-run subfolders
---

## Setup
```bash
mkdir -p docs/shield
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
```

## Prompt
> Use the shield:research skill to capture research for a feature named "auth-rewrite-test-20260522". Use minimal placeholder context: topic is "JWT migration feasibility", prior context is "legacy session-token auth stored in Redis with 24h TTL". Skip interactive Q&A — treat the provided context as the complete Phase 1 answers. Run through Phase 2 with stub findings (no real web search needed — synthesize from the provided context). Write all outputs using the path conventions defined in the skill — do NOT improvise paths or create numbered-run subfolders. Feature name is exactly "auth-rewrite-test-20260522".

## Success criteria

### Structural
- auth-rewrite-test-20260522/research\.md
- session-transcript

### Qualitative
- The agent wrote (or attempted to write) a file at a path ending in `auth-rewrite-test-20260522/research.md` — NOT under any `research/{N}-<slug>/` numbered subfolder.
- No numbered-run folder pattern (e.g. `research/1-jwt` or `research/1-...`) appears in the agent-written file paths or output narration.

## Pass threshold
2 of 2 structural + 2 of 2 qualitative
