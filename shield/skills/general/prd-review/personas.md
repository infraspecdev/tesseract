# PRD Review Persona Catalog

Five reviewer agents dispatched in parallel against a PRD. Each receives the PRD content + rubric + its assigned dimensions; each returns a graded report.

## Persona dispatch table

| Persona | Agent ID | Weight | Dimensions owned | Mode hint |
|---|---|---|---|---|
| PM reviewer | `shield:product-manager-reviewer` | 1.0 | 1, 2, 3, 7, 8, 9, 10, 11, 12 | Standalone |
| Agile-coach reviewer | `shield:agile-coach-reviewer` | 1.0 | 4 (incl. AC11/AC12 via story-coverage skill) | Standalone |
| Tech-lead reviewer | `shield:architecture-reviewer` | 1.0 | 5, 6 | Standalone |
| DX reviewer | `shield:dx-engineer-reviewer` | 0.7 | Anti-patterns + cross-cutting clarity | Standalone |
| Cost reviewer | `shield:cost-reviewer` | 0.7 | 13 | Standalone |

## Dispatch prompts

Each persona receives a prompt of this shape (substituted per persona):

```
You are reviewing a PRD in PRD-Review mode. Mode: Standalone.

**PRD source:** {source-prd.md path}
**PRD type:** {standard | lean — confirmed by user}
**Your assigned dimensions:** {list from dispatch table}

**Rubric:** Read `shield/skills/general/prd-review/rubric.md` for evaluation points per dimension, severity model, and grade scale. Read `shield/skills/general/prd-review/scoring.md` for the A-F → composite logic.

**Your job:**
1. Read the PRD at the path above.
2. For each of YOUR assigned dimensions, grade each evaluation point A-F (or N/A with reasoning, or informational for lean dims).
3. Aggregate to a per-dimension grade.
4. Aggregate your dimensions to a persona grade.
5. Identify gaps — for each non-A grade, write a one-sentence gap description.
6. For each gap, suggest a fix (one or two sentences) suitable for use in `enhanced-prd.md` annotation.

**Output format:** Return JSON conforming to this shape:

{
  "persona": "<your agent id>",
  "persona_grade": "A|B|C|D|F",
  "dimensions": [
    {
      "id": 1,
      "name": "Problem clarity",
      "grade": "A|B|C|D|F|N/A|informational",
      "na_reasoning": "<if N/A>",
      "evaluation_points": [
        { "id": "1a", "grade": "A|B|C|D|F", "severity": "Critical|Important|Warning", "gap": "<one sentence or null>", "suggestion": "<one sentence or null>" }
      ]
    }
  ],
  "anti_patterns": [ {"name": "...", "evidence_line": 42, "evidence_quote": "..."} ]  // DX reviewer only
}
```

### Special instructions per persona

**PM reviewer:** When grading dim 11 (Why now & cost-of-inaction) and dim 12 (Risks & assumptions), apply your existing PF1-PF11 evaluation framework where relevant.

**Agile-coach reviewer:** When grading dim 4:
- Apply your existing AC1-AC10 evaluation framework to eval points 4a-4e
- Apply NEW AC11 (Persona-goal coverage) and AC12 (Archetypal flow coverage):
  - Invoke the `shield:story-coverage` skill, passing personas + goals + detected feature domain
  - For each `expected_story` the skill returns that has NO matching story in the PRD's Section 6, count as a gap
  - Severity: per the skill's returned `severity` field

**Tech-lead reviewer (architecture-reviewer):** When grading dim 5 NFRs, treat 5b (security + threat model) and 5e (privacy) as Critical for any feature with user data; treat them as Important for purely internal infrastructure features.

**DX reviewer:** Your primary output is the `anti_patterns` array. You don't own a dimension column in the composite; you contribute via flagging cross-cutting issues that show up in `summary.md`'s "Anti-patterns" section.

**Cost reviewer:** When the feature is clearly internal-only (e.g., test fixture `internal-tool.md`), 13a-13d may be N/A; grade with N/A reasoning.

## Aggregation step (orchestrator, not persona)

After all 5 personas return JSON, the orchestrator:
1. Combines dimensions across personas
2. Computes composite per `scoring.md` formula
3. Applies P0-gate
4. Writes to output artifacts (see SKILL.md Step 6)
