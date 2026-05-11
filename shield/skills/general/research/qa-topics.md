# Research Phase 1 — Q&A Topic Catalog

The structured Q&A walk after repo scan. Topics are grouped by product / tech, ordered, and skip rules are explicit.

## Depth modes (configurable via `.shield.json` `research_depth`)

| Mode | Topics asked | Use when |
|---|---|---|
| `lean` | Required only — Problem, Users, Success criteria, Existing systems, Constraints | Small feature / bug fix / "stop me if this is wrong" |
| `standard` (default) | Required + Evidence, Alternatives, Integration points, Technical risks | Substantial feature |
| `deep` | Standard + Hypotheses, Migration plan, Detailed risks, Cross-functional handoffs | Compliance / migration / enterprise feature |

Auto-suggest at start:
- `lean` if topic mentions "small", "bug", "fix"
- `deep` if topic mentions "compliance", "migration", "enterprise", "regulatory"
- Else `standard`

User can override.

## Product topics

| Order | Topic | Required? | Skip rule | Example question |
|---|---|---|---|---|
| 1 | **Problem** | Yes | Skip if already answered in user's initial topic message OR in prior research | "What's the user problem driving this? Pick or describe..." |
| 2 | **Users** | Yes | Skip if persona named in topic message | "Which user segment is most affected — and roughly how many?" |
| 3 | **Evidence** | Standard+ | Skip if Problem answer cites data | "What's the strongest evidence the problem is real?" |
| 4 | **Alternatives** | Standard+ | Skip if topic explicitly excludes alternatives | "How are users coping today, and what other solutions have been considered?" |
| 5 | **Success criteria** | Yes | Never skip | "What metric will tell us this worked, and what's a credible target?" |
| 6 | **Why now** | Standard+ | Skip if obvious from Problem (regulatory deadline, etc.) | "Is there a reason to do this now vs. wait 6 months?" |
| 7 | **Hypotheses** | Deep | Always asked in deep mode | "What do you believe will be true if we ship this?" |

## Tech topics

| Order | Topic | Required? | Skip rule | Example question |
|---|---|---|---|---|
| 8 | **Existing systems** | Yes | Skip if repo scan auto-filled this | "What authentication / data / queue layers exist today? (mostly auto-filled from repo scan)" |
| 9 | **Constraints** | Yes | Skip if repo scan detected compliance markers | "Any hard constraints — compliance, deployment, regulatory, performance?" |
| 10 | **Integration points** | Standard+ | Skip if topic is greenfield with no existing integrations | "Which existing systems will this feature touch?" |
| 11 | **Technical risks** | Standard+ | Skip if topic is trivial | "What technical risks should we be aware of?" |
| 12 | **Migration plan** | Deep | Skip if greenfield | "If touching existing data, what's the migration approach?" |
| 13 | **Cross-functional handoffs** | Deep | Always asked in deep mode | "Which other teams (CS, Finance, Legal, Security) will be pulled in?" |
| 14 | **Open technical questions** | Yes | Never skip — surface as catch-all | "What technical questions are you unsure about?" |

## Skip rule mechanics

For each topic, before asking:
1. Check if user's initial invocation message answers it (regex / keyword match)
2. Check if repo scan auto-filled it
3. Check if a prior research transcript already covered it
4. If covered → mark as auto-filled, surface "✓ <Topic> (from <source>): <answer>"
5. If partially covered → ask only the missing piece
6. If unanswered → ask the full question

## "Skip" / "I don't know" handling

The user can reply `skip` or `i don't know` to any question:
- Shield records `[unanswered]` for that field
- Surfaces it as an Open Question in the transcript's `## Open Questions` section
- Does NOT block progression

## Final transcript structure

```markdown
## Product Context
### Problem
<answer>
### Users
<answer>
### Evidence
<answer or [unanswered]>
...

## Technical Context
### Existing systems
<auto-filled from Detected Context — confirmed entries>
### Constraints
<answer + compliance markers from Detected Context>
...

## Open Questions
- <unanswered topic 1>
- <unanswered topic 2>
- ...

## External Findings (Phase 2)
<populated only if Phase 2 ran>
```

## Phase 2 trigger criteria

After Phase 1 completes, Shield surfaces unanswered + technical questions and offers Phase 2:

```
Phase 1 captured your context. These open questions would benefit from external evidence:
- <question 1>
- <question 2>

Run external evidence-gathering on these? (yes / no / pick specific)
```

If yes, run the existing PM-framing + 3-agent flow on the chosen questions only. Output appended as `## External Findings` in `transcript.md`, and `findings.md` written alongside.
