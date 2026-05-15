---
name: 01-terminologies-autofill
skill_under_test: shield:prd-docs
scenario: Authoring a PRD for a JWT auth rewrite, with research transcript containing a glossary
---

## Setup
```bash
mkdir -p docs/shield/auth-rewrite/research/1-discovery
mkdir -p .shield
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
cat > docs/shield/auth-rewrite/research/1-discovery/transcript.md <<'EOF'
# Auth rewrite — research

Context: legacy session-token auth being rewritten to JWT.

## Glossary
| Term | Definition |
|---|---|
| ICP | Ideal Customer Profile — companies with 50-500 employees. |
| PLG | Product-led growth — self-serve activation without sales. |

## Existing systems
Session tokens stored in Redis with 24h TTL. Refresh via /session/refresh.
EOF
```

## Prompt
> Author a standard PRD for "auth-rewrite" using the shield:prd-docs skill. Walk all sections; populate each with plausible content for rewriting legacy session-token auth to JWT. When prompted to confirm Terminologies, accept defaults. Output the final prd.md content only — do not write files.

## Success criteria

### Structural
- ## 2\. Terminologies
- \| ICP \| Ideal Customer Profile
- \| PLG \| Product-led growth
- (JWT|Session token|Refresh token|Token rotation|OAuth).*\|

### Qualitative
- The Terminologies table contains BOTH the research-glossary terms (ICP, PLG) AND at least 2 JWT/auth-specific terms proposed by the LLM scan.
- No Terminologies row's term is absent from the rest of the PRD body or the research transcript (no hallucinations).
- One-line definitions are factually accurate for the auth domain.

## Pass threshold
4 of 4 structural + 3 of 3 qualitative.
