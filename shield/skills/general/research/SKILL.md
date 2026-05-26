---
name: research
description: Use when starting work on a new feature — gathers product + tech context via Q&A walk (Phase 1) with repo auto-detection, then optionally runs external evidence-gathering with citations (Phase 2). Triggers on /research, investigate, compare, evaluate.
---

# Research Skill

Research a technical topic and produce a well-sourced document with direct quotes, industry references, and a clear recommendation.

## Output Paths — MANDATORY

Write outputs using the Write tool to **exactly** these paths (registry-tracked — see `shield/schema/output-paths.yaml`):

| Registry name | Resolved path | When written |
|---|---|---|
| `{research}` | `{output_dir}/{feature}/research.md` | Phase 2 findings; or Phase 1 context if Phase 2 skipped |
| _(side-artifact)_ | `{output_dir}/{feature}/.session-transcript.md` | Always — Phase 1 Q&A + repo scan context |

Where:
- `{output_dir}` — read from `.shield.json` `output_dir` field (default: `docs/shield`)
- `{feature}` — the feature folder name (ask user if no active feature context: "No active feature context. What feature name should this go under?")

**Do NOT** use numbered run subfolders (`research/{N}-{slug}/`). The flat paths above are the only valid write targets. The Write tool creates directories automatically. After writing, update `{output_dir}/manifest.json` and regenerate `{output_dir}/index.html`.

> `.session-transcript.md` is a hidden side-artifact (not a deliverable) and is intentionally NOT declared in the command's `outputs:` frontmatter.

## When to Use

- Comparing architectural approaches (monorepo vs multi-repo, REST vs gRPC, etc.)
- Evaluating tools or technologies for adoption
- Building evidence-based ADRs or decision documents
- Any time the user needs citations and industry backing for a decision

## When NOT to Use

- Breaking down work into stories — use `shield:plan-docs`
- Reviewing existing code or plans — use `shield:review` or `shield:plan-review`
- Quick factual lookups that don't need citations

## Step Skeleton

At startup, call execute-steps to register these steps. Execute them in order, updating status after each.

| Step | Action | Phase | Condition | Mandatory |
|------|--------|-------|-----------|-----------|
| 1 | Repo scan (silent) | Phase 1 | always | Yes |
| 2 | Surface detected context + confirm | Phase 1 | always | Yes |
| 3 | Q&A walk | Phase 1 | always | Yes |
| 4 | Surface open questions + offer Phase 2 | Phase 1 | always | Yes |
| 5 | PM framing on chosen questions | Phase 2 | if Phase 2 accepted | Conditional |
| 6 | Parallel research agents (3) | Phase 2 | if Phase 2 accepted | Conditional |
| 7 | Synthesize findings | Phase 2 | if Phase 2 accepted | Conditional |
| 8 | PM review | Phase 2 | if Phase 2 accepted | Conditional |
| 9 | Write `{research}` (findings) + `.session-transcript.md` (side-artifact) | Both | always | Yes |

## Workflow

### Phase 1 — Structured Q&A with repo auto-detection (Phase C addition)

#### Step 1: Repo scan (silent)

See `repo-scan.md`. Scan in background. Categories: Stack, Integrations, Compliance markers, Deployment pattern, Recent activity, Past decisions / ADRs, Prior Shield artifacts. Performance budget ≤ 30s; degrade gracefully on large repos.

#### Step 2: Surface detected context + confirm with user

Display the `## Detected Context` block to the user. Prompt:

> "I scanned your repo and found: <summary>. Confirm or correct before I ask the rest?"

Update tags based on user feedback: `(detected)` → `(confirmed)` if user says yes; `(corrected by user)` if user pushes back with a different value; `(manual)` if user adds something Shield missed.

#### Step 3: Q&A walk

See `qa-topics.md` for the topic catalog, depth modes, and skip rules. Walk topics in order, asking only what's not auto-answered.

