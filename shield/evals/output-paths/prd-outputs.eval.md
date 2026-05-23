---
name: prd-outputs
skill_under_test: shield:prd-docs
scenario: /prd writes prd.md to the new flat {prd} path, not legacy numbered-run subfolders
---

## Setup
```bash
mkdir -p docs/shield
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
mkdir -p docs/shield/prd-test-20260522
cat > docs/shield/prd-test-20260522/.session-transcript.md <<'EOF'
# Research Transcript — prd-test-20260522

## Summary
JWT migration feasibility study.

## Glossary
| Term | Definition |
|---|---|
| JWT | JSON Web Token — stateless bearer token used for API auth |
| TTL | Time To Live — expiry duration for a token or cache entry |
EOF
```

## Prompt
> Use the shield:prd-docs skill to author a lean PRD (10 sections) for a feature named "prd-test-20260522". Use placeholder content throughout — do not ask the user questions, synthesize reasonable placeholder answers for every section. Use lean type (10 sections). Feature name is exactly "prd-test-20260522". Write all outputs using the path conventions defined in the skill — do NOT create numbered-run subfolders or any prd/{N}-{slug}/ directory. Write prd.md directly into the feature folder. If uv is unavailable, skip prd.html rendering — just write prd.md and prd.meta.json. Feature name is exactly "prd-test-20260522".

## Success criteria

### Structural
- prd-test-20260522/prd\.md

## Pass threshold
1 of 1 structural
