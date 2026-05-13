---
name: research
allowed-tools: Read, Write, Bash, Agent, Glob, Grep, WebFetch
description: Capture product + tech context for a new feature. Phase 1: Q&A walk with repo auto-detection. Phase 2 (optional): external evidence-gathering with citations.
---

# /research

Two-phase research command. Phase 1 captures internal context via Q&A + repo scan. Phase 2 (opt-in) runs external evidence-gathering on open questions.

## Usage

```
/research <topic>             # interactive — both phases offered
/research --lean <topic>      # use lean depth mode (5 topics only)
/research --deep <topic>      # use deep depth mode (~15 topics)
/research --phase2-only       # skip Phase 1, run only external evidence-gathering (legacy behavior)
```

## What it does

### Phase 1 (new)

1. **Silent repo scan** — detects Stack, Integrations, Compliance markers, Deployment pattern, Recent activity, ADRs, Prior research artifacts
2. **Confirm detected context with user** — yes / no / correct / add
3. **Q&A walk** — asks product + tech topics, skipping any auto-answered from invocation message, repo scan, or prior transcript
4. **Surface open questions** + offer Phase 2

### Phase 2 (existing — opt-in after Phase 1)

5. **PM framing** on chosen questions
6. **3 parallel agents** — official sources, industry voices, community experience
7. **Synthesize** with citations
8. **PM review** on synthesis
9. **Write `findings.md`** with sourced evidence

## Output

```
{output_dir}/{feature}/research/{N}-{slug}/
├── transcript.md           # always present
└── findings.md             # only if Phase 2 ran
```

## Reference

Full behavior in `shield/skills/general/research/SKILL.md`. See `repo-scan.md` for detection rules and `qa-topics.md` for the topic catalog.

## See also

- `/prd` — author a PRD informed by this research
- `/prd-review` — review an existing PRD
- `/plan` — generate a technical plan