Skip handling: `skip` or `I don't know` → record `[unanswered]`, surface in Open Questions section.

#### Step 4: Surface unanswered + offer Phase 2

After Phase 1 completes:

```
Phase 1 captured your context. These open questions would benefit from external evidence-gathering:
- <question 1>
- <question 2>

Run Phase 2 (external research)? (yes / no / pick specific)
```

If user says yes or picks specific questions, proceed to Phase 2 (Step 5+). If no, write `.session-transcript.md` to `{output_dir}/{feature}/.session-transcript.md` and finish.

### Phase 2 — External evidence-gathering (existing behavior preserved)

#### Step 5: PM framing on the chosen questions

Dispatch `shield:research-framer` with the chosen research questions as input. Returns the
8-section PF1-PF8 markdown framing brief that shapes the parallel research streams in Step 6.

(Post pm-restructure-v0: this replaces the legacy `shield:product-manager` Research-Framing
dispatch. The output shape is unchanged — markdown brief with PF1-PF8 sections.)

#### Step 6: Three parallel research agents

(Existing 3-agent flow: official sources, industry voices, community experience. Each agent runs with the PM framing context.)

#### Step 7: Synthesize findings

(Existing synthesis logic.)

#### Step 8: PM review on findings (parallel dispatch)

Dispatch the following in parallel, all with the synthesized findings document (and the
framing brief from Step 5) as input:

- `shield:research-reviewer-narrative` — produces the 4-section markdown narrative review
  (User Impact Analysis, Scope Recommendation, Prioritization Framework, Stakeholder Summary).
- `shield:user-impact-clarity` (PM1)
- `shield:problem-solution-fit` (PM2)
- `shield:scope-discipline-of-plan` (PM3)
- `shield:prioritization-rationale` (PM4)
- `shield:stakeholder-communicability` (PM5)
- `shield:market-competitive-awareness` (PM6)
- `shield:adoption-rollout-risk` (PM7)
- `shield:success-metrics-defined` (PM8)
- `shield:reversibility-exit-cost` (PM9)
- `shield:business-value-alignment` (PM10)
- `shield:framing-coverage-honored` (PM11) — passes BOTH `findings_path` AND
  `framing_brief_path`. PM11 returns `N/A` if no framing brief exists; the orchestrator
  excludes N/A from the composite.

The orchestrator collects the 10 single-check JSON returns + PM11 + the narrative markdown
into the legacy `## Product Lens` section shape (narrative + scorecard) so downstream
`{research}` templates keep working.

(Post pm-restructure-v0: replaces the omnibus `shield:product-manager` Research-Review
dispatch with one narrative authoring subagent + 10 PM dim grading subagents + 1 PM11
framing-coverage subagent — 12 parallel calls.)

#### Step 9: Write `{research}` and `.session-transcript.md`

Write findings to `{research}` → `{output_dir}/{feature}/research.md`.
Write the Phase 1 Q&A context to `{output_dir}/{feature}/.session-transcript.md` (hidden side-artifact, always written).

### Combined output

After both phases complete, the feature folder contains:
- `.session-transcript.md` — Phase 1 Q&A + repo scan summary + product/tech context (always present, hidden side-artifact)
- `research.md` (`{research}`) — Phase 2 external evidence with citations (present only if Phase 2 ran; or Phase 1 context summary if Phase 2 skipped)

> Numbered run subfolders (`research/{N}-{slug}/`) are gone. Git history is the run archive.

---

### Legacy clarify step (Phase 2 only mode)

When invoked with `--phase2-only`, skip Phase 1 entirely and run the following original workflow:

## Clarify Topic & Scope

Skip if the user already provided enough context. Otherwise ask:
- What decision or question are they trying to answer?
- Any constraints or preferences to bias toward?

## PM Framing

Dispatch `shield:research-framer` with the research topic as input. Use the Agent tool with
`subagent_type: "shield:research-framer"`.

