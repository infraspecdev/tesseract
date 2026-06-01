---
name: writing-style
description: Use when authoring or revising any Shield doc — research, PRD, TRD/plan, LLD — to make author-written prose simple, clear, concise, and to the point. Applies to prose only; never rewrites rendered/marker-wrapped sections or JSON.
---

# Writing Style

Make Shield doc prose simple, clear, concise, and to the point. This is the
single source of truth for "what good Shield prose looks like." Doc-authoring
skills apply it to author-written prose before writing the doc out.

## Scope — prose only

Apply to **author-written prose**: problem statements, summaries, narrative
sections, outcomes, descriptions, rationale.

**Never touch:**
- Marker-wrapped or deterministically-rendered regions — e.g. the bytes between
  `<!-- BEGIN rendered:* -->` and `<!-- END rendered:* -->` (TRD §10 from
  `render_trd_section.py`). Rewriting these triggers `validate_trd.py` drift
  errors (`milestone_drift`, `unbounded_markers`).
- JSON sidecars, schema-bound field values, stable anchors, code blocks, and
  literal command/output samples.

If unsure whether a region is rendered, leave it untouched.

## The four principles

### 1. Cut filler & redundancy
Delete throat-clearing, hedging, and restated points. Every sentence earns its place.
- ❌ "It is important to note that, at the end of the day, the system is slow."
- ✅ "The system is slow."
Cut: "it is important to note", "basically", "in order to", "due to the fact that",
"aforementioned", "going forward", "really/genuinely", doubled synonyms.

### 2. Plain language
Short sentences. Active voice. Common words. Define an unavoidable term once.
- ❌ "Latency reduction will be facilitated by the team."
- ✅ "The team will cut latency."

### 3. Structure over prose
Prefer tables and bullets to long paragraphs. Lead with the conclusion (BLUF —
bottom line up front), then support it.
- ❌ A 6-sentence paragraph listing five requirements.
- ✅ A 5-row bullet list, conclusion sentence first.

### 4. Concrete & specific
Name real users, numbers, files, outcomes. Replace vague abstractions.
- ❌ "Improve performance."
- ✅ "Cut checkout p95 latency from 800ms to 200ms."

## Revision pass

Before writing the doc, run each prose block through this checklist:

| Check | Action |
|---|---|
| Filler phrase present? | Delete it. |
| Sentence > ~25 words or passive? | Split / make active. |
| Paragraph lists 3+ parallel items? | Convert to a table or bullets. |
| Vague claim ("fast", "better", "improve")? | Replace with a number/name/file. |
| Point already made above? | Cut the repeat. |
| Conclusion buried at the end? | Move it to the front (BLUF). |

Preserve all facts — numbers, names, targets, file paths — exactly. Tighten the
writing, never the meaning.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Rewriting a `<!-- BEGIN rendered:* -->` block | Leave rendered/marker-wrapped content untouched |
| Editing JSON sidecar values for "clarity" | Sidecars are structured data, not prose |
| Dropping a fact while cutting words | Tighten phrasing, keep every number/name |
| Over-compressing into cryptic shorthand | Concise ≠ terse-to-the-point-of-unclear |

## See Also
- `shield:summarize` — sibling skill for condensing existing long content
- `prd-review` `problem-clarity` / `stakeholder-communicability` — downstream clarity checks
