---
name: implement
description: Start TDD-based feature implementation with progress tracking
args: "[feature description or story ID]"
---

# Implement

Start implementing a feature using test-driven development with progress tracking.

## Usage

`/implement [feature or story ID]`

## Behavior

1. If a story ID is provided (e.g., EPIC-1-S1), look up the story in `shield/plan.json`
2. If a feature description is provided, use it as the starting context
3. If nothing provided, ask what the user wants to implement

### Acceptance Criteria Confirmation

4. If story context exists (from sidecar or PM tool):
   - Present acceptance criteria to the user
   - Ask to confirm, edit, or skip
   - If edited, update `shield/plan.json` and re-render HTML

### Implementation

5. Follow the `shield:implement-feature` skill workflow:
   - TDD: write failing tests, implement, per-step review
   - Commit after each step
   - Update `shield/plan.json` story status
6. If superpowers is available, delegate TDD to `superpowers:test-driven-development`
7. After all steps complete, invoke `shield:summarize`

### Final Review

8. Offer to run a full `/review` for comprehensive agent-based review
9. Offer next steps: `/review`, `/pm-sync` (to update status)