The agent returns the 8-section PF1-PF8 markdown framing brief: stakeholders, decision(s) to
make, must-cite definitional/origin voices (PF7), source-type coverage matrix (PF8), success
criteria, prioritized research questions, scope boundaries, and timeline & constraints.

This output shapes the research agent prompts in the next step. If framing fails or times
out, proceed with research without framing context — do not block the workflow.

(Post pm-restructure-v0: replaces the legacy `shield:product-manager` Research-Framing
dispatch with the focused `shield:research-framer` subagent.)

## Research (Parallel Agents)

Launch **3 parallel agents** to maximize coverage:

- **Agent 1: Official sources** — docs from primary tools/frameworks
- **Agent 2: Industry voices** — blog posts, conference talks, expert recommendations
- **Agent 3: Community experience** — GitHub discussions, Stack Overflow, case studies

Each agent's prompt includes the PM framing context (if available):

```
Research [topic] from [source type].

Context from product analysis:
- Stakeholders: [from PM framing]
- Key questions to answer: [from PM framing, prioritized]
- Scope: [from PM framing]
- Timeline: [from PM framing]

## Voices that MUST appear with a direct quote (from framing PF7)
[Paste the framing's Must-Cite Definitional/Origin Voices list verbatim. These voices MUST be quoted in your output regardless of which stream is your natural home — definitional/origin voices fall between "shipped a system" and "reported a failure" buckets unless explicitly carved out.]

## Source-type categories this stream owns (from framing PF8)
[Paste the rows of the Source-Type Coverage Matrix where this stream is the owning stream. Find at least one direct quote per assigned category in your output.]

Return direct quotes with attribution, source URLs, key data points. Prioritize findings that address the key questions above.

## Additionally — Further Exploration candidates
Alongside the sources you cite in the body of your findings, surface 3–8 items for **Further Exploration** — high-quality media that a reader could use to go deeper on this topic but that you did NOT cite in your findings body. Organize by media type:
- Books
- Long-form blogs / articles
- Videos / talks
- Courses
- Podcasts / podcast episodes
- Other (newsletters, communities, X threads, conference programs)

Each item: one line — title, author/host, link, and a short "why it's worth reading/watching." These are NOT citations; they are recommendations for further learning. The synthesis step will curate across all three streams.
```

If PM framing was skipped, use the original prompt: `Research [topic] from [source type]. Return direct quotes with attribution, source URLs, key data points.` Note that Further Exploration recommendations should still be surfaced even when framing is skipped.

## Synthesize Findings

- Identify consensus across sources
- Note disagreements and what drives them
- Map findings to the user's specific context
- Form a clear recommendation with reasoning
- **Honor the framing brief** — every voice on the framing's PF7 Must-Cite list must appear with a direct quote in the body of the synthesis (not just References); every required category on the framing's PF8 Source-Type Coverage Matrix must have at least one direct quote in the body. The PM-review pass (PM11) will pressure-test this; surface gaps now rather than have them returned as recommendations.
- **Curate Further Exploration** — collect the Further Exploration candidates from all three stream outputs, deduplicate, drop anything that's already cited in the body (those go in References), and organize the remainder by media type (Books / Long-form blogs / Videos & talks / Courses / Podcasts / Other) for the Further Exploration section of the output.

## PM Review

After synthesizing findings, dispatch the following IN PARALLEL with the findings doc (and
the Step 5 framing brief) as input:

- `shield:research-reviewer-narrative` — markdown narrative (4 sections).
- `shield:user-impact-clarity` ... `shield:business-value-alignment` (PM1-PM10) — single-check
  JSON, one per dim.
- `shield:framing-coverage-honored` (PM11) — receives both findings + framing brief paths.
  Returns `N/A` if no framing brief was produced upstream.

