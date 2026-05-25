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

This command mutates `{plan_json}` = `{output_dir}/{feature}/plan.json` in place as steps complete. It does NOT write any new files — story status updates land in the existing sidecar so `/plan-review` and `/pm-sync` see the latest state.

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
6. If superpowers is available, delegate TDD to `superpowers:test-driven-development`
7. After all steps complete, invoke `shield:summarize`

### Final Review

8. Offer to run a full `/review` for comprehensive agent-based review
9. Offer next steps: `/review`, `/pm-sync` (to update status)
