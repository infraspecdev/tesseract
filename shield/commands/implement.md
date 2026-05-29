---
name: implement
description: Start TDD-based feature implementation with progress tracking
args: "[feature description or story ID]"
outputs:
  - plan_json    # updated in place with story status as steps complete
---

# Implement

Start implementing a feature using test-driven development with progress tracking.

## Usage

`/implement [feature or story ID]`

## Paths

This command mutates `{plan_json}` = `{output_dir}/{feature}/plan.json` in place as steps complete. On milestone close (step 5h), it also promotes feature-folder LLD drafts to the canonical `docs/lld/{component}.md` location (registry: `lld_canonical_md`).

| Registry key | Resolved path | When written |
|---|---|---|
| `plan_json` | `{output_dir}/{feature}/plan.json` | Mutated in place on every story-status change |
| `lld_canonical_md` | `docs/lld/{component}.md` | Promoted from `{output_dir}/{feature}/lld-{component}.md` at milestone close (step 5h) |

## Behavior

1. If a story ID is provided (e.g., EPIC-1-S1), search all plans in `{output_dir}/*/plan.json` for the story
2. If a feature description is provided, use it as the starting context
3. If nothing provided, ask what the user wants to implement

### Acceptance Criteria Confirmation

4. If story context exists (from sidecar or PM tool):
   - Present acceptance criteria to the user
   - Ask to confirm, edit, or skip
   - If edited, update `{plan_json}` and re-render `{plan_html}` from the updated `{plan_md}` (via the `/plan` rendering flow)

### Implementation

5. Follow the `shield:implement-feature` skill workflow:
   - TDD: write failing tests, implement, per-step review
   - Commit after each step
   - Update story status in `{plan_json}` = `{output_dir}/{feature}/plan.json`
6. **On the story close that completes a milestone**, promote each LLD draft
   listed in `plan.json milestones[<M>].touches_lld[]` from
   `docs/shield/{feature}/lld-{component}.md` to `docs/lld/{component}.md`.
   This includes a fork-drift concurrency check, §14 Changelog row append,
   atomic rename, and `design_refs[]` anchor back-fill. See step 5h in
   `shield:implement-feature/SKILL.md` for the full procedure and the
   just-in-time auto-heal rules.
7. If superpowers is available, delegate TDD to `superpowers:test-driven-development`
8. After all steps complete, invoke `shield:summarize`

### Final Review

8. Offer to run a full `/review` for comprehensive agent-based review
9. Offer next steps: `/review`, `/pm-sync` (to update status)