The orchestrator merges the narrative markdown with a scorecard synthesized from the 10 PM
dim returns (plus PM11) into the legacy `## Product Lens` section shape: narrative + PM1-PM11
scorecard table. Include this output as a `## Product Lens` section in the final document,
placed after `## Summary` and before `## References`.

(Post pm-restructure-v0: replaces the omnibus `shield:product-manager` Research-Review
dispatch with one narrative authoring subagent + 11 focused PM dim grading subagents — 12
parallel calls. Output shape preserved for backward compatibility with `{research}` (`research.md`)
templates.)

## Write Document

**Output: `{research}` → `{output_dir}/{feature}/research.md`**

```markdown
# [Decision Title]

**Status:** Proposed
**Date:** [date]
**Context:** [1-2 sentences on what prompted this]

## Decision
[Clear statement of the recommended approach]

## Why Not [Alternative]?
[Comparison table if applicable]

## What the Industry Recommends
### [Source Name] ([Role/Context])
> *"Direct quote"*
> — [Source with link]
[Repeat for 4-8 authoritative sources]

## How This Works in Practice
[Concrete examples relevant to the user's setup]

## Migration Path / Reversibility
[How to change course if the decision turns out wrong]

## Summary
[2-3 sentence wrap-up tying recommendation to evidence]

## Product Lens
[PM review output — narrative sections and scorecard from the PM agent's research-review mode]

## References
- [All source URLs that were cited in the body, as clickable links]

## Further Exploration
*Curated recommendations for going deeper on this topic. Items here are NOT cited in the body — this list is for readers who want to learn beyond the scope of this research. If an item is cited in the body, it belongs in References, not here.*

### Books
- [Title] — [Author] — [link if available] — [one-line "why it's worth reading"]

### Long-form blogs / articles
- ...

### Videos / talks
- ...

### Courses
- ...

### Podcasts / podcast episodes
- ...

### Other (newsletters, communities, X threads, conference programs)
- ...
```

Sections may be omitted if no good item exists for that media type — do not pad. The goal is signal, not surface area.

## Rules

1. **Every claim needs a source** — no unsourced opinions
2. **Use direct quotes** — don't paraphrase when the original wording is impactful
3. **Bias toward the user's context** — frame advice relative to their scale
4. **Include dissenting views** — present both sides when sources disagree
5. **Make it actionable** — end with concrete next steps
6. **Keep it skimmable** — tables, headers, bullet points

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping PM framing because "the topic is straightforward" | Always run PM framing — it prioritizes research questions and sets scope boundaries, preventing unfocused research |
| Paraphrasing sources instead of using direct quotes | Use the original wording with attribution — paraphrases lose credibility and make claims harder to verify |
| All 3 research agents returning the same sources | Each agent has a distinct source type (official docs, industry voices, community) — if they overlap, the prompts need sharper differentiation |
| Writing Product Lens as a separate document instead of a section | PM review output goes inside `{research}` (`research.md`) as `## Product Lens` between Summary and References |
| Including recommendations without source backing | Every recommendation must trace to at least one cited source — unsupported opinions violate rule 1 |
| Omitting dissenting views when sources agree | If all sources agree, state that explicitly — the absence of disagreement is itself a finding worth noting |
| Treating PF7 must-cite voices and PF8 source-type matrix as optional | Stream prompts inherit them verbatim from framing — the originator of a concept (e.g., Karpathy on context engineering, Willison on lethal trifecta, Young/Fowler on event sourcing) MUST appear with a direct quote in the body, and each PF8 required category MUST have a quoted source in the body. PM-review (PM11) will flag missing items as P0/P1 recommendations. |
| Confusing References with Further Exploration | References = sources cited in the body. Further Exploration = curated learning resources NOT cited in the body. If something is in References, it must NOT also be in Further Exploration; it's already been used. |
| Padding Further Exploration to look thorough | Sections without good fits should be omitted entirely. Three excellent items beats nine mediocre ones. The goal is signal, not surface area. |
