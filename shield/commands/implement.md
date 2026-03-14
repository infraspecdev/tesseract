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

1. If a story ID is provided (e.g., EPIC-1-S1), look up the story in the plan sidecar JSON
2. If a feature description is provided, use it as the starting context
3. If nothing provided, ask what the user wants to implement

### Acceptance Criteria Confirmation

4. If story context exists (from sidecar or PM tool):
   - Present acceptance criteria to the user
   - Ask to confirm, edit, or skip:
     ```
     Acceptance Criteria:
       1. Regional pools allocate /20 CIDRs
       2. No CIDR overlap across regions

     [a] Proceed as-is  [b] Edit criteria  [c] Skip
     ```
   - If edited, update the sidecar JSON and re-render HTML

### Implementation

5. Invoke the `shield:general:implement-feature` skill
6. If superpowers is available, delegate TDD to `superpowers:test-driven-development`
7. After each implementation step:
   - Run a lightweight review (code correctness + domain skill only)
   - Present any findings
   - Commit the step
8. After all steps complete, invoke `shield:general:summarize`

### Final Review

9. Offer to run a full `/review` for comprehensive agent-based review
10. Offer next steps: `/review`, `/pm-sync` (to update status)
